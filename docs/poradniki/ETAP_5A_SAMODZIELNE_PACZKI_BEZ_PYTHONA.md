# Etap 5A — samodzielne paczki bez instalowania Pythona

Data: **1 listopada 2026 r.** Status: **zatwierdzony do wdrożenia 1 listopada 2026 r.**. Polecenie użytkownika: „ok utworz plan dzialania”. Następnie użytkownik polecił „ok implementuj plan”; autoryzuje to wdrożenie A0–A7, bez nowych skanów i publikacji. Historyczne rc1 zostaje zachowane.

Podstawa: [ADR-007 — dotychczasowe pakowanie](../decisions/ADR-007-pakowanie-i-odbior-wydania.md), [propozycja ADR-009](../decisions/ADR-009-samodzielne-paczki-z-interpreterem.md), [raport 0.5.0rc1](../etap-5/RAPORT_ETAP_5.md), [otwarte odbiory Etapu 5](../etap-5/KARTA_ODBIORU_ETAP_5.md). Wyniki zapisujemy w [karcie 5A](../etap-5a/KARTA_ODBIORU_ETAP_5A.md) i [raporcie wdrożenia](../etap-5a/RAPORT_ETAP_5A.md). Pakowanie macOS wdrożono; Windows i pełny odbiór pozostają otwarte.

## 1. Rezultat dla użytkownika

Użytkownik pobiera ZIP odpowiedni dla systemu, rozpakowuje go w lokalnym katalogu i uruchamia mapper. Interpreter i biblioteki są dołączone. Na komputerze odbiorcy nie instaluje się Python/pip/venv, nie pobiera bibliotek ani nie aktywuje środowiska. Domyślny start otwiera przeglądarkę na gotowym lokalnym panelu; kolekcja nadal wymaga jawnej akcji operatora.

Docelowe warianty tej samej aplikacji:

| System | Proponowany start | Budowanie i odbiór |
|---|---|---|
| Windows x64 | Dwuklik Mapper.exe, konsola procesu pozostaje dostępna | Build na Windows x64; osobne próby Windows 10 22H2 i Windows 11 |
| macOS ARM64 | Dwuklik Uruchom Mapper.command uruchamiający dołączony program | Build na macOS ARM64; sprawdzenie zwykłego rozpakowania ZIP/Finder |

Pierwsza wersja zachowuje konsolę: pokazuje URL, komunikaty startu i pozwala zatrzymać własny proces przez Ctrl+C. Błędy przy dwukliku muszą pozostać czytelne. Zamknięcie karty przeglądarki nie zatrzymuje serwera. Graficzny instalator, tray i dodatkowe okno ustawień nie są potrzebne do tego celu.

Nowe nazwy archiwów zawierają **standalone** i nowy numer kandydata ustalony przy wdrożeniu, np. `mapper-sieci-<wersja>-windows-x64-standalone.zip`. Dzisiejsze 0.5.0rc1 nadal wymaga Python 3.13; nie przemianowujemy go na samodzielne wydanie. Dane projektów pozostają w dotychczasowym prywatnym katalogu użytkownika, poza aplikacją.

## 2. Sposób pakowania — propozycja

