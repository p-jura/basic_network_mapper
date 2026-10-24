import argparse
import asyncio
from dataclasses import asdict
import importlib.metadata
import json
from pathlib import Path
import platform
import sqlite3
import sys

from . import __version__
from .config import Limits, data_root, load_config, secret_values
from .errors import MapperError
from .models import Observation, TableResult, new_id, safe_json, uuid_text
from .storage import Repository
from .storage.repository import cycle_lock
from .snapshots import export_snapshot, import_snapshot


class Parser(argparse.ArgumentParser):
    def error(self, _message):
        # Do not echo arbitrary argv, which may contain a mistakenly pasted key.
        raise MapperError("INVALID_ARGUMENTS_USE_HELP")


def parser():
    p = Parser(prog="mapper", description="Lokalny mapper IPv4 — kolektory tylko do odczytu")
    p.add_argument("--version", action="version", version=__version__)
    def shared(obj):
        obj.add_argument("--data-dir", default=argparse.SUPPRESS, help="Katalog projektów; domyślnie katalog danych użytkownika")
        return obj
    shared(p)
    sub = p.add_subparsers(dest="area", required=True)
    shared(sub.add_parser("doctor", help="Wersje lokalnych komponentów, bez sieci"))
    shared(sub.add_parser("interfaces", help="Lokalna lista interfejsów IPv4, bez sond"))
    shared(sub.add_parser("demo", help="Syntetyczny projekt do odbioru offline"))
    projects = sub.add_parser("project").add_subparsers(dest="action", required=True)
    create = shared(projects.add_parser("create"))
    create.add_argument("--name", required=True)
    collect = shared(sub.add_parser("collect"))
    collect.add_argument("--project", required=True)
    collect.add_argument("--config")
    mode = collect.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preview", action="store_true")
    mode.add_argument("--run", action="store_true")
    snapshots = sub.add_parser("snapshot").add_subparsers(dest="action", required=True)
    listing = shared(snapshots.add_parser("list"))
    listing.add_argument("--project", required=True)
    listing.add_argument("--complete", action="store_true")
    export = shared(snapshots.add_parser("export"))
    export.add_argument("--project", required=True)
    export.add_argument("--cycle")
    export.add_argument("--output", required=True)
    export.add_argument("--format", choices=["json", "csv"], default="json")
    imp = shared(snapshots.add_parser("import"))
    imp.add_argument("--new-project", action="store_true", required=True)
    imp.add_argument("--input", required=True)
    imp.add_argument("--name", default="Imported snapshot")
    imp.add_argument("--max-bytes", type=int, default=100 * 1024**2)
    imp.add_argument("--max-records", type=int, default=200000)
    topology = sub.add_parser("topology", help="Topologia wyłącznie z zapisanych danych").add_subparsers(dest="action", required=True)
    for action in ["build", "export", "view"]:
        command = shared(topology.add_parser(action))
        command.add_argument("--project", required=True)
        command.add_argument("--cycle")
        command.add_argument("--max-skew", type=int, default=300)
        if action == "export":
            command.add_argument("--output", required=True)
        if action == "view":
            command.add_argument("--port", type=int, default=8050)
            command.add_argument("--no-browser", action="store_true")
    hist = shared(sub.add_parser("history", help="Historia obserwacji; bez sond"))
    hist.add_argument("--project", required=True)
    hist.add_argument("--limit", type=int, default=100)
    hist.add_argument("--rules-version")
    return p


def project_create(root, name):
    if not isinstance(name, str) or not 1 <= len(name) <= 128 or "\x00" in name:
        raise MapperError("INVALID_PROJECT_NAME")
    pid = new_id()
    with cycle_lock(root), Repository(root, pid, create_name=name) as repo:
        config = {"schema_version": 1, "project_id": pid, "name": name, "basic": None, "seeds": [], "profiles": {}, "allowed_ranges": [], "limits": asdict(Limits()), "recursive": False}
        with (repo.directory / "project.json").open("x", encoding="utf-8") as f:
            f.write(json.dumps(config, ensure_ascii=False, indent=2) + "\n")
        (repo.directory / "project.json").chmod(0o600)
        return {"project_id": pid, "config": str(repo.directory / "project.json"), "database": str(repo.path)}


