# Raport poprawek 3.1 — mapper-sieci 0.3.1

Data: 24 października 2026 r. Podstawa: [plan 3.1](../poradniki/ETAP_3_1_POPRAWKI_PO_REVIEW.md), [ADR-005](../decisions/ADR-005-bezpieczne-sondy-i-blokady.md), autoryzacja „przygotuj szczegolowy plan poprawek, i zacznij wdrazac”. Status: **kod wdrożony i odbiór offline wykonany; rzeczywiste Windows/NTFS oraz switch nieodebrane**. Nie wykonano nowych sond ani zmian konfiguracji urządzeń.

## Wdrożone zmiany

| Obszar | Implementacja | Wynik weryfikacji |
|---|---|---|
| R01: koszt sond | Cache stanu per adapter, TTL 1 s (0,1–2), asyncio.Lock łączący odświeżenia, błędy unieważniają stare dane. Metryki Windows pobierane jednym Get-NetIPInterface na odświeżenie. | 253 sondy w jednym oknie → 1 odczyt tras; po TTL i zmianie VPN jeden wspólny odczyt i pominięcie sond. W symulacji 5/s przez 50,4 s: 51 odczytów zamiast 253, redukcja około 80%. To licznik wywołań, nie pomiar PowerShell ani czasu skanu na sprzęcie. |
| R05: źródło | macOS: `-S source_ip -b interface`. Windows: GetBestRoute2 + IcmpSendEcho2Ex, aktualny alias/indeks i źródło, bez fallbacku PING.EXE. Jeden ograniczony native call z zamknięciem uchwytu; anulowanie czeka na jego zakończenie. | Testy atrap sprawdzają struktury Win32, adres źródłowy, trasę/indeks, status odpowiedzi, timeout i close/cancel. Nie potwierdzają działania DLL ani fizycznego interfejsu na Windows. |
| R02: blokady | Repository trzyma project lock przez swój czas życia i migracje; globalny cycle lock tylko dla run_cycle. Usunięto globalny lock z operacji offline, tworzenia i importu. | Topology build/history, oba eksporty, tworzenie i replay działają w innym projekcie pod zajętą blokadą kolekcji. Drugi cykl nadal odrzucony, ten sam projekt zwraca PROJECT_BUSY, wyjątek konstrukcji zwalnia lock. |
| R09: prywatne pliki | POSIX: 0600/0700 już od tworzenia. Windows: chroniona DACL użytkownik/SYSTEM/administratorzy przy tworzeniu oraz zabezpieczenie istniejących własnych plików. Weryfikacja wsparcia trwałych ACL przez wolumin; brak ochrony przerywa zapis. | Sprawdzone uprawnienia POSIX przed pierwszym zapisem, brak nadpisania/link follow i kontrakt Windows backendu/SDDL/fail-closed. Efektywna DACL NTFS nie była badana z drugiego konta. |
| R06: parsery | Stricte wymagane metryki/alias Windows, BOM/Unicode, obsługa pojedynczego rekordu/listy/null; ucięty lub pusty tekst nie udaje kompletnej pustej tablicy. | Syntetyczne warianty przechodzą; błędne dane odrzucone. Nie są to zrzuty z Windows PL/EN. |

Nowe moduły: [private_files](../../src/mapper/private_files.py), [windows_security](../../src/mapper/windows_security.py), [windows_ipv4](../../src/mapper/discovery/windows_ipv4.py). Zmieniono adapter OS, Limits, Repository, CLI i eksport/import. Schemat SQLite pozostaje v2, źródłowe snapshoty v1, reguły silnika topologii bez zmian. Nie dodano bibliotek ani CI/CD; zachowano podpis MIT i istniejące noty.

## Sprawdzenia

