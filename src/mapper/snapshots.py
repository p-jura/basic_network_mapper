import csv
import json
from pathlib import Path

from .errors import MapperError
from .models import COVERAGES, EXECUTIONS, SOURCES, STATUSES, Observation, TableResult, new_id, safe_json, timestamp, uuid_text
from .storage import Repository
from .private_files import private_file

MAX_BYTES = 100 * 1024**2
MAX_RECORDS = 200000


def export_snapshot(repo, output, cycle_id=None, *, csv_format=False):
    data = repo.snapshot_data(cycle_id)
    safe_json(data, repo.forbidden)  # Both JSON and CSV must reject known secret values.
    # Exclusive creation: do not overwrite a file or follow an existing symlink.
    with private_file(output, newline="") as f:
        if csv_format:
            writer = csv.writer(f)
            writer.writerow(["observation_id", "collector_run_id", "kind", "source_key", "observed_at", "freshness", "evidence_at", "payload_json"])
            for row in data["observations"]:
                cells = [row[k] for k in ["observation_id", "collector_run_id", "kind", "source_key", "observed_at", "freshness", "evidence_at"]] + [safe_json(row["payload"])]
                # Keep spreadsheets from interpreting untrusted names as formulas.
                writer.writerow(["'" + v if isinstance(v, str) and v.startswith(("=", "+", "-", "@", "\t", "\r")) else v for v in cells])
        else:
            f.write(safe_json(data, repo.forbidden))
        f.flush()


def read_snapshot(path, *, max_bytes=MAX_BYTES, max_records=MAX_RECORDS):
    if type(max_bytes) is not int or max_bytes <= 0 or type(max_records) is not int or max_records <= 0:
        raise MapperError("INVALID_IMPORT_LIMIT")
    try:
        with Path(path).expanduser().open("rb") as f:
            raw = f.read(max_bytes + 1)
        if len(raw) > max_bytes:
            raise MapperError("IMPORT_SIZE_LIMIT")
        data = json.loads(raw)
    except (ValueError, OSError, RecursionError):
        raise MapperError("INVALID_SNAPSHOT") from None
    if not isinstance(data, dict) or set(data) != {"schema_version", "project_id", "snapshot", "cycle", "targets", "runs", "observations"} or type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise MapperError("UNSUPPORTED_SNAPSHOT")
    uuid_text(data["project_id"])
    for key in ["targets", "runs", "observations"]:
        if not isinstance(data[key], list) or len(data[key]) > max_records:
            raise MapperError("IMPORT_RECORD_LIMIT")
    cycle = data["cycle"]
    snap = data["snapshot"]
    if not isinstance(cycle, dict) or set(cycle) != {"cycle_id", "project_id", "started_at", "finished_at", "execution_status", "coverage_status", "plan", "config_hash", "origin", "reason"}:
        raise MapperError("INVALID_SNAPSHOT_CYCLE")
    uuid_text(cycle["cycle_id"])
    if cycle["project_id"] != data["project_id"] or cycle["execution_status"] not in EXECUTIONS - {"running", "queued"} or cycle["coverage_status"] not in COVERAGES:
        raise MapperError("INVALID_SNAPSHOT_CYCLE")
    timestamp(cycle["started_at"]); timestamp(cycle["finished_at"])
    if not isinstance(snap, dict) or set(snap) != {"snapshot_id", "cycle_id", "schema_version", "published_at", "coverage_status"} or snap["cycle_id"] != cycle["cycle_id"] or snap["schema_version"] != 1 or snap["coverage_status"] != cycle["coverage_status"]:
        raise MapperError("INVALID_SNAPSHOT_METADATA")
    uuid_text(snap["snapshot_id"]); timestamp(snap["published_at"])
    # Imported plans are not executable configurations. Whitelist their shape.
    if not isinstance(cycle["plan"], dict) or not cycle["plan"].keys() <= {"project_id", "basic", "targets", "limits", "recursive", "allowed_ranges", "sends_probes", "imported_from"}:
        raise MapperError("INVALID_SNAPSHOT_PLAN")
    # Config/command/credential fields are never accepted anywhere in a replay.
    def check_keys(value):
        if isinstance(value, dict):
            for k, v in value.items():
                if k.lower() in {"command", "commands"} or any(word in k.lower() for word in ("password", "community", "auth_key", "priv_key", "secret")):
                    raise MapperError("FORBIDDEN_SNAPSHOT_FIELD")
                check_keys(v)
        elif isinstance(value, list):
            for v in value:
                check_keys(v)
    try:
        check_keys(data)
    except RecursionError:
        raise MapperError("SNAPSHOT_TOO_DEEP") from None
    if cycle["origin"] not in {"live", "synthetic", "imported"} or not isinstance(cycle["config_hash"], str) or len(cycle["config_hash"]) != 64:
        raise MapperError("INVALID_SNAPSHOT_CYCLE")
    if cycle["reason"] is not None and MapperError(cycle["reason"]).code != cycle["reason"]:
        raise MapperError("INVALID_REASON_CODE")
    target_ids = set()
    for t in data["targets"]:
        if not isinstance(t, dict) or set(t) != {"target_id", "project_id", "ip", "port", "context_id", "profile_id", "origin"} or t["project_id"] != data["project_id"]:
            raise MapperError("INVALID_SNAPSHOT_TARGET")
        uuid_text(t["target_id"])
        if t["target_id"] in target_ids:
            raise MapperError("DUPLICATE_SNAPSHOT_TARGET")
        import ipaddress
        try:
            ipaddress.IPv4Address(t["ip"])
        except (ValueError, TypeError):
            raise MapperError("INVALID_SNAPSHOT_TARGET") from None
        if type(t["port"]) is not int or not 1 <= t["port"] <= 65535:
            raise MapperError("INVALID_SNAPSHOT_TARGET")
        if any(not isinstance(t[k], str) or len(t[k]) > 256 or "\x00" in t[k] for k in ["context_id", "profile_id", "origin"]):
            raise MapperError("INVALID_SNAPSHOT_TARGET")
        target_ids.add(t["target_id"])
    runs = {}
    for r in data["runs"]:
        expected = {"collector_run_id", "cycle_id", "target_id", "source", "table_name", "scope_id", "context_id", "context_status", "started_at", "finished_at", "status", "exhausted", "record_count", "reason"}
        if not isinstance(r, dict) or set(r) != expected or r["cycle_id"] != cycle["cycle_id"] or r["source"] not in SOURCES or r["status"] not in STATUSES or r["context_status"] not in {"known", "default", "unknown"} or r["exhausted"] not in (0, 1) or type(r["record_count"]) is not int or r["record_count"] < 0:
            raise MapperError("INVALID_SNAPSHOT_RUN")
        uuid_text(r["collector_run_id"]); timestamp(r["started_at"]); timestamp(r["finished_at"])
        TableResult(r["source"], r["table_name"], status=r["status"], exhausted=bool(r["exhausted"]), reason=r["reason"], started_at=r["started_at"], finished_at=r["finished_at"], target_id=r["target_id"], scope_id=r["scope_id"], context_id=r["context_id"], context_status=r["context_status"])
        if r["target_id"] is not None and r["target_id"] not in target_ids:
            raise MapperError("INVALID_SNAPSHOT_TARGET")
        if r["collector_run_id"] in runs:
            raise MapperError("DUPLICATE_SNAPSHOT_RUN")
        runs[r["collector_run_id"]] = r
    observations = []
    keys = set()
    ids = set()
    counts = dict.fromkeys(runs, 0)
    for o in data["observations"]:
        if not isinstance(o, dict) or set(o) != {"observation_id", "collector_run_id", "kind", "source_key", "observed_at", "freshness", "evidence_at", "payload"} or o["collector_run_id"] not in runs:
            raise MapperError("INVALID_SNAPSHOT_OBSERVATION")
        uuid_text(o["observation_id"])
        obs = Observation(**{k: o[k] for k in ["kind", "source_key", "payload", "observed_at", "freshness", "evidence_at"]})
        key = (o["collector_run_id"], obs.kind, obs.source_key)
        if key in keys or o["observation_id"] in ids:
            raise MapperError("DUPLICATE_SNAPSHOT_OBSERVATION")
        keys.add(key); ids.add(o["observation_id"]); counts[o["collector_run_id"]] += 1
        observations.append((o["collector_run_id"], obs))
    if any(r["record_count"] != counts[rid] for rid, r in runs.items()):
        raise MapperError("SNAPSHOT_COUNT_MISMATCH")
    return data, observations