def demo(root):
    project = project_create(root, "Demo offline — dane syntetyczne")
    with cycle_lock(root), Repository(root, project["project_id"]) as repo:
        cycle_id = repo.begin_cycle({"project_id": project["project_id"], "sends_probes": False}, origin="synthetic")
        interface = {"interface": "demo0", "index": 1, "ip": "192.0.2.10", "netmask": "255.255.255.0", "is_up": True}
        repo.write_result(cycle_id, TableResult("os_interfaces", "interfaces", [Observation("local_interface", "demo0", interface, freshness="fresh")], scope_id="demo0:192.0.2.0/24"))
        repo.write_result(cycle_id, TableResult("os_neighbors", "neighbors_before", [Observation("neighbor", "192.0.2.20", {"ip": "192.0.2.20", "mac": "02:00:00:00:00:20", "interface": "demo0", "state": "cached"}, freshness="cached")], scope_id="demo0:192.0.2.0/24"))
        repo.write_result(cycle_id, TableResult("icmp", "host_discovery", [Observation("probe_result", "192.0.2.20", {"ip": "192.0.2.20", "interface": "demo0", "result": "reply"}, freshness="fresh")], scope_id="demo0:192.0.2.0/24"))
        repo.publish(cycle_id)
    return {**project, "cycle_id": cycle_id, "synthetic": True, "sends_probes": False}


def execute(args):
    if args.area == "doctor":
        versions = {}
        for name in ["psutil", "pysnmp", "netmiko", "ntc-templates", "cryptography", "networkx", "dash", "dash-cytoscape"]:
            try:
                versions[name] = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:
                versions[name] = "not_installed"
        return {"mapper": __version__, "python": platform.python_version(), "platform": platform.system(), "architecture": platform.machine(), "sqlite": sqlite3.sqlite_version, "dependencies": versions, "sends_probes": False}
    if args.area == "interfaces":
        from .discovery.system import interfaces
        return {"interfaces": interfaces(), "sends_probes": False}
    root = data_root(getattr(args, "data_dir", None))
    if args.area == "project":
        return project_create(root, args.name)
    if args.area == "demo":
        return demo(root)
    if args.area == "snapshot" and args.action == "import":
        return {"project_id": import_snapshot(root, args.input, name=args.name, max_bytes=args.max_bytes, max_records=args.max_records), "origin": "imported", "sends_probes": False}
    uuid_text(args.project)
    if args.area == "collect":
        from .cycle import preview, run_cycle
        cfg_path = Path(args.config) if args.config else root / args.project / "project.json"
        config = load_config(cfg_path, args.project)
        forbidden = secret_values(config)
        plan = asyncio.run(preview(config))
        print(safe_json({"preview": plan}, forbidden), flush=True)
        if args.preview:
            return {"status": "preview_only", "sends_probes": False}
        with Repository(root, args.project, forbidden=forbidden, max_bytes=config["limits"]["data_bytes"]) as repo:
            return asyncio.run(run_cycle(repo, config))
    if args.area in {"topology", "history"}:
        from .topology.service import build, history, summary
        with cycle_lock(root), Repository(root, args.project) as repo:
            if args.area == "history":
                return {"events": history(repo, limit=args.limit, rules_version=args.rules_version), "sends_probes": False}
            graph = build(repo, args.cycle, max_skew=args.max_skew)
            if args.action == "export":
                with Path(args.output).open("x", encoding="utf-8") as output:
                    output.write(repo._json(graph) + "\n")
                Path(args.output).chmod(0o600)
            result = summary(graph)
        if args.action == "view":
            from .topology.preview import view
            view(graph, port=args.port, open_browser=not args.no_browser)
        return result
    with Repository(root, args.project) as repo:
        if args.action == "list":
            return {"snapshots": repo.snapshots(complete=args.complete), "sends_probes": False}
        export_snapshot(repo, args.output, args.cycle, csv_format=args.format == "csv")
        return {"status": "exported", "format": args.format, "sends_probes": False}


def main(argv=None):
    try:
        result = execute(parser().parse_args(argv))
        print(safe_json(result))
        return 130 if result.get("execution_status") == "cancelled" else 0
    except MapperError as exc:
        print(safe_json({"error": exc.code}), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print('{"error":"CANCELLED"}', file=sys.stderr)
        return 130
    except (OSError, sqlite3.Error):
        print('{"error":"LOCAL_IO_FAILED"}', file=sys.stderr)
        return 3
    except Exception:
        print('{"error":"INTERNAL_ERROR"}', file=sys.stderr)
        return 3
