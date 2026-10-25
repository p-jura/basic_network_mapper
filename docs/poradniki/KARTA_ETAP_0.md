# Karta decyzji — Etap 0

Instrukcja: [poradnik Etapu 0](ETAP_0_USTALENIA.md). Podstawa: [plan startowy](../PLAN_STARTOWY.md) i [wymagania projektu](../WYMAGANIA_PROJEKTU.md).

Projekt: **Maper sieci — własna aplikacja z darmowych komponentów**.

Status karty: **Etap 0 zatwierdzony; późniejsze wymaganie startu bez SNMP/SSH uwzględnione w korekcie planu**. Historia zatwierdzenia pozostaje w sekcji 9; nowe szczegóły techniczne w sekcji 10 mają status propozycji do próby.

Data aktualizacji: 11 października 2026 r.

Autor ustaleń i zatwierdzający: właściciel projektu. Opracowanie techniczne: Codex.

Pierwotne decyzje D01–D14 i opisane wtedy parametry zostały zatwierdzone przez użytkownika słowami „zatwierdzam całość w takim razie”. „Do potwierdzenia” dotyczy wyłącznie faktów środowiskowych, np. dostępności urządzenia laboratoryjnego. Zatwierdzenie projektu nie stanowi dowodu wykonania prób ani dostępności sprzętu. D05/D06 oraz uzupełnienia D13/D14 uwzględniają późniejsze wymaganie użytkownika; ich stan bieżący opisuje sekcja 10.

## 1. Wymagania już ustalone

- Własny mapper; darmowe komponenty open source, bez triali, ograniczonych planów free i płatnych zależności funkcjonalnych.
- Python dla brakującej logiki i integracji; istniejące silniki protokołów, parsery, baza i renderer.
- IPv4, L2/podstawowe L3, różne sieci i odseparowane projekty.
- Podstawowe odkrywanie lokalnego LAN bez seedów i poświadczeń; opcjonalne SNMPv2c/v3, SSH fallback, ARP/FDB/VLAN/IF-MIB/LLDP do rozszerzonego mapowania.
- Odczyt urządzeń, ochrona sekretów, limity i odporność na awarie.
- Mapa, historia, JSON/CSV/SVG/PNG i offline.
- Szybkie MVP, testy newralgicznych punktów, bez CI/CD.
- Praca etapami z zatwierdzeniem wyniku.
- Systemy docelowe: Windows 10 i nowsze oraz wspierany macOS na Apple Silicon/ARM. Linux możliwy w kolejnych etapach.
- Dostęp do badanej sieci przez kabel Ethernet lub Wi-Fi/AP.
- Długi cykl może trwać kilka godzin; limity mają być modyfikowalne.
- Na etapie pierwotnych ustaleń Python nie był przygotowany. Obecnie w projekcie istnieje venv; interpreter i zależności wymagają potwierdzenia w raporcie Etapu 1.
- Start aplikacji automatycznie otwiera domyślną przeglądarkę po uzyskaniu gotowości lokalnego serwera, pod faktycznie używanym adresem i portem. Przy niepowodzeniu pokazuje klikalny adres.

Pełne wymagania: [WYMAGANIA_PROJEKTU.md](../WYMAGANIA_PROJEKTU.md). Nowe ustalenie dwóch systemów docelowych zastępuje wcześniejsze założenie jednego systemu odbioru w planie. Przyjęto sekwencyjne sprawdzenie obu platform, bez rozbudowanej macierzy testów.

## 2. Rejestr decyzji

| ID | Temat | Wartość / sposób realizacji | Status |
|---|---|---|---|
| D01 | Systemy | Windows 10 i nowsze oraz wspierany macOS ARM; Linux później. Przyjęte minimum odbioru: Windows 10 22H2 x64, Windows 11 x64 oraz jedna aktualnie wspierana wersja macOS ARM. Pierwszy przekrój na macOS ARM, potem krótki odbiór Windows. | Zatwierdzone |
| D02 | Uruchomienie/panel | Lokalny Python w venv, przeglądarka, `127.0.0.1:8050`, jeden operator i jeden cykl naraz. Zajęty port można zmienić w konfiguracji. Po gotowości serwera aplikacja automatycznie otwiera domyślną przeglądarkę pod faktycznym adresem i portem; przy niepowodzeniu pokazuje klikalny adres. | Zatwierdzone |
| D03 | Komponenty | Python 3.13 jako wersja bazowa do próby; PySNMP 7.1, Netmiko, ntc-templates/TextFSM, SQLite, NetworkX, Dash/dash-cytoscape. Dokładne wersje po próbie zgodności. | Zatwierdzone |
| D04 | Dostęp do urządzeń | Ethernet albo Wi-Fi/AP. Korzystamy z adresu i routingu systemu; SNMP UDP/161 i SSH TCP/22 lub porty profilu. Panel pozostaje lokalny. | Zatwierdzone |
| D05 | Odkrywanie | Wymagany start bez seedów: interfejs/trasy/sąsiedzi + ograniczone sondowanie, mapa logiczna. Opcjonalne seedy + LLDP do zarządzających IPv4: 500 urządzeń, 8 przejść, 4 h; regulowane. | Pierwotnie zatwierdzone; skorygowane późniejszym wymaganiem użytkownika, sekcja 10 |
| D06 | Aktywne sondowanie | Brak sond przy samym starcie panelu. Operator uruchamia podstawowe odkrywanie w pokazanym lokalnym zakresie bez profilu dostępu; jedna sonda, 5 celów/s, do 256 adresów. Bez skanowania portów. | Doprecyzowanie zatwierdzonej granicy na potrzeby nowego wymagania; technika do próby |
| D07 | Limity | Kilka godzin dotyczy cyklu, nie pojedynczego zapytania. Przyjęte wartości szczegółowe w sekcji 4: SNMP 3 s, jedno ponowienie, walk 60 s, urządzenie 5 min, cykl 4 h. | Zatwierdzone |
| D08 | SNMPv3 | Domyślny profil authPriv: HMAC-SHA-256 i AES-128. Profil zgodności SHA-1/AES-128 wyłącznie jawnie skonfigurowany dla potrzebnego urządzenia. Bez automatycznej zmiany algorytmów. | Zatwierdzone |
| D09 | Sekrety | ENV w MVP; w plikach wyłącznie identyfikatory profili i nazwy zmiennych. Osobne sekrety projektów, brak sekretów w logach i eksporcie. | Zatwierdzone |
| D10 | Pierwszy SSH | Cisco Catalyst 9300, IOS XE; rodzina 9200 jako kolejny bliski przypadek. Referencja programowa: IOS XE 17.18.4, jeśli dostępny zgodny sprzęt; faktyczną wersję zapisujemy z `show version`. Sterownik `cisco_ios`. | Zatwierdzone; dostępność sprzętu do potwierdzenia |
| D11 | Izolacja projektów | Osobny katalog danych, SQLite, konfiguracja i profile na projekt. `docs/network/` i `docs/seeds/` zachowane jako miejsca dokumentacji bez sekretów, nie jako wspólna baza wszystkich sieci. | Zatwierdzone |
| D12 | Cykle/historia | Ręczny start i opcjonalne odświeżanie co 15 min po zakończeniu poprzedniego cyklu. Snapshoty 7 dni, historia zmian 90 dni, przyjęty budżet danych 2 GB/projekt. Brak obserwacji po 3 porównywalnych odczytach i co najmniej 30 min. | Zatwierdzone |
| D13 | Laboratorium | Osobny LAN bez SNMP/SSH z 2–3 znanymi hostami do podstawowego odkrywania. Dla rozszerzonej ścieżki minimum: agent SNMPv2c/v3, jedna sesja Cisco SSH z próbką parsera, snapshot dwóch switchy/dwóch VLAN-ów. Realistyczny odbiór topologii: dwa switche i kilka hostów. Dostępność nie została podana. | Pierwotnie zatwierdzone; uzupełnione wymaganiem podstawowego LAN, sprzęt do potwierdzenia |
| D14 | Odbiór/wydajność | Podstawowy skan bez community i bez wymyślonych portów/VLAN-ów; przekrój komponentów oraz scenariusze port/VLAN/uplink/historia/awaria. Próba syntetyczna: 50 switchy, 1000 hostów, 20 VLAN-ów, 50 tys. obserwacji; kryteria w sekcji 7. | Pierwotnie zatwierdzone; uzupełnione wymaganiem podstawowego LAN |

