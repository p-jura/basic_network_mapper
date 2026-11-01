"""Prepare an isolated native build from local, hash-locked wheels only."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import venv
from build import ROOT, target


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['wheelhouse','build-wheels','materials','runtime-materials','work','output','source-revision']:
        p.add_argument('--'+name,required=True)
    args=p.parse_args();platform_id=target()
    work=Path(args.work).absolute()
    # Never overwrite somebody's venv, install or previous build attempt.
    work.mkdir(parents=True,exist_ok=False)
    envdir=work/'build-env';venv.EnvBuilder(with_pip=True).create(envdir)
    python=envdir/('Scripts/python.exe' if sys.platform=='win32' else 'bin/python')
    env={**os.environ,'PIP_NO_INDEX':'1','PIP_DISABLE_PIP_VERSION_CHECK':'1','PYTHONNOUSERSITE':'1'}
    def run(argv):subprocess.run([str(python),*map(str,argv)],cwd=ROOT,env=env,check=True)
    run(['-m','pip','install','--no-index','--only-binary=:all:','--require-hashes',
        '--find-links',Path(args.wheelhouse).absolute(),'-r',ROOT/f'packaging/standalone/runtime-{platform_id}.lock'])
    run(['-m','pip','install','--no-index','--only-binary=:all:','--require-hashes',
        '--find-links',Path(args.build_wheels).absolute(),'-r',ROOT/f'packaging/standalone/build-{platform_id}.lock'])
    run(['-m','pip','install','--no-index','--no-build-isolation','--no-deps',ROOT])
    run(['-m','pip','check'])
    run(['-m','unittest','discover','-s',ROOT/'tests/critical'])
    run([ROOT/'packaging/standalone/build.py','--work',work/'native','--output',Path(args.output).absolute(),
        '--materials',Path(args.materials).absolute(),'--runtime-materials',Path(args.runtime_materials).absolute(),
        '--source-revision',args.source_revision])

if __name__=='__main__':main()
