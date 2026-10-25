# Etap 4 — uruchomienie i odbiór panelu 0.4.0

Data: 25 października 2026 r. [Plan](ETAP_4_PANEL_I_PRZEPLYW_OPERATORA.md), [raport techniczny](../etap-4/RAPORT_ETAP_4.md). Polecenia wykonuj z głównego katalogu repozytorium. Panel jest jedną lokalną aplikacją; serwer dostępny wyłącznie przez 127.0.0.1.

## 1. Uruchomienie bez sondowania

Na przygotowanym macOS:

```sh
./.venv/bin/mapper --version
./.venv/bin/mapper doctor
./.venv/bin/mapper panel --offline
```

Oczekiwana wersja: 0.4.0. Przeglądarka otwiera właściwy port po gotowości serwera; adres pozostaje w terminalu. Wybierz projekt lub „Demo offline”, a następnie „Wczytaj mapę”. Demo tworzy syntetyczne dane; import zawsze tworzy nowy projekt. Tryb offline blokuje kolektory także po ręcznym wywołaniu callbacku. Nie jest to tylko ukrycie przycisku.

Na przygotowanym Windows odpowiednikiem jest `.venv\Scripts\mapper.exe panel --offline`. **Nie potwierdzono jeszcze odbioru rzeczywistego Windows/NTFS.** Zależności Dash/dash-cytoscape muszą być wcześniej zainstalowane (`preview` w pyproject); obecny venv je zawiera. Nie instaluj zależności ponownie, jeśli doctor je wykazuje i pip check przechodzi.

Zmiana portu i pominięcie otwarcia przeglądarki:

```sh
./.venv/bin/mapper panel --offline --port 8051 --no-browser
```

Wtedy otwórz adres z terminala. Druga instancja na tym samym porcie zgłasza PANEL_PORT_UNAVAILABLE; nie zatrzymuje pierwszej. Nie mieszaj działających wersji 0.3.0 i 0.4.0 — stary proces nie zna wszystkich blokad projektów. Ctrl+C zamyka własny serwer, rozbraja serię i czeka na zakończenie ograniczonych operacji. Zamknięcie karty nie kończy procesu.

## 2. Projekty, mapa i historia

1. Lista pokazuje nazwę i skrót UUID. Takie same adresy w dwóch projektach pozostają oddzielnymi urządzeniami. Nie ma usuwania projektu w panelu.
2. Importuj plik źródłowego snapshotu JSON v1, nie JSON wyeksportowanej topologii. Limit 100 MiB i 200 tys. rekordów; błędny import nie uruchamia kolektorów. Plik tymczasowy jest prywatny i usuwany po operacji.
3. Wybierz „Najnowszy wynik” albo konkretny cykl i kliknij „Wczytaj mapę”. Nagłówek wskazuje czas, identyfikator i pochodzenie. Stary widok pozostaje przypięty podczas kolejnej kolekcji.
4. Wyszukiwanie IP/MAC/nazwa łączy się z filtrem VLAN, także kategorią „nieustalony”. „Wyczyść filtry” przywraca pełny mały graf; w dużym grafie hosty włączysz oddzielnie. Przerywane obramowanie oznacza dodatkowy kontekst filtra.
5. Kliknij węzeł lub krawędź. Szczegóły pokazują znane przypisania, kandydatów i pewność. Surowe dowody są w zwijanej sekcji. Brak producenta/OUI lub portu/VLAN ma wartość nieustaloną. Rysunek logiczny nie dowodzi fizycznego kabla.
6. Przesuwaj węzły i powiększaj mapę. „Dopasuj i ułóż” odtwarza układ kołowy. Aktualizacja samego postępu nie przebudowuje grafu. Filtry mogą uruchomić dopasowanie do widocznych elementów.
7. Historia pokazuje do 100 ostatnich zdarzeń wybranego projektu i ostrzeżenia grafu. Niezaobserwowany nie oznacza odłączony; pochodzenie danych pozostaje jawne. Historia to zapis projektu, a mapa może być przypięta do wcześniejszego snapshotu.

## 3. Eksporty

- PNG/SVG: bieżący widoczny kadr i filtry, z etykietami. Jeśli chcesz cały graf, najpierw wyczyść filtry i użyj dopasowania. Obrazy nie zawierają panelu szczegółów.
- Topologia JSON: pełny wybrany graf wraz z typami, dowodami i ograniczeniami, niezależnie od filtra.
- CSV urządzeń i CSV relacji: dwa osobne formaty pełnego grafu, łączone identyfikatorami; obiekty/listy jako JSON w komórce. Tekst mogący uruchomić formułę ma prefiks apostrofu. Oryginały pozostają w JSON.
- Źródłowy JSON/CSV: obserwacje, nie rysunek. Tylko źródłowy JSON v1 służy do importu/replay. Eksport źródeł zajętego projektu może zwrócić PROJECT_BUSY; eksport zapamiętanego grafu nie otwiera jego SQLite.

„Zapisz prywatny eksport” tworzy nowy plik w katalogu projektu `exports`, z ochroną 0600/0700 na POSIX lub chronioną DACL Windows. Brak ochrony przerywa zapis. „Pobierz kopię” zachowuje prywatny oryginał i dodatkowo przekazuje plik przeglądarce. Kopia z Downloads i obrazy mają uprawnienia przeglądarki/systemu; mapper nie gwarantuje dla nich DACL/0600. Pliki zawierają dane sieci. Eksporty liczą się do budżetu projektu; powtarzane eksportowanie tworzy nowe pliki bez nadpisywania i bez automatycznego usuwania starszych eksportów.

## 4. Odkrywanie — tylko w autoryzowanej sieci

