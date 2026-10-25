# Etap 5 — odbiór, pakowanie i przygotowanie wydania MVP

Data: **25 października 2026 r.** Status: **plan do zatwierdzenia przed wdrożeniem**. Użytkownik zatwierdził wynik Etapu 4 słowami „zatwierdzam wdrozenie dzialaj przy nastepnym planie”. Zgoda obejmuje zapis odbioru i przygotowanie tego planu. Nie oznacza rozpoczęcia pakowania, publikacji ani nowej zgody na sondowanie sieci.

Podstawa: [plan główny §8–9](../PLAN_STARTOWY.md), [karta decyzji D01–D14](KARTA_ETAP_0.md), [zaakceptowany wynik Etapu 4](../etap-4/RAPORT_ETAP_4.md), [stan licencji i otwarte luki](../licencje/STAN_PRAWNY_I_DYSTRYBUCJA.md), [propozycja ADR-007](../decisions/ADR-007-pakowanie-i-odbior-wydania.md). Do wyników służy [karta odbioru Etapu 5](../etap-5/KARTA_ODBIORU_ETAP_5.md); jej wiersze są obecnie niewykonane.

## 1. Cel i stan wejściowy

Dostarczyć jedną lokalną aplikację, którą można zainstalować na czystym stanowisku, uruchomić bez dostępu do Internetu i używać w jawnie odebranym zakresie. Do wydania dołączyć instrukcje, dokładne wersje i materiały komponentów, a deklaracje zgodności oprzeć na zapisanych próbach.

Bazą jest **0.4.0**: Etap 4 zatwierdzony, 49 testów krytycznych, działający panel i syntetyczne eksporty. Import/korelacja zestawu 50 tys. obserwacji trwały 6,119 s na macOS ARM. Pierwszy licznik widoku infrastruktury pojawił się po 2,165 s od kliknięcia w równoważnym zestawie; pomiar zawiera opóźnienie automatyzacji. Odbiór podstawowego LAN z Etapu 2 jest historycznym dowodem dla ówczesnej wersji i zakresu.

Nieodebrane pozostają: rzeczywisty Windows/NTFS, natywne sondy IPv4 na Windows, SNMPv2c/v3/SSH na sprzęcie, fizyczny test bez Internetu/cache, łączny RAM aplikacja+karta oraz kompletność materiałów konkretnego wydania. Akceptacja Etapu 4 zachowuje te ograniczenia; nie zamieniamy ich w zaliczone próby.

### Uzupełnienie po rzeczywistym odbiorze LAN

Po przygotowaniu tego planu operator zatwierdził jeden aktualny skan. [Raport LAN](../etap-4/ODBIOR_LAN_2026-10-25.md): kolekcja 253 celów poprawna, ale błędny endpoint rozgłoszeniowy i duplikat lokalnego IPv4 blokują odbiór mapy. Przed 5.1 należy zaplanować i wdrożyć wąskie poprawki tych reguł z właściwym wersjonowaniem wyników oraz sprawdzić je offline na zachowanym snapshotcie. Wymagana jest też diagnoza odtwarzania wyboru interfejsu w formularzu. Nie wymaga to ponownego skanu na potrzeby pierwszej regresji i nie oznacza wdrożenia całego planu Etapu 5.

## 2. Proponowany format pierwszego wydania — do zatwierdzenia

