# Plan wdrożenia aplikacji odkrywającej topologię sieci

> Materiał historyczny: odrębny wariant Flutter/Dart. Nie określa bieżącego zakresu mappera Python. Aktualna dokumentacja: [spis treści](../../README.md).

Data: 11 października 2026. Status: propozycja do zatwierdzenia; dokument nie rozpoczyna implementacji.

## 1. Kierunek i ograniczenia projektu

Budujemy jedną aplikację desktopową Flutter/Dart. Operator uruchamia ją w kolejnych, wcześniej nieznanych sieciach, podaje adresy urządzeń startowych i poświadczenia, a aplikacja zbiera dostępne dane i tworzy mapę. Nie wymagamy wcześniejszej znajomości rozmiaru ani konfiguracji sieci.

Priorytetem jest użyteczne MVP w około 20 dniach roboczych, z rezerwą do 25 dni. To szacunek dla jednego doświadczonego wykonawcy pracującego w pełnym wymiarze, na jednej platformie docelowej, przy dostępie do urządzeń lub wiarygodnych snapshotów. Czekanie na sprzęt, odpowiedzi i zatwierdzenia wydłuża termin kalendarzowy. Szacunek nie obejmuje własnej implementacji protokołu SNMPv3.

Przyjmujemy:

- IPv4; IPv6 poza pierwszym wydaniem.
- Wyłącznie odczyty urządzeń. Bez SNMP SET, konfiguracji CLI i aktywnego sondowania podsieci.
- Topologię L2 oraz podstawową L3: urządzenia routujące, adresy interfejsów, podsieci i obserwowane relacje. Bez pełnej analizy routingu i ścieżek pakietów.
- Odporność na niepełne dane i niedostępne urządzenia.
- Osobny projekt dla każdej badanej sieci, również przy powtarzających się adresach IP.
- Brak CI/CD, mikroserwisów, chmury, panelu administracji użytkownikami i rozbudowanej infrastruktury testowej.
- Testy automatyczne tylko dla błędów mogących ujawnić sekret, wykonać zapis, błędnie przypisać hosta lub uszkodzić historię.

Wybór Flutter Desktop zamiast poprzedniej propozycji serwera i panelu webowego wymaga zatwierdzenia. Upraszcza uruchomienie i eliminuje osobny serwer API. Flutter wspiera aplikacje desktopowe na macOS, Windows i Linux [1]. Pierwsze wydanie otrzymuje jednak jeden system operacyjny i jedną uzgodnioną architekturę CPU; pozostałe po pierwszym odbiorze.

## 2. Zakres MVP i zakres odroczony

| Obszar | MVP | Później |
|---|---|---|
| Konfiguracja | Projekty sieci, seedy, profile dostępowe, interwał, limity, start/stop | Import dużej inwentaryzacji, automatyczne szablony klientów |
| SNMP | v2c/v3 przez Net-SNMP, publiczne API oddzielnej paczki Dart | Własny transport i protokół SNMP w czystym Darcie |
| Odkrywanie | Standardowe MIB-y, opcjonalna rekurencja LLDP, deduplikacja | CDP i rozbudowane rozszerzenia producentów |
| SSH | Jeden adapter IOS XE; drugi tylko w dostępnym budżecie lub po zamianie priorytetu | Aruba, Junos, Huawei, Arista, RouterOS, kolejne systemy |
| Dane | FDB, ARP, interfejsy, VLAN, PVID, LLDP, dostępna adresacja L3 | Pełne trasy, zaawansowane EVPN/VXLAN i rozpoznawanie MLAG |
| VRF/LAG/stack | Kontekst w modelu, dostępne informacje o agregacji i członkach; jawne ograniczenia | Pełna obsługa specyficzna dla wszystkich producentów |
| Silnik | Korelacja, przypisania z uzasadnieniem, uplinki, wieloznaczności | Rozbudowane algorytmy identyfikacji fizycznych urządzeń |
| Mapa | Pan/zoom, wybór węzła, porty na linkach, VLAN, wyszukiwanie, ukrywanie hostów | Ręczny edytor mapy, zaawansowane animacje i wiele układów |
| Historia | Pojawienie, brak obserwacji, powrót, zmiana przypisania | Odtwarzanie animowane, powiadomienia, rozbudowane raporty |
| Eksport | JSON, CSV, SVG i PNG | PDF i formaty innych narzędzi |
| Praca ciągła | Odświeżanie, gdy aplikacja działa | Usługa systemowa, kontener i zdalne kolektory |

