# Wspólny cel projektów mapowania sieci

Stan ustaleń: 11 października 2026 r. Dokument zachowuje cel funkcjonalny obu wariantów; nie narzuca ich stosu technologicznego.

## Cel

Po uruchomieniu w nieznanej wcześniej sieci narzędzie ma odkrywać dostępne urządzenia również bez seed-switchy, poświadczeń i obsługi SNMP/SSH przez router. Na podstawie dostępnych dowodów tworzy mapę logiczną sieci lokalnej. Seedy oraz dane dostępowe są opcjonalnym rozszerzeniem pozwalającym odczytywać infrastrukturę i ustalać fizyczne porty, VLAN-y oraz pełniejszą topologię L2/podstawową L3.

Nie wymagamy wcześniejszej znajomości liczby switchy, hostów, VLAN-ów ani lokalizacji. Możliwe są VRF, powtarzająca się adresacja, LAG, stack i MLAG. Nierozpoznany przypadek ma pozostać jawnie niepewny.

## Zakres funkcjonalny

- IPv4. Podstawowe L3 obejmuje routery, interfejsy L3 i podsieci; pełna analiza routingu jest rozszerzeniem.
- Podstawowe odkrywanie bez seedów i poświadczeń: lokalne interfejsy IPv4, trasy/brama, sąsiedzi/ARP oraz sondowanie uruchamiane przez operatora w jawnym zakresie.
- Opcjonalne SNMPv2c/v3 oraz SSH jako fallback tam, gdzie rzeczywiście potrzebny i obsługiwany; brak tych usług nie jest błędem blokującym podstawowy skan.
- ARP: powiązania IPv4–MAC; FDB: MAC–port–VLAN; konfiguracja VLAN: PVID, porty tagowane/nietagowane i dostępne informacje o trybie portu.
- IF-MIB: nazwy, opisy i stan interfejsów. LLDP, opcjonalnie CDP: połączenia infrastruktury i rekurencyjne odkrywanie.
- Korelacja ARP i FDB z uwzględnieniem kontekstu, czasu, bridgePort/ifIndex i FDB ID/VLAN.
- Uplinki nie stają się automatycznie miejscem bezpośredniego podłączenia wszystkich widocznych MAC-ów. Wiele MAC-ów i trunk są wskazówkami, nie samodzielnym dowodem.
- Przypisanie urządzenia do najbardziej bezpośredniego zgodnego portu; konflikty, alternatywy i confidence z uzasadnieniem.
- Jeden obiekt może mieć kilka IP/MAC/interfejsów. Sama nazwa hosta albo sam adres IP nie rozstrzyga tożsamości.
- Osobne środowiska sieciowe nie mieszają danych, nawet przy identycznej adresacji.
- Historia pojawienia, braku obserwacji, powrotu i zmiany portu. Awaria kolektora nie oznacza zniknięcia hostów.
- Mapa: segmenty logiczne, switche, routery/kandydaci, hosty i relacje o określonym rodzaju; fizyczne linki i porty tylko z dowodami; wyszukiwanie IP/MAC/nazwa, filtr VLAN, szczegóły i ostatnia obserwacja.
- Eksport JSON, CSV, SVG i PNG. Producent według lokalnego źródła OUI, gdy dostępne dopasowanie.
- Ostrzeżenia dotyczące konfliktów, zmian przypisań i cykli/redundancji. Cykl w grafie nie jest samodzielnym dowodem aktywnej pętli.
- Tryb offline/snapshot do odtwarzania wyników i krótkiego odbioru.

## Ograniczenia obowiązkowe

