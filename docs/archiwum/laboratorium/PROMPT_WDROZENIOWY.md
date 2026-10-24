# Prompt do przygotowania wdrożenia domowej sieci i lokalnego AI

> Materiał historyczny: laboratorium domowe i sprzęt. Nie określa bieżącego zakresu mappera Python. Aktualna dokumentacja: [spis treści](../../README.md).

Skopiuj treść od „Rola i rezultat” do końca. Prompt służy do przygotowania instrukcji; wybór wariantu dostępności i uzupełnienie danych sprzętowych muszą poprzedzać rzeczywiste przełączenie sieci.

## Rola i rezultat

Działasz jako inżynier sieciowy, administrator Linux/KVM oraz specjalista bezpieczeństwa. Przygotuj po polsku techniczny, zrozumiały przewodnik wdrożenia domowej sieci, OPNsense, lokalnej Ollamy i dostępu VPN. Podawaj konkretne konfiguracje dla wybranego wariantu, wraz z testami i sposobem wycofania zmian.

Najpierw sprawdź wykonalność wymagań. Gdy są sprzeczne, nazwij konflikt i przedstaw minimalną zmianę założeń. Nie obiecuj ciągłości usług ani pełnej wydajności bez uzasadnienia. Twoim zadaniem jest przygotowanie przewodnika, a nie wykonywanie zmian na komputerze lub routerze.

## Sprzęt, koszty i priorytety

- Host: AMD Ryzen 7 9800X3D, 8 rdzeni/16 wątków; 32 GB DDR5; Radeon RX 9070 XT.
- Jedna wbudowana karta Ethernet; jej model, szybkość i sterownik nie są jeszcze znane.
- Operator: **Play, światłowód, deklarowana prędkość 300 Mb/s**. Prędkość wysyłania i model routera/ONT nie są jeszcze znane.
- Według użytkownika **IPv6 jest przydzielany automatycznie**. Nie utożsamiaj automatycznej konfiguracji ze zmiennym prefiksem, delegacją prefiksu do własnego routera ani osiągalnością połączeń przychodzących. Nie wnioskuj o CGNAT, DS-Lite lub rodzaju IPv4 wyłącznie z obecności IPv6.
- Nie znamy modelu płyty, konfiguracji dysków, modelu urządzenia ISP, switcha ani punktu dostępowego Wi-Fi.
- Linux ma służyć również do codziennej pracy. Windows do gier ma działać natywnie w dual-boocie, preferencyjnie na osobnym dysku.
- Usługi obliczeniowe i zarządzanie mają mieścić się na jednym komputerze. Switch, urządzenie ISP i punkt dostępowy pozostają elementami fizycznej sieci.
- Cel: 0 zł dodatkowych opłat licencyjnych i minimalny zakup sprzętu. Preferuj darmowe komponenty Open Source. Oddziel koszt zakupów, energii, ewentualnego publicznego IP oraz posiadanej lub wymaganej licencji Windows.
- Windows, wymagany firmware i opcjonalne usługi SaaS oznacz jawnie jako wyjątki od ścisłego wymogu Open Source. Nie utożsamiaj darmowego planu z otwartym oprogramowaniem. Osobno sprawdź licencję wag wybranego modelu AI.
- Priorytety: bezpieczeństwo i możliwość odzyskania sieci, wykonalność, koszt, wygoda, następnie wydajność.

## Obowiązkowe rozstrzygnięcie: dual-boot a router

Wyjaśnij na początku: restart do Windowsa, wyłączenie, uśpienie lub awaria hosta zatrzymują linuksową VM OPNsense i linuksową usługę AI. Jeśli OPNsense jest jedyną bramą domu, przestają działać routing do Internetu i VPN przez tę VM. GRUB, dodatkowa karta sieciowa ani Proxmox na tym samym komputerze nie usuwają tej zależności.

Przedstaw trzy warianty i tabelę kompromisów:

