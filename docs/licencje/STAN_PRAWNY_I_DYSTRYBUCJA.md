# Licencjonowanie mappera 0.3.0 i warunki dystrybucji

Stan przeglądu: **24 października 2026 r.** Zakres: lokalny wariant Python, inwentarz 50 dystrybucji oraz wskazane teksty i noty z przygotowanego środowiska macOS ARM. Nie jest to audyt kompletnego instalatora, wszystkich plików zależności ani łańcucha praw autorskich. Dokument jest objaśnieniem, a nie formalną opinią radcy prawnego ani dodatkową licencją.

## 1. Wybrany model i stan jego zastosowania

Użytkownik wybrał **MIT dla własnego kodu**, również z prawem dalszej sprzedaży przez odbiorców, oraz zaakceptował podpis osoby fizycznej z marką swojej JDG. Decyzję zapisano w [ADR-004](../decisions/ADR-004-licencja-i-dystrybucja.md). Standardowy tekst znajduje się w głównym [LICENSE](../../LICENSE).

**Podpis uprawnionego: `Copyright (c) 2026 Pawel Juroszek (FL Development)`.** Użytkownik potwierdził, że FL Development jest jego jednoosobową działalnością gospodarczą. Oznaczenie wskazuje osobę fizyczną wraz z marką, a nie dwa odrębne podmioty. Pisownię `Pawel Juroszek` przyjęto zgodnie z konfiguracją autora repozytorium (`git config --get user.name`), bez wywodzenia jej z nazwy konta systemowego. Pełnej firmy w CEIDG nie weryfikowano; przed jej użyciem w odrębnych umowach należy ustalić dokładne brzmienie. Nie dodano NIP, adresu ani innych niepotwierdzonych danych.

MIT została zastosowana do własnych elementów projektu przez dodanie `LICENSE`; `pyproject.toml` odsyła do tego tekstu i podaje autora `Pawel Juroszek (FL Development)`. Wcześniejszy szablon zachowano bez zmian w `old/2026-10-24/docs/licencje/LICENSE.MIT.template.txt`, zgodnie z [rejestrem przeniesień](../OLD.md). Uzupełnienie podpisu nie stanowi pełnego audytu praw ani potwierdzenia zgodności przyszłego instalatora.

Licencja własnego kodu obejmuje wyłącznie elementy, do których publikujący może jej udzielić. Biblioteki, ich dołączony kod, ikony, fonty i dane pomocnicze zachowują własne warunki. Materiały archiwalnego wariantu Flutter/Dart nie były objęte tym przeglądem. Nie należy obejmować cudzych plików deklaracją wyłącznego autorstwa. Przegląd nie rozstrzyga autorstwa każdego fragmentu, w tym zakresu ochrony materiałów powstałych z udziałem AI ani praw wynikających z ewentualnych umów z klientem lub pracodawcą.

## 2. Co MIT oznacza dla odbiorcy i właściciela projektu

Tabela dotyczy **własnych elementów objętych MIT**, a nie automatycznego przelicencjonowania bibliotek.

| Działanie | Skutek MIT |
|---|---|
| Używanie prywatne, firmowe i w odpłatnych usługach | Dozwolone, bez opłat licencyjnych na rzecz autora wynikających z MIT |
| Kopiowanie, zmiany, łączenie i rozpowszechnianie | Dozwolone z zachowaniem wymaganych informacji |
| Sprzedaż oryginalnych lub zmienionych kopii | Dozwolona, także przez podmioty konkurujące z twórcą |
| Zatrzymanie własnych zmian bez publikacji źródeł | MIT nie nakazuje ich publikacji; warunki innych komponentów sprawdza się osobno |
| Usunięcie noty autorstwa i tekstu zgody z kopii lub istotnych części | Niedozwolone w zakresie wymaganym przez MIT |
| Twierdzenie, że autor gwarantuje przydatność lub rekomenduje produkt odbiorcy | MIT nie stanowi takiej gwarancji ani rekomendacji |

