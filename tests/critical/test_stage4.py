"""Critical operator boundaries; no actual network or browser framework."""
import asyncio
import base64
from dataclasses import asdict, replace
import json
import os
import threading
import time
from unittest.mock import patch

from test_stage2 import ProtectedTest, FakeAdapter
from mapper.app import create_app
from mapper.cli import demo
from mapper.config import Limits
from mapper.errors import MapperError
from mapper.snapshots import export_snapshot
from mapper.storage import Repository
from mapper.storage.repository import cycle_lock
from mapper.ui.controller import Controller
from mapper.ui.data import config_read, save_config, read_view, export_private, import_upload, csv_text
from mapper.ui.graph import project, details


def wait(control, job):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        state = control.job(job)
        if state.get('state') in {'finished', 'failed', 'cancelled'}:
            return state
        time.sleep(.005)
    raise AssertionError('Worker failed to finish within 5s')


class PanelTests(ProtectedTest):
    def control(self, **kwargs):
        c = Controller(self.root, **kwargs)
        self.addCleanup(c.close)
        return c

    def setup_basic(self):
        pid = demo(self.root)['project_id']
        cfg = config_read(self.root, pid)
        cfg['basic'] = {'interface': 'fixture0', 'cidr': '192.0.2.0/29'}
        cfg['limits'] = asdict(replace(Limits(), rate=1000))
        cfg['profiles'] = {'unused': {'type':'snmp2','community_env':'MAPPER_UNUSED_MISSING'}}
        save_config(self.root, pid, cfg)
        return pid

    def approval(self, c, pid):
        job = wait(c, c.prepare(pid))
        self.assertEqual(job['state'], 'finished', job)
        return job['result']['approval']

    def test_offline_import_demo_load_and_isolation_never_collect(self):
        a, b = demo(self.root)['project_id'], demo(self.root)['project_id']
        def forbidden(*args, **kwargs):
            raise AssertionError('Offline touched a collector')
        c = self.control(offline=True, adapter_factory=forbidden, runner=forbidden)
        va = wait(c, c.load(a))['result']['view']
        vb = wait(c, c.load(b))['result']['view']
        ga, gb = c.view(va, a)['graph'], c.view(vb, b)['graph']
        self.assertNotEqual(ga['nodes'][0]['id'], gb['nodes'][0]['id'])
        with self.assertRaisesRegex(MapperError, 'VIEW_EXPIRED_RELOAD'):
            c.view(va, b)
        for action in [lambda: c.prepare(a), lambda: c.start(a, 'forged')]:
            with self.assertRaisesRegex(MapperError, 'OFFLINE_MODE'):
                action()
        path = export_private(self.root, a, ga, 'source-json')
        pid = import_upload(self.root, 'data:application/json;base64,' + base64.b64encode(path.read_bytes()).decode())
        self.assertNotIn(pid, [a, b])
        self.assertFalse(list((self.root/'.imports').glob('*.json')))
        self.assertEqual(read_view(self.root, pid)['graph']['origin'], 'imported')

    def test_worker_progress_single_use_preview_and_stale_config(self):
        pid = self.setup_basic()
        c = self.control(adapter_factory=lambda _: FakeAdapter())
        token = self.approval(c, pid)
        result = wait(c, c.start(pid, token))
        self.assertEqual(result['state'], 'finished', result)
        self.assertEqual(result['result']['coverage_status'], 'complete')
        self.assertEqual(result['progress']['basic']['pending'], 0)
        self.assertEqual(sum(result['progress']['basic'][k] for k in ['reply','no_reply','error','skipped']), 5)
        with self.assertRaisesRegex(MapperError, 'PREVIEW_REQUIRED'):
            c.start(pid, token)
        old = self.approval(c, pid)
        cfg = config_read(self.root, pid); cfg['limits']['rate'] = 999
        save_config(self.root, pid, cfg)
        fail = wait(c, c.start(pid, old))
        self.assertEqual(fail['error'], 'CONFIG_CHANGED_PREVIEW_REQUIRED')
        self.assertTrue(c.view(result['result']['view'], pid))

    def test_cancel_waits_for_worker_and_other_project_remains_available(self):
        pid = self.setup_basic(); other = demo(self.root)['project_id']
        started, release = threading.Event(), threading.Event()
        class Adapter(FakeAdapter):
            async def probe(self, *args):
                started.set()
                while not release.is_set():
                    await asyncio.sleep(.005)
                return 'no_reply', None
        c = self.control(adapter_factory=lambda _: Adapter())
        job = c.start(pid, self.approval(c, pid))
        self.assertTrue(started.wait(2))
        try:
            # A second bounded local worker serves project B while A is collecting.
            local = wait(c, c.load(other))
            self.assertEqual(local['state'], 'finished')
            with self.assertRaisesRegex(MapperError, 'PROJECT_BUSY'):
                save_config(self.root, pid, config_read(self.root, pid))
            with self.assertRaisesRegex(MapperError, 'CYCLE_ALREADY_RUNNING'):
                c._start_approved(pid, {})
            c.cancel()
            self.assertEqual(c.job(job)['state'], 'cancelling')
        finally:
            release.set()
        finished = wait(c, job)
        self.assertEqual(finished['state'], 'cancelled', finished)
        self.assertEqual(finished['result']['coverage_status'], 'partial')
        with Repository(self.root, pid) as repo:
            self.assertEqual(repo.snapshots()[0]['coverage_status'], 'partial')

    def test_route_change_root_lock_and_expired_preview_fail_closed(self):
        pid = self.setup_basic(); clock = [0]
        adapter = FakeAdapter()
        c = self.control(adapter_factory=lambda _: adapter, clock=lambda: clock[0])
        token = self.approval(c, pid); clock[0] = 121
        with self.assertRaisesRegex(MapperError, 'PREVIEW_REQUIRED'):
            c.start(pid, token)
        token = self.approval(c, pid)
        with cycle_lock(self.root):
            failed = wait(c, c.start(pid, token))
        self.assertEqual(failed['error'], 'CYCLE_ALREADY_RUNNING')
        token = self.approval(c, pid)
        async def changed():
            return []
        adapter.routes = changed
        failed = wait(c, c.start(pid, token))
        self.assertEqual(failed['error'], 'NETWORK_CHANGED_PREVIEW_REQUIRED')
        self.assertEqual(adapter.calls, 0)  # neighbors are called only during actual collection.

    def test_repeat_timer_no_catchup_changes_disarm_and_no_restart(self):
        pid = self.setup_basic(); clock = [0]
        c = self.control(adapter_factory=lambda _: FakeAdapter(), clock=lambda: clock[0])
        first = wait(c, c.start(pid, self.approval(c, pid), repeat_minutes=15))
        self.assertEqual(c.status()['repeat']['seconds_until_next'], 900)
        clock[0] = 899; c.tick()
        self.assertEqual(c.status()['last_collection'], first['id'])
        clock[0] = 900; c.tick()
        second = c.status()['last_collection']
        self.assertNotEqual(first['id'], second)
        self.assertEqual(wait(c, second)['state'], 'finished')
        cfg = config_read(self.root, pid); cfg['limits']['rate'] = 998; save_config(self.root, pid, cfg)
        clock[0] = 1800; c.tick()
        self.assertEqual(wait(c, c.status()['last_collection'])['error'], 'CONFIG_CHANGED_PREVIEW_REQUIRED')
        self.assertIsNone(c.status()['repeat'])
        self.assertIsNone(self.control(offline=True).status()['repeat'])

    def test_filters_export_and_untrusted_csv_preserve_evidence(self):
        pid = demo(self.root)['project_id']; graph = read_view(self.root, pid)['graph']
        original = json.dumps(graph, sort_keys=True)
        elements, counts = project(graph, '192.0.2.20', 'unknown', True)
        self.assertGreater(counts['nodes'], 0)
        self.assertEqual(json.dumps(graph, sort_keys=True), original)
        for kind in ['topology-json', 'nodes-csv', 'edges-csv', 'source-json', 'source-csv']:
            path = export_private(self.root, pid, graph, kind)
            self.assertTrue(path.is_file())
            if os.name != 'nt':
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        full = json.loads(export_private(self.root, pid, graph, 'topology-json').read_text())
        self.assertEqual(len(full['nodes']), len(graph['nodes']))
        self.assertIn("'=SUM", csv_text([{'name':'=SUM(A1)'}, {'name':'  @evil'}], ['name']))
        self.assertIn("'  @evil", csv_text([{'name':'  @evil'}], ['name']))
        self.assertEqual(details(graph, graph['nodes'][0]['id'])['Producent'], 'nieustalony')
        with self.assertRaises(MapperError):
            export_private(self.root, self.project(), graph, 'topology-json')

    def test_private_config_validation_import_limits_and_secrets(self):
        pid = self.setup_basic(); cfg = config_read(self.root, pid)
        old = (self.root/pid/'project.json').read_bytes()
        cfg['profiles'] = {'bad': {'type':'snmp2', 'community':'do-not-accept'}}
        with self.assertRaises(MapperError): save_config(self.root, pid, cfg)
        self.assertEqual((self.root/pid/'project.json').read_bytes(), old)
        with self.assertRaises(MapperError): import_upload(self.root, 'data:;base64,invalid!')
        cfg = config_read(self.root, pid)
        cfg['profiles'] = {'safe': {'type':'snmp2','community_env':'MAPPER_TEST_SECRET'}}
        with patch.dict(os.environ, {'MAPPER_TEST_SECRET':'fixture-value-hidden'}):
            save_config(self.root, pid, cfg)
            c = self.control(adapter_factory=lambda _: FakeAdapter())
            result = wait(c, c.prepare(pid))
            self.assertNotIn('fixture-value-hidden', json.dumps(result))
            self.assertNotIn(b'fixture-value-hidden', (self.root/pid/'project.json').read_bytes())

    def test_http_origin_session_host_and_callbacks(self):
        pid = demo(self.root)['project_id']
        app = create_app(self.root, offline=True)
        self.addCleanup(app.mapper_controller.close)
        client = app.server.test_client(); url = 'http://127.0.0.1:8050'
        self.assertEqual(client.get('/', base_url='http://evil.test').status_code, 403)
        self.assertEqual(client.post('/_dash-update-component', base_url=url).status_code, 403)
        self.assertEqual(client.get('/', base_url=url).status_code, 200)
        headers = {'Origin': url}
        self.assertEqual(client.post('/_dash-update-component', base_url=url, headers={'Origin':'http://evil.test'}).status_code, 403)
        layout = client.get('/_dash-layout', base_url=url)
        self.assertEqual(layout.status_code, 200)
        self.assertNotIn(b'http://cdn', layout.data)
        key = next(k for k in app.callback_map if k.startswith('..map.elements'))
        meta = app.callback_map[key]
        payload = {'output': key, 'outputs': [{'id': o.component_id, 'property': o.component_property} for o in meta['output']],
                   'inputs': [{'id':i['id'],'property':i['property'],'value':None if i['id']=='view-ref' else ''} for i in meta['inputs']],
                   'state':[{'id':'project','property':'value','value':pid}], 'changedPropIds':['view-ref.data']}
        response = client.post('/_dash-update-component',base_url=url,headers=headers,json=payload)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.json['response']['map']['elements'], [])
        # A forged offline start is also rejected in the controller, not just a disabled widget.
        with self.assertRaisesRegex(MapperError,'OFFLINE_MODE'):
            app.mapper_controller.start(pid,'forged')


