import asyncio
from dataclasses import asdict, replace
import io
import json
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from mapper.cli import demo, main, project_create
from mapper.collectors.snmp import SnmpTransport, bounded_walk, collect_snmp
from mapper.collectors.snmp_tables import TABLES, normalize, oid_tuple, port_list
from mapper.collectors.ssh import COMMANDS, collect_ssh, in_thread, normalize as ssh_normalize
from mapper.config import Limits, load_config, target_id
from mapper.cycle import run_cycle
from mapper.discovery.basic import collect_basic, target_plan
from mapper.discovery.system import CommandOutput, SystemAdapter, parse_macos_neighbors, parse_macos_routes, parse_windows_neighbors, parse_windows_routes, route_matches, run_command
from mapper.errors import MapperError
from mapper.models import Observation, TableResult, new_id
from mapper.snapshots import export_snapshot, import_snapshot, read_snapshot
from mapper.storage import Repository
from mapper.storage.repository import cycle_lock


def forbid_network(*_a, **_k):
    raise AssertionError("Tests must not open network connections")


class ProtectedTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ["connect", "connect_ex", "sendto"]:
            self.guard = patch.object(socket.socket, name, forbid_network)
            self.guard.start(); self.addCleanup(self.guard.stop)

    def project(self):
        return project_create(self.root, "Fixture")["project_id"]


def neighbor():
    return Observation("neighbor", "192.0.2.20", {"ip": "192.0.2.20", "mac": "02:00:00:00:00:20", "interface": "fixture0", "state": "cached"}, freshness="cached")


class StorageTests(ProtectedTest):
    def test_retention_preserves_last_complete_per_scope(self):
        pid = self.project()
        with Repository(self.root, pid) as repo:
            for scope in ["a", "b"]:
                cycle = repo.begin_cycle({"scope": scope})
                repo.write_result(cycle, TableResult("os_neighbors", "cache", [neighbor()]))
                repo.publish(cycle)
                with repo.db:
                    repo.db.execute("UPDATE cycles SET finished_at='2000-01-01T00:00:00Z' WHERE cycle_id=?", (cycle,))
            repo.prune()
            self.assertEqual(len(repo.snapshots(complete=True)), 2)

    def test_persistence_isolation_and_partial_publication(self):
        a, b = self.project(), self.project()
        with Repository(self.root, a) as repo:
            cycle = repo.begin_cycle({})
            repo.write_result(cycle, TableResult("os_neighbors", "cache", [neighbor()]))
            repo.publish(cycle)
        with Repository(self.root, a) as repo:
            original = repo.snapshot_data()
            partial = repo.begin_cycle({})
            repo.write_result(partial, TableResult("snmp", "fdb", status="timeout", reason="SNMP_TIMEOUT"))
            repo.publish(partial)
            self.assertEqual(repo.snapshots()[0]["coverage_status"], "partial")
            self.assertEqual(repo.snapshots(complete=True)[0]["cycle_id"], cycle)
            pending = repo.begin_cycle({})
            repo.recover_interrupted()
            self.assertEqual(repo.db.execute("SELECT execution_status FROM cycles WHERE cycle_id=?", (pending,)).fetchone()[0], "interrupted")
            self.assertEqual(len(repo.snapshots()), 2)
            self.assertEqual(original["observations"][0]["evidence_at"], None)
            self.assertEqual(repo.db.execute("PRAGMA foreign_keys").fetchone()[0], 1)
            self.assertEqual(repo.db.execute("PRAGMA user_version").fetchone()[0], 2)
        with Repository(self.root, b) as repo:
            self.assertEqual(repo.snapshots(), [])
            self.assertEqual(repo.db.execute("SELECT count(*) FROM observations").fetchone()[0], 0)

    def test_lock_and_secret_exclusion(self):
        with cycle_lock(self.root):
            with self.assertRaisesRegex(MapperError, "CYCLE_ALREADY_RUNNING"):
                with cycle_lock(self.root):
                    pass
        pid = self.project()
        sentinel = "fixture_" + "not_a_real_credential"
        with Repository(self.root, pid, forbidden=[sentinel]) as repo:
            cycle = repo.begin_cycle({})
            with self.assertRaisesRegex(MapperError, "SECRET_IN_OUTPUT"):
                repo.write_result(cycle, TableResult("ssh", "version", [Observation("device_identity", "v", {"description": sentinel})]))
        self.assertNotIn(sentinel.encode(), (self.root / pid / "mapper.sqlite3").read_bytes())
        with self.assertRaises(MapperError):
            Observation("device_identity", "bad", {"password": sentinel})
        with self.assertRaises(MapperError):
            Repository(self.root, "../../wrong")

    def test_snapshot_roundtrip_and_import_validation(self):
        result = demo(self.root)
        file = self.root / "snapshot.json"
        with Repository(self.root, result["project_id"]) as repo:
            original = repo.snapshot_data()
            export_snapshot(repo, file)
            with self.assertRaises(FileExistsError):
                export_snapshot(repo, file)
        pid = import_snapshot(self.root, file)
        with Repository(self.root, pid) as repo:
            replay = repo.snapshot_data()
            self.assertEqual(replay["cycle"]["origin"], "imported")
            self.assertEqual([o["payload"] for o in replay["observations"]], [o["payload"] for o in original["observations"]])
            self.assertEqual([o["observed_at"] for o in replay["observations"]], [o["observed_at"] for o in original["observations"]])
            self.assertNotEqual(replay["project_id"], original["project_id"])
        with self.assertRaisesRegex(MapperError, "IMPORT_SIZE_LIMIT"):
            read_snapshot(file, max_bytes=1)
        with self.assertRaisesRegex(MapperError, "IMPORT_RECORD_LIMIT"):
            read_snapshot(file, max_records=1)
        data = json.loads(file.read_text()); data["schema_version"] = 999; file.write_text(json.dumps(data))
        with self.assertRaisesRegex(MapperError, "UNSUPPORTED_SNAPSHOT"):
            read_snapshot(file)
        data["schema_version"] = 1
        data["observations"][0]["payload"]["password"] = "not-real"
        file.write_text(json.dumps(data))
        with self.assertRaisesRegex(MapperError, "FORBIDDEN_SNAPSHOT_FIELD"):
            read_snapshot(file)