**Rekomendacja: ZIP dla macOS ARM i ZIP dla Windows x64, zawierające własny wheel, lokalny wheelhouse zależności oraz skrypty instalacji/uruchomienia.** To artefakty platformowe jednej aplikacji i jednego kodu. Python 3.13 jest wcześniej zainstalowanym wymaganiem stanowiska. Nie kopiujemy developerskiego .venv do paczki: środowisko tworzy się na miejscu. [Python 3.13 — środowiska venv nie są przeznaczone do przenoszenia](https://docs.python.org/3.13/library/venv.html).

Dlaczego ten wariant: korzysta z istniejącego sposobu uruchamiania i bibliotek, pozwala sprawdzić zależności offline oraz ich wymianę, nie dodaje narzędzia do zamrażania aplikacji ani dystrybucji interpretera. Instalator EXE/DMG z interpreterem może być osobnym późniejszym zadaniem, po pomiarze rozmiaru, zgodności i materiałów licencyjnych. Nie dokładamy go do szybkiego MVP bez osobnej decyzji.

Proponowany układ ZIP, nazwy jeszcze nie są gotowymi plikami:

```text
mapper-sieci-<wersja>-<platforma>/
  START_TUTAJ.md
  install.sh / install.cmd
  start.command / start.cmd
  wheelhouse/                     # własny wheel i dokładne zależności platformy
  requirements.lock              # wszystkie instalowane pakiety, wersje i hashe
  LICENSE
  THIRD_PARTY_NOTICES.md
  licenses/                       # odpowiednie pełne teksty i noty
  sources/                        # wymagane źródła dokładnych komponentów
  examples/                       # wyłącznie małe syntetyczne snapshoty
  manifest.json
  SHA256SUMS
```

Środowisko .venv powstaje dopiero u odbiorcy w katalogu z prawem zapisu; nie jest zawartością archiwum. Dane projektów pozostają w obecnym systemowym katalogu użytkownika, poza paczką. Nie dołączamy prywatnych konfiguracji, ENV, known_hosts operatora, baz, eksportów, old/, cache, prototypów ani całego roboczego repozytorium.

Skrypty wymagają zwykłego konta, obsługują spacje i polskie znaki w ścieżkach, wskazują własny interpreter i przekazują poprawne argumenty bez składania poleceń z danych sieci. Nie zmieniają trwale PATH, polityki PowerShell, firewalla, routingu ani uprawnień systemowych. Brak zgodnego Pythona daje informację i kończy instalację; start aplikacji nie pobiera pakietów ani nie uruchamia instalatora w tle.

## 3. Wersje, powtarzalność i instalacja offline

### 3.1. Ustal faktyczną zawartość

- Zanotuj commit i stan katalogu roboczego kandydata, wersję Python/pip/setuptools, OS/architekturę oraz dokładne zależności runtime z preview. Obecny requirements-stage2-macos.txt opisuje obserwowane środowisko macOS, **nie jest lockiem Windows ani finalnym lockiem wydania**.
- Nie aktualizuj bibliotek tylko dlatego, że przygotowujemy wydanie. Zachowaj sprawdzony zestaw; zmianę wymuszoną dostępnością wheel lub zgodnością udokumentuj z powodem i wykonaj regresję dotkniętej ścieżki. Pyproject może nadal opisywać dozwolone zakresy, ale paczka wydania ma dokładne wersje.
- Zbierz koła zgodne z Pythonem, OS i architekturą dla każdego docelowego ZIP. Utworzenie uniwersalnego wheel własnego kodu nie dowodzi zgodności natywnych zależności. Windows wheelhouse należy zainstalować i odebrać na Windows; macOS ARM nie zastępuje tego testu.
- Zbuduj własny wheel w tymczasowym katalogu/kopii. Sprawdź obecność migracji SQL, panelu i CSS, metadanych autora/MIT oraz poprawność instalacji bez src/ z checkoutu. Nie pakuj danych tylko dlatego, że trafiły do lokalnego środowiska.

### 3.2. Instaluj z lokalnych plików

Docelowy skrypt tworzy nowe venv i instaluje cały zestaw z wheelhouse, bez indeksu, z pinami i hashami. Przykład **kontraktu przyszłego instalatora**, nie gotowe polecenie dla obecnego repozytorium:

```text
<python-nowego-venv> -m pip install --no-index --find-links <wheelhouse>   --only-binary=:all: --require-hashes -r <requirements.lock>
```

Własny pakiet i wszystkie zależności muszą być uwzględnione w tym locku. Brak koła lub niezgodny hash przerywa instalację — brak cichego pobierania i budowania zależności na stanowisku. Materiały źródłowe w sources służą odpowiednim obowiązkom i weryfikacji, nie przypadkowemu fallbackowi pip. [Instalacja z lokalnych pakietów](https://pip.pypa.io/en/stable/user_guide/#installing-from-local-packages), [pip — hashe i tylko koła binarne](https://pip.pypa.io/en/stable/topics/secure-installs/).

Pobranie bibliotek na etapie przygotowania wheelhouse wymaga dostępu do oficjalnego źródła; gotowy pakiet nie może wymagać Internetu podczas instalacji i pracy, zakładając wcześniej zainstalowany Python. Hash potwierdza zgodność pliku z manifestem, nie jest podpisem autora. Nie wdrażamy teraz usługi aktualizacji, automatycznego publikowania ani CI/CD.

### 3.3. Sprawdź świeże środowisko

Instalacja do nowego venv w katalogu tymczasowym poza repozytorium, bez aktywacji developerskiego środowiska, bez PYTHONPATH checkoutu i bez dostępu do jego src/. Z nowego interpretera sprawdź wersję, lokalizację importu mapper, doctor i pip check. Uruchom panel offline, demo/import, szczegóły i wszystkie eksporty. Przenieś katalog rozpakowanej paczki **przed** instalacją do ścieżki ze spacjami/znakami i powtórz; nie wymagaj przenoszenia już utworzonego venv.

Zapisz test negatywny: zmieniony hash albo brak jednego koła kończy instalację czytelnym błędem bez Internetu i bez uszkodzenia wcześniejszej instalacji. Nowa próba używa nowego katalogu; nie nadpisuje działającego środowiska ani danych operatora.

## 4. Materiały licencyjne konkretnego artefaktu

Nie zmieniamy własnej MIT ani tekstów upstream. Wykonujemy zadania wskazane w istniejącym [dokumencie dystrybucji §4–5](../licencje/STAN_PRAWNY_I_DYSTRYBUCJA.md), względem rzeczywiście przekazywanych plików. Samo przepisanie nazw licencji z metadanych i zachowanie obecnego katalogu not nie zamyka odbioru.

| Zadanie | Dowód do zapisania |
|---|---|
| Inwentarz artefaktu | Każdy wheel, wersja, hash, architektura i dołączone komponenty; osobno runtime i narzędzia przygotowania |
| Istniejące braki not | Pełny materiał pySerial; noty wewnętrzne setuptools; komplet odpowiednich tekstów scp/Paramiko/certifi; zgodność z przekazywanymi wersjami |
| Biblioteki LGPL | Wybrana ścieżka zgodności, właściwe źródła dokładnych bibliotek i techniczny test możliwości ich wymiany w tej paczce; brak sprzecznej umowy instalatora |
| MPL / zasoby JS / fonty | Identyfikacja faktycznie dołączonych plików, w tym ustalenie wersji i materiałów SheetJS wskazanego przez noty Dash; nie zakładamy, że nieużywany w UI bundle nie trafia do wheel |
| Biblioteki natywne | Sprawdzenie tego, co koła faktycznie zawierają, wraz z wymaganymi tekstami/źródłami; nie ograniczamy się do nazwy głównego pakietu |
| Dostęp offline | Czytelne noty i materiały w archiwum; bez konieczności odwiedzenia ogólnej strony upstream jako jedynego dowodu |

Jeśli konkretnego obowiązku lub pochodzenia pliku nie da się ustalić, pozycja pozostaje otwarta i blokuje deklarację gotowości tej paczki do przekazania odbiorcom. Można nadal wykonywać lokalny odbiór funkcji. Nie usuwamy zależności lub nie modyfikujemy cudzych bibliotek w celu pozornego ominięcia obowiązków. Ewentualna zmiana zależności wymaga zapisanej decyzji i wąskiej regresji.

Producent/OUI pozostaje „nieustalony”, jeśli brak zweryfikowanych danych. Nie dodajemy na końcu nowej bazy, MIB-ów lub aktywnego API. To znane ograniczenie ma wejść do release notes i macierzy wsparcia. Zakres prawny §4 jest listą prac z wcześniejszego przeglądu, nie nowym zapewnieniem kompletności ani zmianą licencji.

## 5. Odbiór systemów i rzeczywistej sieci

### 5.1. Macierz D01

| Stanowisko | Minimalny odbiór | Stan na początku Etapu 5 |
|---|---|---|
| macOS ARM, wspierana wersja zapisana w raporcie | Nowa instalacja, panel/eksporty/offline, prywatne pliki, źródło/interfejs, anulowanie | Kod i odbiór 0.4.0 offline dostępne; nowy artefakt wymaga własnej próby |
| Windows 11 x64 / NTFS | To samo oraz natywne DLL/ABI IPv4, wiązanie źródła, DACL z drugiego zwykłego konta | Niewykonany |
| Windows 10 22H2 x64 / NTFS | Odrębne potwierdzenie instalacji i krytycznych ścieżek D01 | Niewykonany; dostępność stanowiska niepotwierdzona |

Numer OS, Python, architekturę, przeglądarkę i jej wersję zapisujemy, nie zgadujemy. Brak jednego stanowiska nie zmienia automatycznie zatwierdzonego D01 ani nie uprawnia do deklaracji „Windows 10 i nowsze”. Jeśli sprzęt nie jest dostępny, pozostaje kandydat z jawnym ograniczeniem; zmniejszenie zakresu wydania wymaga decyzji użytkownika. Linux i Windows ARM nie są dodawane.

### 5.2. Panel i praca bez Internetu

Na każdym dostępnym docelowym systemie odbierz z nowej instalacji: demo/import, wybór dwóch projektów ze wspólnymi IP, mapę i filtry, szczegóły, historię, JSON/CSV/PNG/SVG, poprawny port oraz zajęty port. Start ma otworzyć własną gotową instancję; drugi proces nie może zatrzymać pierwszego. Brak sond przy starcie i w trybie offline potwierdź osobno od działania trybu online.

Fizyczny test bez Internetu/cache: operator przygotowuje stanowisko bez dostępu do Internetu, a przeglądarkę z wyłączonym cache. Agent nie wyłącza interfejsu ani nie zmienia routingu/firewalla samodzielnie. Potwierdź instalację z lokalnego wheelhouse (Python już dostępny), start, odświeżenie panelu, szczegóły i eksporty. W narzędziach sieciowych przeglądarki zasoby wymagane do pracy mają pochodzić lokalnie. Oddzielnie można badać lokalny LAN bez Internetu — wymaga to jawnego zakresu sondowania.

### 5.3. Windows IPv4 i ochrona danych

- Weryfikacja na rzeczywistym Windows x64, nie tylko test struktur ctypes na macOS: uruchomienie API, timeout/status odpowiedzi, właściwe źródło oraz interfejs, zakończenie uchwytów i anulowanie.
- Wybrane LAN/Wi-Fi i konkurencyjna trasa/VPN, jeśli dostępne. Operator przygotowuje zmiany sieci. Aplikacja pomija sondy przy zmianie/niejednoznaczności, nie przełącza konfiguracji. Potwierdź drogę pakietu i źródło obserwacją na autoryzowanym stanowisku odbiorczym lub dostępnym narzędziem systemowym. Test samego argumentu source_ip nie dowodzi fizycznego interfejsu.
- Prywatne project.json, SQLite, backup, pliki tymczasowe i eksporty serwerowe: efektywny dostęp z drugiego zwykłego konta Windows ma być odmówiony. Konto właściciela ma działać bez administratora. SYSTEM/administratorzy pozostają świadomie dozwoleni. Zrzut samego SDDL nie zastępuje próby dostępu.
- Warunki negatywne: błąd ustawienia ochrony/brak trwałych ACL oraz niebezpieczny link mają przerywać zapis. Nie osłabiamy ACL w celu wykonania próby i nie twierdzimy, że Downloads ma ochronę aplikacji. Oddzielnie sprawdź blokady między dwoma procesami na Windows.

### 5.4. Podstawowy LAN bez seedów

Przed aktywną próbą operator podaje/potwierdza interfejs, źródłowe IPv4, zakres, liczbę celów i budżet oraz uprawnienie do tej sieci. Stara zgoda z Etapu 2 nie jest zgodą na nowy skan. Wystarczy mały, znany zakres z 2–3 znanymi hostami; nie trzeba ponownie skanować całego /24.

Oczekiwania: odpowiedzi znanych hostów, dostępne IP/MAC i źródła/czas; mapa logiczna, port/VLAN nieustalony bez dowodów. Jeden host blokujący ICMP oraz stary/incomplete ARP mają nie tworzyć fałszywej świeżej obecności ani odłączenia. Brak zarządzania routera operatora nie blokuje ścieżki podstawowej. Anuluj jedną kontrolowaną próbę i potwierdź częściowy wynik oraz zwolnienie własnych zasobów; nie zatrzymuj obcych procesów.

### 5.5. SNMPv2c/v3 i SSH na sprzęcie

1. Wskazane IPv4/porty, dozwolone zakresy, prywatne ENV, konto RO i potwierdzony klucz SSH. Informacje o połączeniach/portach podaje operator znający laboratorium. Nie zgadujemy profili i nie wykonujemy prób zapisu.
2. SNMPv2c oraz SNMPv3 authPriv SHA-256/AES-128: udane odczyty z agenta, poprawne zakończenie tabel i normalizacja. Porównaj ARP/IP–MAC, IF-MIB, bridgePort→ifIndex, FDB/VLAN i dostępne LLDP z rzeczywistością. Brak obsługiwanej tabeli jest wynikiem częściowym/unsupported, nie pustą kompletną topologią. Osobne zaliczenie transportu na agencie nie jest odbiorem portów fizycznej sieci.
3. Pierwszy SSH: dostępny Cisco IOS XE/cisco_ios, faktyczny model/wersja w raporcie. Obecnie kod ma sześć odczytów: show version, show mac address-table, show ip arp, show vlan, show interfaces status, show lldp neighbors detail. Wcześniejsza dłuższa lista z karty opisuje możliwy zakres próby; nie udajemy implementacji dodatkowych poleceń. Bez automatycznego enable lub zmiany konfiguracji.
4. Parser zweryfikuj na faktycznych odpowiedziach, w tym brak uprawnień/pusty wynik/zmieniony format. Do repozytorium trafiają wyłącznie bezpiecznie zanonimizowane, zatwierdzone próbki. Awaria jednej sesji nie może zatrzymać pozostałych źródeł.
5. Odbiór korelacji: dwa istniejące switche, 3–5 hostów, dwa VLAN-y, uplink i źródło ARP L3. Sprawdź rzeczywiste host–switch–port–VLAN, LLDP i odrzucenie przypisania hostów bezpośrednio do uplinku. Nie dopisuj VLAN-u na podstawie podsieci.
6. Przeniesienie testowego hosta lub odłączenie testowego źródła wykonuje operator w uzgodnionym laboratorium. Aplikacja tylko odczytuje. Porównaj kolejne snapshoty, port_changed i niepełny cykl; pojedyncza awaria nie może masowo oznaczać fizycznego odłączenia.

Nie rozszerzamy producentów SSH w tym etapie. SNMP jest wspólnym adapterem, ale rzeczywista obsługa MIB/kontekstów zależy od urządzenia. VRF/LAG/stack/MLAG zapisujemy w macierzy jako sprawdzone, częściowe albo niesprawdzone dla konkretnych przypadków; brak próby nie oznacza pełnego wsparcia.

## 6. Zasoby, odporność i aktualizacja

Powtórz D14 dla faktycznie zainstalowanej paczki tylko w zakresie zależności/zmian, które mogą wpłynąć na wynik: 50 switchy, 1000 hostów, 20 VLAN-ów, 50 tys. obserwacji. Cel import+korelacja ≤30 s, pierwszy widok infrastruktury ≤5 s, RAM aplikacja+karta ≤1,5 GB przy min. 6 GB RAM. Pomiar RAM obejmuje proces Pythona, jego procesy potomne oraz procesy karty/renderer; zanotuj metodę, obciążenie bazowe i współdzielenie procesów przeglądarki. Jeśli nie można wyizolować karty, podaj ograniczenie i nie zaliczaj celu na podstawie samego RSS Pythona.

Nie wprowadzamy wielodniowych testów obciążeniowych. Jedna powtarzalna większa próba i mały przypadek awarii wystarczą do pierwszego odbioru. Przekroczenie celu wymaga krótkiej analizy i poprawki albo jawnej akceptacji ograniczenia.

Aktualizacja: zatrzymaj własne aktywne procesy, wykonaj spójną kopię danych projektu w prywatnym katalogu, zainstaluj kandydata obok poprzedniej wersji, użyj kopii testowej bazy do migracji/replay i porównaj wyniki. Nie kopiuj aktywnej SQLite zwykłym kopiowaniem, nie otwieraj równocześnie tego samego projektu w starym i nowym procesie. Rollback używa poprzedniego środowiska i zgodnej kopii danych, nie nadpisania aktualnej bazy starszą wersją. Snapshoty JSON/SQLite to dane operatora, nie element instalatora.

Retencja i budżet 2 GB/projekt: potwierdź zachowanie chronionych wyników i odmowę nowych zapisów przy braku budżetu na danych tymczasowych. Nie wypełniaj rzeczywistego dysku ani nie kasuj historii operatora do próby. Eksporty też zajmują budżet; aplikacja nie ma po cichu usuwać prywatnych eksportów.

## 7. Kolejność realizacji i materiały

| Krok | Zadanie | Warunek przejścia |
|---|---|---|
| 5.0 — zakres | Zatwierdzenie planu/ADR-007, stan wyjściowy 0.4.0, dostępność stanowisk i laboratorium | Ustalony artefakt i lista odbiorów, bez uznawania braku sprzętu za zaliczenie |
| 5.1 — pakiet kandydujący | Minimalne skrypty, własny wheel, dwa platformowe locki/wheelhouse, manifest i materiały komponentów | Zawartość zweryfikowana, bez prywatnych danych; otwarte luki odnotowane |
| 5.2 — czysta instalacja | Nowe venv, lokalne biblioteki, demo/import/eksporty, negatywny hash, ścieżki ze spacjami | Instalacja bez checkoutu i bez Internetu; skrypty nie zmieniają systemu |
| 5.3 — systemy i LAN | macOS, Windows 11/10, źródło/interfejs, ACL/locki, mały LAN po odrębnej zgodzie | Raport konkretnych OS i prób; nie ma pozornych deklaracji Windows |
| 5.4 — zarządzanie | Agent v2c/v3, SSH, znana topologia, awaria/zmiana portu | Wyniki porównane z rzeczywistymi portami i VLAN-ami |
| 5.5 — finalny kandydat | Zasoby/aktualizacja/rollback, macierz wsparcia, release notes, ponowne sprawdzenie zmienionych miejsc | Kryteria wydania spełnione albo jawnie nierozstrzygnięte |
| 5.6 — odbiór użytkownika | Raport, artefakty i decyzja o przekazaniu | Zatwierdzenie końcowego wyniku; publikacja i operacje Git wyłącznie po osobnym poleceniu |

Przy braku Windows/switcha kontynuujemy bezpieczne kroki 5.1–5.2 i dokumentację. Nie blokujemy pracy nad lokalną paczką, lecz nie zamykamy pełnego Etapu 5 jako odebranego MVP. Nie przygotowujemy osobnej uproszczonej aplikacji jako zamiennika.

Planowane pliki: mały katalog packaging/ ze skryptami; platformowe requirements.lock w jego podkatalogach; manifest/sumy w wynikowym archiwum; docs/etap-5/ z raportem, wynikami, macierzą wsparcia oraz instrukcją aktualizacji. Duże wheelhouse, źródła zależności i gotowe archiwa pozostają poza repozytorium. Jeśli skrypt okaże się zbędny po zastąpieniu, trafia do old/ z wpisem w rejestrze; bez kasowania starych materiałów na etapie planu.

Wersja 0.4.0 pozostaje teraz bez zmian. Po implementacji i poprawkach można przygotować lokalnego kandydata 0.5.0rc1; numer finalny ustalimy przed wydaniem. Zmiana wersji nie zastępuje zatwierdzenia, tagu ani publikacji. Żadnego pushu, tagu i GitHub Release bez polecenia użytkownika.

## 8. Minimalna weryfikacja i warunek ukończenia

Pozostaje 49 istniejących testów. Dodajemy wyłącznie krytyczne sprawdzenia nowego pakowania: zgodność manifestu/hashów i obecność zasobów, instalacja bez pobierania/checkoutu, bezpieczne ścieżki oraz zachowanie danych podczas aktualizacji. Jedna mała próba ręczna na danym OS i rzeczywistych protokołach ma większą wartość niż rozbudowany mock hardware. Bez CI/CD, rozbudowanej macierzy każdej przeglądarki i testów kryptografii bibliotek.

Pełne zakończenie Etapu 5 wymaga:

- paczki zainstalowanej na docelowych systemach D01 oraz zgodnych bibliotek/zasobów offline;
- odebranego podstawowego LAN i rzeczywistych SNMPv2c/v3/SSH w zadeklarowanym zakresie, bez zgadywanych portów/VLAN i sekretów;
- potwierdzonego źródła Windows i efektywnej ochrony NTFS;
- pomiarów D14 albo jawnie zaakceptowanego ograniczenia, z łącznym RAM;
- zamknięcia wymaganych materiałów komponentów dla tej paczki i jawnej macierzy wsparcia;
- raportu, instrukcji startu/aktualizacji, sum plików i zatwierdzenia użytkownika.

**Niepełne środowisko lub pozytywne testy syntetyczne nie oznaczają pełnego MVP.** Ograniczone wydanie jest możliwe tylko po osobnej, świadomej decyzji użytkownika o jego zakresie. W karcie rozróżniamy PLANOWANE/NIEWYKONANE, OK, BŁĄD oraz UZGODNIONE OGRANICZENIE, z dowodem i właścicielem.

## 9. Decyzje i brakujące informacje

| ID | Propozycja / brak | Status i wpływ |
|---|---|---|
| E5-D01 | ZIP + lokalne koła + skrypty, Python 3.13 jako wymaganie; bez EXE/DMG na pierwsze wydanie | Do zatwierdzenia wraz z planem; ADR-007 |
| E5-D02 | Dokładne platformowe locki i hashe; bez automatycznej aktualizacji zależności | Do zatwierdzenia wraz z planem |
| E5-D03 | Pełny zakres odbioru D01 i protokołów pozostaje warunkiem pełnego MVP | Zgodne z dotychczasowym planem; nie ograniczamy wydania automatycznie |
| E5-F01 | Dostęp do Windows 11 i Windows 10 x64, drugiego zwykłego konta i NTFS | Fakt niepotwierdzony; wymagany przed odpowiednią próbą |
| E5-F02 | Dostęp do agenta v2c/v3 oraz Cisco SSH; dwa switche/dwa VLAN-y/znane porty do odbioru korelacji | Fakt niepotwierdzony; brak nie blokuje przygotowania paczki offline |
| E5-F03 | Jawny zakres LAN/seedy oraz poświadczenia ENV | Operator przekazuje prywatnie przed konkretnymi odczytami, nie do repozytorium |
| E5-F04 | Stanowisko bez Internetu/cache i metoda izolacji RAM karty | Do uzgodnienia przy odbiorze; bez samodzielnej zmiany konfiguracji sieci przez agenta |

Szacunek po sprawdzeniu kodu i otwartych pozycji licencji: **3–5 dni pracy przy dostępnych stanowiskach i danych**, z korektą po 5.1. To urealnienie wcześniejszych 2–3 dni, nie obietnica czasu kalendarzowego ani powód dodawania nowych usług. Oczekiwanie na sprzęt i wyjaśnienie materiałów komponentów rozliczamy oddzielnie. Najbliższa autoryzacja powinna dotyczyć tego konkretnego zakresu; nie ma potrzeby ponownie zatwierdzać rutynowych kroków 5.1–5.2 po akceptacji całego planu.
