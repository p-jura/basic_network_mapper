"""Pure derivation from a v1 snapshot. No system, SNMP or SSH adapters."""
from collections import defaultdict
import ipaddress
import networkx as nx

from ..errors import MapperError
from .identity import identity, context
from .confidence import assess

RULES_VERSION = '1'


def derive(data, *, max_skew=300):
    if type(max_skew) is not int or not 1 <= max_skew <= 86400:
        raise MapperError('INVALID_TIME_WINDOW')
    project = data['project_id']
    runs = {r['collector_run_id']: r for r in data['runs']}
    facts = data['observations']
    fact_index = {o['observation_id']: o for o in facts}
    nodes, edges, warnings = {}, {}, {}
    grouped = defaultdict(list)
    warning_codes = defaultdict(set)
    for o in facts:
        r = runs[o['collector_run_id']]
        grouped[(r['target_id'], context(r))].append(o)

    def warn(code, subject, evidence=()):
        key = identity(project, 'warning', code, subject)
        warning_codes[subject].add(code)
        old = warnings.get(key, {}).get('observation_ids', [])
        warnings[key] = {'id': key, 'code': code, 'subject_id': subject, 'observation_ids': sorted(set(evidence) | set(old))}

    def node(kind, ctx, key, **attrs):
        nid = identity(project, kind, ctx, key)
        if nid not in nodes:
            nodes[nid] = {'id': nid, 'project_id': project, 'kind': kind, 'context': ctx,
                          'identity_key': [kind, ctx, key], 'ips': [], 'macs': [], 'names': [],
                          'evidence': [], 'fresh_presence': False, 'last_seen': None,
                          'port': None, 'vlan_id': None, 'switch_id': None,
                          'confidence': 'unknown', 'classification_confidence': 'unknown', **attrs}
        return nodes[nid]

    def evidence(n, obs, *, presence=False):
        for o in obs:
            oid = o['observation_id']
            if oid not in n['evidence']:
                n['evidence'].append(oid)
            n['last_seen'] = max(n['last_seen'] or o['observed_at'], o['observed_at'])
        if presence:
            n['fresh_presence'] = True

    def edge(kind, source, target, key, **attrs):
        eid = identity(project, 'edge', kind, source, target, key)
        edges[eid] = {'id': eid, 'kind': kind, 'source': source, 'target': target, **attrs}
        return edges[eid]

    def local_scope_matches(run, payload):
        try:
            iface, prefix = run['scope_id'].split(':', 1)
            return payload.get('interface') == iface and ipaddress.IPv4Address(payload['ip']) in ipaddress.IPv4Network(prefix)
        except (ValueError, KeyError):
            return False

    def valid_ipmac(o):
        p = o['payload']
        # RFC 4293 invalid(2), incomplete(7); RFC 1213 invalid(2).
        return bool(p.get('mac')) and p.get('entry_type') not in {2, 'invalid'} and p.get('state') not in {2, 7, 'invalid', 'incomplete', 'failed'}

    # Per-context IP/MAC pairs prevent proxy ARP from collapsing many IPs.
    pairs = defaultdict(lambda: defaultdict(list))
    for o in facts:
        r = runs[o['collector_run_id']]
        if o['kind'] in {'neighbor', 'ip_mac'} and valid_ipmac(o) and (o['kind'] != 'neighbor' or local_scope_matches(r, o['payload'])):
            pairs[context(r)][(o['payload']['ip'], o['payload']['mac'])].append(o)
    endpoints_by_mac = defaultdict(list)
    endpoints_by_ip = defaultdict(list)
    for ctx, entries in sorted(pairs.items()):
        for (ip, mac), obs in sorted(entries.items()):
            n = node('endpoint', ctx, [ip, mac], ips=[ip], macs=[mac], provisional=False)
            evidence(n, obs, presence=any(o['freshness'] == 'fresh' for o in obs))
            endpoints_by_mac[(ctx, mac)].append(n)
            endpoints_by_ip[(ctx, ip)].append(n)
        mac_ips = defaultdict(set)
        ip_macs = defaultdict(set)
        for ip, mac in entries:
            mac_ips[mac].add(ip); ip_macs[ip].add(mac)
        for (ip, mac) in entries:
            n = endpoints_by_ip[(ctx, ip)]
            if len(mac_ips[mac]) > 1:
                for x in n:
                    warn('SHARED_MAC_OR_PROXY_ARP', x['id'], x['evidence'])
            if len(ip_macs[ip]) > 1:
                for x in n:
                    warn('IP_MAC_CONFLICT', x['id'], x['evidence'])

    # Local segment, replies and routes are logical, never fabricated cables.
    segments = {}
    probes = defaultdict(dict)
    for o in facts:
        r, p = runs[o['collector_run_id']], o['payload']
        if r['target_id'] is not None:
            continue
        ctx = context(r)
        if ctx not in segments:
            segments[ctx] = node('segment', ctx, r['scope_id'], label=r['scope_id'])
        seg = segments[ctx]
        if o['kind'] == 'local_interface':
            # interfaces table may contain unrelated VPN/loopback adapters.
            selected_iface = r['scope_id'].split(':', 1)[0]
            if p['interface'] != selected_iface or not local_scope_matches(r, p):
                continue
            n = node('local_interface', ctx, [p['interface'], p['ip']], ips=[p['ip']], interface=p['interface'])
            evidence(n, [o], presence=True)
        elif o['kind'] == 'probe_result':
            if not local_scope_matches(r, p):
                continue
            probes[ctx][p['ip']] = p['result']
            if p['result'] != 'reply':
                continue
            matches = endpoints_by_ip[(ctx, p['ip'])]
            if len(matches) == 1:
                n = matches[0]
            else:
                n = node('endpoint', ctx, [p['ip'], None], ips=[p['ip']], provisional=True)
                if matches:
                    warn('IP_MAC_CONFLICT', n['id'], [o['observation_id']])
            evidence(n, [o], presence=True)
        elif o['kind'] == 'neighbor':
            for n in endpoints_by_ip[(ctx, p['ip'])]:
                edge('logical_membership', n['id'], seg['id'], '', confidence='unknown', observation_ids=n['evidence'])
            continue
        elif o['kind'] == 'route' and p.get('next_hop') and p['interface'] == r['scope_id'].split(':', 1)[0]:
            # Route may refer to an off-link gateway. Keep only the selected LAN.
            try:
                network = ipaddress.IPv4Network(r['scope_id'].split(':', 1)[1])
                if ipaddress.IPv4Address(p['next_hop']) not in network:
                    continue
            except (ValueError, IndexError):
                continue
            matches = endpoints_by_ip[(ctx, p['next_hop'])]
            n = matches[0] if len(matches) == 1 else node('gateway_candidate', ctx, p['next_hop'], ips=[p['next_hop']], provisional=True)
            n['gateway_by_route'] = True
            evidence(n, [o])
        else:
            continue
        edge('logical_membership', n['id'], seg['id'], '', confidence='unknown', observation_ids=list(n['evidence']))

    targets = {t['target_id']: t for t in data['targets']}
    source_nodes = {}
    interfaces, bridges, vlans, port_config = {}, {}, {}, {}
    vlan_by_fdb, vlan_by_port = {}, {}
    for (target, ctx), obs in sorted(grouped.items(), key=lambda item: str(item[0])):
        if target is None:
            continue
        t = targets[target]
        src = node('collection_endpoint', ctx, target, ips=[t['ip']], collection_target_id=target,
                   label=t['ip'], classification_confidence='low')
        source_nodes[(target, ctx)] = src
        iface, bridge, vlan, pc = defaultdict(list), defaultdict(list), [], defaultdict(list)
        for o in obs:
            p = o['payload']
            if o['kind'] == 'device_identity':
                evidence(src, [o])
                if p.get('name') and p['name'] not in src['names']:
                    src['names'].append(p['name'])
            elif o['kind'] == 'interface' and p.get('if_index'):
                iface[p['if_index']].append(o)
                if p.get('mac') and p['mac'] not in src['macs']:
                    src['macs'].append(p['mac'])
            elif o['kind'] == 'bridge_port_map':
                bridge[p['bridge_port']].append(o)
            elif o['kind'] == 'vlan':
                vlan.append(o)
            elif o['kind'] == 'port_vlan':
                pc[p['bridge_port']].append(o)
        key = (target, ctx)
        interfaces[key], bridges[key], vlans[key], port_config[key] = iface, bridge, vlan, pc
        vlan_by_fdb[key], vlan_by_port[key] = defaultdict(list), defaultdict(list)
        for v in vlan:
            vp = v['payload']
            if vp.get('fdb_id') is not None:
                vlan_by_fdb[key][vp['fdb_id']].append(v)
            for bp in vp.get('egress_ports') or []:
                vlan_by_port[key][bp].append(v)

    def decode_id(value, subtype):
        if not value:
            return None
        try:
            raw = bytes.fromhex(value[4:]) if value.startswith('hex:') else value.encode()
            if subtype == 3:  # portId MAC subtype
                return ':'.join(f'{b:02x}' for b in raw) if len(raw) == 6 else None
            return raw.decode('utf-8') if subtype in {1, 5} else None
        except (ValueError, UnicodeError):
            return None

    def port_match(key, value, subtype):
        decoded = decode_id(value, subtype)
        if decoded is None:
            return None, []
        field = {1: 'alias', 3: 'mac', 5: 'name'}.get(subtype)
        matches = [(i, obs) for i, obs in interfaces[key].items() if any(o['payload'].get(field) == decoded for o in obs)]
        return matches[0] if len(matches) == 1 else (None, [])

    infrastructure = nx.MultiGraph()
    uplinks = set()
    infrastructure_proofs = defaultdict(list)
    unresolved_lldp = set()
    # Join LLDP address and neighbor records by full LLDP row index.
    for key, obs in grouped.items():
        if key not in source_nodes:
            continue
        remotes = defaultdict(list)
        local = defaultdict(list)
        for o in obs:
            p = o['payload']
            if o['kind'] == 'lldp_neighbor':
                remotes[(p.get('time_mark'), p['local_port_num'], p.get('remote_index'))].append(o)
            elif o['kind'] == 'lldp_local_port':
                local[p['local_port_num']].append(o)
        for index, records in remotes.items():
            combined = {}
            for o in records:
                combined.update({k: v for k, v in o['payload'].items() if v is not None})
            chassis = combined.get('remote_chassis_id')
            subtype = combined.get('remote_chassis_subtype')
            # chassis MAC subtype=4; port MAC subtype=3.
            chassis_mac = decode_id(chassis, 3) if subtype == 4 else None
            matched = [(k, s) for k, s in source_nodes.items() if k != key and k[1] == key[1]
                       and chassis_mac and chassis_mac in s['macs']
                       and (not combined.get('management_ip') or combined['management_ip'] in s['ips'])]
            if len(matched) == 1:
                remote_key, remote = matched[0]
            else:
                remote_key = None
                remote = node('lldp_neighbor', key[1], [key[0], subtype, chassis, index[1], combined.get('remote_port_id'), index[2] if not chassis else None],
                              ips=[combined['management_ip']] if combined.get('management_ip') else [],
                              names=[combined['name']] if combined.get('name') else [], classification_confidence='low')
                warn('CHASSIS_IDENTITY_UNRESOLVED', remote['id'], [o['observation_id'] for o in records])
            evidence(remote, records)
            loc = {}
            loc_obs = local.get(index[1], [])
            for o in loc_obs:
                loc.update(o['payload'])
            ifindex, ifobs = port_match(key, loc.get('local_port_id') or combined.get('local_port_id'), loc.get('local_port_subtype'))
            remote_port, remote_ifobs = port_match(remote_key, combined.get('remote_port_id'), combined.get('remote_port_subtype')) if remote_key else (None, [])
            chassis_proofs = [o for o in grouped.get(remote_key, []) if o['kind'] == 'interface' and o['payload'].get('mac') == chassis_mac]
            proofs = records + loc_obs + ifobs + remote_ifobs + chassis_proofs
            reasons = [] if ifindex else ['PORT_MAPPING_MISSING']
            score = assess(proofs, [runs[o['collector_run_id']] for o in proofs], max_skew, reasons)
            e = edge('lldp_adjacency', source_nodes[key]['id'], remote['id'], [ifindex, combined.get('remote_port_id'), index[1]],
                     local_port={'local_port_num': index[1], 'if_index': ifindex},
                     remote_port={'raw_id': combined.get('remote_port_id'), 'subtype': combined.get('remote_port_subtype'), 'if_index': remote_port},
                     confidence=score['level'], reasons=score['reasons'], observation_ids=score['observation_ids'])
            infrastructure_proofs[key].extend(proofs)
            if remote_key:
                infrastructure_proofs[remote_key].extend(proofs)
            if not ifindex:
                unresolved_lldp.add(key)
            if ifindex:
                uplinks.add((key, ifindex))
            if remote_key and score['level'] not in {'low', 'unknown'}:
                infrastructure.add_edge(source_nodes[key]['id'], remote['id'], key=e['id'])
                if remote_port:
                    uplinks.add((remote_key, remote_port))

    simple = nx.Graph(infrastructure)
    # cycle_basis is bounded by graph size; do not enumerate all simple cycles.
    for cycle in nx.cycle_basis(simple):
        warn('GRAPH_CYCLE_NOT_PROOF_OF_LOOP', min(cycle))
    for a, b in simple.edges:
        if infrastructure.number_of_edges(a, b) > 1:
            # Bidirectional LLDP reads of one link are not redundant cables.
            links = [e for e in edges.values() if e['kind'] == 'lldp_adjacency' and {e['source'], e['target']} == {a, b}]
            signatures = set()
            for e in links:
                x, y = e['local_port']['if_index'], e['remote_port']['if_index']
                if x and y:
                    signatures.add((x, y) if e['source'] == a else (y, x))
            if len(signatures) > 1:
                warn('REDUNDANT_LINKS_AGGREGATION_UNKNOWN', a)

    candidates = defaultdict(dict)
    port_macs = defaultdict(set)
    for key, obs in grouped.items():
        if key not in source_nodes:
            continue
        for o in obs:
            if o['kind'] != 'fdb_entry' or not o['payload'].get('mac'):
                continue
            p = o['payload']
            if p.get('status') in {1, 2, 4, 'invalid', 'self'} or p.get('bridge_port') == 0:
                warn('INVALID_FDB', source_nodes[key]['id'], [o['observation_id']]); continue
            bridge_obs = bridges[key].get(p.get('bridge_port'), [])
            indices = {b['payload']['if_index'] for b in bridge_obs if b['payload'].get('if_index')}
            if p.get('if_index'):
                indices.add(p['if_index'])
            reasons = [] if data['snapshot']['coverage_status'] == 'complete' else ['PARTIAL_CYCLE']
            if len(indices) > 1:
                reasons.append('PORT_MAPPING_CONFLICT')
            ifindex = next(iter(indices)) if len(indices) == 1 else None
            ifobs = interfaces[key].get(ifindex, [])
            # SSH reports an actual port name, retained without a fabricated index.
            name = p.get('port_name')
            if not ifindex and not name:
                reasons.append('PORT_MAPPING_MISSING')
            if ifindex and not ifobs:
                reasons.append('PORT_MAPPING_MISSING')
            vlan_obs = vlan_by_fdb[key].get(p.get('fdb_id'), [])
            vlan_ids = {p['vlan_id']} if p.get('vlan_id') else {v['payload']['vlan_id'] for v in vlan_obs}
            if len(vlan_ids) != 1:
                reasons.append('VLAN_AMBIGUOUS' if vlan_ids else 'VLAN_UNKNOWN')
            vlan_id = next(iter(vlan_ids)) if len(vlan_ids) == 1 else None
            if not key[1].startswith('known:'):
                reasons.append('CONTEXT_UNKNOWN')
            # Port metadata belongs to this bridge/context, never substitutes for FDB VLAN.
            pcobs = [v for v in port_config[key].get(p.get('bridge_port'), []) if p.get('bridge_port') is not None or (name and v['payload'].get('port_name') == name)]
            tagged, untagged = set(), set()
            for v in vlan_by_port[key].get(p.get('bridge_port'), []):
                vp = v['payload']
                if p.get('bridge_port') in (vp.get('egress_ports') or []):
                    (untagged if p.get('bridge_port') in (vp.get('untagged_ports') or []) else tagged).add(vp['vlan_id'])
            mode = next((v['payload']['mode'] for v in pcobs if v['payload'].get('mode') not in {None, 'unknown'}), 'unknown')
            port = {'bridge_port': p.get('bridge_port'), 'if_index': ifindex, 'name': name or next((v['payload']['name'] for v in ifobs if v['payload'].get('name')), None),
                    'mode': mode, 'pvid': next((v['payload'].get('pvid') for v in pcobs if v['payload'].get('pvid')), None),
                    'tagged_vlans': sorted(tagged), 'untagged_vlans': sorted(untagged)}
            pk = ifindex or name or ('unmapped:' + str(p.get('bridge_port')))
            port_macs[(key, str(pk))].add(p['mac'])
            endpoints = endpoints_by_mac[(key[1], p['mac'])]
            if not endpoints:
                n = node('endpoint', key[1], [None, p['mac']], macs=[p['mac']], provisional=True)
                endpoints = [n]
                endpoints_by_mac[(key[1], p['mac'])] = endpoints
            for n in endpoints:
                arp = [x for x in (fact_index[oid] for oid in n['evidence']) if x['kind'] in {'neighbor', 'ip_mac'}]
                proofs = [o] + bridge_obs + ifobs + vlan_obs + pcobs + arp + infrastructure_proofs[key]
                more = list(reasons)
                if key in unresolved_lldp:
                    more.append('UNRESOLVED_LLDP_PORT')
                if mode == 'trunk':
                    more.append('TRUNK_BOUNDARY')
                if len(endpoints) > 1:
                    more.append('SHARED_MAC_OR_PROXY_ARP')
                if 'IP_MAC_CONFLICT' in warning_codes[n['id']]:
                    more.append('IP_MAC_CONFLICT')
                if (key, ifindex) in uplinks and ifindex is not None:
                    more.append('UPLINK')
                score = assess(proofs, [runs[x['collector_run_id']] for x in proofs], max_skew, more)
                ck = (source_nodes[key]['id'], str(pk), vlan_id)
                c = {'switch_id': source_nodes[key]['id'], 'target_id': key[0], 'port': port, 'vlan_id': vlan_id,
                     'vlan_candidates': sorted(vlan_ids), 'confidence': score['level'], 'reasons': score['reasons'],
                     'observation_ids': score['observation_ids'], 'uplink': 'UPLINK' in more}
                if ck in candidates[n['id']]:
                    old = candidates[n['id']][ck]
                    c['observation_ids'] = sorted(set(c['observation_ids'] + old['observation_ids']))
                    c['reasons'] = sorted(set(c['reasons'] + old['reasons']))
                    # Duplicate legacy/Q-BRIDGE data cannot upgrade weaker evidence.
                    if old['confidence'] == 'low':
                        c['confidence'] = 'low'
                candidates[n['id']][ck] = c
                evidence(n, [o])

    for nid, options in sorted(candidates.items()):
        choices = list(options.values())
        # A proven LLDP route may remove an upstream candidate; counts alone cannot.
        for c in choices:
            c['mac_count'] = len(port_macs[((c['target_id'], nodes[c['switch_id']]['context']), str(c['port']['if_index'] or c['port']['name'] or ('unmapped:' + str(c['port']['bridge_port']))))])
            if c['mac_count'] > 1:
                c['reasons'] = sorted(set(c['reasons']) | {'MULTIPLE_MAC_BOUNDARY'})
                if c['confidence'] == 'high':
                    c['confidence'] = 'medium'
        viable = [c for c in choices if not c['uplink'] and c['confidence'] in {'high', 'medium'}
                  and c['vlan_id'] is not None and not {'SHARED_MAC_OR_PROXY_ARP', 'IP_MAC_CONFLICT', 'UNRESOLVED_LLDP_PORT'} & set(c['reasons'])]
        chosen = viable[0] if len(viable) == 1 else None
        if len(viable) > 1:
            warn('ATTACHMENT_CONFLICT', nid, [oid for c in choices for oid in c['observation_ids']])
        for c in choices:
            kind = 'attachment' if c is chosen else 'attachment_candidate'
            edge(kind, nid, c['switch_id'], [c['port'], c['vlan_id']], **{k: v for k, v in c.items() if k != 'switch_id'},
                 boundary='MAC observed behind port; intermediate devices may be invisible')
            for reason in c['reasons']:
                if reason != 'CACHE_AGE_UNKNOWN':
                    warn(reason, nid, c['observation_ids'])
        if chosen:
            nodes[nid].update(switch_id=chosen['switch_id'], port=chosen['port'], vlan_id=chosen['vlan_id'], confidence=chosen['confidence'])
        nodes[nid]['candidates'] = sorted(choices, key=lambda c: (c['switch_id'], str(c['port']), str(c['vlan_id'])))

    for r in runs.values():
        if r['status'] not in {'ok', 'empty', 'not_requested'} or not r['exhausted']:
            warn('PARTIAL_SOURCE', r['target_id'] or r['scope_id'])
    # Endpoint history uses only successful explicit ICMP coverage for absence.
    coverage = {}
    for r in runs.values():
        if r['source'] != 'icmp' or r['table_name'] != 'host_discovery':
            continue
        ctx = context(r)
        if r['status'] in {'ok', 'empty'} and r['exhausted'] and data['cycle']['execution_status'] == 'finished':
            coverage[ctx] = {'results': probes[ctx], 'source': 'icmp', 'interface_scope': r['scope_id'], 'collector_run_id': r['collector_run_id']}
    # Preserve useful raw VLAN/IF facts in the derived export without inventing values.
    metadata = [{'observation_id': o['observation_id'], 'kind': o['kind'], 'source': runs[o['collector_run_id']]['source'],
                 'target_id': runs[o['collector_run_id']]['target_id'], 'context': context(runs[o['collector_run_id']]),
                 'observed_at': o['observed_at'], 'evidence_at': o['evidence_at'], 'freshness': o['freshness'],
                 'payload': o['payload']} for o in facts if o['kind'] != 'probe_result' or o['payload']['result'] == 'reply']
    for n in nodes.values():
        n['evidence'].sort(); n['macs'].sort(); n['names'].sort()
        if n['kind'] == 'endpoint':
            n['presence'] = 'fresh_response' if n['fresh_presence'] else 'cache_or_table_observation'
    return {'schema_version': 1, 'format': 'mapper-topology', 'rules_version': RULES_VERSION + ':skew=' + str(max_skew),
            'project_id': project, 'snapshot_id': data['snapshot']['snapshot_id'], 'cycle_id': data['cycle']['cycle_id'],
            'started_at': data['cycle']['started_at'], 'finished_at': data['cycle']['finished_at'],
            'origin': data['cycle']['origin'], 'max_source_skew_seconds': max_skew,
            'comparison_scopes': [list(v) for v in sorted({(r['source'], r['table_name'], r['target_id'], r['scope_id'], r['context_id'], r['context_status']) for r in runs.values()}, key=str)],
            'coverage_status': data['snapshot']['coverage_status'],
            'sends_probes': False, 'nodes': sorted(nodes.values(), key=lambda n: n['id']),
            'edges': sorted(edges.values(), key=lambda e: e['id']), 'warnings': sorted(warnings.values(), key=lambda w: w['id']),
            'evidence': metadata, 'presence_coverage': coverage}
