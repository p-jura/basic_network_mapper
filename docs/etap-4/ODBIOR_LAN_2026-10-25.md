# Rzeczywisty odbiór LAN — panel 0.4.0

Data: **25 października 2026 r.** Oddzielny odbiór po zatwierdzeniu Etapu 4, przed zatwierdzeniem planu Etapu 5. Operator wyraźnie zezwolił na jeden wskazany zakres, potwierdzając prawo do jego badania. Interfejs, IPv4, CIDR, cele i limity zostały pokazane przed startem. Dokładna zgoda i dane znajdują się w prywatnym receipt poza repozytorium.

**Wynik: kolekcja i przepływ panelu działają; odbiór poprawności mapy NIEZALICZONY — wykryto dwa błędy klasyfikacji/tożsamości.** Nie wykonano kolejnego skanu, SNMP/SSH ani zmian konfiguracji urządzeń. To wynik rzeczywisty, odrębny od wcześniejszych prób syntetycznych. [Dowody zbiorcze bez adresacji/MAC](ODBIOR_LAN_2026-10-25.json).

## Przebieg i zakres

1. Odczyt lokalnych interfejsów i tras bez sond. Osobne potwierdzenie aktualnego zakresu przez operatora, ponieważ sieć miała inną adresację niż odbiór Etapu 2.
2. Nowy, prywatny projekt, mapper 0.4.0, panel na 127.0.0.1:8052. Bez seedów/profili i rekurencji, powtarzanie wyłączone.
3. W panelu wybór aktualnego interfejsu/zakresu, podgląd bez sond, potem pojedyncze kliknięcie startu. Pierwsze przygotowanie odrzucono jako NO_SOURCES_CONFIGURED; po jawnym wyczyszczeniu i ponownym wyborze interfejsu pokazano prawidłowy podgląd. Nie uruchomiono wówczas żadnego nieprawidłowego skanu.
4. Jeden cykl: 253 cele, po jednej sondzie, najwyżej 5 nowych celów/s i 4 równolegle; budżet 240 s. Zweryfikowany zbiór celów dokładnie odpowiada zgodzie: **bez własnego IP i bez adresu rozgłoszeniowego**.
5. Wynik automatycznie trafił do mapy. Sprawdzono filtr IP, szczegóły odpowiadającego urządzenia, brak przypisania port/VLAN oraz JSON/CSV/PNG/SVG z panelu.
6. Po odbiorze zamknięto tymczasową kartę i własny serwer. Cykl nie został powtórzony. Źródła, bazy, screenshot i obrazy rzeczywistej sieci pozostały poza repozytorium.

## Wyniki pomiaru

| Obszar | Wynik |
|---|---|
| Czas kolekcji według cyklu | 128,997 s |
| Cele / odpowiedź / brak odpowiedzi | 253 / 2 / 251 |
| Błędy / pominięcia | 0 / 0 |
| Status wykonania / pokrycia zadań | finished / complete |
| Obserwacje źródłowe | 533 |
| Niepuste pary IP–MAC w cache | 6, w tym wpis rozgłoszeniowy i własny adres |
| Graf przed poprawkami | 6 endpointów + lokalny interfejs + segment; 7 relacji logicznych |
| Zdalne adresy unicast po ręcznej weryfikacji | 4, z czego 2 mają świeżą odpowiedź ICMP; pozostałe pochodzą z cache |
| Przypisania portu / VLAN-u endpointom | 0 / 0, zgodnie z brakiem danych zarządzających |
| Historia | 8 zdarzeń; obejmuje też błędnie utworzone obiekty |
| SQLite integrity_check / foreign_key_check | ok / 0 błędów |
| Ponowny build offline | Ten sam graf, niezmieniony hash źródła, bez nowych sond |

Complete oznacza wykonanie zaplanowanych zadań, nie wykrycie wszystkich urządzeń ani fizycznych połączeń. Sam cache nie dowodzi obecnej aktywności. Nie porównujemy liczby urządzeń z inną siecią z Etapu 2 jako zdarzeń pojawienia/zniknięcia.

