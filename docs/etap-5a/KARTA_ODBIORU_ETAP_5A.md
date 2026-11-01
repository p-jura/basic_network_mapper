# Karta odbioru 5A — samodzielne paczki

Aktualizacja **1 listopada 2026 r.** Plan i ADR-009 zatwierdzone słowami „ok implementuj plan”. Kod 0.5.0rc2/macOS wdrożony; **pełny odbiór otwarty**. [Raport](RAPORT_ETAP_5A.md), [plan](../poradniki/ETAP_5A_SAMODZIELNE_PACZKI_BEZ_PYTHONA.md), [Windows](BUDOWANIE_I_ODBIOR_WINDOWS.md). Nie przenosimy wyników rc1 jako dowodów nowego formatu.

## Artefakt i stanowisko

- Baza: `20889851ed6a113ba8502f00c279bf954e91b6ba`, początek czysty; zmiany 5A bez commita agenta.
- macOS: ARM64, system zgłasza macOS 26.6.2, Python dołączony 3.13.0, PyInstaller 6.22.3 / hooks 2026.9.
- ZIP i dokładne sumy: `dist/etap-5a-2026-11-01/ARTEFAKTY.json`; macOS standalone oraz Windows **build kit**, bez .exe.
- Testowe stanowisko macOS ma zainstalowany Python; ukrycie PATH/PYTHONHOME sprawdzono, lecz nie zastępuje czystego OS.
- Przeglądarka IAB; brak fizycznego odłączenia Internetu/cache. Wyłącznie dane syntetyczne i loopback; brak sond LAN.
- Docelowy Windows: **jeden ZIP x64, oddzielny odbiór Windows 10 22H2 i Windows 11**. Dostęp wykonawczy niepotwierdzony.

## Rejestr

Każdy status dotyczy wyłącznie wymienionego zakresu. Brak wiersza Windows OK oznacza brak natywnego dowodu, nie zgodność domyślną.

| ID | Warunek | macOS | Windows 10 / 11 | Dowód / ograniczenie |
|---|---|---|---|---|
| S01 | Prototyp panel/doctor/receipt z dołączonego runtime | OK | NIEWYKONANE / NIEWYKONANE | Executable, SQLite i pięć eksportów |
| S02 | Zgodna wymiana bibliotek i rzeczywisty import | OK | NIEWYKONANE / NIEWYKONANE | Paramiko/scp/autocommand, przywrócenie bajtów i verify |
| S03 | Native build, zasoby, metadane, moduły protokołów | OK | NIEWYKONANE / NIEWYKONANE | Spec/hooks; runtime-check bez komunikacji; Windows build kit nie jest .exe |
| S04 | Manifest/ZIP/linki i uprawnienia | OK | NIEWYKONANE / NIEWYKONANE | Ditto + verify; testy negatywne; NTFS rzeczywisty nadal wymagany |
| S05 | Start na czystym OS bez systemowego Pythona | NIEWYKONANE | NIEWYKONANE / NIEWYKONANE | Obecny Mac ma Python.framework |
| S06 | Start offline także Finder/Explorer | NIEWYKONANE | NIEWYKONANE / NIEWYKONANE | Terminal/executable OK; dwuklik i przekazanie na inne stanowisko otwarte |
| S07 | Import/demo, szczegóły, historia, pięć eksportów danych | OK w sprawdzonym przekroju | NIEWYKONANE / NIEWYKONANE | Receipt/backup/import; host Gi101/VLAN10; pełny ręczny odbiór filtrów/historii do powtórzenia na czystym OS |
| S08 | PNG/SVG otwarte, offline bez cache/Internetu | NIEWYKONANE | NIEWYKONANE / NIEWYKONANE | Przyciski kliknięto; pliki niedostępne w automatyzacji, brak oględzin; 11 JS/CSS lokalne HTTP200 |
| S09 | Przeniesienie, Unicode/spacje, obcy CWD/importy | OK | NIEWYKONANE / NIEWYKONANE | Przed i po uruchomieniu; PATH bez Python, błędne PYTHONPATH/HOME bez obcego importu |
| S10 | Zajęty port, drugi proces, Ctrl+C | OK w sprawdzonym przekroju | NIEWYKONANE / NIEWYKONANE | Kod2 PANEL_PORT_UNAVAILABLE, pierwsza działa; Ctrl+C zamyka. Anulowanie kolekcji chronią testy offline |
| S11 | Receipt/backup/odczyt kopii bez python -m | OK | NIEWYKONANE / NIEWYKONANE | Oryginał bazy byte-exact, nowa kopia odczytana; stary model SQLite bez zmian |
| S12 | Procesy systemowe/przeglądarka i DLL | NIEWYKONANE w pełnym zakresie | NIEWYKONANE / NIEWYKONANE | Testy środowiska i Windows DLL na atrapach OK; prawdziwych sond/Windows nie wykonano |
| S13 | Prywatne pliki/efektywny NTFS drugiego konta | NIEWYKONANE | NIEWYKONANE / NIEWYKONANE | Nie zastępujemy NTFS testem POSIX |
| S14 | Kompletny przegląd materiałów interpretera i wszystkich części | NIEWYKONANE | NIEWYKONANE / NIEWYKONANE | Inwentarz/noty/źródła dołączone; L01 nadal otwarty |
| S15 | D14 i łączny RAM z kartą przeglądarki | NIEWYKONANE w całości | NIEWYKONANE / NIEWYKONANE | Native import+build 11,196s; projekcja źródłowa0,055s; RSS916357120B; łącznego RAM i opóźnienia UI nie zmierzono |
| S16 | Transfer ZIP między komputerami i zwykłe rozpakowanie/ochrona OS | NIEWYKONANE | NIEWYKONANE / NIEWYKONANE | Lokalny ditto OK; ad hoc nie oznacza publicznego podpisu |
| S17 | Raport, instrukcje, nowa tożsamość i akceptacja wyniku | NIEWYKONANE w całości | NIEWYKONANE / NIEWYKONANE | Dokumenty i kandydat gotowe; akceptacja wyniku nie została udzielona |

## Decyzja

A0–A3 wykonane w dostępnym zakresie macOS; A4 wymaga natywnego Windows; A5 ma macOS i zestaw budowania; A6/A7 pozostają otwarte. Nie opublikowano wydania. Sprzęt SNMP/SSH, źródło Windows, NTFS, RAM i L01 z Etapu 5 zachowują status. Nowy aktywny odczyt wymaga osobno określonego zakresu.
