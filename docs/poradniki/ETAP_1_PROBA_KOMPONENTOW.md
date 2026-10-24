# Poradnik: Etap 1 — przygotowanie środowiska i próba komponentów

Projekt: **Maper sieci — własna aplikacja z darmowych komponentów**. Data opracowania: 11 października 2026 r.

Podstawa: zatwierdzona [karta Etapu 0](KARTA_ETAP_0.md). Gdy wcześniejszy [plan startowy](../PLAN_STARTOWY.md) opisuje inne założenia, obowiązują decyzje z karty, w tym Windows/macOS ARM i automatyczne otwieranie przeglądarki.

**Cel:** sprawdzić lokalny panel/graf i PNG/SVG, podstawowe odkrywanie LAN bez seedów/poświadczeń oraz osobno rozszerzone SNMPv2c/v3 i SSH z parserem. Wynikiem jest mała próba techniczna, zestaw wersji i raport. Model produkcyjny, pełne kolektory, wnioskowanie topologii i historia powstają w kolejnych etapach.

Ten plik jest instrukcją. Samo jego utworzenie nie instaluje pakietów, nie tworzy opisanych niżej skryptów i nie wykonuje odczytów. Fragmenty kodu należy zapisać w podanych plikach dopiero podczas realizowania etapu. Weryfikacja składni przykładów nie zastępuje ich uruchomienia z bibliotekami i urządzeniami.

## Doprecyzowanie zakresu: brak SNMP nie blokuje mappera

