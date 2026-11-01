"""Manifest v2 for standalone artifacts. Verification is explicit, never a start gate.

A modified compatible LGPL library may run; `verify` reports its changed hash.
"""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import zipfile


class ManifestError(ValueError):
    pass


def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def safe_name(name):
    if (not isinstance(name, str) or not name or '\\' in name or ':' in name or '\x00' in name
            or name.startswith('/') or any(p in ('', '.', '..') for p in name.split('/'))):
        raise ManifestError('INVALID_MANIFEST_PATH')
    return PurePosixPath(name)


def paths(root):
    # Directory links are entries, never traversal roots.
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in sorted(dirs + files):
            yield Path(directory) / name


def record(root, path):
    info = path.lstat()
    name = path.relative_to(root).as_posix()
    safe_name(name)
    if getattr(info, 'st_file_attributes', 0) & 0x400:  # Windows reparse point
        raise ManifestError('REPARSE_POINT_IN_BUNDLE')
    if stat.S_ISLNK(info.st_mode):
        target = os.readlink(path)
        if Path(target).is_absolute() or '\\' in target or ':' in target:
            raise ManifestError('INVALID_LINK_TARGET')
        try:
            resolved = path.resolve(strict=True)
        except (OSError, RuntimeError):
            raise ManifestError('BROKEN_OR_CYCLIC_LINK') from None
        if not resolved.is_relative_to(root.resolve()) or resolved == root.resolve():
            raise ManifestError('LINK_OUTSIDE_BUNDLE')
        return {'path': name, 'type': 'symlink', 'target': target}
    if stat.S_ISDIR(info.st_mode):
        return None
    if not stat.S_ISREG(info.st_mode):
        raise ManifestError('NON_REGULAR_BUNDLE_ENTRY')
    return {'path': name, 'type': 'file', 'size': info.st_size,
            'sha256': sha256(path), 'executable': bool(info.st_mode & stat.S_IXUSR)}


def inventory(root):
    root = Path(root).absolute()
    if root.is_symlink():
        raise ManifestError('LINKED_BUNDLE_ROOT')
    rows = []
    for path in paths(root):
        if path.relative_to(root).as_posix() in {'manifest.json', 'SHA256SUMS'}:
            if path.is_symlink() or not path.is_file():
                raise ManifestError('INVALID_MANIFEST_FILE')
            continue
        item = record(root, path)
        if item:
            rows.append(item)
    return sorted(rows, key=lambda x: x['path'])


def write(root, version, platform, provenance):
    root = Path(root)
    manifest = {'schema_version': 2, 'format': 'standalone-onedir', 'version': version,
                'platform': platform, 'release_status': 'internal_candidate_not_for_distribution',
                'provenance': provenance, 'files': inventory(root)}
    (root/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    # SHA256SUMS covers regular files and manifest; links are covered by manifest.
    sums = {x['path']: x['sha256'] for x in manifest['files'] if x['type']=='file'}
    sums['manifest.json'] = sha256(root/'manifest.json')
    (root/'SHA256SUMS').write_text(''.join(f'{sums[n]}  {n}\n' for n in sorted(sums)), encoding='utf-8')
    return manifest


def verify(root):
    root = Path(root)
    for name in ('manifest.json', 'SHA256SUMS'):
        p = root/name
        if p.is_symlink() or not p.is_file():
            raise ManifestError('MANIFEST_MISSING_OR_LINKED')
    try:
        manifest = json.loads((root/'manifest.json').read_text(encoding='utf-8'))
        if manifest['schema_version'] != 2 or manifest['format'] != 'standalone-onedir':
            raise ManifestError('UNSUPPORTED_MANIFEST')
        expected = manifest['files']
        for row in expected:
            safe_name(row['path'])
        if expected != inventory(root):
            raise ManifestError('BUNDLE_CONTENT_CHANGED')
        sums = {x['path']: x['sha256'] for x in expected if x['type']=='file'}
        sums['manifest.json'] = sha256(root/'manifest.json')
        want = ''.join(f'{sums[n]}  {n}\n' for n in sorted(sums))
        if (root/'SHA256SUMS').read_text(encoding='utf-8') != want:
            raise ManifestError('CHECKSUM_LIST_MISMATCH')
        return manifest
    except (KeyError, TypeError, json.JSONDecodeError):
        raise ManifestError('INVALID_MANIFEST') from None


def archive(root, destination):
    root, destination = Path(root), Path(destination)
    verify(root)
    # Exclusive creation: never replace an already delivered artifact.
    with zipfile.ZipFile(destination, 'x', compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(paths(root)):
            mode = p.lstat().st_mode
            name = root.name+'/'+p.relative_to(root).as_posix()
            if stat.S_ISLNK(mode):
                info = zipfile.ZipInfo(name)
                info.create_system = 3
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
                z.writestr(info, os.readlink(p).encode('utf-8'))
            elif p.is_file():
                z.write(p, name)
    sidecar = destination.with_suffix(destination.suffix+'.sha256')
    sidecar.write_text(sha256(destination)+'  '+destination.name+'\n', encoding='utf-8')
