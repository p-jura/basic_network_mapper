"""Small local graph viewer; full operator panel belongs to Stage 4."""
import json
import threading
import webbrowser
from ..errors import MapperError


def create_app(graph):
    from dash import Dash, html, Input, Output
    import dash_cytoscape as cyto
    app = Dash(__name__, serve_locally=True)
    nodes = [{'data': {'id': n['id'], 'label': ', '.join(n['names'] or n['ips'] or n['macs']) or n.get('label', n['kind']),
                       'kind': n['kind']}} for n in graph['nodes']]
    edges = []
    labels = {'logical_membership': 'segment logiczny', 'lldp_adjacency': 'LLDP',
              'attachment': 'przypisanie', 'attachment_candidate': 'kandydat'}
    for e in graph['edges']:
        label = labels[e['kind']]
        if e.get('port'):
            label += ' · ' + str(e['port'].get('name') or e['port'].get('if_index') or '?')
            label += ' · VLAN ' + str(e.get('vlan_id') or '?')
        elif e['kind'] == 'lldp_adjacency':
            label += ' · ' + str(e['local_port']['if_index'] or '?') + ' ↔ ' + str(e['remote_port']['if_index'] or '?')
        edges.append({'data': {'id': e['id'], 'source': e['source'], 'target': e['target'], 'label': label}, 'classes': e['kind']})
    app.layout = html.Div([
        html.H3('Topologia offline — podgląd Etapu 3'),
        html.P('Relacje logiczne i kandydatury nie dowodzą kabla. Kliknij węzeł, aby zobaczyć dowody.'),
        html.P('Zielona: przypisanie · niebieska: LLDP · przerywana: kandydatura lub segment logiczny'),
        cyto.Cytoscape(id='graph', elements=nodes + edges, layout={'name': 'circle', 'radius': max(200, min(800, len(nodes) * 18)), 'padding': 70}, minZoom=0.2, maxZoom=1.5,
                       style={'height': '70vh', 'width': '100%'}, stylesheet=[
                           {'selector': 'node', 'style': {'label': 'data(label)', 'background-color': '#2878a5', 'font-size': 12, 'width': 36, 'height': 36}},
                           {'selector': 'edge', 'style': {'label': 'data(label)', 'font-size': 10, 'width': 2, 'curve-style': 'bezier', 'text-rotation': 'autorotate', 'text-background-color': '#fff', 'text-background-opacity': 0.9, 'text-background-padding': 3}},
                           {'selector': 'node[kind = "collection_endpoint"]', 'style': {'shape': 'round-rectangle'}},
                           {'selector': '.attachment', 'style': {'line-color': '#298344'}},
                           {'selector': '.lldp_adjacency', 'style': {'line-color': '#2878a5'}},
                           {'selector': '.logical_membership, .attachment_candidate', 'style': {'line-style': 'dashed', 'line-color': '#b58228'}}]),
        html.Pre(id='details', style={'whiteSpace': 'pre-wrap', 'fontSize': 12})], style={'fontFamily': 'system-ui, sans-serif', 'padding': '12px 24px'})
    by_id = {n['id']: n for n in graph['nodes']}

    @app.callback(Output('details', 'children'), Input('graph', 'tapNodeData'))
    def details(selected):
        return json.dumps(by_id.get((selected or {}).get('id'), {'warnings': graph['warnings']}), ensure_ascii=False, indent=2)
    return app


def view(graph, *, port=8050, open_browser=True):
    if not 1 <= port <= 65535:
        raise MapperError('INVALID_PORT')
    from werkzeug.serving import make_server
    try:
        app = create_app(graph)
    except ImportError:
        raise MapperError('PREVIEW_DEPENDENCIES_MISSING') from None
    # Bind first: a failed bind never opens another process's UI.
    try:
        server = make_server('127.0.0.1', port, app.server, threaded=True)
    except (OSError, SystemExit):
        raise MapperError('PANEL_PORT_UNAVAILABLE') from None
    ready = threading.Event()
    # WSGI socket is already listening; only start browser once the serving
    # loop has processed its first service_actions tick.
    original = server.service_actions
    def service_actions():
        original()
        ready.set()
    server.service_actions = service_actions
    if open_browser:
        def launch():
            if ready.wait(5):
                webbrowser.open(f'http://127.0.0.1:{server.server_port}')
        threading.Thread(target=launch, daemon=True).start()
    try:
        server.serve_forever(poll_interval=0.1)
    finally:
        server.server_close()