## Ustalenia do poprawy

| ID | Obserwacja | Ocena i warunek naprawy |
|---|---|---|
| LAN-01 | Systemowy wpis ARP z rozgłoszeniowym MAC został endpointem i otrzymał krawędź logiczną | Błąd blokujący odbiór mapy. Wpis może zostać w źródłach, lecz nie może udawać urządzenia końcowego. W tym przebiegu adres rozgłoszeniowy NIE był sondowany. |
| LAN-02 | Własny IPv4 występuje jednocześnie jako endpoint z cache i jako local_interface | Błąd prezentacji/tożsamości: dwa węzły tej samej lokalnej obserwacji. Wymaga scalenia/wykluczenia duplikatu bez utraty dowodów i bez ukrywania konfliktów IP. |
| LAN-03 | Załadowana konfiguracja wymagała jawnego ponownego wyboru interfejsu przed poprawnym preview | Uwaga do zbadania offline, nie potwierdzona przyczyna techniczna. Walidacja bezpiecznie blokowała start. Należy odtworzyć zapisany wybór i gotowość formularza w prawdziwej przeglądarce. |

Nie uznajemy 6 endpointów za 6 zdalnych urządzeń: jeden jest wpisem rozgłoszeniowym, a jeden własnym adresem. Z pozostałych czterech dwa mają jedynie dowód z cache. OUI, nazwa sprzętu i fizyczny port pozostają nieustalone.

## Eksporty i szczegóły

- Filtr odpowiadającego IP pokazał 2 z 8 węzłów (endpoint i segment) oraz 1 z 7 relacji. Szczegóły pokazały IP/MAC, czas, świeżą odpowiedź i nieustalony port/VLAN.
- JSON topologii oraz CSV urządzeń/relacji pobrane z panelu zawierały pełny zapisany graf: odpowiednio 8 węzłów, 8 rekordów urządzeń i 7 relacji. JSON porównano z wynikiem silnika.
- PNG odfiltrowanego widoku obejrzano; odpowiada wybranemu hostowi i segmentowi. SVG pełnego widoku ma poprawny XML i oczekiwane etykiety; zawiera też błędny obiekt rozgłoszeniowy, tak jak aktualna mapa.
- To potwierdza format i zgodność eksportu z zakresem widoku/snapshotu, **nie poprawność klasyfikacji zawartości grafu**. Błędy mapy propagują się do topologicznych eksportów i historii.
- Pliki serwerowe powstały prywatnie. Kopie obrazów z Downloads przeniesiono do prywatnego katalogu receipt i zabezpieczono. Nie dodano prywatnych danych do repozytorium.

## Następny krok przed pakowaniem

Przygotować i zatwierdzić mały zakres poprawek LAN-01/LAN-02 oraz odtworzenie LAN-03. Najpierw wykorzystać zachowany snapshot i własne zanonimizowane przypadki: rozgłoszeniowy/grupowy MAC, lokalny adres, rzeczywisty host oraz prawidłowe adresy w /31 i /32. Nie stosować reguły „każdy IPv4 kończący się .255 jest błędny”; znaczenie zależy od kontekstu i maski. Nie tracić obserwacji źródłowych.

Reguły topologii mają wersjonowane, niezmienne wyniki w SQLite. Poprawka nie może pozostawić tej samej wersji reguł i ponownie odczytywać błędnego cache; należy zapisać decyzję o zmianie reguł/replay przed kodem. Surowy snapshot v1 pozostaje dowodem. Początkową regresję można wykonać **offline na tym samym przebiegu, bez kolejnego skanu**.

To odbiór aktualnego kodu 0.4.0, nie nowej paczki Etapu 5. Nie zalicza Windows/NTFS, SNMP/SSH, instalacji offline ani pełnej macierzy wydania. Historyczne zatwierdzenie Etapu 4 pozostaje zapisane; nowy raport ujawnia luki, które trzeba usunąć przed uznaniem mapy i MVP za gotowe.
