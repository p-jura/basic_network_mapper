# AGENTS — Maper sieci

Ten plik jest obowiązującą instrukcją dla agentów pracujących w tym
repozytorium. Jeśli polecenie użytkownika jest z nim sprzeczne, nie wykonuj
ryzykownej zmiany po cichu: opisz konflikt, zagrożenie i bezpieczny następny
krok.

## 1. Zanim zaczniesz

1. Przeczytaj ten plik w całości i sprawdź `git status`. Nie usuwaj,
   nie nadpisuj ani nie porządkuj cudzych zmian przy okazji.
2. Ustal aktywny wariant projektu. Głównym produktem jest lokalny mapper
   Python opisany w `README.md`, `docs/WYMAGANIA_PROJEKTU.md` i `docs/PLAN_STARTOWY.md`.
   Materiały Flutter/Dart są osobnym wariantem historycznym i nie stanowią
   domyślnej architektury tego repozytorium.
3. Przeczytaj wpis zadania/Issue i bieżący poradnik z `docs/poradniki/` wskazany
   w `docs/PLAN_STARTOWY.md`. Jeśli brakuje Issue, planu lub kryteriów, zapisz
   niepewność i nie rozszerzaj zakresu samodzielnie.
4. Zastosuj routing dokumentów poniżej; czytaj tylko dokumenty i sekcje
   istotne dla zmiany. Przed zmianą decyzji produktowej lub architektonicznej
   przeczytaj źródłową kartę decyzji i zaktualizuj ją przed kodem.
5. Nie uruchamiaj aktywnego odkrywania sieci podczas pracy nad kodem lub
   testami. Testy korzystają z fixture'ów, atrap i lokalnych danych; aktywny
   skan wymaga osobnego, jawnego polecenia operatora i wskazanego zakresu.

Dokumentacja projektu znajduje się w `docs/`; spis treści: `docs/README.md`.
`README.md` i ten plik pozostają punktami wejścia w głównym katalogu.

### Routing dokumentacji

| Obszar zadania | Wymagane źródła |
|---|---|
| Produkt, podstawowe odkrywanie, zakres MVP | `README.md`, odpowiednie sekcje `docs/WYMAGANIA_PROJEKTU.md` i `docs/PLAN_STARTOWY.md`, aktywny poradnik Etapu 1 |
| Model danych, SQLite, izolacja projektów, historia | odpowiednie sekcje `docs/PLAN_STARTOWY.md` i `docs/poradniki/ETAP_2_MODEL_DANYCH_I_KOLEKTORY.md`; dodatkowo uzgodnienia bezpieczeństwa w `docs/WYMAGANIA_PROJEKTU.md` |
| Interfejsy, trasy, ARP/sąsiedzi, ping, podstawowy skaner | `docs/PLAN_STARTOWY.md` §4–6, `docs/poradniki/ETAP_1_ODKRYWANIE_PODSTAWOWE.md`; zweryfikuj zachowanie platformy w kodzie i testach |
| SNMP, SSH, FDB, VLAN, LLDP, korelacja topologii | odpowiednie sekcje `docs/PLAN_STARTOWY.md`, `docs/poradniki/ETAP_2_MODEL_DANYCH_I_KOLEKTORY.md`, wymagania dot. tylko odczytu i sekretów |
| Panel, graf, eksport, offline | `README.md`, `docs/PLAN_STARTOWY.md` §7 i właściwe kryteria odbioru w poradnikach |
| Zależności, pakowanie, licencje | `docs/PLAN_STARTOWY.md` §2, `docs/WYMAGANIA_PROJEKTU.md` — bezpłatność komponentów i zachowanie notice/licencji |
| CI lub narzędzia repozytorium | sprawdź najpierw, czy istnieje dedykowany workflow/plan; projekt zakłada brak rozbudowanego CI/CD, nie dodawaj go bez uzasadnionej potrzeby i akceptacji |
| Flutter/Dart | tylko gdy użytkownik jawnie wybierze odrębny wariant Flutter/Dart; wtedy użyj `docs/archiwum/flutter-dart/PLAN_APLIKACJI_TOPOLOGII_MVP.md` i `docs/archiwum/flutter-dart/PORADNIK_ETAP_0_1.md`, nie mieszaj jego kodu ze stosem Python |

## 2. Nienegocjowalne zasady bezpieczeństwa sieci

- Skanuj wyłącznie sieci i urządzenia, do których operator ma prawo dostępu.
  Przed aktywnymi sondami pokaż/ujawnij interfejs, źródłowy adres IPv4,
  wybrany zakres, liczbę adresów i budżet; odkrywanie rozpoczyna wyraźna
  akcja operatora. Nie skanuj automatycznie przy starcie aplikacji.
- Nie skanuj całego Internetu, sąsiadujących sieci ani zakresu wybranego
  domyślnie przez przypadek. Nie wykonuj skanowania portów ani brute force.
  Przestrzegaj limitów liczby celów, tempa, równoległości, timeoutu,
  ponowień i anulowania opisanych w aktywnym planie.
