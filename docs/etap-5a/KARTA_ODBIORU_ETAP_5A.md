# Karta odbioru 5A — paczki bez instalowania Pythona

Utworzono: **1 listopada 2026 r.** Status: **plan; wszystkie nowe próby niewykonane**. [Plan](../poradniki/ETAP_5A_SAMODZIELNE_PACZKI_BEZ_PYTHONA.md), [propozycja ADR-009](../decisions/ADR-009-samodzielne-paczki-z-interpreterem.md). Nie kopiujemy wyników rc1 do odbioru nowego formatu. [Karta pełnego Etapu 5](../etap-5/KARTA_ODBIORU_ETAP_5.md) zachowuje dotychczasowe stany.

## Artefakt i stanowisko

| Pole | Wartość |
|---|---|
| Wersja / commit / dirty state | Do uzupełnienia przy budowie; brak nowego kandydata |
| ZIP / SHA-256 / manifest | Nie utworzono |
| PyInstaller / hooki / interpreter | Dokładne wersje i źródła do ustalenia w A0–A2 |
| System / architektura / sposób rozpakowania | Oddzielnie Windows 10, Windows 11, macOS ARM |
| Brak systemowego Python 3.13 | Dowód czystego stanowiska; nie samo PATH |
| Przeglądarka / brak Internetu/cache | Do zapisania przy próbie |
| Prywatny receipt | Lokalizacja dowodów bez sekretów i danych klienta w repo |

## Rejestr nowych prób

Każdy wiersz zapisuj osobno dla każdej odebranej platformy/wersji OS. Statusy: NIEWYKONANE, OK, BŁĄD, UZGODNIONE OGRANICZENIE. Ostatni wymaga decyzji użytkownika.

| ID | Warunek | Status | Dowód / ograniczenie |
|---|---|---|---|
| S01 | Prototyp onedir uruchamia panel/doctor/receipt z dołączonego runtime | NIEWYKONANE | Warunek A2 |
| S02 | Zgodna wymiana wymaganych bibliotek i faktyczne miejsce importu | NIEWYKONANE | Paramiko, scp, autocommand; nie sam plik obok programu |
| S03 | Build natywny i komplet zasobów/metadanych/DLL | NIEWYKONANE | Spec, hooki, SQL, CSS/JS, parsery, dołączone moduły protokołów |
| S04 | Bezpieczny manifest/ZIP macOS i symlinki; ochrona danych bez zmian | NIEWYKONANE | Wewnętrzne cele, brak pętli/wyjścia z katalogu, APFS |
| S05 | Rzeczywisty start na czystym wspieranym OS bez Python 3.13 | NIEWYKONANE | OS/stanowisko/receipt; bez odinstalowywania narzędzi użytkownika |
| S06 | Start offline bez pip/venv/download, także Explorer/Finder | NIEWYKONANE | Czytelny URL/start/błąd; brak skanu |
| S07 | Import/demo, filtry, szczegóły, historia i pięć eksportów danych | NIEWYKONANE | Dane syntetyczne, nowy prywatny katalog |
| S08 | PNG/SVG otwarte; wymagane zasoby lokalne bez cache/Internetu | NIEWYKONANE | XML/etykiety/oględziny; oddzielić problem narzędzia od produktu |
| S09 | Przeniesiona paczka, Unicode/spacje, obcy CWD i brak obcych importów | NIEWYKONANE | Przed pierwszym i po wcześniejszym uruchomieniu |
| S10 | Zajęty port, drugi proces, anulowanie/Ctrl+C i zamknięcie zasobów | NIEWYKONANE | Bez zatrzymywania cudzej instancji |
| S11 | Receipt i spójny backup działają bez zewnętrznego python -m | NIEWYKONANE | Kopia istniejącego projektu, niezmieniony oryginał i rollback |
| S12 | Procesy systemowe/przeglądarka i DLL nie używają błędnych bibliotek | NIEWYKONANE | Bez wyścigu z pulą kolektorów; próby kodowe na atrapach |
| S13 | Prywatne pliki i efektywny dostęp NTFS z drugiego konta | NIEWYKONANE | Wspólny warunek Etapu 5; wymagany rzeczywisty Windows |
| S14 | Manifest/noty/źródła interpretera, loadera i wszystkich dołączonych części | NIEWYKONANE | Nie zamykać L01 bez przeglądu |
| S15 | D14: ≤30 s import / ≤5 s infrastruktura / ≤1,5 GB app+karta | NIEWYKONANE | Wynik nowego executable, nie tylko RSS Pythona |
| S16 | Przekazany ZIP rozpakowany zwykłym narzędziem, komunikaty ochrony OS | NIEWYKONANE | Nie mylić ad hoc z podpisem dystrybucyjnym |
| S17 | Raport, instrukcje, nowa tożsamość archiwów i akceptacja wyniku | NIEWYKONANE | Bez publikacji i operacji Git |

## Decyzja

Wdrożenie 5A: **oczekuje na zatwierdzenie planu/ADR-009**. Odbiór: **niewykonany**. Nie utworzono paczek bez Pythona. Otwarte odbiory sprzętowe SNMP/SSH, źródła Windows, RAM, NTFS i materiałów z Etapu 5 nie stają się zaliczone przez przygotowanie tej karty. Każdy nowy aktywny odczyt wymaga osobnego wskazanego zakresu.
