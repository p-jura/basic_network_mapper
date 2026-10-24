# Poradnik: Etap 1 — odkrywanie sieci bez SNMP i SSH

Projekt: **Maper sieci — własna aplikacja z darmowych komponentów**. Data: 11 października 2026 r.

Podstawa: [plan](../PLAN_STARTOWY.md), [wymagania](../WYMAGANIA_PROJEKTU.md), [karta Etapu 0](KARTA_ETAP_0.md#10-doprecyzowanie-po-zatwierdzeniu-odkrywanie-bez-snmpssh). Ten poradnik uzupełnia [główny poradnik Etapu 1](ETAP_1_PROBA_KOMPONENTOW.md), szczególnie sekcję 6A.

## 1. Co wykonujemy i jaki ma być wynik

Przygotowujemy mały przekrój techniczny, który odkrywa dostępne urządzenia lokalnego LAN bez seedów, community, konta SNMP i konta SSH. Marka routera nie ma znaczenia. Następnie pokazujemy dane w istniejącym panelu próbnym jako mapę logiczną.

To instrukcja implementacji i odbioru. Gotowego skanera `tools/probe_discovery.py` jeszcze nie dostarczono; polecenia jego przyszłego interfejsu w sekcji 8 są specyfikacją, nie działającą funkcją. Dotychczasowy `run_probe.py` uruchamia wyłącznie próby SNMP/SSH. Nie wymaga zmian, żeby zachować tę rolę.

Wynik do odbioru:

- wybrany interfejs IPv4, maska, zakres oraz brama, jeśli znana z tras;
- lista zaobserwowanych hostów, z IP, dostępnym MAC, źródłem i świeżością;
- mapa segmentu z relacjami logicznymi, bez domniemanych kabli;
- `port`, `vlan` i `switch` nieustalone, jeśli nie ma dowodów infrastruktury;
- liczby wykonanych/pominiętych/nieprzeskanowanych celów, status kompletności i powody;
- zapis lokalnego wyniku i krótki raport na macOS ARM oraz Windows x64.

Podstawowy skan nie gwarantuje znalezienia hostów uśpionych, izolowanych lub nieodpowiadających. Nie dociera automatycznie do sieci sąsiadów, innych VLAN-ów czy urządzeń za NAT. Niezarządzalny switch może nie mieć wykrywalnego adresu. Skanowanie nie ujawni wtedy jego portów.

## 2. Przygotuj komponenty i miejsce próby

Najpierw przygotuj venv i panel według głównego poradnika. Jako nowy komponent proponujemy `psutil` do adresów i masek; dokładną wersję przypnij po próbie. Biblioteka obsługuje interfejsy na Windows/macOS, ale nie zastępuje odczytu tras i tablicy sąsiadów. [API psutil](https://psutil.io/)

Dodaj `psutil` do używanego pliku wejściowego zależności. Zachowaj wymagane noty BSD-3-Clause dla faktycznie dołączonej wersji. [Licencja](https://github.com/giampaolo/psutil/blob/master/LICENSE)

Nie instalujemy na potrzeby tej ścieżki Nmap, Npcap, sterownika przechwytywania ani komercyjnego skanera. Trasy, sąsiadów i ping obsługują istniejące narzędzia systemu; własny kod ogranicza się do adaptera, normalizacji i kontrolera. Nie piszemy surowego ARP ani ICMP. Docelowo próba ma działać jako zwykły użytkownik; brak uprawnień do konkretnej operacji jest wynikiem do naprawy lub opisania, nie powodem automatycznego podnoszenia uprawnień całego panelu.

Pliki do przygotowania podczas implementacji:

```text
tools/probe_discovery.py             # nowa próba, jeszcze nie istnieje
examples/snapshots/basic-demo.json   # wyłącznie dane syntetyczne do repozytorium
docs/etap-1/RAPORT_ETAP_1.md
```

Rzeczywisty wynik zapisuj w prywatnym katalogu projektu, nie w `examples/`. Nie przenoś ani nie nadpisuj roboczych skryptów `prototypes/tools/` bez porównania zawartości. Instrukcje używają docelowego `tools/`; jeżeli zachowujesz inne położenie, dostosuj wszystkie ścieżki.

## 3. Zrób odczyt lokalnego stanu bez sondowania

Te polecenia jedynie odczytują informacje lokalne. Nie są pełnym skanerem. Wykonaj je w terminalu, żeby przygotować adapter i rozpoznać rzeczywisty interfejs. Nie uruchamiamy ich automatycznie w ramach aktualizacji dokumentacji.

Po instalacji `psutil`, macOS:

```sh
./.venv/bin/python -c 'import psutil; print(psutil.net_if_addrs()); print(psutil.net_if_stats())'
/sbin/route -n get default
/usr/sbin/netstat -rn -f inet
/usr/sbin/arp -an
```

Windows, PowerShell:

```powershell
.\.venv\Scripts\python.exe -c 'import psutil; print(psutil.net_if_addrs()); print(psutil.net_if_stats())'
Get-NetIPConfiguration
Get-NetRoute -AddressFamily IPv4 | Select-Object InterfaceIndex,DestinationPrefix,NextHop,RouteMetric | ConvertTo-Json -Depth 3
Get-NetNeighbor -AddressFamily IPv4 | Select-Object InterfaceIndex,IPAddress,LinkLayerAddress,State | ConvertTo-Json -Depth 3
```

Windows udostępnia odczyt tras i sąsiadów przez cmdlety NetTCPIP. Sąsiad ma m.in. interfejs oraz stan wpisu. [Get-NetRoute](https://learn.microsoft.com/en-us/powershell/module/nettcpip/get-netroute), [Get-NetNeighbor](https://learn.microsoft.com/en-us/powershell/module/nettcpip/get-netneighbor)

Na macOS sprawdź składnię na docelowej wersji przez `man route`, `man netstat`, `man arp` i `man ping`. W adapterze ustaw numeryczny wynik i kontrolowane środowisko językowe. Przy nieznanym formacie zgłoś błąd parsera zamiast pustej „poprawnej” tablicy. Zapisz zanonimizowane próbki do krótkiego sprawdzenia parsera.

Nie publikuj pełnych wyników z rzeczywistej sieci. Zawierają adresy i nazwy interfejsów; do raportu lub repozytorium przenieś tylko potrzebne, spójnie zanonimizowane informacje.

## 4. Wybierz interfejs i zakres

1. Z `psutil` wybierz aktywne interfejsy IPv4 z maską; pomiń loopback. Interfejs wirtualny/VPN pokazuj z opisem, zamiast uznawać go automatycznie za LAN.
2. Przy kilku adresach pokaż listę i wymagaj wyboru dla tej próby. Zapisz nazwę oraz indeks systemowy potrzebny do powiązania z trasami i sąsiadami.
3. Wyznacz sieć przez `ipaddress.IPv4Interface`. Nie zakładaj `/24`. Dla adresu bez prawidłowej maski nie proponuj szerokiego skanowania.
4. W MVP ogranicz podstawowe aktywne sondowanie do zakresu bezpośrednio połączonego z wybranym interfejsem. MAC z tablicy sąsiadów dotyczy lokalnego L2; dla celu za routerem nie przypisuj MAC bramy do tego hosta.
5. Pokaż liczbę celów przed startem. Pomijaj własny adres, multicast i broadcast; prawidłowo uwzględnij szczególne zakresy `/31` i `/32` zgodnie z `ipaddress`.
6. Przy zakresie większym niż 256 celów nie zaczynaj automatycznie ani nie obcinaj go po cichu. Operator wybiera podzakres lub jawnie zmienia budżet.
7. Sprawdź efektywną trasę do celów. Na Windows nie wystarczy sama najniższa metryka trasy: znaczenie mają długość prefiksu i metryka interfejsu. Przy VPN lub trasie przez inny interfejs pomiń sondę i pokaż powód. Szczegóły platformowego sprawdzenia trasy należą do adaptera i próby.

Domyślna brama jest informacją o konfiguracji komputera. Może prowadzić przez VPN albo nie odpowiadać na sondy. Węzeł oznacz wtedy „brama według trasy”, a nie „router potwierdzony skanem”. Brak bramy nie blokuje odkrywania bezpośrednio połączonego LAN.

## 5. Zaimplementuj mały adapter systemowy

Utrzymaj jeden interfejs funkcji, z dwiema krótkimi realizacjami dla Windows i macOS:

| Funkcja | Zwracane dane |
|---|---|
| `read_interfaces()` | interfejs, indeks, IPv4, maska, stan |
| `read_routes()` | prefiks, next hop, interfejs i dostępne metryki |
| `read_neighbors(interface)` | IPv4, MAC lub brak, interfejs, stan wpisu jeśli dostępny, czas odczytu |
| `check_target_route(ip, interface)` | zgodność trasy albo powód pominięcia |
| `probe_once(ip, interface)` | odpowiedź, brak odpowiedzi lub błąd procesu, czas i źródło |

Zasady wykonania:

- wywołuj procesy listą argumentów z `shell=False`; IPv4 parsuj przez `ipaddress`, nie wstawiaj surowego tekstu operatora do polecenia;
- PowerShell uruchamiaj bez profilu; stałe skrypty odczytowe zwracają JSON. Normalizuj JSON dla zera, jednego i wielu rekordów; przypisz rekordy po indeksie interfejsu;
- wykryj obecność narzędzi, ustaw deadline i ogranicz przechwycony wynik. Błąd narzędzia/parsera odróżnij od pustej tablicy;
- argumenty ping sprawdź osobno na obu OS. Jedna sonda, limit oczekiwania odpowiedzi oraz niezależny deadline procesu; jednostki i opcje Windows/macOS różnią się;
- nie traktuj wyłącznie kodu wyjścia procesu jako dowodu odpowiedzi hosta. Zweryfikuj docelową odpowiedź; komunikat „unreachable” od bramy nie potwierdza obecności celu;
- potwierdź poprawne źródło/interfejs przed sondą. Jeśli wymuszenie interfejsu nie jest dostępne, dopuść wyłącznie cel z potwierdzoną zgodną trasą; sprawdź ją ponownie przy zmianie sieci;
- nie czyść ARP, nie ustawiaj tras i nie zmieniaj zapory. Anulowanie kończy nowe zadania i sprząta uruchomione procesy.

Budżet z D06: do 256 celów, 5 nowych celów/s, jedna sonda na cel. Dodatkowe propozycje do pomiaru: 4 procesy równolegle, 3 s/proces, 5 s na polecenie odczytowe, 240 s na próbę. Równoległość i tempo to oddzielne limity. Jeżeli budżet czasu się skończy, wynik ma status częściowy i listę niewykonanych celów.

## 6. Zbierz obserwacje i zachowaj ich znaczenie

Przebieg: odczyt tras/interfejsów → sąsiedzi przed → ograniczone sondy → sąsiedzi po → normalizacja → zapis. Zapisz początek i koniec, wybrany zakres, liczbę celów, statusy źródeł i powód zakończenia.

| Obserwacja | Co wolno stwierdzić |
|---|---|
| Poprawna odpowiedź ICMP z celu | Cel odpowiedział w danym czasie; nie znamy z tego portu/VLAN-u |
| Wpis sąsiada sprzed próby | IP–MAC znane systemowi, świeżość obecności może być nieustalona |
| Nowy lub zmieniony wpis po sondach | Dowód zmiany tablicy sąsiadów; zachowaj stan i ograniczenia, bez udawania przechwyconej odpowiedzi ARP |
| Ten sam wpis cache przed i po | Samo odczytanie drugi raz nie aktualizuje czasu rzeczywistego widzenia hosta |
| Brak ICMP, ale MAC w sąsiadach | Host nadal może być osiągalny w L2; pokaż źródło i świeżość zamiast usuwać urządzenie |
| Niekompletny MAC/stan nieudany | Brak potwierdzonego powiązania; nie twórz fikcyjnego MAC |
| Wiele IP z jednym MAC | Możliwy router/proxy ARP lub wiele adresów jednego interfejsu; nie scalaj wszystkich automatycznie |

ARP dostarcza powiązanie adresów IP i sprzętowych, bez numeru fizycznego portu. [RFC 826](https://datatracker.ietf.org/doc/html/rfc826). W lokalnym segmencie próby dotarcia do IP mogą wywoływać rozwiązywanie ARP przez system, lecz cache, filtrowanie i brak odpowiedzi ograniczają wynik. [Techniki wykrywania hostów](https://nmap.org/book/host-discovery-techniques.html). Nmap nie jest zależnością tego projektu.

Minimalny rekord roboczy: `project_id`, `cycle_id`, `interface_id`, `segment_id`, `ip`, `mac` lub `null`, `source`, `observed_at`, `freshness`, `presence_status`. Oddziel `last_seen` wynikające ze świeżego dowodu od `cache_read_at`. Dołącz status źródła/zakresu; nie przypisuj procentowego confidence bez reguły. Produkcyjny schemat uzgodnimy w Etapie 2.

Nazwy i producent nie blokują próby. Brak danych daje „nieustalony”. Reverse DNS/mDNS można dodać później z oddzielnym budżetem; nie wysyłaj dodatkowych zapytań ukrytych pod zwykłym odczytem cache. OUI nie identyfikuje pewnie modelu ani producenta przy lokalnie administrowanym MAC.

## 7. Pokaż wynik w panelu

Zbuduj roboczy snapshot elementów zgodny z próbnym rendererem:

1. Dodaj węzeł segmentu, np. „LAN 192.168.1.0/24”. To grupa logiczna, nie wykryty fizyczny switch i nie VLAN 1.
2. Dodaj hosty oraz bramę według tras, unikając duplikatu, gdy ten sam IP występuje w obu źródłach.
3. Połącz hosty z segmentem krawędziami `relation_type=logical_membership`. W próbnym panelu nadaj im przerywany styl i etykietę „segment logiczny”. Nie łącz wszystkich bezpośrednio z portami routera.
4. Szczegóły zawierają IP/MAC, źródło, świeżość, czas, status obecności i `port/vlan/switch=null`. W pełnym panelu wartości te renderujemy jako „nieustalony”.
5. Dodaj ostrzeżenia: wynik częściowy, nieznana świeżość, izolacja, brak trasy lub nieobsługiwany format. W eksporcie zachowaj rodzaj relacji i ograniczenia.

Obecny przykład `probe_panel.py` czyta stały snapshot. Podczas realizowania tego przekroju dodaj opcję wyboru pliku snapshotu oraz styl segmentu/logicznej krawędzi, zachowując dotychczasową demonstrację dwóch switchy. Nie zakładaj, że te zmiany już są w skrypcie. Na Etap 1 wystarczy zapis kolektora i wczytanie go w panelu; produkcyjny przycisk i integracja tła należą do Etapu 4.

## 8. Ustal interfejs uruchamiania nowej próby

Proponowany kontrakt CLI do zaimplementowania w `tools/probe_discovery.py`:

| Opcja | Zachowanie |
|---|---|
| `--list-interfaces` | Tylko lokalny odczyt, bez sond |
| `--interface` | Jednoznaczny identyfikator z listy |
| `--cidr` | Jawny podzakres wybranego lokalnego LAN |
| `--preview` | Walidacja, trasa, liczba celów i budżet; bez sond |
| `--scan` | Jawny start ograniczonego sondowania; bez tej opcji nie wysyłaj sond |
| `--output` | Plik w prywatnym katalogu danych; zapis bez nadpisania istniejącego wyniku bez jawnej opcji |

Dla macOS przewidywane wywołanie po napisaniu skryptu:

```sh
./.venv/bin/python tools/probe_discovery.py --list-interfaces
```

Windows:

```powershell
.\.venv\Scripts\python.exe tools/probe_discovery.py --list-interfaces
```

Dalsze wywołanie wykorzystuje rzeczywisty identyfikator interfejsu, lokalny CIDR i prywatną ścieżkę wyniku. Najpierw `--preview`, potem operator uruchamia `--scan`. Bez gotowego skryptu powyższe polecenia zakończą się błędem braku pliku; istniejący `run_probe.py` nie ma trybu `basic` i nie dodajemy do instrukcji pozornego działającego wywołania.

## 9. Wykonaj krótki odbiór

| Próba | Oczekiwany wynik |
|---|---|
| LAN domowy, router bez SNMP/SSH | Brak żądania community/seedów; wykrycie znanych odpowiadających hostów i lokalnych powiązań MAC tam, gdzie dostępne |
| Brama w trasach nie odpowiada | Węzeł „brama według trasy”; brak fałszywej informacji o świeżej odpowiedzi |
| Host z blokowanym ICMP | Brak odpowiedzi nie usuwa hosta; dostępne wpisy sąsiadów mają właściwe źródło i świeżość. Jeśli brak dowodów, wynik mówi o ograniczeniu |
| Stary cache | Brak automatycznego podbicia `last_seen`; nie udajemy świeżej obecności |
| Wi-Fi z izolacją | Wynik ograniczony z opisem; nie twierdzimy, że LAN jest pusty |
| VPN lub dwa aktywne interfejsy | Wybór LAN i kontrola tras; pominięcie sond inną drogą, bez zmiany konfiguracji |
| Zakres ponad budżet | Brak cichego obcięcia i automatycznego skanu; czytelny komunikat przed startem |
| Anulowanie/timeout | Nowe zadania zatrzymane, procesy sprzątnięte, częściowy snapshot bez fałszywego zniknięcia |
| LAN bez Internetu | Podstawowe wykrywanie i lokalny panel działają; brak wymaganej chmury/CDN |
| Mapa i eksport | Segment oraz logiczne relacje, brak wymyślonych portów/VLAN-ów, zachowane źródła i ograniczenia |

Nie zmieniaj zapory ani ustawień routera produkcyjnego tylko dla testu. Przypadek blokowanego ICMP/izolacji wykorzystaj, jeśli istnieje w dostępnym laboratorium, albo sprawdź regułę na kontrolowanej próbce. Oznacz, co było realne, a co syntetyczne.

Ręcznie potwierdź IP i połączenie 2–3 znanych hostów, np. na ich ekranie ustawień sieci. Nie używaj jako jedynego wzorca innego skanera, który też może nie widzieć wszystkich urządzeń. Próby wykonuj kolejno na macOS i Windows; jeśli OS niedostępny, zapisz „niewykonana”, bez deklaracji zgodności.

## 10. Zapisz wynik i zakończ przekrój

Do wspólnego `RAPORT_ETAP_1.md` wpisz: OS/Python/psutil, interfejs i zakres po anonimizacji, metody, limity, czasy, liczbę celów i obserwacji, świeżość źródeł, ograniczenia oraz wynik panelu/eksportów. Oddziel podstawowe odkrywanie od SNMPv2c/v3 i SSH.

Minimalna ochrona automatyczna: walidacja zakresu/trasy, budżet i anulowanie, parser pustego/błędnego wyniku, stary cache bez świeżej obecności, brak fizycznego portu/VLAN-u bez dowodu oraz izolacja projektów. Wystarczą małe kontrolowane przypadki, bez rozbudowanej infrastruktury testowej.

Przekrój podstawowy jest gotowy do oceny, gdy działa bez poświadczeń, ma jawny zakres i ograniczenia, wykrywa znane odpowiadające cele oraz poprawnie przedstawia niepewność. Niewykonane próby SNMP/SSH nie odbierają tej funkcji, lecz nie pozwalają deklarować potwierdzonego mapowania rozszerzonego. Wynik całego Etapu 1 przedstawiamy do zatwierdzenia przed Etapem 2.