1. **OPNsense jako główny router na hoście z dual-bootem:** spełnia cel jednego komputera, ale wymaga akceptacji przerw oraz procedury przywrócenia obecnego routera. Główną instrukcję dla tego wariantu oznacz jako warunkową; nie zakładaj, że akceptuję odłączenie domu podczas grania.
2. **Obecny router działa stale, OPNsense obsługuje wydzielone laboratorium:** pozwala zachować Internet podczas pracy Windowsa bez zakupu nowego komputera, jeśli posiadane urządzenie może pełnić rolę routera. Jawnie zaznacz, że OPNsense nie jest wtedy głównym firewallem całej sieci, a AI na Linuksie nadal jest niedostępne podczas pracy Windowsa.
3. **OPNsense jako główny router stale dostępny:** wymaga stale działającego środowiska routera, np. oddzielnego urządzenia, albo rezygnacji z natywnego dual-bootu i zaakceptowania ograniczeń Windowsa w VM. Wyjaśnij koszty oraz ryzyko niezgodności gier/anti-cheat; nie zakładaj, że Windows w VM zastąpi Windows uruchamiany natywnie.

Jeśli nie wybiorę wariantu, przygotuj analizę i warunkowy przewodnik. Wyraźnie wskaż decyzję konieczną przed przełączeniem bramy domu. Nie przedstawiaj wszystkich pierwotnych wymagań jako jednocześnie spełnionych.

## Weryfikacja i brakujące dane

Przed doborem wersji sprawdź aktualną oficjalną dokumentację AMD ROCm/Radeon, Ollamy, OPNsense, Ubuntu, libvirt oraz wybranego VPN. Dla WAN sprawdź materiały Play dotyczące konkretnej usługi światłowodowej i urządzenia; nie przenoś ustawień z oferty mobilnej lub kablowej po UPC na to łącze. Podaj datę sprawdzenia, wersje i linki. Rozróżniaj wsparcie GPU, systemu/kernelu, backendu Ollamy oraz ewentualnego passthrough: obecność GPU w tabeli ROCm nie potwierdza całego zestawu.

Nie wymyślaj nazw interfejsów, identyfikatorów PCI, grup IOMMU, nazw dysków ani właściwości BIOS-u. Używaj oznaczonych parametrów, np. `<WAN_NIC>`, `<LAN_NIC>`, `<LINUX_DISK>`, `<GPU_BDF>`. Pokaż, jak je ustalić poleceniami tylko do odczytu, np. `ip -br link`, `ip route`, `lspci -nnk`, `lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS,MODEL` i odpowiednimi odczytami `/sys`.

Zbierz maksymalnie sześć grup pytań:

1. Czy Internet ma działać podczas grania w Windowsie i wyłączenia hosta? Czy akceptuję oddzielne urządzenie lub wariant laboratoryjny?
2. Jaki jest model routera/ONT Play, tryb bridge/router, sposób zestawiania WAN: DHCP, PPPoE, VLAN operatora? Czy są IPTV/telefonia i czy można użyć własnego routera?
3. Jaki jest rodzaj IPv4? Czy potwierdzony automatyczny IPv6 obejmuje globalny adres, delegację DHCPv6-PD i połączenia przychodzące? Jaka jest długość/stabilność prefiksu oraz prędkość wysyłania przy znanej prędkości 300 Mb/s?
4. Jakie modele switcha i punktu Wi-Fi posiadam? Czy obsługują 802.1Q? Jaki jest obecny plan adresacji?
5. Jaki jest model płyty, NIC i liczba dostępnych slotów PCIe? Czy działa iGPU i wyjście obrazu płyty? Jak wyglądają grupy IOMMU?
6. Jakie dyski, wolne miejsce, konfigurację UEFI/Secure Boot/BitLocker i kopie zapasowe posiadam?

