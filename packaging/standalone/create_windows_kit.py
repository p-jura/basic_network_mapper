from pathlib import Path
import shutil,zipfile,hashlib,json
import argparse,tomllib
p=argparse.ArgumentParser(description='Create local Windows build kit; not a Windows executable.')
for name in ['previous-zip','build-wheels','runtime-materials','output']:p.add_argument('--'+name,required=True)
args=p.parse_args()
root=Path(__file__).resolve().parents[2]
version=tomllib.loads((root/'pyproject.toml').read_text(encoding='utf-8'))['project']['version']
output=Path(args.output).absolute();output.mkdir(parents=True,exist_ok=True)
kit=output/f'mapper-sieci-{version}-windows-x64-build-kit';kit.mkdir()
repo=kit/'repo'
for name in ['src/mapper','packaging','tests','examples']:
 shutil.copytree(root/name,repo/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
for name in ['README.md','LICENSE','pyproject.toml']:shutil.copy2(root/name,repo/name)
shutil.copytree(Path(args.build_wheels),kit/'build-wheels')
shutil.copytree(Path(args.runtime_materials),kit/'runtime-materials')
archive=Path(args.previous_zip)
with zipfile.ZipFile(archive) as z:
 prefix=z.namelist()[0].split('/')[0]+'/'
 for name in z.namelist():
  rel=name.removeprefix(prefix)
  if not name.startswith(prefix) or name.endswith('/'):continue
  if any(part in ('','..','.') for part in rel.split('/')) or '\\' in rel or ':' in rel:raise ValueError('INVALID_INPUT_ARCHIVE_PATH')
  if rel.startswith('wheelhouse/'):
   dest=kit/'runtime-wheels'/Path(rel).name
  elif rel.startswith(('licenses/','sources/')) or rel in ['THIRD_PARTY_NOTICES.md','license-review.json']:
   dest=kit/'materials'/rel
  else:continue
  dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(name))
shutil.copy2(root/'packaging/standalone/BUDUJ_WINDOWS.cmd',kit/'BUDUJ_WINDOWS.cmd')
(kit/'README.md').write_text('''# Zestaw budowania Windows x64 — 0.5.0rc2

To **zestaw dla stanowiska budowania**, nie gotowa aplikacja Windows. Brak jeszcze Mapper.exe. Ten sam wynikowy ZIP ma być odebrany osobno na Windows 10 22H2 x64 i Windows 11 x64. Budowanie z macOS nie zastępuje natywnego Windows.

1. Na stanowisku budowania przygotuj Python 3.13 x64 z launcherem `py`. Nie jest on potrzebny przyszłemu odbiorcy Mapper.exe.
2. Rozpakuj cały zestaw w nowym lokalnym katalogu NTFS użytkownika, bez uprawnień administratora. Nie nadpisuj katalogu wcześniejszej próby.
3. W cmd uruchom `BUDUJ_WINDOWS.cmd`. Przygotowanie materiałów może pobrać z oficjalnego python.org źródło dokładnej używanej wersji interpretera i notę OpenSSL. Instalacja bibliotek i PyInstaller używa wyłącznie lokalnych kół z wymaganymi hashami; nie pobiera pakietów z PyPI.
4. Skrypt tworzy własny `work/build-env`, sprawdza zależności i testy, buduje onedir, materiały i ZIP w `dist/`. Log PyInstaller: `work/native/pyinstaller.log`. Cały katalog work zachowaj w razie błędu; ponowną próbę wykonaj w świeżo rozpakowanej kopii.
5. Po sukcesie sprawdź instrukcję README/START_TUTAJ w wynikowej paczce. Na **innym czystym komputerze bez Pythona** rozpakuj ZIP i uruchom Mapper.exe. Sprawdź doctor, runtime-check, receipt, panel offline i obrazy. Powtórz osobno na Windows 10 i 11.

To kandydat wewnętrzny bez publicznego podpisu/odbioru. Nie wyłączaj ochrony systemu. NTFS z drugiego konta, źródło IPv4 i sprzęt nadal wymagają dowodów; bez aktywnych sond w tym procesie budowania. Nie przekazuj sekretów lub danych rzeczywistej sieci z logami. Materiały pełnego przeglądu licencyjnego L01 pozostają otwarte.
''',encoding='utf-8')
# Exact input checksums; no own source/interpreter hash implied to be an author signature.
files={p.relative_to(kit).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in kit.rglob('*') if p.is_file()}
(kit/'SHA256SUMS').write_text(''.join(f'{files[n]}  {n}\n' for n in sorted(files)),encoding='utf-8')
dest=output/(kit.name+'.zip')
with zipfile.ZipFile(dest,'x',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(kit.rglob('*')):
  if p.is_file():z.write(p,kit.name+'/'+p.relative_to(kit).as_posix())
(dest.with_suffix('.zip.sha256')).write_text(hashlib.sha256(dest.read_bytes()).hexdigest()+'  '+dest.name+'\n')
print(dest.name, dest.stat().st_size)
