# Etap 5A — wdrożenie samodzielnego runtime

Data: **1 listopada 2026 r.** Wersja **0.5.0rc2**, baza Git `20889851ed6a113ba8502f00c279bf954e91b6ba`, początek zadania: czyste drzewo. Użytkownik zatwierdził plan słowami „ok implementuj plan”; ADR-009 zapisano przed kodem. Doprecyzowanie: jedna docelowa paczka Windows x64 dla **Windows 10 22H2 i Windows 11**.

**Wynik:** kod i samodzielny ZIP macOS ARM64 wdrożone. Przygotowano Windows build kit ze skryptem, źródłami i lokalnymi zależnościami. **Windows .exe nie zbudowano** — brak potwierdzonego dostępu wykonawczego do natywnego stanowiska. Pełny odbiór 5A i Etapu 5 pozostaje otwarty. Nie deklarujemy ukończonego MVP.

## Co zmieniono

- PyInstaller **6.22.3**, hooks **2026.9**, natywny onedir; narzędzia i koła sprawdzone względem oficjalnych hashy PyPI. Osobne locki build-time i runtime. Dotychczasowe wersje bibliotek aplikacji bez zmian; Python macOS **3.13.0** pochodzi z istniejącego stanowiska budowania.
- Jedno wejście: bez argumentów panel, istniejące CLI, `doctor`, `verify`, `maintenance receipt/backup/runtime-check`. Odbiorca nie tworzy venv, nie wywołuje pip, nie instaluje Pythona. Błędne argumenty maintenance nie wypisują surowego argv.
- Wspólne maintenance przeniesiono do `src/mapper/maintenance.py`; stary launcher jest cienkim wrapperem. Poprzednią implementację zachowano w old z wpisem w rejestrze. Istniejące ZIP rc1 nie zostały zmienione.
- Zebrano SQL, CSS/JS, metadane dystrybucji, ntc-templates, moduły dynamiczne SNMP/SSH i rozszerzenia natywne. Paramiko/scp/setuptools z vendored autocommand są wymienialnymi plikami Python poza PYZ.
- Windows: add_dll_directory zachowuje uchwyty katalogów rozszerzeń; reset SetDllDirectory następuje raz przed pracownikami. Nie ma przełączania globalnego DLL path podczas odczytów. Sprawdzone na atrapach; rzeczywisty Windows nadal wymagany. Na macOS otwarcie przeglądarki korzysta z /usr/bin/open; środowisko procesów systemowych usuwa wyłącznie ścieżki loadera prowadzące do paczki, zachowując ENV profili.
- Manifest v2 zapisuje pliki i kontrolowane wewnętrzne symlinki; ZIP zachowuje ich typ i wykonywalność. Jawne verify wykrywa zmiany, brak/dodatkowe pliki, pętle/wyjście linka i reparse points. Nie osłabiono ochrony linków w danych projektów. Start nie blokuje zgodnie wymienionych bibliotek LGPL.
- README.md oraz START_TUTAJ.md w katalogu paczki opisują start, konsolę/Ctrl+C, dane poza programem, offline, diagnostykę, backup/rollback i ograniczenia. macOS ma `Uruchom Mapper.command`; Windows spec przewiduje Mapper.exe z konsolą.
- Dołączono inwentarz plików natywnych, źródła CPython i narzędzi, noty PSF/OpenSSL oraz materiały rc1. Pełny przegląd L01 nadal otwarty; ad hoc nie jest podpisem publicznej dystrybucji.

## Wykonane sprawdzenia

