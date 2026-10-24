# Etap 3.1 — szczegółowy plan poprawek po review

Data: 24 października 2026 r. Status: **kod 0.3.1 wdrożony; odbiór offline wykonany, Windows/NTFS nieodebrane**. Wdrożenie autoryzowano poleceniem „przygotuj szczegolowy plan poprawek, i zacznij wdrazac”. Podstawa: [review R01–R09](../reviews/REVIEW_2026-10-24.md) oraz [ADR-005](../decisions/ADR-005-bezpieczne-sondy-i-blokady.md). Zgoda obejmuje kodowanie i odbiór offline, bez ponownego aktywnego skanowania.

## Cel i granice

Usunąć odczyt tras per adres, oddzielić globalną blokadę kolekcji od pracy w projektach, wymusić źródło IPv4 w adapterze Windows i chronić pliki przy ich tworzeniu. Zachować jedną aktywną kolekcję, dotychczasowy model/snapshot v1 i SQLite v2. Nie rozszerzamy SSH poza uzgodnioną platformę ani systemów o Linux. Kwestie dystrybucji pozostają osobnym odbiorem Etapu 5.

## 3.1.1 — stan tras i interfejsów (R01/R06)

- Dodać jeden cache stanu per instancja adaptera/cykl, współdzielony przez pracowników asynchronicznych; brak globalnego cache między projektami i uruchomieniami.
- TTL `route_refresh_seconds=1.0 s`, konfigurowalny w przedziale 0,1–2 s. Współbieżne odświeżenia łączy jeden asyncio.Lock. Odczytywane interfejsy przed i po trasach muszą być zgodne. Wynik/błąd przechowywać przez krótki TTL; błędny odczyt kasuje poprzedni sukces, bez używania starych tras.
- Stan tras nie jest dowodem obecności hosta. Nie utrzymywać jednej tablicy na cały wielogodzinny cykl. Po utracie źródła, zmianie interfejsu, niezgodnych/równorzędnych trasach lub błędzie odczytu pominąć sondę z jawnym powodem.
- Na macOS ping otrzymuje zarówno `-S source_ip`, jak i potwierdzone lokalnym man page `-b interface`; cache nie zastępuje powiązania sondy z interfejsem.
- Windows Get-NetRoute i Get-NetIPInterface pobierać raz na odświeżenie; metryki połączyć w pamięci PowerShell, zamiast uruchamiać cmdlet metryki dla każdego wiersza trasy.
- Odbiór deterministyczny: 253 cele, 4 pracowników, wspólne nieprzeterminowane okno → 1 odczyt tras. Po przekroczeniu TTL → dokładnie jedno wspólne odświeżenie. Dla zegara symulującego 5 celów/s odczyty mają zależeć od TTL, nie każdego celu. Nie nazywać tego pomiarem realnej wydajności Windows.

## 3.1.2 — źródłowy IPv4 Windows (R05)

- Cienki adapter ctypes do systemowych GetBestRoute2 i IcmpSendEcho2Ex; bez nowej biblioteki i bez własnego stosu ICMP. Powiązać źródłowy IPv4, sprawdzić aktualny indeks/alias interfejsu i on-link route bezpośrednio przed wysłaniem.
- Użyć stałych rozmiarów Win32 w strukturach ctypes, bez zależności od rozmiaru C long na macOS. Walidować kod wyniku, adres odpowiadającego hosta i typ odpowiedzi; unreachable/błąd API nie jest zwykłą odpowiedzią ani zniknięciem hosta.
- Brak API lub niezgodność źródła/trasy oznacza jawny błąd/pominięcie; brak fallbacku do niepowiązanego PING.EXE. `/S` nie służy do IPv4.
- Native call ma własny timeout do 1 s, pojedynczą sondę oraz zamykanie uchwytu w finally. Przy anulowaniu zaczekać na zakończenie ograniczonego wywołania wątku; nie uwalniać miejsca pracownika z pozostawioną sondą w tle.
- Testy na atrapach: przekazane źródło i cel, zmiana indeksu/trasy, błąd API, timeout, ICMP error, sprzątanie zasobów i anulowanie. Odbiór rzeczywistego pakietu/źródła wymaga Windows; sam test struktur nie potwierdza zgodności platformy.

