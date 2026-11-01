# Windows 10 i 11 — natywne budowanie i odbiór 5A

Status 1 listopada 2026: **przygotowano zestaw budowania; nie utworzono samodzielnego .exe**. Celem jest **jeden ZIP Windows x64**, odebrany oddzielnie na Windows 10 22H2 i Windows 11. Mac nie kompiluje tego wyniku. Windows ARM i wcześniejsze wydania nie mają deklaracji wsparcia.

## Stanowisko budowania

Zestaw `mapper-sieci-0.5.0rc2-windows-x64-build-kit.zip` znajduje się w `dist/etap-5a-2026-11-01/` repozytorium. Nie jest paczką do uruchamiania mappera. Zawiera źródła, testy krytyczne, 50 lokalnych kół runtime z lockiem (dodatkowo historyczne koło aplikacji nie jest instalowane), przypięte narzędzia PyInstaller, istniejące materiały komponentów i nowe materiały runtime.

1. Na Windows x64 przygotuj **Python 3.13 x64 i launcher py** dla dewelopera. Odbiorca wynikowego Mapper.exe nie potrzebuje Pythona.
2. Porównaj SHA-256 zestawu z plikiem obok; rozpakuj wszystko do nowego lokalnego folderu NTFS użytkownika, np. `C:\Users\TwojeKonto\Mapper build`. Bez administratora i bez nadpisywania poprzedniej próby.
3. Otwórz cmd w tym katalogu i wykonaj:

```bat
BUDUJ_WINDOWS.cmd
```

Przygotowanie materiałów może pobrać przez HTTPS z python.org źródło dokładnej używanej wersji 3.13.x i notę OpenSSL z oficjalnego repozytorium. To krok stanowiska budowania. Dołączone źródło macOS to 3.13.0; jeśli Windows ma inną wersję poprawkową, zachowujemy odpowiadające jej źródła. Koła bibliotek i narzędzi są instalowane **lokalnie, z wymaganymi hashami, bez PyPI**. Skrypt nie skanuje sieci, nie instaluje usług i nie zmienia ochrony systemu.

4. Wyniki: `dist/mapper-sieci-0.5.0rc2-windows-x64-standalone.zip` i `.zip.sha256`. Log: `work/native/pyinstaller.log`; środowisko budowania: `work/build-env`. Nie kopiuj samego Mapper.exe.
5. Błąd: zachowaj kod, log i cały work; nie zmieniaj losowo wersji i nie kasuj wcześniejszego venv. Ponowną próbę wykonaj w świeżym rozpakowaniu. Przekaż wynik bez sekretów i rzeczywistych danych LAN. Nie oznaczaj builda jako zaliczonego przed sukcesem skryptu i weryfikacją paczki.

Odpowiednik z repozytorium, gdy materiały są już przygotowane:

```bat
packaging\standalone\build-windows.cmd --wheelhouse "C:\lokalne\runtime-wheels" --build-wheels "C:\lokalne\build-wheels" --materials "C:\lokalne\materials" --runtime-materials "C:\lokalne\runtime-materials" --work "C:\lokalne\nowa-proba" --output "C:\lokalne\dist" --source-revision "COMMIT-i-stan"
```

To źródłowy wariant dla dewelopera; wszystkie podane katalogi są jawne i lokalne. Work ma być nowy. Pełny przegląd bibliotek natywnych/licencji L01 nadal pozostaje otwarty; build nie zmienia tego statusu.

## Odbiór tej samej paczki na obu systemach

Wykonaj osobno Windows 10 22H2 x64 oraz Windows 11 x64, na czystych stanowiskach bez Python 3.13. Ukrycie PATH lub inne konto na komputerze z globalnym Pythonem nie jest pełnym dowodem. Nie odinstalowuj narzędzi użytkownika do próby.

1. Zapisz OS/build, architekturę, brak Pythona, przeglądarkę, hash ZIP i sposób przekazania. Rozpakuj cały ZIP zwykłym narzędziem.
2. Dwuklik Mapper.exe otwiera właściwy lokalny URL; konsola pozostaje dostępna, start nie wysyła sond. Ctrl+C zatrzymuje serwer. Sprawdź błędny/zajęty port i komunikat przy błędzie. Nie wyłączaj globalnie SmartScreen/AV/firewalla.
3. W cmd z katalogu rozpakowanej paczki:

```bat
Mapper.exe doctor
Mapper.exe verify
Mapper.exe maintenance runtime-check
Mapper.exe maintenance receipt --data-dir "%USERPROFILE%\Mapper odbior\nowa-proba-01"
Mapper.exe panel --offline --port 8051
```

4. Demo/import: szczegóły IP/MAC/port/VLAN i niepewność, filtry, historia, pięć eksportów danych. PNG i SVG **pobierz i otwórz**; zapisz potwierdzenie etykiet. Z wyłączonym cache i fizycznie odłączonym Internetem sprawdź lokalne zasoby.
5. Przenieś całą paczkę do katalogu ze spacjami i polskimi znakami, przed pierwszym i po wcześniejszym uruchomieniu. Sprawdź start z obcego CWD; dane pozostają poza aplikacją. Sprawdź backup na prywatnej kopii i zgodny rollback.
6. Osobno potwierdź importy/DLL oraz efektywne NTFS z drugiego konta. Rzeczywiste sondy źródłowe IPv4 i SNMP/SSH wymagają oddzielnie określonego zakresu — powyższa procedura ich nie uruchamia.
7. Dla LGPL: zgodna wymiana rzeczywistych modułów Paramiko/scp/autocommand, potwierdzenie miejsca i wersji importu przez runtime-check, przywrócenie oryginałów. Verify ma sygnalizować zmienione hashe, ale zwykły start nie blokuje świadomej modyfikacji.

Wyniki wpisz do [karty 5A](KARTA_ODBIORU_ETAP_5A.md), osobno dla obu OS. Receipt i dane prywatne pozostają poza repo. [Raport](RAPORT_ETAP_5A.md) oddziela wykonane próby macOS od niewykonanego Windows.
