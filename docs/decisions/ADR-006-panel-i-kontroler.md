# ADR-006 — lokalny panel i kontroler zadań

Data: 2026-10-25. Status: **przyjęte do implementacji 25 października 2026 r.** Użytkownik zatwierdził plan poleceniem „masz zgode na dzialanie. Wdrazaj”. Zgoda obejmuje kod i odbiór offline, bez nowych aktywnych sond. Podstawa: D02/D06/D09/D11/D12/D14, [ADR-005](ADR-005-bezpieczne-sondy-i-blokady.md), [plan Etapu 4](../poradniki/ETAP_4_PANEL_I_PRZEPLYW_OPERATORA.md).

## Problem

Podgląd 0.3.1 otrzymuje gotowy graf. Panel operatora musi sterować długą kolekcją bez blokowania callbacków, współdzielenia SQLite między wątkami i obejścia zakresu/locków. Obsługa eksportu przez przeglądarkę wymaga oddzielenia jej kopii od ochrony pliku utworzonego przez aplikację.

## Decyzje

1. Pozostaje jeden lokalny proces Python i Dash, bez nowego backendu, kolejki usług ani zależności. Jeden jawnie utworzony kontroler per instancja, jeden pracownik do zadania kolekcja/build oraz jeden ograniczony pracownik operacji offline, aby wczytanie innego projektu nie czekało na skan. Każda pula dopuszcza jedno zadanie bez kolejki. Pracownik tworzy i zamyka własne Repository w tym samym wątku. Callbacki przekazują komendy, odczytują mały obraz postępu i nie otrzymują uchwytu SQLite.
2. Globalny cycle lock i project lock pozostają zgodne z 3.1. W UI jeden aktywny skan, bez kolejki. Ostatni graf/historia w pamięci mają identyfikator projektu/snapshotu; spóźniona odpowiedź nie może podmienić innego projektu. Po publikacji źródeł build może zakończyć się błędem bez utraty danych wejściowych. CLI i podgląd Etapu 3 pozostają kompatybilne.
3. Wąski hook agregowanego postępu w istniejącym kontrolerze/kolektorze nie zmienia źródłowego formatu v1 ani SQLite v2. Sygnały anulowania trafiają do pętli asyncio bezpiecznie dla wątków. Zamykanie procesu czeka na ograniczone timeoutami sprzątanie; zamknięcie karty nie kończy procesu.
4. Start wymaga aktualnego podglądu i jawnej akcji operatora; walidacja po stronie serwera. Zmiany konfiguracji unieważniają podgląd. Profil zawiera wyłącznie referencje ENV, bez wartości sekretów w HTTP/DOM. UI wymaga jawnych dozwolonych zakresów także dla seedów. Brak zmian konfiguracji sieci i brak nowych platform SSH.
5. Odświeżanie D12 domyślnie wyłączone; uzbrajane jawnie dla tego samego planu, domyślnie 15 min po zakończeniu zadania. Bez nadrabiania terminów i wznowienia po restarcie. Zmiana projektu/źródła/konfiguracji, błąd lub anulowanie rozbrajają serię. Każdy start ponownie weryfikuje zgodność sieci. Offline blokuje wszystkie kolektory po stronie kontrolera.
6. Edycja konfiguracji pod project lockiem: walidacja, prywatny plik tymczasowy i atomowa podmiana, zachowana ochrona POSIX/DACL. Brak zmian schematu danych. Lokalny serwer weryfikuje Host/Origin oraz losowy token sesji dla operacji zmieniających stan; bez CORS, tokenu w URL i zdalnego panelu. Nazwy urządzeń są tekstem, nie HTML.
7. JSON topologii i dwa CSV (węzły/relacje) obejmują pełny wybrany graf; źródłowy snapshot v1 pozostaje osobnym eksportem. CSV topologii jest nową projekcją z identyfikatorami i polami dowodów, bez migracji bazy. PNG/SVG obejmują widoczny kadr po filtrach. Tekst sieciowy zabezpieczamy przed wykonaniem formuł CSV, bez zmiany oryginałów w JSON.
8. Eksport serwerowy tworzymy przez istniejącą ochronę prywatnych plików w kontrolowanym katalogu. Browser download jest dodatkową kopią o uprawnieniach przeglądarki/systemu; nie deklarujemy dla niej DACL/0600 mappera. Nie modyfikujemy ACL Downloads. Import ma obecne limity, prywatny plik tymczasowy i zawsze nowy projekt; żadnego importu sekretów/archiwów ani uruchamiania kolektorów.

## Skutki i granice

Brak migracji SQLite, zmiany tożsamości/reguł topologii lub nowych bibliotek. Ograniczona praca kontrolera i lokalne zasoby pomagają zachować małe zużycie zasobów; rzeczywistą wydajność trzeba zmierzyć. Wątek pracownika i harmonogram wymagają kilku testów krytycznych, nie rozbudowanego CI/CD. Windows/NTFS, prawdziwy SNMP/SSH i finalna dystrybucja pozostają osobnymi odbiorami.

Zatwierdzenie obejmuje opisany kontrakt i zakres Etapu 4. Nie stanowi zgody na aktywne skany wykonywane przez agenta podczas implementacji. Szczegóły modułów i zwykłe poprawki UI mogą być dopracowane w ramach tego zakresu.