Cięcie liczby adapterów SSH jest świadome: implementowanie wszystkich producentów przed pierwszą mapą zagraża terminowi. Urządzenie spoza listy może działać przez standardowe MIB-y; potwierdzenie konkretnego zakresu wsparcia wymaga odczytu i walidacji. Sam ranking przychodów producentów nie stanowi macierzy zgodności.

## 3. Architektura jednej aplikacji

Przepływ: Flutter UI → kontroler odkrywania → SNMP/SSH/snapshot → normalizacja → silnik topologii → SQLite → mapa i eksport.

### 3.1. Moduły i odpowiedzialności

| Moduł | Odpowiedzialność |
|---|---|
| UI | Lista projektów, konfiguracja, postęp, mapa, szczegóły, historia |
| DiscoveryCoordinator | Kolejka urządzeń, limity, anulowanie, cykle odświeżania |
| Collectors | Odczyty SNMP, komendy SSH, wczytywanie snapshotów |
| Normalizer | Ujednolicenie MAC, IP, portów, VLAN i kontekstów producentów |
| TopologyEngine | Linki infrastruktury, przypisania hostów, pewność i ostrzeżenia |
| Repository | Transakcje SQLite, odczyt ostatniego widoku i zapis historii |
| GraphScene | Wspólna geometria węzłów, krawędzi i etykiet dla widoku i eksportów |
| SecretStore | Sekrety systemowe i odwołania do nich; bez sekretów w bazie topologii |

Granice modułów pozostają zwykłymi katalogami i klasami. Nie tworzymy osobnej paczki dla każdego modułu, ogólnego frameworka pluginów ani dodatkowych warstw architektury bez zastosowania.

### 3.2. Flutter i praca w tle

- Proste kontrolery z ValueNotifier/ChangeNotifier; bez równoległego używania kilku bibliotek stanu.
- Asynchroniczne I/O; jedno zadanie zbierania danych na urządzenie w danym czasie.
- Obliczenia większych snapshotów oraz synchroniczne operacje SQLite wykonuje jeden worker isolate. Worker jest jedynym właścicielem połączenia z bazą.
- UI dostaje ograniczone częstotliwościowo zdarzenia postępu i gotowe fragmenty widoku, zamiast przebudowy po każdym wpisie FDB.
- Nie przenosimy całej bazy ani pełnych surowych tablic do UI przy każdym odświeżeniu.
- Wyjście z aplikacji zatrzymuje kolektory. Historia nie sugeruje obserwacji wykonanych podczas jej zamknięcia lub uśpienia komputera.

### 3.3. Zależności

| Zależność | Cel | Decyzja |
|---|---|---|
| Flutter / Dart stable | Aplikacja i logika | Zamrożenie wersji narzędzi dla pierwszego wydania |
| dartssh2 | Transport SSH | Weryfikacja kluczy hostów obowiązkowa [2] |
| sqlite3 | Lokalna baza | Prosty SQL i niewielkie migracje; bez obowiązkowego ORM [3] |
| flutter_secure_storage | Systemowy magazyn sekretów | Sprawdzenie konfiguracji na platformie docelowej [4] |
| graphview | Gotowy algorytm rozmieszczenia grafu | Krótka próba; nie uzależniamy od niego modelu danych [5] |
| Net-SNMP | Implementacja SNMP v2c/v3 w MVP | Dystrybuowana zależność natywna; sprawdzenie licencji i komponentów [6] |

Eksport CSV i SVG nie wymaga dużych nowych bibliotek. SVG tworzymy z GraphScene, prawidłowo escapując tekst. PNG renderujemy z tej samej sceny przy jawnie ograniczonym rozmiarze obrazu; eksport obejmuje aktualnie wybraną mapę, nie przypadkowo tylko widoczny fragment okna.

## 4. Oddzielna paczka SNMP

### 4.1. Decyzja rekomendowana dla MVP

Tworzymy jedną paczkę Dart obsługującą v2c i v3, a nie dwa osobne pakiety. Nazwa robocza: home_lan_snmp; dostępność nazwy przed publikacją trzeba sprawdzić. Paczka nie zależy od Fluttera ani od modeli topologii.

