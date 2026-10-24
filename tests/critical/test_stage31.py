"""Review regression contracts. No native Windows calls or network traffic."""
import asyncio
import ctypes as c
from dataclasses import replace
import io
import json
import os
from pathlib import Path
import stat
import threading
import unittest
from unittest.mock import patch

from test_stage2 import ProtectedTest, FakeAdapter
from mapper.cli import main, demo
from mapper.config import Limits
from mapper.discovery.system import SystemAdapter, CommandOutput, parse_windows_routes, parse_windows_neighbors
from mapper.discovery.windows_ipv4 import WindowsIPv4, RouteRow, Sockaddr, EchoHeader, address_number, probe as windows_probe
from mapper.errors import MapperError
from mapper.private_files import private_file, protect
from mapper.windows_security import private_sddl, WindowsSecurity
from mapper.storage import Repository
from mapper.storage.repository import cycle_lock
from mapper.cycle import run_cycle


class StateTests(ProtectedTest):
    def test_253_targets_share_state_and_refresh_on_vpn_change(self):
        clock = [0.0]
        calls = []
        vpn = [False]
        async def runner(args, timeout):
            calls.append(args)
            if 'netstat' in args[0]:
                await asyncio.sleep(0)
                iface = 'utun0' if vpn[0] else 'fixture0'
                return CommandOutput(0, f'Destination Gateway Flags Netif\n192.0.2 link#1 UCS {iface}\n')
            self.assertEqual(args[args.index('-S') + 1], '192.0.2.254')
            self.assertEqual(args[args.index('-b') + 1], 'fixture0')
            return CommandOutput(2, '')
        def interfaces():
            return [{'interface':'fixture0', 'index':7, 'ip':'192.0.2.254', 'netmask':'255.255.255.0', 'is_up':True}]
        async def scenario():
            adapter = SystemAdapter(Limits(), runner, interfaces, 'darwin', clock=lambda: clock[0])
            gate = asyncio.Semaphore(4)
            async def one(n):
                async with gate:
                    return await adapter.probe(f'192.0.2.{n}', 'fixture0', '192.0.2.254')
            result = await asyncio.gather(*(one(n) for n in range(1, 254)))
            self.assertTrue(all(r == ('no_reply', None) for r in result))
            self.assertEqual(sum('netstat' in a[0] for a in calls), 1)
            clock[0] = 1.01; vpn[0] = True
            result = await asyncio.gather(*(one(n) for n in range(1, 5)))
            self.assertTrue(all(r == ('skipped', 'ROUTE_OR_INTERFACE_CHANGED') for r in result))
            self.assertEqual(sum('netstat' in a[0] for a in calls), 2)
            self.assertEqual(sum(a[0] == '/sbin/ping' for a in calls), 253)
        asyncio.run(scenario())

    def test_cache_at_simulated_five_targets_per_second(self):
        clock, count = [0.0], [0]
        async def runner(args, timeout):
            if 'netstat' in args[0]:
                count[0] += 1
                return CommandOutput(0,'Destination Gateway Flags Netif\n192.0.2 link#1 UCS fixture0\n')
            return CommandOutput(2,'')
        def interfaces():
            return [{'interface':'fixture0','ip':'192.0.2.254','netmask':'255.255.255.0','is_up':True}]
        async def scenario():
            adapter=SystemAdapter(Limits(),runner,interfaces,'darwin',clock=lambda:clock[0])
            for n in range(1,254):
                clock[0]=(n-1)/5
                await adapter.probe(f'192.0.2.{n}','fixture0','192.0.2.254')
        asyncio.run(scenario())
        self.assertEqual(count[0],51)

    def test_route_error_invalidates_cache_and_interface_change_skips(self):
        clock, mode, calls = [0.0], ['ok'], []
        async def runner(args, timeout):
            if 'netstat' in args[0]:
                calls.append('route')
                if mode[0] == 'error':
                    return CommandOutput(1, '')
                return CommandOutput(0,'Destination Gateway Flags Netif\n192.0.2 link#1 UCS fixture0\n')
            calls.append('ping');return CommandOutput(2,'')
        def interfaces():
            values = FakeAdapter().interfaces()
            if mode[0] == 'lost':
                values[0]['ip'] = '198.51.100.1'
            return values
        async def scenario():
            a = SystemAdapter(Limits(),runner,interfaces,'darwin',clock=lambda:clock[0])
            self.assertEqual((await a.probe('192.0.2.2','fixture0','192.0.2.1'))[0], 'no_reply')
            clock[0] = 1.1;mode[0] = 'error'
            for _ in range(4):
                self.assertEqual(await a.probe('192.0.2.2','fixture0','192.0.2.1'), ('skipped','SYSTEM_READ_FAILED'))
            self.assertEqual(calls.count('route'),2)
            clock[0] = 2.2;mode[0] = 'lost'
            self.assertEqual((await a.probe('192.0.2.2','fixture0','192.0.2.1'))[0],'skipped')
            self.assertEqual(calls.count('ping'),1)
        asyncio.run(scenario())
        with self.assertRaisesRegex(MapperError,'INVALID_ROUTE_REFRESH'):
            replace(Limits(),route_refresh_seconds=30)

    def test_windows_uses_native_sender_and_one_metric_query(self):
        scripts, sent = [], []
        async def runner(args, timeout):
            self.assertNotIn('PING.EXE',args[0])
            scripts.append(args[-1])
            return CommandOutput(0,json.dumps({'DestinationPrefix':'192.0.2.0/29','NextHop':'0.0.0.0','InterfaceAlias':'fixture0','RouteMetric':5,'InterfaceMetric':10}))
        async def sender(*args):
            sent.append(args)
            return 'reply',None
        async def scenario():
            a=SystemAdapter(Limits(),runner,FakeAdapter().interfaces,'win32',windows_probe=sender)
            self.assertEqual(await a.probe('192.0.2.2','fixture0','192.0.2.1'),('reply',None))
            self.assertEqual(await a.probe('192.0.2.3','fixture0','192.0.2.1'),('reply',None))
        asyncio.run(scenario())
        self.assertEqual(len(scripts),1)
        self.assertEqual(scripts[0].count('Get-NetIPInterface'),1)
        self.assertEqual(sent[0][:3],('192.0.2.2','fixture0','192.0.2.1'))

    def test_windows_json_unicode_and_malformed_data_fail_closed(self):
        row={'DestinationPrefix':'192.0.2.0/24','NextHop':'0.0.0.0','InterfaceAlias':'Połączenie sieciowe','RouteMetric':5,'InterfaceMetric':10}
        self.assertEqual(parse_windows_routes('\ufeff'+json.dumps([row]))[0]['metric'],15)
        for data in ['', '[', json.dumps({**row,'InterfaceMetric':None}), json.dumps({**row,'RouteMetric':-1}), json.dumps({**row,'InterfaceAlias':None})]:
            with self.assertRaises(MapperError):parse_windows_routes(data)
        self.assertEqual(parse_windows_routes('null'),[])
        self.assertEqual(parse_windows_neighbors('[]','Ethernet'),[])
        with self.assertRaises(MapperError):
            parse_windows_neighbors(json.dumps({'InterfaceAlias':'Ethernet','IPAddress':'192.0.2.20','LinkLayerAddress':'02-00-00-00-00-20'}),'Ethernet')


