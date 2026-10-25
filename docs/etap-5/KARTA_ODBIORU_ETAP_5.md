# Karta odbioru Etapu 5

Utworzono: 25 października 2026 r. Status: **szablon, próby niewykonane**. Podstawa: [plan](../poradniki/ETAP_5_ODBIOR_I_PAKOWANIE_MVP.md). Zaakceptowany punkt wejścia: 0.4.0 i wynik Etapu 4; to nie jest wynik prób tej karty.

Nie wpisuj sekretów, rzeczywistych adresów/hostnames klienta ani prywatnych screenshotów do repozytorium. Publiczna karta wskazuje identyfikatory dowodów i bezpieczne podsumowanie; surowe receipt pozostają w prywatnym katalogu.

## Kandydat

| Pole | Wartość do uzupełnienia |
|---|---|
| Wersja / commit / stan drzewa | Nie ustalono kandydata wydania |
| Archiwum i SHA-256 | Nie utworzono artefaktu Etapu 5 |
| System / architektura / Python / przeglądarka | Wypełnij dla każdego stanowiska |
| Data i wykonujący | Wypełnij przy rzeczywistej próbie |
| Laboratorium i zakres | Prywatny identyfikator zgody/konfiguracji, bez IP i ENV w repozytorium |
| Licencje / manifest | Identyfikator raportu konkretnej paczki |

## Rejestr wyników

Statusy: **NIEWYKONANE**, **OK**, **BŁĄD**, **UZGODNIONE OGRANICZENIE**. Każde OK wymaga środowiska, daty, komendy/akcji i dowodu. Ograniczenie wymaga decyzji użytkownika; nie wpisuj go zamiast brakującego stanowiska automatycznie.

| ID | Próba / warunek | Status | Dowód / brak / następny krok |
|---|---|---|---|
| P01 | Własny wheel i zasoby SQL/CSS, manifest i hashe | NIEWYKONANE | Odbiór nowego artefaktu, nie kopia historycznego wyniku 0.4.0 |
| P02 | Platformowe locki i kompletne wheelhouse, bez pobierania przy instalacji | NIEWYKONANE | Oddzielnie macOS ARM / Windows x64 |
| P03 | Czysta instalacja poza checkoutem, Python/import/pip check | NIEWYKONANE | Udowodnij brak importu z src/ projektu |
| P04 | Brak/zmieniony plik kończy instalację; spacje i polskie znaki w ścieżce | NIEWYKONANE | Nie naruszaj działającej instalacji |
| L01 | Licencje/noty/wymagane źródła wszystkich przekazywanych plików | NIEWYKONANE | Rejestr braków i ich zamknięcie dla paczki |
| L02 | Techniczna wymiana wymaganej biblioteki w lokalnej kopii wydania | NIEWYKONANE | Nie modyfikuj developerskiego venv ani biblioteki operatora |
| O01 | macOS ARM: panel, projekty, filtry, historia, eksporty | NIEWYKONANE | Nowa instalacja, numer OS/przeglądarki |
| O02 | Windows 11 x64/NTFS: instalacja i panel | NIEWYKONANE | Wymaga rzeczywistego Windows |
| O03 | Windows 10 22H2 x64/NTFS: instalacja i krytyczne ścieżki | NIEWYKONANE | Dostępność stanowiska niepotwierdzona |
| W01 | Natywne IPv4 Windows: źródło/interfejs/VPN, timeout/cancel | NIEWYKONANE | Fizyczna próba, nie tylko argument ctypes |
| W02 | NTFS: dostęp drugiego zwykłego konta odmówiony | NIEWYKONANE | Baza, config, backup, eksport, plik tymczasowy |
| W03 | Windows: dwa procesy i blokady; brak niechronionego fallbacku | NIEWYKONANE | Kontrolowane dane i zakres |
| F01 | Bez Internetu i z wyłączonym cache: instalacja/start/eksport | NIEWYKONANE | Operator przygotowuje odłączenie, bez samodzielnej zmiany sieci przez agenta |
| N01 | Mały LAN bez seedów, źródła/cache/brak ICMP, anulowanie | NIEWYKONANE | Nowa osobna zgoda na dokładny zakres |
| N02 | Rzeczywisty SNMPv2c: transport/tabele | NIEWYKONANE | Model/wersja/obsługiwane MIB, bez poświadczeń |
| N03 | Rzeczywisty SNMPv3 SHA-256/AES-128 authPriv | NIEWYKONANE | Osobne potwierdzenie odczytu, nie sam wybór opcji |
| N04 | Rzeczywisty SSH cisco_ios i sześć istniejących parserów | NIEWYKONANE | Klucz hosta, faktyczny model/wersja |
| T01 | Dwa switche/dwa VLAN-y, host–port–VLAN i uplink | NIEWYKONANE | Porównanie ze znanymi połączeniami |
| T02 | Zmiana portu/awaria źródła, historia bez fałszywego odłączenia | NIEWYKONANE | Zmiany laboratoryjne wykonuje operator |
| R01 | D14: import ≤30 s / infrastruktura ≤5 s | NIEWYKONANE | Zainstalowana paczka, metoda pomiaru |
| R02 | Łączny RAM aplikacja+karta ≤1,5 GB | NIEWYKONANE | Nie zaliczaj na podstawie samego RSS Pythona |
| U01 | Aktualizacja obok starej wersji, spójna kopia i rollback | NIEWYKONANE | Dane tymczasowe i zachowane oryginały |
| U02 | Retencja/budżet danych/eksportów i przerwanie po braku miejsca | NIEWYKONANE | Symulowane limity, nie zapełnianie dysku operatora |
| Z01 | Release notes, macierz wsparcia, raport i instrukcje | NIEWYKONANE | Zgodne z dowodami konkretnego kandydata |

## Decyzja końcowa

- Pełne MVP: **nie zatwierdzono — odbiór Etapu 5 nie rozpoczęty**.
- Ograniczone wydanie: **brak decyzji użytkownika o ograniczeniu zakresu**.
- Otwarte pozycje i ich wpływ: wszystkie pozycje powyżej oczekują na wykonanie zgodnie z planem.
- Zatwierdzający / data / zakres przekazania: do uzupełnienia po wynikach.
- Publikacja / Git tag / push: brak autoryzacji w ramach przygotowania planu.

## Dodatkowy punkt wejścia — rzeczywisty LAN 0.4.0

[Odbiór LAN](../etap-4/ODBIOR_LAN_2026-10-25.md) wykonano na kodzie 0.4.0, przed budową nowej paczki. Kolekcja i eksporty mają dowody działania, ale mapy nie zaliczono z powodu wpisu rozgłoszeniowego i duplikatu własnego IPv4. Stanowi to materiał do regresji i priorytet przed pakowaniem; nie zmienia wierszy odbioru przyszłego artefaktu na OK.