1. Wyłącznie odczyt konfiguracji urządzeń. Bez SNMP SET, zmian portów/VLAN/PoE i komend konfiguracyjnych.
2. Aplikacja zapewnia uruchamiane przez operatora podstawowe odkrywanie lokalnego zakresu bez poświadczeń oraz opcjonalne odczyty SNMP/SSH. Zakres i obciążenie sondowania muszą być jawne; nie uruchamiamy automatycznie skanowania sieci operatora, sąsiadów ani całego Internetu.
3. Poświadczenia poza kodem i logami; kontrolowany dostęp oraz ochrona przechowywania. Bez sekretów w repozytorium i eksporcie.
4. Limity równoległości, timeouty, ograniczone ponowienia i anulowanie. Awaria jednego celu nie zatrzymuje reszty.
5. Brak gwarancji odkrycia nieaktywnych lub niedostępnych urządzeń i pełnego przypisania za niezarządzalnym switchem.
6. Szybkie MVP, bez CI/CD i rozbudowanej warstwy testowej. Chronimy newralgiczne punkty: odczyt, sekrety, przypisania i historię.
7. Praca etapami: propozycja i review konkretnego wyniku przed przejściem do następnego etapu. Podstawowy stos drugiego wariantu zatwierdzono w karcie Etapu 0; nowe szczegóły odkrywania sprawdzamy w Etapie 1.

## Różnica wariantów

- **Wariant A — Flutter/Dart:** jedna własna aplikacja; niezależna paczka Dart SNMP, początkowo z backendem Net-SNMP, własny protokół po MVP.
- **Wariant B — własny mapper z istniejących komponentów:** budujemy własną aplikację, wykorzystując darmowe biblioteki SNMP/SSH, parsery, bazę i renderer grafu. Python realizuje brakującą logikę odkrywania, normalizacji, korelacji, historii oraz integrację panelu. Gotowy produkt mapowania nie jest bazą aplikacji. Tworzenie własnej paczki SNMP nie jest wymaganiem tego wariantu.

## Obowiązkowa bezpłatność wariantu B

Wszystkie wymagane funkcje wykorzystują lokalne, darmowe komponenty open source. Wykluczamy triale, ograniczone edycje free, subskrypcje, limity urządzeń wynikające z licencji i zależność od płatnych funkcji lub usług. Warunki bibliotek, zależności oraz danych pomocniczych muszą pozwalać na bezpłatne użycie w projekcie. Zachowujemy wymagane informacje licencyjne. Konkretny dobór komponentów opisuje [plan startowy](PLAN_STARTOWY.md).

## Doprecyzowanie: sieci domowe i routery operatorów

Wymaganie użytkownika: podstawowe skanowanie działa niezależnie od marki routera, również przy urządzeniach operatorów, bez obowiązkowego SNMP, SSH i community. Brak tych usług nie blokuje aplikacji ani podstawowego odkrywania.

Plan realizacji: lokalny interfejs IPv4 i maska przez proponowany `psutil`, trasy/brama i sąsiedzi przez istniejące narzędzia systemu, ograniczone sondowanie systemowym pingiem. Własny Python integruje wyniki; nie piszemy stosu pakietów. Komponent i adaptery wymagają sprawdzenia na Windows/macOS w Etapie 1. Nazwy uzupełniamy, gdy dostępne, bez uzależniania od nich podstawowego wyniku. Szczegóły i kryteria zawiera [plan](PLAN_STARTOWY.md) oraz [poradnik odkrywania](poradniki/ETAP_1_ODKRYWANIE_PODSTAWOWE.md).

Mapa bez odczytów infrastruktury pokazuje urządzenia we wspólnym segmencie i relacje logiczne. Nie przedstawia domniemanych połączeń jako potwierdzonych kabli do portów routera. Nieznane porty/VLAN-y pozostają nieustalone. MAC zwykle można ustalić w dostępnym lokalnym segmencie L2, nie automatycznie dla hosta za routerem. Izolacja klientów, zapory, brak odpowiedzi i urządzenia nieaktywne ograniczają kompletność wyniku.

Zakres podstawowego odbioru obejmuje sieć bez SNMP/SSH: wykrycie dostępnych hostów i bramy, mapa z oznaczeniem logiczności, brak żądania community oraz jawne nieznane porty/VLAN-y. Brak ICMP nie oznacza nieistnienia hosta; stary wpis ARP nie dowodzi świeżej obecności. Eksport zachowuje źródła, świeżość i rodzaj relacji. Brak Internetu nie blokuje pracy w aktywnym LAN; tryb odtwarzania offline nie uruchamia kolektorów. Szczegóły implementacji są propozycją do próby, nie potwierdzeniem wykonania funkcji.
