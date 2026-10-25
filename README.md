# Maper sieci

**Pawel Juroszek · FL Development** — rozwój i utrzymanie projektu. Własne elementy projektu udostępniono na [licencji MIT](LICENSE); komponenty zewnętrzne zachowują odrębne warunki.

Lokalna aplikacja Python do odkrywania różnych sieci IPv4 i tworzenia map L2/podstawowych L3. Działa bez znajomości marki routera: podstawowy tryb korzysta z interfejsów, tras, sąsiadów/ARP i ograniczonych sond. Opcjonalne SNMPv2c/v3 lub SSH dostarcza ARP/FDB/VLAN/LLDP do mapowania portów.

Mapa odróżnia przynależność logiczną od przypisania do portu. Brak dostępu do switcha oznacza jawnie nieustalony port/VLAN. Odkrywanie rozpoczyna operator dla wskazanego zakresu; start podglądu nie uruchamia sond.

## Stan

Wersja **0.4.0**. Wdrożono panel operatora: projekty, konfiguracja/preview, start/postęp/anulowanie, opcjonalne odświeżanie, mapa z filtrami i szczegółami, historia oraz eksporty JSON/CSV/PNG/SVG. Przeszło 49 testów krytycznych i odbiór syntetyczny na macOS ARM. Wynik techniczny Etapu 4 czeka na zatwierdzenie użytkownika. Rzeczywiste SNMP/SSH i Windows/NTFS pozostają nieodebrane; łączny RAM aplikacja+karta wymaga pomiaru.

Jedna aplikacja: Python 3.13, SQLite, NetworkX, psutil, PySNMP, Netmiko/ntc-templates i Dash/dash-cytoscape. Darmowe komponenty open source, bez chmury, triali i licencyjnych limitów urządzeń. Odczyty urządzeń są wyłącznie do odczytu; projekty i poświadczenia pozostają odseparowane. Bez rozbudowanego CI/CD.

## Poprawki po review — 3.1

Wersja 0.3.1 współdzieli krótkotrwały stan tras, rozdziela blokady kolekcji i projektów oraz tworzy prywatne pliki od początku zapisu. Na macOS ping jest powiązany ze źródłem i interfejsem; dla Windows dodano systemowy adapter IPv4 i ochronę DACL. Kod Windows sprawdzono na atrapach — rzeczywiste sondy i efektywne uprawnienia NTFS nadal wymagają odbioru na Windows.

[Szczegółowy plan i instrukcja](docs/poradniki/ETAP_3_1_POPRAWKI_PO_REVIEW.md) · [raport 3.1](docs/etap-3-1/RAPORT_ETAP_3_1.md).

## Uruchomienie

Z katalogu repozytorium, w przygotowanym środowisku z lokalnymi zależnościami `preview`:

```sh
./.venv/bin/mapper doctor
./.venv/bin/mapper panel --offline
```

Panel otwiera przeglądarkę po gotowości serwera. Wybierz projekt albo „Demo offline”, następnie „Wczytaj mapę”. Tryb offline blokuje kolektory. Interfejs i eksporty korzystają z lokalnych zasobów.

Do samodzielnego odkrywania autoryzowanej sieci uruchom `./.venv/bin/mapper panel`, wybierz projekt/interfejs/zakres i sprawdź podgląd przed przyciskiem startu. Samo uruchomienie nie wysyła sond. Zmienisz port przez `--port 8051`; `--no-browser` pomija otwarcie przeglądarki. Dotychczasowe CLI i `topology view` nadal działają.

[Instrukcja uruchomienia i odbioru panelu](docs/poradniki/ETAP_4_URUCHOMIENIE_I_ODBIOR.md) · [raport Etapu 4](docs/etap-4/RAPORT_ETAP_4.md).

## Dokumentacja

- [Spis dokumentacji](docs/README.md).
- [Wymagania](docs/WYMAGANIA_PROJEKTU.md) i [plan wdrożenia](docs/PLAN_STARTOWY.md).
- [Uruchomienie i odbiór Etapu 3](docs/poradniki/ETAP_3_URUCHOMIENIE_I_ODBIOR.md) oraz [raport](docs/etap-3/RAPORT_ETAP_3.md).
- [Etap 4 — zatwierdzony plan panelu](docs/poradniki/ETAP_4_PANEL_I_PRZEPLYW_OPERATORA.md).
- [Licencje i informacje o komponentach](docs/THIRD_PARTY_NOTICES.md).
- [Licencja MIT własnych elementów projektu](LICENSE) oraz [objaśnienie stanu prawnego i warunków dystrybucji](docs/licencje/STAN_PRAWNY_I_DYSTRYBUCJA.md). Licencje bibliotek i zasobów zewnętrznych obowiązują odrębnie.

Kod znajduje się w `src/mapper/`, krytyczne testy w `tests/critical/`, przykłady w `examples/snapshots/`, a prototypy komponentów z Etapu 1 w `prototypes/`. Cała dokumentacja projektowa jest w `docs/`; instrukcje pracy z repozytorium pozostają w [AGENTS.md](AGENTS.md). Wcześniejsze materiały Flutter/Dart i laboratorium zachowano w `docs/archiwum/`.
