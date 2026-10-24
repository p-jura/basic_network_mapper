# Etap 2 — uruchomienie i krótki odbiór

Data: 23 października 2026 r. Kod Etapu 2 jest zaimplementowany. Ten poradnik dotyczy rzeczywistych poleceń, nie wcześniejszego kontraktu planu.

## 1. Najpierw sprawdź demonstrację offline

Na Macu otwórz Terminal i przejdź do głównego katalogu:

```sh
cd "/Users/paweljuroszek/all_projects/other/Maper sieci"
./.venv/bin/mapper doctor
./.venv/bin/mapper demo
```

`doctor` pokazuje wersje, bez kontaktu z urządzeniami. `demo` tworzy nowy projekt z trzema syntetycznymi obserwacjami i wypisuje `project_id`, `cycle_id` oraz ścieżkę konfiguracji. Nie skanuje sieci i nie otwiera panelu. Ponowne wywołanie tworzy kolejny projekt.

Polecenie `mapper` zostało już zainstalowane w tutejszym venv. Przy przeniesieniu projektu trzeba zainstalować go ponownie w venv danej kopii. Gdy zależności są już dostępne:

```sh
./.venv/bin/python -m pip install --editable . --no-deps --no-build-isolation --no-index
```

To lokalna instalacja kodu bez pobierania pakietów. `--no-deps` nie instaluje brakujących bibliotek; ich listę zawiera `pyproject.toml`. Nie kopiuj venv między komputerami i systemami.

## 2. Sprawdź zapis, eksport i ponowny odczyt

W poniższych przykładach zastąp `TUTAJ_UUID` wartością `project_id` z demonstracji. Nie wpisuj dosłownie tego tekstu.

```sh
./.venv/bin/mapper snapshot list --project TUTAJ_UUID
./.venv/bin/mapper snapshot export --project TUTAJ_UUID --output "$HOME/Downloads/mapper-demo.json"
./.venv/bin/mapper snapshot import --new-project --input "$HOME/Downloads/mapper-demo.json"
```

Eksport nie nadpisuje istniejącego pliku; wybierz inną nazwę albo samodzielnie usuń wyłącznie własny poprzedni eksport. Import zwraca inny UUID projektu i zachowuje pochodzenie `imported` oraz oryginalne czasy obserwacji.

Zamknij Terminal, otwórz go ponownie, wróć do katalogu projektu i wykonaj `snapshot list` dla UUID projektu z importu. Wynik ma być dostępny bez skanowania, również bez Internetu.

Domyślne dane na Macu: `~/Library/Application Support/MapperSieci/projects/`. Każdy projekt ma osobny `project.json` i `mapper.sqlite3`. Możesz wskazać inny katalog przez `--data-dir /pełna/ścieżka`; stosuj go konsekwentnie w kolejnych poleceniach.

Przykład syntetycznego eksportu jest także w [stage2-demo.json](../../examples/snapshots/stage2-demo.json). Możesz zaimportować ten plik zamiast tworzyć nową demonstrację.

## 3. Podstawowy projekt dla lokalnego LAN

Poniższe polecenia tworzą konfigurację i odczytują informacje lokalne; nie wysyłają sond:

```sh
./.venv/bin/mapper project create --name "Mój LAN"
./.venv/bin/mapper interfaces
```

Zachowaj UUID i ścieżkę `config` z pierwszego polecenia. W odpowiadającym mu `project.json` zmień tylko pole `basic`. Przykład — użyj rzeczywistej nazwy interfejsu i jego lokalnej podsieci, nie kopiuj adresacji w ciemno:

```json
{
  "basic": {
    "interface": "en0",
    "cidr": "192.168.1.0/24"
  }
}
```

To fragment istniejącej konfiguracji, nie cały plik do zastąpienia. Pozostaw `project_id`, wersję schematu i pozostałe pola. Do podstawowego odkrywania `seeds` pozostaje pustą listą, a `profiles` pustym obiektem. Limit początkowy wynosi 256 celów; większy zakres wymaga jawnej zmiany budżetu lub wybrania mniejszego podzakresu.

Sprawdź plan bez sondowania:

```sh
./.venv/bin/mapper collect --project TUTAJ_UUID --preview
```

Oczekuj poprawnego interfejsu, źródłowego IPv4, CIDR, liczby celów i limitów. `route_compatible` pokazuje liczbę celów, do których trasa jest zgodna z wybranym lokalnym interfejsem. Przy VPN lub niespójnej trasie nie uruchamiaj skanu bez wyjaśnienia zakresu.

Aktywne zbieranie wykonuje dopiero jawne wywołanie operatora:

```sh
./.venv/bin/mapper collect --project TUTAJ_UUID --run
```

