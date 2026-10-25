# Etap 4 — panel i pełny przepływ operatora

Data: **25 października 2026 r.** Status: **plan i wynik wdrożenia 0.4.0 zatwierdzone przez użytkownika; Etap 4 zamknięty w przedstawionym zakresie**. Użytkownik polecił przygotować kolejny krok słowami „dzialaj”, w odpowiedzi na propozycję sporządzenia szczegółowego planu. Następnie użytkownik zatwierdził wdrożenie słowami „masz zgode na dzialanie. Wdrazaj”. Nie jest to zapis odbioru Windows, switcha ani nowej zgody na aktywne sondowanie.

Podstawa: [plan główny §7–9](../PLAN_STARTOWY.md), [karta D02/D06/D09/D11/D12/D14](KARTA_ETAP_0.md), [raport 3.1](../etap-3-1/RAPORT_ETAP_3_1.md), [propozycja ADR-006](../decisions/ADR-006-panel-i-kontroler.md). Dokument zachowuje zakres planu; polecenie `mapper panel` i moduły `ui` są już wdrożone. Faktycznie wykonane próby i ograniczenia opisuje [raport Etapu 4](../etap-4/RAPORT_ETAP_4.md), a użycie panelu [poradnik uruchomienia](ETAP_4_URUCHOMIENIE_I_ODBIOR.md).

## 1. Cel i stan wejściowy

Operator uruchamia jedną aplikację, wybiera projekt i działa w przeglądarce: otwiera zapisany wynik albo przygotowuje zakres, uruchamia kolekcję, śledzi postęp, ogląda mapę, historię i eksportuje dane. Podstawowy tryb nie wymaga seedów ani danych logowania. Wszystkie akcje sieciowe mają jawny zakres i start operatora.

| Jest w 0.3.1 | Brakuje w Etapie 4 |
|---|---|
| CLI: projekty, kolekcja, snapshoty, topologia, historia | Obsługa tych operacji w panelu |
| Dash: prosty podgląd zapisanego grafu i surowe szczegóły | Formularze, przyjazne szczegóły, filtry i historia |
| Limity, anulowanie w kolektorach i jedna kolekcja | Kontroler pracy w tle i przycisk anulowania |
| Wyniki sond publikowane po zakończeniu partii | Bieżące liczniki bez zapisywania nowego snapshotu co sondę |
| Blokada projektu przez czas życia Repository | Mapa z kopii w pamięci podczas kolekcji; brak współdzielenia połączenia SQLite między wątkami |
| Eksport źródeł JSON/CSV i grafu JSON z CLI | Eksporty z panelu, CSV topologii, PNG/SVG |

Stan bazowy: 38 testów krytycznych i odbiór offline 3.1 na macOS ARM. Windows IPv4/NTFS sprawdzono tylko na atrapach; SNMP/SSH na rzeczywistych urządzeniach i duża skala nadal wymagają prób. Dodanie kodu na `main` nie potwierdza tych odbiorów. Formalnego zatwierdzenia wyniku Etapu 3 nie dopisujemy wstecz; zatwierdzenie niniejszego planu będzie zgodą na rozpoczęcie Etapu 4 na opisanej bazie.

## 2. Zakres i wynik

W ramach etapu wykonujemy:

- projekty: lista, utworzenie, wybór, syntetyczne demo oraz import snapshotu do nowego projektu;
- konfigurację interfejsu, zakresów i limitów oraz opcjonalnych seedów/profili ENV;
- podgląd zakresu bez sond, ręczny start, postęp, anulowanie i opt-in odświeżanie;
- mapę, wyszukiwanie, filtr VLAN, szczegóły węzła/krawędzi i historię;
- lokalne eksporty danych/obrazu oraz tryb offline;
- minimalne zabezpieczenia lokalnego panelu, małe testy integracji i raport.

Pozostają dotychczasowe biblioteki i architektura jednego procesu. Nie planujemy nowego backendu HTTP, usług, kont użytkowników, własnych protokołów, nowych producentów SSH ani nowych systemów. Pakowanie i odbiór na sprzęcie pozostają Etapem 5. Nie zmieniamy reguł korelacji i historii przy okazji prezentacji danych.

