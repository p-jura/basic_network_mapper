"""Generate a synthetic D14 snapshot, offline. Never polls any network."""
import argparse
from pathlib import Path
from mapper.cli import project_create
from mapper.config import target_id
from mapper.models import Observation, TableResult, safe_json
from mapper.storage import Repository
from mapper.snapshots import export_snapshot


def generate(root):
 root=Path(root).expanduser()
 root.mkdir(parents=True,mode=0o700,exist_ok=True)
 pid=project_create(root,'D14 — 50 switchy / 1000 hostów / 20 VLAN')['project_id']
 count=0
 with Repository(root,pid) as repo:
  cycle=repo.begin_cycle({'project_id':pid,'sends_probes':False},origin='synthetic')
  for switch in range(50):
   seed={'ip':f'198.51.100.{switch+1}','port':161,'profile_id':'synthetic','context':'lab'}
   tid=target_id(pid,seed);repo.register_target(tid,seed)
   groups={k:[] for k in ['device_identity','interface','bridge_port_map','vlan','ip_mac','fdb_entry','lldp_local_port','lldp_neighbor']}
   def add(kind,payload,key): groups[kind].append(Observation(kind,str(key),payload,freshness='fresh'))
   add('device_identity',{'name':f'LAB-SW-{switch+1:02}'},'identity')
   for v in range(1,21):
    add('interface',{'if_index':100+v,'name':f'Gi1/0/{v}'},v)
    add('bridge_port_map',{'if_index':100+v,'bridge_port':v},v)
    add('vlan',{'vlan_id':v,'fdb_id':v,'egress_ports':[v],'untagged_ports':[v]},v)
    h=switch*20+v
    ip=f'10.20.{h//254}.{h%254+1}';mac='02:00:00:'+f'{h:06x}'[:2]+':'+f'{h:06x}'[2:4]+':'+f'{h:06x}'[4:]
    add('ip_mac',{'ip':ip,'mac':mac,'if_index':100+v},h)
    add('fdb_entry',{'mac':mac,'bridge_port':v,'fdb_id':v,'status':3},h)
   def switch_mac(n): return f'02:aa:00:00:00:{n+1:02x}'
   add('interface',{'if_index':9001,'name':'Uplink','mac':switch_mac(switch)},'uplink')
   add('lldp_local_port',{'local_port_num':99,'local_port_id':'hex:55706c696e6b','local_port_subtype':5},'local-lldp')
   if switch < 49:
    add('lldp_neighbor',{'local_port_num':99,'remote_index':1,'time_mark':0,'remote_chassis_id':'hex:'+switch_mac(switch+1).replace(':',''),'remote_chassis_subtype':4,'remote_port_id':'hex:55706c696e6b','remote_port_subtype':5,'management_ip':f'198.51.100.{switch+2}'},'remote-lldp')
   # 1000 observations per switch, 50,000 in total; source inventory load.
   for i in range(1000-sum(map(len,groups.values()))):
    add('interface',{'if_index':1000+i,'name':f'Inventory-{i}','oper_status':2},1000+i)
   for kind,obs in groups.items():
    repo.write_result(cycle,TableResult('snmp',kind,obs,target_id=tid,context_id='lab',context_status='known'))
    count+=len(obs)
  repo.publish(cycle)
  out=root/pid/'scale-source.json';export_snapshot(repo,out)
 return {'project_id':pid,'snapshot':str(out),'observations':count,'synthetic':True,'sends_probes':False}


if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--data-dir',required=True)
 args=parser.parse_args()
 print(safe_json(generate(args.data_dir)))
