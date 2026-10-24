import asyncio
from functools import partial
import ipaddress
from pathlib import Path
import time

from ..config import credentials
from ..errors import MapperError
from ..models import Observation, TableResult, mac_text, now

# No arbitrary operator commands, enable(), send_config_set() or running-config.
COMMANDS = ("show version", "show mac address-table", "show ip arp", "show vlan", "show interfaces status", "show lldp neighbors detail")


def numeric_vlan(value):
    return int(value) if isinstance(value, (str, int)) and str(value).isdigit() and 1 <= int(value) <= 4094 else None


def normalize(command, rows, max_records=50000):
    if command not in COMMANDS or not isinstance(rows, list):
        raise MapperError("SSH_PARSER_NOT_CONFIRMED")
    observations = []
    for index, row in enumerate(rows):
        if len(observations) >= max_records:
            break
        if not isinstance(row, dict):
            raise MapperError("SSH_INVALID_ROW")
        try:
            if command == "show version":
                payload = {"name": row["hostname"], "version": row["version"]}
                hardware = row.get("hardware", [])
                if hardware:
                    payload["model"] = ", ".join(hardware) if isinstance(hardware, list) else str(hardware)
                observations.append(Observation("device_identity", str(index), payload, freshness="fresh"))
            elif command == "show mac address-table":
                ports = row["destination_port"]
                if isinstance(ports, str):
                    ports = [ports]
                if not isinstance(ports, list) or not ports:
                    raise MapperError("SSH_INVALID_ROW")
                for n, port in enumerate(ports):
                    if len(observations) >= max_records:
                        break
                    observations.append(Observation("fdb_entry", f"{index}:{n}", {"mac": mac_text(row["destination_address"]), "bridge_port": None, "port_name": port, "vlan_id": numeric_vlan(row["vlan_id"]), "fdb_id": None, "status": row.get("type", "unknown")}, freshness="cached"))
            elif command == "show ip arp":
                raw = row["mac_address"]
                mac = None if raw.lower() in {"incomplete", "-"} else mac_text(raw)
                observations.append(Observation("ip_mac", str(index), {"ip": row["ip_address"], "mac": mac, "if_index": None, "interface_name": row.get("interface", ""), "state": row.get("age", "unknown")}, freshness="cached"))
            elif command == "show vlan":
                observations.append(Observation("vlan", str(index), {"vlan_id": int(row["vlan_id"]), "name": row["vlan_name"], "reported_ports": row.get("interfaces", []), "origin": "cli_show_vlan"}, freshness="fresh"))
            elif command == "show interfaces status":
                port = row["port"]
                observations.append(Observation("interface", str(index), {"if_index": None, "name": port, "alias": row.get("name", ""), "oper_status": row["status"]}, freshness="fresh"))
                vlan = numeric_vlan(row["vlan_id"])
                mode = "trunk" if row["vlan_id"] == "trunk" else "unknown"
                observations.append(Observation("port_vlan", str(index), {"bridge_port": None, "port_name": port, "pvid": vlan, "mode": mode}, freshness="fresh"))
            elif command == "show lldp neighbors detail":
                payload = {"local_port_num": None, "local_port_id": row["local_interface"], "remote_chassis_id": row["chassis_id"], "remote_port_id": row["neighbor_port_id"], "name": row.get("neighbor_name", "")}
                ip = row.get("mgmt_address")
                if ip:
                    try:
                        payload["management_ip"] = str(ipaddress.IPv4Address(ip))
                    except ValueError:
                        pass
                observations.append(Observation("lldp_neighbor", str(index), payload, freshness="fresh"))
        except (KeyError, ValueError, TypeError, AttributeError):
            raise MapperError("SSH_FIELDS_INVALID") from None
    return observations[:max_records]


