# Etap 2 — szczegółowy plan modelu danych i kolektorów

Projekt: **Maper sieci — własna aplikacja z darmowych komponentów**.

Data: 23 października 2026 r. Status: **zatwierdzony; implementacja gotowa do odbioru offline 23 października 2026 r.**. [Instrukcja uruchomienia](ETAP_2_URUCHOMIENIE_I_ODBIOR.md), [raport](../etap-2/RAPORT_ETAP_2.md).

Podstawa: [plan główny](../PLAN_STARTOWY.md), [wymagania](../WYMAGANIA_PROJEKTU.md) i [karta decyzji](KARTA_ETAP_0.md). Użytkownik zgłosił zakończenie Etapu 1 i poprosił o plan kolejnego etapu. Przyjmujemy to zgłoszenie jako podstawę dalszego planowania. Nie oznacza ono, że Codex samodzielnie wykonał lub zweryfikował wszystkie próby protokołów i systemów.

## 1. Rezultat etapu

Po Etapie 2 aplikacja potrafi uruchomić kontrolowany cykl, zebrać dane z dostępnych źródeł i trwale zapisać je w osobnej bazie projektu. Po ponownym uruchomieniu odczytuje ten sam snapshot bez ponownego skanowania.

Obowiązują dwie ścieżki jednej aplikacji:

| Ścieżka | Wejście | Wynik Etapu 2 |
|---|---|---|
| Podstawowa | Projekt, wybrany interfejs IPv4, lokalny zakres; bez seedów i sekretów | Obserwacje interfejsów, tras/bramy, sąsiadów/cache oraz ograniczonych sond |
| Rozszerzona | Opcjonalne seedy i przypisane profile SNMPv2c/v3 lub obsługiwanego SSH | IF, ARP, FDB, VLAN i LLDP w dostępnym zakresie, ze statusem każdego źródła |

Obie ścieżki zapisują ten sam format obserwacji. Brak SNMP/SSH w routerze domowym nie blokuje podstawowego cyklu. Nieznany port/VLAN pozostaje nieustalony.

**Granica etapu:** budujemy wiarygodną warstwę danych. Algorytm wyboru najbliższego portu hosta, confidence przypisania, rozpoznawanie uplinków, końcowe scalanie tożsamości i historia zmian należą do Etapu 3. Pełne formularze i panel produkcyjny należą do Etapu 4. Zostawiamy działający panel próbny.

## 2. Stan wejścia i krótki odbiór przekazania

Etapu 1 nie powtarzamy. Przed implementacją wystarczy zapisać jego wynik i odnaleźć działający kod.

W katalogu dostępnym przy opracowaniu tego planu istnieją venv, snapshot panelu i robocze pliki `prototypes/tools/`. Nie ma jeszcze `src/mapper/`, raportu Etapu 1 ani widocznego w tym katalogu modułu podstawowego odkrywania. Pliki `probe_snmp.py` i `probe_ssh.py` są puste. Nie przesądza to o wynikach użytkownika wykonanych w innym miejscu.

Zadanie 2.0:

1. Zapisz krótki `docs/etap-1/RAPORT_ETAP_1.md`: wynik panelu, podstawowego skanowania, protokołów, wersje i rzeczywiście sprawdzone OS. Nie dopisuj fikcyjnego sukcesu brakującej próby.
2. Wskaż i przenieś lub skopiuj sprawdzony kod Etapu 1 do katalogu głównego projektu. Zachowaj wersję roboczą do porównania; nie nadpisuj jej w ciemno.
3. Zapisz konkretne wersje zależności z działającego środowiska i istniejące informacje licencyjne. Nie aktualizuj bibliotek tylko dlatego, że zaczynamy nowy etap.
4. Jeżeli zgłoszone zakończenie obejmowało wyłącznie panel/bazę, zapisz brak podstawowego kolektora jako jawne zadanie wejściowe. Jego uzupełnienie jest niezbędne do wyniku podstawowego i może zwiększyć szacunek Etapu 2; nie ukrywamy go pod „integracją”.

Brak laboratorium SNMP/SSH nie blokuje projektu podstawowej bazy ani pracy nad adapterami na próbkach. Odczyty rzeczywiste wymagają istniejącego celu, profilu i zakresu operatora; samo przygotowanie planu nie uruchamia żadnych sond.

## 3. Kolejność prac i nakład

| Krok | Zadanie | Dostarczany wynik | Orientacyjny nakład |
|---|---|---|---|
| 2.0 | Przekazanie wyników Etapu 1 i kodu | Krótki raport, sprawdzone pliki i wersje | 0,25 dnia |
| 2.1 | Kontrakt obserwacji i statusów | Typy danych, walidacja i 2–3 próbki | 0,5 dnia |
| 2.2 | SQLite i izolacja projektów | Schemat v1, zapis/odczyt, migracja, publikacja snapshotu | 0,75 dnia |
| 2.3 | Podstawowy kolektor i kontroler | Istniejący skaner włączony do cyklu i trwałego zapisu | 0,75 dnia |
| 2.4 | Kolektor SNMP | Ograniczone odczyty i normalizacja wymaganych tabel | 1–1,5 dnia |
| 2.5 | Pierwszy adapter SSH | Odczytowe polecenia i wspólny model wyników | 0,5 dnia |
| 2.6 | Replay, odporność i krótki odbiór | Wyniki scenariuszy, snapshoty i raport etapu | 0,5–0,75 dnia |