## 3. Układ panelu i podstawowe scenariusze

Układ desktopowy: pasek projektu i snapshotu u góry; zwijana konfiguracja po lewej; mapa na środku; szczegóły po prawej; zakładka historii i obszar postępu. Własny lokalny CSS, fonty systemowe, polskie etykiety. Przy mniejszej szerokości szczegóły pod mapą. Ruch i powiększenie mapy, wybór elementu, „Dopasuj”, „Ułóż ponownie”; zwykłe odświeżenie statusu nie resetuje pozycji grafu.

### 3.1. Nowa sieć bez poświadczeń

1. Uruchom panel; pokaż wybór/utworzenie projektu. Brak sondowania.
2. Wybierz interfejs spośród aktywnych IPv4. Pokaż źródło, maskę i bramę według tras albo „nieustalona”. Przy kilku adresach bez jednoznacznego wyboru zablokuj start; nie wybieraj VPN po cichu.
3. Zaproponuj CIDR z maski. Za szeroka podsieć wymaga zawężenia albo jawnej zmiany budżetu. Nie obcinaj listy do pierwszych 256 adresów.
4. Po zmianie konfiguracji pokaż aktualny podgląd: interfejs, źródło, zakres, liczba celów, zgodność tras, tempo, równoległość, deadline. To lokalny odczyt bez sond.
5. Kliknięcie „Odkryj wskazany zakres” uruchamia dokładnie pokazany plan. Walidacja serwera obowiązuje niezależnie od stanu przycisku; zmiana planu unieważnia poprzedni podgląd.
6. Podczas pracy pokaż postęp i „Anuluj”; dotychczasowa mapa ma oznaczenie czasu i snapshotu, nie udaje wyniku bieżącej kolekcji.
7. Po publikacji snapshotu przelicz topologię istniejącym silnikiem i podmień widok. Niepełny wynik jest widoczny wraz z powodami. Błąd korelacji nie usuwa snapshotu źródłowego ani poprzedniej mapy.

### 3.2. Sieć zarządzalna — opcjonalne rozszerzenie

Operator dodaje seedy IPv4, port, identyfikator profilu oraz kontekst zgodny z modelem. Profil zawiera wyłącznie nazwy ENV i niesekretne opcje: SNMPv2c, SNMPv3 SHA-256/AES-128 lub istniejące SSH `cisco_ios` z plikiem known_hosts. SHA-1 tylko po jawnym wyborze profilu zgodności. Nie przyjmujemy hasła/community w formularzu i nie wysyłamy wartości ENV do przeglądarki.

Panel pokazuje wyłącznie „wymagana zmienna dostępna/niedostępna”, bez jej wartości. Zmienne muszą istnieć w środowisku procesu przy uruchomieniu; panel nie edytuje powłoki. Seedy muszą mieścić się w pokazanym, jawnym zakresie zarządzania. Wymóg ten doprecyzowuje walidację UI również wtedy, gdy dotychczasowy CLI pozwalał na puste allowed_ranges; nie rozszerza uprawnień sond.

Rekurencja LLDP jest opt-in: wymaga dozwolonych zakresów i jednego przypisanego profilu, pokazuje limit urządzeń/głębokości/czasu. Nie logujemy się do każdego IP znalezionego w ARP. Nie dodajemy automatycznego sprawdzania wszystkich profili ani akceptacji nieznanego klucza SSH. Brak dostępu zarządzającego nie blokuje oddzielnego podstawowego cyklu; nie zmieniamy profilu automatycznie.

### 3.3. Offline

Proponowane polecenie `mapper panel --offline` blokuje w kontrolerze preview online, sondy, SNMP/SSH i automatyczne odświeżanie. Pozwala tworzyć projekty/demo, wczytywać ograniczony rozmiarem snapshot, oglądać mapę/historię i eksportować. Import nigdy sam nie uruchamia kolektorów. Samo odłączenie Internetu nie jest blokadą skanowania LAN; to osobne scenariusze.

