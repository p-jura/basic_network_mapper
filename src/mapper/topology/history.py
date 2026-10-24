"""Conservative, replayable observation history, not cable-disconnect detection."""
import hashlib
import json
from .identity import identity
from .confidence import seconds


def advance(graph, previous=None):
    previous = previous or {}
    state = json.loads(json.dumps(previous.get('history_state', {})))
    events = []
    snapshot = graph['snapshot_id']
    at = graph['finished_at'] or graph['started_at']

    def emit(kind, nid, old, detail):
        events.append({'event_id': identity(graph['project_id'], 'event', graph['rules_version'], snapshot, old, nid, kind, detail.get('code')),
                       'project_id': graph['project_id'], 'rules_version': graph['rules_version'],
                       'snapshot_id': snapshot, 'previous_snapshot_id': old, 'subject_id': nid,
                       'kind': kind, 'at': at, 'origin': graph['origin'], 'detail': detail})

    def coverage_key(ctx):
        c = graph['presence_coverage'].get(ctx)
        if not c or graph['coverage_status'] != 'complete':
            return None
        return hashlib.sha256(json.dumps([ctx, c['source'], c['interface_scope'], sorted(c['results'])], separators=(',', ':')).encode()).hexdigest()

    current = {n['id']: n for n in graph['nodes'] if n['kind'] == 'endpoint'}
    for nid, n in current.items():
        if nid not in state:
            emit('first_observed', nid, None, {'presence': n['presence'], 'observation_ids': n['evidence'], 'physical_arrival_proven': False})
            state[nid] = {'context': n['context'], 'ips': n['ips'], 'fresh_seen': False, 'misses': 0,
                          'missing_since': None, 'unobserved': False, 'last_snapshot_id': None,
                          'port': None, 'port_changes': [], 'coverage_key': None}
        s = state[nid]
        if n['fresh_presence']:
            emit('returned' if s['unobserved'] else 'fresh_response', nid, s['last_snapshot_id'],
                 {'observation_ids': n['evidence'], 'proves_port': False})
            s.update(fresh_seen=True, misses=0, missing_since=None, unobserved=False)
            s['coverage_key'] = coverage_key(n['context'])
        confirmed = n['confidence'] == 'high' and n['port'] is not None and n['vlan_id'] is not None and graph['coverage_status'] == 'complete'
        port = [n['switch_id'], n['port']['if_index'], n['port']['name'], n['vlan_id']] if confirmed else None
        candidate = next((c for c in n.get('candidates', []) if c['switch_id'] == n['switch_id'] and c['port'] == n['port']), None)
        source_key = json.loads(json.dumps(graph['comparison_scopes']))
        if port and s['port'] and port[:3] != s['port'][:3] and source_key == s.get('port_sources') and graph['coverage_status'] == 'complete':
            emit('port_changed', nid, s.get('last_observed_snapshot_id'), {'before': s['port'], 'after': port,
                                                           'observation_ids': candidate['observation_ids']})
            s['port_changes'] = (s['port_changes'] + [{'at': at, 'before': s['port'], 'after': port}])[-4:]
            changes = s['port_changes']
            if len(changes) >= 3 and seconds(at) - seconds(changes[-3]['at']) <= graph['max_source_skew_seconds'] and changes[-3]['before'] == changes[-2]['after'] and changes[-2]['before'] == changes[-1]['after']:
                emit('suspected_mac_flapping', nid, s['last_snapshot_id'], {'changes': changes[-3:], 'active_loop_proven': False})
        # A weak/interrupted observation breaks adjacency of confirmed port comparisons.
        s['port'] = port
        s['port_sources'] = json.loads(json.dumps(source_key))
        s['last_observed_snapshot_id'] = snapshot
        s['last_seen'] = n['last_seen']

    for nid, s in state.items():
        n = current.get(nid)
        if n and n['fresh_presence']:
            s['last_snapshot_id'] = snapshot
            continue
        if not n:
            s['port'] = None
        key = coverage_key(s['context'])
        c = graph['presence_coverage'].get(s['context'])
        if not key or not s['fresh_seen'] or key != s['coverage_key'] or not s['ips']:
            continue
        # Do not regard an IP reply with a different MAC identity as the old host.
        # It also cannot establish absence of the old physical device.
        if any(c['results'].get(ip) != 'no_reply' for ip in s['ips']):
            continue
        s['misses'] += 1
        s['missing_since'] = s['missing_since'] or at
        if s['misses'] >= 3 and seconds(at) - seconds(s['missing_since']) >= 1800 and not s['unobserved']:
            emit('prolonged_unobserved', nid, s['last_snapshot_id'],
                 {'successful_comparable_cycles': s['misses'], 'since': s['missing_since'],
                  'physical_disconnection_proven': False, 'last_known_ips': s['ips'],
                  'scope': c['interface_scope'], 'comparison_key': key, 'collector_run_id': c['collector_run_id']})
            s['unobserved'] = True
        s['last_snapshot_id'] = snapshot
        if n:
            n['observation_state'] = 'prolonged_unobserved' if s['unobserved'] else 'no_fresh_response'
    for w in graph['warnings']:
        if w['code'] in {'ATTACHMENT_CONFLICT', 'IP_MAC_CONFLICT', 'SHARED_MAC_OR_PROXY_ARP'}:
            emit('conflict', w['subject_id'], previous.get('snapshot_id'), {'code': w['code'], 'observation_ids': w['observation_ids']})
    graph['history_state'] = state
    graph['events'] = sorted(events, key=lambda e: e['event_id'])
    return graph
