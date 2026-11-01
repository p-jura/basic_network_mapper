"""Assemble an internal candidate from explicit wheels/materials; never downloads."""
import argparse
from email.parser import BytesParser
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

from bundle import sha256, verify


def wheel_info(path):
    with zipfile.ZipFile(path) as wheel:
        names = [n for n in wheel.namelist() if n.endswith('.dist-info/METADATA') and n.count('/') == 1]
        if len(names) != 1:
            raise ValueError('INVALID_WHEEL_METADATA')
        meta = BytesParser().parsebytes(wheel.read(names[0]))
        name = re.sub(r'[-_.]+', '-', meta['Name']).lower()
        version = meta['Version']
        if not re.fullmatch(r'[a-z0-9-]+', name) or not re.fullmatch(r'[a-zA-Z0-9.+!_-]+', version):
            raise ValueError('INVALID_WHEEL_IDENTITY')
        return {'name': name, 'version': version, 'filename': path.name, 'sha256': sha256(path), 'requires_dist': meta.get_all('Requires-Dist', [])}


def check_closure(records, target):
    from packaging.markers import default_environment
    from packaging.requirements import Requirement
    env = default_environment()
    env.update(python_version='3.13', python_full_version='3.13.0', extra='',
               platform_system='Windows' if target == 'windows-x64' else 'Darwin',
               sys_platform='win32' if target == 'windows-x64' else 'darwin',
               os_name='nt' if target == 'windows-x64' else 'posix',
               platform_machine='AMD64' if target == 'windows-x64' else 'arm64')
    pins = {r['name']: r['version'] for r in records}
    missing = []
    for record in records:
        for text in record['requires_dist']:
            req = Requirement(text)
            if req.marker and not req.marker.evaluate(env):
                continue
            name = re.sub(r'[-_.]+', '-', req.name).lower()
            if name not in pins or not req.specifier.contains(pins[name], prereleases=True):
                missing.append(record['name'] + ' requires ' + str(req))
    if missing:
        raise ValueError('INCOMPLETE_TARGET_DEPENDENCIES: ' + '; '.join(missing))


def copy_tree(source, dest):
    source = Path(source)
    if source.is_symlink() or not source.is_dir():
        raise ValueError('INVALID_MATERIALS_DIRECTORY')
    dest.mkdir()
    for path in sorted(source.rglob('*')):
        if path.is_symlink():
            raise ValueError('LINK_IN_MATERIALS')
        target = dest / path.relative_to(source)
        if path.is_dir(): target.mkdir(exist_ok=True)
        elif path.is_file(): shutil.copy2(path, target)
        else: raise ValueError('INVALID_MATERIALS_FILE')


