"""Dash widgets and callbacks; collection and graph building live in Controller."""
import json
from pathlib import Path

from ..config import validate_config
from ..errors import MapperError
from ..models import safe_json
from .controller import digest
from .data import projects, config_read, save_config, import_upload, read_view, export_private, forbidden
from .graph import project, vlans, details, STYLES


def status_text(status):
    states = {'preparing': 'Przygotowanie', 'collecting': 'Odkrywanie', 'building': 'Budowanie mapy', 'cancelling': 'Anulowanie'}
    lines = []
    for job in status['jobs']:
        lines.append(f"{job['label']}: {states.get(job['state'], job['state'])} · {job['elapsed']} s")
        progress = job.get('progress', {})
        b = progress.get('basic')
        if b:
            lines.append(f"Cele {b['total']} · odpowiedź {b['reply']} · brak odpowiedzi {b['no_reply']} · błąd {b['error']} · pominięte {b['skipped']} · oczekujące {b['pending']}")
        if progress.get('devices_scheduled'):
            lines.append(f"Urządzenia {progress.get('devices_done', 0)}/{progress['devices_scheduled']} · tabele {progress.get('tables_done', 0)}")
    repeat = status['repeat']
    if repeat:
        left = repeat['seconds_until_next']
        lines.append('Odświeżanie włączone' + (f' · kolejny start za {left} s' if left is not None else ' · po zakończeniu zadania'))
    return '\n'.join(lines) or 'Brak aktywnego zadania. Odświeżanie wyłączone.'


def preview_text(plan, env):
    lines = []
    b = plan.get('basic')
    if b:
        lines += [f"Interfejs: {b['interface']}", f"Źródło IPv4: {b['source_ip']} / {b['netmask']}",
                  f"Brama według tras: {b.get('gateway') or 'nieustalona'}", f"Zakres: {b['cidr']} · celów: {b['targets']}",
                  f"Tempo: {b['rate']}/s · równolegle: {b['parallel']} · limit: {b['timeout']} s"]
    lines.append('Seedy: ' + (', '.join(t['ip'] + ':' + str(t['port']) for t in plan['targets']) or 'brak'))
    lines.append('Dozwolone zakresy zarządzania: ' + (', '.join(plan['allowed_ranges']) or 'brak'))
    if plan['targets']:
        limits = plan['limits']
        lines.append(f"Odczyty równolegle: {limits['parallel']} (SSH {limits['ssh_parallel']}) · limit cyklu {limits['cycle_timeout']} s")
    if plan['recursive']:
        lines.append(f"LLDP: do {plan['limits']['recursion_devices']} urządzeń / {plan['limits']['recursion_depth']} przejść")
    for name, present in env.items():
        lines.append(f"ENV {name}: {'dostępna' if present else 'BRAK'}")
    lines.append('Podgląd nie wysłał sond. Start dotyczy wskazanego zakresu.')
    return '\n'.join(lines)


