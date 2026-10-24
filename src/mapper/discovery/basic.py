import asyncio
import ipaddress
import time

from ..config import Limits
from ..errors import MapperError
from ..models import Observation, TableResult, now
from .system import SystemAdapter, route_matches


def target_plan(basic, interfaces, limits):
    network = ipaddress.IPv4Network(basic["cidr"])
    candidates = [i for i in interfaces if i["interface"] == basic["interface"] and i["is_up"] and network.subnet_of(ipaddress.IPv4Network(i["ip"] + "/" + i["netmask"], strict=False))]
    if len(candidates) != 1:
        raise MapperError("LOCAL_INTERFACE_NOT_UNIQUE")
    local = candidates[0]
    # Bound before iterating; never materialize a /8 only to reject it.
    count = network.num_addresses if network.prefixlen >= 31 else network.num_addresses - 2
    if ipaddress.IPv4Address(local["ip"]) in network:
        count -= 1
    if count > limits.max_targets:
        raise MapperError("TARGET_BUDGET_EXCEEDED")
    if network.network_address.is_multicast or network.network_address.is_loopback or network.network_address.is_unspecified:
        raise MapperError("INVALID_SCAN_RANGE")
    own = {i["ip"] for i in interfaces}
    targets = [str(ip) for ip in network.hosts() if str(ip) not in own and not ip.is_multicast and not ip.is_loopback]
    return local, targets


async def preview(basic, limits, adapter=None):
    adapter = adapter or SystemAdapter(limits)
    local, targets = target_plan(basic, adapter.interfaces(), limits)
    routes = await adapter.routes()
    return {"interface": local["interface"], "source_ip": local["ip"], "netmask": local["netmask"], "cidr": basic["cidr"], "targets": len(targets), "route_compatible": sum(route_matches(ip, local["interface"], routes) for ip in targets), "rate": limits.rate, "parallel": limits.ping_parallel, "timeout": limits.basic_timeout, "sends_probes": False}


async def collect_basic(basic, limits, cancel, adapter=None):
    adapter = adapter or SystemAdapter(limits)
    started = now()
    initial = adapter.interfaces()
    local, targets = target_plan(basic, initial, limits)
    iface = local["interface"]
    scope = iface + ":" + basic["cidr"]
    yield TableResult("os_interfaces", "interfaces", [Observation("local_interface", str(i["interface"]) + ":" + i["ip"], i, freshness="fresh") for i in initial], started_at=started, scope_id=scope)
    try:
        routes = await adapter.routes()
        yield TableResult("os_routes", "routes", [Observation("route", str(n), r, freshness="fresh") for n, r in enumerate(routes)], scope_id=scope)
    except MapperError as exc:
        yield TableResult("os_routes", "routes", status="parse_error", reason=exc.code, scope_id=scope)
        return
    before = {}
    for phase in ["before", "after"]:
        try:
            rows = await adapter.neighbors(iface)
            observations = []
            read_at = now()
            for row in rows:
                if ipaddress.IPv4Address(row["ip"]) not in ipaddress.IPv4Network(basic["cidr"]):
                    continue
                payload = {**row, "cache_read_at": read_at}
                if phase == "after":
                    payload["changed_since_before"] = row["mac"] is not None and before.get(row["ip"]) != row["mac"]
                else:
                    before[row["ip"]] = row["mac"]
                observations.append(Observation("neighbor", row["ip"], payload, freshness="cached"))
            yield TableResult("os_neighbors", "neighbors_" + phase, observations, scope_id=scope)
        except MapperError as exc:
            yield TableResult("os_neighbors", "neighbors_" + phase, status="parse_error", reason=exc.code, scope_id=scope)
        if phase == "after":
            break
        results = []
        index = 0
        next_start = time.monotonic()
        gate = asyncio.Lock()
        deadline = time.monotonic() + limits.basic_timeout

        async def worker():
            nonlocal index, next_start
            while index < len(targets) and not cancel.is_set() and time.monotonic() < deadline:
                async with gate:
                    if index >= len(targets):
                        return
                    ip = targets[index]
                    index += 1
                    delay = max(0, next_start - time.monotonic())
                    next_start = max(next_start, time.monotonic()) + 1 / limits.rate
                if delay:
                    await asyncio.sleep(delay)
                if cancel.is_set() or time.monotonic() >= deadline:
                    result, reason = "skipped", "CANCELLED_OR_DEADLINE"
                else:
                    try:
                        async with asyncio.timeout(max(0.001, deadline - time.monotonic())):
                            result, reason = await adapter.probe(ip, iface, local["ip"])
                    except (TimeoutError, MapperError) as exc:
                        result, reason = "error", exc.code if isinstance(exc, MapperError) else "BASIC_DEADLINE"
                at = now()
                results.append(Observation("probe_result", ip, {"ip": ip, "interface": iface, "result": result, "reason": reason}, observed_at=at, freshness="fresh" if result == "reply" else "unknown", evidence_at=at if result == "reply" else None))
        await asyncio.gather(*(worker() for _ in range(limits.ping_parallel)))
        done = {o.payload["ip"] for o in results}
        for ip in targets:
            if ip not in done:
                results.append(Observation("probe_result", ip, {"ip": ip, "interface": iface, "result": "skipped", "reason": "CANCELLED_OR_DEADLINE"}))
        status = "cancelled" if cancel.is_set() else "partial" if any(o.payload["result"] in {"error", "skipped"} for o in results) else "ok"
        yield TableResult("icmp", "host_discovery", results, status=status, scope_id=scope, started_at=started, finished_at=now(), reason="INCOMPLETE_TARGETS" if status != "ok" else None)
