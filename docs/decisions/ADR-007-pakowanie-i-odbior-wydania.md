# ADR-007 — pakowanie i odbiór pierwszego wydania

Data: 2026-10-25. Status: **propozycja do zatwierdzenia z planem Etapu 5**. Użytkownik zaakceptował wynik Etapu 4 i zlecił następny plan; nie zatwierdził jeszcze implementacji tego ADR. Podstawa: D01–D03/D09–D14, [ADR-004](ADR-004-licencja-i-dystrybucja.md), [plan Etapu 5](../poradniki/ETAP_5_ODBIOR_I_PAKOWANIE_MVP.md).

## Problem

Wheel własnego kodu i developerskie venv nie stanowią jeszcze odebranego wydania dla Windows/macOS. Brakuje czystej instalacji, prób sprzętowych, pełnego pomiaru zasobów i zamknięcia materiałów faktycznie przekazywanych bibliotek. MVP ma pozostać jedną aplikacją bez rozbudowanego CI/CD i nowych protokołów.

## Proponowane decyzje

1. Pierwszy pakiet to dwa archiwa platformowe jednego produktu: macOS ARM i Windows x64. Własny wheel, dokładne koła zależności, lock z hashami, skrypty instalacji/startu, instrukcje i odpowiednie materiały komponentów. Python 3.13 jest wymaganiem przygotowanego stanowiska. Venv tworzy się na miejscu; nie przenosimy developerskiego środowiska i nie dołączamy teraz interpretera ani narzędzia EXE/DMG.
2. Instalacja wyłącznie z lokalnego wheelhouse, --no-index/--only-binary/--require-hashes. Brak pliku lub niezgodność hash kończy instalację. Start nie pobiera bibliotek. Zmiana wersji zależności tylko z przyczyn zgodności i z zapisaną weryfikacją; macOS lock nie jest lockiem Windows.
3. Dane projektów pozostają poza archiwum i venv. Instalator nie zmienia konfiguracji sieci, polityk systemu ani istniejących danych. Aktualizację odbieramy obok poprzedniego środowiska na spójnej prywatnej kopii bazy; rollback nie nadpisuje bieżącego stanu starszym programem.
4. Własna MIT i noty autorów pozostają bez zmian. Zawartość wheelhouse/źródeł/not weryfikujemy dla konkretnej paczki zgodnie z istniejącym rejestrem luk; nie deklarujemy zgodności całego wydania na podstawie licencji głównego pakietu. Artefakt nie jest gotowy do przekazania przy nierozstrzygniętych wymaganiach jego komponentów.
5. Macierz D01 i wymagane SNMPv2c/v3/SSH pozostają zakresem pełnego MVP. Prób na Windows/NTFS, sprzęcie i RAM nie zastępują atrapy ani sam wheel. Brak środowiska pozwala kontynuować pakowanie/offline, lecz nie zmniejsza automatycznie zakresu wydania. Ograniczona publikacja wymaga odrębnej decyzji użytkownika.
6. Bez nowych producentów SSH, własnego stosu SNMP, Linuksa, OUI API, CI/CD i automatycznej aktualizacji. Zamykamy istniejące funkcje i krytyczne braki. Duże artefakty i prywatne dowody pozostają poza repozytorium; pliki wycofane trafiają najpierw do old/ z rejestrem.
7. Powstają manifest, sumy, macierz rzeczywistego wsparcia i raport z wersjami/komendami/dowodami. Nie wykonujemy Git tag/push/publikacji ani aktywnego skanu na podstawie zgody na pakowanie. Odczyty online wymagają odrębnego zakresu i jawnej akcji operatora.

## Skutki i granice

Mały zakres skryptów i standardowe mechanizmy Python/pip służą szybkiemu wydaniu; nie dodają usług. Odbiorca musi wcześniej mieć zgodnego Pythona, co trzeba ujawnić w START_TUTAJ. Koła i testy natywne są platformowe, mimo wspólnego kodu aplikacji. Zmiana na instalator z interpreterem wymaga ponownej decyzji o pakowaniu, dystrybucji i odbiorze.

Przed wdrożeniem wymagane jest zatwierdzenie tego ADR i planu. Zatwierdzenie Etapu 4 nie oznacza wykonania przyszłych prób ani odbioru całego MVP.