Łącznie orientacyjnie **4–6 dni pracy**, jeśli kod podstawowego odkrywania jest dostępny po Etapie 1, a próbki i urządzenia do protokołów są przygotowane. To szacunek dla jednej osoby; nie obejmuje odtwarzania niewykonanego skanera, oczekiwania na sprzęt ani dopisywania wielu platform SSH. Pierwszy system: macOS ARM, potem krótki odbiór Windows x64 w uzgodnionym zakresie.

Pracujemy w tej kolejności, aby najpierw uzyskać trwały wynik zwykłego LAN. Każdy krok kończy się małym działającym wynikiem; zatwierdzenie całego Etapu 2 następuje po przedstawieniu raportu, przed Etapem 3.

## 4. Struktura kodu

Docelowy układ jest propozycją modułów, a nie listą pustych plików do utworzenia na zapas:

```text
src/mapper/
  __init__.py
  __main__.py
  models.py                    # kontrakty obserwacji i statusów
  config.py                    # projekt, zakresy i odwołania do profili
  cycle.py                     # kolejność, limity, anulowanie, podsumowanie
  discovery/
    basic.py                   # adaptacja działającego skanera
    platform_macos.py
    platform_windows.py
  collectors/
    snmp.py                    # wyłącznie odczyty
    snmp_tables.py             # indeksy i mapowanie potrzebnych tabel
    ssh.py                     # pierwszy sprawdzony profil platformowy
  storage/
    database.py                # połączenia i transakcje
    repository.py              # zapis/odczyt cykli i obserwacji
    migrations/001_initial.sql
  snapshots.py                 # import/eksport i walidacja
tests/critical/                # niewielki zestaw newralgicznych przypadków
examples/snapshots/            # tylko syntetyczne lub zanonimizowane dane
docs/etap-2/RAPORT_ETAP_2.md
```

Nie dodajemy mikroserwisów, ORM, osobnego serwera bazy, FastAPI, Celery ani CI/CD. Wystarczą biblioteka standardowa, komponenty przyjęte wcześniej i niewielkie moduły własnego Pythona. Przeniesienie kodu z prób nie może zmienić potwierdzonego zachowania bez uzasadnienia.

## 5. Konfiguracja projektu i danych

Każda sieć ma osobny katalog danych użytkownika:

```text
MapperSieci/projects/<project_id>/
  project.json
  mapper.sqlite3
  snapshots/
```

