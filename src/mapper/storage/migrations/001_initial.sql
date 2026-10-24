CREATE TABLE project_meta (
 project_id TEXT PRIMARY KEY, name TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE collection_targets (
 target_id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES project_meta(project_id),
 ip TEXT NOT NULL, port INTEGER NOT NULL, context_id TEXT NOT NULL,
 profile_id TEXT NOT NULL, origin TEXT NOT NULL
);
CREATE TABLE cycles (
 cycle_id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES project_meta(project_id),
 started_at TEXT NOT NULL, finished_at TEXT,
 execution_status TEXT NOT NULL, coverage_status TEXT NOT NULL,
 plan_json TEXT NOT NULL, config_hash TEXT NOT NULL, origin TEXT NOT NULL,
 reason TEXT
);
CREATE TABLE collector_runs (
 collector_run_id TEXT PRIMARY KEY, cycle_id TEXT NOT NULL REFERENCES cycles(cycle_id) ON DELETE CASCADE,
 target_id TEXT REFERENCES collection_targets(target_id), source TEXT NOT NULL, table_name TEXT NOT NULL,
 scope_id TEXT NOT NULL, context_id TEXT NOT NULL, context_status TEXT NOT NULL,
 started_at TEXT NOT NULL, finished_at TEXT NOT NULL, status TEXT NOT NULL,
 exhausted INTEGER NOT NULL, record_count INTEGER NOT NULL, reason TEXT
);
CREATE TABLE observations (
 observation_id TEXT PRIMARY KEY,
 collector_run_id TEXT NOT NULL REFERENCES collector_runs(collector_run_id) ON DELETE CASCADE,
 kind TEXT NOT NULL, source_key TEXT NOT NULL, observed_at TEXT NOT NULL,
 freshness TEXT NOT NULL, evidence_at TEXT, ip TEXT, mac TEXT, payload_json TEXT NOT NULL,
 UNIQUE(collector_run_id, kind, source_key)
);
CREATE TABLE snapshots (
 snapshot_id TEXT PRIMARY KEY, cycle_id TEXT NOT NULL UNIQUE REFERENCES cycles(cycle_id) ON DELETE CASCADE,
 schema_version INTEGER NOT NULL, published_at TEXT NOT NULL, coverage_status TEXT NOT NULL
);
CREATE INDEX cycles_project_time ON cycles(project_id, started_at);
CREATE INDEX runs_cycle_target ON collector_runs(cycle_id, target_id, status);
CREATE INDEX obs_kind_run ON observations(kind, collector_run_id);
CREATE INDEX obs_ip ON observations(ip);
CREATE INDEX obs_mac ON observations(mac);
PRAGMA user_version=1;
