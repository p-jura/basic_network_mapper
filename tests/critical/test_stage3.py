"""Critical inference/persistence contracts. Synthetic IPv4 only; no network."""
from contextlib import closing
from datetime import datetime, timedelta, timezone
import json
import re
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

from mapper.cli import demo, main
from mapper.models import Observation, TableResult, new_id
from mapper.storage import Repository
from mapper.topology.engine import derive
from mapper.topology.history import advance
from mapper.topology.service import build, history

T0 = datetime(2026, 10, 23, 8, tzinfo=timezone.utc)
MAC = '02:00:00:00:00:20'


def stamp(minute=0):
    return (T0 + timedelta(minutes=minute)).isoformat().replace('+00:00', 'Z')


class Fixture:
    def __init__(self, project=None, minute=0):
        self.project = project or new_id()
        self.minute = minute
        self.data = {'schema_version': 1, 'project_id': self.project,
                     'snapshot': {'snapshot_id': new_id(), 'coverage_status': 'complete'},
                     'cycle': {'cycle_id': new_id(), 'started_at': stamp(minute), 'finished_at': stamp(minute), 'execution_status': 'finished', 'origin': 'synthetic'},
                     'targets': [], 'runs': [], 'observations': []}

    def target(self, ip):
        tid = str(uuid4())
        self.data['targets'].append({'target_id': tid, 'ip': ip, 'port': 161, 'context_id': 'blue', 'profile_id': 'fixture', 'origin': 'seed', 'project_id': self.project})
        return tid

    def add(self, kind, payload, *, target=None, ctx='blue', status='ok', fresh='fresh', minute=None, source=None, table=None, scope='fixture0:192.0.2.0/24'):
        rid = new_id()
        source = source or ('snmp' if target else 'os_neighbors')
        run = {'collector_run_id': rid, 'cycle_id': self.data['cycle']['cycle_id'], 'target_id': target,
               'source': source, 'table_name': table or kind, 'scope_id': scope,
               'context_id': ctx if target else '', 'context_status': 'known' if target else 'default',
               'started_at': stamp(self.minute), 'finished_at': stamp(self.minute), 'status': status,
               'exhausted': status in {'ok', 'empty'}, 'reason': None, 'record_count': 1}
        self.data['runs'].append(run)
        obs = {'observation_id': new_id(), 'collector_run_id': rid, 'kind': kind, 'source_key': new_id(),
               'observed_at': stamp(self.minute if minute is None else minute), 'freshness': fresh, 'evidence_at': None, 'payload': payload}
        self.data['observations'].append(obs)
        return obs

    def managed(self, target, host_port=101, uplink=False, shared=False, fresh='fresh', minute=None, ctx='blue'):
        self.add('interface', {'if_index': host_port, 'name': f'Gi{host_port}', 'mac': '02:00:00:00:10:01'}, target=target, ctx=ctx)
        self.add('bridge_port_map', {'bridge_port': 12, 'if_index': host_port}, target=target, ctx=ctx)
        self.add('vlan', {'vlan_id': 10, 'fdb_id': 7, 'egress_ports': [12], 'untagged_ports': [12]}, target=target, ctx=ctx)
        if shared:
            self.add('vlan', {'vlan_id': 20, 'fdb_id': 7}, target=target, ctx=ctx)
        self.add('ip_mac', {'ip': '192.0.2.20', 'mac': MAC, 'if_index': host_port}, target=target, ctx=ctx, fresh=fresh, minute=minute)
        self.add('fdb_entry', {'mac': MAC, 'bridge_port': 12, 'fdb_id': 7, 'status': 3}, target=target, ctx=ctx, fresh=fresh, minute=minute)

    def basic(self, reply=True, *, mac=MAC, status='ok', scope='fixture0:192.0.2.0/24', cache=True):
        self.add('local_interface', {'interface': 'fixture0', 'ip': '192.0.2.1', 'netmask': '255.255.255.0', 'is_up': True}, source='os_interfaces', scope=scope)
        if cache:
            self.add('neighbor', {'ip': '192.0.2.20', 'mac': mac, 'interface': 'fixture0', 'state': 'cached'}, fresh='cached', scope=scope)
        self.add('probe_result', {'ip': '192.0.2.20', 'interface': 'fixture0', 'result': 'reply' if reply else 'no_reply'},
                 source='icmp', table='host_discovery', status=status, scope=scope)
        return self


