# Mapper sieci — uruchomienie samodzielnej paczki

Wewnętrzny kandydat do odbioru. Python i biblioteki są dołączone; nie instaluj Python/pip/venv. Potrzebujesz przeglądarki i lokalnego katalogu użytkownika APFS (macOS ARM64) lub NTFS (Windows x64). Docelowo jedna paczka Windows obsługuje Windows 10 22H2 i Windows 11; faktyczne odbiory muszą być zapisane oddzielnie. Nie uruchamiaj jako administrator. Brak automatycznej aktualizacji lub sond przy starcie.

1. Porównaj SHA-256 ZIP z przekazanym plikiem `.zip.sha256` (`Get-FileHash NAZWA.zip -Algorithm SHA256` w PowerShell; `shasum -a 256 NAZWA.zip` na macOS). Suma potwierdza spójność, nie tożsamość autora.
2. Rozpakuj **cały ZIP** do nowego lokalnego folderu. Zachowaj pliki i podkatalog `_internal` obok programu. Na macOS użyj systemowego Narzędzia archiwizującego zachowującego symlinki i uprawnienia; nie kopiuj pojedynczego pliku Mapper. Nie zapisuj projektów na dysku sieciowym/synchronizowanym.
3. **Windows:** dwuklik `Mapper.exe`. **macOS:** dwuklik `Uruchom Mapper.command`.
4. Panel otwiera się na lokalnym URL pokazanym w konsoli. Zatrzymasz go przez **Ctrl+C w konsoli**. Zamknięcie karty przeglądarki pozostawia serwer uruchomiony. Błąd zajętego portu nie zatrzymuje cudzych procesów.

Pierwsza próba bez odczytów sieci: uruchom z terminala otwartego w katalogu paczki:

```bat
rem Windows — cmd:
Mapper.exe panel --offline
Mapper.exe doctor
Mapper.exe maintenance runtime-check
```

```sh
# macOS:
./Mapper panel --offline
./Mapper doctor
./Mapper maintenance runtime-check
```

W panelu wybierz „Demo offline”, wczytaj mapę, sprawdź szczegóły i eksporty. `runtime-check` sprawdza importy, parser oraz tworzy silnik SNMP bez transportu; nie bada urządzeń. Inny port: `Mapper.exe panel --offline --port 8051` lub `./Mapper panel --offline --port 8051`. `--no-browser` pokazuje URL bez otwierania przeglądarki. Dla normalnej pracy pomiń `--offline`; zakres i limity potwierdzasz przed startem kolekcji.

## Dane, odbiór i backup

Dane są poza paczką: `%LOCALAPPDATA%\MapperSieci\projects` na Windows lub `~/Library/Application Support/MapperSieci/projects` na macOS. `--data-dir` pozwala wskazać prywatny katalog projektów. Paczkę można przenieść w całości; dane pozostają w swoim miejscu.

```bat
Mapper.exe maintenance receipt --data-dir "%USERPROFILE%\Mapper odbior\nowa-proba-01"
Mapper.exe maintenance backup --data-dir "C:\prywatne\projects" --project UUID --output "C:\prywatne\backupy\UUID"
Mapper.exe verify
```

Na macOS użyj `./Mapper` oraz swoich ścieżek. `receipt` wymaga **nieistniejącego katalogu**, tworzy wyłącznie projekt syntetyczny i pięć eksportów danych. `backup` tworzy nowy prywatny katalog z konfiguracją i spójną kopią SQLite; nie nadpisuje celu. Wcześniejsze obrazy/eksporty zachowaj osobno. Ścieżki w receipt mogą zawierać nazwę konta — raport przechowuj prywatnie.

Aktualizacja: zatrzymaj własny serwer, zachowaj starą paczkę, zrób backup i rozpakuj nową obok. Najpierw sprawdź nową wersję offline na kopii. Powrót wymaga poprzedniej paczki i zgodnej kopii danych; nie nadpisuj nowej bazy starszym programem ani nie uruchamiaj dwóch wersji na jednym projekcie.

## Problemy i granice

Zachowaj cały katalog i kod błędu z konsoli. `verify` wykrywa brakujące/dodatkowe/zmienione pliki oraz błędne linki. Nie jest podpisem cyfrowym. Start nie blokuje świadomie zmienionych zgodnych bibliotek LGPL; po ich zmianie `verify` prawidłowo zgłosi różnicę. Ich licencje/noty i źródła są w `licenses/`, `sources/` i `THIRD_PARTY_NOTICES.md`. Pełny przegląd komponentów pozostaje otwarty zgodnie z `license-review.json`.

Kandydat macOS jest podpisany ad hoc, Windows może nie mieć Authenticode. System może zgłosić ostrzeżenie po przeniesieniu ZIP między komputerami. Nie wyłączaj globalnie ochrony systemu, antywirusa ani firewalla; sprawdź pochodzenie i skonsultuj blokadę. Lokalny build nie potwierdza publicznej notaryzacji ani działania na każdym OS.

Start z Findera/Explorera może nie odziedziczyć ENV terminala. Przy profilach SNMP/SSH uruchom program ze środowiska zawierającego prywatne zmienne; aplikacja przechowuje tylko ich nazwy. Nie wpisuj poświadczeń w argumenty, README, raporty ani konfigurację jawną. Nie ma zmian konfiguracji urządzeń. Brak dowodów oznacza nieustalony port/VLAN, a nie zgadywane połączenie fizyczne.
