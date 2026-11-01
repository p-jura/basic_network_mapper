# Karta odbioru Etapu 5 — 0.5.0rc1

Stan: **25 października 2026 r., część wykonana, pełny odbiór otwarty**. Plan i implementację zatwierdzono osobno: „Tak, zatwierdzam wdrożenie Etapu 5”. [Raport z dowodami](RAPORT_ETAP_5.md), [wyniki zbiorcze](ODBIOR_2026-10-25.json), [macierz](MACIERZ_WSPARCIA.md). Dawny pusty szablon został uzupełniony wynikami, nie uznany automatycznie za zaliczony.

## Kandydat

| Pole | Wynik |
|---|---|
| Wersja / baza | 0.5.0rc1, commit bazy 69a94c8df352a54eaa69049618e46cfaeeaea364, drzewo dirty; bez nowego commita |
| Artefakty | Dwa ZIP, 51 kół na platformę; sumy w raporcie i plikach .sha256 |
| Wykonane stanowisko | macOS 26.6.2 ARM64, Python 3.13.0, przeglądarka wbudowana (numer silnika niedostępny) |
| Dostępność Windows | Operator potwierdził Windows 10 lub 11; dokładny OS i receipt nieotrzymane |
| Dane prób | Wyłącznie syntetyczne; prywatne projekty operatora nietknięte; żadnych nowych sond |
| Publikacja / gotowość | Wewnętrzny kandydat; materiały i odbiory pozostają otwarte; brak publikacji |

## Rejestr

Statusy: OK, NIEWYKONANE, BŁĄD, UZGODNIONE OGRANICZENIE. Brak środowiska nie jest uzgodnionym zmniejszeniem wymagań. Wiersze podzielono na platformy tam, gdzie tylko jedna ma dowód.

| ID | Próba | Status | Dowód / następny krok |
|---|---|---|---|
| P01 | Wheel, SQL/CSS, manifest i hashe | OK | Ten sam wheel w obu ZIP; 349 plików w manifestach, weryfikacja archiwów |
| P02-M | Lock/wheelhouse i instalacja bez pobierania macOS | OK | 51 dokładnych kół, dwie świeże instalacje, no-index/only-binary/require-hashes |
| P02-W | Lock/wheelhouse Windows | OK — przygotowanie | 51 kół, hashe i docelowe markery zależności; to nie instalacja na Windows |
| P03-M | Czysta instalacja macOS poza checkoutem | OK | Nowe site-packages, wersja modułu/metadanych, pip check, receipt |
| P03-W | Czysta instalacja Windows | NIEWYKONANE | Gotowy ZIP i instrukcja operatora |
| P04 | Brak/zmieniony plik; Unicode/spacje; odmowa nadpisania venv | OK — macOS | Rzeczywiste negatywne kopie paczki przed utworzeniem venv; oryginał zachowany |
| L01 | Pełny przegląd materiałów wszystkich komponentów | NIEWYKONANE | Źródła/noty zebrane; otwarta kompletność natywnych i JS atrybucji |
| L02 | Zgodna wymiana bibliotek LGPL | OK — macOS | Paramiko/scp/autocommand, import zmienionych kopii, przywrócone oryginały |
| O01 | macOS: panel/filtry/historia/eksporty | OK | Zainstalowany wheel; PNG obejrzany i SVG XML/etykiety; 58 testów |
| O02 | Windows 11 x64/NTFS: instalacja i panel | NIEWYKONANE | Oczekiwanie na receipt konkretnego stanowiska |
| O03 | Windows 10 22H2 x64/NTFS | NIEWYKONANE | Test jednego Windows nie zalicza drugiego |
| W01 | Windows native IPv4: źródło/interfejs/VPN/cancel | NIEWYKONANE | Wymaga dokładnego zakresu i rzeczywistego testu |
| W02 | NTFS: odmowa dostępu drugiego zwykłego konta | NIEWYKONANE | Config/baza/backup/serwerowe eksporty |
| W03 | Windows: dwa procesy/locki/ochrona bez fallbacku | NIEWYKONANE | Rzeczywista próba; atrapy są wcześniejszym, innym dowodem |
| F01 | Fizycznie bez Internetu i bez cache | NIEWYKONANE | Lokalne URL i pip no-index potwierdzono osobno; operator przygotowuje stanowisko |
| N01 | Podstawowy LAN kandydata | NIEWYKONANE | Brak nowej zgody na zakres; wcześniejszy skan i replay są historyczne |
| N02 | Rzeczywisty SNMPv2c | NIEWYKONANE | Wymaga urządzenia/modelu/wersji i zakresu |
| N03 | Rzeczywisty SNMPv3 SHA256/AES128 | NIEWYKONANE | Jak wyżej, osobny dowód odczytu |
| N04 | SSH cisco_ios / sześć poleceń | NIEWYKONANE | Wymaga potwierdzonego klucza hosta i sprzętu |
| T01 | Dwa switche, dwa VLAN, rzeczywiste porty/uplink | NIEWYKONANE | Syntetyczna mapa nie zastępuje znanych połączeń |
| T02 | Zmiana portu/awaria na sprzęcie | NIEWYKONANE | Zmiany laboratoryjne wykonuje operator |
| R01 | D14 import ≤30 s / infrastruktura ≤5 s | OK — macOS | 5,773 s / 1,549 s; drugi wynik zawiera narzut automatyzacji |
| R02 | RAM aplikacja+karta ≤1,5 GB | NIEWYKONANE | Peak RSS samego procesu 539 639 808 B nie zalicza kryterium |
| U01 | Aktualizacja na kopii i powrót | OK — macOS | Osobne 0.4.0/0.5.0rc1, spójny backup, niezmieniony oryginał i stare wyniki |
| U02 | Retencja/budżet/ENOSPC | OK — syntetyczne macOS | Zachowany anchor i eksporty; odmowa nowych zapisów; symulowane ENOSPC config |
| Z01 | Instrukcje, release notes, macierz i raport | OK — kandydat | Zgodne z otwartymi wierszami; to nie końcowe wydanie |

## Decyzja końcowa

Pełne MVP/Etap 5: **nie odebrano**. Nie podjęto decyzji o ograniczeniu D01 ani protokołów. Zgoda na implementację nie zastępuje wyników i akceptacji końcowej. Następny krok: instalacja offline i receipt na dostępnym Windows według [instrukcji](URUCHOMIENIE_I_ODBIOR_WINDOWS.md), następnie pozostałe próby i przegląd materiałów. Każdy aktywny odczyt wymaga osobnego zakresu; brak upoważnienia do skanu, publikacji, tagu i pushu.
