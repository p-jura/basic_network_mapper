# Plan wdrożenia — własny mapper z darmowych komponentów

Data aktualizacji: 25 października 2026 r. Etapy 0–2 mają zapisane wcześniejsze zatwierdzenia. Na bazie implementacji 0.3.1 użytkownik zatwierdził plan Etapu 4 słowami „masz zgode na dzialanie. Wdrazaj”. Wdrożono 0.4.0 i wykonano odbiór techniczny offline; wynik czeka na zatwierdzenie. Rzeczywiste SNMP/SSH i Windows/NTFS pozostają nieodebrane. Dokument nie zastępuje raportów sprzętowych i nie autoryzuje nowych sond.

## 1. Cel i granica wykorzystania istniejących rozwiązań

Budujemy jedną lokalną aplikację odkrywającą różne, wcześniej nieznane sieci IPv4. Podstawowy scenariusz: operator łączy laptop z siecią, uruchamia panel, wybiera interfejs i widoczny zakres, a następnie rozpoczyna odkrywanie. Nie musi znać marki routera, seedów, community ani haseł. Brak SNMP/SSH nie blokuje pracy.

Mapa ma dwa poziomy szczegółowości, korzystające z tego samego modelu obserwacji, bazy i panelu:

| Ścieżka | Dane wejściowe i wynik |
|---|---|
| Podstawowe odkrywanie — wymagane w MVP | Interfejs IPv4, trasy, systemowa tablica sąsiadów i ograniczone sondowanie. Lista dostępnych urządzeń, lokalne MAC tam, gdzie można je ustalić, brama według tras oraz mapa logiczna segmentu. Bez poświadczeń. |
| Rozszerzone mapowanie — wymagane w MVP tam, gdzie dostępne źródła | Opcjonalne seedy i profile SNMPv2c/v3 lub obsługiwane SSH. ARP/FDB/VLAN/IF-MIB/LLDP pozwalają przypisywać porty, VLAN-y i potwierdzać połączenia infrastruktury. |

Nie gwarantujemy wykrycia każdego hosta ani fizycznego kabla, gdy urządzenia nie udostępniają odpowiednich danych. Switch bez adresu zarządzającego może pozostać niewidoczny. Nazwa operatora, OUI lub adres bramy nie dowodzą modelu urządzenia. Połączenie host–segment nie oznacza kabla host–router.

Istniejące rozwiązania oznaczają biblioteki, funkcje systemu, parsery, bazę i renderer. Nie wykorzystujemy gotowego produktu mapowania jako silnika. Python realizuje brakującą integrację i reguły; nie piszemy silnika SNMP, SSH ani stosu pakietów. Odrębny projekt Flutter/Dart pozostaje niezależny.

Wymagane funkcje działają lokalnie, bez triali, ograniczonych edycji free, subskrypcji, płatnych dodatków i licencyjnych limitów urządzeń. Budżety pracy są regulowane i wynikają z obciążenia, nie z licencji.

## 2. Proponowane komponenty

| Zadanie | Komponent | Licencja / warunki | Zakres |
|---|---|---|---|
| Interfejsy IPv4 i maski | `psutil` — nowy kandydat do próby | BSD-3-Clause | `net_if_addrs`, `net_if_stats`; nie dostarcza kompletnej topologii ani tablicy bram |
| Trasy, sąsiedzi i sondy | Narzędzia dostarczone z Windows/macOS + `subprocess`, `ipaddress`, `asyncio` | Narzędzia systemu użytkownika; nie dołączamy ich binariów do paczki | Odczyty tras/ARP, systemowy ping, timeouty i limitowanie. Własny cienki adapter i normalizacja |
| SNMPv2c/v3 | PySNMP, linia 7.1 | BSD-2-Clause | Protokół, authPriv; własne zapytania i interpretacja tabel |
| SSH | Netmiko | MIT | Sesje odczytowe w ograniczonej puli |
| CLI | ntc-templates/TextFSM | ntc-templates: Apache-2.0; zależności oddzielnie | Istniejące parsery; adapter tylko dla rzeczywistej luki |
| Dane i historia | SQLite przez `sqlite3` | SQLite: domena publiczna | Lokalna baza i transakcje |
| Graf | NetworkX | BSD-3-Clause | Wybrane algorytmy; reguły dowodów pozostają własne |
| Panel i mapa | Dash open source, dash-cytoscape | MIT | Formularze, graf, szczegóły, PNG/SVG |
| JSON/CSV | Biblioteka standardowa Pythona | W ramach dystrybucji Pythona | Eksport modelu |

