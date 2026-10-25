from contextlib import contextmanager, closing
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3

from ..config import project_dir
from ..errors import MapperError
from ..private_files import private_directory, prepare_file, protect, reject_link
from ..models import EXECUTIONS, Observation, now, new_id, payload_for, safe_json, uuid_text


class Repository:
    """One thread owns this connection. Collectors hand results to its writer."""

    def __init__(self, root, project_id, *, create_name=None, forbidden=(), max_bytes=2 * 1024**3):
        self.project_id = uuid_text(project_id)
        self.directory = project_dir(root, project_id)
        self.path = self.directory / "mapper.sqlite3"
        self.forbidden = tuple(forbidden)
        self.max_bytes = max_bytes
        if self.directory.is_symlink() or self.path.is_symlink():
            raise MapperError("SYMLINK_PROJECT_NOT_ALLOWED")
        if create_name is not None:
            if self.directory.exists():
                raise MapperError("PROJECT_EXISTS")
            private_directory(self.directory)
        elif not self.path.is_file():
            raise MapperError("PROJECT_NOT_FOUND")
        self._project_lock = None
        try:
            protect(self.directory, directory=True)
            manager = project_lock(self.directory)
            manager.__enter__()
            self._project_lock = manager
            if create_name is not None:
                prepare_file(self.path)
            else:
                for item in self.directory.iterdir():
                    if item.name in {'project.json', 'mapper.sqlite3', 'mapper.sqlite3-journal', 'mapper.sqlite3-wal', 'mapper.sqlite3-shm'} or (item.name.startswith('mapper-v1-') and item.name.endswith('.sqlite3.bak')):
                        protect(item)
            self.db = sqlite3.connect(self.path, timeout=5)
            self.db.row_factory = sqlite3.Row
            self.db.execute("PRAGMA foreign_keys=ON")
            version = self.db.execute("PRAGMA user_version").fetchone()[0]
            if version == 0 and create_name is not None:
                sql = (Path(__file__).parent / "migrations/001_initial.sql").read_text()
                self.db.executescript(sql)
                with self.db:
                    self.db.execute("INSERT INTO project_meta VALUES (?,?,?)", (project_id, create_name, now()))
                protect(self.path)
            elif version not in {1, 2}:
                raise MapperError("UNSUPPORTED_DB_VERSION")
            row = self.db.execute("SELECT project_id FROM project_meta").fetchall()
            if len(row) != 1 or row[0][0] != project_id:
                raise MapperError("DATABASE_PROJECT_MISMATCH")
            version = self.db.execute("PRAGMA user_version").fetchone()[0]
            self.migration_backup = None
            if version == 1:
                # SQLite backup is consistent even if journal/WAL exists.
                self._budget(extra_bytes=self.path.stat().st_size)
                backup_path = self.directory / ("mapper-v1-" + new_id() + ".sqlite3.bak")
                prepare_file(backup_path)
                with closing(sqlite3.connect(backup_path)) as backup:
                    self.db.backup(backup)
                protect(backup_path)
                self.migration_backup = str(backup_path)
                try:
                    self.db.executescript((Path(__file__).parent / "migrations/002_topology.sql").read_text())
                except (sqlite3.Error, OSError):
                    self.db.rollback()
                    raise MapperError("DATABASE_MIGRATION_FAILED_BACKUP_PRESERVED") from None
        except sqlite3.Error:
            self.close()
            raise MapperError("DATABASE_ERROR") from None
        except BaseException:
            self.close()
            raise

    def close(self):
        try:
            if hasattr(self, 'db'):
                self.db.close()
        finally:
            manager = self._project_lock
            self._project_lock = None
            if manager is not None:
                manager.__exit__(None, None, None)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def _json(self, data):
        return safe_json(data, self.forbidden)

    def _budget(self, extra_bytes=0):
        size = sum(p.stat().st_size for p in self.directory.rglob("*") if p.is_file() and not p.is_symlink())
        if size + extra_bytes >= self.max_bytes:
            raise MapperError("DATA_BUDGET_EXCEEDED")

    def register_target(self, target_id, seed, origin="seed"):
        self._json(seed)
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO collection_targets VALUES (?,?,?,?,?,?,?)", (uuid_text(target_id), self.project_id, seed["ip"], seed["port"], seed.get("context", ""), seed["profile_id"], origin))

    def begin_cycle(self, plan, origin="live"):
        self._budget()
        text = self._json(plan)
        cycle = new_id()
        with self.db:
            self.db.execute("INSERT INTO cycles VALUES (?,?,?,?,?,?,?,?,?,?)", (cycle, self.project_id, now(), None, "running", "unknown", text, hashlib.sha256(text.encode()).hexdigest(), origin, None))
        return cycle

    def recover_interrupted(self):
        with self.db:
            self.db.execute("UPDATE cycles SET execution_status='interrupted', coverage_status='partial', finished_at=?, reason='PROCESS_INTERRUPTED' WHERE execution_status IN ('running','queued')", (now(),))

    def write_result(self, cycle_id, result):
        self._budget()
        if not self.db.execute("SELECT 1 FROM cycles WHERE cycle_id=? AND execution_status='running'", (cycle_id,)).fetchone():
            raise MapperError("CYCLE_NOT_RUNNING")
        rid = new_id()
        self._json([result.source, result.table, result.scope_id, result.context_id, result.reason])
        with self.db:
            self.db.execute("INSERT INTO collector_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (rid, cycle_id, result.target_id, result.source, result.table, result.scope_id, result.context_id, result.context_status, result.started_at, result.finished_at, result.status, int(result.exhausted), 0, result.reason))
        try:
            for offset in range(0, len(result.observations), 250):
                rows = []
                for obs in result.observations[offset:offset + 250]:
                    payload = self._json(payload_for(obs.kind, obs.payload))
                    self._json([obs.source_key, obs.evidence_at])
                    rows.append((new_id(), rid, obs.kind, obs.source_key, obs.observed_at, obs.freshness, obs.evidence_at, obs.payload.get("ip"), obs.payload.get("mac"), payload))
                with self.db:
                    self.db.executemany("INSERT INTO observations VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
                self._budget()
            with self.db:
                self.db.execute("UPDATE collector_runs SET record_count=? WHERE collector_run_id=?", (len(result.observations), rid))
        except (MapperError, sqlite3.Error):
            with self.db:
                self.db.execute("UPDATE collector_runs SET status='partial', exhausted=0, reason='WRITE_FAILED' WHERE collector_run_id=?", (rid,))
            raise
        return rid

    def publish(self, cycle_id, execution="finished", reason=None, force_partial=False):
        if execution not in EXECUTIONS - {"running", "queued"}:
            raise MapperError("INVALID_STATUS")
        states = self.db.execute("SELECT status,exhausted FROM collector_runs WHERE cycle_id=?", (cycle_id,)).fetchall()
        coverage = "complete" if states and not force_partial and execution == "finished" and all(s[0] in {"ok", "empty", "not_requested"} and s[1] for s in states) else "partial"
        self._json(reason)
        sid = new_id()
        with self.db:
            cursor = self.db.execute("UPDATE cycles SET execution_status=?,coverage_status=?,finished_at=?,reason=? WHERE cycle_id=? AND execution_status='running'", (execution, coverage, now(), reason, cycle_id))
            if cursor.rowcount != 1:
                raise MapperError("CYCLE_NOT_RUNNING")
            self.db.execute("INSERT INTO snapshots VALUES (?,?,?,?,?)", (sid, cycle_id, 1, now(), coverage))
        return sid

    def snapshots(self, complete=False, scope_hash=None):
        query = "SELECT s.*,c.execution_status,c.origin,c.started_at,c.config_hash FROM snapshots s JOIN cycles c USING(cycle_id)"
        conditions, params = [], []
        if complete:
            conditions.append("s.coverage_status='complete'")
        if scope_hash is not None:
            conditions.append("c.config_hash=?"); params.append(scope_hash)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        return [dict(r) for r in self.db.execute(query + " ORDER BY s.published_at DESC,s.rowid DESC", params)]

    def snapshot_data(self, cycle_id=None):
        if cycle_id is None:
            snapshots = self.snapshots()
            if not snapshots:
                raise MapperError("SNAPSHOT_NOT_FOUND")
            cycle_id = snapshots[0]["cycle_id"]
        snap = self.db.execute("SELECT * FROM snapshots WHERE cycle_id=?", (cycle_id,)).fetchone()
        if snap is None:
            raise MapperError("SNAPSHOT_NOT_FOUND")
        cycle = dict(self.db.execute("SELECT * FROM cycles WHERE cycle_id=?", (cycle_id,)).fetchone())
        cycle["plan"] = json.loads(cycle.pop("plan_json"))
        runs = [dict(r) for r in self.db.execute("SELECT * FROM collector_runs WHERE cycle_id=? ORDER BY rowid", (cycle_id,))]
        targets = [dict(r) for r in self.db.execute("SELECT DISTINCT t.* FROM collection_targets t JOIN collector_runs r ON r.target_id=t.target_id WHERE r.cycle_id=?", (cycle_id,))]
        observations = []
        for row in self.db.execute("SELECT o.* FROM observations o JOIN collector_runs r USING(collector_run_id) WHERE r.cycle_id=? ORDER BY o.rowid", (cycle_id,)):
            item = dict(row)
            item["payload"] = json.loads(item.pop("payload_json"))
            item.pop("ip"); item.pop("mac")
            observations.append(item)
        result = {"schema_version": 1, "project_id": self.project_id, "snapshot": dict(snap), "cycle": cycle, "targets": targets, "runs": runs, "observations": observations}
        self._json(result)
        return result

    def prune(self, days=7):
        # Preserve the latest published and latest complete result for each
        # configuration/scope, not an unrelated LAN's most recent success.
        protected, seen_any, seen_complete = set(), set(), set()
        for s in self.snapshots():
            scope = s["config_hash"]
            if scope not in seen_any or (s["coverage_status"] == "complete" and scope not in seen_complete):
                protected.add(s["cycle_id"])
            seen_any.add(scope)
            if s["coverage_status"] == "complete":
                seen_complete.add(scope)
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat().replace("+00:00", "Z")
        rows = self.db.execute("SELECT cycle_id FROM cycles WHERE finished_at<? AND execution_status!='running'", (cutoff,)).fetchall()
        # Preserve each ruleset's latest graph/state checkpoint as well.
        protected_rules = set()
        for row in self.db.execute("SELECT t.rules_version,s.cycle_id,c.started_at FROM topology_results t JOIN snapshots s USING(snapshot_id) JOIN cycles c USING(cycle_id) ORDER BY c.started_at DESC,s.published_at DESC"):
            if row[0] not in protected_rules:
                protected.add(row[1])
                protected_rules.add(row[0])
        history_cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat().replace("+00:00", "Z")
        with self.db:
            self.db.execute("DELETE FROM history_events WHERE event_at<?", (history_cutoff,))
            for row in rows:
                if row[0] not in protected:
                    self.db.execute("DELETE FROM cycles WHERE cycle_id=?", (row[0],))


@contextmanager
def _file_lock(directory, filename, error):
    """Nonblocking OS advisory lock. Never wait while holding another lock."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    reject_link(path)
    if not path.exists():
        try:
            prepare_file(path)
        except FileExistsError:
            pass
    reject_link(path)
    flags = os.O_RDWR | getattr(os, 'O_NOFOLLOW', 0)
    with os.fdopen(os.open(path, flags), 'r+b') as f:
        try:
            if os.name == 'nt':
                import msvcrt
                f.seek(0)
                if not f.read(1):
                    f.write(b'0'); f.flush()
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise MapperError(error) from None
        try:
            yield
        finally:
            if os.name == 'nt':
                f.seek(0); msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def cycle_lock(root):
    return _file_lock(root, '.cycle.lock', 'CYCLE_ALREADY_RUNNING')


def project_lock(directory):
    return _file_lock(directory, '.project.lock', 'PROJECT_BUSY')