def endpoints(g):
    return [n for n in g['nodes'] if n['kind'] == 'endpoint']


class TopologyTests(unittest.TestCase):
    def test_basic_no_fabricated_cables_and_incomplete_neighbors(self):
        f = Fixture().basic()
        f.add('neighbor', {'ip': '192.0.2.30', 'mac': None, 'interface': 'fixture0', 'state': 'incomplete'})
        g = derive(f.data)
        self.assertEqual(len(endpoints(g)), 1)
        self.assertTrue(endpoints(g)[0]['fresh_presence'])
        self.assertIsNone(endpoints(g)[0]['port'])
        self.assertIsNone(endpoints(g)[0]['vlan_id'])
        self.assertEqual({e['kind'] for e in g['edges']}, {'logical_membership'})
        f.data['runs'][1]['context_status'] = 'unknown'
        self.assertFalse(g['sends_probes'])

    def test_lldp_proved_uplink_leaves_access_port_and_subtype_mapping(self):
        f = Fixture()
        upstream, leaf = f.target('192.0.2.2'), f.target('192.0.2.3')
        f.managed(upstream, host_port=900)
        f.managed(leaf, host_port=101)
        f.add('interface', {'if_index': 924, 'name': 'Gi24', 'mac': '02:00:00:00:10:03'}, target=leaf)
        f.add('lldp_local_port', {'local_port_num': 5, 'local_port_id': 'hex:4769393030', 'local_port_subtype': 5}, target=upstream)
        f.add('lldp_neighbor', {'local_port_num': 5, 'remote_index': 1, 'time_mark': 0,
                              'remote_chassis_id': 'hex:020000001003', 'remote_chassis_subtype': 4,
                              'remote_port_id': 'hex:47693234', 'remote_port_subtype': 5,
                              'management_ip': '192.0.2.3'}, target=upstream)
        g = derive(f.data)
        n = endpoints(g)[0]
        self.assertEqual(n['port']['if_index'], 101)
        self.assertEqual(n['port']['bridge_port'], 12)
        self.assertEqual(n['vlan_id'], 10)
        self.assertEqual(n['confidence'], 'high')
        self.assertEqual(len([e for e in g['edges'] if e['kind'] == 'attachment']), 1)
        self.assertEqual(len([e for e in g['edges'] if e['kind'] == 'attachment_candidate']), 1)
        link = next(e for e in g['edges'] if e['kind'] == 'lldp_adjacency')
        self.assertEqual(link['local_port']['if_index'], 900)
        self.assertNotEqual(link['local_port']['if_index'], 5)
        # MAC count alone never disambiguates the two ports.
        f.data['observations'] = [o for o in f.data['observations'] if not o['kind'].startswith('lldp')]
        g = derive(f.data)
        self.assertIsNone(endpoints(g)[0]['port'])
        self.assertIn('ATTACHMENT_CONFLICT', {w['code'] for w in g['warnings']})

    def test_shared_fdb_and_stale_proofs_never_become_confirmed_port_move(self):
        f = Fixture(); t = f.target('192.0.2.2'); f.managed(t, shared=True)
        g = derive(f.data)
        self.assertIsNone(endpoints(g)[0]['vlan_id'])
        self.assertEqual(endpoints(g)[0]['candidates'][0]['vlan_candidates'], [10, 20])
        self.assertIn('VLAN_AMBIGUOUS', {w['code'] for w in g['warnings']})
        f = Fixture(); t = f.target('192.0.2.2'); f.managed(t, minute=-10)
        g = derive(f.data)
        self.assertIsNone(endpoints(g)[0]['port'])
        self.assertIn('TIME_SKEW', {w['code'] for w in g['warnings']})
        f = Fixture(); t = f.target('192.0.2.2'); f.managed(t, fresh='cached')
        self.assertEqual(endpoints(derive(f.data))[0]['confidence'], 'medium')

    def test_identity_project_vrf_proxy_and_dhcp(self):
        f = Fixture(); a, b = f.target('192.0.2.2'), f.target('192.0.2.3')
        f.managed(a, ctx='blue'); f.managed(b, ctx='red')
        self.assertEqual(len(endpoints(derive(f.data))), 2)
        f = Fixture().basic(); g1 = derive(f.data)
        other = Fixture().basic(); g2 = derive(other.data)
        self.assertNotEqual(endpoints(g1)[0]['id'], endpoints(g2)[0]['id'])
        f.add('neighbor', {'ip': '192.0.2.21', 'mac': MAC, 'interface': 'fixture0', 'state': 'cached'})
        g = derive(f.data)
        self.assertEqual(len(endpoints(g)), 2)
        self.assertIn('SHARED_MAC_OR_PROXY_ARP', {w['code'] for w in g['warnings']})
        changed = Fixture(f.project).basic(mac='02:00:00:00:00:99')
        self.assertNotEqual(endpoints(g1)[0]['id'], endpoints(derive(changed.data))[0]['id'])

    def test_history_threshold_errors_partial_scope_cache_and_return(self):
        project = new_id()
        g = advance(derive(Fixture(project).basic().data))
        for minute, status, scope in [(5, 'timeout', 'fixture0:192.0.2.0/24'), (10, 'ok', 'vpn0:192.0.2.0/24')]:
            f = Fixture(project, minute).basic(False, status=status, scope=scope)
            g = advance(derive(f.data), g)
            self.assertNotIn('prolonged_unobserved', {e['kind'] for e in g['events']})
        for minute in [15, 30]:
            f = Fixture(project, minute).basic(False)
            g = advance(derive(f.data), g)
            self.assertNotIn('prolonged_unobserved', {e['kind'] for e in g['events']})
        f = Fixture(project, 45).basic(False)
        g = advance(derive(f.data), g)
        event = next(e for e in g['events'] if e['kind'] == 'prolonged_unobserved')
        self.assertFalse(event['detail']['physical_disconnection_proven'])
        g = advance(derive(Fixture(project, 50).basic().data), g)
        self.assertIn('returned', {e['kind'] for e in g['events']})
        # A partial cycle with successful ICMP still cannot increment misses.
        f = Fixture(project, 60).basic(False); f.data['snapshot']['coverage_status'] = 'partial'
        g = advance(derive(f.data), g)
        self.assertTrue(all(s['misses'] == 0 for s in g['history_state'].values() if s['context'].startswith('local:fixture0')))

    def test_port_change_flapping_and_weak_observation_break(self):
        project, target = new_id(), new_id()
        g = None
        for minute, port in enumerate([101, 102, 101, 102]):
            f = Fixture(project, minute)
            f.data['targets'] = [{'target_id': target, 'ip': '192.0.2.2'}]
            f.managed(target, host_port=port)
            g = advance(derive(f.data), g)
        self.assertIn('suspected_mac_flapping', {e['kind'] for e in g['events']})
        self.assertIn('port_changed', {e['kind'] for e in g['events']})
        f = Fixture(project, 5); f.data['targets'] = [{'target_id': target, 'ip': '192.0.2.2'}]; f.managed(target, host_port=103, fresh='cached')
        g = advance(derive(f.data), g)
        self.assertNotIn('port_changed', {e['kind'] for e in g['events']})

    def test_cycle_warning_does_not_claim_active_loop(self):
        f = Fixture()
        ts = [f.target('192.0.2.' + str(i + 2)) for i in range(3)]
        for i, t in enumerate(ts):
            f.add('interface', {'if_index': 10 + i, 'name': f'Gi{i}', 'mac': f'02:00:00:00:10:0{i}'}, target=t)
        for i, t in enumerate(ts):
            remote = (i + 1) % 3
            f.add('lldp_local_port', {'local_port_num': i, 'local_port_id': f'Gi{i}', 'local_port_subtype': 5}, target=t)
            f.add('lldp_neighbor', {'local_port_num': i, 'remote_index': 1, 'time_mark': 0, 'remote_chassis_id': f'hex:02000000100{remote}', 'remote_chassis_subtype': 4, 'remote_port_id': f'Gi{remote}', 'remote_port_subtype': 5}, target=t)
        codes = {w['code'] for w in derive(f.data)['warnings']}
        self.assertIn('GRAPH_CYCLE_NOT_PROOF_OF_LOOP', codes)
        self.assertNotIn('suspected_mac_flapping', codes)


