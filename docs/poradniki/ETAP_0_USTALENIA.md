# Poradnik: Etap 0 — ustalenia przed budową mappera

Dotyczy projektu **Maper sieci — własna aplikacja z darmowych komponentów**.

Podstawa: [plan startowy](../PLAN_STARTOWY.md) oraz [wymagania projektu](../WYMAGANIA_PROJEKTU.md). Poradnik opisuje wykonanie Etapu 0 z tabeli etapów: wybór systemu, komponentów, zakresu odczytów, profili SNMPv3, pierwszej platformy SSH i kryteriów odbioru.

**Aktualizacja zakresu:** Etap 0 jest już zatwierdzony. Ten poradnik ujednolicono z późniejszym wymaganiem startu bez SNMP/SSH. Nie wypełniaj ponownie zatwierdzonej karty; sprawdź korekty D05/D06 i sekcję 10. Nowe szczegóły adaptera systemowego weryfikujemy w Etapie 1.

**Wynik etapu:** krótka, wypełniona i zatwierdzona karta decyzji. Samo przeczytanie poradnika, skopiowanie rekomendacji lub brak odpowiedzi nie oznacza zatwierdzenia. Próby SNMP/SSH, instalacja bibliotek i kodowanie należą do Etapu 1 lub kolejnych etapów.

## 1. Przygotuj miejsce na decyzje

Otwórz [KARTA_ETAP_0.md](KARTA_ETAP_0.md) w tym katalogu. To przygotowany formularz do uzupełnienia; nie zawiera sekretów. Pracuj bezpośrednio w nim, zachowując datę i status każdej decyzji.

Używaj czterech statusów:

| Status | Znaczenie |
|---|---|
| Ustalone | Wynika z dotychczasowych wymagań użytkownika |
| Propozycja | Rekomendacja wymagająca zatwierdzenia |
| Do decyzji | Brakuje wyboru albo informacji |
| Zatwierdzone | Właściciel projektu jawnie zaakceptował podaną wartość |

Przy zmianie wcześniejszej decyzji zapisz nową wartość, datę i powód. Nie utrzymuj kilku sprzecznych wersji zakresu w różnych dokumentach.

Zarezerwuj orientacyjnie 4–8 godzin pracy, jeśli masz informacje o środowisku i dostęp do osoby podejmującej decyzje. Oczekiwanie na dane z urządzeń lub zatwierdzenie może wydłużyć czas kalendarzowy; nie trzeba w tym czasie pisać kodu na zapas.

## 2. Zapisz to, co jest już ustalone

W pierwszej części karty zachowaj następujące wymagania jako ustalone:

- Własny mapper, z istniejącymi darmowymi bibliotekami i komponentami. Bez gotowego produktu mapowania jako silnika, triali i ograniczonych planów free.
- Własna logika i integracja w Pythonie. Bez pisania nowego silnika SNMP lub SSH.
- IPv4, topologia L2 i podstawowe L3: routery, interfejsy L3 i podsieci.
- Praca w różnych, wcześniej nieznanych sieciach. Identyczne IP w osobnych projektach nie mieszają danych.
- Odkrywanie lokalnego IPv4 bez seedów i poświadczeń; mapa logiczna oraz jawnie nieustalone porty/VLAN-y.
- Opcjonalne odczyty SNMPv2c/v3, SSH jako fallback, ARP/FDB/VLAN/IF-MIB oraz LLDP do rozszerzania mapy i rekurencji.
- Wyłącznie odczyt urządzeń, sekrety poza kodem/logami/eksportem, odporność na awarie pojedynczych celów.
- Interaktywna mapa, szczegóły, historia, JSON/CSV/SVG/PNG i tryb offline.
- Szybkie MVP, bez CI/CD i rozbudowanej warstwy testowej; ochrona newralgicznych reguł.
- Każdy etap kończy się przedstawieniem wyniku i oczekiwaniem na zatwierdzenie przed kolejnym etapem.

Nie pytaj ponownie o te wymagania, chyba że pojawiła się rzeczywista sprzeczność lub prośba o zmianę. Dla bieżącego projektu korzystaj z już zatwierdzonych D01–D14. Nie dopisuj bez podstawy nowych zakresów skanowania, liczby urządzeń ani szczegółów środowiska.