- `PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m unittest discover -s tests/critical -v`: **38/38 OK, 1,072 s** na macOS ARM. 26 wcześniejszych testów i 12 nowych regresji. Sprawdzenie trybów POSIX jest jawnie pomijane na Windows; nie zastępuje odbioru NTFS.
- `./.venv/bin/python -m pip --no-cache-dir check`: **No broken requirements found**.
- `./.venv/bin/python -m pip --no-cache-dir install --editable . --no-deps --no-build-isolation --no-index`: **0.3.1 zainstalowane**, bez pobierania i zmiany bibliotek.
- `git diff --check`, składnia Python i kontrola zmienionych dokumentów: bez błędów w przekazanej wersji.
- Odbiór przez jednorazowy `/private/tmp/mapper_stage31_accept.py`, na kopii bazy utworzonej SQLite backup z otwarciem źródła mode=ro. Audyt blokował socket.connect/sendto/getaddrinfo; prób ruchu wychodzącego **0**. Kod Windows podczas testów używał wyłącznie atrap.
- [Dowody zbiorcze JSON](ODBIOR_OFFLINE_2026-10-24.json). Prywatne źródła i eksporty pozostały poza repozytorium. Nie zmieniano źródłowej bazy użytkownika ani jego konfiguracji sieci.

## Zachowany wynik LAN

534 obserwacje źródłowe, hash przed/po zgodny. Nadal 14 endpointów + lokalny interfejs + segment oraz 15 relacji logicznych. Nie dopisano fizycznych portów/VLAN-ów. Ponowne przeliczenie i replay bez regresji; `integrity_check=ok`, `foreign_key_check` pusty. Testy eksportów/build/history/import/create wykonano z zajętą globalną blokadą kolekcji; wszystkie te operacje offline zakończyły się kodem 0.

## Granice i dalszy odbiór

- Windows adapter i DACL są zaimplementowane, lecz **brak próby na rzeczywistym Windows/NTFS**. Trzeba potwierdzić DLL/ABI na docelowym Windows x64, źródło i interfejs przy Wi-Fi/LAN/VPN, anulowanie oraz dostęp drugiego zwykłego konta do bazy, backupu i eksportów. To blokuje deklarację odebranego wsparcia Windows, nie wykonanie kodu i analizy offline.
- TTL skraca odstęp odświeżenia, ale nie stanowi atomowej gwarancji całej tablicy podczas wysyłania. macOS binduje interfejs i źródło; Windows kontroluje bieżącą trasę oraz podaje źródło systemowemu API. Wyścigu zmiany routingu i fizycznej drogi pakietu nie uznajemy za rozstrzygnięty testem parametrów.
- Windows ACL dotyczy obiektów aplikacji, nie dowolnych katalogów użytkownika. Dostęp SYSTEM/administratorów jest zamierzony. Brak trwałych ACL na woluminie oznacza odmowę, a nie pozorną ochronę chmod.
- Inne CLI tego samego projektu mogą zwrócić PROJECT_BUSY podczas kolekcji; pracę na wcześniejszym grafie w uruchomionym podglądzie obsługuje kopia w pamięci. Starszy proces 0.3.0 nie zna nowego project locka; nie należy mieszać działających wersji podczas aktualizacji.
- Rzeczywiste SNMPv2c/v3/SSH i duża sieć nadal wymagają odbioru. Nowych platform SSH i Linuksa nie włączono do zakresu tej poprawki. Przygotowanie instalatora i zamknięcie wymagań licencyjnych nadal należy do Etapu 5.
- Nie zamknięto całego review jako „naprawione”. R01/R02 mają potwierdzone poprawki offline; R05/R09 mają kod oraz kontrakty testowe, ale odbiór Windows pozostaje otwarty; R06 częściowo pokryty próbkami syntetycznymi, R07/R08 wymagają środowiska/artefaktu. Etapu 4 nie rozpoczęto.

Prywatne receipt i eksporty tego odbioru: `/Users/paweljuroszek/Library/Application Support/MapperSieci/acceptance/stage31-20261024-ewlm41us`. Dane nie trafiły do publicznych fixture'ów; w repozytorium zachowano tylko zbiorcze wyniki testów.

Końcowa kontrola statyczna: 27 modułów Python przeanalizowanych przez AST, 261 lokalnych odnośników Markdown bez brakujących celów. Nowe pliki nie wymagają odwołań do old/ ani prototypes/. Nie wykonano commita.
