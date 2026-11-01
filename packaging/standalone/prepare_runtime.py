"""Build-host preparation only: exact interpreter sources/notices from official HTTPS.

End-user standalone startup never imports or invokes this script.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import re
import ssl
import tarfile
from urllib.request import urlopen


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dest',required=True);args=p.parse_args()
    root=Path(args.dest).absolute();(root/'sources').mkdir(parents=True,exist_ok=True);(root/'licenses').mkdir(exist_ok=True)
    version=platform.python_version()
    if not re.fullmatch(r'3\.13\.\d+',version):raise ValueError('BUILD_REQUIRES_RELEASE_PYTHON_3_13')
    provenance=root/'provenance.json'
    records=json.loads(provenance.read_text(encoding='utf-8')) if provenance.exists() else []
    def fetch(url,path):
        if path.exists():return
        with urlopen(url,timeout=60) as response:body=response.read()
        with path.open('xb') as stream:stream.write(body)
        records.append({'url':url,'file':path.relative_to(root).as_posix(),'sha256':hashlib.sha256(body).hexdigest()})
    archive=root/'sources'/f'Python-{version}.tar.xz'
    fetch(f'https://www.python.org/ftp/python/{version}/Python-{version}.tar.xz',archive)
    with tarfile.open(archive) as tar:
        for name in ['LICENSE','README.rst']:
            dest=root/'licenses'/f'python-{version}';dest.mkdir(exist_ok=True)
            (dest/name).write_bytes(tar.extractfile(f'Python-{version}/{name}').read())
    openssl=ssl.OPENSSL_VERSION.split()[1]
    if not re.fullmatch(r'\d+\.\d+\.\d+[a-z]?',openssl):raise ValueError('UNRECOGNIZED_OPENSSL_VERSION')
    fetch(f'https://raw.githubusercontent.com/openssl/openssl/openssl-{openssl}/LICENSE.txt',root/'licenses'/f'OpenSSL-{openssl}-LICENSE.txt')
    provenance.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Materiały interpretera przygotowane; końcowy inwentarz natywnych DLL nadal wymaga przeglądu.')

if __name__=='__main__':main()