## 3. Środowisko i połączenie

- **Systemy:** Windows 10 i nowsze oraz macOS ARM w wersji wspieranej w chwili odbioru. Dla Windows przyjęto x64; Windows ARM nie wchodzi automatycznie do pierwszego odbioru. Konkretny numer macOS i architekturę laptopa Windows zapisujemy podczas przygotowania stanowiska.
- **RAM:** użytkownik podał „6 GB” w polu RAM/wolne miejsce. Przyjmujemy roboczo 6 GB RAM jako zatwierdzony punkt odniesienia oraz dodatkowo 5 GB wolnego dysku na środowisko i pierwszy projekt. Rzeczywiste zasoby stanowiska sprawdzimy podczas przygotowania środowiska. 6 GB RAM nie oznacza 6 GB dostępnych dla samego procesu.
- **Python:** pierwotnie do instalacji; obecnie istnieje venv, bez udokumentowanego odbioru środowiska. Przyjęto interpreter 3.13 w aktualnej poprawkowej wersji tej linii; zgodność zależności potwierdzamy w Etapie 1. W MVP uruchomienie skryptem; instalator z dołączonym interpreterem można rozważyć przy pakowaniu, po sprawdzeniu rozmiaru i warunków dystrybucji.
- **Instalacja zależności:** według użytkownika powinna być możliwa. Potwierdzenie uprawnień i instalacja w venv należą do Etapu 1.
- **Podstawowy LAN:** dostęp do lokalnego IPv4 nie wymaga adresu zarządzającego ani profilu. Aplikacja pokazuje interfejs, maskę, trasę i zakres.
- **Adresy zarządzające:** dla opcjonalnych odczytów aplikacja korzysta z istniejącego adresu IPv4 i tras systemu. Operator musi mieć połączenie z VLAN-em zarządzającym albo trasę do niego. Samo Wi-Fi lub podłączenie kabla nie gwarantuje dostępu do wszystkich VLAN-ów.
- **Wi-Fi:** możliwa izolacja klientów i blokady dostępu do zarządzania. Aplikacja pokazuje brak odpowiedzi i wskazówki diagnostyczne; nie przełącza konfiguracji AP ani laptopa.
- **Ethernet:** może być potrzebny adapter USB–Ethernet; aplikacja używa systemowego interfejsu, bez własnego sterownika.
- **Panel:** automatycznie otwierany w domyślnej przeglądarce po uzyskaniu gotowości serwera. Domyślny adres `http://127.0.0.1:8050`; przy zmianie portu otwieramy faktycznie używany adres. Jeśli otwarcie przeglądarki się nie powiedzie, pokazujemy klikalny adres. Działa również podczas połączenia z siecią przez Wi-Fi/Ethernet. Kabel i Wi-Fi dotyczą odczytów urządzeń, nie sposobu publikacji panelu. Zdalnego panelu nie obejmuje pierwsze MVP.
- **Wiele interfejsów:** pokazujemy wybrany interfejs/adres źródłowy i zakres projektu. Nie zmieniamy tras, adresacji ani ustawień interfejsów automatycznie.

## 4. Zakres pierwszej próby i parametry

### Dokumentacja i dane

- Identyfikator pierwszego projektu: `lab-001`.
- `docs/network/`: wskazany przez użytkownika katalog opisu sieci i oczekiwanej topologii. W repozytorium tylko materiały przykładowe/zanonimizowane.
- `docs/seeds/`: wskazany katalog przykładów seedów i opisów profili bez sekretów. Rzeczywiste adresy klienta zapisujemy w prywatnej konfiguracji jego projektu.
- Dane wykonawcze: przyjęty katalog użytkownika `MapperSieci/projects/<project_id>/`; oddzielne `project.json`, `mapper.sqlite3` i snapshoty. Dokładną lokalizację dla Windows/macOS dobierzemy przy implementacji. Nie tworzymy tych katalogów w ramach aktualizacji karty.

### Zakres i aktywne sondowanie — wyjaśnienie