W MVP własne są API, typy wyników, kontrola wywołań i integracja. Implementację protokołu zapewnia Net-SNMP. Paczka będzie jawnie opisywać tę zależność; nie reklamujemy jej jako implementacji pure Dart.

Proponowany kontrakt:

- SnmpTarget: adres, port, timeout, profil v2c/v3, contextName/contextEngineId, opcjonalny adres źródłowy.
- SnmpSession.get(oids).
- SnmpSession.getNext(oids).
- SnmpSession.getBulk(oids, nonRepeaters, maxRepetitions).
- SnmpSession.walk(rootOid): strumień typowanych varbindów.
- Cancel/close i stabilne wyjątki: timeout, authentication, authorization, unsupportedSecurity, malformedResponse, cancelled.
- Typowane wartości OID, integer, unsigned/counter, Counter64, octet string, IP, timeticks oraz wyjątki SNMP.
- Limity liczby varbindów, rozmiaru odpowiedzi i czasu operacji.
- Brak publicznego API zapisu.

Nie dodajemy do paczki pojęć switcha, hosta, VLAN ani LLDP. Interpretowanie MIB-ów należy do aplikacji, dzięki czemu paczka ma zastosowanie również poza tym projektem.

### 4.2. Most do Net-SNMP i sekrety

Rekomendowany most MVP to mały pomocniczy program natywny używający biblioteki Net-SNMP, uruchamiany przez Process.start bez powłoki. To komponent aplikacji, nie dodatkowy instalowany serwer.

- Poświadczenia przekazujemy przez prywatny stdin procesu i przechowujemy tylko w pamięci podczas operacji.
- Wyniki wracają jako ograniczony rozmiarem, wersjonowany strumień komunikatów z typami wartości; bajty octet string jako base64/hex, bez zgadywania tekstu.
- Argumenty procesu nie zawierają community, haseł ani kluczy.
- Nie generujemy jawnych plików konfiguracyjnych z sekretami. Nie mieszamy ustawień poszczególnych projektów ani globalnej konfiguracji SNMP użytkownika.
- Most przyjmuje tylko zamkniętą listę operacji odczytu i sprawdza rozmiary danych. Nie przyjmuje dowolnej komendy CLI lub nazwy funkcji biblioteki.
- Błąd lub zakończenie procesu wpływa na bieżące urządzenie, a nie całą aplikację.
- Algorytmy SNMPv3 opisuje rzeczywista macierz możliwości dołączonego buildu; konfiguracja jawna, bez automatycznego osłabiania zabezpieczeń.

Takie rozwiązanie wymaga niewielkiej ilości kodu natywnego i przygotowania binariów. Jego wykonalność, obsługa sekretów i uruchomienie na czystym systemie są sprawdzane na początku projektu, zanim powstanie reszta aplikacji. Nie zakładamy, że natywne pakowanie rozwiąże się samo na końcu.

### 4.3. Własny SNMP w Darcie po MVP

Własny transport UDP i kodowanie BER można później wprowadzić za tym samym API. Następnie implementujemy v2c, a dopiero po jego stabilizacji SNMPv3 USM: discovery, lokalizację kluczy, HMAC, AES, synchronizację czasu i REPORT-y.

To osobny etap z własną wyceną po krótkiej próbie technicznej. Reguła planowania: eksperyment dotyczący własnego SNMP nie przekracza dwóch dni; jeśli nie potwierdzi się mały i ograniczony zakres, własny protokół zostaje po MVP. Nie uzależniamy premiery od zastąpienia Net-SNMP.

Rozsądny późniejszy punkt startu v3 to SHA-256, SHA-1 i AES-128. Szczegóły zgodności określają RFC 3414, RFC 3826 i RFC 7860 [7–9]. Paczka kryptograficzna dostarcza prymitywy; nadal trzeba poprawnie zaimplementować reguły protokołu. Testy kryptografii i zgodności są obowiązkowe dopiero dla tej własnej implementacji; w MVP nie powielamy całej walidacji Net-SNMP.

### 4.4. Co oznacza „oddzielna paczka” przy odbiorze