def import_snapshot(root, path, *, name="Imported snapshot", max_bytes=MAX_BYTES, max_records=MAX_RECORDS):
    # No platform discovery or protocol imports are invoked in this function.
    data, observations = read_snapshot(path, max_bytes=max_bytes, max_records=max_records)
    pid = new_id()
    with Repository(root, pid, create_name=name) as repo:
        plan = {"project_id": pid, "imported_from": data["project_id"], "sends_probes": False}
        cycle_id = repo.begin_cycle(plan, origin="imported")
        targets = {}
        for t in data["targets"]:
            ident = new_id(); targets[t["target_id"]] = ident
            repo.register_target(ident, {"ip": t["ip"], "port": t["port"], "context": t["context_id"], "profile_id": "imported"}, "imported")
        grouped = {r["collector_run_id"]: [] for r in data["runs"]}
        for rid, obs in observations:
            grouped[rid].append(obs)
        for r in data["runs"]:
            result = TableResult(r["source"], r["table_name"], grouped[r["collector_run_id"]], status=r["status"], exhausted=bool(r["exhausted"]), reason=r["reason"], started_at=r["started_at"], finished_at=r["finished_at"], target_id=targets.get(r["target_id"]), scope_id=r["scope_id"], context_id=r["context_id"], context_status=r["context_status"])
            repo.write_result(cycle_id, result)
        # Preserve historical cycle times. 'origin=imported' prevents it
        # being mistaken for a newly executed successful discovery.
        with repo.db:
            repo.db.execute("UPDATE cycles SET started_at=? WHERE cycle_id=?", (data["cycle"]["started_at"], cycle_id))
        repo.publish(cycle_id, execution=data["cycle"]["execution_status"], reason=data["cycle"]["reason"], force_partial=data["cycle"]["coverage_status"] != "complete")
        with repo.db:
            repo.db.execute("UPDATE cycles SET finished_at=? WHERE cycle_id=?", (data["cycle"]["finished_at"], cycle_id))
        config = {"schema_version": 1, "project_id": pid, "name": name, "basic": None, "seeds": [], "profiles": {}, "allowed_ranges": [], "limits": {}}
        with private_file(repo.directory / "project.json") as output:
            output.write(safe_json(config))
    return pid