Uruchom `./.venv/bin/mapper panel` bez flagi offline. Sam start nadal nie wysyła sond. Poniższe kroki wykonuje operator dla sieci, do której ma prawo dostępu; nie stanowią zgody na skanowanie tej sieci przez agenta w ramach odbioru kodu.

1. Utwórz/wybierz projekt. Kliknij „Odczytaj lokalne interfejsy”, wybierz właściwy LAN. Pokaże się IPv4 i maska; gdy pole zakresu jest puste, zostanie zaproponowany CIDR. Sprawdź też VPN i ewentualną niejednoznaczność kilku adresów tego samego interfejsu.
2. Wpisz zakres i limity. Zbyt duża podsieć jest odrzucana; aplikacja nie obcina listy celów. Domyślnie 256 celów, 5/s, 4 równolegle, jedna sonda na adres i 240 s części podstawowej. Zakres musi być zgodny z lokalnym interfejsem i trasami.
3. Kliknij „Pokaż zakres — bez sond”. Konfiguracja zapisze się prywatnie, a panel pokaże źródło, maskę, zakres, liczbę celów, tempo i deadline oraz opcjonalne seedy/ENV. Podgląd ważny 120 s, do jednego startu. Każda zmiana formularza unieważnia zgodę tego podglądu.
4. Dopiero „Odkryj wskazany zakres” uruchamia pracę. Start ponownie sprawdza konfigurację/źródło/trasy. Drugi start, karta, CLI lub inna instancja nie omijają jednej kolekcji i blokady projektu.
5. Postęp rozróżnia odpowiedzi, brak odpowiedzi, błąd, pominięcie i oczekujące cele. Liczniki urządzeń/tabel nie udają pełnego procentu rekurencji LLDP. Poprzednia mapa pozostaje oznaczona swoim czasem.
6. „Anuluj aktywny cykl” zatrzymuje nowe cele i oczekuje na ograniczone operacje. Nie zabija innych procesów; zapisuje częściowy wynik. Błąd kolektora nie dowodzi zniknięcia hostów. Jeśli budowanie grafu się nie uda, źródła i poprzednia mapa pozostają dostępne.

### Profile opcjonalne

W sekcji rozszerzonej edytujesz JSON seedów/profili/dozwolonych zakresów. Przykład bez wartości poświadczeń:

```json
{
  "profil_ro": {
    "type": "snmp3",
    "user_env": "MAPPER_LAB_USER",
    "auth_key_env": "MAPPER_LAB_AUTH",
    "priv_key_env": "MAPPER_LAB_PRIV"
  }
}
```

Przykładowe seedy: `[{"ip":"192.0.2.2","profile_id":"profil_ro","port":161}]`, zakresy: `["192.0.2.0/24"]`. To adresacja syntetyczna, nie gotowa konfiguracja Twojej sieci. Ustaw wymagane ENV przed uruchomieniem procesu. W panelu pojawiają się nazwy i stan dostępności zmiennych, bez wartości. Dla v2c stosuj type=snmp2 i community_env. SSH obsługuje istniejące cisco_ios oraz wcześniej zweryfikowany plik known_hosts; nie przyjmuje klucza dowolnego hosta.

Rekurencja wymaga jawnego profilu i zakresów; brak poświadczeń użytego profilu wymaga korekty konfiguracji. Nieużywany profil nie blokuje podstawowego cyklu. Rzeczywisty odbiór protokołów nadal jest otwarty; formularz ani test atrapy nie potwierdza obsługi konkretnego switcha.

### Powtarzanie D12

Domyślnie wyłączone. Zaznacz powtarzanie przed ręcznym startem i wybierz interwał (domyślnie 15 min, dopuszczalne 1–10080 min). Kolejny termin liczy się od zakończenia kolekcji i budowania mapy. Nie ma nakładania ani nadrabiania zaległych terminów. Restart aplikacji nie uzbraja serii ponownie.

Zmiana projektu, konfiguracji/źródła, błąd, częściowy wynik lub anulowanie rozbraja serię. Przed każdym cyklem źródło i konfiguracja są sprawdzane ponownie. „Zatrzymaj odświeżanie” wyłącza przyszłe starty; anulowanie aktywnego cyklu jest osobnym przyciskiem.

## 5. Krótki odbiór i stan prób

```sh
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m unittest discover -s tests/critical -v
./.venv/bin/python -m pip --no-cache-dir check
```

Wersja przekazana przeszła 49 testów. Sprawdź demo i syntetyczny managed snapshot, dwa projekty, szczegóły, filtry/unknown, eksporty i zajęty port. Odbiór integracji online wykonano na atrapach; nie wysyłano nowych sond do LAN.

Większy snapshot wygenerujesz bez sieci, w osobnym katalogu:

```sh
./.venv/bin/python examples/generate_scale_snapshot.py --data-dir /private/tmp/mapper-scale
```

Generator wypisze ścieżkę źródłowego JSON i UUID syntetycznego projektu. Na Windows wskaż własny tymczasowy katalog zamiast /private/tmp. Nie zapisuj 50 tys. obserwacji do repozytorium. Zestaw ma 50 switchy, 1000 hostów, 20 VLAN-ów i 49 LLDP; 50 tys. obserwacji obejmuje także rozbudowany inwentarz interfejsów. To próba obciążenia, nie reprezentacja każdego producenta.

Odbiór na rzeczywistym Windows/NTFS, SNMPv2c/v3/SSH, fizyczne odłączenie Internetu/cache oraz łączny RAM procesu i karty pozostają jawnie niewykonane. Lokalność wymaganych skryptów/CSS sprawdzono; nie należy mylić tego z fizycznym testem odłączonego Internetu. [Wyniki i ograniczenia](../etap-4/RAPORT_ETAP_4.md).