Osobny pubspec.yaml, niezależne modele, README, przykład odczytu, opis zależności natywnych, licencja, CHANGELOG i kilka testów kontraktu. Aplikacja korzysta z lokalnej zależności path w tym samym repozytorium. Publikacja na pub.dev jest osobnym krokiem po ustaleniu nazwy i licencji oraz weryfikacji pakowania binariów; nie jest warunkiem pierwszej użytecznej mapy.

## 5. Dane i identyfikacja

Minimalny model:

| Obiekt | Główne informacje |
|---|---|
| NetworkProject | ID, nazwa, seedy, zakres zarządzania, limity, referencje profili |
| DiscoveryRun | ID, projekt, start/koniec, status i kompletność |
| ManagedDevice | Wewnętrzne ID, adresy zarządzania, producent, model, system, możliwości |
| Interface | Urządzenie, ifIndex, bridgePort, ifName, alias, status, identyfikacja agregacji |
| VlanMembership | Kontekst, VLAN, interfejs, tagged/untagged/PVID, źródło, czas |
| Observation | ARP/FDB/LLDP/L3, źródło, kontekst, czas, dane znormalizowane |
| Endpoint | Wewnętrzne ID, interfejsy/MAC, adresy IPv4, nazwy, OUI |
| Link / Attachment | Końce relacji, porty, VLAN/kontekst, dowody, confidence, alternatywy |
| ChangeEvent | Typ zmiany, czas, wcześniejsza i nowa wartość, powiązany run |

Realizacja: kilka tabel SQLite i zwięzłe snapshoty obserwacji jako JSON. Nie tworzymy osobnej tabeli dla każdego OID. Wersja formatu snapshotu i wersja schematu bazy są jawne; zapis cyklu i historii jest transakcyjny.

Zasady tożsamości:

- Adres IP i hostname nie są identyfikatorem urządzenia.
- MAC nie jest samodzielnym globalnym identyfikatorem fizycznego hosta.
- Powiązania uwzględniają projekt, obserwatora, interfejs/bridge, VLAN i znany kontekst L3.
- Ten sam numer VLAN na dwóch switchach nie dowodzi wspólnej domeny L2. Potrzebne są dodatkowe dowody albo relacja pozostaje niepewna.
- Nie łączymy urządzeń wyłącznie na podstawie podobnej nazwy VRF lub hostname.
- Gdy kontekst jest nieznany, zachowujemy informację o niewiedzy; nie przenosimy automatycznie obserwacji do jednej globalnej domeny.
- Host może mieć kilka interfejsów i kilka poprawnych przypisań. Uproszczenie „jeden host = jeden MAC = jeden port” nie będzie wymuszane.

OUI pochodzi z lokalnego, wersjonowanego źródła o sprawdzonej licencji. Brak dopasowania jest poprawnym wynikiem; nie wysyłamy MAC-ów do publicznego API.

## 6. Kolektor i przebieg odkrywania

1. Załaduj projekt i referencje sekretów. Sprawdź seedy, formaty IP i dostępność komponentów lokalnych.
2. Dla seedów odczytaj sysObjectID/sysDescr, identyfikatory i możliwości; nie próbuj wielu haseł bez ograniczeń.
3. Pobierz IF-MIB i mapowanie bridgePort → ifIndex. Dopiero potem interpretuj FDB.
4. Odczytaj VLAN-y bieżące/statyczne, relację FDB ID → VLAN, PVID i bitmapy portów.
5. Pobierz FDB i ARP z dostępnych urządzeń L3. Znacznik czasu zapisuj dla poszczególnych źródeł.
6. Odczytaj LLDP, w tym adresy zarządzania sąsiadów. Same chassis ID i nazwa nie muszą być adresem do połączenia.
7. Przy włączonej rekurencji dodaj nowych sąsiadów do kolejki, po kontroli zakresu i deduplikacji.
8. Dla brakujących obsługiwanych danych użyj odpowiedniego adaptera SSH. Nie wykonuj wszystkich źródeł ponownie bez potrzeby.
9. Zapisz obserwacje oraz status każdej tabeli: sukces, pusta, brak uprawnień, nieobsługiwana, timeout albo ucięta limitem.
10. Zbuduj widok topologii, porównaj z historią i opublikuj mapę także wtedy, gdy część urządzeń nie odpowiedziała.

Proponowane wartości początkowe, konfigurowalne:

