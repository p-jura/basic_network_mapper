"""Private consistent backup and offline installation receipt. No collectors."""
import argparse
from contextlib import closing
import importlib.metadata
import json
from pathlib import Path
import platform
import sqlite3
import sys


def backup(root, pid, destination):
    from mapper.storage import Repository
    from mapper.private_files import private_directory, private_file, protect
    from mapper.models import uuid_text
    from mapper.ui.data import config_read, forbidden
    pid = uuid_text(pid)
    config = config_read(root, pid)
    destination = Path(destination).expanduser().absolute()
    # Never overwrite a backup or copy a live SQLite database as a plain file.
    private_directory(destination)
    with Repository(root, pid, forbidden=forbidden(config)) as repo:
        with private_file(destination / 'project.json') as stream:
            stream.write(repo._json(config) + '\n')
        path = destination / 'mapper.sqlite3'
        with private_file(path):
            pass
        with closing(sqlite3.connect(path)) as copy:
            repo.db.backup(copy)
            if copy.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise RuntimeError('BACKUP_INTEGRITY_FAILED')
        protect(path)
    return {'status': 'backup_ok', 'backup': str(destination), 'sends_probes': False}


def receipt(root):
    import mapper
    from mapper.cli import demo
    from mapper.storage import Repository
    from mapper.topology.service import build
    from mapper.ui.data import export_private
    from mapper.private_files import private_file
    root = Path(root).expanduser().absolute()
    # Data root must be a fresh directory supplied specifically for this receipt.
    if root.exists():
        raise RuntimeError('RECEIPT_ROOT_ALREADY_EXISTS')
    project = demo(root)
    with Repository(root, project['project_id']) as repo:
        graph = build(repo)
        integrity = repo.db.execute('PRAGMA integrity_check').fetchone()[0]
        fk = len(repo.db.execute('PRAGMA foreign_key_check').fetchall())
    exports = [str(export_private(root, project['project_id'], graph, kind)) for kind in
               ['topology-json', 'nodes-csv', 'edges-csv', 'source-json', 'source-csv']]
    result = {'mapper': mapper.__version__, 'installed_mapper': importlib.metadata.version('mapper-sieci'),
              'module_file': mapper.__file__, 'python': platform.python_version(), 'system': platform.platform(),
              'machine': platform.machine(), 'nodes': len(graph['nodes']), 'edges': len(graph['edges']),
              'integrity': integrity, 'foreign_key_errors': fk, 'exports': exports,
              'project_id': project['project_id'], 'sends_probes': False,
              'not_tested': ['physical LAN', 'SNMP/SSH hardware', 'NTFS second-account access', 'PNG/SVG browser', 'physical Internet disconnection']}
    with private_file(root / 'installation-receipt.json') as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description='Mapper: odbiór offline / spójny backup')
    sub = parser.add_subparsers(dest='action', required=True)
    p = sub.add_parser('receipt'); p.add_argument('--data-dir', required=True)
    p = sub.add_parser('backup'); p.add_argument('--data-dir', required=True); p.add_argument('--project', required=True); p.add_argument('--output', required=True)
    args = parser.parse_args()
    try:
        result = receipt(args.data_dir) if args.action == 'receipt' else backup(args.data_dir, args.project, args.output)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception as exc:
        # No raw exception/payload: a private project config may reference secrets.
        print(json.dumps({'status': 'failed', 'error': getattr(exc, 'code', type(exc).__name__), 'sends_probes': False}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
