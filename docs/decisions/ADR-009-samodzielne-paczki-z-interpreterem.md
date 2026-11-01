# ADR-009 — samodzielne paczki z dołączonym interpreterem

Data: **1 listopada 2026 r.** Status: **propozycja do zatwierdzenia z planem 5A**. Użytkownik zlecił utworzenie planu po omówieniu braku Pythona na komputerze odbiorcy. Nie zatwierdził jeszcze implementacji tej zmiany. [Plan i kryteria](../poradniki/ETAP_5A_SAMODZIELNE_PACZKI_BEZ_PYTHONA.md), [karta prób](../etap-5a/KARTA_ODBIORU_ETAP_5A.md).

## Kontekst

[ADR-007](ADR-007-pakowanie-i-odbior-wydania.md) wprowadził ZIP, lokalne koła i tworzenie venv z wcześniej zainstalowanego Python 3.13. Kandydat 0.5.0rc1 działa według tego kontraktu. Nowy cel: rozpakowanie i uruchomienie na wspieranym komputerze bez instalowania Pythona. To zmiana runtime/pakowania, nie zmiana silnika sieciowego. Otwarte odbiory i materiały Etapu 5 zachowują status.

## Proponowane decyzje

1. Nowe osobno nazwane samodzielne ZIP-y Windows x64 i macOS ARM64. Python 3.13 i wymagane biblioteki w paczce; u odbiorcy nie ma tworzenia venv, instalowania pip ani pobierania zależności. Venv pozostaje narzędziem dewelopera/builda.
2. Pierwsza metoda do sprawdzenia: PyInstaller onedir, natywny build na każdym OS. Narzędzie i jego zależności mają osobny lock build-time. Wersje runtime zachowujemy; zmiana tylko po dowodzie konieczności i wąskiej regresji. Bez onefile, graficznego instalatora, CI/CD, updatera i dodatkowej aplikacji.
3. Domyślny start: panel lokalny z konsolą procesu. To samo wejście obsługuje istniejące CLI i maintenance. Frozen sys.executable nie jest traktowany jak interpreter do uruchamiania -m pip lub plików .py. Wspólna logika receipt/backup działa w tym samym runtime.
4. Krótki prototyp przed pełnym pakowaniem ma udowodnić zasoby/metadane i zgodną wymianę Paramiko/scp/autocommand ładowanych z rzeczywiście wymienionych plików. Onedir nie jest samodzielnym dowodem tej własności. Negatywny wynik zatrzymuje wybór tej metody i prowadzi do korekty planu, zamiast zmiany warunków zależności.
5. Zasoby paczki tylko do odczytu, projekty nadal w prywatnym katalogu użytkownika. Manifest samodzielnego artefaktu v2 może opisywać kontrolowane symlinki wewnątrz katalogu macOS; ochrona linków i ACL danych nie jest osłabiana. Archiwizacja zachowuje linki/uprawnienia; nowe archiwa mają nową tożsamość i sumy. Rc1 v1 i jego raporty pozostają.
6. Zachowujemy jawny start kolekcji, read-only urządzeń, ENV, limity, źródło/interfejs, anulowanie i loopback panelu. Ocena środowiska procesów systemowych jest częścią odbioru frozen; nie wolno wprowadzić wyścigu globalnych ścieżek DLL z kolektorami.
7. Dołączony interpreter, loader, DLL/frameworki i zasoby wymagają nowego inwentarza oraz odpowiednich materiałów. Własna MIT pozostaje; istniejące luki L01 nie zostają zamknięte przez zmianę formatu. Podpis ad hoc/wewnętrzny kandydat nie oznacza publicznego podpisu, notaryzacji ani braku ostrzeżeń OS. Nie zakładamy certyfikatów ani zakupów.
8. Odbiór na rzeczywistych czystych stanowiskach bez wymaganego Python 3.13, nie tylko z ukrytą komendą PATH. Osobne wyniki Windows 10/11 i macOS, mały test executable, otwarcie eksportów, kopia/rollback i pomiar D14/RAM. Bez nowych aktywnych sond na podstawie zgody na pakowanie.

## Skutki i status wcześniejszej decyzji

Po zaakceptowaniu i wykonaniu tego ADR zmienią się punkty ADR-007 dotyczące wymaganego Pythona u odbiorcy i sposobu tworzenia runtime. Do tego czasu ADR-007 nadal opisuje działający rc1. Pozostałe zasady: jedna aplikacja, wersje, izolacja danych, źródła/noty, dowody odbioru i osobna zgoda na publikację/sondy — pozostają aktualne.

Akceptacja zakresu A0–A7 pozwoli wdrażać rutynowe kroki bez pytania o nie ponownie. Wynik A2, rzeczywista dostępność stanowisk i ewentualne nowe koszty mają być jawne. Nie zmieniamy macierzy wsparcia tylko dlatego, że jednego stanowiska jeszcze nie ma. Obecne polecenie obejmuje jedynie przygotowanie planu i tego ADR.