| Parametr | Wartość początkowa |
|---|---:|
| Równolegle obsługiwane urządzenia | 4 |
| Równoległe sesje SSH | 2 |
| Timeout zapytania SNMP | 2 sekundy |
| Ponowienia zapytania | 1 |
| GETBULK maxRepetitions | 10; redukcja przy problemach |
| Budżet odczytu urządzenia | 120 sekund, potem wynik częściowy |
| Odświeżanie | Ręczne lub co 5 minut |
| Rekurencja LLDP | Opcjonalna; 3 poziomy, 100 urządzeń na start |
| Stare snapshoty | Retencja 30 dni, ustawialna |

Interwał nie uruchamia drugiego cyklu, gdy pierwszy nadal trwa. Walk kończy się przy wyjściu z poddrzewa, końcu MIB, braku postępu OID, anulowaniu lub przekroczeniu limitu. Duża sieć nie wymaga wcześniejszego policzenia urządzeń, ale przekroczenie limitu oznacza mapę częściową z komunikatem i możliwością zwiększenia limitu.

Zakres rekurencji nie rozszerza się automatycznie na całą adresację RFC1918. Bez jawnej listy podsieci proponujemy dopuszczać seedy i ograniczone liczbą/głębokością adresy zarządzania wskazane przez LLDP. Ostateczna polityka zakresu wymaga zatwierdzenia przed pierwszym odczytem rzeczywistej sieci.

SSH: adapter ma stałą listę komend odczytu. Żaden ifName, hostname ani inny tekst pochodzący z urządzenia nie jest bezpośrednio doklejany do polecenia. Pierwszy klucz hosta jest jawnie akceptowany przez operatora lub dostarczony wcześniej; zmiana znanego klucza blokuje połączenie do wyjaśnienia. Awaria SNMP nie zmienia profilu dostępowego ani poziomu zabezpieczeń bez decyzji operatora.

## 7. Silnik topologii

### 7.1. Kolejność wnioskowania

1. Utwórz urządzenia zarządzalne i ich interfejsy.
2. Zbuduj potwierdzone relacje infrastruktury z LLDP; zachowaj informację, czy dowód jest jednostronny czy wzajemny.
3. Uwzględnij dostępne agregacje. Link logiczny może mieć wiele portów fizycznych.
4. Rozpoznaj porty prowadzące do dalszej infrastruktury na podstawie całego zestawu dowodów. Wiele MAC-ów i trunk to wskazówki, nie samodzielne rozstrzygnięcie.
5. Koreluj ARP i FDB w zgodnym kontekście oraz z uwzględnieniem czasu odczytu.
6. Oceń kandydatów przypisania. Preferuj najbardziej bezpośredni zgodny port, a małą liczbę MAC-ów wykorzystuj pomocniczo.
7. Przy remisie lub sprzeczności pokaż alternatywy. Nie rysuj pewnego pojedynczego kabla, którego nie da się potwierdzić.
8. Dodaj dostępną adresację interfejsów L3 i węzły podsieci. Brak tablicy ARP nie usuwa hosta znanego z FDB.

### 7.2. Confidence i prezentacja ograniczeń

Trzy poziomy: wysokie, średnie, niskie; dodatkowo nierozstrzygnięte. Nie pokazujemy arbitralnej wartości „97%”. Każda decyzja zawiera reasonCodes i źródła, np. wzajemne LLDP, pojedynczy zgodny port, niepełna FDB, konflikt kontekstów lub stara obserwacja.

Przykład: MAC widoczny na uplinku S1 i na porcie końcowym S2 zostaje przypisany do S2, jeżeli dowody i kontekst są zgodne. Gdy S2 jest niedostępny, zapisujemy „osiągalny za portem S1” z niepewnością, zamiast twierdzić, że host jest bezpośrednio wpięty do S1.

### 7.3. Ostrzeżenia i historia

- Cykl w grafie oznacza cykl/redundancję, nie potwierdzoną aktywną pętlę Ethernet. Bez danych o forwarding/STP nie wyciągamy silniejszego wniosku.
- Równoczesne widzenie MAC-a na kilku switchach nie oznacza flappingu. Ostrzeżenie wymaga powtarzających się zmian końcowego przypisania w zgodnym kontekście i oknie czasowym; agregacje mogą wyjaśniać część zmian.
- Zmianę portu zapisujemy tylko między porównywalnymi obserwacjami; nie po samym spadku confidence.
- Brak hosta po dwóch udanych, kompletnych odczytach odpowiedniego źródła daje status „nieobserwowany”. Timeout, brak uprawnień i niepełna tablica tego licznika nie zwiększają.
- Powrót obserwacji przywraca aktywność i tworzy zdarzenie. Status nieobserwowany nie jest dowodem fizycznego odłączenia.