Bez odpowiedzi kontynuuj projekt niezależnych elementów i podaj warunki dla pozostałych. Nie podawaj komend partycjonowania ani finalnej konfiguracji przełączenia WAN jako gotowych do uruchomienia na nieznanym sprzęcie. Nie proś o przesyłanie haseł PPPoE, kluczy prywatnych, klucza odzyskiwania BitLocker ani pełnych konfiguracji z sekretami.

## Wybór bazy i sposób uruchomienia AI

Preferowany punkt wyjścia: **Ubuntu Desktop LTS + KVM/QEMU + libvirt + virt-manager**, w konkretnej kombinacji wydania/kernelu potwierdzonej dla RX 9070 XT i wybranego stosu ROCm/Ollama. Uzasadnij ten wybór względem Debiana i Proxmox VE. Nie wybieraj automatycznie najnowszego LTS, jeśli nie ma potwierdzonego wsparcia GPU. Proxmox omów jako alternatywę dla dedykowanego serwera; nie przedstawiaj go jako rozwiązania konfliktu dual-bootu z dostępnością routera.

OPNsense uruchom w VM. Dla AI porównaj:

- **Usługę na hoście lub kontener:** preferuj prostszy wariant z działającym sterownikiem AMD na hoście. Udostępnienie `/dev/kfd` i odpowiednich urządzeń `/dev/dri` kontenerowi nie jest PCI passthrough i nie wymaga VFIO. Host i AI współdzielą zasoby GPU; opisz wpływ na pulpit i słabszą izolację niż w VM. Wybierz jeden wariant do pełnej instrukcji.
- **VM z dedykowanym GPU:** opcjonalny wariant zaawansowany, po potwierdzeniu IOMMU, izolacji urządzeń i poprawnego resetu GPU. Karta przypisana przez VFIO do VM nie może równocześnie działać jako zwykłe GPU hosta. Rozważ iGPU 9800X3D do pulpitu po sprawdzeniu płyty, BIOS-u i wyjść obrazu. Nie obiecuj współdzielenia RX 9070 XT przez SR-IOV/mdev bez potwierdzonego wsparcia.

## Krok 0 — Projekt i możliwość odzyskania sieci

Przedstaw diagram połączeń, tabelę interfejsów/bridge/VLAN oraz plan adresacji bez konfliktów z obecną siecią i VPN. Oddziel adresację operatora od wewnętrznych VLAN-ów.

Zaplanuj kopie danych, ustawień obecnego routera i konfiguracji systemów. Zapewnij lokalny dostęp do konsoli hosta/VM oraz stały adres zarządzania hostem po stronie LAN. Zarządzanie lokalne nie powinno wymagać działającego DHCP, DNS ani routingu OPNsense. Opisz wejście z klienta ze statycznym adresem w tym samym segmencie LAN.

Najpierw zbuduj laboratorium za obecnym routerem, potem wykonaj testy, a dopiero na końcu opisz przełączenie domu. Przygotuj fizyczny schemat powrotu do poprzedniej konfiguracji. Nie zakładaj automatycznego failoveru ani zapasowego DHCP bez osobnego projektu.

## Krok 1 — Instalacja Linuxa i dual-boot

Użyj GPT i UEFI dla obu systemów. Preferuj osobne dyski, z niezależnymi partycjami EFI, jeśli sprzęt i instalatory na to pozwalają. Dla jednego dysku przedstaw bezpieczny wariant współdzielenia istniejącej ESP bez jej formatowania.

Opisz wybór systemu przez menu UEFI i opcjonalnie GRUB, zachowanie wpisu Windows Boot Manager oraz odzyskanie uruchamiania. Uwzględnij kopię klucza odzyskiwania BitLocker, wpływ zmian rozruchu na TPM/BitLocker i Windows Fast Startup. Nie nakazuj bezwarunkowo wyłączać Secure Boot; uwzględnij wymagania Windows/gier i podpisy modułów lub MOK, jeśli wybrany sterownik tego wymaga.

Podaj instalację KVM/libvirt, kontrolę wirtualizacji AMD-V/SVM i konfigurację uprawnień. IOMMU/VFIO dodaj tylko dla wariantu z passthrough. Wyjaśnij zależność automatycznego startu usług od ewentualnego ręcznego odblokowania zaszyfrowanego dysku.

