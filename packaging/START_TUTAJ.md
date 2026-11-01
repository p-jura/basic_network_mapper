# Mapper sieci — kandydat do odbioru

Pawel Juroszek · FL Development. To lokalny kandydat testowy, nie odebrane pełne MVP. Wersja, platforma, hashe, pochodzenie i otwarte pozycje odbioru są w manifest.json, provenance.json i license-review.json. Materiały zależności zachowują odrębne warunki w licenses/ i sources/. Własna MIT nie zastępuje ich licencji. Brak publikacji ani automatycznej aktualizacji.

## Wymagania i instalacja

Wcześniej zainstalowany **Python 3.13** w architekturze odpowiedniej dla ZIP: macOS ARM64 albo Windows x64. Python/interpreter i przeglądarka nie są dołączone. Rozpakuj do nowego lokalnego katalogu z prawem zapisu, np. w swoim katalogu użytkownika. Używaj lokalnego APFS/NTFS; dane SQLite nie powinny trafiać na dysk sieciowy/synchronizowany. Nie instaluj jako administrator.

Najpierw porównaj SHA-256 archiwum z plikiem .sha256 przekazanym obok niego. Na macOS użyj `shasum -a 256 NAZWA.zip`, na Windows PowerShell `Get-FileHash .\NAZWA.zip -Algorithm SHA256`. Manifest i sumy sprawdzają spójność, nie podpis autora ani źródło zaufania.

**macOS** — Terminal w rozpakowanym katalogu:

```sh
sh install.sh
sh start.command --offline
```

**Windows** — cmd w rozpakowanym katalogu:

```bat
install.cmd
start.cmd --offline
```

Instalator weryfikuje pliki i platformę, tworzy własne .venv i instaluje dokładne koła z wheelhouse: --no-index, --only-binary i --require-hashes. Niczego nie pobiera. Zmieniony/brakujący plik przerywa instalację. Nie nadpisuje istniejącego .venv. Gdy próba zakończyła się błędem, zachowaj cały katalog do diagnozy i rozpakuj ponownie w innym miejscu. Wcześniejsze środowisko i dane projektów pozostają dostępne. Nie przenoś katalogu po utworzeniu venv; nowa lokalizacja wymaga nowej instalacji.

Skrypty nie zmieniają PATH, polityk PowerShell, firewalla ani konfiguracji sieci. Gdy system blokuje uruchomienie pobranego pliku, nie wyłączaj globalnie ochrony; skorzystaj z terminala lub wyjaśnij pochodzenie pliku. Brak poprawnego Pythona kończy pracę komunikatem, bez instalowania go w tle.

## Pierwsze uruchomienie i odbiór

Panel otworzy własny lokalny adres po uruchomieniu serwera. Offline blokuje kolektory. Utwórz „Demo offline”, wczytaj mapę, kliknij hosta i sprawdź szczegóły, filtry, historię i eksporty JSON/CSV/PNG/SVG. Demo jest syntetyczne. Dodatkowy port: `sh start.command --offline --port 8051` albo `start.cmd --offline --port 8051`. Ctrl+C zatrzymuje własny proces. Zajęty port ma wywołać błąd; aplikacja nie zatrzymuje innych procesów.

Automatyczny krótki odbiór instalacji wykonasz na **nowym katalogu danych testowych**, bez sond:

```sh
# macOS — podaj nieistniejący katalog:
.venv/bin/python -I bundle.py maintenance receipt --data-dir "$HOME/Mapper odbior/odbior-01"
```

```bat
rem Windows — podaj nieistniejący katalog:
.venv\Scripts\python.exe -I bundle.py maintenance receipt --data-dir "%USERPROFILE%\Mapper odbior\odbior-01"
```

Powstanie prywatny installation-receipt.json i demo z pięcioma eksportami danych. Receipt zawiera wersje, lokalizację importu i wyniki SQLite. Nie dowodzi działania sprzętowego SNMP/SSH, skanu LAN, efektywnego NTFS z drugiego konta ani eksportów obrazów w przeglądarce. Zachowaj go lokalnie; ścieżki mogą zawierać nazwę konta.

Dane zwykłych projektów: macOS `~/Library/Application Support/MapperSieci/projects`, Windows `%LOCALAPPDATA%\MapperSieci\projects`. W panelu można wskazać osobny katalog przez --data-dir. Wartości poświadczeń ustawiaj w prywatnym środowisku procesu; konfiguracja przechowuje tylko nazwy ENV. Nie wpisuj sekretów w argumentach, plikach instalatora ani raporcie.

## Aktualizacja i powrót

1. Zatrzymaj własne procesy mappera i zachowaj poprzedni katalog instalacji. Nowy ZIP rozpakuj obok, nie na starym venv.
2. Wykonaj spójny backup wybranego projektu. Polecenie korzysta z blokady projektu i sqlite backup, tworząc nowy prywatny katalog z project.json i mapper.sqlite3. Nie nadpisuje celu.

```sh
.venv/bin/python -I bundle.py maintenance backup --data-dir "/katalog/projects" --project PROJECT_UUID --output "/prywatne-backupy/PROJECT_UUID"
```

Na Windows użyj `.venv\Scripts\python.exe` i odpowiednich ścieżek. Nazwa końcowego katalogu kopii powinna być UUID projektu, aby jej rodzic mógł służyć jako --data-dir do offline replay. Backup bazy zawiera źródła i historię; **nie kopiuje istniejących obrazów i eksportów**. Zachowaj je osobno. Backup nie jest automatyczną migracją ani przywróceniem.

3. Zainstaluj nową wersję w nowym katalogu. Najpierw uruchom ją z --offline --data-dir wskazującym rodzica prywatnej kopii. Zweryfikuj źródła, reguły, historię i eksporty. Nie uruchamiaj starego i nowego procesu na tym samym projekcie.
4. Powrót: uruchom poprzednią instalację ze zgodną kopią danych. Nie nadpisuj nowszej bazy starszym programem i nie zmieniaj oryginału kopią roboczą. Poprzednia historia/reguły pozostają dostępne; nowe reguły odtwarzają tylko zachowane źródła.

## Granice kandydata

Rzeczywiste wsparcie opisuje raport Etapu 5. Sama obecność Windows ZIP nie oznacza odbioru Windows/NTFS, natywnych sond ani każdego modelu switcha. Przed badaniem LAN operator potwierdza dokładny zakres i limity. Wystartowanie panelu nie skanuje sieci. Fizyczny test bez Internetu przygotowuje operator; instalator nie wyłącza interfejsów. Producent OUI, fizyczne porty, VLAN-y i VRF pozostają nieustalone, gdy brak dowodów.

Biblioteki są oddzielnymi modułami w .venv i można je wymienić na zgodne wersje. Start nie porównuje ich z hashami pierwotnych kół. Zmodyfikowane biblioteki zachowują własne warunki i wymagają ponownej weryfikacji funkcji. Nie narzucamy zakazu ich modyfikacji ani inżynierii wstecznej.