def create_panel(control, assets):
    from dash import Dash, dcc, html, Input, Output, State, ctx, no_update
    import dash_cytoscape as cyto
    cyto.load_extra_layouts()  # Bundled SVG renderer; no CDN.
    app = Dash(__name__, assets_folder=str(assets), serve_locally=True, title='Mapper sieci', update_title=None)
    def button(label, ident, **kwargs):
        return html.Button(label, id=ident, n_clicks=0, **kwargs)
    app.layout = html.Div([
        dcc.Store(id='interface-facts'), dcc.Store(id='view-ref'), dcc.Store(id='job-ref'), dcc.Store(id='approval'),
        dcc.Interval(id='poll', interval=1000), dcc.Download(id='download'),
        html.Header([html.Div([html.Span('FL / MAPPER', className='brand'), html.H1('Mapa Twojej sieci'),
                    html.P('Lokalne odkrywanie IPv4 · topologia oparta na dowodach')]),
                    html.Div('OFFLINE — kolektory zablokowane' if control.offline else 'TRYB LOKALNY · start ręczny', className='badge')]),
        html.Section([
            html.Div([html.Label('Projekt'), dcc.Dropdown(id='project', options=projects(control.root), placeholder='Wybierz projekt', clearable=False)]),
            dcc.Input(id='new-name', placeholder='Nazwa nowego projektu', maxLength=128),
            button('Utwórz', 'create'), button('Demo offline', 'demo'), button('Odśwież listę', 'refresh-projects'),
            dcc.Upload(id='upload', children=button('Importuj snapshot JSON', 'upload-label'), multiple=False, accept='.json'),
        ], className='project-bar'),
        html.Div(id='message', role='status', className='message'),
        html.Main([
            html.Aside([
                html.H2('Odkrywanie'),
                html.P('Wybierz interfejs i zakres. Start panelu nie wysyła sond.'),
                button('Odczytaj lokalne interfejsy', 'interfaces', disabled=control.offline),
                dcc.Dropdown(id='interface', placeholder='Interfejs IPv4'),
                dcc.Input(id='cidr', placeholder='Zakres CIDR, np. 192.0.2.0/24', type='text', debounce=True),
                html.Div(id='interface-info', className='muted'),
                html.Details([html.Summary('Seedy i profile — opcjonalnie'),
                    html.Label('Seedy JSON'), dcc.Textarea(id='seeds', value='[]'),
                    html.Label('Profile JSON — tylko nazwy zmiennych ENV'), dcc.Textarea(id='profiles', value='{}'),
                    html.Label('Dozwolone zakresy zarządzania JSON'), dcc.Textarea(id='ranges', value='[]'),
                    dcc.Checklist(id='recursive', options=[{'label': 'Rekurencja LLDP w dozwolonym zakresie', 'value': 'yes'}], value=[]),
                    dcc.Input(id='recursive-profile', placeholder='Identyfikator profilu LLDP'),
                    html.P('SNMP2: community_env. SNMP3: user_env, auth_key_env, priv_key_env. SSH: user_env, known_hosts; platforma cisco_ios. Wartości sekretów ustaw przed startem procesu.', className='muted')]),
                html.Details([html.Summary('Budżety pracy'), dcc.Textarea(id='limits', value='{}')]),
                button('Zapisz konfigurację', 'save'),
                button('Pokaż zakres — bez sond', 'prepare', disabled=control.offline),
                html.Pre(id='preview', children='Najpierw przygotuj i sprawdź zakres.', className='preview'),
                dcc.Checklist(id='repeat', options=[{'label': 'Powtarzaj ten plan po zakończeniu cyklu', 'value': 'yes'}], value=[]),
                html.Label('Interwał od zakończenia zadania (minuty)'), dcc.Input(id='minutes', type='number', min=1, max=10080, value=15),
                button('Odkryj wskazany zakres', 'start', disabled=control.offline, className='primary'),
                button('Anuluj aktywny cykl', 'cancel'), button('Zatrzymaj odświeżanie', 'disarm'),
                html.Pre(id='status', className='status')
            ], className='settings'),
            html.Section([
                html.Div([html.H2('Topologia'), html.Span(id='snapshot-meta', className='muted')], className='map-heading'),
                html.Div([dcc.Dropdown(id='snapshot', options=[{'label': 'Najnowszy wynik', 'value': 'latest'}], value='latest', clearable=False),
                          button('Wczytaj mapę', 'load'), dcc.Input(id='search', placeholder='Szukaj IP / MAC / nazwy', debounce=True),
                          dcc.Dropdown(id='vlan', options=[{'label': 'Wszystkie VLAN-y', 'value': 'all'}, {'label': 'VLAN nieustalony', 'value': 'unknown'}], value='all', clearable=False),
                          dcc.Checklist(id='expand', options=[{'label': 'Pokaż hosty w dużym grafie', 'value': 'yes'}], value=[]),
                          button('Dopasuj i ułóż', 'layout'), button('Wyczyść filtry', 'clear-filters')], className='filters'),
                html.P('Zielona: przypisanie · niebieska: LLDP · przerywana: relacja logiczna lub kandydat. Obramowanie przerywane: kontekst filtra.', className='legend'),
                html.Div(id='visible-count', className='muted'),
                cyto.Cytoscape(id='map', elements=[], layout={'name': 'circle', 'radius': 220, 'padding': 65}, stylesheet=STYLES,
                               minZoom=.05, maxZoom=3, style={'height': '58vh', 'width': '100%'}),
                html.Div([button('PNG widoku', 'png'), button('SVG widoku', 'svg'),
                    dcc.Dropdown(id='format', options=[{'label': label, 'value': val} for label, val in [
                        ('Topologia JSON — pełny graf', 'topology-json'), ('Urządzenia CSV — pełny graf', 'nodes-csv'),
                        ('Relacje CSV — pełny graf', 'edges-csv'), ('Snapshot źródłowy JSON — replay', 'source-json'),
                        ('Obserwacje źródłowe CSV', 'source-csv')]], value='topology-json', clearable=False),
                    button('Zapisz prywatny eksport', 'export'), button('Pobierz kopię', 'download-data')], className='exports'),
                html.P('Obrazy obejmują widoczny kadr i filtry. Dane obejmują pełny wybrany snapshot. Pobrana kopia zawiera dane sieci; jej uprawnieniami zarządza przeglądarka.', className='muted'),
                html.Div(id='export-status', role='status'),
                html.Details([html.Summary('Historia i ograniczenia'), html.Pre(id='history')], open=False),
            ], className='workspace'),
            html.Aside([html.H2('Szczegóły'), html.Div(id='details', children='Wczytaj mapę i wybierz urządzenie lub połączenie.')], className='details')
        ]), html.Footer('Pawel Juroszek · FL Development / Dane lokalne · tylko odczyt urządzeń')
    ], className='shell')

    def view(ref, pid):
        if not ref or ref.get('pid') != pid:
            raise MapperError('VIEW_REQUIRED')
        return control.view(ref['key'], pid)

    def form_config(pid, interface, cidr, seeds, profiles, ranges, limits, recursive, recursive_profile):
        cfg = config_read(control.root, pid)
        try:
            cfg.update(basic={'interface': interface, 'cidr': cidr} if interface and cidr else None,
                       seeds=json.loads(seeds or '[]'), profiles=json.loads(profiles or '{}'),
                       allowed_ranges=json.loads(ranges or '[]'), limits=json.loads(limits or '{}'),
                       recursive='yes' in (recursive or []))
        except (ValueError, TypeError):
            raise MapperError('INVALID_CONFIG') from None
        if cfg['recursive']:
            cfg['recursive_profile_id'] = recursive_profile
        else:
            cfg.pop('recursive_profile_id', None)
        return validate_config(cfg, pid)

    @app.callback(Output('interface', 'options'), Output('interface-info', 'children'), Output('interface-facts', 'data'),
                  Input('interfaces', 'n_clicks'), prevent_initial_call=True)
    def interfaces(_):
        if control.offline:
            return [], 'Tryb offline', []
        from ..discovery.system import interfaces as local_interfaces
        try:
            rows = [i for i in local_interfaces() if i['is_up']]
            options = [{'label': f"{i['interface']} · {i['ip']} / {i['netmask']}", 'value': i['interface']} for i in rows]
            return options, 'Wybierz zgodny LAN; zakres sprawdzisz w podglądzie.', rows
        except Exception:
            return [], 'Nie udało się odczytać interfejsów.', []

    @app.callback(Output('interface', 'value'), Output('cidr', 'value'), Output('seeds', 'value'),
                  Output('profiles', 'value'), Output('ranges', 'value'), Output('limits', 'value'),
                  Output('recursive', 'value'), Output('recursive-profile', 'value'),
                  Input('project', 'value'))
    def config_form(pid):
        if not pid:
            return None, '', '[]', '{}', '[]', '{}', [], ''
        try:
            cfg = config_read(control.root, pid)
            basic = cfg.get('basic') or {}
            dumps = lambda value: json.dumps(value, ensure_ascii=False, indent=2)
            return basic.get('interface'), basic.get('cidr', ''), dumps(cfg.get('seeds', [])), dumps(cfg.get('profiles', {})), dumps(cfg.get('allowed_ranges', [])), dumps(cfg.get('limits', {})), ['yes'] if cfg.get('recursive') else [], cfg.get('recursive_profile_id', '')
        except (MapperError, OSError):
            return None, '', '[]', '{}', '[]', '{}', [], ''

    @app.callback(Output('project', 'options'), Output('project', 'value'), Output('view-ref', 'data'),
                  Output('job-ref', 'data'), Output('approval', 'data'), Output('preview', 'children'),
                  Output('message', 'children'), Output('snapshot', 'options'), Output('status', 'children'), Output('snapshot', 'value'),
                  Input('create', 'n_clicks'), Input('demo', 'n_clicks'), Input('refresh-projects', 'n_clicks'),
                  Input('upload', 'contents'), Input('project', 'value'), Input('load', 'n_clicks'),
                  Input('save', 'n_clicks'), Input('prepare', 'n_clicks'), Input('start', 'n_clicks'),
                  Input('cancel', 'n_clicks'), Input('disarm', 'n_clicks'), Input('poll', 'n_intervals'),
                  Input('interface', 'value'), Input('cidr', 'value'), Input('seeds', 'value'),
                  Input('profiles', 'value'), Input('ranges', 'value'), Input('limits', 'value'),
                  Input('recursive', 'value'), Input('recursive-profile', 'value'),
                  State('new-name', 'value'), State('snapshot', 'value'), State('view-ref', 'data'),
                  State('job-ref', 'data'), State('approval', 'data'), State('repeat', 'value'), State('minutes', 'value'),
                  prevent_initial_call=True)
    def actions(_create, _demo, _refresh, upload, pid, _load, _save, _prepare, _start, _cancel, _disarm, _poll,
                interface, cidr, seeds, profiles, ranges, limits, recursive, recursive_profile,
                name, cycle, ref, jobref, approval, repeat, minutes):
        output = [no_update] * 10
        trigger = ctx.triggered_id
        try:
            output[8] = status_text(control.status())
            if trigger == 'poll':
                job = control.job((jobref or {}).get('id'))
                auto = control.job(control.status().get('last_collection'))
                if auto and ref and ref.get('pid') == pid and auto['project_id'] == pid and auto['serial'] > job.get('serial', -1) and cycle == 'latest' and auto['state'] in {'finished', 'failed', 'cancelled'}:
                    job = auto
                    jobref = {'id': auto['id'], 'handled': False}
                if job and job['state'] in {'finished', 'failed', 'cancelled'} and not (jobref or {}).get('handled'):
                    output[3] = {**jobref, 'handled': True}
                    if job.get('project_id') and job['project_id'] != pid:
                        return output
                    if job.get('error'):
                        output[6] = job['error']
                        return output
                    result = job.get('result') or {}
                    if result.get('project'):
                        output[0], output[1] = projects(control.root), result['project']
                        output[6] = 'Projekt gotowy. Wczytaj mapę, jeśli zawiera snapshot.'
                    if result.get('approval'):
                        output[4] = {'token': result['approval'], 'config': result['config']} if 'config' in result else {'token': result['approval']}
                        output[5] = preview_text(result['plan'], result['credentials'])
                        output[6] = 'Sprawdź zakres. Podgląd jest ważny przez 120 s i służy do jednego startu.'
                    if result.get('view'):
                        new_view = control.view(result['view'], pid)
                        # A historical view stays pinned when a newer collection finishes.
                        if job['label'] != 'Odkrywanie i topologia' or cycle == 'latest':
                            output[2] = {'key': result['view'], 'pid': pid}
                        output[7] = [{'label': 'Najnowszy wynik', 'value': 'latest'}] + [
                            {'label': s['started_at'] + ' · ' + s['coverage_status'], 'value': s['cycle_id']} for s in new_view['snapshots']]
                        output[6] = 'Wynik dostępny · ' + {'complete': 'pełny', 'partial': 'częściowy'}.get(result.get('coverage_status'), 'dane zapisane')
                return output
            if trigger in {'interface', 'cidr', 'seeds', 'profiles', 'ranges', 'limits', 'recursive', 'recursive-profile'}:
                control.invalidate()
                output[4], output[5] = None, 'Konfiguracja zmieniona — przygotuj nowy podgląd.'
                return output
            if trigger == 'project':
                control.invalidate()
                output[2], output[3], output[4] = None, None, None
                output[7] = [{'label': 'Najnowszy wynik', 'value': 'latest'}]
                output[9] = 'latest'
                output[5] = 'Wybierz zakres lub otwórz zapisany snapshot.'
                return output
            if trigger in {'create', 'demo', 'upload'}:
                control.invalidate()
                from ..cli import demo, project_create
                def local(_):
                    if trigger == 'upload':
                        return {'project': import_upload(control.root, upload, name or 'Import offline')}
                    result = demo(control.root) if trigger == 'demo' else project_create(control.root, name or 'Nowa sieć')
                    return {'project': result['project_id']}
                job_id = control.submit('Projekt / import offline', None, local)
            elif trigger == 'refresh-projects':
                output[0] = projects(control.root)
                return output
            elif trigger == 'load':
                job_id = control.load(pid, None if cycle == 'latest' else cycle)
            elif trigger in {'save', 'prepare'}:
                control.invalidate()
                cfg = form_config(pid, interface, cidr, seeds, profiles, ranges, limits, recursive, recursive_profile)
                save_config(control.root, pid, cfg)
                output[4] = None
                if trigger == 'save':
                    output[6] = 'Zapisano konfigurację bez sekretów. Nowy start wymaga podglądu.'
                    return output
                job_id = control.prepare(pid)
            elif trigger == 'start':
                # Compare the form again; a forged/late callback cannot reuse an old preview.
                cfg = form_config(pid, interface, cidr, seeds, profiles, ranges, limits, recursive, recursive_profile)
                if digest(cfg) != digest(config_read(control.root, pid)):
                    control.invalidate()
                    raise MapperError('CONFIG_CHANGED_PREVIEW_REQUIRED')
                job_id = control.start(pid, (approval or {}).get('token'), repeat_minutes=minutes if 'yes' in (repeat or []) else None)
                output[4] = None
            elif trigger == 'cancel':
                control.cancel(); output[6] = 'Anulowanie: czekam na zakończenie ograniczonych operacji.'
                return output
            elif trigger == 'disarm':
                control.disarm(); output[6] = 'Przyszłe starty wyłączone. Aktywny cykl ma osobne anulowanie.'
                return output
            else:
                return output
            output[3] = {'id': job_id, 'handled': False}
            output[6] = 'Zadanie uruchomione.'
        except (MapperError, OSError, ValueError, TypeError) as exc:
            output[6] = exc.code if isinstance(exc, MapperError) else 'LOCAL_OPERATION_FAILED'
        return output

    @app.callback(Output('map', 'elements'), Output('visible-count', 'children'), Output('snapshot-meta', 'children'),
                  Output('vlan', 'options'), Output('history', 'children'),
                  Input('view-ref', 'data'), Input('search', 'value'), Input('vlan', 'value'), Input('expand', 'value'), State('project', 'value'))
    def graph(ref, query, vlan, expand, pid):
        defaults = [{'label': 'Wszystkie VLAN-y', 'value': 'all'}, {'label': 'VLAN nieustalony', 'value': 'unknown'}]
        try:
            data = view(ref, pid); g = data['graph']
            elements, counts = project(g, query, vlan, 'yes' in (expand or []))
            stamp = next((s['started_at'] for s in data['snapshots'] if s['snapshot_id'] == g['snapshot_id']), '')
            meta = f"{stamp} · {g['snapshot_id'][:8]} · {g['origin']}"
            count = f"Widoczne urządzenia: {counts['nodes']}/{counts['all_nodes']} · relacje: {counts['edges']}/{counts['all_edges']}"
            if not counts['nodes']:
                count += ' · Brak wyników — wyczyść wyszukiwanie lub wybierz wszystkie VLAN-y.'
            return elements, count, meta, defaults + [{'label': f'VLAN {v}', 'value': str(v)} for v in vlans(g)], json.dumps({'zdarzenia': data['history'], 'ostrzeżenia': g['warnings']}, ensure_ascii=False, indent=2)
        except (MapperError, ValueError):
            return [], 'Wczytaj mapę.', '', defaults, ''

    @app.callback(Output('map', 'layout'), Input('layout', 'n_clicks'), Input('map', 'elements'))
    def arrange(clicks, elements):
        # Depend on rendered elements, not the view token: otherwise layout can
        # fit an empty graph before its parallel projection callback returns.
        count = sum('source' not in e['data'] for e in (elements or []))
        return {'name': 'circle', 'radius': max(220, min(1200, count * 16)), 'padding': 75,
                'animate': False, 'fit': True, '_mapper_revision': digest(elements or []) + str(clicks)}

    @app.callback(Output('details', 'children'), Input('map', 'tapNodeData'), Input('map', 'tapEdgeData'),
                  Input('view-ref', 'data'), State('project', 'value'))
    def show_details(node, edge, ref, pid):
        try:
            selected = edge if ctx.triggered_id == 'map' and ctx.triggered[0]['prop_id'].endswith('tapEdgeData') else node
            data = details(view(ref, pid)['graph'], (selected or {}).get('id'))
            evidence = data.pop('Dowody i ograniczenia', None)
            rows = []
            for label, value in data.items():
                if label == 'Przypisania switch / port / VLAN' and isinstance(value, list):
                    confidence = {'high':'wysoka', 'medium':'średnia', 'low':'niska', 'unknown':'nieustalona'}
                    value = html.Ul([html.Li([html.Span(f"{a['Switch']} · {a['Port']} · VLAN {a['VLAN']}"),
                        html.Br(), html.Small(a['Typ'] + ' · pewność ' + confidence.get(a['Pewność'], a['Pewność']) +
                        (' · uplink' if 'UPLINK' in a['Uzasadnienie'] else ''))]) for a in sorted(value, key=lambda a: a['Typ'] != 'przypisanie')])
                elif isinstance(value, bool):
                    value = 'Tak' if value else 'Nie — sprawdź świeżość dowodów'
                elif isinstance(value, list) and not any(isinstance(v, dict) for v in value):
                    value = ', '.join(str(v) for v in value) or 'nieustalone'
                elif isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                else:
                    value = str(value) if value is not None else 'nieustalone'
                rows += [html.Dt(label), html.Dd(value)]
            return html.Div([html.Dl(rows), html.Details([html.Summary('Surowe dowody i ograniczenia'), html.Pre(json.dumps(evidence, ensure_ascii=False, indent=2))])] if evidence else [html.Dl(rows)])
        except MapperError:
            return 'Wczytaj mapę i kliknij urządzenie lub połączenie.'

    @app.callback(Output('map', 'generateImage'), Input('png', 'n_clicks'), Input('svg', 'n_clicks'),
                  State('view-ref', 'data'), State('project', 'value'), prevent_initial_call=True)
    def image(_png, _svg, ref, pid):
        try:
            g = view(ref, pid)['graph']
            return {'type': ctx.triggered_id, 'action': 'download', 'filename': 'mapper-' + g['snapshot_id'][:8], 'options': {'full': False, 'bg': '#122130', 'scale': 2}}
        except MapperError:
            return no_update

    @app.callback(Output('cidr', 'value', allow_duplicate=True),
                  Output('interface-info', 'children', allow_duplicate=True),
                  Input('interface', 'value'), State('interface-facts', 'data'), State('cidr', 'value'), prevent_initial_call=True)
    def interface_default(interface, rows, cidr):
        import ipaddress
        candidates = [i for i in (rows or []) if i['interface'] == interface]
        if len(candidates) != 1:
            return no_update, 'Źródło nieustalone — sprawdź jednoznaczność adresu interfejsu w podglądzie.'
        i = candidates[0]
        prefix = str(ipaddress.IPv4Network(i['ip'] + '/' + i['netmask'], strict=False))
        return prefix if not cidr else no_update, f"Źródło {i['ip']} · maska {i['netmask']} · lokalna podsieć {prefix}"

    @app.callback(Output('start', 'disabled'), Input('approval', 'data'))
    def can_start(approval):
        return control.offline or not approval

    @app.callback(Output('search', 'value'), Output('vlan', 'value'), Output('expand', 'value'),
                  Input('clear-filters', 'n_clicks'), prevent_initial_call=True)
    def clear_filters(_):
        return '', 'all', []

    @app.callback(Output('download', 'data'), Output('export-status', 'children'),
                  Input('export', 'n_clicks'), Input('download-data', 'n_clicks'), State('format', 'value'),
                  State('view-ref', 'data'), State('project', 'value'), prevent_initial_call=True)
    def exports(_private, _download, kind, ref, pid):
        try:
            g = view(ref, pid)['graph']
            path = export_private(control.root, pid, g, kind)
            if ctx.triggered_id == 'download-data':
                return dcc.send_file(str(path)), 'Zapisano prywatny oryginał; pobrana kopia ma uprawnienia przeglądarki.'
            return no_update, 'Prywatny eksport: ' + str(path)
        except (MapperError, OSError) as exc:
            return no_update, exc.code if isinstance(exc, MapperError) else 'EXPORT_FAILED'
    return app