class Fn:
    def __init__(self,fn):self.fn=fn
    def __call__(self,*args):return self.fn(*args)


class FakeDLL:
    def __init__(self):
        self.index=7;self.route_index=7;self.hop=0;self.status=0;self.error=11010;self.timeout=False;self.closed=[];self.sent=[]
        self.ConvertInterfaceAliasToLuid=Fn(lambda name,out:self.set(out,17))
        self.ConvertInterfaceLuidToIndex=Fn(lambda luid,out:self.set(out,self.index))
        self.GetBestRoute2=Fn(self.route)
        self.IcmpCreateFile=Fn(lambda:99)
        self.IcmpCloseHandle=Fn(lambda h:self.closed.append(h) or 1)
        self.IcmpSendEcho2Ex=Fn(self.send)
    @staticmethod
    def set(ptr,value):ptr._obj.value=value;return 0
    def route(self,luid,index,source,dest,options,row,best):
        row._obj.index=self.route_index;row._obj.next_hop.family=2;row._obj.next_hop.v4.address=self.hop;row._obj.valid_lifetime=3600
        best._obj.v4.family=2;best._obj.v4.address=source._obj.v4.address
        return 0
    def send(self,*args):
        self.sent.append(args)
        if self.timeout:return 0
        header=EchoHeader(args[5],self.status,1,args[7],0)
        c.memmove(args[9],c.byref(header),c.sizeof(header))
        return 1


class NativeTests(ProtectedTest):
    def test_native_fixed_layout_source_route_status_and_handle(self):
        self.assertEqual(c.sizeof(Sockaddr),28)
        self.assertEqual(c.sizeof(RouteRow),104)
        self.assertEqual(RouteRow.metric.offset,84)
        self.assertEqual(c.sizeof(EchoHeader),16)
        dll=FakeDLL();a=WindowsIPv4(dll,last_error=lambda:dll.error)
        send=lambda:a.probe('192.0.2.20','Ethernet','192.0.2.1',7,1000)
        self.assertEqual(send(),('reply',None))
        self.assertEqual(dll.sent[0][4],address_number('192.0.2.1'))
        self.assertEqual(dll.closed,[99])
        dll.status=11003
        self.assertEqual(send(),('error','WINDOWS_ICMP_REPLY_NOT_CONFIRMED'))
        dll.timeout=True
        self.assertEqual(send(),('no_reply',None))
        before=len(dll.sent);dll.route_index=9
        self.assertEqual(send(),('skipped','ROUTE_OR_INTERFACE_CHANGED'))
        self.assertEqual(len(dll.sent),before)
        self.assertEqual(len(dll.closed),3)

    def test_cancelled_native_call_is_drained(self):
        started,finish=threading.Event(),threading.Event()
        class Native:
            def probe(self,*args):
                started.set();finish.wait(1);return 'no_reply',None
        async def scenario():
            task=asyncio.create_task(windows_probe('192.0.2.20','Ethernet','192.0.2.1',7,3,factory=Native))
            while not started.is_set():await asyncio.sleep(0.001)
            task.cancel();await asyncio.sleep(0)
            self.assertFalse(task.done())
            finish.set()
            with self.assertRaises(asyncio.CancelledError):await task
        asyncio.run(scenario())


