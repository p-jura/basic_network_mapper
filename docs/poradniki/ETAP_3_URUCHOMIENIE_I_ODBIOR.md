# Etap 3 — uruchomienie i odbiór

Stan: 23 października 2026 r., mapper-sieci 0.3.0. Polecenia tego poradnika wyłącznie przeliczają zapisane dane. Nie uruchamiają sond ani kolektorów.

## 1. Środowisko

Otwórz terminal w głównym katalogu projektu:

```sh
cd "/Users/paweljuroszek/all_projects/other/Maper sieci"
./.venv/bin/mapper --version
./.venv/bin/mapper doctor
```

Oczekuj wersji `0.3.0`. Kod zainstalowano już editable, bez pobierania bibliotek. NetworkX jest zależnością silnika. Istniejące Dash/dash-cytoscape stanowią opcjonalny zestaw `preview`; bez niego działa budowanie/eksport/historia. Na nowym stanowisku instalację zależności wykonuje się według dostępności lokalnych wheel i wymagań licencyjnych — ta próba nie potwierdza nowego instalatora ani Windows.

Przy pierwszym otwarciu istniejącej bazy v1 aplikacja automatycznie robi spójny backup `mapper-v1-<UUID>.sqlite3.bak` w katalogu projektu danych, następnie migruje do v2. Dotyczy to także otwarcia przez polecenia źródłowych snapshotów. Błąd migracji wycofuje transakcję; backup pozostaje. Nie usuwaj go przed odbiorem. Oryginalne obserwacje i format snapshotu v1 nie zmieniają się.

## 2. Bezpieczna próba na dołączonym przykładzie

```sh
./.venv/bin/mapper snapshot import --new-project \
  --input examples/snapshots/stage3-managed.json \
  --name "Etap 3 — przykład offline"
```

Skopiuj `project_id` z odpowiedzi. W kolejnych poleceniach zastąp `UUID_PROJEKTU` właśnie tym ID. Przykład jest w całości syntetyczny: 2 punkty odczytu switchy, 1 host, znany kontekst, bridge port 12 różny od ifIndex 101, VLAN 10 oraz LLDP z numerem lokalnym 5 różnym od ifIndex 900.

```sh
./.venv/bin/mapper topology build --project UUID_PROJEKTU
./.venv/bin/mapper topology export --project UUID_PROJEKTU --output topologia-demo.json
./.venv/bin/mapper history --project UUID_PROJEKTU
```

Oczekuj 3 węzłów, jednego sąsiedztwa LLDP, jednego `attachment` do portu `Gi101`/ifIndex 101/VLAN 10 i jednego `attachment_candidate` przez uplink `Gi900`. Ostrzeżenie `UPLINK` wyjaśnia pominięcie kandydata. Dwa zdarzenia to pierwsza obserwacja i syntetyczny dowód świeżej obecności; po imporcie pochodzenie jest jawnie `imported`, nigdy nowym skanem.

Powtórz `topology build` i `history`. ID węzłów i liczba zdarzeń mają pozostać takie same. Eksport tworzy nowy plik; istniejący plik nie jest nadpisywany.

## 3. Podgląd w przeglądarce

```sh
./.venv/bin/mapper topology view --project UUID_PROJEKTU --port 8051
```

Serwer nasłuchuje tylko na `127.0.0.1`. Przeglądarka otwiera rzeczywisty port po gotowości własnego serwera. Przy zajętym porcie pojawia się `PANEL_PORT_UNAVAILABLE`, bez zatrzymywania innego procesu i bez otwarcia jego panelu. `--no-browser` wyłącza automatyczne otwieranie; wtedy wejdź samodzielnie na `http://127.0.0.1:8051`.

Sprawdź trzy węzły, etykiety portów/VLAN i legendę. Kliknij hosta: szczegóły mają IP/MAC, port 101, bridge port 12, VLAN 10, confidence `high` i dowody. Przesuwanie i powiększenie obsługuje Cytoscape. Zakończ własny proces `Ctrl+C`.

