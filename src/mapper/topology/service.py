"""Single-writer persistence and chronological offline replay."""
import json
from .engine import derive, RULES_VERSION
from .history import advance
from .identity import identity
from ..errors import MapperError
from ..models import now


def build(repo, cycle_id=None, *, max_skew=300):
    # Validate options before a migration result or event is written.
    if type(max_skew) is not int or not 1 <= max_skew <= 86400:
        raise MapperError('INVALID_TIME_WINDOW')
    chosen = repo.snapshot_data(cycle_id)
    selected_id = chosen['snapshot']['snapshot_id']
    version = RULES_VERSION + ':skew=' + str(max_skew)
    snapshots = sorted(repo.snapshots(), key=lambda s: (s['started_at'], s['published_at'], s['snapshot_id']))
    previous = None
    selected = None
    # Recompute retained snapshots in chronological order. Existing results are
    # immutable; historical insertion needs an explicit new project/replay.
    last_stored_time = repo.db.execute('SELECT MAX(c.started_at) FROM topology_results t JOIN snapshots s USING(snapshot_id) JOIN cycles c USING(cycle_id) WHERE t.rules_version=?', (version,)).fetchone()[0]
    for s in snapshots:
        cached = repo.db.execute('SELECT result_json FROM topology_results WHERE snapshot_id=? AND rules_version=?', (s['snapshot_id'], version)).fetchone()
        if cached:
            graph = json.loads(cached[0])
        else:
            if last_stored_time and s['started_at'] < last_stored_time:
                raise MapperError('BACKDATED_REPLAY_REQUIRES_NEW_PROJECT')
            data = chosen if s['snapshot_id'] == selected_id else repo.snapshot_data(s['cycle_id'])
            graph = advance(derive(data, max_skew=max_skew), previous)
            repo._budget()
            text = repo._json(graph)
            repo._budget(extra_bytes=3 * len(text.encode('utf-8')))
            # Includes registry, result and events in one transaction.
            with repo.db:
                for n in graph['nodes']:
                    repo.db.execute('INSERT INTO entity_registry VALUES (?,?,?,?,?) ON CONFLICT(entity_id) DO UPDATE SET last_seen=excluded.last_seen',
                                    (n['id'], repo.project_id, repo._json(n['identity_key']), n['last_seen'], n['last_seen']))
                repo.db.execute('INSERT INTO topology_results VALUES (?,?,?,?,?)',
                                (identity(repo.project_id, 'result', s['snapshot_id'], version), s['snapshot_id'], version, now(), text))
                for e in graph['events']:
                    repo.db.execute('INSERT OR IGNORE INTO history_events VALUES (?,?,?,?,?,?,?,?,?)',
                                    (e['event_id'], e['subject_id'], version, e['snapshot_id'], e['previous_snapshot_id'], e['at'], e['kind'], e['origin'], repo._json(e)))
        previous = graph
        if s['snapshot_id'] == selected_id:
            selected = graph
    if selected is None:
        raise MapperError('SNAPSHOT_NOT_FOUND')
    return selected


def history(repo, *, limit=100, rules_version=None):
    if type(limit) is not int or not 1 <= limit <= 10000:
        raise MapperError('INVALID_HISTORY_LIMIT')
    query = 'SELECT event_json FROM history_events'
    params = []
    if rules_version:
        query += ' WHERE rules_version=?'; params.append(rules_version)
    params.append(limit)
    return [json.loads(r[0]) for r in repo.db.execute(query + ' ORDER BY event_at DESC,event_id LIMIT ?', params)]


def summary(graph):
    from collections import Counter
    return {'project_id': graph['project_id'], 'snapshot_id': graph['snapshot_id'], 'rules_version': graph['rules_version'],
            'origin': graph['origin'], 'nodes': dict(Counter(n['kind'] for n in graph['nodes'])),
            'edges': dict(Counter(e['kind'] for e in graph['edges'])), 'warnings': dict(Counter(w['code'] for w in graph['warnings'])),
            'events': len(graph['events']), 'sends_probes': False}
