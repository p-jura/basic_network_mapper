# Poradnik wykonania Etapu 0 i Etapu 1 aplikacji mapującej sieć

> Materiał historyczny: odrębny wariant Flutter/Dart. Nie określa bieżącego zakresu mappera Python. Aktualna dokumentacja: [spis treści](../../README.md).

Data: 11 października 2026 r.

Dokument uzupełnia [plan wdrożenia](PLAN_APLIKACJI_TOPOLOGII_MVP.md). Korzysta z numeracji jego harmonogramu: **Etap 0 = zamknięcie założeń**, **Etap 1 = sprawdzenie ryzyk technicznych**. Uwzględnia również decyzje architektoniczne potrzebne do tych prac.

Rezultatem ma być uzgodniony zakres i mały prototyp potwierdzający, że można uruchomić Flutter Desktop, odczytać dane przez SNMPv2c/v3 bez ujawnienia sekretów oraz pokazać i wyeksportować prostą mapę. Nie budujemy jeszcze pełnego kolektora, bazy, historii ani silnika topologii.

To instrukcja do wykonania. Polecenia i przykłady z tego dokumentu nie zostały uruchomione na Twoim komputerze. Fragmenty oznaczone jako kontrakt albo schemat implementacji wymagają napisania wskazanych plików; nie są informacją o istniejących już funkcjach aplikacji. W katalogu projektu utworzono na razie dokumentację.

## 1. Zasady pracy

- Jedna aplikacja Flutter Desktop i jedna niezależna paczka Dart dla SNMPv2c/v3.
- Jedna platforma systemowa i jedna architektura CPU w pierwszym wydaniu.
- Bez CI/CD i rozbudowanego frameworka testów.
- Sprawdzamy tylko ryzyka blokujące użycie: narzędzia, SNMP, sekrety, natywne zależności, mapa i eksport.
- Do prób używamy lokalnego agenta laboratoryjnego albo wskazanego urządzenia z istniejącym dostępem tylko do odczytu.
- Nie konfigurujemy urządzeń produkcyjnych i nie skanujemy podsieci.
- Własny protokół SNMP w czystym Darcie pozostaje po MVP. Przez pierwsze dwa dni sprawdzamy integrację Net-SNMP, nie piszemy USM od początku.
- Wynik każdego etapu przedstawiamy do zatwierdzenia przed przejściem dalej, zgodnie z ustalonym procesem pracy.

## 2. Etap 0 — zamknięcie założeń

### Krok 0.1. Wybierz pierwszy system operacyjny

Wybierz system na podstawie komputera operatora, a nie wyłącznie komputera dewelopera.

| Wariant | Kiedy wybrać | Co jest potrzebne |
|---|---|---|
| macOS | Operator korzysta z Maca | Mac, Xcode, Flutter; architektura arm64 lub x64 |
| Windows | Operatorzy korzystają głównie z laptopów Windows | Windows, Visual Studio z C++, Flutter; najczęściej x64 |
| Linux | Operator używa stacji linuksowej | Dystrybucja z narzędziami Flutter Desktop i kompilatorem C |

Wybór nie oznacza braku możliwości przeniesienia kodu później. Oznacza ograniczenie liczby kombinacji do sprawdzenia przed MVP. Build Windows wykonujesz na Windows, build macOS na macOS; samo dodanie katalogu platformy nie potwierdza zgodności.

**Wynik:** zapisany system, architektura i sposób dostarczenia aplikacji: lokalne archiwum/pakiet dla operatora albo podpisana dystrybucja. Nie zakładaj posiadania kont i certyfikatów do podpisywania.

### Krok 0.2. Uzgodnij zakres pierwszego wydania

Zapisz poniższy zakres jako propozycję do zatwierdzenia:

1. IPv4 oraz mapowanie L2/podstawowe L3.
2. Projekty niezależnych sieci, seedy i profile dostępowe.
3. Odczyty SNMPv2c/v3 przez Net-SNMP opakowane w paczkę Dart.
4. Standardowe IF-MIB, BRIDGE-MIB, Q-BRIDGE-MIB, ARP i opcjonalne LLDP.
5. Jeden adapter SSH: IOS XE albo platforma z dostępnym sprzętem i przykładami wyników.
6. Interaktywna mapa, szczegóły, filtry, prosta historia i eksport JSON/CSV/SVG/PNG.
7. Jawne wyniki częściowe i niepewne przypisania.
8. Tryb offline z tym samym silnikiem topologii.

Oddzielnie zapisz zakres późniejszy: własny protokół SNMP, pozostałe systemy operacyjne, kolejne adaptery SSH, pełne rozpoznawanie wariantów MLAG/EVPN, usługa działająca po zamknięciu aplikacji.

**Wynik:** krótka lista „MVP” i „po MVP”, bez dokładania nowych platform w trakcie pierwszej próby technicznej.