- Wszystkie odczyty konfiguracji urządzeń są tylko do odczytu. SNMP używa
  wyłącznie GET/GETNEXT/GETBULK. SSH korzysta z jawnej allowlisty poleceń
  odczytowych i weryfikacji klucza hosta. Bez SNMP SET, zmian konfiguracji,
  restartów, czyszczenia ARP ani modyfikowania interfejsów/trasy/VLAN/PoE.
- Sekrety nie trafiają do kodu, argumentów procesu, logów, wyjątków,
  screenshotów, eksportów, testowych fixture'ów ani repozytorium. Nie zgaduj
  ani nie wyszukuj community/passwordów. Używaj uzgodnionego lokalnego
  mechanizmu ochrony; wartości redaguj przed logowaniem. Sekrety nie są
  przechowywane w zwykłej bazie SQLite bez jawnej decyzji i ochrony.
- Wywołania systemowe uruchamiaj przez listę argumentów (`shell=False`),
  z walidacją adresów i timeoutem. Nie składaj poleceń shell z danymi
  użytkownika. Proces potomny musi mieć ograniczenie czasu i ścieżkę anulowania.
- Błąd, timeout, brak ICMP/SNMP/SSH, stary wpis ARP lub niepełny cykl nie
  dowodzi nieistnienia urządzenia ani nie odłącza go automatycznie. Zachowuj
  źródło, zakres, czas i świeżość obserwacji; niepewność pokazuj jawnie.
- Nie wyprowadzaj fizycznego portu, VLAN-u, modelu sprzętu ani połączenia
  kablowego z samej nazwy, OUI, IP, bramy, liczby MAC-ów czy położenia
  w grafie. Logiczne sąsiedztwo i potwierdzony fizyczny link to różne relacje.
- Każdy projekt/środowisko jest izolowane również przy identycznych adresach
  IP. Awaria kolektora nie oznacza zniknięcia hostów; snapshot częściowy ma
  status i ograniczenia.

## 3. Granice rozwiązania

- Główny wariant: jedna lokalna aplikacja Python 3.13 w środowisku venv;
  zatwierdzony kierunek używa SQLite, NetworkX, Dash/dash-cytoscape oraz
  opcjonalnych adapterów psutil, PySNMP i Netmiko/parserów. Sprawdź aktualny
  plan i wersje przed dodaniem zależności.
- Nie pisz własnego stosu SNMP/SSH ani gotowego produktu mapowania. Korzystaj
  z bibliotek/systemowych adapterów do protokołów, a własny kod przeznaczaj
  na walidację zakresu, kolekcję, normalizację dowodów, korelację, historię
  i panel.
- Domyślna struktura docelowa opisana jest w `docs/PLAN_STARTOWY.md` §10:
  `src/mapper/{discovery,collectors,topology,storage,ui}`. Istniejące
  `prototypes/tools/` to robocze próby; po potwierdzeniu ich zastąpienia stosuj
  zasady porządkowania poniżej, zachowując zawartość i poprawiając odwołania.
- Oddzielaj adaptery systemowe/protokołów, logikę domenową, persystencję
  i interfejs. Widget/callback UI nie powinien samodzielnie wykonywać
  długiego skanu, wyliczać topologii ani omijać limitów kontrolera.
- Panel nasłuchuje tylko lokalnie (`127.0.0.1`), otwiera się po potwierdzeniu
  gotowości serwera i używa rzeczywistego portu. Uruchomienie panelu nie
  rozpoczyna kolekcji. Nie dodawaj CDN, obowiązkowej chmury, Redis,
  mikroserwisów ani płatnych komponentów bez zaakceptowanej zmiany decyzji.
- Nie dodawaj ukrytej globalnej mutowalności, niejawnego skanowania,
  nieograniczonej współbieżności ani automatycznych retry bez limitu.

## 4. Zmiany i decyzje

- Najpierw doprecyzuj plan/kryteria, potem implementuj najmniejszą zmianę.
  Nowa funkcja kolektora musi określać: źródło danych, uprawnienia,
  zakres, timeout/limit, zachowanie przy braku danych, wpływ na świeżość
  i sposób prezentowania niepewności.
- Zmiana architektury, bazy/modelu danych, granicy projektu, obsługi sekretów,
  zakresu skanowania, protokołu lub warunków licencyjnych wymaga zapisanej
  decyzji (ADR/karty decyzji) przed wdrożeniem. Nie zmieniaj zatwierdzonej
  decyzji „przy okazji”.
- Nie dodawaj zależności, jeśli nie jest potrzebna; przed wyborem sprawdź
  licencję, darmowe użycie, ograniczenia urządzeń/funkcji, zależności
  pośrednie i możliwość pracy offline. Aktualizuj informacje licencyjne
  wymagane do dystrybucji.
