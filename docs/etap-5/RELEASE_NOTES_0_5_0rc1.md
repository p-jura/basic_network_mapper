# Mapper 0.5.0rc1 — informacje o kandydacie

25 października 2026 r. Wewnętrzny kandydat do odbioru, bez publikacji. [Raport](RAPORT_ETAP_5.md) i [macierz](MACIERZ_WSPARCIA.md).

- Dodano dwa ZIP jednej aplikacji z lokalnymi kołami, pinami/hashami i materiałami źródłowymi.
- Instalator sprawdza pliki, platformę i Python 3.13, tworzy nowe venv i odmawia nadpisania istniejącego. Start nie pobiera bibliotek.
- Dodano skrypty startu, receipt offline i spójny backup config/SQLite. Backup nie obejmuje wcześniejszych obrazów/eksportów — zachowaj je osobno.
- Zawartość obejmuje poprawki LAN 0.4.1: brak endpointów z grupowych/zerowych MAC i lokalnego duplikatu, poprawne maski interfejsów, odtwarzanie formularza. Reguły 2 zachowują stare wyniki i odtwarzają zachowane źródła w osobnej historii wersji.
- Nie zmieniono wersji bibliotek runtime. Dash-cytoscape 1.0.2 zbudowano z potwierdzonego źródła tej samej wersji; nie dodano własnego SNMP, CI/CD ani aktualizacji automatycznej.

macOS: instalacja i panel odebrane technicznie, 58 testów, D14 czas zaliczony. Windows: ZIP przygotowany, odbiór rzeczywisty niewykonany. Otwarte: NTFS/źródło IPv4, sprzęt SNMP/SSH i topologia, fizycznie bez Internetu/cache, łączny RAM, pełna weryfikacja materiałów komponentów. Nie deklarujemy pełnego MVP ani gotowości do przekazywania klientom. OUI pozostaje nieustalony, gdy brak danych; porty/VLAN wyłącznie z dowodów.
