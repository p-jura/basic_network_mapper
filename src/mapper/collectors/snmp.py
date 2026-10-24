import asyncio
import time

from ..config import credentials
from ..errors import MapperError
from ..models import TableResult, now
from .snmp_tables import TABLES, normalize, oid_tuple


class SnmpTransport:
    """Read-only facade; no SET method or automatic MIB downloads."""

    def __init__(self, seed, profile, limits):
        self.seed, self.profile, self.limits = seed, profile, limits
        self.engine = None

    async def __aenter__(self):
        from pysnmp.hlapi.v3arch import asyncio as h
        values = credentials(self.profile)
        self.h = h
        self.engine = h.SnmpEngine()
        try:
            if self.profile["type"] == "snmp2":
                self.auth = h.CommunityData(values["community"], mpModel=1)
            else:
                auth_protocol = h.USM_AUTH_HMAC192_SHA256 if self.profile.get("auth_protocol", "sha256") == "sha256" else h.USM_AUTH_HMAC96_SHA
                self.auth = h.UsmUserData(values["user"], authKey=values["auth_key"], privKey=values["priv_key"], authProtocol=auth_protocol, privProtocol=h.USM_PRIV_CFB128_AES)
            self.target = await h.UdpTransportTarget.create((self.seed["ip"], self.seed["port"]), timeout=self.limits.snmp_timeout, retries=self.limits.retries)
            self.context = h.ContextData(contextName=self.seed.get("context", ""))
        except BaseException:
            self.engine.close_dispatcher()
            raise
        return self

    async def __aexit__(self, *_):
        if self.engine is not None:
            self.engine.close_dispatcher()

    def _check(self, result):
        from pysnmp.proto import errind
        indication, status, _index, bindings = result
        if indication:
            if isinstance(indication, errind.RequestTimedOut):
                raise MapperError("SNMP_TIMEOUT")
            # Never format an indication which could contain credentials.
            if any(word in type(indication).__name__.lower() for word in ("auth", "digest", "user", "decrypt")):
                raise MapperError("SNMP_AUTH_ERROR")
            raise MapperError("SNMP_TRANSPORT_ERROR")
        if status:
            raise MapperError("SNMP_AGENT_ERROR")
        return bindings

    async def bulk(self, cursor):
        h = self.h
        bindings = self._check(await h.bulk_cmd(self.engine, self.auth, self.target, self.context, 0, self.limits.bulk, h.ObjectType(h.ObjectIdentity(".".join(map(str, cursor)))), lookupMib=False))
        from pysnmp.proto.rfc1905 import EndOfMibView, NoSuchInstance, NoSuchObject
        return [(tuple(oid), value, "unsupported" if isinstance(value, (NoSuchInstance, NoSuchObject)) else "end" if isinstance(value, EndOfMibView) else "value") for oid, value in bindings]

    async def uptime(self):
        h = self.h
        bindings = self._check(await h.get_cmd(self.engine, self.auth, self.target, self.context, h.ObjectType(h.ObjectIdentity("1.3.6.1.2.1.1.3.0")), lookupMib=False))
        return int(bindings[0][1])


async def bounded_walk(transport, root, limits, cancel, remaining):
    prefix = oid_tuple(root)
    cursor = prefix
    values = []
    deadline = time.monotonic() + limits.walk_timeout
    limit = min(limits.walk_records, remaining)
    while True:
        if cancel.is_set():
            return values, "cancelled", "CANCELLED"
        if len(values) >= limit:
            return values, "partial", "RECORD_LIMIT"
        if time.monotonic() >= deadline:
            return values, "partial", "WALK_DEADLINE"
        try:
            batch = await asyncio.wait_for(transport.bulk(cursor), max(0.001, deadline - time.monotonic()))
        except TimeoutError:
            return values, "timeout", "WALK_DEADLINE"
        except MapperError as exc:
            status = "timeout" if exc.code == "SNMP_TIMEOUT" else "auth_error" if exc.code in {"SNMP_AUTH_ERROR", "MISSING_CREDENTIAL"} else "transport_error"
            return values, status, exc.code
        if not batch:
            # Empty PDU is not evidence of an exhausted table.
            return values, "partial", "EMPTY_SNMP_PDU"
        for oid, value, state in batch:
            if state == "unsupported":
                return values, "unsupported", "SNMP_OBJECT_UNAVAILABLE"
            if state == "end" or tuple(oid)[:len(prefix)] != prefix:
                return values, "ok", None
            if tuple(oid) <= cursor:
                return values, "partial", "NON_INCREASING_OID"
            cursor = tuple(oid)
            values.append((cursor, value))
            if len(values) >= limit:
                return values, "partial", "RECORD_LIMIT"


async def collect_snmp(seed, profile, limits, cancel, transport_factory=SnmpTransport):
    started = time.monotonic()
    count = 0
    metadata = {"target_id": seed["target_id"], "scope_id": "management:" + seed["target_id"], "context_id": seed.get("context", ""), "context_status": seed.get("context_status", "default")}
    try:
        async with transport_factory(seed, profile, limits) as transport:
            before = await asyncio.wait_for(transport.uptime(), limits.snmp_timeout * (limits.retries + 1) + 1)
            for name, spec in TABLES.items():
                if cancel.is_set() or time.monotonic() - started >= limits.device_timeout or count >= limits.device_records:
                    yield TableResult("snmp", name, status="cancelled" if cancel.is_set() else "partial", reason="DEVICE_BUDGET_OR_CANCELLED", **metadata)
                    break
                at = now()
                remaining_time = limits.device_timeout - (time.monotonic() - started)
                try:
                    raw, status, reason = await asyncio.wait_for(bounded_walk(transport, spec.root, limits, cancel, limits.device_records - count), max(0.001, remaining_time))
                    count += len(raw)
                    observations, skipped = normalize(name, raw)
                    if skipped and reason is None:
                        reason = "NON_IPV4_SKIPPED"
                except TimeoutError:
                    yield TableResult("snmp", name, status="timeout", reason="DEVICE_DEADLINE", **metadata)
                    break
                except (MapperError, ValueError, TypeError, IndexError):
                    yield TableResult("snmp", name, status="parse_error", reason="SNMP_NORMALIZATION_FAILED", **metadata)
                    continue
                yield TableResult("snmp", name, observations, status=status, exhausted=status == "ok", reason=reason, started_at=at, finished_at=now(), **metadata)
                if status in {"auth_error", "cancelled"}:
                    break
            if not cancel.is_set() and time.monotonic() - started < limits.device_timeout:
                try:
                    after = await asyncio.wait_for(transport.uptime(), min(limits.snmp_timeout * (limits.retries + 1) + 1, limits.device_timeout - (time.monotonic() - started)))
                    if after < before:
                        yield TableResult("snmp", "consistency", status="partial", reason="DEVICE_RESTARTED", **metadata)
                except (MapperError, TimeoutError):
                    yield TableResult("snmp", "consistency", status="partial", reason="UPTIME_NOT_CONFIRMED", **metadata)
    except MapperError as exc:
        yield TableResult("snmp", "session", status="auth_error" if exc.code in {"MISSING_CREDENTIAL", "SNMP_AUTH_ERROR"} else "timeout" if exc.code == "SNMP_TIMEOUT" else "transport_error", reason=exc.code, **metadata)
    except TimeoutError:
        yield TableResult("snmp", "session", status="timeout", reason="SNMP_SESSION_TIMEOUT", **metadata)
    except Exception:
        yield TableResult("snmp", "session", status="transport_error", reason="SNMP_SESSION_FAILED", **metadata)
