BEGIN IMMEDIATE;
CREATE TABLE entity_registry (
 entity_id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES project_meta(project_id),
 identity_key_json TEXT NOT NULL, first_seen TEXT, last_seen TEXT,
 UNIQUE(project_id, identity_key_json)
);
CREATE TABLE topology_results (
 result_id TEXT PRIMARY KEY, snapshot_id TEXT NOT NULL REFERENCES snapshots(snapshot_id) ON DELETE CASCADE,
 rules_version TEXT NOT NULL, created_at TEXT NOT NULL, result_json TEXT NOT NULL,
 UNIQUE(snapshot_id, rules_version)
);
-- Source IDs intentionally are provenance values, not cascading foreign keys:
-- 90-day event details survive 7-day source retention.
CREATE TABLE history_events (
 event_id TEXT PRIMARY KEY, subject_id TEXT NOT NULL REFERENCES entity_registry(entity_id),
 rules_version TEXT NOT NULL, snapshot_id TEXT NOT NULL, previous_snapshot_id TEXT,
 event_at TEXT NOT NULL, kind TEXT NOT NULL, origin TEXT NOT NULL, event_json TEXT NOT NULL
);
CREATE INDEX history_subject_time ON history_events(subject_id,event_at);
CREATE INDEX topology_rules_time ON topology_results(rules_version,created_at);
PRAGMA user_version=2;
COMMIT;