## Krok 2 — Połączenia WAN/LAN i sieci wirtualne

Porównaj trzy fizycznie wykonalne topologie:

1. **Dwie karty Ethernet:** oddzielny `br-wan` i `br-lan`; modem/ONT do WAN, domowy switch/AP do LAN. Porównaj tanią kartę PCIe i USB na podstawie chipsetu, dostępnych slotów, sterownika Linux, szybkości i stabilności. Jeśli NIC obsługuje host, a VM ma VirtIO, nie wymagaj sterownika FreeBSD dla tego fizycznego NIC. Preferencję dla PCIe uzasadnij; USB może być wariantem budżetowym.
2. **Jedna karta i switch zarządzalny 802.1Q:** trunk do hosta oraz rozdzielone VLAN-y WAN/LAN. Pokaż tabelę portów access/trunk, tagged/untagged/PVID, port urządzenia ISP, porty LAN/AP i dostęp do zarządzania switchem. Wybierz jedno miejsce obsługi tagów: np. subinterfejsy VLAN hosta i oddzielne bridge z nietagowanymi vNIC dla OPNsense. Nie dodawaj ponownie tych samych tagów w VM. Uwzględnij współdzielenie przepustowości oraz odrębność VLAN-u operatora.
3. **Jedna karta bez infrastruktury VLAN:** zaprojektuj OPNsense jako router wydzielonego wirtualnego laboratorium za istniejącą bramą. Wyjaśnij, że dwa bridge w oprogramowaniu nie tworzą dwóch odizolowanych fizycznych sieci domowych na jednym nietagowanym łączu.

Nigdy nie łącz WAN i LAN wspólnym bridge. W wariancie głównego routera nie przypisuj hostowi adresu IPv4/IPv6, DHCP ani usług zarządzania po stronie WAN. Wyłącz automatyczną konfigurację IPv6 na interfejsach hosta należących do WAN, bez wyłączania tranzytu IPv6 do VM.

Dla Ubuntu wybierz jeden spójny sposób zarządzania siecią, np. NetworkManager lub Netplan z jednym wskazanym rendererem. Nie konfiguruj tych samych interfejsów kilkoma niezależnymi metodami. Wyjaśnij różnicę między bezpośrednim bridge a domyślną siecią NAT libvirt. Nie uruchamiaj konkurencyjnych DHCP/NAT w produkcyjnym LAN. Zmiany mogące zerwać połączenie wykonuj z konsoli lokalnej i zapewnij wycofanie.

OPNsense nie zastępuje fizycznego punktu Wi-Fi. Wyjaśnij tryb AP, okablowanie oraz wyłączenie jego DHCP/NAT, gdy bramą jest OPNsense.

## Krok 3 — OPNsense

Zaproponuj początkowo 2 vCPU, 4 GiB stałego RAM, około 40 GiB dysku i dwie karty VirtIO. Zweryfikuj bieżące zalecenia OPNsense, przypisz WAN/LAN według MAC i opisz wymagane ustawienia offloadingu.

Rozróżnij WAN DHCP, PPPoE, wymagany VLAN ISP, bridge urządzenia operatora oraz wariant za routerem z podwójnym NAT. Nie proponuj zmiany trybu urządzenia operatora bez uwzględnienia IPTV/telefonii. Ustawienia blokowania adresów prywatnych na WAN dopasuj do rzeczywistej topologii.

Skonfiguruj LAN, jeden serwer DHCP, DNS oraz outbound NAT IPv4, jeśli jest potrzebny. Uwzględnij istniejący IPv6 Play jako osobny element projektu. Rozróżnij adres WAN, adres klienta uzyskany przez SLAAC/DHCPv6 oraz prefiks delegowany routerowi przez DHCPv6-PD. Adres IPv6 na obecnym komputerze nie dowodzi możliwości delegacji prefiksu do OPNsense.

