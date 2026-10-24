# ADR-004 — MIT dla własnego kodu i odrębne warunki komponentów

Data: 2026-10-24.

Status: **MIT oraz podpis osoby fizycznej z marką FL Development zatwierdzone przez użytkownika; zastosowanie do własnych elementów projektu**.

## Podstawa i zakres

Zadanie pochodzi z rozmowy o `third_party_licenses/`, bez osobnego Issue. Użytkownik wybrał „Open source — MIT, także z prawem dalszej sprzedaży”, następnie potwierdził, że FL Development jest jego jednoosobową działalnością gospodarczą. Zaakceptował rekomendację podpisu łączącego imię i nazwisko z marką słowami „bardzo dobrze wykonaj, dopisz podpis do licencji”.

Przyjęty podpis: `Copyright (c) 2026 Pawel Juroszek (FL Development)`. Pisownię imienia i nazwiska pobrano z konfiguracji autora repozytorium (`git config --get user.name`: `Pawel Juroszek`), a formę działalności i markę z oświadczenia użytkownika. Nie ustalano danych na podstawie samej nazwy konta systemowego. Nie sprawdzano pełnej firmy w CEIDG ani nie dopisywano numerów identyfikacyjnych. FL Development identyfikuje markę tej samej osoby fizycznej, a nie drugiego współuprawnionego.

Źródłowe ustalenia: [karta Etapu 0](../poradniki/KARTA_ETAP_0.md), [wymagania](../WYMAGANIA_PROJEKTU.md), [plan §2](../PLAN_STARTOWY.md), [noty komponentów](../THIRD_PARTY_NOTICES.md). Wymaganie darmowych komponentów nie rozstrzygało dotąd licencji własnego kodu.

## Decyzja

1. Docelową licencją własnych elementów projektu, do których publikujący ma odpowiednie prawa, jest standardowa MIT. Nie dopisujemy do niej zakazu sprzedaży, konkurencji, modyfikacji ani dodatkowych ograniczeń zastosowania.
2. Dodajemy standardowy tekst MIT z zaakceptowanym sposobem podpisu w głównym [LICENSE](../../LICENSE). Wcześniejszy szablon zachowujemy bez zmian w `old/2026-10-24/docs/licencje/LICENSE.MIT.template.txt`, a przeniesienie odnotowujemy w [rejestrze](../OLD.md).
3. Metadane własnego pakietu odsyłają do pliku `LICENSE` i wskazują autora jako `Pawel Juroszek (FL Development)`. README eksponuje ten sam podpis. Zastosowanie MIT do własnych elementów nie stanowi potwierdzenia pełnego audytu praw do kodu ani gotowości instalatora do dystrybucji.
4. Licencje bibliotek, ich kodu dołączonego wewnętrznie, zasobów JS, ikon, fontów i danych pozostają odrębne. MIT własnego kodu nie zastępuje LGPL, MPL ani innych warunków.
5. Powstaje [objaśnienie bieżącego stanu](../licencje/STAN_PRAWNY_I_DYSTRYBUCJA.md), rozróżniające ustalenia, braki oraz warunki przyszłego wydania. Jest informacyjne i nie ustanawia dodatkowych warunków MIT.

## Skutki i granice

Po prawidłowym zastosowaniu MIT odbiorcy będą mogli używać własnego kodu projektu także komercyjnie, modyfikować go, rozpowszechniać i sprzedawać, zachowując wymagane noty. MIT nie wymaga udostępniania ich zmian. Zmiana modelu kolejnych wydań nie odbiera automatycznie praw do kopii już udostępnionych na MIT.

Nie zatwierdzamy instalatora ani redystrybucji całego środowiska. Przed takim wydaniem trzeba uzupełnić noty, sprawdzić źródła i wymienialność bibliotek LGPL, obowiązki MPL oraz rzeczywistą zawartość artefaktu. Nie zmieniamy zależności, funkcji, architektury, ograniczeń bezpieczeństwa ani stanu odbioru Etapu 3.

Teksty upstream w `third_party_licenses/` pozostają niezmienione. Ta decyzja nie jest formalną opinią radcy prawnego ani dowodem pełnego audytu praw do kodu.
