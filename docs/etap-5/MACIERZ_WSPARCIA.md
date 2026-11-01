# Macierz kandydata 0.5.0rc1

Stan: 25 października 2026 r. [Raport](RAPORT_ETAP_5.md). Obecność kodu albo ZIP nie oznacza zaliczonego odbioru.

| Obszar | Stan | Dowód / ograniczenie |
|---|---|---|
| macOS 26.6.2 ARM64, Python 3.13.0 | Instalacja offline i panel odebrane technicznie | 51 lokalnych kół, import z nowego venv, 58 testów, demo/import/eksporty |
| Windows 11 x64/NTFS | Paczka przygotowana, wykonanie niewykonane | Operator ma Windows 10 lub 11; dokładny OS do zapisania |
| Windows 10 22H2 x64/NTFS | Paczka przygotowana, wykonanie niewykonane | Wymaga osobnego rzeczywistego potwierdzenia |
| Windows native IPv4/DACL/locki | Kod i wcześniejsze atrapy | Brak rzeczywistego receipt źródła/interfejsu i drugiego konta |
| Offline replay L2/L3 | Odebrany na syntetycznych i zachowanych danych | Reguły 2; port/VLAN tylko z dowodów; brak sond |
| Fizyczny LAN kandydata | Niewykonany | Poprzedni odbiór 0.4.0 i replay 0.4.1 są historycznymi dowodami |
| SNMPv2c/v3 SHA256/AES128 | Adapter i testy offline | Brak odbioru na rzeczywistym sprzęcie |
| SSH cisco_ios / sześć odczytów | Adapter/parsery i testy offline | Brak konkretnego modelu/wersji odebranych na sprzęcie |
| VRF/LAG/stack/MLAG | Konserwatywny model/ostrzeżenia | Brak pełnego odbioru na tych konfiguracjach |
| OUI | Nieustalony | Nie dołączono nowej bazy ani API |
| D14 import / widok infrastruktury | Cele czasu zaliczone na macOS | 5,773 s / 1,549 s z narzutem automatyzacji |
| RAM aplikacja+karta | Niewykonany | RSS samego Pythona nie zalicza 1,5 GB |
| Fizyczny brak Internetu/cache | Niewykonany | Instalator no-index i lokalne zasoby są osobnymi dowodami |
| Pełna gotowość dystrybucji | Otwarta | Weryfikacja natywnych/JS materiałów i pozostałych odbiorów |

Linux i Windows ARM nie zostały dodane do zakresu. Nie deklarujemy wykrycia każdego urządzenia ani uniwersalnej zgodności każdego producenta.