## 3. Wybierz pierwsze środowisko uruchomieniowe

### Jak wykonać

1. Wskaż komputer mający połączenie z badanym LAN. Dostęp do adresów zarządzających jest potrzebny tylko dla rozszerzonych odczytów. To ważniejsze niż system używany tylko do pisania kodu.
2. Zapisz system i wersję, architekturę procesora, RAM, wolne miejsce oraz możliwość instalowania Pythona i zależności.
3. Ustal, czy odczyty będą przechodzić przez lokalny interfejs, VPN czy inną trasę. W Etapie 0 wystarczy opis; nie wykonuj automatycznego skanowania.
4. Zgodnie z D01 wykonaj pierwszy przekrój na macOS ARM, potem krótki odbiór Windows 10/11 x64. Linux pozostaje na później.
5. Zapisz sposób uruchomienia i dostępu do panelu.

**Rekomendacja do zatwierdzenia:** środowisko `venv`, lokalny proces Python, panel w przeglądarce na `127.0.0.1`, jeden operator. Bez wymaganej chmury, kontenera i osobnej usługi bazy danych. Jeżeli laptop używany w badanych sieciach ma macOS, rozpocznij od macOS; jeżeli rzeczywistym narzędziem operatora jest Windows lub Linux, wybierz ten system.

Opcjonalnie sprawdź tylko zainstalowany interpreter. Poniższe polecenia nie instalują bibliotek i nie kontaktują się ze switchami.

macOS/Linux:

```sh
python3 --version
python3 -c 'import platform, sqlite3; print(platform.platform()); print(platform.machine()); print("SQLite:", sqlite3.sqlite_version)'
```

Windows, PowerShell — jeśli dostępny jest launcher `py`:

```powershell
py -3 --version
py -3 -c 'import platform, sqlite3; print(platform.platform()); print(platform.machine()); print("SQLite:", sqlite3.sqlite_version)'
```

Jeśli interpreter jest niedostępny, zapisz „do przygotowania w Etapie 1”. Na tym etapie nie trzeba go instalować. Sam wynik wersji nie potwierdza zgodności wszystkich zależności.

**Co wpisać do karty:** system pierwszego odbioru, parametry komputera, metoda dostępu do sieci, sposób uruchomienia, localhost albo wymaganie zdalnego dostępu. Jeśli wymagany jest dostęp zdalny, logowanie i TLS stają się osobnym zadaniem przed udostępnieniem panelu.

## 4. Ustal zestaw komponentów i warunek bezpłatności

### Jak wykonać

