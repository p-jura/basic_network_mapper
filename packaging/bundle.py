"""Standalone offline installer/launcher. Standard library only, no discovery."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import stat
import subprocess
import sys
import venv


class BundleError(Exception):
    pass


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def regular(root, relative):
    name = PurePosixPath(relative)
    if not relative or '\\' in relative or ':' in relative or name.is_absolute() or any(p in {'', '.', '..'} for p in relative.split('/')):
        raise BundleError('UNSAFE_MANIFEST_PATH')
    path = root
    for part in name.parts:
        path /= part
        try:
            info = path.lstat()
        except FileNotFoundError:
            raise BundleError('BUNDLE_FILE_MISSING: ' + relative) from None
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise BundleError('LINK_IN_BUNDLE')
    if not path.is_file():
        raise BundleError('BUNDLE_FILE_MISSING')
    return path


def verify(root):
    if root.is_symlink():
        raise BundleError('LINK_IN_BUNDLE')
    manifest = json.loads(regular(root, 'manifest.json').read_text(encoding='utf-8'))
    if manifest['schema_version'] != 1 or manifest['platform'] not in {'macos-arm64', 'windows-x64'}:
        raise BundleError('UNSUPPORTED_BUNDLE')
    seen = set()
    for item in manifest['files']:
        name = item['path']
        if name in seen:
            raise BundleError('DUPLICATE_MANIFEST_PATH')
        seen.add(name)
        path = regular(root, name)
        if path.stat().st_size != item['size'] or sha256(path) != item['sha256']:
            raise BundleError('BUNDLE_HASH_MISMATCH: ' + name)
    required = {'bundle.py', 'maintenance.py', 'requirements.lock', 'START_TUTAJ.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md'}
    if not required <= seen:
        raise BundleError('INCOMPLETE_BUNDLE')
    wheel_names = {'wheelhouse/' + p.name for p in (root / 'wheelhouse').iterdir()}
    if wheel_names != {name for name in seen if name.startswith('wheelhouse/')}:
        raise BundleError('UNEXPECTED_WHEELHOUSE_CONTENT')
    expected_sums = {item['path']: item['sha256'] for item in manifest['files']}
    expected_sums['manifest.json'] = sha256(root / 'manifest.json')
    actual_sums = regular(root, 'SHA256SUMS').read_text(encoding='utf-8').splitlines()
    expected = [expected_sums[name] + '  ' + name for name in sorted(expected_sums)]
    if actual_sums != expected:
        raise BundleError('CHECKSUM_LIST_MISMATCH')
    return manifest


def check_platform(manifest):
    expected = ('Darwin', 'arm64') if manifest['platform'] == 'macos-arm64' else ('Windows', 'amd64')
    if sys.version_info[:2] != (3, 13):
        raise BundleError('PYTHON_3_13_REQUIRED')
    if (platform.system(), platform.machine().lower()) != expected or sys.maxsize <= 2**32:
        raise BundleError('WRONG_PLATFORM')


def interpreter(root):
    return root / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def install(root):
    manifest = verify(root)
    check_platform(manifest)
    target = root / '.venv'
    if target.exists() or target.is_symlink():
        raise BundleError('VENV_ALREADY_EXISTS: use a new unpacked folder')
    print('Weryfikacja plików OK. Instalacja lokalna, bez indeksu i aktualizacji.', flush=True)
    target.mkdir(mode=0o700)  # Atomic reservation: concurrent install cannot overwrite.
    venv.EnvBuilder(with_pip=True).create(target)
    py = str(interpreter(root))
    args = [py, '-I', '-m', 'pip', '--isolated', 'install', '--disable-pip-version-check', '--no-cache-dir',
            '--no-index', '--only-binary=:all:', '--require-hashes', '--find-links', str(root / 'wheelhouse'),
            '-r', str(root / 'requirements.lock')]
    subprocess.run(args, check=True, timeout=600, cwd=root)
    subprocess.run([py, '-I', '-m', 'pip', '--isolated', 'check'], check=True, timeout=60, cwd=root)
    code = 'import mapper,importlib.metadata as m; print(mapper.__file__); assert mapper.__version__ == m.version("mapper-sieci") == ' + repr(manifest['version'])
    subprocess.run([py, '-I', '-c', code], check=True, timeout=60, cwd=root)
    with (target / '.mapper-installed.json').open('x', encoding='utf-8') as stream:
        json.dump({'version': manifest['version'], 'manifest_sha256': sha256(root / 'manifest.json')}, stream)
    print('Instalacja OK. Uruchom start.command / start.cmd. Status wydania: ' + manifest['release_status'], flush=True)


def installed(root):
    marker = regular(root, '.venv/.mapper-installed.json')
    manifest = json.loads(regular(root, 'manifest.json').read_text(encoding='utf-8'))
    check_platform(manifest)
    receipt = json.loads(marker.read_text(encoding='utf-8'))
    if receipt['version'] != manifest['version'] or receipt['manifest_sha256'] != sha256(root / 'manifest.json'):
        raise BundleError('INSTALLATION_RECEIPT_MISMATCH')
    return str(interpreter(root))


def start(root, args):
    # Installed libraries remain replaceable. Wheelhouse hashes are checked at
    # installation, not used to forbid compatible LGPL library replacement.
    command = [installed(root), '-I', '-m', 'mapper', 'panel', *args]
    if os.name != 'nt':
        os.execv(command[0], command)
    return subprocess.call(command, cwd=root)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Mapper — lokalna instalacja i start')
    parser.add_argument('action', choices=['verify', 'install', 'start', 'maintenance'])
    args, rest = parser.parse_known_args(argv)
    root = Path(__file__).absolute().parent
    try:
        if args.action in {'verify', 'install'} and rest:
            raise BundleError('UNEXPECTED_ARGUMENTS')
        if args.action == 'verify':
            m = verify(root)
            print(json.dumps({'status': 'verified', 'version': m['version'], 'platform': m['platform'], 'release_status': m['release_status']}, ensure_ascii=False))
        elif args.action == 'install':
            install(root)
        elif args.action == 'start':
            return start(root, rest)
        else:
            return subprocess.call([installed(root), '-I', str(root / 'maintenance.py'), *rest], cwd=root)
    except (BundleError, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        print('Instalacja/start przerwany: ' + (str(exc) if isinstance(exc, BundleError) else type(exc).__name__) + '. Istniejących danych nie zmieniono.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