Import przez wybór pliku w przeglądarce, wyłącznie JSON istniejącego formatu źródłowego v1, do nowego UUID projektu. Obowiązują obecne limity 100 MiB i 200 tys. rekordów; limit żądania HTTP uwzględnia narzut base64 i jest sprawdzany także przed parsowaniem. Wgrany plik trafia do prywatnego pliku tymczasowego, usuwanego po operacji. Odrzucamy zły format i przekroczony rozmiar; nie dodajemy archiwów ZIP ani dowolnych ścieżek serwera. Import może wymagać dodatkowej pamięci — podlega pomiarowi, nie zwiększamy limitu na potrzeby UI.

## 4. Kontroler kolekcji, blokady i postęp

Proponowana realizacja w [ADR-006](../decisions/ADR-006-panel-i-kontroler.md): jeden kontroler na instancję aplikacji, z jawnymi zależnościami. Callback Dash przekazuje polecenie i szybko wraca. Jeden dedykowany pracownik wykonuje asyncio, kolekcję i build; osobny, pojedynczy pracownik obsługuje zadania offline innych projektów, bez kolejki; utworzone w nim Repository/SQLite pozostaje w tym wątku. Nie dodajemy menedżera wieloprocesowego.

Stan zadania: `idle → preparing → collecting → building → finished`; dodatkowo `cancelling`, `cancelled`, `failed`. Osobno zapisany execution_status i coverage_status cyklu. Kolekcja nie jest zakończona sukcesem tylko dlatego, że skończył się spinner.

- Zachowujemy globalny cycle lock i project lock 3.1; kontroler dodatkowo odrzuca podwójny start/dwuklik i drugą kartę. Lock systemowy chroni także przed CLI i drugą instancją aplikacji.
- Po publikacji źródeł zwalniamy cycle lock; build nadal trzyma projekt. Nie współdzielimy połączenia SQLite z callbackiem ani nie włączamy check_same_thread=False.
- Pracownik publikuje mały, niezmienny obraz postępu; callback odczytuje go co około 1 s. Nie odpytuje zajętej bazy przy każdym ticku i nie pobiera całej topologii co sekundę.
- Minimalny opcjonalny hook postępu dodajemy w `collect_basic`/`run_cycle`: liczniki sond oraz zakończonych tabel/urządzeń. Nie przenosi surowych odpowiedzi ani sekretów. CLI bez hooka działa jak dotąd. Zdarzenia są agregowane, nie tworzą nieograniczonej kolejki ani nowego formatu snapshotu.
- Podstawowy postęp rozróżnia: odpowiedź, brak odpowiedzi, błąd, pominięcie i jeszcze nieprzetworzone cele. „Nieprzeskanowany” pozostaje osobny od „nie odpowiedział”. Wyświetlamy etap i czas; dla rosnącej rekurencji LLDP liczniki zamiast fałszywego procentu całości.
- Anulowanie przekazuje sygnał bezpiecznie do pętli asyncio i zatrzymuje przydzielanie pracy; bieżące operacje kończą się w istniejących timeoutach. Stan cancelling trwa do faktycznego posprzątania wątków/procesów i publikacji wyniku częściowego. Nie obiecujemy natychmiastowego zatrzymania istniejącego SSH.
- Zamknięcie karty nie zatrzymuje procesu. Ctrl+C zamyka serwer, rozbraja harmonogram i uruchamia kontrolowane anulowanie; nie porzuca aktywnych operacji w daemon thread. Awaria procesu korzysta z obecnego recover_interrupted przy następnym cyklu, bez automatycznego wznowienia skanu.
- Mapa i historia aktywnego projektu korzystają z ostatniej kopii; nowy odczyt tej bazy może zwrócić PROJECT_BUSY. Operacje innego projektu są dozwolone zgodnie z 3.1, ale kontroler nie tworzy kolejki kolejnych skanów.

### Odświeżanie cykliczne D12