class AdditionalBoundaries(ProtectedTest):
    def test_expected_source_and_plan_do_not_allow_a_changed_address(self):
        from mapper.discovery.basic import collect_basic
        from mapper.cycle import run_cycle
        pid = self.project()
        cfg = config_read(self.root, pid)
        cfg['basic'] = {'interface':'fixture0','cidr':'192.0.2.0/29'}
        adapter = FakeAdapter()
        async def local():
            return [r async for r in collect_basic(cfg['basic'], Limits(), asyncio.Event(), adapter, expected_source='192.0.2.99')]
        with self.assertRaisesRegex(MapperError, 'NETWORK_CHANGED_PREVIEW_REQUIRED'):
            asyncio.run(local())
        with Repository(self.root,pid) as repo:
            with self.assertRaisesRegex(MapperError, 'NETWORK_CHANGED_PREVIEW_REQUIRED'):
                asyncio.run(run_cycle(repo,cfg,adapter=adapter,expected_plan={}))
            self.assertEqual(repo.snapshots(),[])
        self.assertEqual(adapter.calls,0)

    def test_source_csv_rechecks_known_secrets_and_managed_scope_is_explicit(self):
        from mapper.models import Observation,TableResult
        pid = self.project()
        with Repository(self.root,pid) as repo:
            cycle = repo.begin_cycle({})
            repo.write_result(cycle, TableResult('snmp','identity',[Observation('device_identity','name',{'name':'fixture-known-secret'})]))
            repo.publish(cycle)
        with Repository(self.root,pid,forbidden=('fixture-known-secret',)) as repo:
            with self.assertRaisesRegex(MapperError,'SECRET_IN_OUTPUT'):
                export_snapshot(repo,self.root/'must-not-exist.csv',csv_format=True)
        self.assertFalse((self.root/'must-not-exist.csv').exists())
        c = Controller(self.root,adapter_factory=lambda _: FakeAdapter())
        try:
            cfg = config_read(self.root,pid)
            cfg['seeds'] = [{'ip':'192.0.2.5','port':161,'profile_id':'fixture'}]
            cfg['profiles'] = {'fixture':{'type':'snmp2','community_env':'MAPPER_FIXTURE_COMMUNITY'}}
            save_config(self.root,pid,cfg)
            self.assertEqual(wait(c,c.prepare(pid))['error'],'SEED_OUTSIDE_SCOPE')
        finally:
            c.close()


class LauncherTests(ProtectedTest):
    def test_ready_opens_actual_port_and_closes_owned_resources(self):
        from mapper.app import run
        opened = threading.Event(); urls = []
        class Server:
            server_port = 8051
            closed = False
            def service_actions(self): pass
            def serve_forever(self, **kwargs):
                self.service_actions()
                if not opened.wait(1): raise AssertionError('Browser was not opened after readiness')
            def server_close(self): self.closed = True
        server = Server()
        def browser(url): urls.append(url); opened.set(); return True
        with patch('werkzeug.serving.make_server', return_value=server) as bind, patch('webbrowser.open', browser):
            run(self.root, port=8051, offline=True)
        self.assertEqual(bind.call_args.args[:2], ('127.0.0.1', 8051))
        self.assertEqual(urls,['http://127.0.0.1:8051'])
        self.assertTrue(server.closed)