class LockAndFileTests(ProtectedTest):
    def test_global_collection_lock_allows_other_project_offline(self):
        a,b=demo(self.root),demo(self.root)
        with cycle_lock(self.root):
            for args in [
                ['topology','build','--project',b['project_id']],
                ['history','--project',b['project_id']],
                ['snapshot','export','--project',b['project_id'],'--output',str(self.root/'snapshot.json')],
                ['snapshot','import','--new-project','--input',str(self.root/'snapshot.json')],
                ['project','create','--name','During collection'],
            ]:
                out,err=io.StringIO(),io.StringIO()
                with patch('sys.stdout',out),patch('sys.stderr',err):
                    self.assertEqual(main(['--data-dir',str(self.root),*args]),0,err.getvalue())
            with Repository(self.root,a['project_id']) as repo:
                with self.assertRaisesRegex(MapperError,'CYCLE_ALREADY_RUNNING'):
                    asyncio.run(run_cycle(repo,{'project_id':repo.project_id,'limits':{},'basic':None,'seeds':[]}))

    def test_project_lock_and_constructor_error_release(self):
        a,b=demo(self.root),demo(self.root)
        with Repository(self.root,a['project_id']):
            with self.assertRaisesRegex(MapperError,'PROJECT_BUSY'):Repository(self.root,a['project_id'])
            with Repository(self.root,b['project_id']):pass
        with Repository(self.root,a['project_id']) as repo:
            with repo.db:repo.db.execute('PRAGMA user_version=99')
        with self.assertRaisesRegex(MapperError,'UNSUPPORTED_DB_VERSION'):Repository(self.root,a['project_id'])
        # A failure released its OS lock, not merely its SQLite connection.
        from mapper.storage.repository import project_lock
        with project_lock(self.root/a['project_id']):pass

    @unittest.skipIf(os.name == 'nt', 'POSIX modes; effective NTFS DACL needs Windows acceptance')
    def test_private_file_mode_from_first_write_and_no_follow(self):
        p=self.root/'export.json';parent_mode=stat.S_IMODE(self.root.stat().st_mode)
        with private_file(p) as f:
            self.assertEqual(stat.S_IMODE(p.stat().st_mode),0o600)
            f.write('synthetic')
        self.assertEqual(stat.S_IMODE(self.root.stat().st_mode),parent_mode)
        with self.assertRaises(FileExistsError):
            with private_file(p):pass
        link=self.root/'link';link.symlink_to(p)
        with self.assertRaisesRegex(MapperError,'UNSAFE_DATA_PATH'):
            with private_file(link):pass
        self.assertEqual(p.read_text(),'synthetic')
        result=demo(self.root)
        directory=self.root/result['project_id']
        self.assertEqual(stat.S_IMODE(directory.stat().st_mode),0o700)
        for f in directory.iterdir():self.assertEqual(stat.S_IMODE(f.stat().st_mode),0o600)

    def test_windows_volume_without_acl_is_rejected(self):
        native=object.__new__(WindowsSecurity)
        class Kernel:
            @staticmethod
            def GetVolumePathNameW(path, buffer, size):buffer.value='X:/';return 1
            @staticmethod
            def GetVolumeInformationW(volume, label, size, serial, maximum, flags, fs, fs_size):
                flags._obj.value=0;return 1
        native.kernel=Kernel()
        with self.assertRaisesRegex(MapperError,'FILE_PROTECTION_UNAVAILABLE'):
            native._require_acl_volume(self.root/'synthetic-file')

    def test_windows_private_backend_failure_and_protected_sddl(self):
        calls=[]
        class Backend:
            def create_file(self,path):
                calls.append(('create',path));return os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            def protect(self,path,**kwargs):calls.append(('protect',path))
        p=self.root/'windows-contract.json'
        with patch('mapper.private_files.is_windows',return_value=True),patch('mapper.private_files.windows_security',return_value=Backend()):
            with private_file(p) as f:f.write('fixture')
            protect(p)
        self.assertEqual([v[0] for v in calls],['create','protect'])
        with patch('mapper.private_files.is_windows',return_value=True),patch('mapper.private_files.windows_security',side_effect=MapperError('FILE_PROTECTION_FAILED')):
            with self.assertRaisesRegex(MapperError,'FILE_PROTECTION_FAILED'):
                with private_file(self.root/'must-not-exist'):pass
        self.assertFalse((self.root/'must-not-exist').exists())
        sddl=private_sddl('S-1-5-21-10-20-30-1001',True)
        self.assertTrue(sddl.startswith('D:P'))
        self.assertEqual(sddl.count('(A;OICI;FA;;;'),3)
        self.assertNotIn(';;;WD',sddl)


if __name__=='__main__':unittest.main()