Odczyt SNMP/SSH oznacza pytanie znanego urządzenia o dane. **Aktywne sondowanie** oznacza dodatkowe wysyłanie np. ICMP do kolejnych adresów, żeby sprawdzić, co odpowiada. Może odświeżyć część obserwacji ARP, ale nie gwarantuje odnalezienia wszystkich hostów i generuje dodatkowy ruch.

**Aktualny zakres:** podstawowe odkrywanie rozpoczyna operator dla widocznego lokalnego zakresu i wybranego interfejsu, bez seedów/sekretów. Propozycja zakresu wynika z maski, lecz przy kilku interfejsach/VPN trzeba potwierdzić właściwy LAN. Brak zgodnej trasy wstrzymuje sondę. Zbyt duży zakres nie jest po cichu obcinany.

Sondowanie nie startuje przy otwarciu panelu. Przycisk „Odkryj” uruchamia jedną sondę na adres, do 5 nowych celów/s i 256 adresów. Zwiększenie budżetu jest jawne. Brak ICMP oznacza brak odpowiedzi, nie nieistnienie urządzenia. Stary wpis ARP ma oznaczenie cache, nie świeżą obecność. Nie czyścimy cache i nie zmieniamy ustawień. Zapis dokumentacji nie uruchamia żadnego skanu.

Rozszerzenie odczytuje wskazane seedy i sąsiadów LLDP w dozwolonym zakresie, jeśli istnieje przypisany profil. Sam adres znaleziony w ARP nie uruchamia logowania. Brak SNMP/SSH ogranicza szczegółowość mapy, a nie dostępność podstawowego odkrywania.

### Limity — zatwierdzone wartości startowe

| Parametr | Wartość startowa | Znaczenie |
|---|---|---|
| Podstawowe sondy | 5 nowych celów/s, do 256 adresów, jedna sonda na adres | Budżet D06 zastosowany do podstawowego odkrywania |
| Nowe deadline’y podstawowe — propozycja | 4 procesy ping; 3 s/proces; 240 s/próbę; odczyt systemowy 5 s | Do pomiaru na Windows/macOS, nie potwierdzone wyniki |
| Urządzenia równolegle | 4 łącznie; najwyżej 2 sesje SSH | Ogranicza ruch i zużycie zasobów |
| SNMP | Timeout 3 s, jedno ponowienie, najwyżej jedno aktywne żądanie na urządzenie | Błąd pojedynczego zapytania nie blokuje całego cyklu |
| GETBULK | `maxRepetitions=20`, możliwość zmniejszenia | Wielkość porcji, nie limit całej tablicy |
| Jeden walk tabeli | 60 s lub 50 000 rekordów — pierwszy osiągnięty limit | Limit obejmuje ponowienia; ucięcie oznaczamy w wyniku |
| Cały odczyt urządzenia | 5 min lub 200 000 rekordów | Zatrzymuje bardzo duże/wolne odczyty; nie udaje kompletności |
| SSH | 10 s na połączenie, 15 s na uwierzytelnienie/banner, 30 s na komendę | Bez ponawiania błędnego hasła; najwyżej jedno ponowienie błędu transportu |
| Cały cykl | 4 h | Realizuje „kilka godzin”; cykl kończy się wcześniej po wyczerpaniu kolejki |
| Odkrywanie infrastruktury | 500 unikalnych urządzeń i 8 przejść od seeda | Bezpiecznik pracy, regulowany niezależnie od licencji |
| Anulowanie | Zatrzymanie nowych zadań od razu, zakończenie bieżących w granicach timeoutów | Zapisujemy oznaczony wynik częściowy |

**Budżet rekurencji** to maksymalna ilość pracy jednego uruchomienia: czas, liczba urządzeń i odległość od seeda. Nie jest kosztem ani pakietem licencyjnym. Przykład: seed → sąsiad → sąsiad sąsiada to dwa przejścia. Po osiągnięciu granicy pokazujemy nieodwiedzone cele i powód zatrzymania; operator może zwiększyć budżet lub dodać seedy.

Wszystkie wartości są modyfikowalne. Przy 6 GB RAM odczyty przetwarzamy porcjami i zapisujemy do SQLite; nie trzymamy równolegle wszystkich surowych tabel i pełnych kopii grafu w pamięci. Limity wymagają pomiaru i ewentualnej korekty w Etapie 1/2.

### Interwał, retencja i brak obserwacji — przyjęte zasady

- Tryb domyślny: ręczny cykl. Opcjonalny tryb cykliczny: kolejny start 15 min po zakończeniu poprzedniego cyklu; bez kolejkowania zaległych startów. Dla cyklu trwającego 2 h odstęp między startami wyniesie około 2 h 15 min.
- Snapshoty znormalizowane: 7 dni. Historia zmian: 90 dni. Aktualny stan i ostatni poprawny snapshot pozostają dostępne również po tym okresie.
- Budżet danych: przyjęte 2 GB na projekt, regulowane. Najpierw usuwamy najstarsze snapshoty według retencji. Jeśli budżetu nie da się zachować bez utraty chronionych danych, pokazujemy komunikat i wstrzymujemy nowe zapisy; nie kasujemy historii zmian bez wiedzy operatora. Retencja to górny okres, a nie gwarancja zmieszczenia dowolnej ilości danych.
- Host po jednym poprawnym odczycie bez jego MAC dostaje „niezaobserwowany w tym cyklu”. Zdarzenie dłuższego braku obserwacji: 3 kolejne udane, kompletne i porównywalne odczyty jego właściwego zakresu, obejmujące co najmniej 30 min. Wygasanie FDB/ARP nie dowodzi fizycznego odłączenia.
- Błąd, ucięcie odczytu lub niedostępność źródłowego switcha oznacza nieaktualne/niepełne dane i nie zwiększa licznika zniknięcia. Duża rozpiętość czasu między odczytami obniża confidence przypisania.
- Podstawowy skan porównujemy tylko przy zgodnym interfejsie/zakresie i sprawnych adapterach. Zmiana Wi-Fi/VPN nie powoduje masowego zniknięcia hostów. Stary cache ani brak ICMP nie rozstrzygają obecności fizycznej. Zdarzenie po 3 cyklach/30 min oznacza dłuższy brak obserwacji, nie pewne odłączenie.
- Zmiana portu wymaga nowych zgodnych dowodów. Sprzeczne obserwacje pokazujemy jako konflikt. Przy odczytach co kilkanaście minut nie gwarantujemy wykrycia szybkiego MAC flapping.