class PersistenceTests(unittest.TestCase):
    def test_migration_backup_rollback_and_replay_idempotence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); project = new_id(); folder = root / project; folder.mkdir()
            db = sqlite3.connect(folder / 'mapper.sqlite3')
            db.executescript((Path(__file__).parents[2] / 'src/mapper/storage/migrations/001_initial.sql').read_text())
            db.execute('INSERT INTO project_meta VALUES (?,?,?)', (project, 'Legacy', stamp())); db.commit(); db.close()
            with Repository(root, project) as repo:
                backup = repo.migration_backup
                self.assertEqual(repo.db.execute('PRAGMA user_version').fetchone()[0], 2)
                self.assertEqual(repo.db.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
            with closing(sqlite3.connect(backup)) as old:
                self.assertEqual(old.execute('PRAGMA user_version').fetchone()[0], 1)
            result = demo(root)
            with Repository(root, result['project_id']) as repo:
                source = repo.snapshot_data()
                g = build(repo); count = len(history(repo))
                self.assertEqual(g, build(repo))
                self.assertEqual(count, len(history(repo)))
                self.assertEqual(source, repo.snapshot_data())
            with Repository(root, result['project_id']) as repo:
                self.assertEqual(g, build(repo))
                self.assertEqual(count, len(history(repo)))

    def test_migration_transaction_failure_preserves_v1(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); pid = new_id(); folder = root / pid; folder.mkdir()
            with closing(sqlite3.connect(folder / 'mapper.sqlite3')) as db:
                db.executescript((Path(__file__).parents[2] / 'src/mapper/storage/migrations/001_initial.sql').read_text())
                db.execute('INSERT INTO project_meta VALUES (?,?,?)', (pid, 'Legacy', stamp())); db.commit()
            original = Path.read_text
            def broken(path, *args, **kwargs):
                if path.name == '002_topology.sql':
                    return 'BEGIN IMMEDIATE; CREATE TABLE should_rollback(x); INVALID SQL; COMMIT;'
                return original(path, *args, **kwargs)
            with patch.object(Path, 'read_text', broken):
                with self.assertRaisesRegex(Exception, 'DATABASE_MIGRATION_FAILED_BACKUP_PRESERVED'):
                    Repository(root, pid)
            with closing(sqlite3.connect(folder / 'mapper.sqlite3')) as db:
                self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 1)
                self.assertIsNone(db.execute("SELECT name FROM sqlite_master WHERE name='should_rollback'").fetchone())
            self.assertEqual(len(list(folder.glob('*.bak'))), 1)

    def test_retention_keeps_history_and_comparison_checkpoint(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = demo(root)
            with Repository(root, result['project_id']) as repo:
                first = build(repo)
                count = len(history(repo))
                second_cycle = repo.begin_cycle({'project_id': repo.project_id, 'sends_probes': False}, origin='synthetic')
                obs = Observation('neighbor', 'host', {'ip': '192.0.2.20', 'mac': MAC, 'interface': 'demo0', 'state': 'cached'}, freshness='cached')
                repo.write_result(second_cycle, TableResult('os_neighbors', 'neighbors_before', [obs], scope_id='demo0:192.0.2.0/24'))
                repo.publish(second_cycle)
                checkpoint = build(repo)
                self.assertEqual(count, len(history(repo)))
                with repo.db:
                    repo.db.execute("UPDATE cycles SET finished_at='2000-01-01T00:00:00Z'")
                repo.prune()
                self.assertEqual(len(repo.snapshots()), 1)
                self.assertEqual(count, len(history(repo)))
                self.assertEqual(checkpoint, build(repo))
                self.assertEqual(repo.db.execute('PRAGMA foreign_key_check').fetchall(), [])

    def test_preview_local_assets_and_node_details_without_server(self):
        from mapper.topology.preview import create_app
        graph = derive(Fixture().basic().data)
        app = create_app(graph)
        with app.server.test_client() as client:
            html = client.get('/')
            self.assertEqual(html.status_code, 200)
            resources = re.findall(r"""(?:src|href)=["']([^"']+)["']""", html.data.decode())
            for resource in resources:
                self.assertFalse(resource.startswith(('http:', 'https:', '//')))
                self.assertEqual(client.get(resource).status_code, 200)
            self.assertEqual(client.get('/_dash-layout').status_code, 200)
            node = endpoints(graph)[0]
            response = client.post('/_dash-update-component', json={'output': 'details.children',
                'outputs': {'id': 'details', 'property': 'children'},
                'inputs': [{'id': 'graph', 'property': 'tapNodeData', 'value': {'id': node['id']}}],
                'changedPropIds': ['graph.tapNodeData'], 'state': []})
            self.assertEqual(response.status_code, 200)
            self.assertIn(MAC, response.get_json()['response']['details']['children'])


if __name__ == '__main__':
    unittest.main()
