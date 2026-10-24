import asyncio
from dataclasses import dataclass
import ipaddress
import json
import os
import re
import socket
import sys

from ..errors import MapperError
from ..models import mac_text


@dataclass(frozen=True)
class CommandOutput:
    code: int
    text: str


async def run_command(args, timeout=5, max_output=2 * 1024**2):
    """No shell, no inherited diagnostic stderr, bounded stdout and lifetime."""
    process = None
    try:
        process = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL, env={**os.environ, "LC_ALL": "C", "LANG": "C"})
        async def read():
            chunks = []
            count = 0
            while chunk := await process.stdout.read(16384):
                count += len(chunk)
                if count > max_output:
                    raise MapperError("COMMAND_OUTPUT_LIMIT")
                chunks.append(chunk)
            await process.wait()
            return CommandOutput(process.returncode, b"".join(chunks).decode("utf-8", errors="replace"))
        return await asyncio.wait_for(read(), timeout)
    except TimeoutError:
        raise MapperError("COMMAND_TIMEOUT") from None
    except OSError:
        raise MapperError("COMMAND_UNAVAILABLE") from None
    finally:
        if process is not None and process.returncode is None:
            try:
                process.kill()
            except ProcessLookupError:
                pass
            await process.wait()


def interfaces():
    import psutil
    stats = psutil.net_if_stats()
    items = []
    for name, addresses in psutil.net_if_addrs().items():
        for a in addresses:
            if a.family != socket.AF_INET or not a.netmask or ipaddress.IPv4Address(a.address).is_loopback:
                continue
            try:
                index = socket.if_nametoindex(name)
            except OSError:
                index = None
            items.append({"interface": name, "index": index, "ip": a.address, "netmask": a.netmask, "is_up": bool(name in stats and stats[name].isup)})
    return items


def ipv4_prefix(text):
    if text == "default":
        return "0.0.0.0/0"
    address, slash, length = text.partition("/")
    parts = address.split(".")
    if len(parts) < 4:
        address += ".0" * (4 - len(parts))
        if not slash:
            length = str(len(parts) * 8)
    elif not slash:
        length = "32"
    return str(ipaddress.IPv4Network(address + "/" + length, strict=False))


def parse_macos_routes(text):
    if "Destination" not in text or "Netif" not in text:
        raise MapperError("ROUTE_PARSE_ERROR")
    header = None
    result = []
    for line in text.splitlines():
        words = line.split()
        if words and words[0] == "Destination":
            header = words.index("Netif")
            continue
        if not words or words[0] in {"Routing", "Internet:", "Internet6:"} or header is None:
            continue
        if len(words) <= header:
            raise MapperError("ROUTE_PARSE_ERROR")
        try:
            prefix = ipv4_prefix(words[0])
            gateway = str(ipaddress.IPv4Address(words[1])) if "G" in words[2] else None
        except ValueError:
            raise MapperError("ROUTE_PARSE_ERROR") from None
        result.append({"prefix": prefix, "next_hop": gateway, "interface": words[header], "metric": 0})
    return result


def parse_macos_neighbors(text, interface):
    result = []
    for line in text.splitlines():
        if not line.strip():
            continue
        m = re.search(r"\((\d+\.\d+\.\d+\.\d+)\) at (\S+) on (\S+)", line)
        if not m:
            raise MapperError("NEIGHBOR_PARSE_ERROR")
        ip, mac, iface = m.groups()
        if iface != interface:
            continue
        if mac == "(incomplete)":
            normalized = None
        else:
            parts = mac.split(":")
            normalized = mac_text(":".join(p.zfill(2) for p in parts))
        result.append({"ip": str(ipaddress.IPv4Address(ip)), "mac": normalized, "interface": iface, "state": "incomplete" if normalized is None else "cached"})
    return result


def json_records(text):
    try:
        data = json.loads(text.lstrip("\ufeff")) if text.strip() else None
    except ValueError:
        raise MapperError("SYSTEM_JSON_INVALID") from None
    if data is None:
        return []
    if isinstance(data, dict):
        return [data]
    if not isinstance(data, list) or any(not isinstance(row, dict) for row in data):
        raise MapperError("SYSTEM_JSON_INVALID")
    return data


def parse_windows_routes(text):
    result = []
    for row in json_records(text):
        try:
            hop = str(ipaddress.IPv4Address(row["NextHop"]))
            result.append({"prefix": str(ipaddress.IPv4Network(row["DestinationPrefix"])), "next_hop": None if hop == "0.0.0.0" else hop, "interface": str(row["InterfaceAlias"]), "metric": int(row["RouteMetric"]) + int(row["InterfaceMetric"])})
        except (ValueError, KeyError, TypeError):
            raise MapperError("ROUTE_PARSE_ERROR") from None
    return result


