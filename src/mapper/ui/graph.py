"""Read-only view projection. Filtering never changes topology evidence."""
import re

LABELS = {'logical_membership': 'segment logiczny', 'lldp_adjacency': 'LLDP',
          'attachment': 'przypisanie', 'attachment_candidate': 'kandydat'}
COLORS = ['#54a4db', '#e4ac54', '#68b7a2', '#be87d2', '#df7d83', '#879de1']


def vlans(graph):
    return sorted({e['vlan_id'] for e in graph['edges'] if type(e.get('vlan_id')) is int})


def matches(node, query):
    values = node.get('ips', []) + node.get('macs', []) + node.get('names', []) + [node.get('label', '')]
    if any(query.casefold() in str(v).casefold() for v in values):
        return True
    mac_query = re.sub('[:.\\-]', '', query).casefold()
    return len(mac_query) >= 4 and any(mac_query in re.sub('[:.\\-]', '', m).casefold() for m in node.get('macs', []))


def project(graph, query='', vlan='all', expand=False):
    nodes = {n['id']: n for n in graph['nodes']}
    query = (query or '').strip()[:256]
    selected_vlan = None if vlan in {'all', 'unknown', None} else int(vlan)
    edges = [e for e in graph['edges'] if vlan in {'all', None} or
             (e.get('vlan_id') is None if vlan == 'unknown' else e.get('vlan_id') == selected_vlan)]
    involved = {e[k] for e in edges for k in ('source', 'target')}
    known_vlan_nodes = {e[k] for e in graph['edges'] if e.get('vlan_id') is not None for k in ('source', 'target')}
    chosen = {nid for nid, n in nodes.items() if (vlan in {'all', None} or nid in involved or
              (vlan == 'unknown' and n.get('vlan_id') is None and nid not in known_vlan_nodes)) and
              (not query or matches(n, query))}
    if not query and not expand and len(nodes) > 200:
        chosen = {nid for nid in chosen if nodes[nid]['kind'] != 'endpoint'}
    context = set()
    # Only infrastructure/segments provide context; never reveal unrelated hosts.
    for e in edges:
        for a, b in [(e['source'], e['target']), (e['target'], e['source'])]:
            if a in chosen and b in nodes and nodes[b]['kind'] != 'endpoint':
                context.add(b)
    shown = chosen | context
    result = []
    by_vlan = {}
    for e in graph['edges']:
        for n in (e['source'], e['target']):
            if e.get('vlan_id') is not None:
                by_vlan.setdefault(n, set()).add(e['vlan_id'])
    for nid in sorted(shown):
        n = nodes[nid]
        label = ', '.join(n.get('names') or n.get('ips') or n.get('macs') or []) or n.get('label', n['kind'])
        memberships = sorted(by_vlan.get(nid, set()))
        result.append({'data': {'id': nid, 'label': label, 'kind': n['kind'], 'gateway': 1 if n.get('gateway_by_route') else 0, 'color': COLORS[memberships[0] % len(COLORS)] if len(memberships) == 1 else '#728497'},
                       'classes': 'context' if nid not in chosen else ''})
    for e in edges:
        if e['source'] not in shown or e['target'] not in shown:
            continue
        label = LABELS[e['kind']]
        if e.get('port'):
            label += ' · ' + str(e['port'].get('name') or e['port'].get('if_index') or '?')
        if e['kind'] == 'lldp_adjacency':
            label += ' · ' + str(e.get('local_port', {}).get('if_index') or '?') + ' ↔ ' + str(e.get('remote_port', {}).get('if_index') or '?')
        if e.get('vlan_id') is not None:
            label += ' · VLAN ' + str(e['vlan_id'])
        result.append({'data': {'id': e['id'], 'source': e['source'], 'target': e['target'], 'label': label}, 'classes': e['kind']})
    return result, {'nodes': len(shown), 'all_nodes': len(nodes), 'edges': sum('source' in x['data'] for x in result), 'all_edges': len(graph['edges'])}


def details(graph, ident):
    for node in graph['nodes']:
        if node['id'] == ident:
            assignments = [e for e in graph['edges'] if e['kind'] in {'attachment', 'attachment_candidate'} and ident in (e['source'], e['target'])]
            by_id = {n['id']: n for n in graph['nodes']}
            assignments = [{'Switch': ', '.join(by_id.get(e['target'], {}).get('names') or by_id.get(e['target'], {}).get('ips') or [e['target']]),
                            'Port': (e.get('port') or {}).get('name') or (e.get('port') or {}).get('if_index') or 'nieustalony',
                            'VLAN': e.get('vlan_id') if e.get('vlan_id') is not None else 'nieustalony',
                            'Pewność': e.get('confidence', 'unknown'), 'Typ': LABELS[e['kind']],
                            'Uzasadnienie': e.get('reasons', [])} for e in assignments]
            return {'IP': node.get('ips', []), 'MAC': node.get('macs', []), 'Nazwa': node.get('names', []),
                    'Rola według dowodów': node['kind'], 'Producent': 'nieustalony',
                    'Ostatnia obserwacja': node.get('last_seen'), 'Świeża obecność': node.get('fresh_presence'),
                    'Przypisania switch / port / VLAN': assignments or 'nieustalone',
                    'Dowody i ograniczenia': node}
    return next((e for e in graph['edges'] if e['id'] == ident), {'Wybór': 'Kliknij urządzenie lub połączenie'})


STYLES = [
    {'selector': 'node', 'style': {'label': 'data(label)', 'background-color': 'data(color)', 'color': '#dce7ee', 'text-background-color': '#122130', 'text-background-opacity': .9, 'text-background-padding': 3, 'font-size': 11, 'width': 30, 'height': 30}},
    {'selector': 'node[kind="collection_endpoint"]', 'style': {'shape': 'round-rectangle', 'width': 45}},
    {'selector': 'node[kind="gateway_candidate"], node[gateway=1]', 'style': {'shape': 'triangle'}},
    {'selector': 'node[kind="segment"]', 'style': {'shape': 'diamond', 'background-color': '#b89752'}},
    {'selector': 'node[kind="local_interface"]', 'style': {'shape': 'hexagon'}},
    {'selector': 'edge', 'style': {'label': 'data(label)', 'color': '#b8c8d4', 'line-color': '#728497', 'width': 2, 'curve-style': 'bezier', 'font-size': 9, 'text-rotation': 'autorotate', 'text-background-color': '#122130', 'text-background-opacity': .95, 'text-background-padding': 3}},
    {'selector': '.attachment', 'style': {'line-color': '#68b7a2'}},
    {'selector': '.lldp_adjacency', 'style': {'line-color': '#54a4db', 'width': 3}},
    {'selector': '.logical_membership, .attachment_candidate', 'style': {'line-style': 'dashed', 'line-color': '#e4ac54'}},
    {'selector': '.context', 'style': {'border-width': 2, 'border-style': 'dashed', 'border-color': '#dce7ee'}},
    {'selector': ':selected', 'style': {'border-width': 3, 'border-color': '#fff', 'line-color': '#fff'}}]