Proponowane domyślne położenie: macOS `~/Library/Application Support/MapperSieci/projects/`; Windows `%LOCALAPPDATA%\MapperSieci\projects\`. Dopuszczamy jawne `--data-dir`. Nie zakładamy, że katalog roboczy programu jest miejscem danych. Nie używamy folderu sieciowego lub synchronizowanego jako domyślnej lokalizacji SQLite.

`project_id` to UUID, nazwa wyświetlana jest osobnym polem. Identyfikator walidujemy przed utworzeniem ścieżki. Nazwa hosta czy podsieci nie staje się nazwą pliku. Ten sam adres IP w drugim projekcie nie współdzieli żadnej tożsamości ani profilu.

`project.json` zawiera: wersję formatu, ID i nazwę projektu, wybrany interfejs/scope, dozwolone zakresy, limity, opcjonalne seedy, mapowanie target → profile ID oraz nazwy zmiennych ENV. Nie zawiera haseł, community ani prywatnego klucza. Adresacja projektu pozostaje prywatnymi danymi nawet bez haseł.

MVP ma jednego operatora i jeden aktywny cykl. Przed rozpoczęciem sprawdzamy zakres oraz już trwający cykl; drugie uruchomienie nie wykonuje równoległego zbierania do tej samej bazy. Zmiana Wi-Fi, adresacji lub VPN w trakcie cyklu wstrzymuje sondowanie i oznacza niepełny wynik; aplikacja nie przełącza projektu automatycznie na inną sieć.

## 6. Wspólny model obserwacji

### 6.1. Oddzielamy obserwację od interpretacji

Obserwacja mówi „źródło zwróciło X w czasie T”. Nie mówi jeszcze „to jeden fizyczny komputer” albo „host jest bezpośrednio w porcie 3”. To rozstrzygnie Etap 3.

Własne typy można zrealizować przez `dataclasses` i `Enum`; nie dokładamy biblioteki modelowania bez potrzeby. Pola tabel są typowane w kontrakcie Pythona. W SQLite wspólna koperta jest kolumnami, a mały, walidowany rekord konkretnego rodzaju jest JSON-em. Nie budujemy kilkunastu niemal identycznych tabel ani nie wrzucamy całych surowych odpowiedzi do jednego niekontrolowanego JSON-a.

| Pole wspólne | Znaczenie |
|---|---|
| `observation_id` | UUID obserwacji |
| `project_id`, `cycle_id`, `collector_run_id` | Projekt, cykl i konkretne źródło/tabela |
| `kind`, `source` | Rodzaj faktu i np. `os_neighbors`, `icmp`, `snmp`, `ssh` |
| `source_key` | Deterministyczny klucz rekordu wewnątrz odczytu, np. indeks wiersza MIB |
| `source_target_id` | Źródłowe urządzenie zarządzające, jeśli istnieje; nie tożsamość końcowego hosta |
| `scope_id`, `context_id` | Lokalny segment/interfejs i kontekst/VRF, jeśli rozpoznany |
| `context_status` | `known`, `default` lub `unknown`; brak wiedzy nie scala różnych VRF |
| `observed_at` | Czas odebrania/odczytania danych, UTC |
| `freshness` | `fresh`, `cached`, `unknown` |
| `evidence_at` | Czas rzeczywistego dowodu odpowiedzi/zmiany, jeśli źródło go dostarcza; inaczej `null` |
| `payload` | Tylko pola dopuszczone dla danego `kind`, bez obiektów dostępu i sekretów |

`observed_at` ponownego odczytu cache nie przesuwa automatycznie czasu widzenia hosta. `fresh` dla nowo odebranej tabeli oznacza świeżość odczytu, a nie świeżą odpowiedź każdego hosta z tej tabeli. Dla wpisów cache zachowujemy ich dostępny stan i nie udajemy przechwyconej odpowiedzi ARP.

### 6.2. Minimalne rodzaje faktów

| `kind` | Najważniejsze pola `payload` |
|---|---|
| `local_interface` | systemowy identyfikator interfejsu, IPv4, maska, stan |
| `route` | prefiks, next hop, interfejs, dostępna metryka |
| `neighbor` | IPv4, MAC lub `null`, interfejs, stan wpisu, moment odczytu cache |
| `probe_result` | cel IPv4, interfejs, wynik: odpowiedź/brak odpowiedzi/błąd/pominięty |
| `device_identity` | sysName/sysObjectID/sysDescr lub odpowiednik CLI; tylko dozwolone pola |
| `interface` | `ifIndex`, nazwa, alias, stan; źródłowy indeks nie staje się globalnym ID |
| `ip_mac` | IPv4, MAC, źródłowy interfejs i dostępny stan wpisu ARP |
| `bridge_port_map` | bridge port → `ifIndex` w konkretnym źródle/kontekście |
| `fdb_entry` | MAC, bridge port, FDB ID lub `null`, status, VLAN tylko gdy rzeczywiście znany |
| `vlan` | VLAN ID, nazwa, konfiguracja/bieżący stan i dostępne powiązanie FDB ID |
| `port_vlan` | bridge port, PVID, tagowane/nietagowane członkostwo według dostępnych danych |
| `lldp_neighbor` | lokalny identyfikator portu i subtype, zdalny chassis/port ID i subtype, nazwa/adres zarządzający jeśli dostępne |

MAC normalizujemy do jednego zapisu. IPv4 walidujemy, liczby i stany konwertujemy jawnie, nieznane wartości mają `null`/opis stanu. Oryginalny indeks tabeli i rodzaj identyfikatora zachowujemy. Nie wyznaczamy VLAN-u z adresu podsieci. Pole trybu portu może być `unknown`; członkostwo VLAN nie zawsze daje jedną uniwersalną etykietę access/trunk.

Przykład syntetycznej obserwacji FDB, bez przypisania hosta do fizycznego portu:

```json
{
  "schema_version": 1,
  "kind": "fdb_entry",
  "source": "snmp",
  "source_target_id": "seed-a",
  "scope_id": "lab-a",
  "context_id": "",
  "context_status": "default",
  "observed_at": "2026-10-23T10:00:00Z",
  "freshness": "fresh",
  "evidence_at": null,
  "source_key": "fdb:7:02:00:00:00:00:01",
  "payload": {
    "mac": "02:00:00:00:00:01",
    "fdb_id": 7,
    "bridge_port": 12,
    "if_index": null,
    "vlan_id": null,
    "status": "learned"
  }
}
```

To fragment kontraktu: repozytorium nadaje identyfikatory projektu, cyklu, uruchomienia i obserwacji. `fdb_id=7` nie jest dowodem VLAN 7. Mapowanie bridge portu i listę powiązanych VLAN-ów zapisujemy oddzielnie, zamiast modyfikować fakt źródłowy.

## 7. SQLite: mały schemat, trwałość i izolacja

### 7.1. Tabele wersji 1

| Tabela | Główne kolumny i odpowiedzialność |
|---|---|
| `project_meta` | Jeden projekt: `project_id`, nazwa, data utworzenia; zgodność ID z konfiguracją przy otwarciu |
| `collection_targets` | `target_id`, adres/port zarządzający i kontekst, pochodzenie seed/LLDP, profil ID bez sekretu; to punkty odczytu, nie gotowa inwentaryzacja hostów |
| `cycles` | `cycle_id`, `project_id`, start/koniec, stan wykonania, pokrycie, zakres i budżet, hash konfiguracji bez sekretów, powód zatrzymania |
| `collector_runs` | `collector_run_id`, cykl, źródło/target, tabela/komenda, scope/kontekst, czasy, status, liczby rekordów, ucięcie i bezpieczny kod błędu |
| `observations` | Wspólna koperta z sekcji 6 i `payload_json`; tylko rekordy zwalidowane |
| `snapshots` | `snapshot_id`, `cycle_id`, wersja formatu, czas publikacji i kompletność; odniesienie do zapisanych obserwacji, bez drugiej kopii całej bazy |

Zależności: projekt → cykle → odczyty → obserwacje; snapshot wskazuje cykl. Odczyt źródłowy jest przypisany do kontekstu, a nie tylko IP. Gdy ten sam indeks pojawia się w innym źródle/kontekście, nie zastępuje wcześniejszego rekordu.

Indeksy początkowe: cykle po projekcie/czasie; odczyty po cyklu/target/statusie; obserwacje po cyklu/rodzaju i source run. Klucz unikalny rekordu: `collector_run_id + kind + source_key`. Potrzebne do późniejszego wyszukiwania IP/MAC można dodać jako jawne kolumny indeksowane podczas implementacji, bez skanowania wszystkich JSON-ów w panelu. Brak globalnej unikalności samego IP lub MAC.

### 7.2. Zapis i publikowanie

1. Utwórz bazę i zastosuj `001_initial.sql`. Wersję schematu trzymaj przez `PRAGMA user_version`.
2. Przy każdym połączeniu włącz `PRAGMA foreign_keys=ON`, zanim rozpocznie się transakcja. Korzystaj z parametryzowanych zapytań. [SQLite — klucze obce](https://www.sqlite.org/foreignkeys.html)
3. Zapis koordynuje jeden właściciel połączenia, przez ograniczoną kolejkę partii. Kolektory nie współdzielą dowolnie tego samego obiektu połączenia między wątkami. Kolejka ma limit, żeby spowolnienie dysku nie wyczerpało RAM.
4. Obserwacje zapisuj porcjami w krótkich transakcjach; nie trzymaj transakcji przez kilkugodzinny cykl. Częściowe dane mają odniesienie do bieżącego, nieopublikowanego cyklu.
5. Na końcu jedną krótką transakcją zakończ cykl i dodaj wpis snapshotu. Widok domyślny korzysta z ostatniego opublikowanego snapshotu, nie z połowy zapisywanej tabeli. [SQLite — transakcje](https://www.sqlite.org/lang_transaction.html)
6. Można opublikować snapshot częściowy, ale ma jawny status i nie zastępuje informacji o ostatnim kompletnym wyniku. Zapytania rozróżniają „ostatni opublikowany” i „ostatni kompletny w tym zakresie”.
7. Po awarii procesu cykl pozostawiony jako `running` oznacz przy następnym starcie jako `interrupted`. Nie publikuj go automatycznie jako kompletnego. Ukończony wcześniejszy snapshot pozostaje dostępny.

Migracje są sekwencyjne i niewielkie; nie wprowadzamy frameworka migracji. Przed zmianą istniejącej bazy wykonaj kopię przez mechanizm SQLite backup; nie kopiuj w ciemno wyłącznie pliku aktywnej bazy. Nie dodawaj WAL bez pomiaru potrzeby; pierwszą wersję uprość do jednego zapisującego i krótkich odczytów.

Retencja z karty pozostaje: snapshoty 7 dni, historia docelowo 90 dni, budżet 2 GB/projekt. W Etapie 2 liczymy zajętość i sprzątamy jedynie kwalifikujące się stare obserwacje/snapshoty bez uszkadzania ostatniego poprawnego wyniku. Zdarzenia historii powstaną w Etapie 3; nie tworzymy fikcyjnej historii z samych braków odpowiedzi.

## 8. Kontroler cyklu i znaczenie statusów

### 8.1. Status nie jest jednym polem „sukces”

Cykl ma osobno:

- `execution_status`: `queued`, `running`, `finished`, `cancelled`, `interrupted`, `failed`;
- `coverage_status`: `complete`, `partial`, `unknown`, zawsze względem zaplanowanego zakresu i źródeł;
- podsumowanie: liczba celów planowanych/wykonanych/pominiętych, rekordów i błędów, przyczyna zatrzymania.

Zakończony proces nie oznacza kompletnej mapy. Poprawnie zakończony podstawowy cykl nie deklaruje znajomości wszystkich hostów w sieci. SNMP nie jest brakującym źródłem w cyklu, w którym nie został włączony.

Każda tabela/komenda ma osobny wynik: `ok`, `empty`, `partial`, `unsupported`, `auth_error`, `timeout`, `transport_error`, `parse_error`, `cancelled` lub `not_requested`. Dodatkowo zapisujemy, czy odczyt do końca źródła rzeczywiście się zakończył.

Pusta tabela po pełnym, poprawnym odczycie to `empty`; pusta lista po błędzie parsera to `parse_error`. Timeout nie dowodzi braku obsługi MIB. `unsupported` wymaga odpowiedniej odpowiedzi agenta lub potwierdzonego ograniczenia profilu, a nie domysłu. Jeśli zaplanowane źródło było niedostępne/ucięte/nieobsługiwane, cykl ma niepełne pokrycie, mimo poprawnego działania pozostałych źródeł.

### 8.2. Przebieg

Walidacja projektu/zakresu → rejestracja cyklu → plan źródeł → kolektory → walidacja i zapis partii → statusy odczytów → transakcyjna publikacja → podsumowanie. Błąd jednego targetu nie kończy pozostałych.

Budżety czasu mierzymy zegarem monotonicznym, daty dowodów zapisujemy w UTC. Zmiany konfiguracji i anulowanie zatrzymują nowe zadania. Procesy ping są sprzątane. Wątku blokującego SSH nie traktujemy jako zakończonego tylko dlatego, że anulowano oczekujące zadanie; obowiązują timeouty transportu/komendy i zamknięcie sesji.

## 9. Kolektor podstawowy

Adaptujemy sprawdzony kod Etapu 1 zamiast pisać drugi skaner.

1. Zamień bezpośrednie drukowanie wyniku na emitowanie walidowanych obserwacji i postępu.
2. Zachowaj odczyt interfejsów, tras, sąsiadów przed/po i wyniki pojedynczych sond. Brak odpowiedzi oraz błąd wykonania to różne stany.
3. Potwierdzaj trasę przez wybrany interfejs przed sondowaniem, szczególnie przy VPN. Nie przypisuj MAC bramy do hosta poza lokalnym L2.
4. Zachowaj stan i świeżość wpisów cache; drugi odczyt tego samego wpisu nie aktualizuje dowodu obecności.
5. Uzupełnij współpracę z limitem, anulowaniem, kolejką zapisu i statusem pokrycia.
6. Zapisz, zamknij proces, otwórz bazę ponownie i odczytaj te same obserwacje bez ruchu sieciowego.

Wejście podstawowe nie wymaga danych SNMP/SSH. Logiczne grupowanie segmentu może nadal korzystać z próbnego renderera; nie dodajemy fizycznych portów bez dowodów. Nazwy/OUI mają wartość nieustaloną, jeśli nie ma dopuszczonego lokalnego źródła; ich brak nie blokuje kolektora.

## 10. Kolektor SNMP

### 10.1. Jeden transport i lista potrzebnych tabel

PySNMP pozostaje silnikiem protokołu. Tworzymy ograniczony adapter GET/GETNEXT/GETBULK, bez SET i bez automatycznego pobierania MIB-ów. Profile v2c/v3 z karty pozostają jawnie przypisane do targetów; bez zgadywania community i automatycznego osłabiania v3.

| Kolejność | Źródło | Zapisany fakt |
|---|---|---|
| 1 | `sysName`, `sysObjectID`, `sysDescr`, `sysUpTime` | Identyfikacja źródła i znacznik ponownego uruchomienia |
| 2 | IF-MIB: `ifTable`, `ifXTable` | Nazwy, aliasy i stany interfejsów |
| 3 | `ipNetToPhysicalTable`, zgodnościowo `ipNetToMediaTable` | IPv4–MAC, interfejs i dostępny stan wpisu |
| 4 | `dot1dBasePortTable` | Bridge port → `ifIndex` |
| 5 | `dot1qTpFdbTable`, zgodnościowo `dot1dTpFdbTable` | MAC → bridge port, FDB ID i stan |
| 6 | `dot1qVlanCurrentTable`, `dot1qVlanStaticTable`, `dot1qPvid` | Bieżące/konfiguracyjne członkostwo i dostępne powiązania VLAN |
| 7 | Lokalne i zdalne obiekty LLDP-MIB oraz adresy zarządzające | Dane sąsiadów i identyfikatorów portów |

Na start implementujemy tylko niezbędne kolumny tych tabel, nie całą MIB. Numeryczne OID i indeksowanie zapisujemy w jednym module; sprawdzamy je względem definicji, nie kopiujemy przypadkowych OID z Internetu.

### 10.2. Reguły normalizacji

- IP-MIB obsługuje różne typy adresów; ten projekt przyjmuje z niej wyłącznie IPv4. Zachowaj typ i źródłowy indeks, a odrzucone typy policz. [RFC 4293](https://www.rfc-editor.org/rfc/rfc4293)
- Bridge port i `ifIndex` nie są zamienne. Zapisz oddzielne mapowanie `dot1dBasePortIfIndex`; brak mapowania nie jest powodem wymyślenia nazwy interfejsu. Wpis FDB z portem 0 nie wskazuje zwykłego fizycznego portu. [RFC 4188](https://www.rfc-editor.org/rfc/rfc4188)
- FDB ID nie zawsze jest VLAN ID. Zachowaj powiązania z `dot1qVlanCurrentTable`, jego indeks czasu i możliwość współdzielenia FDB. Odróżnij konfigurację statyczną od bieżącego członkostwa. Bitmapy portów dekoduj według bridge portów, od najbardziej znaczącego bitu pierwszego oktetu. PVID nie jest pełnym opisem trunku. [RFC 4363](https://www.rfc-editor.org/rfc/rfc4363)
- Przy zwykłym BRIDGE-MIB bez potwierdzonego kontekstu VLAN pozostaw VLAN nieustalony. Konteksty producenta odczytuj tylko według jawnie obsługiwanego profilu, bez dopisywania VLAN-u do community na próbę.
- LLDP zachowuje lokalne/zdalne subtype identyfikatorów; numer lokalnego portu LLDP nie staje się automatycznie `ifIndex`. Brak jednoznacznego mapowania pozostaje brakiem.

### 10.3. Ograniczone walki i rekurencja

Walk kończy się po opuszczeniu poddrzewa, końcu tabeli, błędzie, anulowaniu albo budżecie. Kontrolujemy rosnące OID; powtarzające się odpowiedzi nie mogą powodować nieskończonej pętli. Rekordy przekazujemy porcjami, nie trzymamy wszystkich surowych tablic w RAM.

LLDP dodaje do kolejki wyłącznie IPv4 zarządzające w dozwolonym zakresie i z przypisanym profilem. Deduplikacja uwzględnia projekt, endpoint i kontekst. Liczba przejść i urządzeń jest ograniczona; adres hosta z ARP nie uruchamia automatycznego logowania SNMP/SSH.

Odczyt uptime przed/po większym zestawie pomaga wykryć restart w trakcie. Taki zestaw oznacz jako potencjalnie niespójny. Nawet bez restartu tablice z różnych chwil nie są jednym atomowym obrazem urządzenia — zachowujemy czas każdego źródła.

## 11. Pierwszy adapter SSH

Zakres: przyjęty profil `cisco_ios` i dostępna, sprawdzona rodzina IOS XE. To pierwszy adapter kolektora, nie warunek obsługi podstawowego LAN.

1. Przenieś sprawdzony odczyt z Etapu 1 do adaptera Netmiko. Jeśli nie ma kodu lub próbki, zapisz brak zamiast traktować pusty skrypt jako wynik.
2. Użyj zamkniętej listy odczytów z karty: identyfikacja, MAC, ARP, VLAN, interfejsy i LLDP; agregację tylko jeśli potrzebna do dostępnego przypadku. Bez `enable()`, konfiguracji i zapisu.
3. Sprawdź polecenia przygotowania sesji przypiętego sterownika, weryfikuj klucz hosta, wyłącz surowe logowanie sesji. Lista poleceń pochodzi z profilu aplikacji, nie z dowolnego tekstu operatora.
4. Używaj istniejących szablonów. Wynik tekstowy zamiast oczekiwanych rekordów oznacza niepotwierdzone parsowanie; jawnie sprawdź pola MAC/port/VLAN i wymagany kontekst.
5. Znormalizuj rezultat do tych samych rodzajów obserwacji co SNMP. Sprzeczne źródła zachowaj oddzielnie, bez cichego nadpisania i bez automatycznego wyboru „prawdy”.

Pusta poprawnie sparsowana tabela jest odrębnym wynikiem. Nieobsługiwane polecenie i błąd uprawnień to inne statusy. Przy błędzie SNMP nie próbujemy automatycznie SSH, chyba że profil targetu jawnie dopuszcza tę ścieżkę. Parsery kolejnych producentów dopisujemy później na podstawie próbek.

## 12. Limity i odporność

| Obszar | Parametry startowe |
|---|---|
| Podstawowe cele | Do 256 adresów, 5 nowych celów/s, jedna sonda na adres; jawna zmiana budżetu |
| Podstawowe procesy | Propozycja z planu: 4 ping równolegle, 3 s/proces, 5 s na odczyt systemowy, 240 s/próbę; zachowaj korekty zmierzone w Etapie 1 |
| Zarządzające urządzenia | 4 równolegle, maksymalnie 2 sesje SSH |
| SNMP | 3 s, jedno ponowienie, jedno aktywne żądanie na target; GETBULK startowo 20 |
| Walk | 60 s lub 50 tys. rekordów; pierwszy osiągnięty limit |
| Urządzenie zarządzające | 5 min lub 200 tys. rekordów |
| SSH | Connect 10 s, auth/banner 15 s, komenda 30 s; bez ponawiania błędnego hasła |
| Rekurencja/cykl | 500 zarządzających urządzeń, 8 przejść, cykl do 4 h |

Są to budżety pracy, nie licencyjne limity produktu. Nie przesyłamy surowych wyjątków, obiektów profili ani sekretów do logów i eksportu. Dopuszczone operacje oraz błędy mają krótkie kody; szczegóły diagnostyczne są kontrolowane.

Przy niedostępnym źródle zapisujemy status i kontynuujemy pozostałe. Wynik częściowy nie usuwa danych poprzedniego snapshotu i nie generuje zdarzenia zniknięcia. Przy pełnym dysku wycofujemy nieudaną transakcję, pozostawiamy poprzedni opublikowany wynik i zgłaszamy błąd zapisu. Nie kasujemy chronionych danych, żeby ukryć problem.

## 13. Snapshot, import i odtwarzanie

Format `schema_version=1` zawiera: `project_id`, identyfikatory/czasy cyklu, planowany scope, budżet bez sekretów, wyniki źródeł, obserwacje, pokrycie i ostrzeżenia. To snapshot danych wejściowych dla Etapu 3, nie wyłącznie lista węzłów Cytoscape.

Eksport jest tworzony z ostatniego wybranego, opublikowanego snapshotu. JSON zachowuje rodzaje faktów i konteksty. CSV na tym etapie wystarczy jako diagnostyczny eksport obserwacji; docelowe eksporty mapy pozostają zadaniem panelu. Graf próbny może dostać osobny prosty adapter, bez uzależniania kolektorów od formatu renderera.

Import:

1. Sprawdź wersję, strukturę, rozmiar pliku i limity rekordów. Nie wykonuj zawartych poleceń, nie rozwiązywaj adresów i nie otwieraj sesji sieciowych.
2. Waliduj pola według rodzajów obserwacji; nie zapisuj dowolnego obiektu źródłowego. Nieznaną wersję odrzuć z czytelnym komunikatem.
3. Przy innym projekcie importuj do nowego projektu lub przez jawne mapowanie ID; nie mieszaj danych automatycznie. Zachowaj pochodzenie `imported` i pierwotne czasy; nie udawaj świeżego skanu.
4. Zapisz transakcyjnie i odtwórz po ponownym uruchomieniu, bez jakiegokolwiek ruchu kolektorów.

Rzeczywiste snapshoty są prywatne. Próbki w repozytorium mają syntetyczne adresy/MAC i spójne relacje. Proponowany początkowy limit importu: 100 MiB i 200 tys. obserwacji, konfigurowalny; to nowy bezpiecznik do oceny, nie uzgodniony wcześniej limit produktu. Import większy od limitu nie jest po cichu ucinany.

## 14. Minimalne sprawdzenia — bez rozbudowanej warstwy testowej

Nie tworzymy CI/CD ani pełnej macierzy bibliotek. Wystarczy kilka scenariuszy z małymi fixture'ami; łączymy pokrewne reguły zamiast pisać test dla każdej funkcji.

| Krytyczny scenariusz | Ochrona |
|---|---|
| Dwa projekty z tym samym IP; ten sam MAC w innych kontekstach | Brak scalenia i zapisu do niewłaściwej bazy |
| Cache odczytany ponownie; brak ICMP | Brak fałszywej świeżej obecności, brak wymyślonego portu/VLAN-u |
| Bridge port różny od `ifIndex`; FDB ID współdzielony; bitmapa | Normalizacja zachowuje indeksy i nie produkuje fałszywego VLAN-u |
| Pusta tabela, timeout, ucięcie, nieobsługiwany obiekt i błąd parsera | Różne statusy i prawidłowe pokrycie |
| Anulowanie/awaria przed publikacją i ponowny start | Poprzedni snapshot działa; brak fałszywie kompletnego wyniku |
| Zapis → odczyt → eksport/import offline | Zachowane fakty, konteksty i czasy; zero wywołań transportu w replay |
| Atrapa transportu i kontrolowany sekret testowy | Brak SET/komend konfiguracji; brak sekretu w bazie, logach i eksporcie |

Nie testujemy ponownie kryptografii PySNMP, SQLite ani wszystkich parserów dostawcy. Nowy własny parser lub niejednoznaczny indeks wymaga tylko odpowiadającej mu małej próbki. Rzeczywiste dane klientów nie trafiają do fixture'ów.

Ręczny odbiór: lokalny LAN bez SNMP/SSH; restart i odczyt bazy; jeden niedostępny target; anulowanie; następnie dostępny agent v2c/v3 i jeden adapter SSH. Na Windows sprawdzamy adapter OS, zapis/odczyt i uruchomienie zgodnie z D01, z jawnym wynikiem każdej dostępnej wersji OS. Braku stanowiska lub urządzenia nie zastępujemy deklaracją sukcesu.

## 15. Proponowany interfejs uruchamiania

W Etapie 2 wystarczy CLI, zanim powstanie pełny panel. Poniższe polecenia są **kontraktem do implementacji**, a nie informacją o obecnie istniejących modułach:

```text
python -m mapper project create --name "Laboratorium" --data-dir <katalog>
python -m mapper collect --project <UUID> --config <project.json> --preview
python -m mapper collect --project <UUID> --config <project.json> --run
python -m mapper snapshot list --project <UUID>
python -m mapper snapshot export --project <UUID> --cycle <UUID> --output <plik.json>
python -m mapper snapshot import --new-project --input <plik.json>
```

`--preview` odczytuje jedynie potrzebne informacje lokalne i prezentuje plan; nie wysyła sond ani SNMP/SSH. `--run` rozpoczyna jawnie wybrany zakres. Brak profili oznacza podstawową ścieżkę, a nie błąd konfiguracji. Po implementacji dodaj entry point pakietu i rzeczywiste przykłady macOS/Windows do raportu; same polecenia w planie jeszcze nie działają.

## 16. Odbiór Etapu 2

| ID | Warunek |
|---|---|
| E2-01 | Nowy projekt tworzy oddzielną konfigurację i bazę z właściwą wersją schematu |
| E2-02 | Podstawowy cykl nie wymaga seedów/community i zapisuje źródła, zakres, czasy i statusy |
| E2-03 | Po zamknięciu i ponownym uruchomieniu można odczytać opublikowany snapshot bez skanowania |
| E2-04 | Drugi projekt z tą samą adresacją nie miesza żadnych danych i profili |
| E2-05 | Każdy wymagany rodzaj danych SNMP ma adapter, normalizację i wynik próby: rzeczywisty lub jawnie ograniczony do fixture'u |
| E2-06 | Dostępny profil v2c/v3 i pierwszy SSH mają zapisany rzeczywisty wynik; niewykonane próby pozostają luką |
| E2-07 | Błąd targetu, timeout i ucięcie nie blokują reszty i nie udają kompletnego pokrycia |
| E2-08 | Anulowanie i przerwanie nie uszkadzają poprzedniego snapshotu; brak automatycznej historii zniknięć |
| E2-09 | Eksport/import zachowuje kontekst i świeżość, replay nie używa sieci, sekrety są wykluczone |
| E2-10 | Istnieje krótki raport z wersjami, wynikami krytycznych sprawdzeń, OS i pozostałymi lukami |

Brak sprzętu do odczytu zarządzającego nie blokuje E2-01–04 i podstawowego zapisu. Jeżeli część rozszerzona jest potwierdzona tylko na próbkach, raport nazywa wynik częściowym. Przejście do Etapu 3 może objąć taki jawnie ograniczony wynik po decyzji użytkownika; nie przedstawiamy go jako pełnego odbioru online.

Szablon raportu do utworzenia podczas realizacji:

```markdown
# Raport Etapu 2

