# Maper sieci

**Pawel Juroszek · FL Development** — rozwój i utrzymanie projektu. Własne elementy projektu udostępniono na [licencji MIT](LICENSE); komponenty zewnętrzne zachowują odrębne warunki.

Lokalna aplikacja Python do odkrywania różnych sieci IPv4 i tworzenia map L2/podstawowych L3. Działa bez znajomości marki routera: podstawowy tryb korzysta z interfejsów, tras, sąsiadów/ARP i ograniczonych sond. Opcjonalne SNMPv2c/v3 lub SSH dostarcza ARP/FDB/VLAN/LLDP do mapowania portów.

Mapa odróżnia przynależność logiczną od przypisania do portu. Brak dostępu do switcha oznacza jawnie nieustalony port/VLAN. Odkrywanie rozpoczyna operator dla wskazanego zakresu; start podglądu nie uruchamia sond.

## Stan

Wersja **0.3.0**. Etap 2 zatwierdzony; implementacja i odbiór techniczny Etapu 3 są gotowe i oczekują na zatwierdzenie wyniku. Działają kolektory, snapshoty, topologia offline, confidence, historia i prosty podgląd. Przeszło 26 testów krytycznych oraz odbiór zapisanych danych LAN na macOS ARM. Rzeczywiste SNMP/SSH, Windows i duża skala wymagają osobnych prób. Pełny panel pozostaje Etapem 4.

Jedna aplikacja: Python 3.13, SQLite, NetworkX, psutil, PySNMP, Netmiko/ntc-templates i Dash/dash-cytoscape. Darmowe komponenty open source, bez chmury, triali i licencyjnych limitów urządzeń. Odczyty urządzeń są wyłącznie do odczytu; projekty i poświadczenia pozostają odseparowane. Bez rozbudowanego CI/CD.

## Uruchomienie

Z katalogu repozytorium, w przygotowanym środowisku:

```sh
./.venv/bin/mapper doctor
./.venv/bin/mapper demo
```

Oba polecenia działają bez sondowania. `demo` tworzy projekt syntetyczny i zwraca jego `project_id`. Zastąp nim `UUID_PROJEKTU`:

```sh
./.venv/bin/mapper topology build --project UUID_PROJEKTU
./.venv/bin/mapper topology view --project UUID_PROJEKTU --port 8051
```

Podgląd wymaga Dash/dash-cytoscape (zestaw `preview`) i używa wyłącznie zapisanych danych. Szczegóły instalacji oraz odbioru są w poradnikach.

## Dokumentacja

- [Spis dokumentacji](docs/README.md).
- [Wymagania](docs/WYMAGANIA_PROJEKTU.md) i [plan wdrożenia](docs/PLAN_STARTOWY.md).
- [Uruchomienie i odbiór Etapu 3](docs/poradniki/ETAP_3_URUCHOMIENIE_I_ODBIOR.md) oraz [raport](docs/etap-3/RAPORT_ETAP_3.md).
- [Licencje i informacje o komponentach](docs/THIRD_PARTY_NOTICES.md).
- [Licencja MIT własnych elementów projektu](LICENSE) oraz [objaśnienie stanu prawnego i warunków dystrybucji](docs/licencje/STAN_PRAWNY_I_DYSTRYBUCJA.md). Licencje bibliotek i zasobów zewnętrznych obowiązują odrębnie.

Kod znajduje się w `src/mapper/`, krytyczne testy w `tests/critical/`, przykłady w `examples/snapshots/`, a prototypy komponentów z Etapu 1 w `prototypes/`. Cała dokumentacja projektowa jest w `docs/`; instrukcje pracy z repozytorium pozostają w [AGENTS.md](AGENTS.md). Wcześniejsze materiały Flutter/Dart i laboratorium zachowano w `docs/archiwum/`.
