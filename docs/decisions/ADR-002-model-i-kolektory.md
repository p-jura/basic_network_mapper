# ADR-002 — model danych i kolektory

Data: 23 października 2026 r. Status: zatwierdzone przez użytkownika.

Podstawa: plan `docs/poradniki/ETAP_2_MODEL_DANYCH_I_KOLEKTORY.md` oraz polecenie „ok zatwierdzam plan, dzialaj”.

Przyjęto sześć tabel SQLite, wspólną kopertę obserwacji z walidowanym payloadem, osobny katalog/bazę projektu, jeden zapisujący i krótkie transakcje. Snapshot częściowy pozostaje jawnie częściowy. Domyślne katalogi danych są systemowe; można wskazać własny `--data-dir`. Import ograniczamy początkowo do 100 MiB i 200 tys. obserwacji; limity są jawnie konfigurowalne.

Podstawowy kolektor działa bez poświadczeń. Opcjonalne kolektory używają istniejących PySNMP i Netmiko/ntc-templates; nie implementujemy protokołów. Sekrety wyłącznie przez ENV/agent SSH, bez ich zapisu w bazie, logach lub snapshotach. Wspólny model nie nadaje jeszcze pewności fizycznego podłączenia.

Zakres wykonania: model, SQLite, kontroler, adaptery lokalne, SNMP i pierwszy SSH, replay oraz krytyczne testy na atrapach. Nie uruchamiamy aktywnych skanów, SNMP ani SSH bez osobnego zakresu operatora. Brak podstawowego skanera w widocznych plikach zostanie uzupełniony w ramach zatwierdzonego zadania wejściowego 2.0. Nie zmieniamy roboczych `prototypes/tools/` i wariantu Flutter/Dart.

Wyniki rzeczywistych odczytów i zgodność Windows pozostają do osobnego odbioru. Etap 3 wymaga zatwierdzenia wyniku Etapu 2.
