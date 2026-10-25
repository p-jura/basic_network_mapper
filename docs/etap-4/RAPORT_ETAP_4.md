# Raport Etapu 4 — panel operatora 0.4.0

Data: **25 października 2026 r.** Status: **kod wdrożony, odbiór techniczny offline wykonany; wynik do zatwierdzenia użytkownika**. Autoryzacja: „masz zgode na dzialanie. Wdrazaj”. Podstawa: [plan](../poradniki/ETAP_4_PANEL_I_PRZEPLYW_OPERATORA.md) i [ADR-006](../decisions/ADR-006-panel-i-kontroler.md). Nie rozpoczęto Etapu 5, nie wykonano nowych sond do LAN ani commita/pushu.

## Wdrożony zakres

| Obszar | Rezultat |
|---|---|
| Start | mapper panel, port/no-browser/offline/data-dir, loopback, gotowość przed otwarciem URL, bez zabijania innych procesów |
| Projekty | Lista z nazwą/UUID, tworzenie, demo, import v1 do nowego projektu; prywatne ograniczone pliki tymczasowe |
| Konfiguracja | Interfejs/źródło/maska/CIDR, brama lub nieustalona w podglądzie, limity; opcjonalne seedy/profile ENV i jawne zakresy; prywatny atomowy zapis pod lockiem |
| Kontroler | Osobny pracownik kolekcji/build i jeden ograniczony pracownik offline; własne SQLite, brak kolejki kolejnych skanów, zgodne locki 3.1 |
| Kolekcja | Aktualny podgląd 120 s do jednego startu, ponowna walidacja planu/źródła także w run_cycle, postęp, anulowanie i częściowe wyniki |
| Odświeżanie | Opt-in, domyślnie 15 min po zakończeniu zadania; bez restartu serii po uruchomieniu aplikacji; zmiana planu/źródła, błąd, partial lub cancel rozbrajają |
| Mapa | Wyszukiwanie IP/MAC/nazwa, VLAN/unknown, kontekst infrastruktury, legenda, klikane węzły/krawędzie, szczegóły i zwijane dowody; w dużym grafie start od infrastruktury |
| Historia | Do 100 ostatnich zdarzeń projektu i ostrzeżenia; wybór historycznego snapshotu; brak fałszywej etykiety odłączenia |
| Eksport | Pełna topologia JSON i osobne CSV węzłów/relacji, źródła v1 JSON/CSV, PNG/SVG widocznego kadru; prywatny oryginał i osobna kopia przeglądarki |
| Lokalna ochrona | Host/Origin i podpisana sesja z losowym tokenem, brak CORS/debug/reloader; tekst zamiast HTML, brak sekretów w UI, ochrona CSV i prywatnego zapisu |

Nie zmieniono reguł topologii/historii, SQLite v2 ani formatu snapshotów v1. Doszły jedynie referencje UI/projekcje eksportowe i agregowany hook postępu. Nieużywany profil ENV nie blokuje podstawowego cyklu. Budżet projektu uwzględnia też podkatalog eksportów. Źródłowy CSV ponownie weryfikuje znane sekrety przed utworzeniem pliku, tak jak JSON.

Zachowano zgodność CLI i starego topology view. Nie dodano bibliotek ani CI/CD. Stare prototypy nadal dokumentują próbę Etapu 1, więc ich nie usunięto ani nie przenoszono tylko ze względu na wiek. Brak nowych zależności od old/ lub prototypes/.

## Sprawdzenia

- 49 testów krytycznych: 38 wcześniejszych + 11 grup Etapu 4. Komenda: `PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m unittest discover -s tests/critical -v`. Przechodzą testy offline, scopes/źródła, single-use preview, blokad, anulowania, serii na sztucznym zegarze, izolacji, eksportów, ochrony HTTP/sekretów oraz gotowości launchera. To mały zestaw kontraktów, nie testy każdego widgetu.
- Dodatkowy odbiór rzeczywistych payloadów callbacków Dash przez lokalny Flask test_client: preview → start → poll → graf 4 węzłów, wyłącznie FakeAdapter. Zero sond do rzeczywistego LAN.
- W przeglądarce otwarto syntetyczny managed snapshot: 3 węzły/3 relacje; filtr VLAN10 + tekst hosta: 3 węzły/2 relacje. Kliknięcie pokazało IP/MAC i Gi101/VLAN10/high oraz alternatywę uplink Gi900, bez promowania jej do bezpośredniego przypisania.
- PNG pobrano i obejrzano; SVG pobrano oraz sprawdzono poprawny XML i komplet oczekiwanych etykiet. Układ kołowy otrzymał jawny promień i aktualizację zależną od gotowych elementów grafu, po wykryciu wyścigu równoległych callbacków podczas wczytywania/filtrowania. Dostosowano kontrast do komponentów lokalnego Dash 4.
- Wymagane skrypty/CSS w DOM wskazują wyłącznie 127.0.0.1, w tym lokalny bundle SVG. Tryb offline blokuje kolektory po stronie kontrolera. **Nie odłączano fizycznie Internetu ani nie wykonano osobnego odbioru z wyłączonym cache.**
- Gotowość i URL 8051 potwierdza test launchera z atrapą bind/serwera i webbrowser; lokalną drugą instancję sprawdzono na rzeczywiście zajętym 8054: PANEL_PORT_UNAVAILABLE, bez otwierania cudzej instancji i bez jej zatrzymania. Ctrl+C zakończyło własny serwer testowy.
- Zbudowano tymczasowy wheel własnego pakietu bez pobierania zależności; sprawdzenie lokalnych assets nie zastępuje pełnej oceny instalatora/licencji w Etapie 5. Instalacja editable 0.4.0 odbyła się z --no-deps --no-build-isolation --no-index.