## 5. Profile dostępu — bez sekretów

Profile nie są wymagane do podstawowego odkrywania. Nie wymyślamy community i nie włączamy usług na routerze operatora.

Zatwierdzone profile są wzorcami; nie wskazują istniejących kont ani poświadczeń.

| Profil | Protokół | Poziom / algorytmy lub metoda SSH | Kontekst | Sposób dostarczenia sekretu |
|---|---|---|---|---|
| `snmp-v3-primary` | SNMPv3 UDP/161 | authPriv, HMAC-SHA-256, AES-128 | Domyślnie pusty; jawna nazwa dla wymaganego kontekstu/VRF | ENV: `MAPPER_SNMP3_USER`, `MAPPER_SNMP3_AUTH_KEY`, `MAPPER_SNMP3_PRIV_KEY` |
| `snmp-v3-compat` | SNMPv3 UDP/161 | authPriv, SHA-1, AES-128; tylko po jawnym wyborze | Według konfiguracji urządzenia | Osobne nazwy ENV przypisane w projekcie |
| `snmp-v2-readonly` | SNMPv2c UDP/161 | Community z prawami odczytu; protokół bez szyfrowania | Kontekst producenta wyłącznie przez jawny profil, bez zgadywania community | ENV: `MAPPER_SNMP2_COMMUNITY` |
| `ssh-cisco-readonly` | SSH TCP/22 | Klucz SSH/agent preferowany; hasło konta RO jako alternatywa | Kontekst odczytu określa dozwolona komenda | Agent lub ścieżka do klucza; użytkownik/hasło przez ENV |

