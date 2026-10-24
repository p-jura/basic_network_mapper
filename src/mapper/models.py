from dataclasses import dataclass, field
from datetime import datetime, timezone
import ipaddress
import json
import re
from uuid import UUID, uuid4

from .errors import MapperError

STATUSES = {"ok", "empty", "partial", "unsupported", "auth_error", "timeout", "transport_error", "parse_error", "cancelled", "not_requested"}
EXECUTIONS = {"queued", "running", "finished", "cancelled", "interrupted", "failed"}
COVERAGES = {"complete", "partial", "unknown"}
SOURCES = {"os_interfaces", "os_routes", "os_neighbors", "icmp", "snmp", "ssh"}
# Required fields, followed by optional fields. No unvalidated arbitrary payloads.
SCHEMAS = {
    "local_interface": ({"interface", "ip", "netmask", "is_up"}, {"index"}),
    "route": ({"prefix", "interface"}, {"next_hop", "metric"}),
    "neighbor": ({"ip", "mac", "interface", "state"}, {"cache_read_at", "changed_since_before"}),
    "probe_result": ({"ip", "interface", "result"}, {"reason"}),
    "device_identity": (set(), {"name", "description", "object_id", "uptime", "model", "version"}),
    "interface": ({"if_index"}, {"name", "alias", "oper_status", "description", "mac"}),
    "ip_mac": ({"ip", "mac", "if_index"}, {"state", "entry_type", "interface_name"}),
    "bridge_port_map": ({"bridge_port", "if_index"}, set()),
    "fdb_entry": ({"mac", "bridge_port"}, {"fdb_id", "if_index", "vlan_id", "status", "port_name"}),
    "vlan": ({"vlan_id"}, {"name", "fdb_id", "time_mark", "origin", "egress_ports", "untagged_ports", "forbidden_ports", "reported_ports"}),
    "port_vlan": ({"bridge_port"}, {"pvid", "acceptable_frames", "ingress_filtering", "mode", "port_name"}),
    "lldp_local_port": ({"local_port_num"}, {"local_port_id", "local_port_subtype", "description"}),
    "lldp_neighbor": ({"local_port_num"}, {"local_port_id", "time_mark", "remote_index", "remote_chassis_id", "remote_chassis_subtype", "remote_port_id", "remote_port_subtype", "name", "management_ip"}),
}


def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def new_id():
    return str(uuid4())


def uuid_text(value):
    try:
        if str(UUID(value)) != value:
            raise ValueError()
    except (ValueError, TypeError, AttributeError):
        raise MapperError("INVALID_ID") from None
    return value


def timestamp(value):
    try:
        if not isinstance(value, str) or len(value) > 64 or datetime.fromisoformat(value.replace("Z", "+00:00")).utcoffset() is None:
            raise ValueError()
    except (ValueError, TypeError):
        raise MapperError("INVALID_TIMESTAMP") from None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def mac_text(value):
    if value is None:
        return None
    text = re.sub(r"[:.\-]", "", str(value)).lower()
    if not re.fullmatch(r"[0-9a-f]{12}", text) or text == "000000000000":
        raise MapperError("INVALID_MAC")
    return ":".join(text[i:i + 2] for i in range(0, 12, 2))


def safe_json(value, forbidden=()):
    try:
        text = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    except (ValueError, TypeError):
        raise MapperError("INVALID_DATA") from None
    if any(secret and secret in text for secret in forbidden):
        raise MapperError("SECRET_IN_OUTPUT")
    return text