Wykonuj je wyłącznie w swoim dopuszczonym LAN, po sprawdzeniu podglądu. Pierwszy autoryzowany odbiór rzeczywistego LAN został wykonany przez Codex i opisany w [raporcie odbioru](../etap-2/ODBIOR_2026-10-23.md). `Ctrl+C` anuluje zbieranie; częściowy wynik ma jawny status. Potem użyj `snapshot list` i `snapshot export` jak w punkcie 2.

## 4. Co oznacza wynik Etapu 2

To warstwa danych i CLI. Snapshot zawiera obserwacje, źródła, zakres, czasy i status każdego odczytu. Nie jest jeszcze gotową topologią fizyczną ani listą zdarzeń historii.

- `execution_status=finished` oznacza zakończenie wykonania; pokrycie sprawdzaj osobno.
- `coverage_status=complete` odnosi się do zaplanowanych źródeł/zakresu, nie gwarantuje poznania wszystkich hostów.
- Brak odpowiedzi ICMP to `no_reply`; nie oznacza usunięcia urządzenia.
- Wpisy ARP/FDB/cache zachowują swoją świeżość, bez automatycznego przesunięcia czasu rzeczywistej obecności.
- Nieznane porty/VLAN-y nie są zgadywane. Reguły przypisania i confidence powstaną w Etapie 3.

Dotychczasowy panel `prototypes/tools/probe_panel.py` pozostaje demonstracją starszego snapshotu grafu. Nie otwieraj nowego formatu danych Etapu 2 bezpośrednio w tym skrypcie — integracja pełnego panelu należy do Etapu 4.

## 5. Opcjonalne SNMP/SSH

Zwykły domowy LAN nie potrzebuje tych profili. Jeśli masz urządzenie zarządzalne, dodaj odpowiedni profil i seed do istniejącego `project.json`. Przykład struktury bez sekretów:

```json
{
  "profiles": {
    "switch-v3": {
      "type": "snmp3",
      "user_env": "MAPPER_SNMP3_USER",
      "auth_key_env": "MAPPER_SNMP3_AUTH_KEY",
      "priv_key_env": "MAPPER_SNMP3_PRIV_KEY",
      "auth_protocol": "sha256"
    }
  },
  "seeds": [
    {
      "ip": "192.0.2.10",
      "port": 161,
      "profile_id": "switch-v3",
      "context": ""
    }
  ]
}
```

Adres `192.0.2.10` jest dokumentacyjny. Wpisz rzeczywisty, dozwolony cel. Sekrety dostarcz do ENV poza kodem i historią terminala, zgodnie z dotychczasowym sposobem z Etapu 1; nie wpisuj ich do JSON ani argumentów. CLI nie zgaduje poświadczeń i nie przechodzi samoczynnie z v3 na v2c.

Profil v2c używa `type=snmp2` i `community_env`. Profil SSH używa `type=ssh`, `user_env`, zweryfikowanego pliku `known_hosts` oraz opcjonalnie `password_env`; bez hasła korzysta z klucza/agenta. Pierwsza platforma SSH: `cisco_ios`, bez obsługi dowolnej rodziny urządzeń i bez automatycznego wejścia w kontekst VRF przez CLI.

Rekurencja jest domyślnie wyłączona. Wymaga `recursive=true`, `recursive_profile_id` oraz jawnego `allowed_ranges`. Nowe cele pochodzą z LLDP, a nie z logowania do każdego hosta znalezionego w ARP. Przed `--run` sprawdź `--preview`.

## 6. Krótka kontrola i następny etap

Minimalny odbiór operatora:

1. Demonstracja → eksport → import → ponowny odczyt po restarcie.
2. Dwa projekty mają inne UUID i oddzielne bazy.
3. Podgląd rzeczywistego LAN pokazuje poprawny zakres, bez żądania community.
4. Osobno dopuszczony skan LAN i, jeśli dostępne, próby SNMPv2c/v3 oraz SSH.
5. Windows ma osobny rzeczywisty wynik; uruchomienie testów parsera Windows na Macu go nie zastępuje.

Testy krytyczne, bez sieci:

```sh
./.venv/bin/python -m unittest discover -s tests/critical -v
```

Na Windows użyj odpowiednio `.\.venv\Scripts\python.exe -m mapper ...` oraz `.\.venv\Scripts\python.exe -m unittest discover -s tests/critical -v`, po instalacji pakietu w tamtejszym venv. Nie deklarujemy jeszcze wykonania tego odbioru na Windows.

Wyniki i ograniczenia opisuje [raport Etapu 2](../etap-2/RAPORT_ETAP_2.md). Po ocenie tego wyniku i jego zatwierdzeniu zaczynamy Etap 3: korelację ARP/FDB/VLAN, uplinki, confidence i historię zmian. Nie rozpoczynamy go automatycznie po uruchomieniu demonstracji.
