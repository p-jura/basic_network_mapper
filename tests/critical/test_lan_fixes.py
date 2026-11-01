"""Small LAN regression set, synthetic data and blocked network only."""
from copy import deepcopy
import json
from unittest.mock import patch

from test_stage2 import ProtectedTest, FakeAdapter
from test_stage3 import Fixture, endpoints
from test_stage4 import wait
from mapper.app import create_app
from mapper.cli import demo
from mapper.models import Observation, TableResult
from mapper.storage import Repository
from mapper.topology.engine import derive
from mapper.topology.service import build, history
from mapper.ui.controller import Controller
from mapper.ui.data import config_read, save_config, read_view


class LanTests(ProtectedTest):
    def test_group_zero_mac_arp_fdb_and_raw_preservation(self):
        f = Fixture().basic()
        target = f.target('192.0.2.2')
        for mac in ['ff:ff:ff:ff:ff:ff','01:00:5e:00:00:01','33:33:00:00:00:01','00:00:00:00:00:00']:
            f.add('neighbor', {'ip':'192.0.2.30','interface':'fixture0','mac':mac})
            f.add('ip_mac', {'ip':'192.0.2.31','mac':mac}, target=target)
            f.add('fdb_entry', {'mac':mac,'bridge_port':2,'status':3}, target=target)
        before = deepcopy(f.data)
        g = derive(f.data)
        self.assertEqual(len(endpoints(g)), 1)
        self.assertEqual(f.data, before)
        self.assertEqual({o['observation_id'] for o in f.data['observations']}, {o['observation_id'] for o in g['evidence']})

    def test_prefix_boundaries_including_255_and_point_to_point(self):
        cases = [('192.0.2.0/24', '192.0.2.255', False), ('192.0.2.0/24', '192.0.2.0',False),
                 ('192.0.2.0/23','192.0.2.255',True), ('192.0.2.254/31','192.0.2.255',True),
                 ('192.0.2.255/32','192.0.2.255',True)]
        for prefix, ip, keep in cases:
            with self.subTest(prefix=prefix, ip=ip):
                f=Fixture();scope='fixture0:'+prefix
                import ipaddress
                net=ipaddress.IPv4Network(prefix)
                if net.prefixlen != 32:
                    own=str(next(net.hosts()))
                    f.add('local_interface',{'interface':'fixture0','ip':own,'netmask':str(net.netmask),'is_up':True},source='os_interfaces',scope=scope)
                f.add('neighbor', {'ip':ip,'interface':'fixture0','mac':'02:00:00:00:00:44'},scope=scope)
                self.assertEqual(len(endpoints(derive(f.data))),int(keep))
        # A /24 chosen as a scan range does not make .255 a broadcast on /23.
        f=Fixture()
        f.add('local_interface',{'interface':'fixture0','ip':'192.0.2.1','netmask':'255.255.254.0','is_up':True},source='os_interfaces')
        f.add('neighbor',{'ip':'192.0.2.255','interface':'fixture0','mac':'02:00:00:00:00:44'})
        self.assertEqual(len(endpoints(derive(f.data))),1)

    def test_local_claims_conflicts_scope_and_remote_host(self):
        f=Fixture().basic();own='192.0.2.1'
        claims=[]
        for mac in ['02:00:00:00:00:01','02:00:00:00:00:02']:
            claims.append(f.add('neighbor',{'ip':own,'interface':'fixture0','mac':mac},fresh='cached'))
        t=f.target('192.0.2.2')
        f.add('ip_mac', {'ip':own,'mac':'02:00:00:00:00:03'},target=t,ctx='other-vrf')
        g=derive(f.data)
        local=next(n for n in g['nodes'] if n['kind']=='local_interface')
        self.assertEqual(local['macs'],[])
        self.assertEqual(len(local['neighbor_mac_claims']),2)
        self.assertTrue(all(o['observation_id'] in local['evidence'] for o in claims))
        self.assertEqual(len(endpoints(g)),2) # actual remote plus separate VRF
        self.assertEqual({w['code'] for w in g['warnings'] if w['subject_id']==local['id']}, {'LOCAL_IP_NEIGHBOR_CLAIM','IP_MAC_CONFLICT'})
        self.assertTrue(all(n['port'] is None and n['vlan_id'] is None for n in g['nodes']))

    def test_new_rules_preserve_old_result_history_and_source(self):
        pid=self.project()
        with Repository(self.root,pid) as repo:
            cycle=repo.begin_cycle({},origin='synthetic')
            repo.write_result(cycle,TableResult('os_neighbors','neighbors_before',[
                Observation('neighbor','broadcast',{'ip':'192.0.2.255','interface':'fixture0','mac':'ff:ff:ff:ff:ff:ff','state':'cached'},freshness='cached')],scope_id='fixture0:192.0.2.0/24'))
            repo.publish(cycle)
            before=repo.snapshot_data()
            with patch('mapper.topology.service.RULES_VERSION','1'),patch('mapper.topology.engine.RULES_VERSION','1'):
                legacy=build(repo)
            old=repo.db.execute('SELECT result_json FROM topology_results WHERE rules_version=?',('1:skew=300',)).fetchone()[0]
            # A retained legacy event must not pollute the current UI timeline.
            nid=legacy['nodes'][0]['id']
            event={'event_id':'legacy-fixture','kind':'first_observed','rules_version':'1:skew=300'}
            with repo.db:
                repo.db.execute('INSERT INTO history_events VALUES (?,?,?,?,?,?,?,?,?)',('legacy-fixture',nid,'1:skew=300',legacy['snapshot_id'],None,'2026-10-25T00:00:00Z','first_observed','synthetic',json.dumps(event)))
            graph=build(repo)
            self.assertEqual(graph['rules_version'],'2:skew=300')
            self.assertEqual(graph,build(repo))
            self.assertEqual(repo.snapshot_data(),before)
            self.assertEqual(old,repo.db.execute('SELECT result_json FROM topology_results WHERE rules_version=?',('1:skew=300',)).fetchone()[0])
            self.assertNotIn(event,history(repo))
            self.assertIn(event,history(repo,rules_version='1:skew=300'))
            self.assertEqual(repo.db.execute('PRAGMA foreign_key_check').fetchall(),[])
        self.assertNotIn(event,read_view(self.root,pid)['history'])

    def callback(self, app, prefix, values, changed):
        key=next(k for k in app.callback_map if k.startswith(prefix));meta=app.callback_map[key]
        outputs=meta['output'];outputs=outputs if isinstance(outputs,list) else [outputs]
        payload={'output':key,'outputs':[{'id':o.component_id,'property':o.component_property} for o in outputs],
                 'inputs':[{'id':i['id'],'property':i['property'],'value':values.get(i['id'])} for i in meta['inputs']],
                 'state':[{'id':i['id'],'property':i['property'],'value':values.get(i['id'])} for i in meta['state']], 'changedPropIds':[changed]}
        c=app.server.test_client();url='http://127.0.0.1:8050';c.get('/',base_url=url)
        response=c.post('/_dash-update-component',base_url=url,headers={'Origin':url},json=payload)
        self.assertEqual(response.status_code,200,response.data)
        return response.json['response']

    def test_prefill_ready_guard_and_preview_without_reselect_or_probes(self):
        pid=demo(self.root)['project_id'];cfg=config_read(self.root,pid)
        cfg['basic']={'interface':'fixture0','cidr':'192.0.2.0/29'};save_config(self.root,pid,cfg)
        adapter=FakeAdapter();control=Controller(self.root,adapter_factory=lambda _:adapter)
        app=create_app(self.root,controller=control);self.addCleanup(control.close)
        with patch('mapper.discovery.system.interfaces',side_effect=AssertionError('Unrequested interface read')):
            form=self.callback(app,'..interface.value',{'project':pid},'project.value')
        self.assertEqual(form['interface']['value'],'fixture0')
        self.assertEqual(form['interface']['options'][0]['value'],'fixture0')
        values={k:v.get('value',v.get('data')) for k,v in form.items()}
        values.update(project=pid)
        not_ready=self.callback(app,'..save.disabled',{'project':pid,'form-project':None,'approval':{'token':'stale'}},'project.value')
        self.assertTrue(not_ready['start']['disabled'])
        outputs=[o for meta in app.callback_map.values() for o in (meta['output'] if isinstance(meta['output'],list) else [meta['output']])]
        self.assertEqual(sum(o.component_id=='start' and o.component_property=='disabled' for o in outputs),1)
        before=(self.root/pid/'project.json').read_bytes()
        bad=self.callback(app,'..project.options',{**values,'form-project':None},'prepare.n_clicks')
        self.assertEqual(bad['message']['children'],'PROJECT_FORM_NOT_READY')
        incomplete=self.callback(app,'..project.options',{**values,'interface':None},'prepare.n_clicks')
        self.assertEqual(incomplete['message']['children'],'BASIC_INTERFACE_AND_CIDR_REQUIRED')
        self.assertEqual((self.root/pid/'project.json').read_bytes(),before)
        ready=self.callback(app,'..project.options',values,'prepare.n_clicks')
        job=wait(control,ready['job-ref']['data']['id'])
        self.assertEqual(job['state'],'finished',job)
        self.assertEqual(job['result']['plan']['basic']['interface'],'fixture0')
        self.assertEqual(adapter.calls,0)
        self.assertEqual(config_read(self.root,pid)['basic'],cfg['basic'])