Domyślnie wyłączone. Operator może uzbroić powtarzanie tego samego, wyświetlonego planu; domyślny interwał 15 min od zakończenia całego poprzedniego zadania. Wartość edytowalna i walidowana, bez nadrabiania zaległych uruchomień i nakładania cykli. Powtarzanie jest stanem bieżącego procesu, nie odtwarza się po ponownym uruchomieniu panelu.

Zmiana projektu, zakresu, profilu, interfejsu/źródła, błąd lub anulowanie rozbrajają serię. Przed kolejnym cyklem kontroler ponownie sprawdza zgodność sieci i konfiguracji; zmiana wymaga nowego podglądu oraz akcji operatora. Blokada zajęta przez inny proces oznacza pominięcie terminu i jawny stan, bez kolejki. Przycisk „Zatrzymaj odświeżanie” zatrzymuje przyszłe starty; aktywny cykl ma osobne „Anuluj”.

## 5. Projekty, konfiguracja i lokalny serwer

- Lista projektów tylko z ustalonego data_root i poprawnych UUID. Nazwy użytkownika nie są ścieżkami. Błędny/zajęty projekt daje lokalny komunikat; nie zatrzymuje panelu. Nie dodajemy usuwania projektów.
- Edycja project.json pod project lockiem; konfiguracja przechodzi istniejącą walidację. Zapis przez nowy prywatny plik w tym samym katalogu i atomową podmianę, z zachowaniem ochrony POSIX/DACL. Zmiana konfiguracji podczas cyklu tego projektu jest zablokowana. Zmiany formularza nie modyfikują uruchomionego planu.
- Proponowane uruchomienie: `mapper panel [--port 8050] [--no-browser] [--offline] [--data-dir ...]`. Dotychczasowe CLI i `topology view` zachowują działanie. Opcje będą opisane po implementacji; teraz nie należy ich traktować jako gotowych komend.
- Serwer tylko `127.0.0.1`, debug/reloader wyłączone; najpierw skuteczny bind, potem gotowość i otwarcie rzeczywistego URL. Zajęty port daje błąd bez otwierania innej instancji lub jej zatrzymywania. Gdy przeglądarka się nie otworzy, terminal podaje adres.
- Minimalna ochrona lokalnych operacji: sprawdzanie Host oraz Origin przy żądaniach zmieniających stan i losowy token sesji/instancji. Token w prywatnym ciasteczku/sesji, bez logowania i parametrów URL. Odrzucamy obcy origin/host, brak tokenu i start przez GET. Nie włączamy CORS; to nie projekt zdalnego panelu ani systemu kont. Szczegóły implementacji muszą obejmować żądania Dash, pobieranie i odświeżanie strony.
- Dane urządzeń renderujemy jako tekst; bez HTML z hostname/ifAlias lub importu. Błędy pokazują kod i bezpieczny opis; bez tracebacków, surowych komend i wartości ENV.

## 6. Mapa, filtry i szczegóły

Graf prezentuje istniejące typy i tożsamości. Nie zamieniamy collection_endpoint na potwierdzony switch bez dowodu. Nazwa/OUI/brama nie przesądzają roli. Legenda rozróżnia segment logiczny, LLDP, przypisanie oraz kandydata; typ relacji ma też etykietę/styl, nie tylko kolor.

Filtry są wyłącznie projekcją zapisanej topologii, bez ponownego wnioskowania:

- Tekst dopasowuje fragment IP/MAC/nazwy, bez znaczenia wielkości liter; normalizuje separatory MAC. Działa łącznie z VLAN.
- VLAN: „wszystkie”, dostępne identyfikatory oraz „nieustalony”. Przynależność wynika z zapisanych relacji/dowodów; adres podsieci nie nadaje VLAN-u. Węzeł wielo-VLAN pozostaje jeden, z listą powiązań.
- Pokaż pasujące węzły i niezbędny kontekst infrastruktury; krawędzie tylko między widocznymi końcami. Kontekst wyróżnij, aby użytkownik wiedział, czemu widzi dodatkowy switch. Przy filtrze VLAN nie pokazuj obcych przypisań hostów; LLDP może pozostać jako kontekst z VLAN-em nieustalonym.
- Pokazuj liczbę widocznych/wszystkich elementów i aktywne filtry. Brak wyników ma komunikat oraz „Wyczyść filtry”. Wybór grafu nie zmienia zapisanego snapshotu.
- Dla małego grafu można pokazać całość. Dla dużego start od infrastruktury, z rozwijaniem hostów; dokładny próg dobieramy po pomiarze D14. Nie uruchamiamy kosztownego układu przy każdym odczycie postępu.

