# Raport Etapu 2

Data: 23 października 2026 r. Wykonujący: Codex.

Status: **odbiór offline i podstawowego LAN na macOS — OK; rzeczywiste SNMP/SSH i Windows niezweryfikowane**. Szczegółowe wyniki: [odbiór 23 października](ODBIOR_2026-10-23.md). Przedstawiony wynik został zatwierdzony przez użytkownika; ograniczenia pełnego odbioru online pozostają. Plan Etapu 3 podlega osobnej ocenie.

## Zakres

Zaimplementowano pakiet `mapper-sieci` 0.2.0, CLI, walidowany model obserwacji, sześć tabel SQLite i migrację v1, izolację projektów, koordynację zapisu, kontroler cyklu, adaptery lokalne Windows/macOS, ograniczone sondowanie, adapter PySNMP, pierwszy adapter Netmiko/TextFSM, rekurencję LLDP, snapshoty JSON/CSV i import do nowego projektu bez ruchu sieciowego. Zachowano dotychczasowe skrypty `prototypes/tools/`.

Podstawowy skaner nie był dostępny w przekazanych plikach Etapu 1; uzupełniono go w zatwierdzonym zadaniu wejściowym 2.0. Nie odtworzono fikcyjnego raportu rzeczywistych prób Etapu 1.

Implementacja nie wyznacza jeszcze końcowego portu hosta, confidence ani historii zdarzeń i nie zmienia panelu próbnego w pełny panel produktu. To zadania kolejnych etapów.

## Środowisko wykonanych sprawdzeń

- Darwin/macOS, architektura arm64; Python 3.13.0; SQLite 3.45.3.
- psutil 7.2.2, PySNMP 7.1.30, cryptography 50.0.2, Netmiko 4.8.0, ntc-templates 9.3.0, TextFSM 2.1.0.
- W istniejącym venv są także Dash 4.4.1 i dash-cytoscape 1.0.2. Nowego panelu w tym etapie nie implementowano.
- Nie aktualizowano istniejących bibliotek. Pakiet mappera zainstalowano lokalnie w trybie editable bez pobierania zależności i bez Internetu.

## Wykonane komendy i wyniki

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src ./.venv/bin/python -m unittest discover -s tests/critical -v
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src ./.venv/bin/python -m mapper doctor
./.venv/bin/python -m pip check
git diff --check
./.venv/bin/python -m pip --no-cache-dir install --editable . --no-deps --no-build-isolation --no-index
```

Wyniki: **15 testów, OK**, ostatni zapisany przebieg około 0,52 s; poprawne wersje `doctor`, `No broken requirements found`, brak zgłoszeń `git diff --check`, poprawne zbudowanie i instalacja lokalnego entry pointu. `git diff --check` nie obejmuje plików nieśledzonych; nowe pliki sprawdzono dodatkowo pod względem składni i whitespace podczas przekazania.

Oddzielnie uruchomiono z tymczasowego katalogu, bez `PYTHONPATH`, zainstalowane polecenie `.venv/bin/mapper`: `demo` → `snapshot export` → `snapshot import --new-project` → `snapshot list`. Wynik: poprawny zapis, trzy syntetyczne obserwacje, nowy UUID i `origin=imported`. Przebieg nie wywoływał kolektorów sieciowych.

Testy używają lokalnych fixture'ów, atrap oraz tymczasowych baz. Operacje `socket.connect`, `connect_ex` i `sendto` są w nich blokowane. Sprawdzono także rzeczywisty parser ntc-templates na syntetycznej tablicy MAC i konstrukcję profilu SNMPv3 z podmienionym transportem. Nie jest to rzeczywiste uwierzytelnienie ani szyfrowany odczyt z urządzenia.

## Kryteria

| Kryterium | Wynik i dowód |
|---|---|
| E2-01, E2-03, E2-04 | OK lokalnie: oddzielne bazy, schemat v1, trwałość, publikacja pełnego/częściowego wyniku, odczyt po ponownym otwarciu |
| E2-02 | OK na atrapach: źródła lokalne, zakres, wyniki sond i cache; rzeczywisty LAN odebrany w aktualizacji opisanej poniżej |
| E2-05 | Normalizacja wszystkich zaimplementowanych tabel SNMP sprawdzona na fixture'ach; bridge port 12 nie jest utożsamiany z ifIndex 101, FDB ID 7 nie staje się VLAN 7 |
| E2-06 | Niewykonane rzeczywiste SNMPv2c/v3 i SSH — brak osobnego wskazanego celu i profilu. Profile i fasady sprawdzone lokalnie, bez ruchu |
| E2-07, E2-08 | OK na atrapach: awaria targetu nie blokuje pozostałych, ograniczenia i anulowanie, nieopublikowany cykl po przerwaniu, poprzedni wynik pozostaje dostępny |
| E2-09 | OK lokalnie: eksport/import zachowuje fakty, konteksty i czasy, pochodzenie importu jest jawne; testowy znacznik sekretu nie trafia do bazy |
| E2-10 | Raport i instrukcja przygotowane; rzeczywisty odbiór Windows 10/11 niewykonany |

## Ograniczenia i następny krok

W późniejszym odbiorze wykonano autoryzowany skan podstawowego LAN na macOS: 253 cele, 8 odpowiedzi, 127,01 s i poprawny zapis/replay. Nie wykonano połączeń SNMP/SSH, kontrolowanej próby izolacji Wi-Fi/VPN ani uruchomienia na Windows. Parsery formatów obu OS mają sprawdzenia na małych próbkach; zgodność wszystkich wersji systemów nie jest z tego wyprowadzana.

Odczyt SNMP ma konserwatywny budżet liczby varbindów, więc limit może uciąć dużą tabelę przed zebraniem tylu wierszy, ile wynosi limit liczbowy. Wynik pozostaje jawnie częściowy. SSH ogranicza liczbę znormalizowanych rekordów, ale rozmiar surowego bufora jest zależny również od Netmiko. Nie dodano własnego transportu ani parsera uniwersalnego dla wszystkich producentów.

Nie mierzono wydajności dla 50 switchy/1000 hostów ani szczytowego RAM; to nie jest potwierdzona gwarancja wydajności. Nie wykonano pełnej symulacji fizycznej awarii dysku; transakcje i przerwanie publikacji sprawdzano w lokalnych bazach.

Odbiór offline i podstawowego LAN wykonał Codex na polecenie użytkownika; [wynik i lokalizacja danych](ODBIOR_2026-10-23.md). Rzeczywiste SNMP/SSH wymagają wskazania urządzeń i profili. Po zatwierdzeniu opisanego wyniku można rozpocząć Etap 3.

## Zatwierdzenie wyniku

23 października 2026 r. użytkownik zatwierdził przedstawiony wynik poleceniem „Zatwierdzam wynik etapu 2”. Etap 2 jest zamknięty w opisanym zakresie: odbiór offline i podstawowego LAN na macOS. Rzeczywiste SNMP/SSH, Windows oraz duża próba wydajnościowa pozostają niezweryfikowane; zatwierdzenie nie zmienia tych faktów. Kolejny krok to ocena [planu Etapu 3](../poradniki/ETAP_3_TOPOLOGIA_I_HISTORIA.md), przed kodowaniem.