Po przygotowaniu poradnika użytkownik doprecyzował wymaganie odkrywania również w sieciach domowych/operatorów bez SNMP/SSH. Obowiązuje dopisek w [karcie Etapu 0](KARTA_ETAP_0.md#10-doprecyzowanie-po-zatwierdzeniu-odkrywanie-bez-snmpssh) i [wymaganiach projektu](../WYMAGANIA_PROJEKTU.md).

Poniższe `run_probe.py`, `probe_snmp.py` i `probe_ssh.py` sprawdzają opcjonalną ścieżkę zarządzającą. Nie są uniwersalnym skanerem lokalnej sieci. Jeśli router nie obsługuje SNMP, nie trzeba wymyślać community ani wymuszać dostępu SSH. Próba tych protokołów może korzystać z oddzielnego laboratorium, a podstawowe wykrywanie ma działać bez nich.

Podstawowy przekrój wykonaj według [osobnego poradnika odkrywania](ETAP_1_ODKRYWANIE_PODSTAWOWE.md): proponowany `psutil`, adapter istniejących narzędzi OS, ograniczony ping i sąsiedzi/ARP. Poradnik podaje kroki implementacji i odbioru; gotowego `probe_discovery.py` jeszcze nie dostarczono. Graf offline nie potwierdza skanowania. Podstawowy i rozszerzony wynik zapisuj oddzielnie, bez wymuszania community w domowym LAN.

## 1. Zaplanuj krótki przebieg

| Kolejność | Praca | Oczekiwany wynik |
|---|---|---|
| 1 | Python 3.13 i venv na macOS ARM | Właściwy interpreter, izolowane zależności |
| 2 | Instalacja bibliotek i kontrola importów | Spójny zestaw pakietów, brak błędów zależności |
| 3 | Mały snapshot, graf, SQLite/NetworkX | Lokalny przekrój bez dostępu do urządzeń |
| 4 | Start przeglądarki i PNG/SVG | D02 działa na właściwym porcie |
| 5 | Podstawowy LAN według osobnego poradnika, bez seedów i profili | Zakres/interfejs, wykryte hosty, logiczna mapa, nieustalone porty/VLAN-y |
| 6 | Osobne laboratorium SNMPv2c/v3 i Cisco SSH | Dowód ścieżki rozszerzonej albo jawny brak laboratorium |
| 7 | Powtórzenie panelu i odkrywania podstawowego na Windows | Potwierdzenie przenośności wybranego zestawu |
| 8 | Przypięcie wersji, licencje i raport | Wynik do zatwierdzenia przed Etapem 2 |

Cel czasowy po rozszerzeniu: 2–4 dni pracy przy przygotowanym stanowisku; korekta po próbie adapterów obu OS. Brak laboratorium oznaczamy w raporcie; nie zastępujemy wyniku online fikcyjnym sukcesem. Nie budujemy w tym etapie CI/CD ani rozbudowanej warstwy testowej.

## 2. Przygotuj stanowisko

1. Sprawdź system/architekturę, RAM i wolny dysk. Punkt odniesienia: 6 GB RAM i 5 GB wolnego miejsca. Pierwszy przekrój wykonujemy na macOS ARM; potem sprawdzamy Windows x64.
2. Pobierz interpreter **Python 3.13** z oficjalnego źródła, wybierając dostępne wydanie poprawkowe tej linii. Na macOS użyj instalacji obsługującej Apple Silicon; sprawdź wynik `platform.machine()`, żeby wykryć uruchomienie przez Rosettę. Na Windows wybierz x64.
3. Otwórz terminal w katalogu projektu `Maper sieci`. Na macOS jest to `/Users/paweljuroszek/all_projects/other/Maper sieci`; na Windows użyj rzeczywistego położenia swojej kopii projektu.
4. Zapisz wersje systemu i Pythona w raporcie, nie zakładaj ich na podstawie samej nazwy komputera.

Źródła instalacji i obsługi: [Python — pobieranie](https://www.python.org/downloads/), [macOS](https://docs.python.org/3.13/using/mac.html), [Windows](https://docs.python.org/3.13/using/windows.html).

macOS, w katalogu projektu:

```sh
python3.13 --version
python3.13 -c 'import platform; print(platform.platform()); print(platform.machine())'
python3.13 -m venv .venv
```

Windows, PowerShell, w katalogu projektu:

```powershell
py -3.13 --version
py -3.13 -c 'import platform; print(platform.platform()); print(platform.machine())'
py -3.13 -m venv .venv
```

Jeżeli instalacja nie udostępnia launchera `py` lub nazwy `python3.13`, użyj pełnej ścieżki do zainstalowanego Pythona 3.13. Nie uruchamiaj przypadkowego interpretera systemowego. Dalej wywołujemy Python z venv bez aktywacji, więc nie trzeba zmieniać polityki uruchamiania skryptów PowerShell. [Dokumentacja venv](https://docs.python.org/3.13/library/venv.html)

## 3. Utwórz niewielki obszar próby

Utwórz w projekcie następujące katalogi i pliki w czasie wykonywania instrukcji. Nie nadpisuj istniejących danych ani `.gitignore`; brakujące reguły dopisz.

```text
Maper sieci/
  .venv/                         # lokalne środowisko, poza repozytorium
  requirements-stage1.in
  requirements-stage1-macos.txt  # dopiero po udanej próbie
  requirements-stage1-windows.txt
  tools/
    probe_discovery.py           # do napisania według osobnego poradnika
    probe_panel.py
    probe_storage.py
    probe_snmp.py
    probe_ssh.py
    run_probe.py
  examples/snapshots/lab-001.json
  docs/network/                  # opisy i oczekiwane połączenia bez sekretów
  docs/seeds/                    # przykłady bez rzeczywistych poświadczeń
  docs/etap-1/RAPORT_ETAP_1.md
  docs/THIRD_PARTY_NOTICES.md    # po kontroli dołączanych komponentów
```

W obecnej kopii projektu część skryptów użytkownik umieścił w `prototypes/tools/`, a plik zależności w `poza repozytorium/`. Instrukcja poniżej używa układu `tools/` w katalogu głównym. Przed uruchomieniem sprawdź rzeczywiste ścieżki i kompletność plików; nie nadpisuj własnych skryptów. Samo utworzenie pustego `probe_snmp.py`/`probe_ssh.py` nie realizuje próby. Jeśli pozostawiasz układ roboczy, konsekwentnie dostosuj ścieżki do skryptów i snapshotu.

Do `.gitignore` dodaj `.venv/`, `__pycache__/`, `*.pyc` oraz prywatny katalog danych, jeśli znajduje się pod projektem. Nie dodawaj rzeczywistych sekretów do żadnego pliku projektu. Zanonimizowane snapshoty i szablony dokumentacji mogą trafić do repozytorium; rzeczywiste dane klienta przechowuj poza nim.

## 4. Zainstaluj wybrany zestaw i sprawdź importy

Zapisz jako `requirements-stage1.in`:

```text
psutil
pysnmp>=7.1,<7.2
cryptography>=50
netmiko
ntc-templates
textfsm
networkx
dash
dash-cytoscape
```

To zakres do pierwszej próby, jeszcze nie zamrożony zestaw wersji. `psutil` jest nowym proponowanym komponentem podstawowego odkrywania; interfejsy i maski sprawdź na obu OS i zapisz wersję/licencję. [API](https://psutil.io/), [licencja BSD-3-Clause](https://github.com/giampaolo/psutil/blob/master/LICENSE). `cryptography` jest wymaganą częścią naszej próby AES dla SNMPv3; sam udany import PySNMP nie potwierdza szyfrowania. Warunek wersji wynika z aktualnego opisu pakietu — w razie konfliktu sprawdź wymagania konkretnej wersji, bez cichego wyłączania v3. Instalujemy pakiet `pysnmp`, nie historyczny wariant `pysnmp-lextudio`. SQLite, JSON i CSV są dostępne w bibliotece standardowej Pythona. [Opis pakietu PySNMP](https://pypi.org/project/pysnmp/)

macOS:

```sh
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements-stage1.in
./.venv/bin/python -m pip check
./.venv/bin/python -c 'import psutil, dash, dash_cytoscape, netmiko, ntc_templates, textfsm, networkx, sqlite3, cryptography; from pysnmp.hlapi.v3arch.asyncio import get_cmd, USM_AUTH_HMAC192_SHA256, USM_PRIV_CFB128_AES; print("IMPORT_OK"); print("SQLite", sqlite3.sqlite_version)'
```

Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-stage1.in
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -c 'import psutil, dash, dash_cytoscape, netmiko, ntc_templates, textfsm, networkx, sqlite3, cryptography; from pysnmp.hlapi.v3arch.asyncio import get_cmd, USM_AUTH_HMAC192_SHA256, USM_PRIV_CFB128_AES; print("IMPORT_OK"); print("SQLite", sqlite3.sqlite_version)'
```

Oczekiwany wynik: `pip check` bez konfliktów i `IMPORT_OK`. Jeśli kompilacja zależności jest wymagana zamiast dostępnej paczki dla danego systemu, najpierw sprawdź interpreter/architekturę i dostępność zgodnych wersji. Nie zmieniaj całego stosu ani wersji Python bez odnotowania przyczyny.

## 5. Przygotuj snapshot i mały panel offline

### 5.1. Snapshot

Zapisz poniższy JSON jako `examples/snapshots/lab-001.json`. Dane są syntetyczne. To roboczy format demonstracji renderera, nie zatwierdzony produkcyjny model obserwacji z Etapu 2.

```json
{
  "schema_version": "stage1-demo-1",
  "project_id": "lab-001",
  "synthetic": true,
  "elements": [
    {"data": {"id": "sw1", "label": "SW1", "kind": "switch", "ip": "192.0.2.10"}},
    {"data": {"id": "sw2", "label": "SW2", "kind": "switch", "ip": "192.0.2.11"}},
    {"data": {"id": "h1", "label": "Host A", "kind": "host", "ip": "192.0.2.101", "mac": "02:00:00:00:00:01", "vlan": 10, "switch": "sw1", "port": "Gi1/0/1"}},
    {"data": {"id": "h2", "label": "Host B", "kind": "host", "ip": "198.51.100.102", "mac": "02:00:00:00:00:02", "vlan": 20, "switch": "sw2", "port": "Gi1/0/2"}},
    {"data": {"id": "h3", "label": "Host C", "kind": "host", "ip": "192.0.2.103", "mac": "02:00:00:00:00:03", "vlan": 10, "switch": "sw2", "port": "Gi1/0/3"}},
    {"data": {"id": "uplink", "source": "sw1", "target": "sw2", "label": "Gi1/0/24 ↔ Gi1/0/24", "kind": "uplink", "vlans": [10, 20]}},
    {"data": {"id": "l1", "source": "sw1", "target": "h1", "label": "Gi1/0/1", "vlan": 10}},
    {"data": {"id": "l2", "source": "sw2", "target": "h2", "label": "Gi1/0/2", "vlan": 20}},
    {"data": {"id": "l3", "source": "sw2", "target": "h3", "label": "Gi1/0/3", "vlan": 10}}
  ]
}
```

### 5.2. Panel, szczegóły, eksport i automatyczna przeglądarka

Zapisz jako `tools/probe_panel.py`:

```python
import argparse
import json
import threading
import time
import uuid
import webbrowser
from pathlib import Path
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener

import dash_cytoscape as cyto
from dash import Dash, Input, Output, ctx, html

ROOT = Path(__file__).resolve().parents[1]
snapshot = json.loads((ROOT / "examples/snapshots/lab-001.json").read_text(encoding="utf-8"))
parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=8050)
args = parser.parse_args()
if not 1024 <= args.port <= 65535:
    parser.error("Port musi należeć do zakresu 1024–65535")

cyto.load_extra_layouts()
app = Dash(__name__, serve_locally=True)
run_id = uuid.uuid4().hex
url = f"http://127.0.0.1:{args.port}"

@app.server.get("/_mapper_ready")
def ready():
    return run_id

app.layout = html.Div([
    html.H2("Mapper — próba offline"),
    html.P("Dane syntetyczne; brak odczytów sieci."),
    html.Button("Pobierz PNG", id="png", n_clicks=0),
    html.Button("Pobierz SVG", id="svg", n_clicks=0),
    cyto.Cytoscape(
        id="map", elements=snapshot["elements"],
        layout={"name": "breadthfirst"},
        style={"width": "100%", "height": "60vh"},
        stylesheet=[
            {"selector": "node", "style": {"label": "data(label)", "background-color": "#2563eb"}},
            {"selector": "node[kind = 'switch']", "style": {"shape": "rectangle"}},
            {"selector": "node[vlan = 20]", "style": {"background-color": "#d97706"}},
            {"selector": "edge", "style": {"label": "data(label)", "font-size": 10}},
        ],
    ),
    html.Pre(id="details"),
])

@app.callback(Output("details", "children"), Input("map", "tapNodeData"))
def details(data):
    return json.dumps(data, ensure_ascii=False, indent=2) if data else "Wybierz węzeł"

@app.callback(
    Output("map", "generateImage"),
    Input("png", "n_clicks"), Input("svg", "n_clicks"),
    prevent_initial_call=True,
)
def export_image(_png, _svg):
    return {"type": ctx.triggered_id, "action": "download", "filename": "mapper-lab-001"}

def open_when_ready():
    opener = build_opener(ProxyHandler({}))
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        try:
            with opener.open(url + "/_mapper_ready", timeout=1) as response:
                if response.read().decode() == run_id:
                    try:
                        opened = webbrowser.open(url)
                    except webbrowser.Error:
                        opened = False
                    if not opened:
                        print(f"Otwórz panel ręcznie: {url}", flush=True)
                    return
        except (URLError, OSError):
            pass
        time.sleep(0.2)
    print(f"Nie potwierdzono gotowości panelu. Sprawdź terminal: {url}", flush=True)

if __name__ == "__main__":
    print(f"Panel lokalny: {url}", flush=True)
    threading.Thread(target=open_when_ready, daemon=True).start()
    app.run(host="127.0.0.1", port=args.port, debug=False, use_reloader=False)
```

Przykład czeka na odpowiedź własnego procesu, dzięki identyfikatorowi uruchomienia; nie otwiera obcego serwera tylko dlatego, że coś odpowiada na porcie. Reloader jest wyłączony, żeby nie otwierać dwóch kart. Adres wypisany w terminalu ma służyć jako ręczne wyjście; sprawdź, czy terminal renderuje go jako klikalny link. Ten serwer służy lokalnej próbie, nie publikacji panelu dla innych użytkowników.

Mechanizm eksportu korzysta z `generateImage`, `action=download` i włączenia rozszerzenia SVG. Nie wymaga płatnej usługi. [Eksport obrazów](https://dash.plotly.com/cytoscape/images), [API komponentu](https://dash.plotly.com/cytoscape/reference)

macOS:

```sh
./.venv/bin/python tools/probe_panel.py
```

Windows:

```powershell
.\.venv\Scripts\python.exe tools/probe_panel.py
```

### 5.3. Wykonaj krótki odbiór panelu

1. Potwierdź automatyczne otwarcie właściwego URL i wyświetlenie dwóch switchy oraz trzech hostów.
2. Kliknij hosta i sprawdź IP/MAC/VLAN/port w szczegółach. Przesuń graf i zmień powiększenie.
3. Pobierz PNG i SVG, otwórz oba pliki oraz sprawdź etykiety i kompletność rysunku.
4. Zatrzymaj serwer przez `Ctrl+C`. Uruchom ponownie z `--port 8051`; przeglądarka ma otworzyć 8051, nie 8050.
5. Przy działającym pierwszym procesie uruchom drugi na tym samym porcie. Oczekuj błędu zajętego portu, bez automatycznego zatrzymywania innego procesu i bez otwarcia cudzej instancji. Następnie zakończ pierwszą instancję.
6. Odłącz Internet, uruchom panel i odśwież go z wyłączonym cache przeglądarki. Ponownie sprawdź szczegóły i eksporty. W narzędziach sieciowych przeglądarki wymagane zasoby mają pochodzić lokalnie, bez CDN.

W przykładzie połączenia hostów są zapisane w snapshotcie. Ich prawidłowy rysunek nie potwierdza działania silnika wnioskowania. Filtry pełnego panelu, ARP/FDB i confidence należą do późniejszych etapów.

## 6. Potwierdź SQLite i NetworkX bez projektowania pełnej bazy

Zapisz jako tymczasowy skrypt `tools/probe_storage.py`, uruchamiany Pythonem z venv:

```python
import json
import sqlite3
import networkx as nx

with sqlite3.connect(":memory:") as db:
    db.execute("CREATE TABLE probe (project_id TEXT, payload TEXT)")
    db.execute("INSERT INTO probe VALUES (?, ?)", ("lab-001", json.dumps({"ok": True})))
    assert db.execute("SELECT COUNT(*) FROM probe WHERE project_id=?", ("lab-001",)).fetchone()[0] == 1

graph = nx.Graph()
graph.add_edge("sw1", "sw2")
graph.add_edge("sw1", "h1")
assert nx.has_path(graph, "h1", "sw2")
print("STORAGE_GRAPH_OK")
```

Oczekiwany wynik: `STORAGE_GRAPH_OK`. To tylko próba bibliotek. Nie potwierdza jeszcze trwałego zapisu, izolacji projektów, migracji ani historii; te elementy odbierzemy po implementacji modelu w Etapie 2.

## 6A. Wykonaj podstawowe odkrywanie bez poświadczeń

Po próbie panelu i bazy wykonaj [poradnik podstawowego odkrywania](ETAP_1_ODKRYWANIE_PODSTAWOWE.md). Ta część jest wymagana niezależnie od marki routera i dostępności SNMP/SSH. Odczytaj lokalne interfejsy/trasy/sąsiadów, przygotuj ograniczony kolektor, a następnie sprawdź go we wskazanym LAN. Nie uruchamiaj do tego `run_probe.py snmp2` — ten launcher wymaga community, ponieważ bada inną ścieżkę.

Oczekiwane: brak żądania seedów/sekretów, jawny zakres i interfejs, znane aktywne hosty, źródła i świeżość, logiczne relacje oraz nieustalone porty/VLAN-y. Próba bez Internetu nadal korzysta z aktywnego LAN. Dla odtwarzania snapshotu offline nie wysyłamy sond. Wynik wpisz do raportu, także jeśli jest częściowy.

## 7. Przygotuj rozszerzone odczyty online i sekrety

Ta opcjonalna dla badanego LAN ścieżka wymaga konkretnego urządzenia z usługą zarządzającą i profilu RO. Jej próby pozostają wymagane do potwierdzenia rozszerzonego zakresu MVP. W sekcjach 7–9 nie uruchamiaj rekurencji ani skanowania podsieci; podstawowe sondowanie odbywa się oddzielnie według sekcji 6A. Pierwsza próba dotyczy jednego ręcznie wskazanego adresu IPv4.

Przed wykonaniem:

- Potwierdź połączenie przez Ethernet/Wi-Fi z trasą do adresu zarządzającego.
- Przygotuj v2c oraz v3 SHA-256/AES-128 zgodnie z istniejącą konfiguracją agenta. Aplikacja nie tworzy kont i nie włącza SNMP/SSH na urządzeniach.
- Dla SSH przygotuj konto RO oraz plik `known_hosts` z kluczem porównanym z fingerprintem otrzymanym od administratora. Samo pobranie klucza z sieci nie potwierdza jego autentyczności.
- Jeśli router nie udostępnia SNMP/SSH, pomiń te próby w tej sieci; nie zgaduj community. Użyj oddzielnego laboratorium albo wpisz „niewykonane — brak laboratorium”. Kontynuuj podstawowy LAN i offline; nie oznaczaj całej aplikacji jako niezdolnej do skanowania.

Poniższy launcher wprowadza hasła przez ukryty prompt i przekazuje je do procesu próby w ENV. Nie wpisujesz haseł w poleceniach terminala. Zapisz jako `tools/run_probe.py`:

```python
import argparse
import getpass
import ipaddress
import os
import subprocess
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("mode", choices=["snmp2", "snmp3", "ssh"])
args = parser.parse_args()
env = os.environ.copy()
env["MAPPER_TARGET_IP"] = str(ipaddress.IPv4Address(input("IPv4 urządzenia laboratoryjnego: ").strip()))
if args.mode == "snmp2":
    env["MAPPER_SNMP2_COMMUNITY"] = getpass.getpass("Community RO: ")
elif args.mode == "snmp3":
    env["MAPPER_SNMP3_USER"] = input("Użytkownik SNMPv3: ").strip()
    env["MAPPER_SNMP3_AUTH_KEY"] = getpass.getpass("Hasło uwierzytelniania: ")
    env["MAPPER_SNMP3_PRIV_KEY"] = getpass.getpass("Hasło szyfrowania: ")
else:
    env["MAPPER_SSH_USER"] = input("Użytkownik SSH RO: ").strip()
    env["MAPPER_SSH_PASSWORD"] = getpass.getpass("Hasło SSH (puste = klucz/agent): ")
    env["MAPPER_KNOWN_HOSTS"] = str(Path(input("Ścieżka do zweryfikowanego known_hosts: ").strip()).expanduser())
script = "probe_ssh.py" if args.mode == "ssh" else "probe_snmp.py"
command = [sys.executable, str(Path(__file__).with_name(script))]
if args.mode != "ssh":
    command.append(args.mode)
raise SystemExit(subprocess.run(command, env=env, check=False).returncode)
```

Uruchamiaj z prawdziwego terminala. Jeżeli `getpass` ostrzega, że nie może ukryć wpisywania, przerwij i użyj terminala obsługującego ukryty prompt. Nie zapisuj zrzutów ENV ani pełnych logów sesji. Launcher jest narzędziem laboratoryjnym dla jednego profilu, nie docelowym magazynem sekretów.

## 8. Sprawdź SNMPv2c i SNMPv3

Zapisz jako `tools/probe_snmp.py`:

```python
import asyncio
import os
import sys
from pysnmp.hlapi.v3arch.asyncio import (
    CommunityData, ContextData, ObjectIdentity, ObjectType,
    SnmpEngine, UdpTransportTarget, UsmUserData, get_cmd,
    USM_AUTH_HMAC192_SHA256, USM_PRIV_CFB128_AES,
)
from pysnmp.proto.rfc1905 import NoSuchInstance, NoSuchObject, EndOfMibView

async def probe():
    engine = SnmpEngine()
    try:
        if sys.argv[1] == "snmp2":
            auth = CommunityData(os.environ["MAPPER_SNMP2_COMMUNITY"], mpModel=1)
        else:
            auth = UsmUserData(
                os.environ["MAPPER_SNMP3_USER"],
                authKey=os.environ["MAPPER_SNMP3_AUTH_KEY"],
                privKey=os.environ["MAPPER_SNMP3_PRIV_KEY"],
                authProtocol=USM_AUTH_HMAC192_SHA256,
                privProtocol=USM_PRIV_CFB128_AES,
            )
        target = await UdpTransportTarget.create(
            (os.environ["MAPPER_TARGET_IP"], 161), timeout=3, retries=1,
        )
        result = await get_cmd(
            engine, auth, target, ContextData(),
            ObjectType(ObjectIdentity("1.3.6.1.2.1.1.1.0")),
            ObjectType(ObjectIdentity("1.3.6.1.2.1.1.2.0")),
            lookupMib=False,
        )
        indication, status, _index, bindings = result
        if indication or status:
            raise RuntimeError("SNMP_REQUEST_FAILED")
        missing = (NoSuchInstance, NoSuchObject, EndOfMibView)
        if len(bindings) != 2 or any(isinstance(value, missing) for _oid, value in bindings):
            raise RuntimeError("SNMP_VALUE_MISSING")
        print("SNMP_GET_OK: sysDescr i sysObjectID")
    finally:
        engine.close_dispatcher()

try:
    asyncio.run(asyncio.wait_for(probe(), timeout=30))
except Exception as exc:
    print("SNMP_FAIL:", type(exc).__name__)
    raise SystemExit(1)
```

Przykład korzysta z aktualnego API `v3arch.asyncio`, z jawnie podanymi algorytmami i numerycznymi OID. Nie wykonuje SET i nie pobiera zewnętrznych MIB-ów. Nie drukuje obiektu poświadczeń ani surowych wyjątków biblioteki. Jest ograniczony do domyślnego portu 161 i kontekstu — jeśli laboratorium wymaga innych, wprowadź wartości profilu jawnie, nie zgaduj. [API PySNMP 7.1](https://docs.lextudio.com/pysnmp/v7.1/docs/api-reference)

macOS:

```sh
./.venv/bin/python tools/run_probe.py snmp2
./.venv/bin/python tools/run_probe.py snmp3
```

Windows:

```powershell
.\.venv\Scripts\python.exe tools/run_probe.py snmp2
.\.venv\Scripts\python.exe tools/run_probe.py snmp3
```

Oczekiwany wynik dla obu profili: `SNMP_GET_OK`. W raporcie zapisz wersję protokołu, algorytmy, model agenta i czas; nie community ani hasła. Przy błędzie sprawdź wskazany cel, trasę, profil i uprawnienia z administratorem. Nie drukuj konfiguracji dostępu dla diagnostyki i nie przełączaj samoczynnie na v2c. Jeśli potrzebny jest zatwierdzony profil SHA-1/AES-128, wykonaj oddzielną, jawnie oznaczoną próbę, zastępując stałą uwierzytelniania przez `USM_AUTH_HMAC96_SHA`.

Sukces GET dwóch wartości nie potwierdza kompletności ARP/FDB/VLAN/LLDP ani działania dużych walków. Te odczyty i ograniczenia implementujemy w Etapie 2. Błędu dostępu nie traktuj jako zniknięcia urządzeń.

## 9. Sprawdź SSH i istniejący parser

Zapisz jako `tools/probe_ssh.py`:

```python
import os
from netmiko import ConnectHandler

password = os.environ.get("MAPPER_SSH_PASSWORD", "")
try:
    with ConnectHandler(
        device_type="cisco_ios", host=os.environ["MAPPER_TARGET_IP"],
        username=os.environ["MAPPER_SSH_USER"], password=password,
        use_keys=not bool(password), allow_agent=not bool(password),
        ssh_strict=True, alt_host_keys=True,
        alt_key_file=os.environ["MAPPER_KNOWN_HOSTS"],
        conn_timeout=10, auth_timeout=15, banner_timeout=15,
        allow_auto_change=False, session_log=None,
    ) as connection:
        rows = connection.send_command(
            "show mac address-table", use_textfsm=True, read_timeout=30,
        )
        if not isinstance(rows, list) or not rows:
            raise RuntimeError("PARSER_NOT_CONFIRMED")
        required = {"destination_address", "destination_port", "vlan_id"}
        if not all(required <= set(row) for row in rows):
            raise RuntimeError("PARSER_FIELDS_MISSING")
        print("SSH_PARSE_OK: liczba rekordów", len(rows))
except Exception as exc:
    print("SSH_FAIL:", type(exc).__name__)
    raise SystemExit(1)
```

Uruchom przez launcher:

```sh
./.venv/bin/python tools/run_probe.py ssh
```

Odpowiednik Windows:

```powershell
.\.venv\Scripts\python.exe tools/run_probe.py ssh
```

Oczekuj `SSH_PARSE_OK` i co najmniej jednego rekordu o wskazanych polach. Sprawdź w zanonimizowanej próbce, czy VLAN/MAC/port odpowiadają rzeczywistemu wynikowi CLI, a nie tylko czy parser zwrócił listę. Schemat pól porównaj z szablonem przypiętej wersji; zmiana nazw wymaga jawnego adaptera. Pusta FDB nie dowodzi błędu urządzenia, ale nie wystarcza do potwierdzenia parsera — potrzebna jest próbka z rekordem.

Netmiko może zwrócić tekst, gdy szablon nie zostanie zastosowany; nie uznaj tego za udane parsowanie. `use_textfsm`, timeout i kontrolę host key opisuje [API Netmiko](https://ktbyers.github.io/netmiko/docs/netmiko/base_connection.html); wzorce parserów opisuje [dokumentacja ntc-templates](https://ntc-templates.readthedocs.io/en/latest/user/lib_getting_started/).

Sterownik Cisco przygotowuje sesję poleceniami terminalowymi; sprawdź kod przypiętej wersji zgodnie z zatwierdzoną listą z karty. Nie wywołujemy `enable()`, trybu konfiguracji ani zapisu. Przy braku uprawnień raportujemy brak dostępu. Lista wszystkich planowanych poleceń z Etapu 0 nie musi być jeszcze pełnym kolektorem — na tym etapie wystarczy jedna potwierdzona ścieżka SSH+parser.

## 10. Powtórz podstawowy przekrój na Windows

1. Skopiuj pliki źródłowe i syntetyczny snapshot; nie kopiuj `.venv`, sekretów ani danych klienta z macOS.
2. Utwórz nowe venv Python 3.13 x64 i zainstaluj ten sam zestaw wersji głównych bibliotek.
3. Wykonaj `pip check`, kontrolę importów, SQLite/NetworkX i podstawowy przekrój z sekcji 6A, w tym adapter Windows i ograniczenia tras/cache. Uruchom panel. Sprawdź automatyczną przeglądarkę, zmianę portu, szczegóły, PNG/SVG i offline.
4. Jeśli dostępne jest laboratorium, powtórz po jednym odczycie SNMP i SSH. Brak dostępu oznacz jako niewykonaną próbę, nie jako zaliczoną zgodność.
5. W raporcie odróżnij Windows 10 od Windows 11. Jeśli dysponujesz tylko jednym z nich, drugi pozostaje do odbioru przed deklaracją wsparcia; nie potrzebujemy równolegle wielu wersji wszystkich bibliotek.

W przypadku zależności specyficznych dla systemu dopuszczalne są osobne pliki przypiętych wersji. Nie przepisujemy bibliotek do Pythona ani nie zmieniamy stosu tylko po to, żeby uniknąć opisania różnic instalacyjnych.

## 11. Przypnij wersje i sprawdź warunki dystrybucji

Po udanej próbie zapisz pełną listę z venv do UTF-8. macOS:

```sh
./.venv/bin/python -c 'from pathlib import Path; import subprocess,sys; result=subprocess.run([sys.executable,"-m","pip","freeze"],capture_output=True,text=True,check=True); Path("requirements-stage1-macos.txt").write_text(result.stdout,encoding="utf-8")'
```

Windows:

```powershell
.\.venv\Scripts\python.exe -c 'from pathlib import Path; import subprocess,sys; result=subprocess.run([sys.executable,"-m","pip","freeze"],capture_output=True,text=True,check=True); Path("requirements-stage1-windows.txt").write_text(result.stdout,encoding="utf-8")'
```

`pip freeze` zapisuje zainstalowane wersje; nie rozwiązuje za nas zgodności i nie jest pełnym lockfile z hashami. Przed odbiorem odtwórz środowisko z odpowiedniego pliku w osobnym venv i powtórz importy/panel. Nie usuwaj działającego środowiska, zanim odtworzenie się powiedzie. [Dokumentacja pip freeze](https://pip.pypa.io/en/stable/cli/pip_freeze/)

Dla dołączanych pakietów odczytaj warunki z ich rzeczywistych wersji, w tym zależności pośrednich. Zapisz nazwę, wersję, źródło, licencję i wymagane noty w `docs/THIRD_PARTY_NOTICES.md`; dołącz wymagane teksty. Automatyczna metadana licencji jest wskazówką, nie zastępuje treści warunków. Nie dodawaj triali, Enterprise ani zewnętrznego hostingu do realizacji funkcji.

Źródło OUI pozostaje zadaniem tego etapu: wybierz lokalne dane o warunkach umożliwiających zamierzony użytek i dystrybucję, zapisz pochodzenie/datę/warunki. Jeżeli nie zostało potwierdzone, producent pozostaje „nieustalony”, a raport jawnie wymienia brak. Nie uzupełniaj go płatnym API ani przypadkowo pobraną bazą. Własne symbole grafu i fonty systemowe nie wymagają osobnej płatnej paczki.

## 12. Zapisz raport i zakończ etap

Utwórz `docs/etap-1/RAPORT_ETAP_1.md`. Raport ma zawierać wyniki, a nie same zaznaczone deklaracje. Możesz użyć szablonu:

```markdown
# Raport Etapu 1

Data i wykonujący:
Systemy / architektury / Python / RAM / wolny dysk:
Pliki przypiętych zależności:
Laboratorium i zakres próby bez sekretów:

| Próba | Wynik: OK / błąd / niewykonana | Dowód, czas i ograniczenia |
|---|---|---|
| Instalacja/importy/pip check macOS ARM | | |
| Panel i automatyczne otwarcie właściwego portu | | |
| Szczegóły węzła, PNG i SVG | | |
| Offline bez CDN i cache | | |
| SQLite i NetworkX | | |
| Interfejs IPv4/maska/trasa i wybór zakresu | | |
| Podstawowe odkrywanie bez seedów/poświadczeń | | |
| Cache vs świeża odpowiedź, host bez ICMP | | |
| Limity/anulowanie i zmiana interfejsu/VPN | | |
| Mapa logiczna, port/VLAN nieustalony | | |
| Aktywny LAN bez Internetu | | |
| SNMPv2c GET | | |
| SNMPv3 SHA-256/AES-128 GET | | |
| SSH i parser istniejącego szablonu | | |
| Windows 10 x64 | | |
| Windows 11 x64 | | |
| Odtworzenie środowiska z przypiętych wersji | | |
| Warunki bibliotek/zależności i OUI | | |

Pozostałe luki, właściciel, wpływ i następny krok:
Zmiany wymagające decyzji względem karty Etapu 0:
Ocena: gotowe / częściowo gotowe / wymaga naprawy.
Zatwierdzenie wyniku przed Etapem 2:
```

W raporcie rozróżnij poprawność przykładowego grafu od poprawności odkrywania prawdziwej sieci. Duża próba 50 switchy/1000 hostów/50 tys. obserwacji dotyczy późniejszego importu, korelacji i wydajności — nie jest warunkiem udawania gotowego silnika już w Etapie 1.

Pełny wynik Etapu 1 wymaga lokalnego panelu/D02/eksportów, podstawowego odkrywania bez profili i oddzielnie wskazanych protokołów/parsera, wersji/warunków zależności oraz wyników wymaganych OS. Brak laboratorium zarządzającego nie blokuje wykonania i oceny podstawowego przekroju, lecz pozostawia ścieżkę rozszerzoną niepotwierdzoną. Jeżeli czegoś nie wykonano, przedstawiamy częściowy wynik z przyczyną i planem uzupełnienia. Przejście do Etapu 2 wymaga zatwierdzenia tego konkretnego wyniku; nie następuje automatycznie po przeczytaniu poradnika.

## 13. Krótka diagnostyka

| Problem | Pierwsze działanie |
|---|---|
| Router nie ma SNMP/SSH | Wykonaj podstawowe odkrywanie z sekcji 6A; community nie jest wymagane |
| Nie widać hosta bez ping | Odczytaj sąsiadów, sprawdź świeżość, izolację i trasę; nie uznawaj braku ICMP za nieistnienie |
| Wybrany LAN, ruch przez VPN | Sprawdź efektywną trasę; pomiń sondę innym interfejsem i pokaż powód |
| Import starego API PySNMP | Sprawdź interpreter venv, wersję pakietu i import z `v3arch.asyncio` |
| v2c działa, v3 nie | Sprawdź profile, zgodne algorytmy, backend kryptografii i agenta; bez automatycznego downgrade |
| Brak SNMP/SSH przez Wi-Fi | Sprawdź trasę/VLAN zarządzający i ograniczenia AP z administratorem |
| SSH odrzuca host key | Porównaj fingerprint z zaufanym źródłem; nie wyłączaj weryfikacji |
| SSH zwraca tekst zamiast listy | Sprawdź dostępność szablonu i zgodność odpowiedzi, a nie tylko połączenie |
| Zajęty port panelu | Zatrzymaj własną poprzednią instancję albo wybierz `--port 8051` |
| PNG działa, SVG nie | Sprawdź `load_extra_layouts()`, konsolę przeglądarki i wersję komponentu |
| Przeglądarka nie otwiera się sama | Użyj wypisanego adresu i zanotuj błąd D02 do naprawy |
| Panel działa tylko z Internetem | Sprawdź CDN, zasoby/fonty i cache; wymagane zasoby mają być lokalne |

Źródła API sprawdzono podczas pisania poradnika. Aktualizacja dokumentacji nie wykonuje instalacji ani prób online. W projekcie istnieją robocze pliki i venv; faktyczne wyniki należy potwierdzić i zapisać w raporcie.