Źródła: [psutil — API](https://psutil.io/), [licencja psutil](https://github.com/giampaolo/psutil/blob/master/LICENSE), [PySNMP](https://docs.lextudio.com/pysnmp/v7.1/), [Netmiko](https://github.com/ktbyers/netmiko/blob/develop/LICENSE), [ntc-templates](https://github.com/networktocode/ntc-templates/blob/master/LICENSE), [SQLite](https://sqlite.org/copyright.html), [NetworkX](https://github.com/networkx/networkx/blob/main/LICENSE.txt), [Dash](https://github.com/plotly/dash/blob/dev/LICENSE), [dash-cytoscape](https://github.com/plotly/dash-cytoscape/blob/main/LICENSE).

W Etapie 1 sprawdzamy konkretne wersje, zależności pośrednie i warunki dystrybucji; zapisujemy `docs/THIRD_PARTY_NOTICES.md`. `psutil` jest dodatkiem do zatwierdzonego stosu proponowanym w tej aktualizacji, nie biblioteką już sprawdzoną na stanowisku. Podstawowa ścieżka nie wymaga Nmap, Npcap, raw socketów, sterownika przechwytywania ani uruchomienia całej aplikacji jako administrator. Ich ewentualne późniejsze użycie wymaga osobnej oceny potrzeby i warunków.

OUI, MIB-y i inne dane pomocnicze wymagają osobnego sprawdzenia. Producent pozostaje nieustalony, gdy brak zweryfikowanej bazy lub MAC jest lokalnie administrowany. Brak CDN, Dash Enterprise i płatnych API.

## 3. Architektura jednej aplikacji

```text
Przeglądarka → lokalny panel Dash + dash-cytoscape
                         │
               Projekty + kontroler cykli
                         │
             ┌───────────┴─────────────────┐
             │                             │
  Odkrywanie podstawowe           Mapowanie rozszerzone
  psutil + adapter OS             opcjonalne seedy/profile
  trasy/sąsiedzi/ping              PySNMP / Netmiko + parsery
             │                             │
             └───────────┬─────────────────┘
                         ▼
       Normalizacja → dowody → korelacja → graf
                         │
                SQLite + historia
                         │
                 JSON/CSV/SVG/PNG
```

Jeden proces Python 3.13 w venv, jeden operator, jeden aktywny cykl. Panel na `127.0.0.1:8050`, automatyczne otwarcie przeglądarki po potwierdzeniu gotowości własnego serwera; zmieniony port trafia do URL. Wiele projektów ma osobne konfiguracje, bazy i dane.

Pierwszy przekrój: macOS ARM, następnie krótki odbiór Windows 10 22H2 x64 i Windows 11 x64 zgodnie z D01. Linux później. Dostęp przez Ethernet albo Wi-Fi, bez zmieniania adresacji, tras, konfiguracji AP czy urządzeń.

Kontroler działa w tle. Procesy systemowe mają timeout i obsługę anulowania; SNMP jest asynchroniczne, SSH korzysta z ograniczonej puli wątków. SQLite publikuje ukończony snapshot transakcyjnie; wynik częściowy ma jawny status. Bez Redis, Celery, mikroserwisów, osobnego FastAPI i CI/CD.

## 4. Kolejność realizacji podstawowego odkrywania

1. Odczytaj aktywne interfejsy IPv4, maski i trasy. Przy kilku kandydatach pokaż wybór; nie zakładaj, że domyślna trasa przez VPN wskazuje badany LAN.
2. Wyznacz propozycję lokalnego zakresu z maski. Pokaż interfejs, adres źródłowy, zakres i liczbę celów przed przyciskiem „Odkryj”. Seedy i poświadczenia są opcjonalne.
3. Zapisz sąsiadów przed sondowaniem, wraz z interfejsem, dostępnym stanem wpisu i czasem odczytu. Wpis cache nie oznacza świeżej odpowiedzi.
4. Po uruchomieniu przez operatora wykonaj ograniczone sondy ICMP systemowym pingiem, a następnie ponownie odczytaj sąsiadów. Brak odpowiedzi ICMP nie usuwa hosta. W lokalnym L2 system może rozwiązać MAC przez ARP mimo braku odpowiedzi ICMP; wynik zależy od tras, cache i izolacji.
5. Normalizuj obserwacje: odpowiedź ICMP, wpis sąsiada/cache, lokalny interfejs, brama z trasy. Zachowaj źródło i świeżość; nie przypisuj pozornego sukcesu na podstawie starego cache.
6. Zbuduj mapę segmentu i hostów, z logicznymi relacjami. Port i VLAN mają `null`/„nieustalony”. Brama jest kandydatem na router według konfiguracji systemu, nie dowodem wykrycia całej infrastruktury.
7. Zapisz wynik, zasięg i ograniczenia. Opcjonalne SNMP/SSH wzbogaca go później bez tworzenia drugiej, niezależnej listy hostów.

Nazwy z lokalnego cache/systemu można wykorzystać od razu. Aktywne reverse DNS/mDNS jest opcjonalnym uzupełnieniem po podstawowym przekroju, z osobnym limitem; nazwa nie rozstrzyga tożsamości. Nie blokuje odbioru MVP i nie wymaga Internetu.

## 5. Zasady modelu i wnioskowania

- Obserwacja zawiera projekt, cykl, czas, źródło, interfejs/segment oraz kontekst/VRF, jeśli znany. IP nie jest globalnym identyfikatorem.
- Oddzielamy dowód obecności, powiązanie IP–MAC i pewność fizycznego podłączenia. Świeża odpowiedź hosta nie dowodzi jego portu ani VLAN-u.
- Segment lokalny nie dostaje VLAN ID z numeru podsieci, SSID lub domysłu. Filtr VLAN ma kategorię „nieustalony”. MAC hosta za routerem nie jest MAC bramy.
- Rozszerzone ARP/FDB łączymy w zgodnym kontekście i czasie. Bridge port mapujemy przez `dot1dBasePortIfIndex`; FDB ID nie zawsze oznacza jeden VLAN. Bitowe mapy VLAN korzystają z numeracji portów bridge.
- LLDP, konfiguracja portu i obserwacje pomagają ustalać uplinki. Liczba MAC-ów, trunk i najmniejsza tablica są wskazówkami, nie samodzielnym dowodem fizycznego kabla.
- Konflikty zachowują kandydatów i uzasadnienie confidence. Proxy ARP, AP, telefon z komputerem, hypervisor i niezarządzalny switch mogą uniemożliwić jednoznaczność.
- LAG/stack/MLAG pokazujemy zgodnie z dowodami. Nieznane VRF nie uprawnia do scalenia IP. Podstawowe L3 obejmuje routery/interfejsy/podsieci, bez pełnych ścieżek routingu.
- Historię porównujemy w tym samym zakresie i interfejsie; zmiana Wi-Fi, VPN albo podsieci wymaga sprawdzenia projektu. Brak odpowiedzi to „niezaobserwowany”, nie dowód fizycznego odłączenia. Awaria lub ucięcie cyklu nie zwiększa licznika braku obserwacji. MAC flapping wymaga porównywalnych dowodów zmian portów, nie zmian IP w skanie podstawowym.

ARP wiąże adres protokołu z adresem sprzętowym, bez fizycznego portu switcha. [RFC 826](https://datatracker.ietf.org/doc/html/rfc826). Możliwość wykrywania zależy od odpowiedzi i filtrowania ruchu. [Opis technik wykrywania](https://nmap.org/book/host-discovery-techniques.html). To odniesienie do technik, nie wybór Nmap jako zależności.

## 6. Zakres, obciążenie i bezpieczeństwo

Domyślnie uruchomienie panelu nie wysyła sond. Odczyt lokalnych informacji pozwala pokazać zakres, a przycisk „Odkryj” uruchamia podstawowe sondowanie bez żądania community. Bazujemy na wcześniejszym budżecie D06: do 256 adresów, 5 nowych celów/s, jedna sonda na cel, bez skanowania portów. Dla większej podsieci operator wybiera mniejszy zakres lub jawnie zmienia limit; nie skanujemy po cichu pierwszych 256 i nie nazywamy wyniku kompletnym.

Nowa propozycja do pomiaru w Etapie 1: najwyżej 4 równoczesne procesy ping, deadline procesu 3 s, deadline podstawowej próby 240 s, timeout odczytu polecenia systemowego 5 s. Globalny limit cyklu nadal wynosi 4 h; krótszy budżet podstawowy działa dodatkowo. Przekroczenie oznacza wynik częściowy. Nie ponawiamy sond bez jawnej zmiany profilu.

W rozszerzonej ścieżce pozostają zatwierdzone limity: 4 urządzenia, maksymalnie 2 SSH, SNMP 3 s i jedno ponowienie, GETBULK 20, walk 60 s/50 tys. rekordów, urządzenie 5 min/200 tys. rekordów, LLDP 500 urządzeń/8 przejść, cykl 4 h. SSH: połączenie 10 s, auth/banner 15 s, komenda 30 s. Ucięcia i nieodwiedzone cele są widoczne.

SNMP tylko GET/GETNEXT/GETBULK. SSH ma zamkniętą listę odczytów, weryfikację klucza hosta i sprawdzone przygotowanie sesji. Bez SET, konfiguracji, restartów i zapisu. Sekrety w ENV/agentach, nigdy w argumentach, logach, snapshotach ani eksporcie. Nie szukamy ani nie zgadujemy community.

Adapter OS korzysta z list argumentów `subprocess`, `shell=False`, walidacji IPv4 i timeoutów. Odczytuje trasy i sąsiadów; nie czyści ARP i nie zmienia ustawień. Jeśli nie można potwierdzić trasy przez wybrany interfejs, pomija sondę z powodem zamiast wysyłać ją inną siecią.

Ręczny cykl domyślny; opcjonalny następny start 15 min po zakończeniu poprzedniego. Snapshoty 7 dni, historia 90 dni, budżet 2 GB/projekt zgodnie z kartą. Dłuższy brak obserwacji po 3 udanych porównywalnych cyklach i co najmniej 30 min pozostaje statusem obserwacji, a nie dowodem odłączenia.

## 7. Panel i eksport

Pierwszy ekran: projekt, interfejs, IPv4/maska, brama lub „nieustalona”, zakres, budżet i przycisk odkrywania. Sekcja opcjonalna: seedy i profile SNMP/SSH. Postęp rozróżnia wykonane, nieodpowiadające, pominięte i nieprzeskanowane cele.

Mapa rozróżnia segmenty, hosty, routery/kandydatów i switche. Relacje logiczne mają osobny styl i etykietę; krawędzie z dowodami portów mają etykiety portów oraz dostępne źródło. Panel szczegółów pokazuje IP, MAC, nazwę, producenta, świeżość, źródła, confidence oraz jawnie nieustalone port/VLAN/switch.

Wyszukiwanie IP/MAC/nazwa, filtr VLAN z kategorią „nieustalony”, historia i lokalne eksporty JSON/CSV/SVG/PNG. Obraz obejmuje aktualny widok/filtr, JSON/CSV pełny wybrany snapshot wraz z typami relacji i ograniczeniami. SVG/PNG przez istniejący `generateImage`. [Dokumentacja eksportu](https://dash.plotly.com/cytoscape/images).

Offline: lokalny snapshot, panel i eksport bez Internetu, CDN i uruchamiania kolektorów. To osobna opcja od odkrywania aktywnego LAN bez dostępu do Internetu.

## 8. Etapy i punkty odbioru

**Aktualny krok:** [Etap 4 — panel](poradniki/ETAP_4_PANEL_I_PRZEPLYW_OPERATORA.md) wdrożony w wersji 0.4.0, 49 testów krytycznych i odbiór syntetyczny. [Uruchomienie](poradniki/ETAP_4_URUCHOMIENIE_I_ODBIOR.md) i [raport techniczny](etap-4/RAPORT_ETAP_4.md) zawierają dokładne wyniki oraz granice prób. Wynik czeka na odbiór użytkownika przed Etapem 5. Nie potwierdzono jeszcze Windows/NTFS, realnego SNMP/SSH ani łącznego RAM aplikacja+karta.

| Etap | Zakres | Wynik |
|---|---|---|
| 0. Ustalenia | Karta i ujednolicenie wymogu startu bez poświadczeń | Zatwierdzenie historyczne zachowane; późniejsze wymaganie dopisane |
| 1. Próba komponentów | Venv, psutil + adapter OS, podstawowy przekrój bez SNMP/SSH, panel offline/PNG/SVG, osobne próby SNMPv2c/v3 i SSH | Raport z oddzielnym wynikiem odkrywania podstawowego i rozszerzonego |
| 2. Model i kolektory | Obserwacje lokalne i zarządzające, SQLite, statusy/świeżość, limity, izolacja, IF/ARP/FDB/VLAN/LLDP | Snapshot z dowodami; brak SNMP nie blokuje kolektora podstawowego |
| 3. Topologia i historia | Segment logiczny, korelacja rozszerzona, uplinki, konflikty, confidence, porównania zakresów | Poprawne mapy i historia na kontrolowanych danych |
| 4. Panel | Scenariusz bez seedów, opcjonalne profile, postęp, mapa, filtry, szczegóły, eksporty | Kompletny przepływ operatora |
| 5. Odbiór i pakowanie | Sieć domowa bez zarządzania i sieć z SNMP/SSH, Windows/macOS, instalacja | MVP z jawnymi granicami wsparcia |

Cel organizacyjny: tygodnie pracy, bez wielomiesięcznego budowania własnych protokołów. Wstępna rezerwa: Etap 1 2–4 dni; Etap 2 4–6; Etap 3 3–4; Etap 4 3–4; Etap 5 2–3. Łącznie 14–21 dni pracy i 3–5 dni bufora po przygotowaniu stanowisk; szacunek do korekty po Etapie 1. Oczekiwanie na urządzenia i drugi OS zwiększa czas kalendarzowy. Nie jest to obietnica pełnego wsparcia każdego producenta, VRF/MLAG ani każdego hosta.

Brak laboratorium SNMP/SSH nie blokuje podstawowego przekroju. Próby rozszerzone pozostają oznaczone jako niewykonane; nie deklarujemy pełnego MVP bez ich odbioru lub jawnej decyzji o ograniczeniu wydania. Na końcu każdego etapu przedstawiamy konkretny wynik do zatwierdzenia przed następnym.

### 8.1. Uwagi po niezależnym review — wdrożenie 3.1

24 października 2026 r. porównano niezależne review z kodem i planem. [Weryfikacja oraz rejestr R01–R09](reviews/REVIEW_2026-10-24.md) rozdziela potwierdzone problemy, zatwierdzone ograniczenia zakresu i niewykonane odbiory.

Zatwierdzony poleceniem użytkownika krok przed integracją aktywnego odkrywania z panelem: ograniczenie odczytów tras per cel przy zachowaniu aktualności stanu, poprawne źródło IPv4 na Windows, oddzielenie globalnej blokady kolekcji od blokad projektów, doprecyzowanie ochrony ACL i małe sprawdzenia parserów. Jeden aktywny cykl pozostaje wymaganiem; nie włączamy równoległych skanów jako skutku zmiany locka.

**Status: wdrożono 0.3.1 i wykonano odbiór offline (38 testów).** [Szczegółowy plan](poradniki/ETAP_3_1_POPRAWKI_PO_REVIEW.md) i [raport](etap-3-1/RAPORT_ETAP_3_1.md) rozdzielają wykonany kod i niewykonane odbiory Windows/NTFS/switcha. Nie zmieniono zakresu MVP ani statusu odbioru Etapu 3. Linux pozostaje późniejszym rozszerzeniem, nowe SSH wymagają wyboru platform i próbek. Próby Windows/SNMP/SSH nadal wymagają środowiska i osobnego zakresu operatora; nie oznaczamy ich jako wykonanych. Kwestie redystrybucji są już prowadzone w [dokumencie licencji](licencje/STAN_PRAWNY_I_DYSTRYBUCJA.md) i muszą zostać zamknięte dla konkretnego artefaktu w Etapie 5.

## 9. Minimalne sprawdzenia

Automatycznie chronimy tylko krytyczne reguły: zakres/interfejs i limit celów, timeout/anulowanie, niepełny cykl i stary cache bez fałszywej obecności/zniknięcia, brak wymyślonego portu/VLAN i MAC za routerem, izolację projektów, bridgePort/ifIndex/VLAN, uplinki/konflikty i brak sekretów/operacji zapisu.

Ręcznie: domowy LAN bez SNMP/SSH i bez Internetu, kontrolowany host bez ICMP, zmiana interfejsu/VPN, panel/eksporty, następnie laboratorium port/VLAN/uplink/awaria. Bez rozbudowanej warstwy testowej i CI/CD. Nie testujemy ponownie kryptografii ani całych bibliotek.

Większy snapshot pozostaje próbą wydajnościową D14: 50 switchy, 1000 hostów, 20 VLAN-ów, 50 tys. obserwacji; cel 30 s na import/korelację, 5 s na widok infrastruktury i 1,5 GB łącznie aplikacja + karta przy minimum 6 GB RAM. Wartości mierzymy, nie traktujemy ich jako limitu produktu.

## 10. Struktura docelowa

```text
Maper sieci/
  README.md
  AGENTS.md
  docs/
    README.md
    WYMAGANIA_PROJEKTU.md
    PLAN_STARTOWY.md
    THIRD_PARTY_NOTICES.md
    poradniki/
    decisions/
    etap-1/
    etap-2/
    etap-3/
    archiwum/
  pyproject.toml
  third_party_licenses/
  prototypes/tools/                        # próby, nie gotowa aplikacja
  src/mapper/
    app.py
    discovery/                  # interfejsy, adapter OS, zakres, sondy
    collectors/                 # opcjonalne SNMP/SSH
    topology/
    storage/
    ui/
  examples/snapshots/
  tests/critical/
```

Rzeczywiste dane poza repozytorium. Istniejące ręcznie utworzone próby w `prototypes/tools/` pozostają robocze; aktualizacja dokumentów ich nie przenosi ani nie nadpisuje. Układ `tools/` w poradniku jest układem docelowym próby. Nie deklarujemy gotowego skanera na podstawie samych dokumentów.

## 11. Pozostałe zadania

Stan przekazania Etapu 1 i dostępność dowodów zapisujemy w zadaniu 2.0 nowego planu; nie powtarzamy całego odbioru tylko z powodu rozpoczęcia następnego etapu.

Nie otwieramy ponownie zatwierdzonych D01–D14. Sprawdzamy nowe szczegóły: zgodność `psutil`, parsery tras/sąsiadów i wywołania ping na obu OS, zachowanie cache i Wi-Fi oraz proponowane krótkie deadline'y. Wersje przypinamy dopiero po próbie.

Do wykonania pozostają materiały laboratoryjne SNMPv3/SSH, źródło OUI i warunki zależności, rzeczywiste zasoby stanowisk oraz przypadki VRF/LAG/stack/MLAG. Nazwy przez aktywne DNS/mDNS, bezpośrednie sondy ARP wymagające uprawnień, dodatkowe parsery SSH i Linux mogą być rozszerzeniami po podstawowym MVP.

Instrukcje: [Etap 0](poradniki/ETAP_0_USTALENIA.md), [karta decyzji](poradniki/KARTA_ETAP_0.md), [Etap 1 — komponenty](poradniki/ETAP_1_PROBA_KOMPONENTOW.md), [Etap 1 — odkrywanie podstawowe](poradniki/ETAP_1_ODKRYWANIE_PODSTAWOWE.md).

Wynik Etapu 3: [raport](etap-3/RAPORT_ETAP_3.md), [instrukcja uruchomienia](poradniki/ETAP_3_URUCHOMIENIE_I_ODBIOR.md), decyzja `ADR-003`. Bez nowych sond podczas implementacji i odbioru.