- **SNMPv3 — wyjaśnienie:** `authPriv` zapewnia uwierzytelnienie i szyfrowanie. SHA określa uwierzytelnianie, AES szyfrowanie. Oba algorytmy oraz hasła muszą odpowiadać konfiguracji urządzenia. PySNMP udostępnia SHA-256 i AES-128; zgodność z konkretnym agentem potwierdzimy w próbie. [API PySNMP](https://docs.lextudio.com/pysnmp/v7.1/docs/api-reference)
- **Zakres MVP:** v2c, v3 authPriv SHA-256/AES-128 oraz jawny profil zgodności SHA-1/AES-128, jeśli potrzebny w laboratorium. MD5/DES, AES-192/256 i inne warianty nie są częścią pierwszego odbioru bez konkretnej potrzeby. Brak zgodnego profilu daje jawny błąd obsługi, nie ciche osłabienie ustawień.
- **Fallback v3 → v2c:** domyślnie wyłączony. Dozwolony tylko po przypisaniu alternatywnego profilu do konkretnego celu/projektu. Nie próbujemy wszystkich haseł na wszystkich urządzeniach.
- **Uprawnienia:** użytkownik wymaga wyłącznie odczytu. Weryfikujemy opis uprawnień i zamkniętą listę operacji aplikacji; nie wykonujemy prób zapisu na urządzeniu produkcyjnym. SNMP SET i metody konfiguracji SSH nie są dostępne w kolektorze.
- **SSH:** weryfikujemy klucz hosta; pierwszy fingerprint zatwierdza operator. Brak automatycznego akceptowania dowolnego klucza. Pełny surowy log sesji domyślnie wyłączony.
- **Konteksty/VRF:** zapisujemy kontekst obserwacji, nie łączymy IP między VRF. Brak danych o kontekście daje niepewność, nie domyślną zgodę na scalenie.

### Pierwsza platforma SSH i znaczenie „najnowsza”

**Przyjęto:** Cisco Catalyst 9300, Cisco IOS XE; następnie Catalyst 9200. IDC podaje dla Cisco 27,6% udziału w przychodach rynku switchy Ethernet w IV kwartale 2025 r. To uzasadnia wybór producenta jako pierwszego; nie jest rankingiem liczby zainstalowanych urządzeń ani dowodem, że konkretny model 9300 jest najpopularniejszy. [IDC, publikacja 18 marca 2026 r.](https://www.idc.com/resource-center/blog/ethernet-switch-market-size-and-growth-datacenter-segment-surges-60-in-q4-as-ai-workloads-expand/)

Wpis użytkownika „najnowsza” realizujemy jako aktualne rekomendowane wydanie dla dostępnego modelu, zamiast wymagać dowolnego najnowszego obrazu. Według rekomendacji Cisco z września 2026 r. dla rodzin 9200/9300 wskazano IOS XE 17.18.4 i 17.15.6. Przyjęto 17.18.4 jako referencję próby, jeśli jest dostępna na zgodnym urządzeniu; zapisujemy faktyczną wersję i nie aktualizujemy switcha w ramach mappera. Nie uzależniamy działania mappera w innych sieciach od jednej wersji firmware. [Rekomendowane wydania Cisco](https://www.cisco.com/c/en/us/support/docs/switches/catalyst-9300-series-switches/214814-recommended-releases-for-catalyst-9200-9.html)

Sterownik Netmiko: `cisco_ios`. Istniejące szablony ntc-templates obejmują poniższe główne odczyty; zgodność odpowiedzi konkretnej wersji IOS XE sprawdzimy na próbkach. [Indeks szablonów](https://github.com/networktocode/ntc-templates/blob/master/ntc_templates/templates/index), [mapowanie sterowników Netmiko](https://github.com/ktbyers/netmiko/blob/develop/netmiko/ssh_dispatcher.py)

| Komenda odczytowa | Cel |
|---|---|
| `show version` | Model i faktyczna wersja systemu |
| `show mac address-table` | FDB: MAC, VLAN, port |
| `show ip arp` | IPv4–MAC w odczytywanym kontekście |
| `show vlan` | Dostępne VLAN-y i członkostwo |
| `show interfaces status` | Nazwy/stany portów |
| `show interfaces switchport` | Tryb portu, access/native/tagowane VLAN-y — według dostępnych pól |
| `show lldp neighbors detail` | Sąsiedzi infrastruktury |
| `show ip interface brief` | Interfejsy i IPv4; maski/podsieci dodatkowo z odczytów L3 SNMP |
| `show etherchannel summary` | Informacje o agregacji, jeśli dostępne |

Przygotowanie sesji: dopuszczamy `terminal length 0` i `terminal width 511`, które dotyczą sposobu prezentowania tej sesji. Sprawdzamy inicjalizację przypiętego sterownika; nie dopuszczamy wejścia w konfigurację, zapisu, restartu ani automatycznego podnoszenia uprawnień. Konto RO musi mieć dostęp do wymaganych poleceń. [Kod przygotowania sesji Netmiko](https://ktbyers.github.io/netmiko/docs/netmiko/cisco/cisco_ios.html)

Nie pobieramy pełnego `show running-config` do zwykłego cyklu. Brak LLDP/VLAN/ARP w CLI lub brak uprawnień oznacza częściowy wynik. Lista wyżej jest zatwierdzonym zakresem próby; wykonanie wymaga wskazania urządzenia, profilu i zakresu laboratorium.

## 6. Komponenty, dane pomocnicze i licencje

- **Zestaw:** Python 3.13, PySNMP 7.1, Netmiko, ntc-templates/TextFSM, SQLite, NetworkX, Dash/dash-cytoscape. [Tabela i źródła licencji](../PLAN_STARTOWY.md#2-proponowane-komponenty); [dokumentacja Python 3.13 dla Windows](https://docs.python.org/3.13/using/windows.html).
- **Stan sprawdzenia:** źródła głównych komponentów sprawdzono podczas opracowania planu, 11 października 2026 r. W chwili opracowania karty nie potwierdzono instalacji ani całego drzewa zależności. Obecnie istnieje venv, lecz brak raportu potwierdzającego zgodność zestawu. Algorytmy PySNMP, kandydat na sterownik, szablony oraz rekomendacje Cisco sprawdzono dodatkowo przy uzupełnianiu tej karty.
- **Nowy kandydat:** `psutil` (BSD-3-Clause) do interfejsów i masek; trasy/sąsiedzi/ping przez narzędzia dostarczone z systemem. Wymaga próby i sprawdzenia konkretnej wersji, nie zmienia historycznego zatwierdzenia D03. [API](https://psutil.io/), [licencja](https://github.com/giampaolo/psutil/blob/master/LICENSE).
- **Etap 1:** dobór konkretnych wersji zgodnych na Windows x64 i macOS ARM, kontrola zależności pośrednich i przypięcie wersji. Nie używamy niesprawdzonych przykładów API ze starszego PySNMP.
- **OUI:** przyjęto lokalną tabelę importowanej z darmowego źródła o potwierdzonych warunkach użycia i dystrybucji. Konkretne źródło wymaga sprawdzenia w Etapie 1. Do tego czasu producent ma wartość „nieustalony”, a przykłady używają własnych danych syntetycznych; brak płatnego lub sieciowego lookup API.
- **Ikony/fonty:** własne proste symbole grafu i fonty systemowe; bez płatnych paczek i CDN.
- **MIB-y:** odczyty po numerycznych OID i własne mapowanie potrzebnych pól. Dołączamy tylko te dodatkowe pliki MIB, których warunki wcześniej potwierdzimy; nie pobieramy automatycznie całych repozytoriów producentów.
- **Informacje licencyjne:** `docs/THIRD_PARTY_NOTICES.md`, wymagane teksty licencji i informacje autorów dla rzeczywiście dołączonych komponentów i danych. Reklamowane płatne usługi producentów bibliotek nie są zależnością aplikacji.

## 7. Laboratorium i kryteria próby/odbioru

### D13 — co oznacza pytanie o laboratorium

Chodzi o możliwość uzyskania wiarygodnych danych i połączeń, a nie o zakup dedykowanego sprzętu. Potrzebujemy wiedzieć, czy można skorzystać z istniejącego switcha z SNMP/SSH, czy są przykładowe wyniki poleceń oraz czy znamy rzeczywiste połączenia hostów. **Wpisy użytkownika nie potwierdzają dostępności takich urządzeń.**

Przyjęty podział:

1. Podstawowy LAN: zwykły router, 2–3 znane aktywne hosty, bez seedów/SNMP/SSH; Internet niepotrzebny. Osobny wynik próby podstawowej.
2. Bez sprzętu: własne snapshoty dwóch switchy, dwóch VLAN-ów i kilku hostów do grafu oraz reguł korelacji.
3. Próba SNMP: dostępny agent v2c i v3 authPriv, lokalny albo rzeczywiste urządzenie. Nie wymaga komercyjnego emulatora; przy wyborze narzędzia laboratoryjnego również obowiązuje wymóg bezpłatności.
4. Próba SSH: dostępny Cisco IOS XE i zanonimizowane odpowiedzi do parsera. Atrapa sesji i próbki CLI pomagają rozwijać kod, lecz nie potwierdzają działania na realnym switchu.
5. Odbiór topologii rozszerzonej: dwa istniejące switche, 3–5 hostów, dwa VLAN-y, uplink i źródło ARP L3. Ruch testowych hostów generuje operator; aplikacja tylko odczytuje dane.

Jeśli dostępne są wyłącznie snapshoty, zatwierdzenie obejmuje rozpoczęcie części offline Etapu 1. Próby rzeczywistych protokołów pozostają zadaniami otwartymi; nie deklarujemy wtedy gotowości rozszerzonej online. Podstawowy skan można odebrać niezależnie, jeśli jest dostępny zwykły LAN.

### D14 — co oznacza pytanie o odbiór i wydajność

Potrzebujemy mierzalnej odpowiedzi „wynik jest poprawny i działa wystarczająco szybko”. Nie wymaga to znajomości wszystkich przyszłych sieci. Ustalamy mały przypadek o znanym wyniku oraz jeden większy zestaw syntetyczny, który sprawdzi zużycie zasobów.

| Obszar | Zatwierdzony warunek zaliczenia |
|---|---|
| Etap 1: podstawowy LAN | Wykrycie znanych odpowiadających hostów bez seedów/profili, poprawny interfejs/zakres, źródła i świeżość. Brama według trasy. Logiczne relacje; port/VLAN nieustalony. Brak ICMP/cache nie daje fałszywej pewności. |
| Etap 1: protokoły rozszerzone | Udany odczyt v2c oraz v3 SHA-256/AES-128 z dostępnego agenta; jeśli potrzebny profil zgodności, osobna próba. Jedna sesja SSH i poprawne parsowanie przykładu. Brak sekretów w wyniku/logach. |
| Etap 1: uruchomienie | Start aplikacji po gotowości serwera otwiera domyślną przeglądarkę na rzeczywistym porcie; przy błędzie pokazuje klikalny adres. |
| Etap 1: graf | Lokalny panel otwiera snapshot, zaznacza węzeł, pokazuje szczegóły i pobiera PNG/SVG bez zewnętrznej usługi. |
| Host–port–VLAN | Dla znanej topologii przypisania odpowiadają połączeniom; dostępne dowody i niepewność. Host widoczny przez uplink nie dostaje fałszywego bezpośredniego przypisania. |
| Historia i awaria | Snapshot po przeniesieniu hosta daje zmianę portu; niedostępność jednego switcha daje nieaktualność, bez masowego zniknięcia hostów. |
| Izolacja i eksport | Dwa projekty z tym samym IP pozostają oddzielne; JSON/CSV i obrazy zachowują zakres/filtry i nie zawierają sekretów. |
| Offline | Po instalacji zależności i odłączeniu Internetu działa lokalny panel, snapshot i eksport; kolektory nie uruchamiają się. |
| Windows/macOS | Ten sam scenariusz uruchomienia, wczytania snapshotu i eksportu na obu platformach; odczyty online tam, gdzie dostępne jest laboratorium. Wynik zapisany z numerem systemu. |
| Wi-Fi/Ethernet | Jeśli stanowisko ma oba łącza, krótka próba odczytu tą samą aplikacją na każdym. Blokada Wi-Fi jest raportowana jako problem dostępu, nie brak hostów. |
| Mała sieć online | Dwa switche i 3–5 hostów: cel poniżej 2 min dla udanego pełnego cyklu w lokalnym laboratorium, z podaniem rozmiaru tabel. To cel pomiaru, nie gwarancja w każdej sieci. |
| Większy snapshot | 50 switchy, 1000 hostów, 20 VLAN-ów i 50 tys. obserwacji: cel do 30 s na import/korelację, do 5 s na pierwszy widok infrastruktury; hosty rozwijane/filtrowane, bez obowiązku stałego rysowania wszystkich. |
| Zasoby | Na stanowisku z co najmniej 6 GB RAM cel do 1,5 GB łącznie dla procesu aplikacji i karty przeglądarki w większej próbie; pomiar i korekta po pierwszym przekroju. |

Niezweryfikowane na starcie: VRF, współdzielone FDB, LAG, stack, MLAG, specyficzne konteksty VLAN i inne rodziny CLI. Zachowujemy kontekst i dowody, pokazujemy ograniczenia. Osoba potwierdzająca połączenia: właściciel projektu lub wskazany administrator znający laboratorium; dane kontaktowe nie zostały podane i nie są potrzebne w tej karcie.

## 8. Ryzyka i zadania otwarte

| Brak/ryzyko | Skutek | Następne działanie | Właściciel / rola | Termin/etap | Czy blokuje Etap 1? |
|---|---|---|---|---|---|
| Dostępność SNMPv3/Cisco SSH niepotwierdzona | Nie można potwierdzić ścieżki rozszerzonej online; nie blokuje podstawowej | Wskazać istniejące urządzenie/agenta i dostępne próbki | Właściciel projektu | Przed próbą online | Tylko rozszerzone online; podstawowy LAN i offline dopuszczone |
| Rzeczywiste zasoby stanowiska niezweryfikowane | Zatwierdzone cele mogą wymagać korekty po pomiarze | Sprawdzić RAM i dysk względem przyjętych 6 GB RAM / 5 GB wolnego miejsca | Właściciel projektu | Przy przygotowaniu stanowiska | Nie blokuje dokumentacji ani snapshotów |
| Adapter OS/psutil niepotwierdzony | Nie można potwierdzić podstawowego przekroju | Sprawdzić interfejs/trasy/cache/ping na obu OS według nowego poradnika | Implementacja | Etap 1 | Tak, dla zaliczenia podstawowego odkrywania |
| Nieznane realne zakresy i profile | Brak granic próby lub dostępu zarządzającego | Dla podstawowego LAN wskazać interfejs/zakres; tylko dla rozszerzenia prywatne seedy/profile | Operator | Przed odczytami | Zakres dla sond; profile tylko dla rozszerzenia |
| Dwa systemy docelowe | Większy zakres niż pierwotny odbiór jednego OS | Najpierw przekrój macOS ARM, potem krótki odbiór Windows; skorygować termin po próbie | Implementacja + właściciel | Etap 1 i pakowanie | Nie, ale może zwiększyć szacunek czasu |
| Zależności/warunki OUI niezweryfikowane | Nie można uznać paczki za w pełni sprawdzoną | Sprawdzić wersje i warunki; bezpłatne źródło OUI dobrać przed dystrybucją | Implementacja | Etap 1 | Nie dla syntetycznego offline; tak dla finalnego pakowania |
| Słabe Wi-Fi lub duże tabele | Częściowe odczyty i długi cykl | Ucięcia z powodem, regulowane timeouty/budżety, pomiar zamiast gwarancji | Implementacja | Etap 1/2 | Nie |
| Nieznane VRF/MLAG/stack | Niepewna tożsamość i linki | Snapshoty szczególnych przypadków, jawna macierz wsparcia | Implementacja + administrator laboratorium | Etap 2/3 | Nie blokuje podstawowego przekroju |
| Duża historia na małym dysku | Wzrost bazy ponad budżet | Retencja, licznik zajętości i bezpieczne wstrzymanie zapisu | Implementacja | Etap 2/5 | Nie |

## 9. Zatwierdzenie i kolejny krok

- **Decyzja:** zatwierdzone w całości; Etap 0 zamknięty.
- **Zatwierdził i data:** właściciel projektu, 11 października 2026 r.; potwierdzenie w rozmowie: „zatwierdzam całość w takim razie”.
- **Historyczny zakres zatwierdzenia:** pierwotne D01–D14, parametry, profile, kryteria odbioru i sposób pracy. Późniejsze uzupełnienie odnotowano w sekcji 10. D02 obejmuje automatyczne otwieranie przeglądarki po gotowości serwera i klikalny adres przy niepowodzeniu.
- **Punkt odniesienia zasobów:** przyjęto 6 GB RAM i 5 GB wolnego miejsca. Faktyczne zasoby komputerów, wersje systemów, dostępność laboratorium i zgodność bibliotek sprawdzamy w Etapie 1.
- **Dane przed próbą podstawową:** interfejs i zakres lokalnego LAN, bez poświadczeń. **Przed próbą rozszerzoną:** konkretne urządzenia, seedy, dozwolony zakres i poświadczenia w prywatnej konfiguracji. Nie zapisujemy sekretów ani nieujawnionej adresacji w repozytorium. Brak tych danych nie blokuje części offline.
- **Granice po doprecyzowaniu:** brak sond przy starcie panelu; operator uruchamia wymagane podstawowe odkrywanie po wskazaniu lokalnego zakresu. Seedy/poświadczenia nie są warunkiem tego uruchomienia. Zmiany konfiguracji urządzeń pozostają wykluczone. Panel pozostaje lokalny.
- **Następny krok:** Etap 1 — przygotowanie venv i krótki przekrój komponentów w zatwierdzonych granicach. Gdy brak sprzętu zarządzalnego, wykonać snapshot/graf i próbę podstawowego LAN, a protokoły rozszerzone potwierdzić później w laboratorium.
- **Zakończenie Etapu 1:** przed przejściem do Etapu 2 przedstawiamy wyniki i czekamy na zatwierdzenie, zgodnie z przyjętym procesem.

W ramach zapisania zatwierdzenia zaktualizowano tylko dokument. Nie wykonano instalacji, testów protokołów ani odczytów sieci.

## 10. Doprecyzowanie po zatwierdzeniu: odkrywanie bez SNMP/SSH

**Wymaganie ustalone przez użytkownika:** aplikacja odkrywa dostępną sieć także za routerem domowym/operatora, niezależnie od marki, bez obowiązkowych seedów, poświadczeń, SNMP i SSH. Następnie użytkownik polecił zaktualizować plan i poradniki. W ramach tej aktualizacji skorygowano D05/D06 oraz kryteria odbioru; nie wykonano implementacji ani skanowania.

Aktualny plan ma dwie uzupełniające się ścieżki:

1. Podstawowa: interfejs/maska, trasy/brama, sąsiedzi/ARP i ograniczone sondy po uruchomieniu przez operatora. Wynik logiczny, źródła i świeżość, nieustalone porty/VLAN-y. Nazwy tylko, gdy dostępne.
2. Rozszerzona: opcjonalne seedy/profile, SNMP/SSH i ARP/FDB/VLAN/LLDP. Porty i linki zgodnie z dowodami; dotychczasowe próby protokołów pozostają wymagane do potwierdzenia tej ścieżki.

**Propozycja techniczna do próby:** `psutil` do adresów/masek i cienki adapter istniejących narzędzi OS do tras, sąsiadów i ping. Bez obowiązkowego Nmap/Npcap, drivera przechwytywania i własnego stosu pakietów. Do sprawdzenia: zgodność wersji i parserów na Windows/macOS, wybór trasy przy VPN, świeżość cache i nowe deadline’y. Nie przedstawiamy tych elementów jako wcześniej zatwierdzonych i przetestowanych bibliotek.

Budżet podstawowy wykorzystuje 5 celów/s, 256 adresów i jedną sondę z D06. Nowe propozycje 4 procesy/3 s/240 s/5 s zapisano w sekcji 4. Brak odpowiedzi, izolacja Wi-Fi i niepełny cykl nie są dowodem zniknięcia urządzeń. Połączenie z segmentem nie staje się kablem do routera.

Instrukcje i oczekiwane wyniki: [Etap 1 — komponenty](ETAP_1_PROBA_KOMPONENTOW.md) oraz [Etap 1 — podstawowe odkrywanie](ETAP_1_ODKRYWANIE_PODSTAWOWE.md). Próba podstawowa nie wymaga laboratorium Cisco. Niewykonane próby SNMP/SSH pozostają jawne, bez blokowania samego skanu podstawowego i bez deklaracji pełnego MVP.

Zatwierdzenie historyczne D01–D14 pozostaje zapisane. Weryfikacja nowej ścieżki jest częścią raportu Etapu 1; przejście do Etapu 2 nadal wymaga zatwierdzenia wyniku.

## 11. Zatwierdzenie Etapu 2

23 października 2026 r. użytkownik zatwierdził plan Etapu 2 poleceniem „ok zatwierdzam plan, dzialaj”. Obowiązują decyzje z sekcji 17 planu: sześć tabel, systemowy katalog danych, jeden zapisujący, jawna publikacja snapshotów i limit importu. Zapis architektury przed implementacją: [ADR-002](../decisions/ADR-002-model-i-kolektory.md). Zgoda obejmuje implementację i testy offline; nie jest poleceniem skanowania sieci.

## 12. Zamknięcie Etapu 2 i planowanie Etapu 3

23 października 2026 r. użytkownik zatwierdził wynik Etapu 2 słowami „Zatwierdzam wynik etapu 2”. Wynik i jego granice opisuje [odbiór](../etap-2/ODBIOR_2026-10-23.md): offline i podstawowy LAN macOS potwierdzone; rzeczywiste SNMP/SSH, Windows i duża próba wydajnościowa niezweryfikowane. Etap 2 zamknięty w przedstawionym zakresie.

Przygotowano [propozycję Etapu 3](ETAP_3_TOPOLOGIA_I_HISTORIA.md). Jej reguły confidence, okno czasowe i migracja danych pochodnych wymagają zatwierdzenia przed kodem. Zgoda na wcześniejszy odbiór LAN nie uruchamia kolejnego skanu.

## 13. Zatwierdzenie Etapu 3 — 23 października 2026 r.

Użytkownik zatwierdził plan słowami „zatwierdzam koduj”. Przyjęto zakres poradnika Etapu 3, confidence jakościowe, okno 300 s i migrację SQLite v2 z backupem. Implementacja oraz odbiór offline są autoryzowane. Kolejny aktywny skan i rozpoczęcie Etapu 4 nie są częścią tej zgody. Decyzja: `docs/decisions/ADR-003-topologia-i-historia.md`.

## 14. Wynik techniczny Etapu 3 — 23 października 2026 r.

Zaimplementowano 0.3.0: topologia offline, korelacja portów/VLAN/LLDP, jakościowe confidence, stabilne ID, historia, SQLite v2 z backupem oraz CLI/podgląd. 26 testów i odbiór na zapisanym LAN przeszły bez nowych sond. SNMP/SSH na rzeczywistym sprzęcie, Windows i pełny panel pozostają nieodebrane. Raport: `docs/etap-3/RAPORT_ETAP_3.md`. Wynik Etapu 3 czeka na zatwierdzenie użytkownika; nie rozpoczynamy Etapu 4.

## 15. Autoryzacja poprawek 3.1 — 24 października 2026 r.

Użytkownik polecił „przygotuj szczegolowy plan poprawek, i zacznij wdrazac”. Przyjęto do implementacji plan `docs/poradniki/ETAP_3_1_POPRAWKI_PO_REVIEW.md` i ADR-005: krótkotrwały współdzielony stan tras, źródłowe sondy Windows, oddzielne blokady projektów i prywatne tworzenie plików. Zgoda obejmuje kodowanie i odbiór offline; nie stanowi zgody na nowe skany ani potwierdzenia Windows/sprzętu.

Wynik techniczny 3.1: wersja 0.3.1 zainstalowana offline, 38 testów krytycznych OK. Odczyty tras współdzielone, jedna kolekcja nadal globalnie, operacje offline innych projektów niezależne; nowe pliki prywatne od utworzenia. Adaptery Windows IPv4/DACL zweryfikowane na atrapach, nie na Windows/NTFS. Szczegóły w `docs/etap-3-1/RAPORT_ETAP_3_1.md`. Nie zatwierdza to pełnego odbioru Windows ani Etapu 4.

## 16. Przygotowanie planu Etapu 4 — 25 października 2026 r.

Po informacji użytkownika o dodaniu zmian na main zaproponowano sporządzenie planu panelu przed kodowaniem. Użytkownik odpowiedział „dzialaj”. Polecenie zrealizowano jako przygotowanie [planu Etapu 4](ETAP_4_PANEL_I_PRZEPLYW_OPERATORA.md) i [propozycji ADR-006](../decisions/ADR-006-panel-i-kontroler.md), bez implementacji panelu i bez nowych sond.

Status: plan do zatwierdzenia, nie zatwierdzony kod ani odbiór wcześniejszych niewykonanych prób. Wnioskowane kolejne zatwierdzenie obejmuje 4.0–4.4, kontroler zadań, odświeżanie opt-in D12, ENV, jawne zakresy seedów, eksporty i lokalną ochronę operacji. Formalnego odbioru Etapu 3/Windows/SNMP/SSH nie dopisano wstecz na podstawie commita. Szczegółowe kryteria znajdują się w poradniku.

## 17. Zatwierdzenie planu Etapu 4 — 25 października 2026 r.

Użytkownik polecił „masz zgode na dzialanie. Wdrazaj”. Przyjęto zakres 4.0–4.4 poradnika Etapu 4 i ADR-006: lokalny panel, kontroler w tle, postęp/anulowanie, opt-in seria D12, profile ENV, jawne zakresy seedów, mapa/historia/eksporty i ochrona lokalnych operacji. Autoryzacja obejmuje implementację oraz odbiór offline i oznacza zgodę na rozpoczęcie Etapu 4 na bazie 0.3.1. Nie jest potwierdzeniem niewykonanych prób Windows/NTFS/SNMP/SSH ani poleceniem nowych skanów.

Wynik techniczny Etapu 4: wdrożono 0.4.0 i panel operatora; 49 testów krytycznych oraz syntetyczny odbiór przeszły na macOS ARM. Wyniki i ograniczenia: [raport](../etap-4/RAPORT_ETAP_4.md). Wynik do zatwierdzenia; nie rozpoczęto Etapu 5. Nie wykonano nowych sond LAN ani odbioru Windows/NTFS/SNMP/SSH.

## 18. Zatwierdzenie wyniku Etapu 4 i planowanie Etapu 5 — 25 października 2026 r.

Użytkownik polecił „zatwierdzam wdrozenie dzialaj przy nastepnym planie”. Zatwierdzono wynik 0.4.0 wraz z przedstawionymi granicami prób. Etap 4 zamknięty w tym zakresie; niewykonane odbiory Windows/NTFS, SNMP/SSH, bez Internetu/cache i łącznego RAM pozostają otwarte.

Przygotowano [szczegółowy plan Etapu 5](ETAP_5_ODBIOR_I_PAKOWANIE_MVP.md), [propozycję ADR-007](../decisions/ADR-007-pakowanie-i-odbior-wydania.md) i [kartę prób](../etap-5/KARTA_ODBIORU_ETAP_5.md). Proponowany pierwszy artefakt: dwa ZIP jednej aplikacji z własnym wheel, lokalnymi kołami i skryptami, Python 3.13 jako wymaganie stanowiska. Plan wymaga zatwierdzenia przed wdrożeniem. Nie wykonano instalacji, nowych prób protokołów ani sond, nie zmieniono wersji aplikacji i nie opublikowano wydania.

## 19. Rzeczywisty odbiór LAN z panelu — 25 października 2026 r.

Przed zatwierdzeniem Etapu 5 użytkownik poprosił o skan obecnej sieci. Po odczycie lokalnych informacji zatwierdził konkretny interfejs, źródło i zakres słowami „Tak, skanuj ten zakres — mam prawo badać tę sieć”. Jednorazowy odbiór obejmował 253 cele, 5/s, 4 równolegle, 240 s, bez SNMP/SSH i powtarzania. Dokładny zakres zgody pozostał prywatny.

Cykl zakończył się po 128,997 s, z 2 odpowiedziami i bez błędów sond. Wykryto dwa błędy mapy: endpoint z rozgłoszeniowego ARP i powielenie własnego IPv4. [Raport](../etap-4/ODBIOR_LAN_2026-10-25.md). Zachowany snapshot umożliwia dalszą regresję offline bez nowego skanu. Nie zmieniono kodu ani reguł topologii podczas odbioru; poprawki wymagają konkretnego planu przed wdrożeniem.
