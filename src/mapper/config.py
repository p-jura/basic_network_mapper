from dataclasses import asdict, dataclass, fields
import ipaddress
import json
import os
from pathlib import Path
import re
import sys
from uuid import UUID, uuid5

from .errors import MapperError
from .models import safe_json, uuid_text


@dataclass(frozen=True)
class Limits:
    max_targets: int = 256
    rate: float = 5
    ping_parallel: int = 4
    ping_timeout: float = 3
    basic_timeout: float = 240
    command_timeout: float = 5
    route_refresh_seconds: float = 1.0
    parallel: int = 4
    ssh_parallel: int = 2
    snmp_timeout: float = 3
    retries: int = 1
    bulk: int = 20
    walk_timeout: float = 60
    walk_records: int = 50000
    device_timeout: float = 300
    device_records: int = 200000
    cycle_timeout: float = 14400
    recursion_devices: int = 500
    recursion_depth: int = 8
    data_bytes: int = 2 * 1024**3

    def __post_init__(self):
        for f in fields(self):
            v = getattr(self, f.name)
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 < v < 2**40:
                if not (f.name in {"retries", "recursion_depth"} and type(v) is int and v == 0):
                    raise MapperError("INVALID_LIMIT")
            if isinstance(f.default, int) and type(v) is not int:
                raise MapperError("INVALID_LIMIT")
        if not 0.1 <= self.route_refresh_seconds <= 2:
            raise MapperError("INVALID_ROUTE_REFRESH")
        if self.parallel > 64 or self.ping_parallel > 64 or self.ssh_parallel > self.parallel:
            raise MapperError("INVALID_CONCURRENCY")


PROFILE_FIELDS = {"type", "community_env", "user_env", "auth_key_env", "priv_key_env", "password_env", "auth_protocol", "known_hosts", "device_type"}


def validate_profile(p):
    if not isinstance(p, dict) or not p.keys() <= PROFILE_FIELDS or p.get("type") not in {"snmp2", "snmp3", "ssh"}:
        raise MapperError("INVALID_PROFILE")
    for k, v in p.items():
        if not isinstance(v, str) or not v or len(v) > 4096:
            raise MapperError("INVALID_PROFILE")
        if k.endswith("_env") and not re.fullmatch(r"[A-Z][A-Z0-9_]{0,127}", v):
            raise MapperError("INVALID_ENV_REFERENCE")
    required = {"snmp2": {"community_env"}, "snmp3": {"user_env", "auth_key_env", "priv_key_env"}, "ssh": {"user_env", "known_hosts"}}[p["type"]]
    if not required <= p.keys() or p.get("auth_protocol", "sha256") not in {"sha256", "sha1"}:
        raise MapperError("INVALID_PROFILE")
    if p.get("device_type", "cisco_ios") != "cisco_ios":
        raise MapperError("UNSUPPORTED_SSH_PLATFORM")
    return dict(p)


def data_root(value=None):
    if value:
        return Path(value).expanduser().resolve()
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support/MapperSieci/projects"
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local"))) / "MapperSieci/projects"
    raise MapperError("UNSUPPORTED_PLATFORM_USE_DATA_DIR")


def project_dir(root, project_id):
    return Path(root) / uuid_text(project_id)


def load_config(path, project_id):
    try:
        if Path(path).stat().st_size > 1024 * 1024:
            raise MapperError("CONFIG_TOO_LARGE")
        c = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise MapperError("INVALID_CONFIG") from None
    allowed = {"schema_version", "project_id", "name", "basic", "seeds", "profiles", "allowed_ranges", "limits", "recursive", "recursive_profile_id"}
    if not isinstance(c, dict) or not c.keys() <= allowed or c.get("schema_version") != 1 or c.get("project_id") != project_id:
        raise MapperError("CONFIG_PROJECT_MISMATCH")
    try:
        c["limits"] = asdict(Limits(**c.get("limits", {})))
        c["allowed_ranges"] = [str(ipaddress.IPv4Network(n)) for n in c.get("allowed_ranges", [])]
    except (TypeError, ValueError):
        raise MapperError("INVALID_CONFIG") from None
    if not isinstance(c.get("profiles", {}), dict) or not isinstance(c.get("seeds", []), list):
        raise MapperError("INVALID_CONFIG")
    c["profiles"] = {k: validate_profile(v) for k, v in c.get("profiles", {}).items()}
    for seed in c.get("seeds", []):
        if not isinstance(seed, dict) or not seed.keys() <= {"ip", "port", "profile_id", "context", "context_status"}:
            raise MapperError("INVALID_SEED")
        try:
            seed["ip"] = str(ipaddress.IPv4Address(seed["ip"]))
            profile = c["profiles"][seed["profile_id"]]
        except (ValueError, KeyError, TypeError):
            raise MapperError("INVALID_SEED") from None
        port = seed.setdefault("port", 22 if profile["type"] == "ssh" else 161)
        if type(port) is not int or not 1 <= port <= 65535:
            raise MapperError("INVALID_PORT")
        if not isinstance(seed.get("context", ""), str) or seed.get("context_status", "default") not in {"known", "default", "unknown"}:
            raise MapperError("INVALID_CONTEXT")
    basic = c.get("basic")
    if basic is not None and (not isinstance(basic, dict) or not basic.keys() <= {"interface", "cidr"} or set(basic) != {"interface", "cidr"}):
        raise MapperError("INVALID_BASIC_CONFIG")
    if basic is not None:
        try:
            basic["cidr"] = str(ipaddress.IPv4Network(basic["cidr"]))
        except (ValueError, TypeError):
            raise MapperError("INVALID_PREFIX") from None
        if not isinstance(basic["interface"], str) or not basic["interface"]:
            raise MapperError("INVALID_INTERFACE")
    if type(c.get("recursive", False)) is not bool:
        raise MapperError("INVALID_CONFIG")
    if c.get("recursive") and c.get("recursive_profile_id") not in c["profiles"]:
        raise MapperError("RECURSION_NEEDS_PROFILE")
    safe_json(c)
    return c


def secret_values(config):
    names = {v for p in config.get("profiles", {}).values() for k, v in p.items() if k in {"community_env", "auth_key_env", "priv_key_env", "password_env"}}
    return tuple(os.environ[n] for n in names if os.environ.get(n))


def credentials(profile):
    result = {}
    for key, name in profile.items():
        if key.endswith("_env"):
            if name not in os.environ or not os.environ[name]:
                raise MapperError("MISSING_CREDENTIAL")
            result[key[:-4]] = os.environ[name]
    return result


def target_id(project_id, seed):
    key = safe_json([seed["ip"], seed["port"], seed.get("context", ""), seed["profile_id"]])
    return str(uuid5(UUID(project_id), key))
