"""Bounded local jobs; worker-owned SQLite, no collector calls on rendering."""
import asyncio
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
import copy
import hashlib
import threading
import time

from ..config import Limits
from ..cycle import preview, run_cycle, in_ranges
from ..discovery.system import SystemAdapter
from ..errors import MapperError
from ..models import new_id, safe_json
from ..storage import Repository
from ..topology.service import build, history
from .data import config_read, credential_status, forbidden, read_view


def digest(value):
    return hashlib.sha256(safe_json(value).encode()).hexdigest()


class Controller:
    def __init__(self, root, *, offline=False, adapter_factory=SystemAdapter,
                 runner=run_cycle, clock=time.monotonic):
        self.root, self.offline = root, offline
        self.adapter_factory, self.runner, self.clock = adapter_factory, runner, clock
        self._lock = threading.RLock()
        self._collection = ThreadPoolExecutor(1, thread_name_prefix='mapper-collection')
        self._local = ThreadPoolExecutor(1, thread_name_prefix='mapper-offline')
        self._futures = {}
        self._jobs, self._views = OrderedDict(), OrderedDict()
        self._serial = 0
        self._approvals = {}
        self._loop = self._cancel = None
        self._cancel_requested = False
        self._series = None
        self._last_collection = None
        self._closed = threading.Event()
        self._timer = threading.Thread(target=self._timer_loop, name='mapper-timer')
        self._timer.start()

    def _online(self):
        if self.offline:
            raise MapperError('OFFLINE_MODE')

    def submit(self, label, pid, function, *, collection=False):
        lane = 'collection' if collection else 'local'
        with self._lock:
            if self._closed.is_set():
                raise MapperError('PANEL_CLOSED')
            if lane in self._futures and not self._futures[lane].done():
                raise MapperError('CYCLE_ALREADY_RUNNING' if collection else 'PANEL_JOB_BUSY')
            job_id = new_id()
            self._serial += 1
            self._jobs[job_id] = {'id': job_id, 'project_id': pid, 'label': label,
                                  'state': 'preparing', 'started': self.clock(), 'serial': self._serial, 'progress': {}}
            while len(self._jobs) > 16:
                completed = next((k for k, j in self._jobs.items() if 'ended' in j), None)
                if completed is None:
                    break
                del self._jobs[completed]
            if collection:
                self._last_collection = job_id
                self._cancel_requested = False
            executor = self._collection if collection else self._local
            self._futures[lane] = executor.submit(self._execute, job_id, function, collection)
            return job_id

    def _execute(self, job_id, function, collection):
        try:
            result = function(job_id)
            self.update(job_id, state='cancelled' if (result or {}).get('execution_status') == 'cancelled' else 'finished', result=result)
        except Exception as exc:
            code = exc.code if isinstance(exc, MapperError) else 'PANEL_JOB_FAILED'
            self.update(job_id, state='failed', error=code)
            if collection:
                self.disarm()
        finally:
            with self._lock:
                self._jobs[job_id]['ended'] = self.clock()
                if collection:
                    self._loop = self._cancel = None
                    if self._series:
                        self._series['next'] = self.clock() + self._series['seconds']

    def update(self, job_id, **values):
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].update(values)

    def progress(self, job_id, value):
        with self._lock:
            self._jobs[job_id]['progress'].update(value)

    def job(self, job_id):
        with self._lock:
            job = copy.deepcopy(self._jobs.get(job_id, {}))
            if job:
                job['elapsed'] = round(job.get('ended', self.clock()) - job['started'], 1)
            return job

    def status(self):
        with self._lock:
            jobs = list(self._jobs.values())
            running = [j for j in jobs if j['state'] in {'preparing', 'collecting', 'building', 'cancelling'}]
            return {'offline': self.offline, 'jobs': [self.job(j['id']) for j in running], 'last_collection': self._last_collection,
                    'repeat': None if not self._series else {
                        'project_id': self._series['pid'],
                        'seconds_until_next': None if self._series['next'] is None else max(0, round(self._series['next'] - self.clock()))}}

    def cache(self, view):
        with self._lock:
            key = new_id()
            self._views[key] = view
            while len(self._views) > 4:
                self._views.popitem(last=False)
            return key

    def view(self, key, pid):
        with self._lock:
            view = self._views.get(key)
            if not view or view['graph']['project_id'] != pid:
                raise MapperError('VIEW_EXPIRED_RELOAD')
            return view

    def load(self, pid, cycle=None):
        return self.submit('Wczytanie mapy', pid, lambda _: {'view': self.cache(read_view(self.root, pid, cycle))})

    def prepare(self, pid):
        self._online()
        self.disarm()
        def work(_):
            cfg = config_read(self.root, pid)
            self._scope(cfg)
            plan = asyncio.run(preview(cfg, self.adapter_factory(Limits(**cfg['limits']))))
            if plan.get('basic') and plan['basic']['route_compatible'] != plan['basic']['targets']:
                raise MapperError('ROUTE_OR_INTERFACE_CHANGED')
            token = new_id()
            with self._lock:
                self._approvals = {token: {'pid': pid, 'config': digest(cfg), 'plan': digest(plan),
                                          'expires': self.clock() + 120}}
            return {'approval': token, 'plan': plan, 'credentials': credential_status(cfg)}
        return self.submit('Podgląd zakresu — bez sond', pid, work)

    @staticmethod
    def _scope(cfg):
        if cfg.get('seeds') and (not cfg.get('allowed_ranges') or any(not in_ranges(s['ip'], cfg['allowed_ranges']) for s in cfg['seeds'])):
            raise MapperError('SEED_OUTSIDE_SCOPE')
        if cfg.get('recursive') and not cfg.get('allowed_ranges'):
            raise MapperError('RECURSION_NEEDS_SCOPE')

    def invalidate(self):
        with self._lock:
            self._approvals.clear()
        self.disarm()

    def start(self, pid, token, *, repeat_minutes=None):
        self._online()
        with self._lock:
            approved = self._approvals.get(token)
            if not approved or approved['pid'] != pid or approved['expires'] < self.clock():
                raise MapperError('PREVIEW_REQUIRED')
            approved = dict(approved)
            if repeat_minutes is not None:
                if isinstance(repeat_minutes, bool) or not isinstance(repeat_minutes, (int, float)) or not 1 <= repeat_minutes <= 10080:
                    raise MapperError('INVALID_REFRESH_INTERVAL')
            job = self._start_approved(pid, approved)
            self._approvals.pop(token, None)  # Single-use, including a second browser tab.
            self._series = None if repeat_minutes is None else {
                'pid': pid, 'approved': approved, 'seconds': repeat_minutes * 60, 'next': None}
            return job

    def _start_approved(self, pid, approved):
        self._online()
        return self.submit('Odkrywanie i topologia', pid,
                           lambda job: self._collect(job, pid, approved), collection=True)

    def _collect(self, job, pid, approved):
        async def work():
            cfg = config_read(self.root, pid)
            self._scope(cfg)
            if digest(cfg) != approved['config']:
                raise MapperError('CONFIG_CHANGED_PREVIEW_REQUIRED')
            used = {s['profile_id'] for s in cfg.get('seeds', [])}
            if cfg.get('recursive'):
                used.add(cfg['recursive_profile_id'])
            required = {key: cfg['profiles'][key] for key in used}
            if not all(credential_status({'profiles': required}).values()):
                raise MapperError('MISSING_CREDENTIAL')
            adapter = self.adapter_factory(Limits(**cfg['limits']))
            plan = await preview(cfg, adapter)
            if digest(plan) != approved['plan']:
                raise MapperError('NETWORK_CHANGED_PREVIEW_REQUIRED')
            with self._lock:
                self._loop = asyncio.get_running_loop()
                self._cancel = asyncio.Event()
                if self._cancel_requested or self._closed.is_set():
                    self._cancel.set()
            with Repository(self.root, pid, forbidden=forbidden(cfg), max_bytes=cfg['limits']['data_bytes']) as repo:
                self.update(job, state='collecting')
                result = await self.runner(repo, cfg, self._cancel, adapter=adapter,
                                           progress=lambda value: self.progress(job, value), expected_plan=plan)
                self.update(job, state='building')
                graph = build(repo, result['cycle_id'])
                repo._json(graph)
                key = self.cache({'graph': graph, 'history': history(repo), 'snapshots': repo.snapshots()})
            if result['execution_status'] != 'finished' or result['coverage_status'] != 'complete':
                self.disarm()
            return {**result, 'view': key}
        return asyncio.run(work())

    def cancel(self):
        self.disarm()
        with self._lock:
            self._cancel_requested = True
            if self._loop and self._cancel:
                self._loop.call_soon_threadsafe(self._cancel.set)
            for job in self._jobs.values():
                if job['label'] == 'Odkrywanie i topologia' and job['state'] in {'preparing', 'collecting'}:
                    job['state'] = 'cancelling'

    def disarm(self):
        with self._lock:
            self._series = None

    def tick(self):
        with self._lock:
            series = self._series
            if not series or series['next'] is None or self.clock() < series['next']:
                return
            series['next'] = None
            try:
                self._start_approved(series['pid'], series['approved'])
            except MapperError as exc:
                if exc.code == 'CYCLE_ALREADY_RUNNING':
                    series['next'] = self.clock() + series['seconds']
                else:
                    self._series = None

    def _timer_loop(self):
        while not self._closed.wait(1):
            self.tick()

    def close(self):
        self._closed.set()
        self.cancel()
        self._timer.join()
        self._collection.shutdown(wait=True, cancel_futures=True)
        self._local.shutdown(wait=True, cancel_futures=True)