def payload_for(kind, value):
    if kind not in SCHEMAS or not isinstance(value, dict):
        raise MapperError("INVALID_OBSERVATION")
    required, optional = SCHEMAS[kind]
    if not required <= value.keys() or not value.keys() <= required | optional:
        raise MapperError("INVALID_FIELDS")
    data = dict(value)
    for key, val in data.items():
        if val is None:
            continue
        if key in {"ip", "management_ip", "next_hop"}:
            try:
                data[key] = str(ipaddress.IPv4Address(val))
            except (ValueError, TypeError):
                raise MapperError("INVALID_IPV4") from None
        elif key == "prefix":
            try:
                data[key] = str(ipaddress.IPv4Network(val, strict=False))
            except (ValueError, TypeError):
                raise MapperError("INVALID_PREFIX") from None
        elif key == "netmask":
            try:
                ipaddress.IPv4Network("0.0.0.0/" + str(val))
            except ValueError:
                raise MapperError("INVALID_NETMASK") from None
        elif key == "mac":
            data[key] = mac_text(val)
        elif key in {"if_index", "bridge_port", "fdb_id", "vlan_id", "pvid", "index", "metric", "uptime", "time_mark", "local_port_num", "remote_index", "local_port_subtype", "remote_chassis_subtype", "remote_port_subtype", "acceptable_frames", "ingress_filtering"}:
            if type(val) is not int or val < 0 or (key in {"vlan_id", "pvid"} and not 1 <= val <= 4094):
                raise MapperError("INVALID_NUMBER")
        elif key in {"egress_ports", "untagged_ports", "forbidden_ports"}:
            if not isinstance(val, list) or len(val) > 65536 or any(type(n) is not int or not 1 <= n <= 65536 for n in val):
                raise MapperError("INVALID_PORT_LIST")
        elif key in {"is_up", "changed_since_before"}:
            if type(val) is not bool:
                raise MapperError("INVALID_BOOLEAN")
        elif key == "reported_ports":
            if not isinstance(val, list) or len(val) > 65536 or any(not isinstance(p, str) or len(p) > 256 for p in val):
                raise MapperError("INVALID_PORT_LIST")
        else:
            if key in {"state", "entry_type", "oper_status", "status"} and type(val) is int:
                continue
            if not isinstance(val, str) or len(val) > 4096 or "\x00" in val:
                raise MapperError("INVALID_FIELD_VALUE")
    if "cache_read_at" in data:
        data["cache_read_at"] = timestamp(data["cache_read_at"])
    if kind == "probe_result" and data["result"] not in {"reply", "no_reply", "error", "skipped"}:
        raise MapperError("INVALID_PROBE_RESULT")
    safe_json(data)
    return data


@dataclass(frozen=True)
class Observation:
    kind: str
    source_key: str
    payload: dict
    observed_at: str = field(default_factory=now)
    freshness: str = "unknown"
    evidence_at: str | None = None

    def __post_init__(self):
        if not isinstance(self.source_key, str) or not 1 <= len(self.source_key) <= 2048:
            raise MapperError("INVALID_SOURCE_KEY")
        if self.freshness not in {"fresh", "cached", "unknown"}:
            raise MapperError("INVALID_FRESHNESS")
        object.__setattr__(self, "observed_at", timestamp(self.observed_at))
        if self.evidence_at is not None:
            object.__setattr__(self, "evidence_at", timestamp(self.evidence_at))
        object.__setattr__(self, "payload", payload_for(self.kind, self.payload))


@dataclass
class TableResult:
    source: str
    table: str
    observations: list[Observation] = field(default_factory=list)
    status: str = "ok"
    exhausted: bool = True
    reason: str | None = None
    started_at: str = field(default_factory=now)
    finished_at: str = field(default_factory=now)
    target_id: str | None = None
    scope_id: str = "local"
    context_id: str = ""
    context_status: str = "default"

    def __post_init__(self):
        if self.source not in SOURCES or self.status not in STATUSES:
            raise MapperError("INVALID_STATUS")
        if self.context_status not in {"known", "default", "unknown"} or type(self.exhausted) is not bool:
            raise MapperError("INVALID_CONTEXT")
        for text, maximum in [(self.table, 256), (self.scope_id, 1024), (self.context_id, 256)]:
            if not isinstance(text, str) or len(text) > maximum or "\x00" in text:
                raise MapperError("INVALID_SOURCE_METADATA")
        if self.target_id is not None:
            uuid_text(self.target_id)
        self.started_at = timestamp(self.started_at)
        self.finished_at = timestamp(self.finished_at)
        if self.reason is not None and MapperError(self.reason).code != self.reason:
            raise MapperError("INVALID_REASON_CODE")
        if not self.observations and self.status == "ok":
            self.status = "empty"
        if self.status not in {"ok", "empty", "not_requested"}:
            self.exhausted = False