1. **63 krytyczne testy**, 1,958 s; `pip check`: bez konfliktów. Pięć nowych grup chroni dispatch, sekrety w błędnych argumentach, manifest/ZIP/linki, środowisko procesów oraz inicjalizację DLL. Próba linków POSIX nie wymaga uprawnień administratora na Windows; natywne NTFS pozostaje oddzielnym odbiorem.
2. Prototyp A1–A2: doctor, receipt, SQL i pięć eksportów; runtime-check importuje Paramiko/scp/autocommand, cryptography i psutil, tworzy i zamyka SnmpEngine **bez transportu**, odczytuje parser VLAN. Bez ruchu do urządzeń.
3. Wymiana wszystkich trzech bibliotek na zgodne zmodyfikowane pliki z rozpoznawalnym `__version__` rzeczywiście zmienia wynik importu w executable. Po próbie przywrócono dokładne bajty; verify ponownie OK. Sprawdzone także na rozpakowanym ZIP.
4. ZIP rozpakowano narzędziem macOS ditto; symlinki i uprawnienia przeszły manifest. Przeniesienie do polskiej ścieżki, obcy CWD i celowo błędne PYTHONPATH/PYTHONHOME nie wczytały obcych modułów. PATH bez Pythona to próba izolacji — **nie zastępuje czystego OS bez zainstalowanego interpretera**.
5. Syntetyczny receipt: 3 węzły/2 relacje, integralność SQLite OK, 0 błędów FK, 5 eksportów danych. Backup nie zmienia bajtów oryginału; odczyt kopii i import snapshotu zarządzanego OK. Końcowy ZIP ponownie sprawdzony przez verify/doctor/runtime-check/receipt i redakcję argumentów.
6. Panel z rzeczywistego executable na 127.0.0.1:8056, offline: 2 switche i host, 3 relacje. Klik hosta pokazuje 192.0.2.20 / 02:00:00:00:00:20, Gi101/VLAN10 i wysoką pewność; uplink Gi900 pozostaje kandydatem. Zmiana zoom działa. Screenshot zawiera wyłącznie dane syntetyczne.
7. **11 lokalnych JS/CSS, wszystkie HTTP 200**, brak odwołań CDN w wymaganych zasobach strony. Fizycznego odłączenia Internetu/cache nie wykonano. Kliknięto PNG/SVG; narzędzie przeglądarki nie udostępniło pobranych plików do oględzin. **Nie zaliczono odbioru obrazów**; nie uznano tego za dowód błędu produktu.
8. Druga instancja na zajętym porcie kończy się kodem 2 / PANEL_PORT_UNAVAILABLE, pierwsza nadal działa. Własny serwer zakończono Ctrl+C, zamykając kontroler i port. Pierwsza próba bind w sandboxie dostała odmowę OS; powtórzona poza sandboxem na loopback działała — nie była to awaria paczki.
9. D14: syntetyczne **50 switchy, 1000 hostów, 20 VLAN, 50 000 obserwacji, jawnie wspólny kontekst blue**. Import i budowa/eksport przez executable: **4,404 s + 6,792 s = 11,196 s**. Próbkowany szczyt RSS aplikacji **916 357 120 B**. Widok infrastruktury z tego grafu: 50 węzłów, projekcja 0,055 s w identycznym kodzie źródłowym; nie jest to pomiar opóźnienia przeglądarki. Łącznego RAM aplikacja+karta nie zmierzono.

D14 celowo obejmuje 45 900 kandydatur; 918 konfliktów przypisania pozostaje jawnych, nie wymuszamy kabla przez najmniejszą liczbę MAC-ów. Pierwsza próba fixture nie podawała wspólnego kontekstu; silnik prawidłowo izolował adresacje per target, co rozszerzało liczbę obiektów, a budżet odmówił zapisu dużego wyniku. Nie zwiększono budżetu i nie scalono nieznanych VRF. Właściwa próba 1000 wspólnych hostów jawnie określa kontekst; wynik nie dowodzi wydajności dowolnej gęstej sieci/nieznanych VRF.

## Artefakty i odtworzenie

Katalog repozytorium: `dist/etap-5a-2026-11-01/` (ignorowany przez Git):

- `mapper-sieci-0.5.0rc2-macos-arm64-standalone.zip` i suma — działający kandydat macOS z interpreterem.
- `mapper-sieci-0.5.0rc2-windows-x64-build-kit.zip` i suma — **zestaw budowania**, bez gotowego .exe. Instrukcja [Windows](BUDOWANIE_I_ODBIOR_WINDOWS.md).
- `ARTEFAKTY.json` — dokładne rozmiary i SHA-256 przekazanych plików.

Źródłowe pliki budowania: `packaging/standalone/Mapper.spec`, entry.py, build.py, bootstrap.py, hooki, locki i skrypty. `build.py` bierze jawne katalogi materiałów i work/output; nie pobiera pakietów. `prepare_runtime.py` jest krokiem stanowiska budowania dla odpowiadających źródeł/not. Nie jest częścią startu mappera.

Komendy sprawdzeń (Python oznacza interpreter odizolowanego build-env):

```sh
python -m unittest discover -s tests/critical
python -m pip check
PYINSTALLER_CONFIG_DIR=/prywatny/work/cache python -m PyInstaller --noconfirm --distpath /prywatny/work/dist --workpath /prywatny/work/pyinstaller packaging/standalone/Mapper.spec
./Mapper verify
./Mapper doctor
./Mapper maintenance runtime-check
./Mapper maintenance receipt --data-dir /prywatny/nowy-katalog
```

Rzeczywiste logi i receipt są poza repozytorium; publiczne [podsumowanie prób](ODBIOR_2026-11-01.json) nie zawiera danych LAN ani poświadczeń. [Screenshot panelu](PANEL_STANDALONE.png) dotyczy danych dokumentacyjnych. Po zapisaniu plików repozytorium sprawdzono diff, odnośniki i regresję; brak commit/push/tag/publikacji.

## Niewykonane warunki

Natywny Windows build i testy obu OS, efektywne NTFS, start z Findera/Explorera i rzeczywista kopia ZIP między komputerami, czysty macOS/Windows bez Pythona, fizyczny brak Internetu/cache, odbiór PNG/SVG, łączny RAM oraz materiały L01. Pozostają również sprzętowe warunki Etapu 5: rzeczywiste SNMP/SSH i źródło IPv4 Windows. Pakowanie nie autoryzuje nowego skanu.

**Następny krok:** wykonać przygotowany BUDUJ_WINDOWS.cmd na natywnym Windows x64 i przekazać wynik; następnie odebrać ten sam ZIP na Windows 10 i 11 oraz czystym macOS. Do tego czasu brak deklaracji pełnej zgodności i ukończenia A4/A6/A7.