class FakeAdapter:
    def __init__(self):
        self.calls = 0

    def interfaces(self):
        return [{"interface": "fixture0", "index": 1, "ip": "192.0.2.1", "netmask": "255.255.255.248", "is_up": True}]

    async def routes(self):
        return [{"prefix": "192.0.2.0/29", "next_hop": None, "interface": "fixture0", "metric": 0}]

    async def neighbors(self, interface):
        self.calls += 1
        return [{"ip": "192.0.2.2", "mac": "02:00:00:00:00:02", "interface": interface, "state": "cached"}]

    async def probe(self, ip, interface, source):
        return ("reply", None) if ip == "192.0.2.3" else ("no_reply", None)


class DiscoveryTests(ProtectedTest):
    def test_scope_routes_and_platform_parsers(self):
        adapter = FakeAdapter()
        limits = Limits()
        with self.assertRaisesRegex(MapperError, "LOCAL_INTERFACE_NOT_UNIQUE"):
            target_plan({"interface": "fixture0", "cidr": "192.0.0.0/16"}, adapter.interfaces(), limits)
        with self.assertRaisesRegex(MapperError, "TARGET_BUDGET_EXCEEDED"):
            target_plan({"interface": "fixture0", "cidr": "192.0.2.0/29"}, adapter.interfaces(), replace(limits, max_targets=1))
        mac = "Routing tables\nInternet:\nDestination Gateway Flags Netif Expire\n192.0.2 link#1 UCS fixture0\n192.0.2.3 198.51.100.1 UGHS utun0\n"
        routes = parse_macos_routes(mac)
        self.assertTrue(route_matches("192.0.2.2", "fixture0", routes))
        self.assertFalse(route_matches("192.0.2.3", "fixture0", routes))
        rows = parse_macos_neighbors("? (192.0.2.2) at 2:0:0:0:0:2 on fixture0 ifscope [ethernet]", "fixture0")
        self.assertEqual(rows[0]["mac"], "02:00:00:00:00:02")
        win = json.dumps({"DestinationPrefix": "192.0.2.0/29", "NextHop": "0.0.0.0", "InterfaceAlias": "Ethernet", "RouteMetric": 5, "InterfaceMetric": 10})
        self.assertEqual(parse_windows_routes(win)[0]["metric"], 15)
        self.assertEqual(parse_windows_neighbors("null", "Ethernet"), [])
        with self.assertRaises(MapperError):
            parse_macos_routes("changed format")

    def test_basic_cache_no_reply_and_cancellation(self):
        async def scenario(cancelled):
            cancel = asyncio.Event()
            if cancelled:
                cancel.set()
            return [r async for r in collect_basic({"interface": "fixture0", "cidr": "192.0.2.0/29"}, replace(Limits(), rate=1000), cancel, FakeAdapter())]
        results = asyncio.run(scenario(False))
        after = next(r for r in results if r.table == "neighbors_after").observations[0]
        self.assertEqual(after.freshness, "cached")
        self.assertIsNone(after.evidence_at)
        self.assertFalse(after.payload["changed_since_before"])
        probes = next(r for r in results if r.source == "icmp")
        self.assertEqual(probes.status, "ok")
        self.assertEqual(sum(o.payload["result"] == "reply" for o in probes.observations), 1)
        self.assertNotIn("vlan_id", after.payload)
        cancelled = asyncio.run(scenario(True))
        self.assertEqual(next(r for r in cancelled if r.source == "icmp").status, "cancelled")

    def test_ping_does_not_trust_exit_code_or_unreachable(self):
        async def runner(args, _timeout):
            if "netstat" in args[0]:
                return CommandOutput(0, "Destination Gateway Flags Netif\n192.0.2 link#1 UCS fixture0\n")
            return CommandOutput(0, "Reply from 192.0.2.2: Destination host unreachable")
        async def scenario():
            adapter = SystemAdapter(Limits(), runner, FakeAdapter().interfaces, "darwin")
            return await adapter.probe("192.0.2.2", "fixture0", "192.0.2.1")
        self.assertEqual(asyncio.run(scenario())[0], "error")
        async def exit_scenario(code):
            async def failing_runner(args, _timeout):
                if "netstat" in args[0]:
                    return CommandOutput(0, "Destination Gateway Flags Netif\n192.0.2 link#1 UCS fixture0\n")
                return CommandOutput(code, "")
            adapter = SystemAdapter(Limits(), failing_runner, FakeAdapter().interfaces, "darwin")
            return await adapter.probe("192.0.2.2", "fixture0", "192.0.2.1")
        self.assertEqual(asyncio.run(exit_scenario(77)), ("error", "PING_PROCESS_FAILED"))
        self.assertEqual(asyncio.run(exit_scenario(2)), ("no_reply", None))

    def test_subprocess_timeout_and_output_bound(self):
        with self.assertRaisesRegex(MapperError, "COMMAND_TIMEOUT"):
            asyncio.run(run_command([sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.05))
        with self.assertRaisesRegex(MapperError, "COMMAND_OUTPUT_LIMIT"):
            asyncio.run(run_command([sys.executable, "-c", "print('x'*10000)"], timeout=2, max_output=100))


def snmp_fixture():
    values = {}
    def row(table, column, index, value):
        values.setdefault(table, []).append((oid_tuple(TABLES[table].root) + (column,) + tuple(index), value))
    row("system", 1, [0], b"Synthetic switch")
    row("system", 3, [0], 100)
    row("interfaces", 1, [101], 101)
    row("interfaces", 8, [101], 1)
    row("interface_names", 1, [101], b"Gi1/0/1")
    row("arp_physical", 4, [101, 1, 4, 192, 0, 2, 20], bytes.fromhex("020000000020"))
    row("arp_legacy", 2, [101, 192, 0, 2, 20], bytes.fromhex("020000000020"))
    row("bridge_ports", 2, [12], 101)
    row("fdb_q", 2, [7, 2, 0, 0, 0, 0, 32], 12)
    row("fdb_legacy", 2, [2, 0, 0, 0, 0, 32], 12)
    row("vlan_current", 3, [0, 10], 7)
    row("vlan_current", 4, [0, 10], b"\x80\x10")
    row("vlan_static", 1, [10], b"Users")
    row("port_vlan", 1, [12], 10)
    row("lldp_local", 2, [5], 5)
    row("lldp_local", 3, [5], b"Gi1/0/5")
    row("lldp_remote", 7, [0, 5, 1], b"Gi1/0/24")
    row("lldp_addresses", 3, [0, 5, 1, 1, 4, 192, 0, 2, 2], 2)
    return values


class FakeSnmp:
    def __init__(self, *_):
        self.values = snmp_fixture()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        pass

    async def uptime(self):
        return 100

    async def bulk(self, cursor):
        for name, spec in TABLES.items():
            prefix = oid_tuple(spec.root)
            if cursor[:len(prefix)] == prefix:
                return [(oid, v, "value") for oid, v in sorted(self.values.get(name, [])) if oid > cursor] + [((2, 0), None, "end")]
        raise AssertionError("Unexpected OID")


class ManagedTests(ProtectedTest):
    def test_snmp_v3_profile_and_actual_readonly_facade_without_network(self):
        from pysnmp.hlapi.v3arch import asyncio as h
        from pysnmp.proto.rfc1902 import Integer32, ObjectName
        seed = {"ip": "192.0.2.1", "port": 161}
        async def scenario():
            with patch.object(h.UdpTransportTarget, "create", AsyncMock(return_value=object())), patch.object(h, "bulk_cmd", AsyncMock(return_value=(None, 0, 0, [(ObjectName("1.3.6.1.2.1.1.3.0"), Integer32(100))]))) as bulk, patch.object(h, "get_cmd", AsyncMock(return_value=(None, 0, 0, [(ObjectName("1.3.6.1.2.1.1.3.0"), Integer32(100))]))):
                async with SnmpTransport(seed, {"type": "snmp3", "user_env": "MAPPER_TEST_USER", "auth_key_env": "MAPPER_TEST_AUTH", "priv_key_env": "MAPPER_TEST_PRIV"}, Limits()) as transport:
                    self.assertEqual(transport.auth.authentication_protocol, h.USM_AUTH_HMAC192_SHA256)
                    self.assertEqual(transport.auth.privacy_protocol, h.USM_PRIV_CFB128_AES)
                    self.assertEqual(await transport.uptime(), 100)
                    rows = await transport.bulk((1, 3, 6))
                    self.assertEqual(rows[0][2], "value")
                    self.assertFalse(bulk.call_args.kwargs["lookupMib"])
                    self.assertEqual(bulk.call_args.args[5], 20)
        with patch.dict("os.environ", {"MAPPER_TEST_USER": "fixture-user", "MAPPER_TEST_AUTH": "fixture-auth-only", "MAPPER_TEST_PRIV": "fixture-priv-only"}):
            asyncio.run(scenario())

    def test_cancelled_ssh_connect_is_cleaned_up(self):
        import threading
        started, finish = threading.Event(), threading.Event()
        cleaned = []
        def connect():
            started.set(); finish.wait(1)
            return "session"
        async def scenario():
            task = asyncio.create_task(in_thread(connect, cleanup=cleaned.append))
            while not started.is_set():
                await asyncio.sleep(0.001)
            task.cancel(); finish.set()
            with self.assertRaises(asyncio.CancelledError):
                await task
        asyncio.run(scenario())
        self.assertEqual(cleaned, ["session"])

    def test_snmp_all_tables_preserve_indices_vlan_and_ports(self):
        payloads = {name: normalize(name, rows)[0] for name, rows in snmp_fixture().items()}
        self.assertEqual(payloads["bridge_ports"][0].payload, {"if_index": 101, "bridge_port": 12})
        self.assertEqual(payloads["fdb_q"][0].payload["fdb_id"], 7)
        self.assertIsNone(payloads["fdb_q"][0].payload["vlan_id"])
        self.assertEqual(payloads["fdb_q"][0].freshness, "cached")
        self.assertEqual(payloads["vlan_current"][0].payload["vlan_id"], 10)
        self.assertEqual(port_list(b"\x80\x10"), [1, 12])
        self.assertEqual(payloads["lldp_addresses"][0].payload["management_ip"], "192.0.2.2")
        seed = {"ip": "192.0.2.1", "port": 161, "target_id": new_id()}
        async def scenario():
            return [r async for r in collect_snmp(seed, {"type": "snmp2"}, Limits(), asyncio.Event(), FakeSnmp)]
        result = asyncio.run(scenario())
        self.assertEqual(len(result), len(TABLES))
        self.assertTrue(all(r.status == "ok" for r in result))
        self.assertFalse(hasattr(SnmpTransport, "set"))

    def test_non_increasing_oid_empty_and_limits(self):
        class Bad:
            async def bulk(self, cursor):
                return [(cursor, 1, "value")]
        result = asyncio.run(bounded_walk(Bad(), TABLES["fdb_q"].root, Limits(), asyncio.Event(), 100))
        self.assertEqual(result[1:], ("partial", "NON_INCREASING_OID"))
        result = asyncio.run(bounded_walk(FakeSnmp(), TABLES["fdb_q"].root, replace(Limits(), walk_records=1), asyncio.Event(), 100))
        self.assertEqual(result[1:], ("partial", "RECORD_LIMIT"))

    def test_actual_textfsm_and_ssh_allowlist(self):
        from ntc_templates.parse import parse_output
        raw = "          Mac Address Table\n-------------------------------------------\n\nVlan    Mac Address       Type        Ports\n----    -----------       --------    -----\n  10    0200.0000.0020    DYNAMIC     Gi1/0/1\nTotal Mac Addresses for this criterion: 1\n"
        rows = parse_output(platform="cisco_ios", command="show mac address-table", data=raw)
        self.assertEqual(len(rows), 1)
        observation = ssh_normalize("show mac address-table", rows)[0]
        self.assertEqual(observation.payload["port_name"], "Gi1/0/1")
        self.assertIsNone(observation.payload["bridge_port"])
        hostkeys = self.root / "known_hosts"; hostkeys.write_text("")
        calls = []
        class Session:
            def send_command(self, command, **kwargs):
                calls.append(command)
                return rows if command == "show mac address-table" else []
            def disconnect(self):
                calls.append("disconnect")
        def connector(**kwargs):
            self.assertTrue(kwargs["ssh_strict"])
            self.assertFalse(kwargs["allow_auto_change"])
            self.assertIsNone(kwargs["session_log"])
            return Session()
        async def scenario():
            return [r async for r in collect_ssh({"ip": "192.0.2.1", "port": 22, "target_id": new_id()}, {"type": "ssh", "user_env": "MAPPER_FIXTURE_USER", "known_hosts": str(hostkeys)}, Limits(), asyncio.Event(), connector)]
        with patch.dict("os.environ", {"MAPPER_FIXTURE_USER": "fixture_user"}):
            results = asyncio.run(scenario())
        self.assertEqual(calls, [*COMMANDS, "disconnect"])
        self.assertEqual(len(results), len(COMMANDS))

    def test_controller_fault_isolation_and_recursive_dedup(self):
        pid = self.project()
        seed = {"ip": "192.0.2.1", "port": 161, "profile_id": "fixture"}
        config = {"project_id": pid, "basic": {"interface": "fixture0", "cidr": "192.0.2.0/29"}, "limits": asdict(replace(Limits(), rate=1000, recursion_devices=2)), "seeds": [seed], "profiles": {"fixture": {"type": "snmp2"}}, "allowed_ranges": ["192.0.2.0/24"], "recursive": True, "recursive_profile_id": "fixture"}
        visited = []
        async def collector(seed, profile, limits, cancel):
            visited.append(seed["ip"])
            if seed["ip"] == "192.0.2.1":
                yield TableResult("snmp", "lldp", [Observation("lldp_neighbor", "1", {"local_port_num": 1, "management_ip": "192.0.2.2"})], target_id=seed["target_id"])
            else:
                yield TableResult("snmp", "fdb", status="timeout", reason="SNMP_TIMEOUT", target_id=seed["target_id"])
        with Repository(self.root, pid) as repo:
            result = asyncio.run(run_cycle(repo, config, adapter=FakeAdapter(), snmp_collector=collector))
            self.assertEqual(result["coverage_status"], "partial")
            self.assertEqual(sorted(visited), ["192.0.2.1", "192.0.2.2"])
            self.assertTrue(any(o["kind"] == "probe_result" for o in repo.snapshot_data()["observations"]))

    def test_cli_offline_no_sources_and_credentials_not_echoed(self):
        out, err = io.StringIO(), io.StringIO()
        with patch("sys.stdout", out), patch("sys.stderr", err):
            self.assertEqual(main(["demo", "--data-dir", str(self.root)]), 0)
        self.assertTrue(json.loads(out.getvalue())["synthetic"])
        with patch("sys.stdout", io.StringIO()), patch("sys.stderr", err):
            self.assertEqual(main(["--password", "fixture-do-not-echo"]), 2)
        self.assertNotIn("fixture-do-not-echo", err.getvalue())


if __name__ == "__main__":
    unittest.main()