1. Przeczytaj tabelę komponentów i źródła licencji w [planie startowym](../PLAN_STARTOWY.md#2-proponowane-komponenty).
2. Dla każdej funkcji przypisz komponent. Nie pozostawiaj np. eksportu SVG jako funkcji „do dokupienia”.
3. Zaznacz, czy potrzebna funkcja jest dostępna w lokalnej bibliotece open source, bez konta, abonamentu lub aktywacji.
4. Osobno zapisz źródła danych pomocniczych: OUI, ikony, fonty i ewentualne MIB-y. Jeśli źródło nie jest wybrane, pozostaw jawne zadanie sprawdzenia warunków.
5. Zatwierdź dobór komponentów. Dokładne wersje i zgodność całego zestawu sprawdzisz podczas próby w Etapie 1.

Proponowany zestaw:

| Funkcja | Propozycja |
|---|---|
| Interfejsy IPv4/maski | `psutil` — nowy kandydat do próby |
| Trasy/sąsiedzi/sondy | Narzędzia Windows/macOS + biblioteka standardowa; cienki adapter Python |
| SNMPv2c/v3 | PySNMP |
| SSH i odczyt CLI | Netmiko |
| Gotowe parsery | ntc-templates/TextFSM |
| Lokalna baza i historia | SQLite przez `sqlite3` |
| Potrzebne algorytmy grafowe | NetworkX |
| Panel | Dash open source |
| Graf i eksport obrazu | dash-cytoscape |
| JSON/CSV | Biblioteka standardowa Pythona |

Własny Python będzie obsługiwać dobór odczytów, normalizację, korelację, confidence, historię, konfigurację i połączenie panelu z danymi. Nie oznacza to pisania od nowa transportu, parserów, renderera czy bazy.

**Kryterium odrzucenia komponentu:** choć jedna wymagana funkcja potrzebuje triala, ograniczonej edycji free, opłaty, klucza licencyjnego lub obowiązkowej usługi komercyjnej. Bezpłatne używanie biblioteki nie zwalnia z zachowania wymaganych informacji licencyjnych. Sprawdzenie zależności i przygotowanie `docs/THIRD_PARTY_NOTICES.md` są zadaniem Etapu 1.

**Co wpisać do karty:** przyjęty zestaw albo konkretną alternatywę, odnośniki do warunków i pozostałe wątpliwości. Nie zapisuj „wszystkie licencje zweryfikowane”, jeżeli sprawdzono tylko główne biblioteki.

## 5. Określ zakres odczytów i odkrywania

### Jak wykonać

1. Opisz podstawowe wejście: projekt, wybrany interfejs IPv4 i lokalny zakres. Seedy, marka routera i poświadczenia nie są wymagane.
2. Oddziel odczyt lokalnych tras/sąsiadów, sondowanie po kliknięciu „Odkryj” oraz opcjonalne SNMP/SSH i rekurencję LLDP.
3. Przed sondowaniem pokaż zakres, liczbę celów, interfejs i budżet. Domyślny start panelu nie wysyła sond. Przy większej podsieci wybierz mniejszy zakres lub jawnie zmień limit.
4. Dla LLDP zachowaj dozwolony zakres, osiągalny adres i przypisany profil. Sam IP znaleziony w ARP nie uruchamia logowania.
5. Określ zatrzymanie i statusy: anulowanie, timeout, budżet, pominięte cele. Wpis starego cache nie potwierdza świeżej obecności; brak odpowiedzi nie oznacza braku urządzenia.

**Przyjęta korekta zakresu:** podstawowe odkrywanie musi działać bez SNMP/SSH. D06 oznacza brak sond przy samym uruchomieniu panelu; operator uruchamia je w pokazanym lokalnym zakresie. Budżet 5 adresów/s, 256 celów i jedna sonda pozostaje punktem odniesienia. Nowe krótkie timeouty oraz adapter OS sprawdzamy zgodnie z [poradnikiem podstawowym](ETAP_1_ODKRYWANIE_PODSTAWOWE.md). Nie zakładamy skanowania portów, sieci operatora ani innych VLAN-ów.

Nie ustalaj produktu na „maksymalnie 20 switchy”. Zamiast tego ustal regulowany budżet jednego cyklu i próbę wydajnościową. Przykładowy rozmiar laboratorium jest scenariuszem odbioru, a nie ograniczeniem liczby urządzeń w aplikacji.

Wartości zatwierdzone zawiera karta; poniższa lista wskazuje, co sprawdzić podczas próby, bez ponownego otwierania wcześniejszych decyzji:

| Parametr | Propozycja / sposób wyboru |
|---|---|
| Odkrywanie podstawowe | 5 celów/s, 256 celów; proponowane 4 procesy ping, deadline 3 s/proces i 240 s/próbę |
| Równoległość zarządzania | 4 urządzenia; możliwość zmiany |
| Timeout SNMP | 3 s; jedno ponowienie |
| SSH | 10 s na połączenie, 30 s na komendę |
| Limit całego walku | Wybrać maksymalny czas i liczbę rekordów; oznaczać ucięcie |
| Budżet rekurencji | Wybrać czas, liczbę celów i opcjonalną głębokość; oznaczać nieodwiedzone cele |
| Odświeżanie | Ręczne oraz konfigurowalny interwał; bez nakładania cykli |
| Historia | Wybrać okres przechowywania oraz warunki uznania braku obserwacji |

**Co wpisać do karty:** dopuszczone metody, reguły rekurencji, wartości parametrów albo właściciela i termin uzupełnienia. Dobór wartości można skorygować po próbie, lecz Etap 1 musi mieć jawne granice odczytów.

## 6. Zdefiniuj profile SNMP i obsługę sekretów

Ta sekcja dotyczy rozszerzonego mapowania. W podstawowym scenariuszu pozostaw profile puste; nie szukaj community do routera, który nie udostępnia SNMP.

### Jak wykonać

1. Wskaż, które warianty protokołu trzeba sprawdzić: v2c i v3. Dla v3 ustal wymagane poziomy bezpieczeństwa oraz algorytmy uwierzytelniania i szyfrowania obsługiwane przez urządzenia laboratoryjne.
2. Zapisz metadane profilu: identyfikator, wersja protokołu, port, poziom bezpieczeństwa, nazwy algorytmów i kontekst, jeśli potrzebny. Hasła/community przechowuj oddzielnie.
3. Ustal źródło sekretów. Rekomendacją MVP są zmienne środowiskowe, a w konfiguracji tylko odniesienia do nazw profili.
4. Ustal zachowanie dla błędu dostępu: komunikat bez sekretu, ograniczone ponowienia, status nieudanego odczytu i dalsza praca pozostałych celów.
5. Zapisz zasadę: brak automatycznego przejścia z v3 do v2c, jeśli operator nie skonfigurował i nie dopuścił takiego profilu.

Karta nie zawiera community, haseł SNMPv3, haseł SSH, prywatnych kluczy ani zrzutów zmiennych środowiskowych. Zapisz wyłącznie identyfikator profilu i sposób bezpiecznego dostarczenia danych do próby. Nie podawaj sekretów w argumentach poleceń.

**Rekomendacja do zatwierdzenia:** pierwsza próba obejmuje v2c i v3 `authPriv`; konkretne algorytmy wynikają z dostępnego agenta i wymagań docelowych. Jeśli jeszcze ich nie znamy, zapisujemy brak informacji. Mock danych topologii nie potwierdza poprawnego uwierzytelniania v3 — potrzebny będzie agent w laboratorium.

Jeżeli badane sieci mają VRF lub konteksty SNMP, zapisz sposób ich jawnego wskazania oraz dostępność przykładu. Brak kontekstu nie uprawnia do scalania powtarzających się IP.

**Co wpisać do karty:** profile bez sekretów, wymagany zestaw v3, źródło poświadczeń i dostępność agenta do Etapu 1.

## 7. Wybierz pierwszą platformę SSH

Wybrana platforma służy próbie parsera, nie ogranicza podstawowego skanowania do jednej marki. Brak Cisco nie blokuje odkrywania w domowym LAN.

### Jak wykonać

1. Wybierz rodzinę systemu rzeczywiście dostępną w laboratorium albo w zanonimizowanych materiałach. Nie wybieraj tylko na podstawie rozpoznawalności marki.
2. Zapisz producenta, model, rodzinę systemu i dokładną wersję. Różne rodziny jednego producenta nie muszą mieć takich samych komend ani formatu odpowiedzi.
3. W dokumentacji Netmiko i ntc-templates sprawdź kandydata na sterownik i gotowe szablony. To sprawdzenie dostępności, jeszcze nie dowód poprawnego parsowania konkretnego urządzenia.
4. Zdobądź przykłady odczytów: tablica MAC, ARP, VLAN-y, interfejsy i LLDP. Polecenia zależą od platformy; nie zakładaj jednej uniwersalnej listy `show`.
5. Spisz planowaną listę dozwolonych komend. Uwzględnij inicjalizację sesji przez sterownik; nie zatwierdzaj poleceń zmieniających konfigurację urządzenia.
6. Jeśli brakuje szablonu, opisz konkretną lukę. Własny adapter/parser powstanie dopiero po potwierdzeniu, że istniejący komponent nie wystarcza.

**Rekomendacja do zatwierdzenia:** jedna platforma SSH w pierwszym przekroju MVP, wybrana według dostępności urządzenia i parserów. Pozostałe platformy mają jawny status nieobsługiwany/niezweryfikowany dla SSH; standardowe odczyty SNMP pozostają osobną ścieżką.

Jeśli nie masz urządzenia SSH, nie wymyślaj modelu ani wersji. Zapisz blokadę próby SSH, sposób uzyskania materiałów oraz decyzję, czy Etap 1 może zacząć się od pozostałych komponentów. Obsługa fallbacku pozostaje wymaganiem; przesunięcie jego próby nie jest dowodem realizacji.

**Co wpisać do karty:** model/system/wersja, kandydat na sterownik, szablony i brakujące próbki. Same nazwy „Cisco” lub „HP” są zbyt ogólne.

## 8. Przygotuj materiał do odbioru

Nie musisz znać wszystkich przyszłych sieci. Potrzebujesz kontrolowanego przypadku, dla którego znasz prawidłową odpowiedź.

Przygotuj dwa niezależne scenariusze. **Podstawowy:** zwykły LAN z routerem i 2–3 znanymi aktywnymi hostami, bez dostępu SNMP/SSH. Sprawdź wykryte IPv4, lokalne MAC tam, gdzie dostępne, logiczne relacje oraz nieustalone porty/VLAN-y. Dodaj host bez odpowiedzi ICMP i odróżnij cache od świeżego dowodu. Internet nie jest wymagany.

**Rozszerzony:** przygotuj opis laboratorium: dwa switche, kilka hostów, dwa VLAN-y, uplink, dostęp do ARP na urządzeniu L3 oraz możliwość bezpiecznej zmiany podłączenia hosta przez operatora w laboratorium. Aplikacja wykonuje tylko odczyty. Jeżeli fizyczne laboratorium jest niedostępne, topologię i historię można sprawdzać snapshotami, ale próby protokołów wymagają agentów/urządzeń.

Zapisz oczekiwane połączenia oraz źródła potwierdzenia. Nie wykonuj teraz zmian w konfiguracji switchy. Materiały z rzeczywistych sieci anonimizuj spójnie: zachowaj relacje IP/MAC/VLAN/port, usuń sekrety i niepotrzebne dane identyfikujące organizację.

Ustal kryteria w dwóch osobnych grupach:

| Etap 1 — próba komponentów | Późniejszy odbiór MVP |
|---|---|
| Podstawowe odkrywanie bez seedów i poświadczeń | Mapa logiczna bez zgadywania kabli, portów i VLAN-ów |
| Zakres/interfejs/limity oraz brak odpowiedzi/cache | Brak fałszywego zniknięcia i brak skanowania inną trasą |
| Odczyt v2c i v3 authPriv z laboratorium | Host przypisany do portu/VLAN z dowodami |
| Jedna sesja SSH i wynik istniejącego parsera | MAC widoczny na uplinku nie daje fałszywego bezpośredniego przypisania |
| Graf ze snapshotu w lokalnym panelu | Awaria switcha nie oznacza automatycznie zniknięcia wszystkich hostów |
| Pobranie PNG i SVG bez zewnętrznej usługi | Zmiana portu trafia do historii |
| Uzgodnione wersje i licencje zależności | Identyczne IP w różnych projektach pozostają odseparowane |
| Brak sekretów w logach/wynikach próby | Filtry, szczegóły, JSON/CSV/SVG/PNG i odtworzenie offline działają |

Rozmiar próby wydajnościowej zapisz oddzielnie: liczba urządzeń/rekordów/węzłów, sprzęt i akceptowalny czas. Docelowo aplikacja działa w różnych sieciach; próba mierzy konkretny przypadek i nie daje gwarancji dla każdej możliwej skali.

**Co wpisać do karty:** dostępne materiały, oczekiwane wyniki, osoba potwierdzająca poprawność i brakujące przypadki, np. MLAG/VRF. Nie deklaruj ich pełnego wsparcia bez dowodów.

## 9. Zamknij ryzyka i zadania otwarte

Wpisz krótką listę konkretnych ryzyk. Dla każdego podaj skutek, następne działanie i moment sprawdzenia. Wystarczy jedna tabela; nie twórz rozbudowanego procesu zarządzania ryzykiem.

| Przykład ryzyka | Działanie |
|---|---|
| Router nie ma SNMP/SSH | Podstawowy skan pozostaje dostępny; port/VLAN nieustalony |
| Wi-Fi izoluje klientów lub VPN zmienia trasę | Pokazać ograniczony zasięg; nie zmieniać ustawień i nie zgadywać połączeń |
| Urządzenie nie udostępnia pełnego FDB/VLAN | Sprawdzić odczyty w Etapie 1/2; pokazywać wynik niepełny, rozważyć istniejący parser SSH |
| Brak agenta SNMPv3 do próby | Zapewnić laboratorium przed potwierdzeniem działania v3 |
| Nieznane warunki bazy OUI | Wybrać i zweryfikować źródło przed dołączeniem danych |
| Brak dowodów dla MLAG/VRF | Zachować kontekst/niepewność; nie scalać urządzeń po samym IP |
| Zbyt duży graf w przeglądarce | Ustalić próbę oraz widoki z filtrowaniem i rozwijaniem hostów |

Zadanie otwarte powinno wskazywać, czy blokuje Etap 1, czy można je rozwiązać później. Nie pozostawiaj bez decyzji granic odczytu, obsługi sekretów ani funkcji wymagającej potencjalnej opłaty.

## 10. Zatwierdź wynik i przekaż do Etapu 1

Przejrzyj kartę według listy:

- [ ] Ustalone wymagania są zachowane; propozycje nie zostały przedstawione jako zatwierdzone.
- [ ] Wybrano pierwszy system, sposób uruchomienia i zasady dostępu do panelu.
- [ ] Wybrano komponenty spełniające wymóg pełnej bezpłatności; zaplanowano kontrolę zależności w Etapie 1.
- [ ] Określono granice odczytów, rekurencji i ewentualnego sondowania oraz parametry pierwszej próby.
- [ ] Start bez seedów/poświadczeń ma kryteria odbioru; profile SNMP są potrzebne tylko dla próby rozszerzonej.
- [ ] Wybrano pierwszą platformę SSH albo jawnie rozstrzygnięto brak materiałów.
- [ ] Rozdzielono domowy LAN do podstawowego skanu, snapshot offline i laboratorium protokołów; braki nie udają zaliczonych prób.
- [ ] Pozostałe zadania mają właściciela, termin/etap i informację, czy blokują próbę.
- [ ] Właściciel projektu zatwierdził kartę lub wskazał korekty; zapisano datę i zakres zatwierdzenia.

Przedstaw do zatwierdzenia wypełnioną kartę, zwięzłą listę ryzyk i plan próby komponentów. Zatwierdzenie Etapu 0 pozwala rozpocząć Etap 1 w przyjętych granicach. Nie oznacza zgody na skanowanie dowolnych sieci, zmianę konfiguracji urządzeń ani rozszerzenie stosu o płatne usługi.

Jeżeli potrzebne informacje są nieznane, zatwierdzenie może określić warunki: np. próba grafu offline jest dopuszczona, a odczyty urządzeń czekają na wskazanie zakresu i profili. Zapisz te warunki w karcie zamiast domyślać się odpowiedzi.

## Źródła do sprawdzenia w czasie wykonywania etapu

Punktem odniesienia jest [plan startowy](../PLAN_STARTOWY.md), zawierający źródła licencji sprawdzone przy jego opracowaniu. Przy faktycznym wyborze wersji zweryfikuj odpowiadające im dokumenty upstream:

- [Poradnik podstawowego odkrywania](ETAP_1_ODKRYWANIE_PODSTAWOWE.md).
- [psutil — API i interfejsy sieciowe](https://psutil.io/).
- [PySNMP — dokumentacja](https://docs.lextudio.com/pysnmp/v7.1/).
- [Netmiko — repozytorium i obsługiwane platformy](https://github.com/ktbyers/netmiko).
- [ntc-templates — istniejące szablony](https://github.com/networktocode/ntc-templates).
- [dash-cytoscape — eksport obrazów](https://dash.plotly.com/cytoscape/images).

Ten poradnik nie stanowi raportu z instalacji ani potwierdzenia działania protokołów lub parserów. Takie dowody powstaną podczas próby komponentów.