### Krok 0.3. Ustal środowisko do próby SNMP

Wybierz jedną drogę:

- **Istniejące laboratorium:** administrator podaje adres/port agenta, wersję SNMP i dane profilu. Dane dostępowe przekazuje poza dokumentacją i repozytorium.
- **Lokalny agent:** osobny Net-SNMP snmpd w kontrolowanej VM lub na komputerze laboratoryjnym. Konfigurację kont i community wykonuje administrator laboratorium. To konfiguracja fixture testowego, a nie funkcja aplikacji.

Potrzebne są dwa profile tylko do odczytu:

| Profil | Parametry jawne | Sekrety |
|---|---|---|
| v2c | Adres IPv4, port, timeout | Community |
| v3 authPriv | Adres, port, username, auth protocol, privacy protocol, context | Hasło uwierzytelniania i szyfrowania |

Pierwszą próbę v3 można wykonać jako SHA-1 + AES-128, jeżeli laboratorium ma taki profil. Jeśli docelowo wymagane jest SHA-256, uwzględnij je także w odbiorze Etapu 1. Udany odczyt SHA-1 nie potwierdza SHA-256, a etykieta „AES” wymaga ustalenia konkretnego wariantu.

Do pojedynczego GET wystarczy agent udostępniający sysDescr. Do pełnego odbioru kolektora w późniejszych etapach potrzebne będą switche z FDB/VLAN/LLDP i źródło ARP; agent na laptopie nie zastąpi takiej topologii.

Nie zapisuj rzeczywistych haseł w przykładach YAML/JSON, historii terminala ani zrzutach ekranu. Przykłady w poradniku używają adresu 127.0.0.1:1161, który działa tylko wtedy, gdy rzeczywiście uruchomiono tam agenta.

### Krok 0.4. Ustal ograniczenia odkrywania

Nie wymagaj od operatora policzenia wszystkich hostów i switchy. W zamian określ zachowanie przy osiągnięciu limitów:

- Seedy to punkty startowe, nie pełna inwentaryzacja.
- Rekurencja LLDP jest opcjonalna i ograniczona głębokością/liczbą urządzeń.
- Bez listy podsieci można proponować odczyt adresów zarządzania wskazanych przez LLDP, w uzgodnionych limitach. Nie rozszerzaj zakresu na wszystkie prywatne adresy IP.
- Nieudany odczyt oznacza brak danych źródła, nie zniknięcie hostów.
- Nierozpoznany VRF/LAG/stack/MLAG daje jawne ograniczenie, a nie sztuczną pewność mapy.
- Nie ma aktywnych ping sweepów, zmian VLAN ani komend konfiguracyjnych.

Na Etapie 1 odczytuj wyłącznie wskazany agent/urządzenie. Rekurencja jest zadaniem późniejszego kolektora.

### Krok 0.5. Zapisz kartę decyzji

Utwórz docelowo `network_mapper/docs/etap_0_decyzje.md`. Skopiuj poniższy szablon i uzupełnij go. Pola „do zatwierdzenia” nie są automatycznie zaakceptowane.

```markdown
# Karta decyzji — Etap 0

- Status: do zatwierdzenia
- System i wersja: ...
- Architektura CPU: ...
- Pierwsza dystrybucja: ...
- Interfejs: jedna aplikacja Flutter Desktop
- Backend SNMP w MVP: Net-SNMP przez osobną paczkę Dart
- Własny protokół SNMP: po MVP
- Pierwszy adapter SSH: ...
- Laboratorium dostępne: tak / nie
- Wymagane warianty SNMPv3: ...
- Zakres odczytów rzeczywistych: ...
- Budżet Etapu 1: maksymalnie 2 dni robocze
- Budżet MVP: około 20 dni pracy + 5 dni rezerwy
- Otwarte decyzje: ...
- Zatwierdzone przez / data: ...
```

**Etap 0 jest zakończony**, gdy wybór platformy, architektury, backendu SNMP, zakresu MVP i laboratorium jest rozstrzygnięty albo jawnie wskazano blokadę. Zgodnie z procesem przedstaw tę kartę do zatwierdzenia przed wykonywaniem Etapu 1. Samo napisanie poradnika nie jest akceptacją tych wyborów.

## 3. Etap 1 — plan dwóch dni

| Część | Orientacyjny budżet | Cel |
|---|---:|---|
| Narzędzia i uruchomienie Flutter | 1–2 h | Działająca aplikacja desktopowa |
| Minimalny most Net-SNMP | 3–4 h | Pojedynczy GET v2c/v3 przez stdin |
| Połączenie paczki Dart z mostem | 2–3 h | Bez sekretów w argv/pliku; kontrolowany timeout |
| Próba mapy i eksportu | 2–3 h | Pan/zoom, wybór węzła, SVG i PNG |
| Próba dystrybucji i zapis wyniku | 2–4 h | Lista zależności i decyzja o dalszej pracy |