def build(args):
    wheelhouse, output = Path(args.wheelhouse), Path(args.output)
    records = [wheel_info(p) for p in sorted(wheelhouse.glob('*.whl'))]
    by_name = {r['name']: r for r in records}
    if len(by_name) != len(records) or 'mapper-sieci' not in by_name:
        raise ValueError('DUPLICATE_OR_MISSING_OWN_WHEEL')
    with zipfile.ZipFile(wheelhouse / by_name['mapper-sieci']['filename']) as own:
        required = {'mapper/storage/migrations/001_initial.sql', 'mapper/storage/migrations/002_topology.sql',
                    'mapper/ui/assets/panel.css', 'mapper/app.py', 'mapper/ui/panel.py'}
        if not required <= set(own.namelist()):
            raise ValueError('OWN_WHEEL_RESOURCES_MISSING')
    check_closure(records, args.platform)
    version = by_name['mapper-sieci']['version']
    # Candidate is deliberately never advertised as a completed release.
    folder = output / ('mapper-sieci-' + version + '-' + args.platform)
    output.mkdir(parents=True, exist_ok=True)
    folder.mkdir()
    (folder / 'wheelhouse').mkdir()
    for r in records:
        if not r['filename'].endswith('-any.whl'):
            if args.platform == 'macos-arm64' and not any(x in r['filename'] for x in ['arm64.whl', 'universal2.whl']):
                raise ValueError('WRONG_PLATFORM_WHEEL')
            if args.platform == 'windows-x64' and not r['filename'].endswith('-win_amd64.whl'):
                raise ValueError('WRONG_PLATFORM_WHEEL')
        shutil.copy2(wheelhouse / r['filename'], folder / 'wheelhouse' / r['filename'])
    lock = '\n'.join(r['name'] + '==' + r['version'] + ' --hash=sha256:' + r['sha256'] for r in sorted(records, key=lambda r: r['name'])) + '\n'
    (folder / 'requirements.lock').write_text(lock, encoding='utf-8')
    templates = Path(__file__).parent
    for name in ['bundle.py', 'maintenance.py', 'START_TUTAJ.md']:
        shutil.copy2(templates / name, folder / name)
    launchers = ['install.sh', 'start.command'] if args.platform == 'macos-arm64' else ['install.cmd', 'start.cmd']
    for name in launchers:
        shutil.copy2(templates / name, folder / name)
        if args.platform == 'macos-arm64': (folder / name).chmod(0o755)
    repo = Path(args.repo)
    shutil.copy2(repo / 'LICENSE', folder / 'LICENSE')
    shutil.copy2(templates / 'THIRD_PARTY_NOTICES.md', folder / 'THIRD_PARTY_NOTICES.md')
    copy_tree(args.licenses, folder / 'licenses')
    copy_tree(args.sources, folder / 'sources')
    copy_tree(args.examples, folder / 'examples')
    if args.provenance: shutil.copy2(args.provenance, folder / 'provenance.json')
    # Resolves the full set, including platform markers, without installed packages.
    command = [sys.executable, '-I', '-m', 'pip', '--isolated', 'install', '--dry-run', '--ignore-installed',
               '--disable-pip-version-check', '--no-cache-dir', '--no-index', '--only-binary=:all:', '--require-hashes',
               '--find-links', str(folder / 'wheelhouse'), '-r', str(folder / 'requirements.lock')]
    if args.platform == 'windows-x64':
        command += ['--platform', 'win_amd64', '--python-version', '3.13', '--implementation', 'cp', '--abi', 'cp313', '--abi', 'abi3', '--abi', 'none']
    subprocess.run(command, check=True, timeout=180)
    review = json.loads(Path(args.review).read_text(encoding='utf-8'))
    with (folder / 'license-review.json').open('x', encoding='utf-8') as stream:
        json.dump(review, stream, ensure_ascii=False, indent=2)
    manifest = {'schema_version': 1, 'version': version, 'platform': args.platform, 'python': '3.13',
                'release_status': 'internal_candidate_not_for_distribution',
                'commit': args.commit, 'working_tree': args.tree_state,
                'wheels': records, 'open_acceptance': review.get('open_items', []), 'files': []}
    for p in sorted(folder.rglob('*')):
        if p.is_file():
            manifest['files'].append({'path': p.relative_to(folder).as_posix(), 'size': p.stat().st_size, 'sha256': sha256(p)})
    (folder / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    sums = [sha256(p) + '  ' + p.relative_to(folder).as_posix() for p in sorted(folder.rglob('*'), key=lambda p: p.relative_to(folder).as_posix()) if p.is_file()]
    (folder / 'SHA256SUMS').write_text('\n'.join(sums) + '\n', encoding='utf-8')
    verify(folder)
    archive = output / (folder.name + '.zip')
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in sorted(folder.rglob('*')):
            if p.is_file(): z.write(p, p.relative_to(output))
    with (output / (archive.name + '.sha256')).open('x', encoding='utf-8') as stream:
        stream.write(sha256(archive) + '  ' + archive.name + '\n')
    return {'archive': str(archive), 'sha256': sha256(archive), 'wheels': len(records), 'version': version, 'platform': args.platform, 'release_status': manifest['release_status']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['wheelhouse', 'output', 'repo', 'licenses', 'sources', 'examples', 'review', 'commit', 'tree-state']:
        p.add_argument('--' + name, required=True)
    p.add_argument('--provenance')
    p.add_argument('--platform', choices=['macos-arm64', 'windows-x64'], required=True)
    print(json.dumps(build(p.parse_args()), ensure_ascii=False))


if __name__ == '__main__':
    main()