**Rekomendacja: PyInstaller, tryb onedir, z zachowaniem oddzielnych wymienialnych bibliotek objętych takim wymaganiem.** Narzędzie zbiera interpreter i zależności do katalogu; wynik buduje się osobno na docelowych OS/architekturach. To mechanizm pozwalający uruchamiać program bez instalowania Pythona. [Dokumentacja trybu i platform](https://pyinstaller.org/en/stable/operating-mode.html).

Wstępny układ, nie istniejące jeszcze pliki:

```text
mapper-sieci-<wersja>-<platforma>-standalone/
  Mapper.exe / Mapper             # uruchamia lokalny panel
  Uruchom Mapper.command          # tylko macOS, bez systemowego python
  _internal/                      # interpreter, wymagane moduły i zasoby
  START_TUTAJ.md
  LICENSE
  licenses/                       # teksty/noty wszystkich dołączonych części
  sources/                        # wymagane źródła odpowiadające artefaktowi
  examples/                       # wyłącznie dane syntetyczne
  manifest.json
  SHA256SUMS
```

Dokładne rozmieszczenie bibliotek ustali krótki prototyp. Sam onedir nie dowodzi ich wymienialności: moduł może trafić do wewnętrznego archiwum PYZ. Próba ma wykazać, że właściwy kod Paramiko, scp i autocommand jest ładowany z wymienialnych plików; pomocne mogą być ustawienia hooków `module_collection_mode`. [Hooki PyInstaller](https://pyinstaller.org/en/stable/hooks.html).

Nie przyjmujemy tej własności na podstawie nazwy formatu. Jeśli prototyp nie przejdzie wymiany bibliotek i odczytu zasobów w ograniczonym czasie, zapisujemy wynik i przedstawiamy korektę sposobu dołączenia interpretera. Nie przebudowujemy w tym celu SNMP, SSH ani całego panelu.

PyInstaller będzie wyłącznie zależnością **budowania**. Dokładny numer i zależności narzędzia przypinamy po sprawdzeniu zgodności z Python 3.13; dokumentacja dostępna podczas planowania opisuje 6.22.3, nie oznacza to wykonanej instalacji ani przyjęcia tej wersji. Obecne wersje bibliotek aplikacji zachowujemy, o ile prototyp nie wykaże konkretnej konieczności zmiany. Własna MIT pozostaje; warunki narzędzia i wszystkich dołączonych części sprawdzamy względem artefaktu. [Licencja narzędzia](https://pyinstaller.org/en/stable/license.html).

## 3. Rzeczy wymagające dostosowania w obecnym kodzie

| Miejsce | Obecne zachowanie | Planowana zmiana i sprawdzenie |
|---|---|---|
| `packaging/bundle.py` | Tworzy venv, wywołuje pip i interpreter przez -I/-m | Samodzielny start omija instalowanie środowiska; obecny wariant deweloperski pozostaje dostępny |
| Start i maintenance | Wywołują plik Python lub `python -m mapper` | Jedno wejście programu wykonywalnego: panel, doctor, receipt, backup i verify; bez traktowania frozen sys.executable jako zwykłego python |
| `src/mapper/app.py` | Ładuje CSS według __file__ i uruchamia przeglądarkę po bind | Zachować rozdział zasobów tylko do odczytu i danych użytkownika; potwierdzić poprawne ścieżki w paczce |
| `src/mapper/storage` | Czyta pliki migracji SQL | Jawnie dołączyć oba SQL i sprawdzić nowy projekt oraz istniejącą kopię SQLite |
| Dash/dash-cytoscape | Lokalne JS/CSS i renderer SVG | Zebrać wymagane dane pakietów i metadane; sprawdzić wszystkie URL oraz PNG/SVG po rozpakowaniu |
| Netmiko/ntc-templates/PySNMP | Parsery, transporty i część importów dynamicznych | Jawny wykaz potrzebnych modułów, szablonów i dołączonych danych; smoke test offline nie może wymagać pip |
| doctor i receipt | Korzystają z importlib.metadata | Dołączyć potrzebne dist-info i odróżnić interpreter dołączony od systemowego; nie raportować braku działającej biblioteki z powodu pominiętych metadanych |
| `src/mapper/discovery/system.py` | Uruchamia narzędzia OS z odziedziczonym środowiskiem | Sprawdzić wpływ frozen loadera na ping/ARP/trasy/PowerShell i otwieranie przeglądarki; zachować argv, timeouty, anulowanie i właściwe źródło |
| Manifest i ZIP | Weryfikator odrzuca linki, zwykły writer ZIP zapisuje pliki | Nowy profil artefaktu opisuje także dozwolone wewnętrzne symlinki macOS i zachowuje je przy archiwizacji; nie zmienia ochrony linków w danych projektów |

PyInstaller ustawia ścieżki modułów w paczce; zasoby można wiązać z `__file__`. To wymaga faktycznego dołączenia plików, a nie tylko poprawienia ścieżki. [Ścieżki runtime](https://pyinstaller.org/en/stable/runtime-information.html).

Proponowany kontrakt wejścia, do wdrożenia dopiero po zatwierdzeniu:

```text
Mapper.exe                                # domyślnie panel
Mapper.exe panel --offline --port 8051
Mapper.exe doctor
Mapper.exe maintenance receipt --data-dir <nowy-katalog-testowy>
Mapper.exe maintenance backup --data-dir <projekty> --project <UUID> --output <nowa-kopia>
Mapper.exe verify
```

Na macOS te same podkomendy obsługuje dołączony `Mapper`. Wrapper .command jedynie wywołuje go względnie do swojego położenia. Żaden z nich nie szuka systemowego Python, nie modyfikuje PATH i nie dopisuje sekretów do argumentów. Świadome uruchomienie profili ENV z konsoli pozostaje dostępne; start z Findera nie musi odziedziczyć środowiska terminala. Brak ENV pokazujemy bez odczytów i bez ujawnienia wartości.

## 4. Kolejność wdrożenia i warunki przejścia

| Krok | Prace | Konkretny wynik / warunek |
|---|---|---|
| A0 — decyzja i baza | Zatwierdzenie planu i ADR-009; zapis wersji/commita/dirty state; dopasowanie zasad runtime w AGENTS po zatwierdzeniu | Oddzielne środowisko budowania, zachowane rc1 i dane, wersje narzędzi z hashami i notami |
| A1 — krótki prototyp macOS | Jedno wejście, onedir, SQL/CSS/JS/metadane; brak instalatora Python po stronie użytkownika | Start panelu offline oraz doctor/receipt z dołączonego interpretera |
| A2 — sprawdzenie wykonalności | Wymiana właściwych bibliotek LGPL; uruchomienie z innego katalogu; weryfikacja symlinków i środowiska procesów OS | Kontynuujemy po dowodzie; budżet tej próby około pół dnia, potem jawna korekta planu przy istotnej przeszkodzie |
| A3 — zebranie całej aplikacji | Hooki i zasoby parserów/SNMP/SSH, DLL/rozszerzenia natywne, backup, obsługa startu/błędu/Ctrl+C | Mały przekrój offline, zgodność źródeł i historii, bez nowych funkcji domenowych |
| A4 — natywny build Windows | Czyste środowisko Windows x64, te same runtime pins, własny build executable i inwentarz DLL | Działający Windows kandydat; build macOS nie zastępuje tego kroku |
| A5 — artefakty i materiały | Manifest, bezpieczna archiwizacja, noty/źródła interpretera i dołączonych części, instrukcje, sumy | Nowe ZIP-y o odrębnych nazwach, bez prywatnych danych; macOS rozpakowuje się z zachowaniem linków/uprawnień |
| A6 — odbiór bez Pythona | Czyste stanowiska Windows/macOS, brak Internetu, panel/CLI/eksporty, przeniesienie przed startem, kopia/rollback | Osobny receipt i status dla każdego stanowiska, bez kopiowania historycznych OK |
| A7 — przekazanie | Raport, macierz rzeczywistego wsparcia, aktualizacja kart i instrukcji | Wynik do akceptacji użytkownika; pełny Etap 5 zależy też od nadal otwartych odbiorów |

Developer nadal używa Pythona do budowania. Odbiorca dostaje dołączony runtime. Jeśli operator przygotowuje Windows samodzielnie, otrzymuje jeden skrypt budowania z przypiętymi narzędziami i instrukcją; nie prosimy go o ręczne odtwarzanie wielu zależności. Budowanie na Windows wymaga dostępu do tego stanowiska; w obecnym czacie dostęp wykonawczy do niego nie został potwierdzony.

## 5. Bezpieczne pakowanie i uruchamianie

### Linki i ścieżki

PyInstaller na macOS używa symlinków; archiwum i rozpakowanie muszą je zachować. [Wymagania formatu](https://pyinstaller.org/en/stable/common-issues-and-pitfalls.html#requirements-imposed-by-symbolic-links-in-frozen-application).

Proponowany manifest samodzielnego artefaktu v2 rozróżnia pliki regularne i linki z jawnym celem. Linki mogą wskazywać wyłącznie do wnętrza katalogu paczki; pętle, cele poza nim, nieoczekiwane linki i ścieżki z przejściem do rodzica są odrzucane. Nie osłabiamy `private_files.reject_link` ani ochrony config/SQLite/eksportów. Istniejące manifesty rc1 v1 i archiwa pozostają historyczne. Na Windows reparse points/junctions nie są domyślnie dozwolone przez ten wyjątek.

Program nie zapisuje danych projektu ani trwałych logów do `_internal`, folderu programu lub katalogu bieżącego. Działa ze zwykłego konta; updater nie jest dodawany. Importy muszą pochodzić z kontrolowanej paczki, a nie z przypadkowego pliku w CWD/PYTHONPATH. Sprawdzenie bezpieczeństwa nie może jednocześnie uniemożliwić świadomej, zgodnej wymiany bibliotek objętych takim wymaganiem.

### Narzędzia systemowe i przeglądarka

Środowisko loadera może wpływać na uruchamiane narzędzia OS. [Zalecenia PyInstaller](https://pyinstaller.org/en/stable/common-issues-and-pitfalls.html#launching-external-programs-from-the-frozen-application). Oczyszczenie obejmuje wyłącznie konieczne ścieżki runtime; nie usuwa profili ENV ani nie loguje ich wartości. Zmiany ścieżki DLL na Windows mają zakres procesu: trzeba zaprojektować je bez wyścigu z importami i kolektorami w puli. Zakres sieci, limity i walidacja trasy pozostają takie same.

Do paczki nie kopiujemy systemowego ping/ARP/PowerShell ani systemowych DLL Windows. Potwierdzamy ich znalezienie i poprawny start. Nowy packaging nie uprawnia do aktywnego ICMP: podczas implementacji korzystamy z atrap; ewentualny późniejszy odbiór fizycznego źródła wymaga osobnego zakresu.

### Podpis i dystrybucja

Wewnętrzny macOS build korzysta z podpisania ad hoc zapewnianego przez wybrany proces budowania; Windows kandydat może być bez Authenticode. Nie jest to obietnica uruchomienia bez ostrzeżeń po pobraniu z innego komputera. [Podpisywanie macOS w narzędziu](https://pyinstaller.org/en/stable/feature-notes.html#macos-binary-code-signing).

Nie zakładamy posiadania certyfikatów, kont płatnych ani zgody na zakup. Developer ID/notaryzacja i Authenticode do szerszej dystrybucji wymagają ustalenia dostępnych poświadczeń i zakresu. Nie wyłączamy globalnie Gatekeeper/SmartScreen/AV, nie usuwamy automatycznie kwarantanny i nie deklarujemy gotowości publicznej na podstawie lokalnego builda. Odbiór obejmuje także rzeczywistą kopię ZIP między komputerami i zwykłe rozpakowanie; ewentualną decyzję OS wykonuje operator.

## 6. Krótki odbiór nowej paczki

Najważniejszy warunek: **odbiorca uruchamia aplikację na wspieranym OS bez zainstalowanego Python 3.13 i bez używania pip/venv**. Samo usunięcie `python` z PATH, ukrycie komendy albo inne konto na Macu z globalnym Python.framework nie dowodzi tego warunku. Potrzebne jest czyste stanowisko lub przygotowana przez operatora VM. Nie odinstalowujemy narzędzi użytkownika do próby.

1. Zapisz OS/architekturę, brak wymaganego runtime, przeglądarkę, źródło i hash ZIP. Operator przygotowuje fizyczny brak Internetu/cache; nie zmieniamy samodzielnie ustawień sieci.
2. Dwuklik z Findera/Explorera otwiera właściwy URL i nie wykonuje sond. Brak przeglądarki daje czytelny URL/błąd startu, bez tracebacków i danych poufnych.
3. `doctor` i `maintenance receipt` działają z dołączonego runtime. Tworzą nowy projekt syntetyczny, SQLite i pięć eksportów danych. Nie uruchamiają zewnętrznego python/pip.
4. Panel: demo/import, szczegóły, historia, tekst/VLAN, PNG i SVG. Zasoby lokalne; eksporty obrazów rzeczywiście otwarte i etykiety sprawdzone. Problemy narzędzia automatyzacji zapisujemy oddzielnie od błędów produktu.
5. Przenieś całą **jeszcze nieuruchamianą** paczkę do innej ścieżki ze spacjami i polskimi znakami; uruchom z obcego CWD. Sprawdź także ponowne uruchomienie po przeniesieniu całej paczki. Dane użytkownika i backupy mają pozostać w ustalonym katalogu.
6. Zajęty port: druga instancja odmawia bez zatrzymania pierwszej i bez otwarcia jej strony. Zakończenie Ctrl+C zwalnia własny port, uchwyty i blokady. Przy anulowaniu testowego zadania dane mają zachować częściowy status.
7. Tymczasowa kopia starych danych: backup, odczyt/nowy build, powrót do poprzedniego środowiska na zgodnej kopii. Nie nadpisujemy aktualnej bazy starszym programem.
8. Brak/uszkodzenie zasobu lub biblioteki daje czytelny błąd. Osobno: kontrolowana wymiana zgodnej biblioteki LGPL ma działać, z potwierdzeniem faktycznego miejsca importu; oryginał testowej kopii przywracamy.
9. Na Windows sprawdź DLL/ctypes i prywatne pliki. Pełny odbiór NTFS z drugiego konta i natywnego źródła IPv4 pozostaje wymaganiem Etapu 5. Bez prawdziwego odczytu nie oznaczamy jako zaliczonego SNMP/SSH ani portów fizycznych.
10. Jedna próba D14 z faktycznej paczki, ponieważ loader/importy się zmieniają: import/korelacja ≤30 s, infrastruktura ≤5 s, osobno pomiar łącznego RAM ≤1,5 GB. Wielkość ZIP i czas zimnego startu zapisujemy jako pomiar, bez wymyślonego limitu odbioru.

Nowe automatyczne testy ograniczamy do wejścia executable i obsługi argumentów, zasobów/metadanych, bezpiecznych ścieżek/linków oraz braku fallbacku do systemowego Pythona/pip. Obecne 58 testów chroni logikę; uruchamiamy je w środowisku budowania, a mały smoke test sprawdza wynikowy executable. Nie dodajemy CI/CD, pełnej macierzy przeglądarek ani powielania testów bibliotek.

## 7. Materiały i porządek

Proponowane pliki do przyszłego wdrożenia:

| Obszar | Pliki / rezultat |
|---|---|
| Build | `packaging/standalone/` — wejście, spec, uzasadnione hooki, skrypty natywne Windows/macOS, osobne locki narzędzi budowania |
| Runtime | Niewielki adapter dispatch zasobów/maintenance; bez zmiany protokołów, SQLite i reguł topologii |
| Artefakty | Nowy katalog `dist/` z ZIP i sumami, manifest interpretera oraz faktycznie dołączonych bibliotek/DLL/frameworków |
| Materiały | Licencje/noty i potrzebne źródła Pythona, loadera i komponentów; pełny przegląd istniejących luk L01 nadal otwarty |
| Odbiór | `docs/etap-5a/` — karta, późniejszy raport, instrukcja użytkownika i wskazanie prywatnych dowodów |

Materiały SDK/narzędzi kompilacji nie stają się automatycznie zawartością paczki. Weryfikujemy to, co naprawdę dołączono; zbędny build-time pakiet usuwamy z listy runtime dopiero po potwierdzeniu, że nie jest zależnością wykonawczą (Dash obecnie wymaga setuptools). Sam tool z wyjątkiem licencyjnym nie zmienia warunków zależności.

Dotychczasowe paczki rc1 i ich raporty zachowujemy. Pliki rzeczywiście zastąpione w repozytorium trafiają do `old/RRRR-MM-DD/<poprzednia-ścieżka>` z wpisem w `docs/OLD.md`; aplikacja nie korzysta z old. Podczas przygotowania tego planu niczego nie przenosimy. Bez nowych sekretów, skanów, commitów, tagów i publikacji.

## 8. Nakład i decyzje przed kodem

**Wstępny nakład: 2–4 dni pracy przy dostępnych obu stanowiskach**, w tym około pół dnia na prototyp i ocenę wykonalności. Szacunek dotyczy tego rozszerzenia pakowania. Oczekiwanie na Windows/czyste środowisko, certyfikaty i pozostałe odbiory Etapu 5 rozliczamy osobno. Korekta po A2 jest jawna; trudnego problemu loadera/licencji nie ukrywamy w kolejnych dniach prób.

| ID | Propozycja / brak | Status |
|---|---|---|
| D01 | PyInstaller onedir, Python 3.13 dołączony do paczki, wersja narzędzia przypięta po krótkiej próbie | Zatwierdzone 1 listopada 2026 r. |
| D02 | Windows executable z konsolą, macOS executable + .command; zwykły użytkownik, lokalny panel | Zatwierdzone 1 listopada 2026 r. |
| D03 | Wymienialność wymaganych bibliotek potwierdzona przed pełnym pakowaniem | Warunek przejścia A2; nie domysł o onedir |
| D04 | Pierwszy kandydat wewnętrzny; podpisy publikacyjne i zakupy oddzielnie | Zatwierdzone 1 listopada 2026 r. |
| F01 | Windows 10 czy 11 i dostęp do natywnego builda/testu | Operator ma jeden z tych systemów; dokładny wariant/dostęp niepotwierdzony |
| F02 | Czysty macOS ARM i Windows bez Python 3.13 | Dostępność stanowisk/VM do ustalenia; maskowanie PATH nie wystarcza |
| F03 | Certyfikaty i docelowy sposób przekazywania ZIP | Brak potwierdzenia; nie zakładamy zakupu ani gładkiej dystrybucji publicznej |

Użytkownik zatwierdził **cały zakres A0–A7 oraz ADR-009** słowami „ok implementuj plan”. A2 przeszedł na macOS. Wdrożono 0.5.0rc2 i samodzielny ZIP macOS; przygotowano zestaw natywnego budowania Windows, bez deklarowania istnienia gotowego .exe. Historyczne rc1 pozostaje. Szczegóły i niewykonane próby zawiera raport. Zgoda nie obejmuje nowych sond ani publikacji.
