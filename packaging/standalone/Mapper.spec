# Native onedir build. No onefile extraction, no GUI/tray or network setup.
from pathlib import Path
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

root = Path(SPECPATH).parents[1]
datas = []
hidden = []
for package in ['dash', 'dash_cytoscape', 'plotly', 'ntc_templates', 'pysnmp']:
    datas += collect_data_files(package)
for package in ['netmiko', 'pysnmp', 'pyasn1', 'cryptography', 'paramiko', 'ntc_templates']:
    hidden += collect_submodules(package, filter=lambda n: '.tests' not in n)
for dist in ['mapper-sieci', 'dash', 'dash-cytoscape', 'netmiko', 'pysnmp', 'networkx', 'psutil', 'ntc-templates', 'cryptography', 'setuptools']:
    datas += copy_metadata(dist, recursive=True)
datas += [(str(root/'src/mapper/storage/migrations'), 'mapper/storage/migrations'),
          (str(root/'src/mapper/ui/assets'), 'mapper/ui/assets')]
a = Analysis([str(root/'packaging/standalone/entry.py')], pathex=[str(root/'src')],
    binaries=[], datas=datas, hiddenimports=hidden,
    hookspath=[str(root/'packaging/standalone/hooks')],
    excludes=['tkinter', 'IPython', 'jupyter_client', 'jupyter_core', 'pytest'],
    module_collection_mode={'paramiko':'py', 'scp':'py', 'setuptools':'py'},
    noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='Mapper',
    debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
    console=True, argv_emulation=False, target_arch='arm64' if sys.platform=='darwin' else None)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='Mapper')