Jeśli PD jest dostępne, dobierz WAN DHCPv6 i przypisanie odrębnych podsieci /64 do LAN/VLAN zgodnie z otrzymanym prefiksem; nie zgaduj /56 ani /60. Użyj mechanizmu śledzenia/delegacji właściwego dla wybranej wersji OPNsense i skonfiguruj RA oraz DNS dla klientów. Jeśli router Play zostaje przed OPNsense, potwierdź jego delegację do routera podrzędnego lub jawnie routowany prefiks. Brak PD nie przeszkadza sam w sobie w VPN kończącym się na osiągalnym adresie WAN, ale ogranicza zwykłe routowanie publicznego IPv6 do oddzielnych sieci za OPNsense. Nie dziel tego samego /64 między odrębne segmenty ani nie stosuj NAT66/NDP proxy jako automatycznego obejścia.

Nie zakładaj, że NAT IPv4 zabezpiecza IPv6. Reguły IPv6 mają blokować niezamówiony dostęp do usług, zachowując niezbędny ICMPv6, w tym obsługę Path MTU Discovery, oraz właściwy dla interfejsu ruch RA/NDP/DHCPv6. Sprawdź zachowanie po odnowieniu dzierżawy i ewentualnej zmianie prefiksu. Jeśli zachowanie IPv6 nie jest jeszcze potwierdzone, opisz ograniczenie etapu przejściowego i plan jego uruchomienia.

Podaj tabelę reguł: źródło, cel, protokół, port, kierunek i uzasadnienie. GUI/SSH udostępnij wyłącznie uprawnionym klientom LAN/VPN, zablokuj niezamówione połączenia z WAN, ogranicz UPnP. IDS/IPS i inne kosztowne usługi pozostaw poza konfiguracją początkową.

Host powinien przekazywać ruch domowy przez OPNsense, bez alternatywnej bramy i niezamierzonego routingu między WAN/LAN. Jednocześnie wyjaśnij granicę bezpieczeństwa: administrator hosta kontroluje VM routera. Zapora OPNsense nie filtruje automatycznie komunikacji między hostem i klientami w tym samym segmencie ani ruchu kończącego się bezpośrednio na VPN hosta; potrzebna jest również zapora hosta.

## Krok 4 — Ollama i Radeon

Podaj sprawdzoną kombinację dystrybucji/kernelu, sterownika, ROCm i wydania/obrazu Ollamy. Dla kontenera przypnij zweryfikowany tag lub digest i opisz aktualizację; nie opieraj odtwarzalnego wdrożenia wyłącznie na zmiennym tagu. Nie instaluj pełnego SDK ROCm, jeśli wybrana metoda go nie wymaga.

Utwórz trwały katalog modeli, automatyczny start i limity zasobów. Dobierz model, kwantyzację i kontekst do faktycznej VRAM, pozostawiając zapas na cache i pulpit. RAM systemowy i VRAM rozliczaj osobno. Zacznij od jednego załadowanego modelu i jednego równoległego żądania.

Potwierdź użycie właściwego GPU przez logi, `ollama ps` oraz pomiar obciążenia/pamięci GPU. Samo `rocminfo` nie potwierdza akceleracji konkretnego procesu. Nie wymuszaj `HSA_OVERRIDE_GFX_VERSION` dla poprawnie wspieranej karty. Vulkan przedstaw jako osobno zweryfikowaną alternatywę, jeśli jest potrzebny.

W opcjonalnej VM opisz SVM/IOMMU, grupy urządzeń, przypisanie właściwych funkcji PCI, UEFI gościa, obsługę obrazu hosta, test restartu VM i powrotu do Windowsa oraz wycofanie VFIO. Nie stosuj domyślnie ACS override ani globalnego blacklistowania `amdgpu`, które mogłoby wyłączyć iGPU hosta.

