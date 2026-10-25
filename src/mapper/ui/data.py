"""Project operations and bounded private import/export, independent of widgets."""
import base64
import binascii
import csv
import io
import json
import os
from pathlib import Path

from ..config import load_config, validate_config, project_dir, secret_values
from ..errors import MapperError
from ..models import new_id, safe_json, uuid_text
from ..private_files import private_directory, private_file, reject_link, protect
from ..snapshots import MAX_BYTES, import_snapshot, export_snapshot
from ..storage import Repository
from ..topology.service import build, history


def forbidden(config):
    # Usernames also remain on the server; references, never values, enter UI.
    return tuple({*secret_values(config), *(os.environ[v] for p in config.get('profiles', {}).values()
                  for k, v in p.items() if k.endswith('_env') and os.environ.get(v))})


def config_path(root, pid):
    folder = project_dir(root, pid)
    reject_link(folder)
    path = folder / 'project.json'
    reject_link(path)
    return path


def config_read(root, pid):
    return load_config(config_path(root, pid), uuid_text(pid))


def projects(root):
    result = []
    if not Path(root).exists():
        return result
    for folder in Path(root).iterdir():
        try:
            pid = uuid_text(folder.name)
            if folder.is_symlink() or not folder.is_dir():
                continue
            config = config_read(root, pid)
            result.append({'label': str(config.get('name') or pid)[:128] + ' · ' + pid[:8], 'value': pid})
        except (MapperError, OSError):
            continue
    return sorted(result, key=lambda row: (row['label'].casefold(), row['value']))


def save_config(root, pid, config):
    config = validate_config(config, uuid_text(pid))
    path = config_path(root, pid)
    with Repository(root, pid, forbidden=forbidden(config)):
        temporary = path.with_name('.config-' + new_id() + '.tmp')
        try:
            with private_file(temporary) as stream:
                stream.write(safe_json(config, forbidden(config)) + '\n')
                stream.flush()
                os.fsync(stream.fileno())
            reject_link(path)
            os.replace(temporary, path)
            protect(path)
        finally:
            temporary.unlink(missing_ok=True)
    return config


def read_view(root, pid, cycle=None):
    config = config_read(root, pid)
    with Repository(root, pid, forbidden=forbidden(config)) as repo:
        graph = build(repo, cycle)
        repo._json(graph)
        return {'graph': graph, 'history': history(repo, limit=100), 'snapshots': repo.snapshots()}


def credential_status(config):
    return {name: bool(os.environ.get(name)) for profile in config.get('profiles', {}).values()
            for key, name in profile.items() if key.endswith('_env')}


def import_upload(root, contents, name='Import offline'):
    if not isinstance(contents, str) or len(contents) > ((MAX_BYTES + 2) // 3) * 4 + 256:
        raise MapperError('IMPORT_SIZE_LIMIT')
    head, sep, encoded = contents.partition(',')
    if not sep or not head.endswith(';base64'):
        raise MapperError('INVALID_SNAPSHOT')
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error):
        raise MapperError('INVALID_SNAPSHOT') from None
    if len(raw) > MAX_BYTES:
        raise MapperError('IMPORT_SIZE_LIMIT')
    folder = Path(root) / '.imports'
    if not folder.exists():
        private_directory(folder)
    protect(folder, directory=True)
    path = folder / (new_id() + '.json')
    try:
        with private_file(path) as stream:
            stream.write(raw.decode('utf-8-sig'))
        return import_snapshot(root, path, name=name)
    except UnicodeError:
        raise MapperError('INVALID_SNAPSHOT') from None
    finally:
        path.unlink(missing_ok=True)


def csv_text(rows, columns):
    stream = io.StringIO(newline='')
    writer = csv.writer(stream)
    writer.writerow(columns)
    for row in rows:
        cells = []
        for key in columns:
            value = row.get(key)
            if isinstance(value, (dict, list)):
                value = safe_json(value)
            if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@')):
                value = "'" + value
            if isinstance(value, str) and value.startswith(('\t', '\r', '\n')):
                value = "'" + value
            cells.append(value)
        writer.writerow(cells)
    return stream.getvalue()


def export_content(graph, kind):
    if kind == 'topology-json':
        return safe_json(graph), 'json'
    if kind in {'nodes-csv', 'edges-csv'}:
        group = 'nodes' if kind == 'nodes-csv' else 'edges'
        rows = [{**row, 'snapshot_id': graph['snapshot_id'], 'rules_version': graph['rules_version']}
                for row in graph[group]]
        # All derived fields, including evidence and uncertainty, remain available.
        columns = ['snapshot_id', 'rules_version', 'id', 'kind'] + sorted(set().union(*(r.keys() for r in rows)) - {'snapshot_id', 'rules_version', 'id', 'kind'})
        return csv_text(rows, columns), 'csv'
    raise MapperError('INVALID_EXPORT_FORMAT')


def export_private(root, pid, graph, kind):
    if kind not in {'topology-json', 'nodes-csv', 'edges-csv', 'source-json', 'source-csv'}:
        raise MapperError('INVALID_EXPORT_FORMAT')
    if graph['project_id'] != uuid_text(pid):
        raise MapperError('EXPORT_PROJECT_MISMATCH')
    config = config_read(root, pid)
    folder = project_dir(root, pid) / 'exports'
    if not folder.exists():
        private_directory(folder)
    protect(folder, directory=True)
    suffix = 'csv' if kind.endswith('csv') else 'json'
    path = folder / (graph['snapshot_id'] + '-' + kind + '-' + new_id() + '.' + suffix)
    size = sum(p.stat().st_size for p in project_dir(root, pid).rglob('*') if p.is_file() and not p.is_symlink())
    budget = config['limits']['data_bytes']
    if size >= budget:
        raise MapperError('DATA_BUDGET_EXCEEDED')
    if kind in {'source-json', 'source-csv'}:
        with Repository(root, pid, forbidden=forbidden(config)) as repo:
            snaps = {s['snapshot_id']: s['cycle_id'] for s in repo.snapshots()}
            if graph['snapshot_id'] not in snaps:
                raise MapperError('SNAPSHOT_NOT_FOUND')
            export_snapshot(repo, path, snaps[graph['snapshot_id']], csv_format=kind == 'source-csv')
    else:
        text, _ = export_content(graph, kind)
        safe_json(text, forbidden(config))
        if size + len(text.encode('utf-8')) >= budget:
            raise MapperError('DATA_BUDGET_EXCEEDED')
        with private_file(path) as stream:
            stream.write(text)
    if size + path.stat().st_size >= budget:
        path.unlink()
        raise MapperError('DATA_BUDGET_EXCEEDED')
    return path