## 8. Interfejs i mapa

Jedno okno: pasek projektu i Start/Stop, filtry, obszar mapy, panel szczegółów oraz zakładka historii.

Ścieżka pierwszego użycia: Nowy projekt → seedy → profil SNMP/SSH → uruchom → postęp i wyniki częściowe → mapa → wybór urządzenia → eksport.

GraphScene przechowuje pozycje i wymiary węzłów, końce linków, etykiety i kolory. Flutter renderuje scenę przez CustomPainter i InteractiveViewer. Kliknięcia sprawdzają położenie węzłów. Korzystamy z gotowego algorytmu rozmieszczenia, jeżeli krótka próba graphview potwierdzi integrację [5]; w przeciwnym razie układ warstwowy od seedów z dodatkowo narysowanymi krawędziami cykli. Nie tworzymy od zera rozbudowanego edytora grafów.

- Switche, routery i hosty mają odróżnialne symbole.
- Filtr VLAN i wyszukiwanie obejmują IP/MAC/nazwę oraz porty.
- Trunk z wieloma VLAN-ami ma jawne oznaczenie, zamiast jednego mylącego koloru.
- Linki niepewne mają inny styl; panel pokazuje dowody i alternatywy.
- Etykiety hostów i portów można ukrywać przy oddaleniu; hosty można zwinąć do licznika przy switchu.
- Przy większej sieci początkowo pokazujemy infrastrukturę i wybrany fragment hostów; pełny wynik nadal jest w tabeli i eksporcie.
- Panel: IP, MAC, OUI, VLAN/kontekst, switch/port, ostatnia obserwacja, confidence i źródło.
- Po odświeżeniu zachowujemy pozycje znanych urządzeń, żeby mapa nie przeskakiwała bez potrzeby.

JSON zawiera wersję schematu, obserwacje lub ich wybrany zakres, kompletność i uzasadnienia. CSV: osobne pliki urządzeń/przypisań i linków. Chronimy pola tekstowe przed interpretowaniem ich jako formuł arkusza. Eksport nie zawiera sekretów. SVG i PNG przedstawiają aktualne filtry i jawnie podany czas obserwacji.

## 9. Minimalna ochrona newralgicznych punktów

Nie wyznaczamy procentu pokrycia, nie budujemy farmy testów ani pełnego zestawu testów UI. Poniższe małe grupy są uruchamiane ręcznie przed wydaniem oraz po zmianie danej logiki.

| Grupa | Minimalne przypadki |
|---|---|
| Tryb odczytu i sekrety | Odrzucenie operacji zapisu; brak sekretów w argv/logach/eksporcie; walidacja wejścia mostu |
| Paczka SNMP | Typowane wyniki, timeout, anulowanie, koniec walk, brak postępu, duże/błędne odpowiedzi |
| Krytyczne mapowania | bridgePort/ifIndex, FDB ID/VLAN, bitmapy VLAN, normalizacja MAC |
| Topologia | Host za uplinkiem; wiele MAC za AP/hypervisorem; remis; ten sam IP w różnych kontekstach |
| Historia | Timeout nie usuwa hostów; częściowy cykl nie udaje kompletnego; poprawna zmiana portu |
| Dane i eksport | Transakcja zapisu, ponowne otwarcie bazy, escapowanie SVG i pól CSV |

Używamy 4–6 małych snapshotów wspólnych dla demonstracji, ręcznego odbioru i powyższych przypadków. Nie tworzymy setek wariantów modeli producentów. Odbiór ręczny obejmuje pełną ścieżkę użytkownika, błędne hasło, niedostępny switch, anulowanie i uruchomienie gotowego pakietu na czystym systemie.

Pomiar wydajności to jeden powtarzalny scenariusz: orientacyjnie 50 switchy, 2000 hostów i 100 tys. obserwacji FDB. To cel pomiarowy, nie zadeklarowana obsługiwana skala. Mierzymy czas silnika, pamięć i płynność przeglądania wybranego fragmentu. Nie wymagamy czytelnego wyświetlenia wszystkich etykiet naraz i nie obiecujemy czasu odczytu zależnego od urządzeń.