API lokalnej Ollamy traktuj jako usługę bez wbudowanej kontroli dostępu użytkowników. Nie przekierowuj portu 11434 z Internetu. Wybierz konkretny adres nasłuchu i reguły hosta dla uprawnionych klientów LAN/VPN albo loopback oraz pośrednika z uwierzytelnianiem. Uwzględnij osiągalność adresu VPN przy starcie usługi. Dla Dockera sprawdź rzeczywistą ekspozycję portów i reguły silnika; sama reguła UFW nie wystarcza jako dowód blokady.

API i interfejs rozmowy to osobne elementy. Zaproponuj opcjonalny lekki interfejs WWW z logowaniem, po sprawdzeniu aktualnej licencji i zasobów; nie przypisuj Ollamie funkcji wybranego frontend-u. Opisz tryb wyłącznie lokalnego AI, bez korzystania z modeli chmurowych.

## Krok 5 — Bezpieczny dostęp zdalny

Preferuj WireGuard w OPNsense, jeśli istnieje osiągalny endpoint: publiczny IPv4 lub poprawnie dostępny globalny IPv6. Rozróżnij adres dynamiczny z DDNS, NAT własnego routera, CGNAT i DS-Lite. DDNS i przekierowanie na własnym routerze nie usuwają CGNAT.

W przypadku tego łącza Play najpierw sprawdź możliwość WireGuard przez IPv6. Samo CGNAT dla IPv4 nie wyklucza bezpośredniego VPN po osiągalnym IPv6. Klient poza domem musi jednak mieć działającą łączność IPv6 do tego endpointu; pokaż alternatywę dla sieci wyłącznie IPv4. Rodzinę adresu endpointu odróżnij od adresacji wewnątrz tunelu: przez endpoint IPv6 można uzyskać dostęp do domowego LAN IPv4.

Jeśli adres/prefiks się zmienia, zaprojektuj DDNS z rekordem AAAA wskazującym aktualny adres endpointu, uwzględnij TTL i ponowne rozwiązywanie nazwy przez konkretnego klienta WireGuard. Sama aktualizacja DNS nie gwarantuje odświeżenia już działającego tunelu. Nie wybieraj tymczasowego adresu prywatności jako stałego celu DNS. Przy zwykłym routowanym IPv6 otwieraj konkretny port UDP w odpowiednich zaporach, również routera Play, jeśli stoi przed OPNsense; nie zastępuj tego przekierowaniem NAT dla IPv4. Potwierdź działanie handshake poprawnie skonfigurowanego klienta, ponieważ sam ping lub skan portu UDP nie potwierdza dostępności WireGuard.

Pokaż konfigurację serwera i klientów, osobny klucz każdego urządzenia, `AllowedIPs`, routing odpowiedzi, DNS i reguły firewall. Preferuj split tunnel do wskazanych usług/podsieci; full tunnel omów osobno. Port UDP WireGuard dopuść na WAN OPNsense; przekierowanie portu dodaj tylko na rzeczywistym routerze stojącym przed nim, jeśli jest potrzebne. Keepalive stosuj tam, gdzie uzasadnia go NAT.

Dla CGNAT przedstaw zarządzany Tailscale jako opcję z darmowym planem i zależnością od zewnętrznego, zamkniętego serwera koordynacyjnego. Określ miejsce instalacji, uprawnienia ACL/grants oraz różnicę między dostępem tylko do hosta AI i dostępem do LAN przez subnet router. Sprawdź bieżące limity i możliwe użycie relay; nie gwarantuj bezpośredniego połączenia ani określonej szybkości.

Jeśli wymaganie Open Source jest bezwzględne, omów Headscale lub WireGuard przez osiągalny zewnętrzny węzeł. Nie obiecuj kosztu 0 zł, gdy taki węzeł/publiczny endpoint nie jest już dostępny. Sam Headscale umieszczony za tym samym CGNAT nie zapewnia automatycznie jego osiągalności.

