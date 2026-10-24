"""Only the columns used by the mapper; retain source indices and contexts.

OID references: RFC 2863, RFC 4293, RFC 4188, RFC 4363, LLDP-MIB.
"""
from dataclasses import dataclass
import ipaddress

from ..errors import MapperError
from ..models import Observation, mac_text


@dataclass(frozen=True)
class Spec:
    root: str
    columns: dict


TABLES = {
    "system": Spec("1.3.6.1.2.1.1", {1: ("description", "text"), 2: ("object_id", "text"), 3: ("uptime", "int"), 5: ("name", "text")}),
    "interfaces": Spec("1.3.6.1.2.1.2.2.1", {1: ("if_index", "int"), 2: ("description", "text"), 6: ("mac", "mac"), 8: ("oper_status", "int")}),
    "interface_names": Spec("1.3.6.1.2.1.31.1.1.1", {1: ("name", "text"), 18: ("alias", "text")}),
    "arp_physical": Spec("1.3.6.1.2.1.4.35.1", {4: ("mac", "mac"), 6: ("entry_type", "int"), 7: ("state", "int")}),
    "arp_legacy": Spec("1.3.6.1.2.1.4.22.1", {2: ("mac", "mac"), 4: ("entry_type", "int")}),
    "bridge_ports": Spec("1.3.6.1.2.1.17.1.4.1", {2: ("if_index", "int")}),
    "fdb_q": Spec("1.3.6.1.2.1.17.7.1.2.2.1", {1: ("mac", "mac"), 2: ("bridge_port", "int"), 3: ("status", "int")}),
    "fdb_legacy": Spec("1.3.6.1.2.1.17.4.3.1", {1: ("mac", "mac"), 2: ("bridge_port", "int"), 3: ("status", "int")}),
    "vlan_current": Spec("1.3.6.1.2.1.17.7.1.4.2.1", {3: ("fdb_id", "int"), 4: ("egress_ports", "ports"), 5: ("untagged_ports", "ports")}),
    "vlan_static": Spec("1.3.6.1.2.1.17.7.1.4.3.1", {1: ("name", "text"), 2: ("egress_ports", "ports"), 3: ("forbidden_ports", "ports"), 4: ("untagged_ports", "ports")}),
    "port_vlan": Spec("1.3.6.1.2.1.17.7.1.4.5.1", {1: ("pvid", "int"), 2: ("acceptable_frames", "int"), 3: ("ingress_filtering", "int")}),
    "lldp_local": Spec("1.0.8802.1.1.2.1.3.7.1", {2: ("local_port_subtype", "int"), 3: ("local_port_id", "identifier"), 4: ("description", "text")}),
    "lldp_remote": Spec("1.0.8802.1.1.2.1.4.1.1", {4: ("remote_chassis_subtype", "int"), 5: ("remote_chassis_id", "identifier"), 6: ("remote_port_subtype", "int"), 7: ("remote_port_id", "identifier"), 9: ("name", "text")}),
    "lldp_addresses": Spec("1.0.8802.1.1.2.1.4.2.1", {3: ("unused", "int")}),
}


def oid_tuple(value):
    return tuple(int(n) for n in str(value).strip(".").split("."))


def octets(value):
    if isinstance(value, bytes):
        return value
    if hasattr(value, "asOctets"):
        return value.asOctets()
    raise MapperError("SNMP_OCTETS_REQUIRED")


def port_list(value):
    return [offset * 8 + bit + 1 for offset, octet in enumerate(octets(value)) for bit in range(8) if octet & (0x80 >> bit)]


def decode(value, kind):
    if kind == "int":
        return int(value)
    if kind == "ports":
        return port_list(value)
    if kind == "mac":
        raw = octets(value)
        if not raw or raw == bytes(len(raw)):
            return None
        return mac_text(raw.hex())
    if kind == "identifier":
        try:
            raw = octets(value)
            return "hex:" + raw.hex()  # subtype retained; never guess an ifIndex
        except MapperError:
            return str(value)
    if isinstance(value, bytes) or hasattr(value, "asOctets"):
        return octets(value).decode("utf-8", errors="replace").replace("\x00", "")
    return str(value)


def normalize(table, bindings):
    spec = TABLES[table]
    prefix = oid_tuple(spec.root)
    rows = {}
    skipped = 0
    for oid, value in bindings:
        oid = tuple(oid)
        suffix = oid[len(prefix):]
        if oid[:len(prefix)] != prefix or len(suffix) < 2:
            raise MapperError("SNMP_INVALID_INDEX")
        column, index = suffix[0], suffix[1:]
        if column not in spec.columns:
            continue
        name, kind = spec.columns[column]
        try:
            rows.setdefault(index, {})[name] = decode(value, kind)
        except (ValueError, TypeError):
            raise MapperError("SNMP_INVALID_VALUE") from None
    results = []
    for index, data in rows.items():
        kind = None
        if table == "system":
            kind = "device_identity"
        elif table in {"interfaces", "interface_names"}:
            kind = "interface"; data["if_index"] = index[0]
        elif table == "arp_physical":
            if len(index) != 7 or index[1:3] != (1, 4):
                skipped += 1; continue
            kind = "ip_mac"; data.update(ip=str(ipaddress.IPv4Address(bytes(index[3:]))), if_index=index[0])
            data.setdefault("mac", None)
        elif table == "arp_legacy":
            if len(index) != 5:
                raise MapperError("SNMP_INVALID_INDEX")
            kind = "ip_mac"; data.update(ip=str(ipaddress.IPv4Address(bytes(index[1:]))), if_index=index[0]); data.setdefault("mac", None)
        elif table == "bridge_ports":
            kind = "bridge_port_map"; data["bridge_port"] = index[0]
        elif table in {"fdb_q", "fdb_legacy"}:
            expected = 7 if table == "fdb_q" else 6
            if len(index) != expected:
                raise MapperError("SNMP_INVALID_INDEX")
            kind = "fdb_entry"
            data.setdefault("mac", mac_text(bytes(index[-6:]).hex()))
            data.setdefault("bridge_port", None)
            data["fdb_id"] = index[0] if table == "fdb_q" else None
            data["vlan_id"] = None
        elif table == "vlan_current":
            if len(index) != 2:
                raise MapperError("SNMP_INVALID_INDEX")
            kind = "vlan"; data.update(time_mark=index[0], vlan_id=index[1], origin="current")
        elif table == "vlan_static":
            kind = "vlan"; data.update(vlan_id=index[0], origin="static")
        elif table == "port_vlan":
            kind = "port_vlan"; data["bridge_port"] = index[0]; data["mode"] = "unknown"
        elif table == "lldp_local":
            kind = "lldp_local_port"; data["local_port_num"] = index[0]
        elif table in {"lldp_remote", "lldp_addresses"}:
            if len(index) < 3:
                raise MapperError("SNMP_INVALID_INDEX")
            kind = "lldp_neighbor"
            data.update(time_mark=index[0], local_port_num=index[1], remote_index=index[2])
            if table == "lldp_addresses":
                data.pop("unused", None)
                if len(index) != 9 or index[3:5] != (1, 4):
                    skipped += 1; continue
                data["management_ip"] = str(ipaddress.IPv4Address(bytes(index[5:])))
        if kind:
            # A fresh FDB/ARP read is not a fresh response from the end host.
            freshness = "cached" if kind in {"ip_mac", "fdb_entry"} else "fresh"
            results.append(Observation(kind, ".".join(map(str, index)), data, freshness=freshness))
    return results, skipped