[Zbiorcze dowody JSON](ODBIOR_2026-10-25.json). Ręczne uruchomienie: [poradnik](../poradniki/ETAP_4_URUCHOMIENIE_I_ODBIOR.md). [Syntetyczny panel](PANEL_ETAP_4.png).

## Próba D14

Generator [examples/generate_scale_snapshot.py](../../examples/generate_scale_snapshot.py) tworzy bez sieci 50 switchy, 1000 hostów, 20 VLAN-ów i 49 potwierdzonych syntetycznie relacji LLDP, łącznie 50 tys. obserwacji. Wypełnienie obejmuje duży inwentarz interfejsów; nie jest uniwersalnym benchmarkiem wszystkich rodzajów tabel i producentów.

| Pomiar macOS ARM | Wynik | Cel/ograniczenie |
|---|---|---|
| Import + korelacja | 6.119 s | ≤30 s, zaliczone dla tego zestawu |
| Projekcja infrastruktury w Pythonie | 0.0016 s | 50/1050 węzłów, 49/1049 relacji |
| Kliknięcie „Wczytaj mapę” → widoczny licznik w przeglądarce | 2,165 s | ≤5 s, równoważny zestaw 50/1050/49; pomiar obejmuje opóźnienie narzędzia automatyzacji, nie jest precyzyjnym pomiarem samego renderera |
| Szczyt RSS procesu generator/import/build | 629653504 B, około 600.5 MiB | resource.getrusage na macOS; obejmuje generowanie i import, nie sam proces serwera |
| Łączny RAM aplikacja + karta | Niewykonany | Nie potwierdzamy celu ≤1,5 GB na podstawie samego RSS Pythona |

Wyniki dotyczą syntetycznego przykładu, nie wydajności sond na sprzęcie ani porównania Windows/macOS. Plik 50 tys. obserwacji pozostał poza repozytorium; w repo jest generator i zbiorczy raport.

## Granice przekazania

- Windows/NTFS i natywne IPv4/DACL nadal wymagają rzeczywistego odbioru. Tak samo SNMPv2c/v3/SSH na sprzęcie, w tym deklaracje obsługi producenta.
- Brak zweryfikowanej bazy OUI oznacza „nieustalony”. Panel nie dodaje zewnętrznego lookupu, nowych platform SSH ani Linuksa.
- Historia panelu jest ograniczona do 100 ostatnich zdarzeń; CLI zachowuje własny limit. Jeden kontroler pokazuje po jednym aktywnym zadaniu kolekcji i offline; cache maksymalnie czterech widoków, starszy wymaga ponownego wczytania. Zajęty projekt może odmówić odczytu źródeł, ale wczytana mapa nadal działa.
- Zamknięcie karty nie zatrzymuje procesu. Anulowanie i Ctrl+C czekają na ograniczone timeoutami operacje, zwłaszcza SSH. Częściowy wynik rozbraja powtarzanie.
- Powtarzane eksporty są nowe i prywatne; pobrana kopia ma prawa przeglądarki, bez gwarancji ACL mappera. Nie zmieniono katalogu Downloads ani uprawnień innych plików użytkownika.
- Fizyczny test bez Internetu/cache i łączny RAM karty pozostają do odbioru. Nie deklarujemy kompletnego MVP ani gotowego instalatora. Etap 5 i jego próby wymagają odrębnego zatwierdzenia zakresu; aktywny odbiór wymaga wskazanej sieci i jawnej akcji operatora.

Zmiany pozostawiono do przeglądu i commita użytkownika. Dokumenty planowania Etapu 4 zastane na początku zachowano i uzupełniono; prywatnych istniejących projektów nie modyfikowano.

Końcowy odbiór zainstalowanej aplikacji odbył się na 8051, w układzie wąskim i desktopowym 1440×1000. Zapisano syntetyczny screenshot ze szczegółami hosta, przywrócono rozmiar przeglądarki, zamknięto tymczasową kartę i własny serwer. Pole interwału pokazuje wartość i jednostkę, a przypisanie portu jest oddzielone od kandydata uplink.

Końcowe sprawdzenie: 49/49 testów w 1,830 s w głównym projekcie; pip check bez problemów; git diff --check bez błędów; AST poprawne, 293 lokalne odnośniki Markdown bez brakujących celów. Wheel 0.4.0 zawiera aktualne app/controller/panel i CSS, porównane bajtowo z kodem. Roboczy build przeniesiono do old/2026-10-25/build/ bez usuwania, zgodnie z rejestrem docs/OLD.md; pozostaje lokalnym artefaktem ignorowanym przez Git.
