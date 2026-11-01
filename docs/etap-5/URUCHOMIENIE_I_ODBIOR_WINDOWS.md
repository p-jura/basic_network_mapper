# Etap 5 — instalacja i odbiór na Windows

Kandydat **0.5.0rc1**, wyłącznie lokalny odbiór. [Raport](RAPORT_ETAP_5.md), [karta](KARTA_ODBIORU_ETAP_5.md). Operator potwierdził dostęp do Windows 10 lub 11. Kod nie wykonał jeszcze próby na tym stanowisku. To nie jest instrukcja skanowania LAN.

## 1. Przygotuj pliki

Przenieś na Windows [ZIP x64](../../dist/etap-5-2026-10-25/mapper-sieci-0.5.0rc1-windows-x64.zip) i plik .sha256 z tego samego katalogu. W PowerShell porównaj:

```powershell
Get-FileHash .\mapper-sieci-0.5.0rc1-windows-x64.zip -Algorithm SHA256
```

Oczekiwana suma: `ea7a6e647ec40d8b33dbf8ffa03c677e3972e7ac32126eb789f8ae4428d577c9`. Python **3.13 x64** musi być wcześniej zainstalowany. Nie wyłączaj globalnie SmartScreen/antywirusa ani polityki PowerShell. Skrypty nie wymagają administratora ani Activate.ps1. Na karcie odbioru zapisz dokładny numer Windows (`winver`), Python, system plików i przeglądarkę. Windows 10 musi odpowiadać D01 (22H2 x64); test jednego OS nie zalicza drugiego.

Rozpakuj ZIP do nowego lokalnego folderu z prawem zapisu, np. `%USERPROFILE%\Mapper odbior żółć\`. Nie kopiuj .venv z Maca i nie instaluj na wcześniejszym środowisku. W cmd przejdź do rozpakowanego folderu:

```bat
install.cmd
start.cmd --offline --port 8051
```

Oczekiwania: weryfikacja plików, instalacja 51 kół bez Internetu, pip check OK, własna strona na 127.0.0.1:8051. Instalator odmawia przy złym Pythonie/platformie albo istniejącym venv. Przy błędzie zachowaj katalog do diagnozy, do następnej próby rozpakuj nową kopię.

## 2. Zapisz receipt bez sond

W cmd tego samego folderu, z **nowym** katalogiem testowych danych:

```bat
.venv\Scripts\python.exe -I bundle.py maintenance receipt --data-dir "%USERPROFILE%\Mapper odbior\odbior-01"
```

Powstanie `installation-receipt.json`. Sprawdź mapper i installed_mapper=0.5.0rc1, module_file w .venv/Lib/site-packages, integrity=ok, foreign_key_errors=0, trzy węzły i dwa linki logiczne demo oraz pięć eksportów. Receipt zawiera lokalne ścieżki; przekaż go prywatnie lub usuń nazwę konta przed wklejeniem. Nie publikuj ENV, prawdziwej sieci ani danych klienta.

## 3. Krótki odbiór panelu

1. „Demo offline” → „Wczytaj mapę”; kliknij hosta i sprawdź IP/MAC, źródła, nieustalony port/VLAN. Zmień projekt, filtr tekstu i VLAN.
2. Zaimportuj do nowego projektu dołączony `examples/stage3-managed.json`. Sprawdź syntetyczny host na Gi101/VLAN10 oraz kandydata uplink Gi900. To fixture, nie dowód działania switcha.
3. Zapisz JSON/CSV; pobierz PNG/SVG i otwórz oba. Porównaj etykiety. Eksporty danych obejmują cały wybrany snapshot, obrazy aktualny widok.
4. Przy działającej instancji uruchom drugie `start.cmd --offline --port 8051`. Ma odmówić z PANEL_PORT_UNAVAILABLE, nie zatrzymywać pierwszej. Zakończ pierwszą Ctrl+C i sprawdź nowy port 8052.
5. Gdy stanowisko ma być fizycznie bez Internetu, przygotuj to ręcznie w bezpieczny sposób i wyłącz cache przeglądarki; powtórz start/odświeżenie/eksporty. Sam --offline nie dowodzi fizycznego odłączenia. Nie zmieniaj routingu/firewalla do obejścia problemów.

## 4. Rzeczy, których receipt nie zalicza

NTFS: z drugiego zwykłego konta sprawdź odmowę dostępu do config, SQLite, backupu i serwerowych eksportów; konto właściciela nadal ma działać. Nie osłabiaj ACL. Nie zakładaj, że pobrane przez przeglądarkę kopie w Downloads mają ochronę mappera.

Źródło/interfejs Windows oraz SNMP/SSH wymagają **osobnego polecenia z zakresem i limitami**. Nie klikaj aktywnego startu na podstawie tej instrukcji odbioru offline. Modele, wersje i znane połączenia sprzętu zapisuje się prywatnie przed odpowiednią próbą. Wynik instalacji Windows nie zamyka tych wierszy karty.

Po wykonaniu podaj: dokładny OS/Python/przeglądarkę, receipt, wynik panelu/eksportów/portów oraz ewentualny komunikat błędu. Każdą niewykonaną próbę pozostaw niewykonaną.