Testuj z telefonu przez sieć komórkową. Sprawdź dostęp uprawnionego klienta do AI oraz odmowę dla nieuprawnionego klienta. Wyjaśnij odebranie dostępu zgubionemu urządzeniu. Zdalny dostęp nadal zależy od działania odpowiedniego hosta/routera.

## Budżet zasobów

Przygotuj tabelę RAM, vCPU/limitów CPU, dysku i VRAM. Punkt startowy dla 32 GiB: OPNsense 4 GiB, limit RAM usługi/kontenera AI 12 GiB, orientacyjny budżet pulpitu/systemu 10 GiB, 6 GiB zapasu na narzut i skoki zużycia. To plan, nie cztery sztywne rezerwacje; uwzględnij faktycznie dostępną pamięć, cache i narzut QEMU. Dla VM AI przelicz budżet osobno.

Wyjaśnij, że vCPU i limity CPU są współdzielone, a limit RAM kontenera nie ogranicza VRAM. Zaproponuj limity AI i obserwację `MemAvailable`, aby przeciążenie AI nie destabilizowało routera. Nie opieraj stałej pracy routera na agresywnym overcommitcie, ballooningu lub swapie. Swap/zram może pomóc hostowi, ale nie zastępuje RAM-u. Bez uzasadnienia nie włączaj ogromnych stron, pinningu wszystkich rdzeni ani rozbudowanych warstw pamięci masowej.

## Krok 6 — Odbiór, aktualizacje i rollback

Dla każdego kroku podaj: warunki wejścia, miejsce wykonania poleceń (host/gość/OPNsense/Windows), pełne pliki dla wybranego wariantu, test i oczekiwany wynik, warunek zatrzymania oraz wycofanie. Polecenia wymagające podstawienia parametrów oznacz wyraźnie. Zmiany dyskowe i sieciowe przedstawiaj po kopiach i kontroli stanu.

Końcowe testy powinny obejmować:

- Rozruch obu systemów i przewidziane zachowanie sieci podczas pracy Windowsa.
- Start hosta bez dostępnego Internetu: router uruchamia się bez pobierania obrazów, działającej usługi AI czy zewnętrznego DNS; AI startuje później.
- DHCP/DNS, WAN IPv4, przyjęte zachowanie IPv6, izolację WAN/LAN i brak obejścia zapory.
- Dla Play: uzyskanie IPv6 na WAN i — jeśli wdrażany jest routowany IPv6 LAN — delegacji prefiksu, aktualizację adresacji/DNS po zmianie prefiksu, ponowne zestawienie VPN oraz wariant dostępu z sieci wyłącznie IPv4.
- Dostęp do hosta z lokalnego klienta ze statycznym adresem po zatrzymaniu OPNsense.
- Routing podczas obciążenia AI i brak presji pamięci destabilizującej VM.
- Faktyczną akcelerację GPU, VPN z sieci komórkowej i niedostępność API/GUI od strony WAN dla IPv4 i IPv6.
- Restart VM/hosta, odtworzenie konfiguracji oraz praktyczny powrót do poprzedniego routera.

Zaplanuj backup konfiguracji OPNsense, definicji libvirt, konfiguracji sieci hosta, usługi/kontenerów i bezpiecznie przechowywanych kluczy VPN. Rozróżnij odtwarzalne modele AI od danych, których utrata jest istotna. Kopia wyłącznie na tym samym dysku/hoście nie chroni przed jego awarią; jeśli nie mam zewnętrznego miejsca, nazwij to ograniczenie kosztu 0 zł. Opisz kolejność aktualizacji, test po aktualizacji i powrót do sprawdzonej wersji.

Zakończ decyzjami wymaganymi przed przełączeniem domu oraz kryteriami „gotowe do wdrożenia”. Nie deklaruj gotowości rzeczywistej konfiguracji, gdy nie ustalono dostępności, topologii ISP, fizycznej separacji WAN/LAN albo nie wykonano wymaganych testów. Jeśli nie masz dostępu do aktualnych źródeł, oznacz wersje i kompatybilność jako niezweryfikowane.