Można sprzedawać własne wydanie, wdrożenia i wsparcie. Odbiorcy nie muszą jednak kupować kopii wyłącznie od pierwotnego autora. MIT nie zapewnia wyłączności sprzedaży, nie nakłada obowiązku oddawania części przychodów i nie zabrania konkurencji. Nie dodajemy do standardowego tekstu zakazu działalności komercyjnej ani dalszej sprzedaży. [Źródło: standardowa MIT](https://opensource.org/license/mit).

Udostępnienie własnego kodu na MIT nie usuwa warunków LGPL/MPL z gotowej aplikacji. MIT nie jest certyfikatem bezpieczeństwa, jakości ani kompletności wykrywania sieci.

## 3. Warunki komponentów zewnętrznych

Obowiązują teksty odpowiednie dla rzeczywiście użytych wersji i plików; tabela jest ich objaśnieniem. Inwentarz oraz zachowane teksty: [THIRD_PARTY_NOTICES](../THIRD_PARTY_NOTICES.md), [inventory.json](../../third_party_licenses/inventory.json).

| Rodzaj | Przykłady w środowisku | Znaczenie przy przekazywaniu kopii |
|---|---|---|
| MIT, BSD, ISC i pokrewne licencje liberalne | Netmiko, NetworkX, psutil, Dash; libsodium w PyNaCl | Zachować właściwe noty, warunki i zastrzeżenia; niektóre licencje zabraniają sugerowania poparcia autorów. MIT-0 nie zawiera typowego warunku zachowania noty, ale nie znosi warunków odrębnych części pakietu. |
| Apache 2.0 | ntc-templates, TextFSM, requests, bcrypt | Dołączyć licencję, zachować wymagane noty, oznaczyć zmienione pliki i uwzględnić odpowiednie informacje NOTICE. Uprawnienia patentowe mają warunki; licencja nie udziela ogólnego prawa do marek. |
| LGPL 2.1 / 2.1-or-later | Paramiko, scp | Zachować licencję i informacje o użyciu; spełnić wymagania źródeł oraz właściwe dla sposobu połączenia wymagania modyfikacji i wymiany biblioteki. |
| LGPL 3 | autocommand dołączony wewnątrz setuptools | Ocenić, czy i w jakiej formie element trafia do wydania; samo użycie narzędzia do zbudowania aplikacji nie nadaje wynikowi LGPL. |
| MPL 2.0 | wskazany zestaw certyfikatów certifi; części setuptools | Obowiązki dotyczą objętych plików, ich zmian i odpowiedniej postaci źródłowej, a nie automatycznie całego własnego kodu. |
| PSF i historyczne warunki Pythona | typing-extensions; dodatkowy tekst w Netmiko | Zachować odpowiednie warunki i informacje; zbiorczy opis „MIT/BSD/Apache” jest niewystarczający. |
| CC BY 4.0 / SIL OFL 1.1 / MIT | zasoby Font Awesome wskazane w notach Dash | Sprawdzić rzeczywiście dołączone ikony, fonty i kod oraz zachować wymagane uznanie autorstwa i warunki. |

W przeanalizowanych warunkach nie stwierdzono opłat za liczbę skanowanych hostów ani obowiązku zakupu edycji komercyjnej tych komponentów. Nie jest to zapewnienie o przyszłych wersjach, dodatkach lub usługach. Pakiety deklarujące alternatywne licencje, np. `Apache-2.0 OR BSD-3-Clause`, wymagają ustalenia i udokumentowania wybranej ścieżki dla odpowiedniego kodu; warunki dodatkowych części sprawdza się osobno.

### LGPL i sposób instalacji

Uruchomienie programu jest odrębne od przekazywania jego kopii. Przy dystrybucji biblioteki w postaci wykonywalnej LGPL 2.1 §4 wymaga odpowiednich źródeł; §6 opisuje warunki dystrybucji połączonego programu. Mechanizm współdzielony z §6(b) ma pozwalać działać z wymienioną, zgodną wersją biblioteki. Nie wystarcza nazwanie importu „dynamicznym”. Trzeba sprawdzić rzeczywistą paczkę i nie ograniczać praw wymaganych przez licencję. [LGPL 2.1, tekst publikowany przez Paramiko](https://raw.githubusercontent.com/paramiko/paramiko/main/LICENSE).

Praktyczna ścieżka do sprawdzenia przy pakowaniu: oddzielne moduły bibliotek, zachowane informacje oraz dołączone źródła dokładnych wersji w zakresie wymaganym przez odpowiednią licencję. Źródła dostarcza się zgodnie z wybraną ścieżką licencji; nie zawsze oznacza to publiczne repozytorium całej aplikacji. Ogólny link do strony głównej upstream nie dowodzi spełnienia wymagań źródeł.

Własna MIT nie nakłada zakazu modyfikacji ani inżynierii wstecznej. Nie należy dodawać do instalatora sprzecznej umowy zabraniającej uprawnień wymaganych przez LGPL. Przy LGPL 3 trzeba uwzględnić także dołączenie odpowiedniego tekstu GPL 3 i ewentualne informacje instalacyjne, jeśli wymagają ich warunki konkretnej dystrybucji. [Zachowany tekst LGPL 3, §4](../../third_party_licenses/setuptools/2-LICENSE).

### MPL i zasoby interfejsu

MPL pozwala łączyć objęte nią pliki z własnym kodem na innej licencji. Przy przekazywaniu postaci wykonywalnej trzeba poinformować, jak uzyskać odpowiednie źródła; przy przekazywaniu źródeł zachować ich warunki i informacje. Dostarczanie pliku w postaci źródłowej ma inne znaczenie niż wyłącznie skompilowanej. Lokalna nota certifi wskazuje zestaw certyfikatów; nie rozciągamy jej bez zbadania plików na każde własne dane mappera. [MPL 2.0, §3](https://www.mozilla.org/en-US/MPL/2.0/).

Noty Dash wskazują Font Awesome Free 5.15.4. Ikony SVG/JS podlegają CC BY 4.0, fonty SIL OFL 1.1, a kod MIT. Trzeba zachować właściwą atrybucję i oznaczenia zmian. OFL dopuszcza sprzedaż aplikacji z fontem, lecz ogranicza sprzedaż samego fontu i użycie zastrzeżonych nazw jego zmodyfikowanych wersji. Nie wymaga otwarcia własnego kodu aplikacji. [Font Awesome 5.15.4](https://raw.githubusercontent.com/FortAwesome/Font-Awesome/5.15.4/LICENSE.txt), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), [SIL OFL 1.1](https://openfontlicense.org/open-font-license-official-text/).

## 4. Potwierdzone luki przed wydaniem dla odbiorców

1. **Podpis i zakres praw:** podpis oraz główny `LICENSE` zostały uzupełnione. Pełny audyt praw do poszczególnych elementów oraz identyfikacja przyszłych współautorów nie były przedmiotem tej zmiany.
2. **Setuptools:** nagłówek MIT nie opisuje całej zawartości. `third_party_licenses/setuptools/2-LICENSE` odpowiada bajtowo tekstowi w `setuptools/_vendor/autocommand-2.2.2.dist-info/LICENSE` z LGPL 3. W środowisku Dash 4.4.1 deklaruje `Requires-Dist: setuptools`.
3. **Dodatkowe noty setuptools:** pliki `setuptools/config/NOTICE` oraz `setuptools/config/_validate_pyproject/NOTICE` opisują m.in. części MPL/BSD i nie zostały odwzorowane w obecnym katalogu not. Ich obecność w zainstalowanej paczce nie dowodzi jeszcze obecności w przyszłym instalatorze.
4. **pySerial:** zachowano [referencję](../../third_party_licenses/pyserial/LICENSE_REFERENCE.txt), lecz przed redystrybucją należy dołączyć wymagany pełny tekst wraz z notą autora. [Upstream pySerial 3.5](https://raw.githubusercontent.com/pyserial/pyserial/v3.5/LICENSE.txt).
5. **Skrócone noty:** plik scp zawiera odwołanie do LGPL, a plik certifi notę MPL, nie pełne teksty. LGPL 2.1 jest zachowana przy Paramiko, ale dopiero paczka wydania pokaże, czy odbiorca faktycznie otrzymuje wymagane materiały. Warto dołączyć także pełną MPL dla kompletności dokumentacji; sam jej brak nie przesądza o naruszeniu, skoro tekst MPL przewiduje informację, jak ją uzyskać.
6. **Zasoby JS:** zachowane komentarze licencyjne nie są pełnym inwentarzem bibliotek wewnątrz paczek. Nota `dash/2-async-export.js.LICENSE.txt` identyfikuje SheetJS, lecz nie ustala wersji i pełnych warunków dołączonego kodu. Trzeba je ustalić dla rzeczywistego zasobu przed jego wydaniem.
7. **Brak odbioru artefaktu:** nie sprawdzono dołączonego interpretera, bibliotek natywnych, narzędzia pakowania, wszystkich zasobów przeglądarkowych ani nowych danych OUI/MIB. Licencja głównego pakietu nie zastępuje analizy jego zawartości.

Nie stwierdzamy na tej podstawie, że dotychczasowe lokalne korzystanie narusza licencje. Stwierdzamy, że obecne materiały nie wystarczają do potwierdzenia kompletności przyszłego wydania.

## 5. Proces wydania

1. Zachować aktualny podpis, główny `LICENSE`, rozgraniczenie komponentów i deklarację w metadanych pakietu. Przy dodawaniu cudzego wkładu ustalić jego pochodzenie i odpowiednie prawa; własny podpis nie zastępuje not innych uprawnionych.
2. Ustalić konkretny format wydania: własne źródła z niezależnie instalowanymi zależnościami, wheel, instalator lub spakowane środowisko. Sprawdzić, jakie kopie faktycznie przekazuje dystrybutor; samo polecenie instalacji nie rozstrzyga obowiązków całego procesu.
3. Uzupełnić braki z §4 i przygotować inwentarz plików oraz wersji rzeczywistego artefaktu. Dołączyć właściwe licencje, noty i wymagane źródła. Sprawdzić dostępność wymaganych informacji również offline w lokalnym wydaniu.
4. Jeśli przyjęto ścieżkę wymienialnych bibliotek LGPL, sprawdzić technicznie wymianę biblioteki na zgodną, zmienioną wersję w wydawanej paczce. Nie uznawać kodu źródłowego repozytorium za dowód właściwości instalatora.
5. Zapisać wynik przeglądu konkretnego wydania, nierozstrzygnięte kwestie i miejsce udostępnienia źródeł. Zachować dostarczone materiały odpowiadające wersji wydania.

Te kroki nie zostały wykonane przez samo sporządzenie dokumentu. Zmiana zależności lub formatu wydania wymaga ponownego sprawdzenia odpowiednich warunków.

## 6. Odpowiedzialność i korzystanie z sieci

MIT zawiera standardowe zastrzeżenie braku gwarancji i odpowiedzialności. Nie należy obiecywać odbiorcom, że usuwa ono każdą odpowiedzialność wynikającą z prawa lub osobnej umowy. Płatne wdrożenie i wsparcie mogą wymagać odrębnych warunków; nie można automatycznie przenieść własnych zobowiązań na autorów bibliotek.

W polskim prawie trzeba uwzględnić zasady licencjonowania i uprawnienia dotyczące programów komputerowych, a przy ograniczeniach odpowiedzialności m.in. zakaz wyłączenia odpowiedzialności za szkodę wyrządzoną umyślnie. Dokument nie analizuje pełnego prawa konsumenckiego, wszystkich późniejszych nowelizacji ani każdej jurysdykcji dystrybucji. [Prawo autorskie, m.in. art. 67 oraz 74–76, tekst jednolity Dz.U. 2025 poz. 24](https://api.sejm.gov.pl/eli/acts/DU/2025/24/text.pdf), [Kodeks cywilny, art. 473 §2, tekst jednolity Dz.U. 2026 poz. 795](https://api.sejm.gov.pl/eli/acts/DU/2026/795/text.pdf).

Uprawnienie do korzystania z kodu nie jest uprawnieniem do dostępu do cudzych systemów. Operator potrzebuje odpowiedniego upoważnienia do badanej sieci; dane wynikowe mogą wymagać ochrony. Techniczne zasady projektu — jawny zakres, uruchomienie przez operatora, ograniczenie ruchu, tylko odczyt i ochrona sekretów — pozostają aktualne. Są zasadami działania produktu i nie stanowią dopisanych ograniczeń do tekstu MIT.

## 7. Wykonane sprawdzenia i ograniczenia

Przegląd objął inwentarz, teksty not, konfigurację pakietu oraz wskazane metadane i noty z lokalnego venv. Zweryfikowano zgodność tekstu LGPL 3 z kopią autocommand oraz zależność Dash od setuptools. Nie uruchamiano aktywnego odkrywania sieci, nie przebudowywano bibliotek ani instalatora i nie przeprowadzono testów zgodności gotowego wydania. Oryginalne teksty upstream pozostają niezmienione.

Walidacja wcześniejszego projektu (przed podpisaniem MIT): `git diff --check` i `git diff --cached --check` zakończyły się bez błędów. Jednorazowy skrypt uruchomiony poleceniem `python3 -` sprawdził 142 lokalne odnośniki w sześciu plikach, kodowanie UTF-8 i białe znaki, zgodność części normatywnej projektu MIT z zachowanym tekstem MIT z Dash po pominięciu formatowania oraz obecność pola uprawnionego. Potwierdził brak nowego głównego `LICENSE` i brak zmian względem indeksu Git w `src/`, `pyproject.toml` oraz `third_party_licenses/`. Jest to kontrola dokumentów, a nie test aplikacji lub zgodności dystrybucji; testów funkcjonalnych nie uruchamiano, ponieważ zmiana dotyczy wyłącznie dokumentacji.


Walidacja po dodaniu podpisu, 24 października 2026 r.:

- `git diff --check` i `git diff --cached --check`: bez błędów.
- Jednorazowy skrypt `python3 -`: 148 lokalnych odnośników w ośmiu plikach, poprawne kodowanie i białe znaki, standardowy tekst MIT, zgodność podpisu z metadanymi TOML, zachowanie wcześniejszego szablonu bez zmiany treści oraz brak zmian kodu aplikacji i oryginalnych licencji zależności względem indeksu Git.
- `./.venv/bin/python -m pip wheel --no-index --no-deps --no-build-isolation <kopia-projektu> --wheel-dir <katalog-tymczasowy>`: wynik poprawny. Polecenie wykonano z bezwzględną ścieżką do interpretera, w tymczasowej kopii zawierającej `src/`, `pyproject.toml` i `LICENSE`. W wygenerowanym wheel potwierdzono autora, treść licencji w metadanych i dołączony plik `LICENSE` z podpisem. Nie pobierano ani nie instalowano zależności; kopię i wynik usunięto wraz z katalogiem tymczasowym.
- Nie uruchamiano testów funkcjonalnych ani skanów sieci: zmiana obejmuje podpis, dokumentację i metadane pakietu. Budowa własnego wheel nie stanowi odbioru instalatora z bibliotekami zewnętrznymi.