## 3.1.3 — blokady (R02)

- Pozostawić globalny `.cycle.lock` wyłącznie dla aktywnej kolekcji. Drugi cykl w tym samym katalogu danych nadal jest odrzucany.
- Dodać `.project.lock`, automatycznie obejmujący czas życia Repository, w tym tworzenie bazy, migrację i zapisy. Jeden właściciel repozytorium na projekt; odczyty SQLite przez drugi proces tego samego projektu mogą zwrócić PROJECT_BUSY. Podgląd już uruchomiony działa z kopią grafu po zamknięciu repozytorium.
- Usunąć użycie globalnej blokady z tworzenia/importu/demo/topology/history. Operacje innego projektu mogą działać w czasie kolekcji.
- Kolejność: Repository trzyma project lock, a run_cycle próbuje globalny lock bez oczekiwania. Wszystkie advisory locki są nieblokujące i zwalniane w finally/close; żadna ścieżka nie czeka z globalnym lockiem na project lock. To zapobiega cyklicznemu oczekiwaniu.
- Testy: blokada globalna nie blokuje pracy offline B; druga kolekcja odrzucona; drugi Repository A odrzucony; wyjątek konstrukcji/migracji zwalnia project lock. Bez zmiany schematu SQLite.

## 3.1.4 — tworzenie i ochrona danych (R09)

- Wspólny moduł prywatnych plików. POSIX: katalogi 0700, nowe pliki tworzone od początku jako 0600 przez O_EXCL/O_NOFOLLOW; nie dopiero chmod po zapisie.
- Windows: chroniona DACL obejmująca aktualnego użytkownika, SYSTEM i administratorów; prywatne SECURITY_ATTRIBUTES przy CreateFileW/CreateDirectoryW. Plik nie może być najpierw zapisany z szerokimi prawami. Bez icacls /T na katalogach użytkownika, bez wymagania uprawnień administratora do zwykłych własnych plików.
- Objąć bazę, backup migracji, project.json i eksporty JSON/CSV/topologii. Istniejące własne katalogi/pliki projektu zabezpieczać przed otwarciem; nie modyfikować ACL dowolnego katalogu nadrzędnego wskazanego przy eksporcie. Odrzucać symlinki/reparse points w chronionych obiektach.
- Błąd ustawienia ochrony przerywa zapis; nie kontynuować po cichu. Nie przenosić sekretów z ENV do SQLite. Administrator/SYSTEM nie jest wykluczony z dostępu.
- Odbiór offline: tryb pliku już w trakcie zapisu, brak nadpisania/symlink follow, wywołania Windows backendu i propagacja błędu. Efektywną DACL trzeba sprawdzić na Windows z drugiego zwykłego konta; atrapa tego nie potwierdza.

## 3.1.5 — parsery i ograniczony odbiór (R06/R07)

- Rozszerzyć tylko krytyczne przypadki: Windows JSON z Unicode/BOM, pojedynczy rekord/lista/pusto, ucięcie i brak pól, nieprawidłowe metryki, wpis invalid/incomplete, macOS zakresy i zmiana interfejsu. Próbki syntetyczne oznaczyć jako syntetyczne — nie udawać zrzutów z rzeczywistego Windows PL/EN.
- Uruchomić istniejące 26 testów oraz mały zestaw regresji 3.1. Odbiór CLI na tymczasowych projektach i istniejącym snapshotcie LAN wyłącznie offline, bez nowych sond.
- Dokonać przeglądu diff/składni/odnośników. W razie zastąpienia zbędnych plików zachować je pod old/ i wpisać do docs/OLD.md. Zmiana istniejącego modułu nie wymaga kopiowania każdej jego wersji poza Git.
- Zakończyć raportem, z wersją, komendami, liczbą testów i uczciwą listą niewykonanych prób. Własny pakiet można zainstalować lokalnie offline; nie aktualizować bibliotek.