async def in_thread(call, cleanup=None):
    """Cancellation must not abandon a live Netmiko session in a worker."""
    task = asyncio.create_task(asyncio.to_thread(call))
    try:
        return await asyncio.shield(task)
    except asyncio.CancelledError:
        try:
            result = await asyncio.shield(task)
            if cleanup is not None:
                await asyncio.shield(asyncio.to_thread(cleanup, result))
        except Exception:
            pass
        raise


async def collect_ssh(seed, profile, limits, cancel, connector=None):
    connection = None
    meta = {"target_id": seed["target_id"], "scope_id": "management:" + seed["target_id"], "context_id": seed.get("context", ""), "context_status": seed.get("context_status", "default")}
    started = time.monotonic()
    records = 0
    try:
        if seed.get("context"):
            yield TableResult("ssh", "session", status="unsupported", reason="SSH_CONTEXT_NOT_SUPPORTED", **meta)
            return
        values = credentials(profile)
        host_keys = Path(profile["known_hosts"]).expanduser()
        if not host_keys.is_file():
            raise MapperError("KNOWN_HOSTS_REQUIRED")
        if connector is None:
            from netmiko import ConnectHandler
            connector = ConnectHandler
        kwargs = {"device_type": "cisco_ios", "host": seed["ip"], "port": seed["port"], "username": values["user"], "password": values.get("password", ""), "use_keys": "password" not in values, "allow_agent": "password" not in values, "ssh_strict": True, "alt_host_keys": True, "alt_key_file": str(host_keys), "conn_timeout": 10, "auth_timeout": 15, "banner_timeout": 15, "allow_auto_change": False, "session_log": None}
        connection = await in_thread(partial(connector, **kwargs), cleanup=lambda session: session.disconnect())
        for command in COMMANDS:
            if cancel.is_set() or time.monotonic() - started > limits.device_timeout or records >= limits.device_records:
                yield TableResult("ssh", command, status="cancelled" if cancel.is_set() else "partial", reason="DEVICE_BUDGET_OR_CANCELLED", **meta)
                break
            at = now()
            try:
                rows = await in_thread(partial(connection.send_command, command, use_textfsm=True, raise_parsing_error=True, read_timeout=min(30, max(0.1, limits.device_timeout - (time.monotonic() - started)))))
                if isinstance(rows, str) and any(marker in rows for marker in ("% Invalid input", "% Unrecognized command", "% Unknown command")):
                    yield TableResult("ssh", command, status="unsupported", reason="SSH_COMMAND_UNSUPPORTED", **meta)
                    continue
                if not isinstance(rows, list):
                    raise MapperError("SSH_PARSER_NOT_CONFIRMED")
                allowed = min(limits.walk_records, limits.device_records - records)
                truncated = len(rows) > allowed
                observations = normalize(command, rows[:allowed], max_records=allowed)
                truncated = truncated or len(observations) >= allowed
                records += len(observations)
                yield TableResult("ssh", command, observations, status="partial" if truncated else "ok", exhausted=not truncated, reason="RECORD_LIMIT" if truncated else None, started_at=at, finished_at=now(), **meta)
            except MapperError as exc:
                yield TableResult("ssh", command, status="parse_error", reason=exc.code, **meta)
            except Exception as exc:
                name = type(exc).__name__.lower()
                status = "timeout" if "timeout" in name else "parse_error" if "pars" in name else "transport_error"
                yield TableResult("ssh", command, status=status, reason="SSH_COMMAND_FAILED", **meta)
    except MapperError as exc:
        yield TableResult("ssh", "session", status="auth_error", reason=exc.code, **meta)
    except Exception as exc:
        status = "auth_error" if "auth" in type(exc).__name__.lower() or "hostkey" in type(exc).__name__.lower() else "timeout" if "timeout" in type(exc).__name__.lower() else "transport_error"
        yield TableResult("ssh", "session", status=status, reason="SSH_SESSION_FAILED", **meta)
    finally:
        if connection is not None:
            try:
                await in_thread(connection.disconnect)
            except Exception:
                pass