Szczegóły węzła: IP/MAC/nazwy, rola wraz z podstawą, producent lub „nieustalony”, ostatnia obserwacja i świeżość. Przypisania pokazuj jako listę switch–port–VLAN–confidence–źródło, z alternatywami i powodami niepewności. Szczegóły krawędzi: typ, port lokalny/zdalny według dowodów, VLAN/kontekst, czasy i ostrzeżenia. Nie zastępuj braków zerem lub przypadkowym portem uplink.

OUI: bez aktywnego lookupu i bez dodawania niesprawdzonej bazy. Gdy zweryfikowanych danych producenta nie ma, etykieta „nieustalony”; to istniejące ograniczenie, nie blokada panelu.

## 7. Historia i eksporty

Historia używa istniejących zdarzeń, z limitem/paginacją, czasem i pochodzeniem synthetic/imported/online oraz powiązaniem ze snapshotem. Zdarzenia niezaobserwowania nie są etykietowane „odłączono”. Wybór starego snapshotu przypina mapę do jego daty; zakończenie bieżącego cyklu pokazuje dostępność nowszego wyniku bez cichej podmiany oglądanej historii.

| Eksport | Dokładny zakres |
|---|---|
| Topologia JSON | Pełny wybrany graf: identyfikatory projektu/snapshotu/reguł, węzły, relacje, źródła i ograniczenia; bez wpływu filtra widoku |
| Topologia CSV | Pełny wybrany graf: osobne pliki urządzeń i relacji; identyfikatory łączą rekordy, pola złożone jako JSON w komórce; każdy rekord zawiera snapshot/rules_version, typ i dostępne dowody |
| Snapshot źródłowy JSON/CSV | Osobna, wyraźnie nazwana opcja, zgodna z istniejącym formatem v1; JSON służy do replay, nie mylić z JSON topologii |
| PNG/SVG | Aktualnie widoczna, odfiltrowana mapa z etykietami; zachowuje bieżące położenia i kadr, nie obejmuje ukrytych hostów ani panelu szczegółów |

CSV topologii to nowa projekcja eksportowa, nie migracja SQLite ani zmiana źródłowego snapshotu. Pola z tekstem pochodzącym z sieci wymagają ochrony przed wykonaniem formuły w arkuszu; dokumentujemy sposób neutralizacji. JSON zachowuje oryginalne wartości, z dotychczasową kontrolą sekretów.