Budżety obejmują mały prototyp, nie pełną bibliotekę. Jeśli instalacja środowiska lub natywne pakowanie pochłonie cały czas, zapisz wynik i przedstaw wybór dalszej drogi. Nie przedłużaj automatycznie etapu o własne SNMPv3.

### Krok 1.1. Sprawdź narzędzia

Zainstaluj Flutter stable według [oficjalnej instrukcji](https://docs.flutter.dev/install). Używaj Darta dostarczonego z Flutterem, żeby nie mieszać wersji SDK.

Uruchom w terminalu:

```text
flutter --version
dart --version
flutter doctor -v
flutter devices
```

Napraw tylko błędy potrzebne do wybranej platformy desktopowej. Dla tego projektu nie musisz instalować emulatorów Androida ani narzędzi przeglądarkowych.

**macOS:** potrzebne są Xcode, poprawnie wybrane narzędzia command-line i zaakceptowana licencja; wymagania dotyczące pluginów sprawdź w dokumentacji bieżącego Fluttera. Sprawdzenie wersji:

```bash
xcodebuild -version
xcode-select -p
clang --version
```

Jeżeli Flutter wskazuje niepoprawny Xcode, skorzystaj z [instrukcji konfiguracji macOS](https://docs.flutter.dev/platform-integration/macos/setup). Nie przełączaj wersji Xcode bez sprawdzenia, czy używają jej inne projekty.

**Windows:** potrzebne jest Visual Studio z workloadem „Desktop development with C++”; samo Visual Studio Code go nie zastępuje. Szczegóły: [konfiguracja Windows](https://docs.flutter.dev/platform-integration/windows/setup).

**Oczekiwany wynik:** `flutter devices` pokazuje wybraną platformę, a `flutter doctor -v` nie zgłasza blokady jej toolchainu.

### Krok 1.2. Utwórz minimalną strukturę

Wykonuj polecenia w nowym katalogu `network_mapper` wewnątrz istniejącego workspace. Nie nadpisuj wcześniejszych plików projektu.

Poniższy blok dotyczy macOS/Linux, po wybraniu platformy macOS:

```bash
mkdir network_mapper
cd network_mapper
mkdir -p packages docs scripts
flutter create --platforms=macos --project-name network_mapper app
dart create -t package packages/home_lan_snmp
```

Na Windows odpowiednikiem, w PowerShell, jest:

```powershell
New-Item -ItemType Directory -Path network_mapper
Set-Location network_mapper
New-Item -ItemType Directory -Path packages, docs, scripts
flutter create --platforms=windows --project-name network_mapper app
dart create -t package packages/home_lan_snmp
```

Jeśli katalog już istnieje, sprawdź jego zawartość i kontynuuj w nim. Nie dodawaj `--overwrite` ani `--force`, żeby ominąć konflikt.

W `app/pubspec.yaml` dodaj do istniejącej sekcji `dependencies`, bez tworzenia drugiej sekcji o tej samej nazwie:

```yaml
  home_lan_snmp:
    path: ../packages/home_lan_snmp
```

Następnie, z katalogu `app`:

```text
flutter pub get
flutter run -d macos
```

Na Windows użyj `flutter run -d windows`. Zamknij aplikację po sprawdzeniu okna.

Zachowaj lockfile aplikacji. Nie dodawaj jeszcze SQLite, magazynu sekretów, wielu adapterów i modułów historii — należą do kolejnych etapów.

Uzupełnij istniejące reguły ignorowania Gita o katalog `native/build/` paczki SNMP, lokalne pliki sekretów i prywatne raporty. Nie nadpisuj wygenerowanych `.gitignore`. Zanim później zapiszesz commit, przejrzyj jego zawartość; instrukcja nie wymaga tworzenia commita ani publikacji repozytorium w tym etapie.

Architektura próby pozostaje mała:

```text
Flutter: formularz i wynik      Flutter: syntetyczna mapa
          │                              │
          ▼                              ▼
paczka Dart home_lan_snmp             GraphScene
          │                         ↙          ↘
          ▼                    ekran       SVG / PNG
helper C przez stdin/stdout
          │
          ▼
biblioteka Net-SNMP → agent laboratoryjny
```

Mapa i odczyt są na tym etapie oddzielnymi próbami. Połączenie rzeczywistych obserwacji z mapą następuje po wdrożeniu kolektora i silnika topologii.

**Oczekiwany wynik:** aplikacja uruchamia się, a lokalna paczka Dart jest poprawnie rozwiązywana.

### Krok 1.3. Przygotuj Net-SNMP i sprawdź kompilator

Na macOS, jeśli używasz już Homebrew, zainstaluj bibliotekę deweloperską:

```bash
brew install net-snmp
```

Nie zakładaj, że systemowe `snmpget` ma tę samą wersję i zestaw algorytmów co instalacja Homebrew. Sprawdź właściwe ścieżki:

```bash
mapper_snmp_prefix="$(brew --prefix net-snmp)"
"$mapper_snmp_prefix/bin/net-snmp-config" --version
"$mapper_snmp_prefix/bin/net-snmp-config" --cflags
"$mapper_snmp_prefix/bin/net-snmp-config" --libs
"$mapper_snmp_prefix/bin/snmpget" --version
```

Na Debianie/Ubuntu wariantem laboratoryjnym jest:

```bash
sudo apt-get install build-essential libsnmp-dev snmp
net-snmp-config --version
```

To alternatywa dla wybranego Linuxa lub laboratoryjnej VM, nie dodatkowa docelowa platforma MVP. Instalacja bibliotek lokalnych nie zmienia konfiguracji switchy.

Na Windows wybierz i sprawdź konkretny build biblioteki Net-SNMP dla właściwej architektury, z obsługą wymaganej kryptografii, nagłówkami i bibliotekami do linkowania. Nie traktuj losowego starego instalatora zawierającego samo CLI jako gotowego SDK. Jeśli nie można uzyskać powtarzalnego buildu w budżecie etapu, jest to wynik do decyzji o zmianie platformy/backendu/terminu.

**Oczekiwany wynik:** znana wersja biblioteki, działający kompilator C i udokumentowane warianty SNMPv3 obsługiwane przez ten build.

### Krok 1.4. Napisz minimalny most natywny

Docelowy plik próby: `packages/home_lan_snmp/native/snmp_probe.c`. W Etapie 1 zaimplementuj tylko jeden GET dla numerycznego OID:

```text
1.3.6.1.2.1.1.1.0    sysDescr.0
```

Nie implementuj jeszcze ogólnego walk ani parsowania tablic. Najpierw udowodnij działanie v2c/v3 i bezpiecznego kanału danych.

#### Kontrakt wejścia i wyjścia

Most otrzymuje pojedynczy komunikat JSON zakończony nową linią przez stdin. Przyjmij maksymalnie 16 KiB wejścia. Do parsowania wykorzystaj małą istniejącą bibliotekę C, np. cJSON, zamiast pisać własny parser JSON. To zależność pomocnicza mostu; jej licencję i dystrybucję uwzględnij w wyniku próby. Jeśli wybierzesz inny format IPC, opisz go i zachowaj limity.

Przykład kontraktu v2c z syntetycznym znacznikiem sekretu — nie gotowy profil do uruchomienia:

```json
{
  "ipcVersion": 1,
  "operation": "get",
  "target": {"ipv4": "127.0.0.1", "port": 1161},
  "oid": "1.3.6.1.2.1.1.1.0",
  "timeoutMs": 2000,
  "retries": 1,
  "security": {"version": "2c", "community": "<W_PAMIECI>"}
}
```

Profil v3 zastępuje `security`:

```json
{
  "version": "3",
  "level": "authPriv",
  "username": "<UŻYTKOWNIK_LABORATORYJNY>",
  "authProtocol": "SHA-256",
  "authPassword": "<W_PAMIECI>",
  "privProtocol": "AES-128",
  "privPassword": "<W_PAMIECI>",
  "contextName": ""
}
```

Przykładowa odpowiedź, dla syntetycznej wartości `demo`:

```json
{"ipcVersion":1,"ok":true,"oid":"1.3.6.1.2.1.1.1.0","type":"octetString","hex":"64656d6f"}
```

Przykład błędu:

```json
{"ipcVersion":1,"ok":false,"error":{"code":"timeout"}}
```

Stdout zawiera wyłącznie wynik IPC. Stderr nie zawiera wejściowego JSON, sekretów ani pełnego profilu. W prototypie wystarczą stałe kody błędów; nie przekazuj bez kontroli całego tekstu błędu biblioteki.

#### Schemat implementacji C

To lista zadań programistycznych, nie kompletny kod źródłowy:

1. Wczytaj jeden komunikat z limitem. Odrzuć dodatkowe rekordy.
2. Sprawdź wersję IPC, `operation == get`, poprawny IPv4/port, numeryczny OID i zakresy timeoutu/retries.
3. W tej próbie dopuść wyłącznie OID sysDescr. Odrzuć `set` i każdy nieobsługiwany wariant, zamiast wybierać ustawienia domyślne.
4. Przed inicjalizacją Net-SNMP wyłącz odczytywanie globalnych i osobistych plików konfiguracji biblioteki. Sprawdź odpowiednią opcję API w użytej wersji, np. `NETSNMP_DS_LIB_DONT_READ_CONFIGS`.
5. Zainicjalizuj sesję przez `snmp_sess_init`; zbuduj endpoint `udp:<IPv4>:<port>` wyłącznie ze zwalidowanych pól.
6. Dla v2c ustaw wersję i community w pamięci.
7. Dla v3 ustaw USM, username, poziom bezpieczeństwa i OID-y algorytmów. Wyprowadź klucze przez API Net-SNMP, zgodnie z wybranym algorytmem; nie implementuj samodzielnie HMAC/AES ani lokalizacji kluczy.
8. Otwórz sesję. Użyj PDU `SNMP_MSG_GET`, dodaj numeryczny OID i wykonaj ograniczone czasowo zapytanie. Nie dodawaj ścieżki wywołującej `SNMP_MSG_SET`.
9. Sprawdź status transportu, errstat PDU, liczbę varbindów i typ odpowiedzi. Octet string koduj jako hex/base64; nie zakładaj UTF-8 ani końcowego bajtu NUL.
10. Zwróć ograniczony rozmiarem JSON, np. maksymalnie 64 KiB dla tego pojedynczego GET.
11. Zwolnij PDU, sesję i obiekty parsera przy sukcesie i błędzie. Usuń własne kopie sekretów z buforów, jeśli mechanizm platformy na to pozwala; nie obiecuj wyzerowania wszystkich kopii zarządzanych przez runtime/bibliotekę.

Za punkt odniesienia dla API służą [dokumentacja biblioteki Net-SNMP](https://www.net-snmp.org/dev/agent/group__library.html) i [tutorial pojedynczego odczytu](https://www.net-snmp.org/wiki/index.php/TUT:Simple_Application). Własny IPC i obsługa sekretów muszą zostać dodane; kopiowanie przykładu CLI z hasłem w argumentach nie realizuje wymagań.

#### Kompilacja próbna na macOS

Jeżeli wybrano cJSON z Homebrew:

```bash
brew install cjson
```

Z katalogu głównego `network_mapper`, dopiero po napisaniu `snmp_probe.c`:

```bash
mkdir -p packages/home_lan_snmp/native/build
mapper_snmp_prefix="$(brew --prefix net-snmp)"
mapper_json_prefix="$(brew --prefix cjson)"
clang -Wall -Wextra \
  $("$mapper_snmp_prefix/bin/net-snmp-config" --cflags) \
  -I"$mapper_json_prefix/include" \
  packages/home_lan_snmp/native/snmp_probe.c \
  -o packages/home_lan_snmp/native/build/snmp_probe \
  $("$mapper_snmp_prefix/bin/net-snmp-config" --libs) \
  -L"$mapper_json_prefix/lib" -lcjson
```

W kodzie użyj nagłówka zgodnego z tą instalacją, np. `<cjson/cJSON.h>`. Flagi kompilatora pochodzą z lokalnego zaufanego `net-snmp-config`; nigdy z wyniku odczytu urządzenia. Build jest lokalną próbą, jeszcze nie przenośną dystrybucją.

**Oczekiwany wynik:** program kompiluje się i odrzuca niepoprawny kontrakt. Nie wklejaj rzeczywistego JSON z hasłem do polecenia `echo`, argumentów terminala lub pliku.

### Krok 1.5. Połącz most z paczką Dart

Dodaj w paczce plik `lib/src/probe_transport.dart` oraz tymczasowy `example/probe.dart`. Program przykładowy pobiera adres, wersję i sekrety interaktywnie albo przez formularz Fluttera. Dla terminala wpisywanie sekretu musi mieć wyłączone echo i przywracać je w `finally`.

Poniższy fragment pokazuje sposób startu procesu. Nie jest kompletną implementacją transportu: przed odbiorem trzeba dodać limit strumieni wyjściowych, sprawdzenie kodu zakończenia, walidację odpowiedzi oraz sprzątanie po timeoutach.

```dart
final child = await Process.start(
  absoluteBridgePath,
  const [],
  runInShell: false,
);

// request powstaje w pamięci; nie loguj go.
child.stdin.writeln(jsonEncode(request));
await child.stdin.close();

// Odczyt stdout i stderr uruchom współbieżnie, zanim zaczniesz
// czekać na exitCode. Oba strumienie muszą mieć ograniczenie rozmiaru.
```

Uzupełnij działanie:

1. Sprawdź, że helper pochodzi ze znanej ścieżki aplikacji, nie z niekontrolowanego PATH lub bieżącego katalogu.
2. Zaszyfruj trwałe przechowywanie dopiero przez systemowy magazyn sekretów w dalszym etapie; na potrzeby próby sekrety istnieją wyłącznie w pamięci formularza/procesu.
3. Wczytaj stdout/stderr równolegle z limitem. W tej próbie wystarczy 64 KiB stdout i mały limit stderr.
4. Ustaw limit całej operacji, np. 8 sekund, obejmujący discovery SNMPv3, nie tylko pojedynczy pakiet.
5. Przy timeout/anulowaniu zakończ proces, odczekaj krótko na jego koniec i upewnij się, że nie pozostał helper. Samo `Future.timeout` nie zatrzymuje procesu.
6. Zwaliduj `ipcVersion`, `ok`, OID, typ i zawartość wyniku. Nie zapisuj surowego żądania przy błędzie parsowania.
7. Zwróć mały wynik Dart, niezależny od Fluttera. W Etapie 1 nie potrzebujesz pełnego API sesji/walk z planu MVP.

Program `example/probe.dart` powinien przyjmować jako argument wyłącznie ścieżkę helpera. Po jego napisaniu, z katalogu paczki:

```text
dart run example/probe.dart native/build/snmp_probe
```

Adres i profil wpisuj w interaktywnych polach. Nie zapisuj sekretów w plikach `.env` na potrzeby demonstracji ani w parametrze `--password`.

W trakcie działania sprawdź argumenty procesu. Na macOS/Linux:

```bash
ps -axo pid,args
```

Na Windows, w PowerShell:

```powershell
Get-CimInstance Win32_Process |
  Where-Object Name -Like '*snmp_probe*' |
  Select-Object ProcessId, CommandLine
```

Sprawdzaj lokalnie. Nie wklejaj całej listy procesów do raportu; wystarczy informacja, że argv helpera nie zawierało sekretów. Ta kontrola nie zastępuje sprawdzenia logów i plików.

### Krok 1.6. Wykonaj minimalne próby SNMP

| Próba | Jak wykonać | Poprawny wynik |
|---|---|---|
| v2c | Wprowadź istniejący profil RO i pobierz sysDescr | Wynik octet string z właściwego agenta |
| v3 authPriv | Użyj uzgodnionego algorytmu i profilu | Poprawny wynik bez plików z sekretami |
| Błędny sekret | Zmień hasło/community w pamięci formularza | Ograniczony czasowo błąd, bez fallbacku do słabszego profilu |
| Nieosiągalny cel | Użyj wskazanego celu laboratoryjnego bez działającego agenta | Timeout i zamknięcie helpera |
| Niedozwolona operacja | W lokalnej próbie IPC podaj `set` z syntetycznymi danymi | Odrzucenie przed wysłaniem pakietu |
| Anulowanie | Przerwij oczekujące zapytanie | UI działa, proces pomocniczy nie pozostaje aktywny |

Nie wymagaj, aby błędna community i brak agenta dawały odmienne komunikaty: w pewnych przypadkach oba kończą się timeoutem. Nie identyfikuj przyczyny z pewnością, której nie daje odpowiedź agenta.

Próby wykonujemy ręcznie, bez platformy testowej. Zapisz wersję biblioteki, system, algorytmy, status i czas; nie zapisuj sekretów. Snapshot offline nie potwierdza działania transportu v3.

### Krok 1.7. Przygotuj próbę mapy

Do `app` dodaj tylko bibliotekę potrzebną do krótkiej próby układu, jeżeli chcesz sprawdzić graphview:

```text
flutter pub add graphview
```

Użyj małego grafu syntetycznego: S1 — S2 — H1 oraz S1 — H2. Link S1–S2 ma etykiety portów, hosty należą do dwóch VLAN-ów. Węzły nie pochodzą jeszcze z silnika topologii.

Kolejność implementacji:

1. Zdefiniuj mały `GraphScene`: ID i pozycja węzła, rozmiar prostokąta, etykieta; link z ID końców, portami i kolorem.
2. Najpierw narysuj scenę w stałych współrzędnych przez `CustomPainter`. Owiń w `InteractiveViewer`, ustaw granice skalowania i sprawdź pan/zoom.
3. Dodaj kliknięcie. Punkt zdarzenia przelicz do współrzędnych sceny, np. przez `TransformationController.toScene`; dopiero potem wykonaj hit-test. Sprawdź wybór po przybliżeniu i przesunięciu.
4. Dopiero teraz sprawdź jeden algorytm graphview. Pozycje przenieś do GraphScene, zamiast uzależniać cały model aplikacji od klas biblioteki.
5. Jeśli biblioteka nie daje łatwego dostępu do pozycji w budżecie około godziny, zachowaj proste rozmieszczenie warstwowe. Zapisz tę decyzję; nie twórz kolejnego edytora grafów.
6. Dodaj drugą scenę z cyklem S1–S2–S3–S1. Rysunek ma zachować wszystkie krawędzie, nawet jeśli bazowy układ wykorzystuje drzewo.

Przykładowa scena do przepisania na obiekty Dart:

```json
{
  "width": 900,
  "height": 600,
  "nodes": [
    {"id":"S1","x":100,"y":100,"label":"Switch 1"},
    {"id":"S2","x":450,"y":100,"label":"Switch 2"},
    {"id":"H1","x":450,"y":350,"label":"Host A / VLAN 10"},
    {"id":"H2","x":100,"y":350,"label":"Host B / VLAN 20"}
  ],
  "edges": [
    {"a":"S1","b":"S2","label":"Gi1/0/24 ↔ Gi1/0/24"},
    {"a":"S2","b":"H1","label":"Gi1/0/1"},
    {"a":"S1","b":"H2","label":"Gi1/0/2"}
  ]
}
```

W prototypie pomiń ikony producentów, animacje, przeciąganie węzłów, filtry i bazę. Sprawdzasz mechanizm mapy, a nie końcowy wygląd produktu.

### Krok 1.8. Sprawdź SVG i PNG

**SVG:** zbuduj tekst XML z GraphScene: `svg` z viewBox, linie, prostokąty i etykiety. Użyj wspólnych wymiarów sceny. Escapuj co najmniej `&`, `<`, `>`, a w atrybutach również cudzysłowy. Otwórz wynik w przeglądarce. Dodaj syntetyczną etykietę `Switch <A> & B`, żeby sprawdzić escapowanie.

**PNG:** wywołaj ten sam renderer sceny na `Canvas` związanym z `PictureRecorder`, następnie `toImage` i `toByteData(format: ImageByteFormat.png)`. Ustal rozsądny rozmiar, np. 1800×1200 pikseli dla sceny 900×600. Użyj skali na canvasie, narysuj tło, zwolnij obraz/picture po eksporcie. Nie eksportuj bez limitu rozmiaru wielkiej sceny.

W Etapie 1 zapisuj do wybranego katalogu prób, np. systemowego katalogu tymczasowego pokazanego operatorowi. Nie zakładaj, że aplikacja sandboxowana może dowolnie pisać do Documents. Systemowe okno wyboru pliku to zadanie późniejszego interfejsu.

**Oczekiwany wynik:** oba formaty pokazują wszystkie cztery węzły, linki i etykiety; PNG nie jest jedynie zrzutem aktualnie przybliżonego fragmentu mapy.

### Krok 1.9. Sprawdź build i zależności natywne

Z katalogu `app`, dla wybranej platformy:

```text
flutter analyze
flutter build macos --release
```

Na Windows zamiast ostatniego polecenia:

```text
flutter build windows --release
```

Build Fluttera sam nie dołącza automatycznie Twojego helpera. Dodaj jego kopiowanie do paczki aplikacji lub przygotuj tymczasowy katalog dystrybucyjny zawierający aplikację, helper i potrzebne biblioteki. Ścieżkę helpera wyznaczaj względem instalacji aplikacji, nie katalogu źródeł.

Na macOS/Linux z katalogu głównego sprawdź zależności helpera odpowiednim narzędziem:

```bash
otool -L packages/home_lan_snmp/native/build/snmp_probe
```

Na Linux zamiast `otool -L` użyj `ldd` wyłącznie na własnym zaufanym helperze. Na Windows użyj narzędzia `dumpbin /DEPENDENTS` z narzędzi Visual Studio, dla właściwego pliku EXE.

Zapisz zależności Net-SNMP, kryptografii i parsera JSON. Ścieżka do Homebrew na komputerze dewelopera jest sygnałem zależności środowiskowej; nie dowodzi przenośności aplikacji.

Na macOS sprawdź dodatkowo sandbox/entitlements dla wychodzących połączeń oraz uruchamiania helpera, podpisanie komponentów i ich dziedziczenie uprawnień. Nie wyłączaj sandboxu bez opisania wpływu na sposób dystrybucji. Wersja debug działająca z terminala nie potwierdza działania gotowego pakietu.

Przenieś próbę na czysty komputer lub VM **tego samego systemu i architektury**. Sprawdź uruchomienie, odczyt laboratoryjny i mapę bez Flutter SDK oraz bez bibliotek pozostawionych przypadkiem przez środowisko deweloperskie. Drugi użytkownik na tym samym komputerze nie usuwa globalnie zainstalowanego Homebrew i nie jest równoważny czystej maszynie.

Jeżeli nie masz takiego środowiska, oznacz pakowanie jako **niezweryfikowane**, zamiast wpisywać sukces. Przed zatwierdzeniem odbioru uzgodnij, czy MVP może wymagać jawnej instalacji zależności systemowych.

## 4. Minimalna lista sprawdzeń Etapu 1

To lista ręcznego odbioru, nie nowa warstwa testująca:

- [ ] Flutter uruchamia aplikację na zatwierdzonym OS/CPU.
- [ ] Paczka SNMP jest niezależna od Fluttera.
- [ ] GET v2c działa na kontrolowanym agencie.
- [ ] GET v3 authPriv działa dla każdego wariantu wymaganego w pierwszym wydaniu.
- [ ] Sekrety nie pojawiają się w argv, logach, plikach ani repozytorium.
- [ ] Brak dostępu, timeout i anulowanie nie blokują UI i nie zostawiają helpera.
- [ ] Próba operacji `set` zostaje odrzucona przed wysłaniem.
- [ ] Mapa obsługuje zoom, przesuwanie, wybór węzła i cykl w grafie.
- [ ] SVG i PNG zawierają całą scenę próbną.
- [ ] Znane są zależności natywne oraz status próby na czystej maszynie.

Jeśli trzeba coś zautomatyzować już teraz, wystarczą trzy małe przypadki: odrzucenie operacji zapisu, timeout/posprzątanie procesu i błędna odpowiedź IPC. Nie buduj zestawu testów całego UI ani własnej walidacji kryptografii biblioteki Net-SNMP.

## 5. Zapis wyniku i decyzja o dalszej pracy

Utwórz docelowo `network_mapper/docs/etap_1_wynik.md`:

```markdown
# Wynik Etapu 1

- Data: ...
- Platforma / CPU: ...
- Flutter / Dart: ...
- Net-SNMP / komponenty kryptografii: ...
- Agent laboratoryjny i zakres: ... (bez sekretów)
- v2c: działa / nie działa / niezweryfikowane
- v3 — sprawdzone algorytmy: ...
- Kanał sekretów i kontrola wycieku: ...
- Timeout i anulowanie: ...
- Mapa / SVG / PNG: ...
- Zależności natywne: ...
- Czysta maszyna: sprawdzona / niezweryfikowana
- Zużyty czas: ...
- Blokady: ...
- Rekomendacja: kontynuacja / zmiana założenia / dodatkowa próba
- Zmiana estymacji MVP: ...
- Decyzja właściciela projektu / data: ...
```

### Gdy wszystko działa

Przedstaw raport, zrzut mapy, przykładowe SVG/PNG i listę sprawdzonych wariantów SNMP. Po zatwierdzeniu przejdź do Etapu 2: właściwe modele, lokalna baza, magazyn sekretów i snapshoty.

### Gdy działa aplikacja, ale nie pakowanie Net-SNMP

Przedstaw konkretne warianty z kosztem: instalacja zależności systemowej u operatora, zmiana pierwszej platformy albo dodatkowy czas na dystrybucję. Nie przedstawiaj aplikacji wymagającej Homebrew jako samodzielnej paczki.

### Gdy nie działa SNMPv3

Oddziel błąd profilu/uprawnień, brak algorytmu w buildzie, niedostępność agenta i błąd mostu. Zapisz dowody bez sekretów. Ograniczenie MVP do v2c/SSH wymaga jawnej zmiany zakresu; nie przechodź do niego automatycznie.

### Gdy nie ma laboratorium

Możesz przygotować mapę i kontrakt paczki, ale status rzeczywistego transportu pozostaje niezweryfikowany. Dane offline nie uprawniają do deklaracji, że SNMPv3 działa.

## 6. Źródła i granice weryfikacji

Dokumentację sprawdzono 11 października 2026 r. Dokładne wersje zależności i polecenia kompilowania trzeba potwierdzić w wybranym środowisku. Poradnik nie zawiera pełnego kodu helpera i nie potwierdza jego kompilacji.

- [Flutter — instalacja](https://docs.flutter.dev/install)
- [Flutter — macOS](https://docs.flutter.dev/platform-integration/macos/setup)
- [Flutter — Windows](https://docs.flutter.dev/platform-integration/windows/setup)
- [Net-SNMP — biblioteka](https://www.net-snmp.org/dev/agent/group__library.html)
- [Net-SNMP — pojedynczy GET](https://www.net-snmp.org/wiki/index.php/TUT:Simple_Application)
- [Net-SNMP — opcje klienta i sekrety w argumentach](https://www.net-snmp.org/docs/man/snmpcmd.html)
- [Homebrew — Net-SNMP](https://formulae.brew.sh/formula/net-snmp)
- [Homebrew — cJSON](https://formulae.brew.sh/formula/cjson)
- [Flutter graphview](https://pub.dev/packages/graphview)
- [Flutter — przeliczanie współrzędnych mapy](https://api.flutter.dev/flutter/widgets/TransformationController/toScene.html)
- [Flutter — renderowanie obrazu z Picture](https://api.flutter.dev/flutter/dart-ui/Picture/toImage.html)
- [SNMPv3 USM — RFC 3414](https://www.rfc-editor.org/rfc/rfc3414.html)
- [AES w SNMP — RFC 3826](https://www.rfc-editor.org/rfc/rfc3826.html)
- [SHA-2 w SNMP — RFC 7860](https://www.rfc-editor.org/rfc/rfc7860.html)
