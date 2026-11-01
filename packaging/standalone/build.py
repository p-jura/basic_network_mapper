"""Native standalone builder. Explicit local inputs; never downloads or scans."""
import argparse
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import platform
import shutil
import struct
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
from mapper import __version__
from mapper.standalone_manifest import write, verify, archive, sha256


def target():
    if sys.version_info[:2] != (3,13) or struct.calcsize('P') != 8:
        raise ValueError('BUILD_REQUIRES_PYTHON_3_13')
    machine=platform.machine().lower()
    if sys.platform=='darwin' and machine=='arm64': return 'macos-arm64'
    if sys.platform=='win32' and machine in ('amd64','x86_64'): return 'windows-x64'
    raise ValueError('UNSUPPORTED_NATIVE_BUILD_TARGET')


def build(args):
    platform_id=target()
    output=Path(args.output).absolute();output.mkdir(parents=True,exist_ok=True)
    work=Path(args.work).absolute();work.mkdir(parents=True,exist_ok=True)
    folder=output/f'mapper-sieci-{__version__}-{platform_id}-standalone'
    if folder.exists() or (folder.parent/(folder.name+'.zip')).exists():
        raise ValueError('OUTPUT_ALREADY_EXISTS')
    materials=Path(args.materials).resolve()
    for name in ['licenses','sources','THIRD_PARTY_NOTICES.md','license-review.json']:
        if not (materials/name).exists():raise ValueError('MISSING_COMPONENT_MATERIALS')
    env={**os.environ,'PYINSTALLER_CONFIG_DIR':str(work/'cache')}
    with (work/'pyinstaller.log').open('w',encoding='utf-8') as log:
        subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--distpath',str(work/'dist'),
            '--workpath',str(work/'pyinstaller'),str(ROOT/'packaging/standalone/Mapper.spec')],
            cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    frozen=work/'dist/Mapper'
    exe=frozen/('Mapper.exe' if platform_id=='windows-x64' else 'Mapper')
    result=subprocess.run([str(exe),'doctor'],capture_output=True,text=True,timeout=90,check=True)
    if json.loads(result.stdout)['mapper']!=__version__:raise ValueError('FROZEN_VERSION_MISMATCH')
    shutil.copytree(frozen,folder,symlinks=True)
    for name in ['licenses','sources']:
        shutil.copytree(materials/name,folder/name,symlinks=True)
    # Additional interpreter/loader source material prepared explicitly per build.
    extra=Path(args.runtime_materials).resolve()
    if not (extra/'sources'/f'Python-{platform.python_version()}.tar.xz').is_file():
        raise ValueError('RUNTIME_SOURCE_VERSION_MISMATCH')
    for name in ['licenses','sources']:
        if not (extra/name).is_dir():raise ValueError('MISSING_RUNTIME_MATERIALS')
        shutil.copytree(extra/name,folder/name,dirs_exist_ok=True,symlinks=True)
    shutil.copy2(materials/'THIRD_PARTY_NOTICES.md',folder/'THIRD_PARTY_NOTICES.md')
    review=json.loads((materials/'license-review.json').read_text(encoding='utf-8'))
    review['standalone_note']='New runtime/interpreter/loader inventory added; L01 remains open; not for public release.'
    (folder/'license-review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    shutil.copy2(extra/'provenance.json',folder/'runtime-provenance.json')
    shutil.copy2(ROOT/'LICENSE',folder/'LICENSE')
    shutil.copy2(ROOT/'packaging/standalone/START_TUTAJ.md',folder/'START_TUTAJ.md')
    shutil.copytree(ROOT/'examples/snapshots',folder/'examples/snapshots')
    shutil.copy2(ROOT/'packaging/standalone/START_TUTAJ.md',folder/'README.md')
    if platform_id=='macos-arm64':
        launcher=folder/'Uruchom Mapper.command'
        shutil.copy2(ROOT/'packaging/standalone/start.command',launcher);launcher.chmod(0o755)
    # Ship exactly the project's own sources used to build this candidate.
    with zipfile.ZipFile(folder/'sources'/f'mapper-sieci-{__version__}-source.zip','x',zipfile.ZIP_DEFLATED) as z:
        for name in ['src/mapper','packaging','tests','examples']:
            for p in sorted((ROOT/name).rglob('*')):
                if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc',):
                    z.write(p,p.relative_to(ROOT).as_posix())
        for name in ['LICENSE','pyproject.toml','README.md']:z.write(ROOT/name,name)
    binaries=[]
    for p in (folder/'_internal').rglob('*'):
        if p.is_file() and not p.is_symlink() and (p.suffix in ('.dll','.pyd','.dylib','.so') or p.name=='Python'):
            binaries.append({'path':p.relative_to(folder).as_posix(),'sha256':sha256(p)})
    (folder/'native-components.json').write_text(json.dumps({'python':platform.python_version(),'binaries':binaries,
        'review':'internal_candidate; full component review remains open'},indent=2)+'\n',encoding='utf-8')
    source_hashes={p.relative_to(ROOT).as_posix():sha256(p) for p in (ROOT/'src/mapper').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    provenance={'native_system':platform.platform(),'machine':platform.machine(),'python':platform.python_version(),
        'pyinstaller':metadata.version('pyinstaller'),'hooks':metadata.version('pyinstaller-hooks-contrib'),
        'source_hashes':source_hashes,'build_input':args.source_revision,
        'base_materials':'0.5.0rc1 + explicit interpreter/loader materials; L01 remains open',
        'support_target':['Windows 10 22H2 x64','Windows 11 x64'] if platform_id=='windows-x64' else ['macOS ARM64'],
        'acceptance':'native build is not clean-OS acceptance'}
    write(folder,__version__,platform_id,provenance);verify(folder)
    dest=folder.parent/(folder.name+'.zip');archive(folder,dest)
    return {'archive':str(dest),'sha256':sha256(dest),'version':__version__,'platform':platform_id,'sends_probes':False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['output','work','materials','runtime-materials','source-revision']:p.add_argument('--'+name,required=True)
    print(json.dumps(build(p.parse_args()),ensure_ascii=False))

if __name__=='__main__':main()