## 10. Harmonogram wdrożenia

Kolejne etapy rozpoczynamy po zatwierdzeniu wyniku poprzedniego. Zatwierdzenie można przekazać po krótkiej demonstracji; czekanie na decyzję nie jest wliczone do dni pracy. Testy newralgiczne dopisujemy przy danym module, a końcowy etap służy integracji i odbiorowi.

| Etap | Dni pracy | Zadania | Konkretny wynik do zatwierdzenia |
|---|---:|---|---|
| 0. Zamknięcie założeń | Przed startem | Platforma/CPU, zakres MVP, adaptery, sposób pakowania SNMP | Uzgodniona lista zakresu i limitu czasu |
| 1. Sprawdzenie ryzyk | 1–2 | Flutter na docelowym OS; most Net-SNMP v2c/v3; sekrety przez stdin; próba grafu i eksportu | Odczyt z agenta, przykład mapy, decyzja o wykonalności pakowania |
| 2. Szkielet i model | 3–4 | Projekt aplikacji, paczka SNMP, modele, SQLite, magazyn sekretów, snapshot offline | Projekt sieci zapisuje się i otwiera, offline przechodzi przez model |
| 3. Kolektor SNMP | 5–8 | MIB-y, mapowania, limity, LLDP, częściowe odczyty, normalizacja | Znormalizowany snapshot rzeczywistej małej sieci oraz statusy błędów |
| 4. Silnik i historia | 9–11 | Linki infrastruktury, ARP/FDB, confidence, konflikty, podstawowa L3, zdarzenia | Poprawne przypisania i jawne niepewności na snapshotach |
| 5. Interfejs mapy | 12–15 | Mapa, filtry, szczegóły, postęp, Start/Stop, historia, eksporty | Użyteczna aplikacja offline i online z eksportem |
| 6. SSH i pakowanie | 16–18 | Adapter IOS XE lub zatwierdzony zamiennik; fallback; paczka binarna, dokumentacja pakietu SNMP | Odczyt SSH i samodzielnie uruchamialna dystrybucja |
| 7. Odbiór | 19–20 | Newralgiczne sprawdzenia, pomiar wydajności, próba czystego systemu, poprawki | Wydanie MVP z jawną macierzą wsparcia i ograniczeń |
| Rezerwa | 21–25 | Rozbieżności MIB/CLI, natywne zależności i błędy odbioru | Usunięte problemy blokujące użycie |

Po etapie 1 aktualizujemy wycenę na podstawie wyników, zamiast utrzymywać fikcyjny termin. Gdy opakowanie Net-SNMP na wybranym OS nie jest wykonalne w budżecie, przedstawiamy konkretny wybór: systemowa instalacja Net-SNMP, pierwsze wydanie na innym OS albo zmiana terminu. Nie zastępujemy tego po cichu wielotygodniowym pisaniem protokołu.

Pierwsza mapa offline powstaje wcześnie, a pierwsza korelacja rzeczywistych danych przed końcem drugiego tygodnia pracy. Nie odkładamy sprawdzenia odczytów i mapowania portów na końcowy odbiór.

## 11. Zasady utrzymania terminu i odbiór MVP

Przy zagrożeniu terminu odraczamy kolejno: drugi adapter SSH, upiększenia grafu, dodatkowe systemy operacyjne, dodatkowe rozszerzenia producentów, zaawansowane rozpoznawanie MLAG i własny protokół SNMP. Nie usuwamy ochrony sekretów, trybu odczytu, sygnalizacji niepełnych danych ani krytycznych mapowań portów.

Definicja gotowego MVP:

1. Jedna dystrybucja uruchamia się na uzgodnionym OS bez środowiska deweloperskiego. Jeżeli wymaga instalacji zależności systemowej, jest to jawne i wcześniej zatwierdzone.
2. Dwa oddzielne projekty z identyczną adresacją pozostają rozdzielone.
3. Na kontrolowanej topologii z co najmniej dwoma switchami aplikacja pokazuje link między nimi, VLAN-y i hosty na właściwych portach w granicach dostępnych dowodów.
4. SNMP v2c i uzgodnione warianty SNMPv3 działają przez oddzielną paczkę; README opisuje wymagany backend.
5. Brak odpowiedzi jednego urządzenia daje mapę częściową, nie awarię procesu ani masowe fałszywe zniknięcie hostów.
6. Konflikty i niepewne przypisania są widoczne, a uplinki nie stają się automatycznie portami końcowymi.
7. Działają filtry, panel szczegółów, historia, anulowanie i cztery formaty eksportu.
8. Demo offline używa tego samego silnika co odczyt online.
9. Dostępna jest krótka instrukcja uruchomienia i macierz: potwierdzone urządzenia/wersje, zakres częściowy, ograniczenia.

LAG, stack i MLAG mogą wystąpić w dowolnej sieci. MVP musi zachować ich kontekst lub zaznaczyć brak rozpoznania. Pełne potwierdzone przypisania we wszystkich odmianach tych konstrukcji nie są obietnicą pierwszego wydania.

## 12. Struktura repozytorium i wydanie

```text
network_mapper/
  app/
    lib/
      ui/
      discovery/
      collectors/
      models/
      topology/
      storage/
      export/
    assets/demo/
    test/critical/
  packages/
    home_lan_snmp/
      lib/src/
      native/           # most i instrukcja/budowanie backendu
      example/
      test/critical/
      README.md
      CHANGELOG.md
      LICENSE
  docs/
    supported_devices.md
    quick_start.md
  scripts/
    build_release.*     # jeden skrypt na uzgodniony system
```

Jedno repozytorium, jedna aplikacja i jedna paczka publiczna SNMP. Biblioteki Net-SNMP i ich zależności otrzymują wymagane informacje licencyjne. Dystrybucja i podpisanie/notaryzacja zależą od wybranej platformy i dostępności kont/certyfikatów; nie zakładamy ich posiadania.

Wydanie wykonujemy ręcznie: analiza statyczna → testy krytyczne → build release → krótki odbiór → spakowanie. Zwykły skrypt budowania nie jest pipeline'em CI/CD. Nie dodajemy automatycznego wdrażania, botów aktualizujących ani publikacji przy każdym commicie.

## 13. Decyzje przed implementacją

1. Platforma i architektura pierwszego wydania. Propozycja: macOS na obecnym środowisku, jeśli to także komputer operatora; Windows x64, jeżeli odbiorcy mają przede wszystkim laptopy Windows. Nie zakładamy wyboru na podstawie samego komputera deweloperskiego.
2. Flutter Desktop jako jedno okno zamiast osobnego serwera i panelu webowego.
3. Paczka SNMP v2c/v3 z backendem Net-SNMP w MVP, własny protokół Dart po MVP.
4. Jeden adapter SSH na start: IOS XE lub konkretna platforma, dla której dostępne są urządzenia/snapshoty.
5. Dostęp do kontrolowanego agenta SNMPv3 i małej sieci testowej; bez tego można odebrać tryb offline, ale nie deklarować zgodności rzeczywistych odczytów.

Pozostałe parametry opisane jako propozycje zatwierdzamy zbiorczo z planem. Szczegóły wykonania niewpływające na zakres można rozstrzygać podczas implementacji. Kolejne zatwierdzenia dotyczą gotowych wyników etapów, nie każdej klasy i biblioteki.

## Źródła techniczne

Sprawdzone 11 października 2026 r. Źródła potwierdzają możliwości komponentów, nie podane estymacje projektu. Dokładne wersje zależności przypinamy po sprawdzeniu współdziałania na platformie docelowej.

1. Flutter Desktop: https://docs.flutter.dev/platform-integration/desktop
2. dartssh2: https://pub.dev/packages/dartssh2
3. sqlite3: https://pub.dev/packages/sqlite3
4. flutter_secure_storage: https://pub.dev/packages/flutter_secure_storage
5. graphview: https://pub.dev/packages/graphview
6. Net-SNMP i API biblioteki: https://www.net-snmp.org/ oraz https://www.net-snmp.org/dev/agent/group__library.html
7. SNMPv3 USM: https://www.rfc-editor.org/rfc/rfc3414.html
8. AES w SNMP: https://www.rfc-editor.org/rfc/rfc3826.html
9. SHA-2 w SNMP: https://www.rfc-editor.org/rfc/rfc7860.html