def parse_windows_neighbors(text, interface):
    result = []
    for row in json_records(text):
        try:
            if row["InterfaceAlias"] != interface:
                continue
            raw = row.get("LinkLayerAddress")
            mac = None if not raw or raw.replace("-", "").replace(":", "") == "000000000000" else mac_text(raw)
            result.append({"ip": str(ipaddress.IPv4Address(row["IPAddress"])), "mac": mac, "interface": interface, "state": str(row["State"])})
        except (ValueError, KeyError, TypeError):
            raise MapperError("NEIGHBOR_PARSE_ERROR") from None
    return result


def route_matches(ip, interface, routes):
    address = ipaddress.IPv4Address(ip)
    candidates = [(ipaddress.IPv4Network(r["prefix"]), r) for r in routes if address in ipaddress.IPv4Network(r["prefix"])]
    if not candidates:
        return False
    best_prefix = max(n.prefixlen for n, _ in candidates)
    candidates = [r for n, r in candidates if n.prefixlen == best_prefix]
    metric = min(r["metric"] for r in candidates)
    best = [r for r in candidates if r["metric"] == metric]
    return all(r["interface"] == interface and r["next_hop"] is None for r in best)


class SystemAdapter:
    def __init__(self, limits, runner=run_command, interface_reader=interfaces, platform=None):
        self.limits = limits
        self.runner = runner
        self.interface_reader = interface_reader
        self.platform = platform or sys.platform
        if self.platform not in {"darwin", "win32"}:
            raise MapperError("UNSUPPORTED_PLATFORM")

    def interfaces(self):
        return self.interface_reader()

    async def _read(self, command):
        result = await self.runner(command, self.limits.command_timeout)
        if result.code != 0:
            raise MapperError("SYSTEM_READ_FAILED")
        return result.text

    async def powershell(self, script):
        path = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "WindowsPowerShell", "v1.0", "powershell.exe")
        return await self._read([path, "-NoProfile", "-NonInteractive", "-Command", "$ErrorActionPreference='Stop'; [Console]::OutputEncoding=[Text.UTF8Encoding]::new(); " + script])

    async def routes(self):
        if self.platform == "darwin":
            return parse_macos_routes(await self._read(["/usr/sbin/netstat", "-rn", "-f", "inet"]))
        script = "Get-NetRoute -AddressFamily IPv4 | Select-Object DestinationPrefix,NextHop,InterfaceAlias,RouteMetric,@{n='InterfaceMetric';e={(Get-NetIPInterface -AddressFamily IPv4 -InterfaceIndex $_.InterfaceIndex).InterfaceMetric}} | ConvertTo-Json -Depth 3 -Compress"
        return parse_windows_routes(await self.powershell(script))

    async def neighbors(self, interface):
        if self.platform == "darwin":
            return parse_macos_neighbors(await self._read(["/usr/sbin/arp", "-an"]), interface)
        return parse_windows_neighbors(await self.powershell("Get-NetNeighbor -AddressFamily IPv4 | Select-Object InterfaceAlias,IPAddress,LinkLayerAddress,State | ConvertTo-Json -Depth 3 -Compress"), interface)

    async def probe(self, ip, interface, source_ip):
        ip = str(ipaddress.IPv4Address(ip))
        source_ip = str(ipaddress.IPv4Address(source_ip))
        selected = [i for i in self.interfaces() if i["interface"] == interface and i["ip"] == source_ip and i["is_up"]]
        if not selected or not route_matches(ip, interface, await self.routes()):
            return "skipped", "ROUTE_OR_INTERFACE_CHANGED"
        if self.platform == "darwin":
            args = ["/sbin/ping", "-n", "-c", "1", "-W", "1000", "-S", source_ip, ip]
        else:
            args = [os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "PING.EXE"), "-n", "1", "-w", "1000", "-4", ip]
        output = await self.runner(args, self.limits.ping_timeout)
        escaped = re.escape(ip)
        replied = any(re.search(r"\b" + escaped + r"(?:\s|:)", line) and re.search(r"\bttl[= :]\s*\d+", line, re.I) for line in output.text.splitlines())
        if replied:
            return "reply", None
        if output.code == 0:
            return "error", "PING_REPLY_NOT_CONFIRMED"
        # macOS ping(8): only exit 2 means sent but no reply; sysexits
        # errors (e.g. permissions, invalid invocation) are transport errors.
        no_reply_code = 2 if self.platform == "darwin" else 1
        if output.code != no_reply_code:
            return "error", "PING_PROCESS_FAILED"
        return "no_reply", None