## Kryteria i kolejność

| Krok | Rezultat | Warunek przejścia |
|---|---|---|
| Plan/ADR | Zapisana zgoda i kontrakt bezpieczeństwa | Przed kodowaniem |
| Stan sieci i sondy | Mniej odczytów, powiązane źródło/interfejs | Test cache/TTL/zmiany oraz atrap Windows |
| Repository i CLI | Osobne blokady, jeden cykl globalnie | Test dwóch projektów i błędów/migracji |
| Ochrona plików | Prywatne tworzenie i aktualizacja własnych plików | Testy POSIX i kontraktu Windows |
| Regresja/dokumentacja | Raport techniczny | Bez nowych skanów, brak regresji |
| Odbiór Windows/switch | Faktycznie potwierdzone zachowanie | Dostępne środowisko, zakres i osobna zgoda operatora |

R03/R04 pozostają rozszerzeniami zakresu, R08 pozostaje warunkiem przyszłej dystrybucji. Wdrożenie 3.1 nie oznacza odebrania tych pozycji ani rozpoczęcia Etapu 4. Brak Windows/switcha nie blokuje wykonania bezpiecznych poprawek i testów offline.

## Wynik implementacji i uruchomienie

Zainstalowano **0.3.1** lokalnie, bez pobierania zależności. Wdrożono kroki kodowe 3.1.1–3.1.5 i mały zestaw regresji: 38 testów łącznie. Na macOS przechodzi odbiór offline; Windows IPv4/DACL pozostaje kodem zweryfikowanym na atrapach, z niewykonanym odbiorem na Windows. [Raport](../etap-3-1/RAPORT_ETAP_3_1.md).

Z katalogu głównego projektu:

```sh
./.venv/bin/mapper --version
./.venv/bin/mapper doctor
./.venv/bin/mapper demo
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m unittest discover -s tests/critical -v
```

`demo` tworzy dane syntetyczne bez sondowania. Jego ID można podać dotychczasowym `topology build`, `topology view`, `history` i `snapshot export`. Polecenia CLI oraz formaty danych nie zmieniły się. Opcjonalnie w `project.json` ustaw `limits.route_refresh_seconds` między 0,1 a 2; domyślnie 1,0 s. JSON wymaga kropki dziesiętnej, np. `"route_refresh_seconds": 1.0`.

`CYCLE_ALREADY_RUNNING` oznacza drugą kolekcję w tym samym katalogu danych; `PROJECT_BUSY` oznacza inne otwarte Repository tego samego projektu. Podgląd już uruchomiony nie trzyma Repository. CLI pracujące na tym samym projekcie może być zablokowane na czas kolekcji, natomiast praca offline w innym projekcie pozostaje dostępna. Przed używaniem nowej wersji zakończ stare procesy mappera, które nie znają project locka.

Nowe pliki eksportu powstają od początku jako prywatne, nadal bez nadpisywania istniejącego pliku. Na Windows system plików musi wspierać trwałe ACL. Brak takiej możliwości daje `FILE_PROTECTION_UNAVAILABLE`; nie ma obejścia zapisującego dane z niepotwierdzoną ochroną. `FILE_PROTECTION_FAILED` oznacza niepowodzenie ustawienia ochrony. Nie zmieniamy ACL katalogu nadrzędnego wybranego do eksportu. `WINDOWS_IPV4_API_UNAVAILABLE` nie uruchamia zastępczego PING.EXE.

Nie usunięto ani nie zastąpiono zbędnych samodzielnych plików: wcześniejsze prototypy nadal mają własną rolę. Nie tworzono kopii każdej edytowanej wersji modułów w old/; zmiany kodu są widoczne w Git. Sekrety i dane prywatne nie trafiły do repozytorium.