Mechanizm obrazów: istniejący generateImage; SVG wymaga lokalnie dołączonego zestawu rozszerzeń. [Oficjalny przykład Dash Cytoscape](https://dash.plotly.com/cytoscape/images). Dla danych dostępne jest [dcc.Download](https://dash.plotly.com/dash-core-components/download); użycie nie wymaga nowej biblioteki. Zgodność sprawdzamy również na wersjach z lokalnego venv. Nie korzystamy z CDN ani zewnętrznego serwera renderującego.

Pliki tworzone przez Python trafiają do prywatnego katalogu eksportów z kontrolowanymi nazwami, bez nadpisywania, przez ochronę 3.1. Nazwa zawiera snapshot i format; nie przyjmujemy dowolnej ścieżki z callbacku. Browser download tworzy dodatkową kopię według uprawnień przeglądarki/systemu — **nie gwarantuje trybu 0600 ani DACL mappera**. Panel rozróżnia „Zapisz prywatny eksport” od „Pobierz kopię”; PNG/SVG są pobierane przez przeglądarkę. Nie cofamy ochrony eksportów CLI ani nie zmieniamy ACL katalogu Downloads. Zaznaczamy, że mapa/eksport zawiera dane sieci.

## 8. Kolejność realizacji

| Krok | Zakres kodu i dokumentacji | Warunek zakończenia |
|---|---|---|
| 4.0 — decyzje | Zatwierdzenie tego planu i ADR-006; zapis w karcie | Jawny zakres implementacji, bez dopisywania wykonanych testów Windows |
| 4.1 — panel offline | app/ui, launcher CLI, projekty/demo/import, kopia grafu, podstawowe szczegóły, ochrona lokalnego serwera | Uruchomienie i przełączanie dwóch projektów bez kolektorów; zajęty port i offline poprawne |
| 4.2 — sterowanie kolekcją | Kontroler, edycja konfiguracji, preview/start/cancel, hook postępu, blokady, opt-in harmonogram | Atrapy potwierdzają jedną kolekcję, brak startu przy renderowaniu, anulowanie i bezpieczne zmiany zakresu |
| 4.3 — mapa i dane | Filtry, legenda, szczegóły dowodów, historia, JSON/CSV i obrazy | Wynik zgodny ze snapshotami; eksporty mają zadeklarowany zakres i działają lokalnie |
| 4.4 — odbiór i porządek | Krytyczne regresje, ręczny panel, większy syntetyczny snapshot, raport i instrukcja | Brak regresji; wyniki pomiarów i niewykonane próby jawne |

Kroki 4.1–4.4 stanowią jeden zatwierdzany etap; nie wymagają osobnej zgody na każdą rutynową zmianę. Nowa architektura, zależność lub rozszerzenie protokołu wymaga odrębnej decyzji. Aktywnego odbioru nie wykonujemy na podstawie zgody na kodowanie.

Docelowo dodamy `src/mapper/app.py`, `src/mapper/ui/` (kontroler, widok, projekcja grafu i eksporty) oraz lokalne assets. Nazwy i podział małych modułów mogą dostosować się do implementacji. Zmieniamy CLI, config i wąskie punkty raportowania postępu; nie przepisujemy silnika topologii ani kolektorów. Lokalne zasoby muszą wejść do package-data. `topology view` zostaje kompatybilne; prototypy przenosimy do old/ tylko po wykazaniu zastąpienia, z wpisem w docs/OLD.md.

Wstępny budżet zgodny z planem głównym: **3–4 dni pracy oraz do 1 dnia bufora** na integrację i przeglądarkę, do korekty po 4.1. To szacunek, nie obietnica; nie obejmuje oczekiwania na Windows/switche ani instalatora. Bez CI/CD, frameworka testów UI czy nowej biblioteki komponentów.

## 9. Krytyczne sprawdzenia i odbiór

Zachowujemy 38 istniejących testów. Dodajemy kilka grup regresji tam, gdzie UI może obejść zabezpieczenia; używamy unittest, atrap, tymczasowych prywatnych projektów i lokalnego klienta HTTP. Nie testujemy każdej etykiety/callbacku osobno.

1. Start/odświeżenie strony, import/demo, filtry, historia i eksport nie wywołują kolektorów; offline blokuje próbę startu także po ręcznie spreparowanym żądaniu.
2. Preview i start używają identycznej zwalidowanej konfiguracji; zmiana źródła/zakresu unieważnia preview, zbyt duży zakres nie jest obcinany; drugi start/karta/CLI nie omija locka.
3. Pracownik posiada SQLite; postęp nie otwiera zajętej bazy. Anulowanie nie uruchamia kolejnych celów, czeka na posprzątanie i zachowuje częściowy wynik. Błąd nie usuwa wcześniejszej mapy.
4. Dwa projekty o tych samych IP, przełączanie podczas kolekcji i spóźniony callback nie mieszają grafów ani eksportów. Każda operacja jest związana z UUID projektu/snapshotu i generacją zadania.
5. Hook/liczniki i harmonogram na sztucznym zegarze: brak nakładania, brak restartu serii po uruchomieniu, zmiana sieci rozbraja, wyłączenie przyszłych startów oddzielone od anulowania.
6. Test źródła danych w filtrach i eksportach: unknown VLAN, wielo-VLAN i kandydat uplink nie zmieniają dowodów; JSON/CSV pełne, obraz tylko widok. Sekrety nie występują w odpowiedzi/plikach; tekst HTML i formuły CSV są neutralizowane we właściwym formacie.
7. Brak tokenu/obcy Host/Origin nie uruchamia kolekcji ani zapisu. Prywatny eksport, atomowy config i import zachowują ochronę oraz limity; upload nie nadpisuje plików.

### Ręczny odbiór na macOS, bez nowych sond

- Uruchom demo i syntetyczny managed snapshot z examples; sprawdź mapę logiczną oraz przypisanie/LLDP/kandydaturę. Sama obecność węzłów nie potwierdza działania protokołu.
- Sprawdź wyszukiwanie, VLAN/unknown, szczegóły węzła i linku, historię oraz przełączanie dwóch projektów. Zachowaj pozycje po odświeżeniu postępu; stary snapshot nie zmienia się sam.
- Pobierz/otwórz PNG i SVG; sprawdź etykiety i kadr. Porównaj JSON/oba CSV z pełnym wybranym snapshotem mimo aktywnego filtra. Sprawdź prywatne pliki osobno od pobrań przeglądarki.
- Uruchom na 8051, sprawdź właściwy URL; druga instancja na zajętym porcie ma zakończyć się błędem bez otwarcia cudzej strony i bez zabijania procesu. Ctrl+C zamyka własne zasoby.
- W trybie offline i z odłączonym Internetem odśwież z wyłączonym cache. Wymagane zasoby mają być lokalne; obserwuj brak wywołań kolektorów. Odbiór kontrolera online odbywa się na atrapach, bez wysyłania sond do LAN.
- Zmierz większy syntetyczny zestaw D14: 50 switchy, 1000 hostów, 20 VLAN-ów, 50 tys. obserwacji; import/korelacja ≤30 s, pierwszy widok infrastruktury ≤5 s i RAM aplikacja+karta ≤1,5 GB na stanowisku min. 6 GB. Zanotuj wersję OS/przeglądarki, rzeczywiste czasy i sposób pomiaru. Niespełnienie celu wymaga korekty lub jawnego ograniczenia odbioru; brak pomiaru nie jest zaliczeniem.

Odbiór aktywnego LAN, SNMPv2c/v3/SSH i Windows/NTFS wymaga dostępnego środowiska oraz osobnego jawnego zakresu operatora. Niewykonane próby zachowują ten status w raporcie; nie blokują wykonania panelu offline, lecz blokują odpowiednie deklaracje pełnego wsparcia.

## 10. Definition of Done i przekazanie

Etap gotowy technicznie, gdy działa pełny przepływ w panelu, dane/niepewność odpowiadają silnikowi, nie ma sond przy starcie, pojedyncza kolekcja i ochrona danych pozostają skuteczne, filtry/eksporty mają określony zakres, a offline korzysta wyłącznie z lokalnych zasobów. Dotknięte regresje przechodzą; pomiary D14 i niewykonane odbiory mają jawny wynik.

Po wdrożeniu: `docs/etap-4/RAPORT_ETAP_4.md`, zbiorcze dowody bez prywatnych adresacji, syntetyczny obraz panelu oraz poradnik faktycznego uruchomienia i odbioru. Aktualizacja README/indeksu/planu i wersji aplikacji dopiero wraz z kodem. Jeśli element zastąpiono, przenieść go do old/ z rejestrem. Commit/push wyłącznie na polecenie użytkownika.

**Zatwierdzono do implementacji:** zakres 4.0–4.4 i ADR-006, w tym kontroler w tle, opt-in seria D12, profile wyłącznie ENV, jawny zakres seedów w UI, format CSV topologii, rozróżnienie prywatnego eksportu/pobrania oraz mała ochrona lokalnych operacji. Rozpoczęcie Etapu 5 następuje po przedstawieniu i zatwierdzeniu wyniku Etapu 4.