- Nie deklaruj zgodności Windows/macOS/Linux, wsparcia producenta, pełnego
  odkrywania, wydajności ani odbioru funkcji bez testu/raportu dla danego
  środowiska. Oznacz propozycję, próbę i potwierdzony wynik osobno.
- Zachowuj zakres: bez szerokiego refaktoringu, automatycznego formatowania
  obcych plików, porządkowania materiałów historycznych i zmian Flutter/Dart
  niezwiązanych z zadaniem.

### Bieżące porządkowanie i katalog old

- Utrzymuj porządek podczas kolejnych prac. Zgodnie z poleceniem użytkownika
  z 24 października 2026 r. potwierdzone jako zbędne lub zastąpione elementy
  przenoś najpierw do `old/`, zamiast trwale je usuwać.
- Zachowuj oryginalną strukturę w `old/RRRR-MM-DD/<poprzednia-ścieżka>`;
  nie nadpisuj wcześniejszego archiwum. Wpisz poprzednią i nową ścieżkę,
  przyczynę przeniesienia oraz ewentualny zamiennik w `docs/OLD.md`.
- Przed przeniesieniem sprawdź odwołania, importy, uruchamianie i pakowanie;
  popraw potrzebne ścieżki. Aplikacja nie może zależeć od elementów w `old/`.
  Nie uznawaj pliku za zbędny wyłącznie na podstawie nazwy lub wieku.
- Dokumentacja nadal należy do `docs/`. `docs/archiwum/` zachowuje materiały
  historyczne do wglądu; `old/` jest tymczasowym miejscem elementów
  przeznaczonych do późniejszego usunięcia. Nie przenoś tam sekretów ani
  prywatnych danych sieciowych.
- Trwałe usunięcie zawartości `old/` zostaw na końcowe porządki po zakończeniu
  projektu. Wcześniej nie usuwaj zachowanych materiałów; nie dotykaj cudzych
  niezwiązanych zmian ani elementów o nieustalonym przeznaczeniu.

## 5. Testowanie i jakość

- Projekt nie zakłada obecnie rozbudowanego CI/CD ani wielkiej test suite.
  Chronimy krytyczne reguły i ręczne scenariusze wskazane w `docs/PLAN_STARTOWY.md`
  §9 oraz aktywnym poradniku. Nie dodawaj drogiej infrastruktury bez potrzeby.
- Testy jednostkowe nie wysyłają ruchu do sieci. Używaj atrap adapterów,
  deterministycznych fixture'ów i testowych SQLite; nigdy prawdziwych
  poświadczeń ani niekontrolowanych hostów.
- Co najmniej sprawdź dotkniętą logikę: zakres/interfejs i limit celów,
  timeout/anulowanie, obsługę niepełnego cyklu i cache, źródła/świeżość,
  brak zgadywanych portów/VLAN-ów, izolację projektów i brak sekretów.
- Przed przekazaniem uruchom dostępne testy/lint/typowanie dla zmienionych
  komponentów, sprawdź diff oraz `git diff --check`. Zapisz dokładne komendy,
  wynik i niewykonane próby. Nie przedstawiaj ręcznej inspekcji jako
  automatycznego testu.
- Ręczny test aktywnego odkrywania wykonuje się wyłącznie po osobnej zgodzie
  operatora, w wybranej przez niego autoryzowanej sieci i w pokazanym limicie.

## 6. Git i przekazanie

- Przed zmianą zachowaj zastane pliki i stan Git. Preferuj krótki branch
  `feat/<zakres>` lub `docs/<zakres>` od zatwierdzonej bazy; jeśli repozytorium
  nie ma jeszcze ustalonego workflow/remote, nie zakładaj ich ani nie
  inicjalizuj zdalnych usług bez zgody.
- Nie wykonuj force-push, resetu, usuwania branchy, pushu/merge do `main`
  ani operacji na zdalnym repo bez wyraźnego upoważnienia. Jeżeli repozytorium
  wprowadzi PR workflow, wszystkie merge wykonuj wyłącznie przez PR.
- Podsumowanie podaje zakres, zmienione pliki, walidację, ograniczenia lub
  nierozstrzygnięte decyzje oraz bezpieczny następny krok. Nie twierdź, że
  commit, push, test sieciowy ani odbiór użytkownika zaszły, jeśli nie ma na
  to dowodu.

## 7. Definition of Done

Zadanie jest gotowe, gdy kryteria i granice sieci są spełnione; testy
dotkniętego obszaru przechodzą; bezpieczeństwo sekretów i aktywnych sond
zostało sprawdzone; ograniczenia/niepewność są widoczne; dokumentacja
odpowiada zachowaniu; zależności/licencje są udokumentowane, jeśli dodano;
diff nie zawiera przypadkowych danych ani zmian; a niewykonane testy i
blokady są jawnie wymienione.