To prosty podgląd reguł Etapu 3. Pełny przepływ operatora, filtry, wygodna tabela historii i PNG/SVG pozostają Etapem 4. Nie przenosimy ich do tej próby.

## 4. Istniejący projekt LAN

Użyj ID istniejącego projektu z Etapu 2 (katalog UUID w katalogu danych aplikacji), a następnie tych samych poleceń `topology build`, `export`, `view` i `history`. Nie uruchamiaj `collect --run`, aby obejrzeć zapisany wynik.

Na stanowisku macOS odebrany snapshot LAN daje 14 endpointów, 1 lokalny interfejs, 1 segment i 15 relacji logicznych. Brak danych switchy oznacza `port=null`, `vlan_id=null`, `switch_id=null`. Osiem świeżych odpowiedzi IP jest odróżnionych od odczytanych wpisów cache; 253 cele nie oznaczają 253 wykrytych hostów.

## 5. Okno źródeł, wybór cyklu i historia

```sh
./.venv/bin/mapper snapshot list --project UUID_PROJEKTU
./.venv/bin/mapper topology build --project UUID_PROJEKTU --cycle UUID_CYKLU --max-skew 300
./.venv/bin/mapper history --project UUID_PROJEKTU --limit 100
```

`--cycle` wybiera zwracany graf. Budowanie uzupełnia brakujące wyniki zachowanych snapshotów chronologicznie, dzięki czemu historia ma spójny poprzednik. Wynik jest niezmienny dla pary snapshot/reguły. Inne `--max-skew` tworzy osobny zestaw reguł, np. `1:skew=300`; historia może zawierać kilka zestawów. Filtruj przez `history --rules-version '1:skew=300'`. Limit odczytu historii: 1–10000 zdarzeń. Wstawienie dawnych danych przed już policzoną historią wymaga nowego projektu/replay (`BACKDATED_REPLAY_REQUIRES_NEW_PROJECT`), aby nie zmieniać po cichu starych zdarzeń.

Stan „dłużej niezaobserwowany” wymaga wcześniejszej świeżej odpowiedzi ICMP oraz 3 udanych prób tego samego zbioru IP w tym samym interfejsie/zakresie, obejmujących co najmniej 30 min od pierwszego braku odpowiedzi. Częściowy cykl, awaria, zmiana zakresu i cache nie tworzą pewnego odłączenia. Nie rozszerzamy tej reguły na sam brak wpisu w FDB/ARP.

Mocna zmiana portu wymaga jednoznacznych, świeżych i porównywalnych przypisań. Cache bez znanego wieku obniża poziom do `medium`; sam wybór takiego kandydata nie tworzy `port_changed`. Trzy naprzemienne mocne zmiany w oknie reguł dają podejrzenie flappingu, nie dowód aktywnej pętli.

## 6. Formaty, retencja i krytyczne sprawdzenia

`topology export` zapisuje osobny JSON `format=mapper-topology`, schema 1: graf, dowody, ostrzeżenia, zdarzenia bieżącego snapshotu i stan porównawczy historii. Nie importuj go przez `snapshot import`; ten importer przyjmuje źródłowy snapshot v1. Dotychczasowy eksport źródłowy JSON/CSV nadal działa. Zdarzenia ze wszystkich zachowanych porównań odczytuje `history`.

Snapshoty mają retencję 7 dni z ochroną ostatniego wyniku i ostatniego kompletnego wyniku zakresu; dodatkowo chroniony jest najnowszy graf każdego zestawu reguł wraz ze stanem historii. Zdarzenia trwają 90 dni niezależnie od usunięcia źródłowego cyklu. Retencję wykonuje kontroler kolekcji, a budżet projektu uwzględnia również backupy. Nie kasuj ręcznie bazy lub backupów podczas działania aplikacji.

```sh
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m unittest discover -s tests/critical -v
```

26 małych testów chroni newralgiczne reguły Etapów 2–3. Nie dodano CI/CD ani rozbudowanej infrastruktury. [Raport odbioru](../etap-3/RAPORT_ETAP_3.md) podaje wykonane próby i granice potwierdzenia.