Data, wykonujący, OS/architektura:
Wersje Python/zależności i schematu:
Pochodzenie kodu i wyników Etapu 1:
Zakres próby, profile ID bez sekretów:

| Kryterium E2 | Wynik: OK / błąd / niewykonane | Dowód i ograniczenie |
|---|---|---|
| E2-01–04: baza, podstawowy cykl i izolacja | | |
| E2-05–06: SNMP/SSH i normalizacja | | |
| E2-07–08: błędy, limity, anulowanie | | |
| E2-09: replay i sekrety | | |
| E2-10: stanowiska i dokumentacja | | |

Czasy, liczby rekordów i szczytowe zużycie zasobów:
Niewykonane odczyty/platformy i wpływ na zakres:
Ocena: gotowy / częściowo gotowy / wymaga poprawy.
Decyzja użytkownika przed Etapem 3:
```

## 17. Decyzje do zatwierdzenia wraz z planem

Nie pytamy ponownie o stos, IPv4, lokalny panel, dwie ścieżki ani brak CI/CD. Nowe propozycje tego etapu to:

1. Lekki model koperty obserwacji z typowanym JSON-em oraz sześcioma tabelami SQLite, bez ORM.
2. Domyślne katalogi danych systemu i opcjonalne `--data-dir`.
3. Jeden zapisujący, krótkie transakcje i jawna publikacja kompletnego/częściowego snapshotu.
4. Wstępny limit importu 100 MiB/200 tys. rekordów, jawnie konfigurowalny.
5. Kolejność: trwały podstawowy LAN, SNMP, jeden adapter SSH, replay i krótki odbiór; bez pełnego silnika topologii i panelu produkcyjnego w tym etapie.

Plan zatwierdzono poleceniem użytkownika „ok zatwierdzam plan, dzialaj”. Zaimplementowany wynik i ograniczenia opisuje raport Etapu 2. Nie wykonano aktywnych odczytów sieci. Etap 3 czeka na zatwierdzenie wyniku Etapu 2.
