# Domowe laboratorium sieciowe i lokalne AI — plan wdrożenia

> Materiał historyczny: laboratorium domowe i sprzęt. Nie określa bieżącego zakresu mappera Python. Aktualna dokumentacja: [spis treści](../../README.md).

Stan założeń: 10 października 2026 r. Łącze Play, światłowód 300 Mb/s, router z dawnej infrastruktury UPC (model nieznany), automatycznie przydzielany IPv6. Komputer główny: Ryzen 7 9800X3D, 32 GB RAM, Radeon RX 9070 XT, jedna karta Ethernet; Linux do pracy i AI, Windows do gier. Jest też laptop prawdopodobnie z procesorem Intel Core i3 drugiej generacji i **2 GB RAM**; model, porty i możliwość rozbudowy trzeba sprawdzić. Jest osobny router/AP Wi-Fi, ale nie ma switcha zarządzalnego VLAN. **Internet w całym domu ma działać bez przerwy także po uruchomieniu Windows.**

## Nowy wariant: laptop jako stale włączony router

Przy budżecie 150–400 zł, sprzęcie używanym i posiadanym osobnym AP konkretne opcje zakupowe oraz kryteria wyboru są w [planie sprzętowym](PLAN_SPRZETOWY_150-400_ZL.md).

Laptop mógłby uruchamiać OPNsense **bezpośrednio na swoim dysku** i pracować 24/7. To usuwa zasadniczy konflikt między głównym routerem a dual bootem komputera z Radeonem. **Obecne 2 GB RAM nie wystarczają do zalecanego wdrożenia OPNsense**: dokumentacja podaje minimum 3 GB, a dla łącza z zakresu 151–350 Mb/s rozsądny punkt startu to dwurdzeniowy procesor około 1 GHz, 4 GB RAM i dysk 40 GB. Wymagania rosną przy IDS/IPS i proxy. OPNsense wymaga x86-64. Są to wymagania orientacyjne, a rzeczywistą przepustowość sprawdza się testem po instalacji ([wymagania sprzętowe OPNsense](https://docs.opnsense.org/manual/hardware.html)).

**Brama wdrożeniowa dla tego laptopa:** najpierw potwierdź, że pamięć można zwiększyć do co najmniej 4 GB (8 GB daje większy zapas), CPU jest 64-bitowy, dysk nadaje się do pracy ciągłej, a laptop ma dwa przewodowe porty Ethernet. Bez switcha VLAN pojedynczy port nie wystarczy do oddzielenia WAN/LAN; jeśli jest tylko jeden, potrzebny będzie drugi adapter zgodny z FreeBSD. Sprawdź, czy laptop ma USB 3 (`lsusb -t` pokazuje magistralę `5000M` lub więcej); przy samym USB 2 nie zakładaj osiągnięcia stabilnych 300 Mb/s na adapterze Ethernet. **Nie instaluj OPNsense na obecnych 2 GB i nie przełączaj jeszcze domu.**

Jeśli rozbudowa RAM okaże się niemożliwa lub nieopłacalna, lżejszy [OpenWrt na x86](https://openwrt.org/docs/guide-user/installation/openwrt_x86) jest opcją do osobnego testu na tym laptopie, lecz nie spełnia pierwotnego wymagania użycia OPNsense. Nadal potrzebuje pewnego rozdzielenia WAN/LAN i AP po stronie LAN. Alternatywnie pozostaw router Play jako bramę, a OPNsense testuj w VM zgodnie z dalszą częścią przewodnika.

Docelowa topologia, **jeśli laptop ma dwa działające interfejsy Ethernet i osobny punkt Wi-Fi za nim**:

```text
Play/UPC (Internet, modem/router)
    │ port LAN; bridge mode tylko jeśli dany model i usługa na to pozwalają
    ▼
WAN laptopa z OPNsense ── firewall/NAT/DHCP/VPN ── LAN laptopa
                                                    │
                                                    ├── switch/AP Wi-Fi → urządzenia domowe
                                                    └── komputer Ryzen → Ubuntu lub Windows
```

Router Play może na początek nadal routować. Wówczas OPNsense na laptopie ma WAN z prywatnym adresem Play i robi drugi NAT dla IPv4; to wystarcza do sprawdzenia działania, lecz utrudnia przekierowania i może blokować delegację IPv6. Po potwierdzeniu modelu Play można rozważyć jego bridge mode lub sposób podłączenia bezpośrednio do ONT, o ile operator i sprzęt to dopuszczają. **Całe Wi-Fi domu musi być za LAN OPNsense.** Jeśli Play nadal nadaje Wi-Fi po stronie WAN laptopa, podłączone tam urządzenia omijają OPNsense. Wbudowane Wi-Fi laptopa nie jest pewnym zamiennikiem punktu dostępowego: dokumentacja OPNsense zaleca zewnętrzne AP ze względu na ograniczenia sterowników i standardów ([OPNsense Wireless](https://docs.opnsense.org/manual/wireless.html)).

Ponieważ **nie ma switcha VLAN**, dla laptopa z jednym wbudowanym Ethernetem praktyczną drogą jest drugi **sprawdzony w FreeBSD/OPNsense** adapter USB 3 Ethernet dla WAN/LAN. Najpierw odczytaj identyfikator chipsetu adaptera i sprawdź jego obsługę w aktualnym FreeBSD; nie kupuj według samej nazwy handlowej. USB może być mniej stabilne niż port wbudowany, więc po instalacji testuj wielodniową pracę i wznowienie po awarii zasilania. Osobny router/AP, który już posiadasz, można umieścić za LAN OPNsense; trzeba sprawdzić jego tryb AP/bridge.

Zasilacz laptopa musi być podłączony stale, a zamknięcie klapy nie może go usypiać. W UEFI wyłącz automatyczne usypianie i, jeśli dostępne, ustaw uruchomienie po powrocie zasilania. Sprawdź stan baterii i wentylacji; zużyta lub puchnąca bateria nie nadaje się do całodobowej pracy. Przetestuj restart, zanik zasilania i powrót Internetu **zanim** przełączysz całą rodzinę na nową bramę.

**Zmiana względem kroków poniżej:** Kroki 1, 2 i 3 opisują nadal działające laboratorium OPNsense na komputerze głównym. Po zatwierdzeniu sprzętu laptopa zastąp je instalacją OPNsense na laptopie i dwiema fizycznymi sieciami WAN/LAN; Ubuntu/Windows i Ollama na komputerze głównym pozostają jak w krokach 1 i 4. Serwer WireGuard najlepiej wtedy uruchomić na laptopie z OPNsense, bo będzie dostępny niezależnie od systemu na komputerze głównym. Dostęp do API Ollamy nadal zniknie, gdy komputer uruchomi Windows; VPN do domu będzie działać dalej.

### Kolejność wdrożenia na laptopie (po potwierdzeniu sprzętu)

1. **Inwentaryzacja i kopia danych.** Na dotychczasowym systemie laptopa odczytaj model CPU, RAM, dysku, portu Ethernet i ewentualnego adaptera USB. W Linuxie pomocne są `lscpu`, `free -h`, `lsblk -o NAME,SIZE,MODEL`, `lspci -nn` i `lsusb`; w Windows — `msinfo32` i Menedżer urządzeń. Zrób kopię danych: bezpośrednia instalacja OPNsense zastąpi obecny system na wybranym dysku. Zapisz dane logowania i konfigurację Play, aby mieć drogę powrotu.
2. **Przygotowanie nośnika.** Pobierz z [oficjalnej strony OPNsense](https://docs.opnsense.org/manual/install.html) obraz USB `vga` dla `amd64` oraz plik sum kontrolnych. Porównaj SHA256, nagraj obraz na pendrive, uruchom laptop w UEFI i zainstaluj OPNsense na jego dysku. Dla 4 GB RAM zacznij od podstawowego routingu i WireGuard bez IDS/IPS/proxy. W ustawieniach zasilania/UEFI wyłącz usypianie po zamknięciu pokrywy i przetestuj start po zaniku prądu.
3. **Próba bez ruszania domu.** Połącz `Play LAN → laptop WAN`, a drugi port laptopa `LAN → jeden testowy komputer/switch`. OPNsense WAN ustaw na DHCPv4 z Play, LAN np. `10.77.20.1/24` z DHCP `10.77.20.100–199`; włącz domyślny NAT wychodzący i zaporę. Upewnij się, że testowy komputer dostaje `10.77.20.x`, rozwiązuje DNS i osiąga około 300 Mb/s przy pobieraniu, bez wyłączania sieci domowej Play. Sprawdź stabilność linku i temperaturę laptopa przez kilka dni. Jeśli adapter Ethernet USB znika po restarcie/odłączeniu, nie używaj go jako krytycznego portu routera.
4. **Przygotowanie Wi-Fi za OPNsense.** Osobny router Wi-Fi ustaw w tryb AP/bridge (bez NAT i bez jego DHCP), połącz go do LAN laptopa i nadaj mu adres zarządzania w `10.77.20.0/24`, np. `10.77.20.2` poza pulą DHCP. Gdy sprzęt nie ma jawnego trybu AP, zwykle używa się portu LAN zamiast WAN, ale zależy to od modelu. Wszystkie urządzenia domowe, w tym komputer Ryzen, muszą znaleźć się **po stronie LAN laptopa**. Pozostaw Play Wi-Fi włączone tylko jako tymczasowy kanał awaryjny podczas testu; urządzenia przy nim nie są chronione przez OPNsense.
5. **Przełączenie i powrót awaryjny.** Dopiero po udanym teście przepnij pozostałe urządzenia/switch/AP na LAN OPNsense. Odnowienie dzierżaw DHCP lub ponowne połączenie Wi-Fi jest konieczne po zmianie bramy. Sprawdź Internet i DNS na telefonie, telewizorze i Windows; potem uruchom Ubuntu i sprawdź Ollamę. Jeśli laptop przestanie routować, przywróć połączenia urządzeń bezpośrednio do Play i jego dawny DHCP/Wi-Fi. Przed utrwaleniem nowego układu wykonaj kopię konfiguracji OPNsense.

**IPv6 to osobna bramka odbioru:** za routerem Play laptop nie dostanie automatycznie osobnego prefiksu tylko dlatego, że Play przydziela IPv6 klientom. Sprawdź DHCPv6-PD na WAN laptopa i prefiks na jego LAN. Jeśli Play go nie deleguje, sieć za OPNsense będzie na razie IPv4; pełne IPv6 wymaga potwierdzonej delegacji z Play, bridge/direct ONT albo innego świadomie zaprojektowanego rozwiązania. Nie kopiuj prefiksu `/64` z Play na obie strony firewalla ([OPNsense IPv6](https://docs.opnsense.org/manual/ipv6.html)).

**VPN po przeniesieniu OPNsense:** skonfiguruj WireGuard Road Warrior na laptopie według [instrukcji OPNsense](https://docs.opnsense.org/manual/how-tos/wireguard-client.html). Utwórz instancję serwera, osobne peer dla telefonu i laptopa, regułę UDP na WAN oraz reguły ruchu na interfejsie VPN tylko do potrzebnych podsieci. Jeśli WAN OPNsense nadal ma prywatny adres z Play, potrzebne będzie osiągalne połączenie przychodzące i przekierowanie/reguła na Play; publiczny IPv4 lub osiągalny IPv6 trzeba potwierdzić testem spoza domu. `AllowedIPs` klienta może obejmować wyłącznie podsieć domową (split tunnel). Do API Ollamy dodaj regułę VPN → adres komputera głównego tylko wtedy, gdy Ubuntu działa i usługa jest wystawiona **wyłącznie** na chroniony interfejs/adres; nie otwieraj portu `11434` na WAN.

## Wariant bez laptopa: OPNsense jako laboratorium

Przy tym warunku VM z OPNsense na komputerze z dual bootem **nie może być głównym routerem domu**. Przy przełączeniu z Linuxa na Windows VM się wyłączy i odetnie dom od Internetu. Druga karta sieciowa, VLAN-y ani dodatkowy switch tego nie naprawią. Wariant bez zakupów wygląda tak:

```text
Internet Play ── router/ONT Play (brama, DHCP, Wi-Fi, IPv6) ── domowa sieć
                                      │
                                      └── jedna karta Ethernet komputera
                                            ├── Windows: gry; dom nadal online
                                            └── Ubuntu Desktop: KVM, Ollama/ROCm
                                                 │
                                                 ├── br-home ── WAN VM OPNsense
                                                 └── br-lab  ── LAN VM OPNsense ── testowe VM
```

OPNsense będzie rzeczywistym routerem i firewallem **dla odizolowanej sieci laboratoryjnej**, ale nie dla całego domu. Ta sieć działa tylko po uruchomieniu Ubuntu i VM. Ollama na Ubuntu działa tylko, gdy uruchomiony jest Linux. Do nieprzerwanego działania OPNsense jako bramy całego domu potrzebny jest osobny, stale włączony komputer/router z co najmniej dwoma portami Ethernet (lub jednym portem i zarządzalnym switchem VLAN). Druga karta w komputerze z dual bootem nie zastępuje tego urządzenia.

Wybieram Ubuntu Desktop 24.04 LTS + KVM/libvirt/virt-manager, bo komputer ma służyć także jako stacja graficzna z Radeonem. Proxmox VE jest sensowny na osobnej maszynie działającej 24/7, ale utrudnia ten konkretny scenariusz codziennego pulpitu, gier i współdzielenia GPU. Oprogramowanie jest darmowe; Windows, posiadany router oraz energia elektryczna nie są kosztem zerowym. Tailscale jest darmową opcją dostępu prywatnego, lecz jego usługa koordynacyjna nie spełnia wymogu „wyłącznie Open Source”; ścieżkę w pełni otwartą przez WireGuard opisuję osobno.

### Co sprawdzić przed instalacją

1. Odczytaj model i wersję oprogramowania routera z naklejki lub panelu administracyjnego. Zapisz adres jego LAN (np. `192.168.0.1`), zakres DHCP, tryb pracy WAN, opcje przekierowania portów i obsługę delegacji prefiksu IPv6. Występowanie urządzeń [Connect Box](https://www.play.pl/pomoc/wsparcie-techniczne/routery-i-modemy/connect-box?id=ib6) w sieci Play nie potwierdza, że właśnie taki model posiadasz. Przy dawnej infrastrukturze UPC sprawdź też, czy ostatni odcinek do urządzenia jest Ethernet/światłowód czy koncentryk HFC; wpływa to na ewentualną wymianę bramy.
2. Sprawdź, czy `10.77.10.0/24` nie koliduje z istniejącą siecią domową ani VPN. W razie konfliktu wybierz inną prywatną podsieć i zmień ją konsekwentnie we wszystkich krokach.
3. Przygotuj kopię zapasową danych i klucz odzyskiwania BitLockera; instalacja systemu i zmiany UEFI mogą uruchomić odzyskiwanie Windows. Zapisz ustawienia UEFI przed zmianami. [Ubuntu opisuje wpływ BitLockera na instalację obok Windows](https://ubuntu.com/desktop/docs/en/latest/reference/bitlocker-during-ubuntu-installation/).
4. Potwierdź, że masz osobny dysk dla Linuxa albo wystarczające nieprzydzielone miejsce. Nie formatuj dysku Windows. Sprawdź aktualną [macierz AMD dla Radeon + ROCm](https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/compatibility/compatibilityrad/native_linux/native_linux_compatibility.html) **przed** wyborem obrazu Ubuntu i sterownika: wersje HWE i ROCm zmieniają się. Poniższe polecenia ROCm odnoszą się do konkretnej sprawdzonej pary Ubuntu 24.04.4 Desktop, jądro 6.17 HWE, ROCm 7.2.1 i RX 9070 XT. Nie mieszaj ich bez sprawdzenia z nowszym obrazem lub innym jądrem.

## Krok 1. Ubuntu, KVM i dual boot

W UEFI włącz `SVM`/AMD-V i IOMMU (drugie jest przydatne przy ewentualnym VFIO), używaj trybu UEFI/GPT dla obu systemów. Najczytelniejszy układ to Windows na jednym dysku, Ubuntu na drugim, z osobnymi partycjami EFI. Windows instaluj albo zachowaj na jego dysku, następnie zainstaluj Ubuntu na dysku Linux. Na ekranie partycjonowania identyfikuj dyski po modelu i pojemności, nie tylko po nazwie `/dev/nvme...`, która może się zmienić. W Ubuntu wybierz dysk Linux jako miejsce instalacji bootloadera. W menu UEFI wybieraj `ubuntu` lub `Windows Boot Manager`; ewentualne menu GRUB jest wygodą, a nie warunkiem poprawnego dual bootu. W Windows wyłącz „Szybkie uruchamianie”, jeśli zamierzasz montować partycje NTFS z Linuxa. Nie zakładaj wspólnego montowania partycji Windows w trybie zapisu, gdy Windows został zahibernowany.

Po instalacji Ubuntu, z lokalnej sesji graficznej:

```bash
sudo apt update
sudo apt full-upgrade
sudo apt install qemu-kvm libvirt-daemon-system libvirt-clients virt-manager virtinst bridge-utils cpu-checker
sudo usermod -aG libvirt,kvm "$USER"
sudo systemctl enable --now libvirtd
```

Wyloguj się i zaloguj ponownie, by odświeżyć grupy, następnie uruchom `kvm-ok` i `virsh -c qemu:///system list --all`. Jeśli `kvm-ok` zgłasza brak przyspieszenia, sprawdź SVM w UEFI. Zaplanuj na Linux co najmniej około 120 GB, wygodniej 200 GB lub więcej na VM, modele i cache. Dla OPNsense wystarczy początkowo 40 GB wirtualnego dysku. Regularnie aktualizuj oba systemy i wykonuj kopię XML konfiguracji VM oraz dysku VM po ustabilizowaniu ustawień.

## Krok 2. Mosty `br-home` i `br-lab`

W tym wariancie **nie przełączaj routera Play w bridge mode**: to jego routing ma utrzymywać dom online, gdy komputer startuje do Windows. Jedyny fizyczny port komputera podłącz do zwykłego portu LAN routera Play. Dwa mosty Linux działają tak:

| Most | Połączenie | Adres hosta | Rola |
|---|---|---|---|
| `br-home` | fizyczny Ethernet + WAN OPNsense | DHCPv4 i IPv6 z Play | pulpit Ubuntu i wyjście VM do Internetu |
| `br-lab` | LAN OPNsense + testowe VM | `10.77.10.2/24`, bez bramy | sieć testowa, dostęp administracyjny do OPNsense |

Twórz mosty **przy monitorze i klawiaturze komputera**, nie przez zdalny SSH: aktywacja portu zerwie na chwilę połączenie hosta. Zanotuj nazwę dotychczasowego profilu Ethernet jako `STARY_PROFIL` i nazwę urządzenia jako `NIC` z poniższych poleceń. `NIC` ma być np. `enp5s0`, nie `wlp...` (typowy most do Wi-Fi nie pasuje do tego układu).

```bash
nmcli device status
nmcli -f NAME,UUID,TYPE,DEVICE connection show
ip -4 route
ip -6 route
```

Podstaw **rzeczywistą** nazwę portu i profilu, po czym uruchom:

```bash
NIC='enp5s0'                  # ZMIEŃ po sprawdzeniu nmcli
STARY_PROFIL='Wired connection 1'  # ZMIEŃ po sprawdzeniu nmcli

sudo nmcli connection add type bridge con-name br-home ifname br-home \
  bridge.stp no ipv4.method auto ipv6.method auto connection.autoconnect no
sudo nmcli connection add type ethernet con-name br-home-port ifname "$NIC" \
  controller br-home connection.autoconnect no
sudo nmcli connection add type bridge con-name br-lab ifname br-lab \
  bridge.stp no ipv4.method manual ipv4.addresses 10.77.10.2/24 \
  ipv4.never-default yes ipv6.method disabled connection.autoconnect no

sudo nmcli connection up br-home
sudo nmcli connection up br-home-port
sudo nmcli connection up br-lab
ip -br address show br-home br-lab
ip -4 route
ip -6 route
```

Sprawdź dostęp do panelu routera Play i zewnętrznego adresu, np. `ping -c 3 1.1.1.1`; nazwy DNS sprawdź osobno przez `getent hosts example.org`. Jeśli połączenie zniknie, wróć lokalnie do starego profilu: `sudo nmcli connection up "$STARY_PROFIL"`. Dopiero gdy testy przejdą, włącz start mostów i wyłącz automatyczny start starego profilu:

```bash
sudo nmcli connection modify br-home connection.autoconnect yes
sudo nmcli connection modify br-home-port connection.autoconnect yes
sudo nmcli connection modify br-lab connection.autoconnect yes
sudo nmcli connection modify "$STARY_PROFIL" connection.autoconnect no
```

Po restarcie Ubuntu sprawdź ponownie trasę domyślną i dostęp do Internetu. `br-lab` **nie może** mieć trasy domyślnej. Składnia profili bridge opiera się na [NetworkManager/nmcli](https://networkmanager.pages.freedesktop.org/NetworkManager/NetworkManager/nmcli-examples.html).

## Krok 3. OPNsense jako router sieci laboratoryjnej

Pobierz oficjalny obraz `dvd-amd64` OPNsense, porównaj sumę SHA256 i utwórz VM w `virt-manager` połączonym z `QEMU/KVM system` (`qemu:///system`). Na start przydziel **2 vCPU, 4 GiB RAM, 40 GiB dysku** i dwie karty `virtio`: pierwsza `br-home` jako WAN, druga `br-lab` jako LAN. Wybierz istniejący most hosta, nie sieć libvirt `default` z własnym NAT. Zapisz MAC obu kart; nazwy `vtnet0/vtnet1` mogą wymagać potwierdzenia po uruchomieniu. [OPNsense zaleca co najmniej 3 GB RAM dla VM i wyłączenie sprzętowego offloadingu](https://docs.opnsense.org/manual/virtuals.html).

Zainstaluj OPNsense na dysku VM, odmontuj ISO i w konsoli przypisz WAN do karty `br-home`, LAN do `br-lab`. WAN ustaw na DHCPv4 z routera Play. LAN ustaw na `10.77.10.1/24` i DHCP dla urządzeń testowych, np. `10.77.10.100–10.77.10.199`. Wejdź z Ubuntu na `https://10.77.10.1`, ustaw mocne hasło administratora, aktualizacje i kopię konfiguracji. W `Interfaces → Settings` wyłącz hardware checksum/TSO/LRO offloading. Zostaw domyślną zaporę WAN i NAT wychodzący; ewentualne reguły LAN ogranicz do potrzeb testów. WAN OPNsense jest za prywatną siecią Play, więc weryfikuj czy opcja blokowania prywatnych adresów WAN nie przeszkadza w konkretnym teście, zanim ją zmienisz.

Uruchom testową VM podłączoną **tylko** do `br-lab`. Powinna dostać adres `10.77.10.x`, bramę `10.77.10.1` i dostęp do Internetu. Zatrzymanie OPNsense ma odciąć tę VM, ale **nie** telefon/TV na Wi-Fi Play. Jeśli chcesz startować laboratorium automatycznie po uruchomieniu Ubuntu:

```bash
virsh -c qemu:///system list --all
sudo virsh -c qemu:///system autostart NAZWA_TWOJEJ_VM
```

### IPv6 od Play

Automatycznie przydzielony IPv6 na WAN/routerze albo na Ubuntu **nie dowodzi** delegacji prefiksu DHCPv6-PD do kolejnego routera ani dostępności połączeń przychodzących. Najpierw sprawdź w routerze Play: jego globalny adres IPv6, rozmiar delegowanego prefiksu, tryb zapory IPv6 i to, czy deleguje odrębny prefiks na WAN OPNsense. Na Ubuntu użyj `ip -6 addr show br-home` i `ip -6 route`; to pokazuje adres hosta, nie potwierdza PD. W OPNsense sprawdź dziennik DHCPv6 i status WAN. [Dokumentacja OPNsense rozróżnia adres WAN od delegacji prefiksu](https://docs.opnsense.org/manual/ipv6.html).

Bez rzeczywistego osobnego prefiksu dla sieci lab **pozostaw IPv6 na `br-lab` wyłączony**. Laboratorium będzie używać IPv4 z NAT, podczas gdy domowa sieć Play zachowa własne IPv6. Nie próbuj użyć tego samego prefiksu `/64` jednocześnie po obu stronach OPNsense. Jeśli Play udostępni PD dla OPNsense, dopiero wtedy skonfiguruj DHCPv6-PD na jego WAN, śledzenie prefiksu na LAN, RA oraz osobne reguły IPv6 firewall; nie blokuj całego ICMPv6, bo jest niezbędny do działania IPv6 ([RFC 4890](https://www.rfc-editor.org/info/rfc4890/)).

## Krok 4. Lokalny model AI na Radeon RX 9070 XT

W zalecanym układzie Ollama działa **natywnie na Ubuntu**, nie w VM. RX 9070 XT jest wtedy jednocześnie kartą obrazu pulpitu i akceleratorem ROCm; nie trzeba jej odłączać od hosta. Przekazanie jedynej karty graficznej do VM przez VFIO odebrałoby Ubuntu obraz z tej karty, a izolacja IOMMU, reset GPU i drugie wyjście obrazu komplikowałyby codzienne użytkowanie. Specyfikacja Ryzen 7 9800X3D obejmuje podstawową grafikę zintegrowaną, więc VFIO jest technicznie możliwym *późniejszym eksperymentem*, lecz wymaga sprawdzenia obrazu z iGPU, grup IOMMU i stabilności konkretnej płyty; nie jest potrzebny do pełnej akceleracji Ollamy. [Ollama wymienia RX 9070 XT jako obsługiwaną kartę Linux/ROCm](https://docs.ollama.com/gpu).

### Sterownik i ROCm

Przed wykonaniem poleceń potwierdź `lsb_release -a`, `uname -r` oraz zgodność zestawu z [macierzą AMD](https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/compatibility/compatibilityrad/native_linux/native_linux_compatibility.html). Poniższy przykład jest **zamrożonym wariantem ROCm 7.2.1** z [instrukcji AMD dla Radeon](https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/install/installrad/native_linux/install-radeon.html); dokumentacja AMD tej gałęzi nie oznacza, że to najnowsza dostępna wersja w dniu instalacji. Jeśli zainstalowałeś nowsze Ubuntu/jądro, dobierz aktualną wspieraną parę przed zmianą sterowników.

```bash
lsb_release -a
uname -r
sudo apt update
sudo apt install python3-setuptools python3-wheel
wget https://repo.radeon.com/amdgpu-install/7.2.1/ubuntu/noble/amdgpu-install_7.2.1.70201-1_all.deb
sudo apt install ./amdgpu-install_7.2.1.70201-1_all.deb
sudo amdgpu-install -y --usecase=graphics,rocm
sudo usermod -aG render,video "$USER"
sudo reboot
```

Po restarcie sprawdź `groups`, `dkms status` i `rocminfo`. W `rocminfo` RX 9070 XT powinien być widoczny jako `gfx1201`. Jeśli nie jest, zatrzymaj się na diagnostyce jądra/sterownika; samo uruchomienie Ollamy nie potwierdzi użycia GPU. [AMD podaje te kontrole po instalacji](https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/install/installrad/native_linux/install-radeon.html).

### Ollama i limity zasobów

Wybierz jeden sposób instalacji z [oficjalnej instrukcji Ollamy dla Linuxa](https://docs.ollama.com/linux): skrypt instalacyjny po obejrzeniu jego treści albo ręczne rozpakowanie pakietu `ollama-linux-amd64.tar.zst` i dodatkowego `ollama-linux-amd64-rocm.tar.zst` oraz utworzenie jednostki systemd według tej instrukcji. Dla prostego wdrożenia:

```bash
curl -fsSL https://ollama.com/install.sh -o /tmp/ollama-install.sh
less /tmp/ollama-install.sh
sh /tmp/ollama-install.sh
```

Jeśli po instalacji `ollama ps` wskazuje tylko CPU mimo poprawnego `rocminfo`, sprawdź, czy pakiet AMD ROCm Ollamy został zainstalowany; [instrukcja ręczna](https://docs.ollama.com/linux) podaje jego osobny plik. Sprawdź także uprawnienia konta usługi do `/dev/kfd` i `/dev/dri/renderD*`:

```bash
getent passwd ollama
sudo usermod -aG render,video ollama
sudo systemctl restart ollama
systemctl status ollama --no-pager
```

Wprowadź plik `/etc/systemd/system/ollama.service.d/override.conf` przez `sudo systemctl edit ollama` z treścią:

```ini
[Service]
Environment="OLLAMA_HOST=127.0.0.1:11434"
Environment="OLLAMA_NO_CLOUD=1"
Environment="OLLAMA_NUM_PARALLEL=1"
Environment="OLLAMA_MAX_LOADED_MODELS=1"
Environment="OLLAMA_CONTEXT_LENGTH=4096"
MemoryMax=12G
```

Następnie:

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
ss -ltnp | grep 11434
ollama pull qwen3:4b
ollama run qwen3:4b 'Napisz jedno zdanie po polsku.'
ollama ps
curl -s http://127.0.0.1:11434/api/tags
```

Model [`qwen3:4b`](https://ollama.com/library/qwen3%3A4b) jest rozsądnym punktem startu. `ollama ps` powinno pokazać użycie GPU; `rocminfo` i `ollama ps` razem potwierdzają akcelerację lepiej niż sam czas odpowiedzi. Limit `MemoryMax=12G` dotyczy **RAM systemowego**, a nie VRAM; zbyt duży model lub kontekst może nadal nie zmieścić się w 16 GB VRAM i zwolnić wskutek przenoszenia na RAM/CPU. Zmniejsz model/kontekst przed podnoszeniem limitów. `OLLAMA_NO_CLOUD=1` blokuje funkcje chmurowe Ollamy, ale pobranie modelu nadal wymaga Internetu. Dostęp do lokalnego API domyślnie nie wymaga hasła, dlatego musi pozostać poza publicznym Internetem ([Ollama API authentication](https://docs.ollama.com/api/authentication)).

### Bilans 32 GB RAM

| Składnik | Przydział/punkt startu | Uwagi |
|---|---:|---|
| Ubuntu, pulpit, przeglądarka, cache | ok. 10–12 GiB | nie przydzielaj tego VM na sztywno |
| OPNsense VM | 4 GiB | stały przydział |
| Ollama | do 12 GiB RAM | limit usługi, przy małym modelu zwykle mniej |
| Rezerwa hosta | ok. 4–6 GiB | bufor przeciw swap/OOM |

To są **limity i plan obciążenia**, a nie jednoczesna rezerwacja dokładnie 32 GiB. 16 GB VRAM karty Radeon jest osobnym zasobem, współdzielonym przez pulpit i model. Nie uruchamiaj dużych modeli, gier pod Linuxem i kilku ciężkich VM jednocześnie bez kontroli `free -h`, `vmstat 1`, `systemd-cgtop` i `ollama ps`. Jeśli Ubuntu zaczyna swapować, zmniejsz model lub jego kontekst, a nie zwiększaj przydział OPNsense.

## Krok 5. Dostęp zdalny i VPN

Są dwa oddzielne cele: dostęp do **Ollamy na Ubuntu** oraz do **całej sieci domowej**. Bez stale włączonego urządzenia VPN w domu drugi cel nie będzie działał w czasie gry na Windows, chyba że sam router Play ma serwer VPN lub dodasz urządzenie pracujące 24/7. Również Ollama na Ubuntu przestaje działać po uruchomieniu Windows. Nie wystawiaj portu TCP `11434` na routerze Play ani przez IPv6.

### Wariant praktyczny przy nieznanym Play/CGNAT: Tailscale Serve

To wariant bez przekierowania portów i bez potrzeby publicznego IPv4. [Plan osobisty Tailscale](https://tailscale.com/docs/reference/free-plans-discounts) może być używany bez opłaty w jego aktualnych limitach. Wyjątek od rygoru „tylko Open Source”: klient korzysta z usługi koordynacyjnej Tailscale, której infrastruktura nie jest otwarta. Jeśli ten rygor jest bezwzględny, użyj poniższego wariantu WireGuard po potwierdzeniu osiągalności IPv6 albo własnego serwera koordynacyjnego na innej, stale dostępnej maszynie.

Zainstaluj Tailscale na Ubuntu według [oficjalnej instrukcji Linux](https://tailscale.com/docs/install/linux), np. po przejrzeniu instalatora:

```bash
curl -fsSL https://tailscale.com/install.sh -o /tmp/tailscale-install.sh
less /tmp/tailscale-install.sh
sh /tmp/tailscale-install.sh
sudo tailscale up
tailscale status
```

Zainstaluj aplikację Tailscale na telefonie/laptopie i zaloguj oba urządzenia do tego samego tailnetu. Włącz HTTPS/certyfikaty dla tailnetu, jeżeli konfigurator o to poprosi. Ponieważ Ollama nasłuchuje tylko na `127.0.0.1`, udostępnij jej API **wyłącznie w tailnecie**:

```bash
sudo tailscale serve --bg 11434
tailscale serve status
```

Na telefonie wyłącz Wi-Fi, połącz się przez sieć komórkową i otwórz adres `https://NAZWA_HOSTA.NAZWA_TAILNETU.ts.net/api/tags` wskazany przez `tailscale serve status`. API do generowania odpowiedzi jest pod `/api/generate`, np. klient może wysłać `POST` z JSON zawierającym `model` i `prompt`. Ogranicz reguły dostępu tailnetu do własnych urządzeń; usuń stare urządzenia i włącz MFA w koncie. `tailscale serve` dotyczy prywatnego tailnetu; **nie włączaj Funnel**, który publikuje usługę w Internecie. [Tailscale potwierdza działanie Serve, wymaganie HTTPS i reguły dostępu](https://tailscale.com/docs/features/tailscale-serve). Tailscale na Ubuntu zapewnia dostęp do tego hosta w czasie pracy Linuxa; dostępu 24/7 do całej sieci nie włącza samym poleceniem `serve`.

### Wariant w pełni Open Source: WireGuard przez IPv6

Warunek: router Play musi przepuszczać/przekierowywać przychodzący UDP do hosta z Ubuntu po IPv6, a klient poza domem musi mieć trasę IPv6 do domu. Przydział adresu IPv6 przez Play nie dowodzi spełnienia tych warunków. Sprawdź globalny adres Ubuntu przez `ip -6 addr show br-home`, ustaw w routerze stały adres/powiązanie dla hosta, dodaj regułę zapory IPv6 dla UDP `51820` **tylko do tego hosta** i sprawdź połączenie z sieci komórkowej. Jeśli prefiks Play zmienia się, użyj dynamicznego rekordu AAAA i kontroluj jego aktualizację; nie wpisuj stałego IPv6 na ślepo. Bez opcji reguły IPv6 w routerze lub bez dostępu IPv6 po stronie klienta ten wariant może nie zadziałać. Nie wyłączaj całej zapory IPv6 routera.

Po potwierdzeniu tych warunków na Ubuntu:

```bash
sudo apt install wireguard
sudo install -d -m 700 /etc/wireguard
sudo install -m 600 /dev/null /etc/wireguard/server.key
wg genkey | sudo tee /etc/wireguard/server.key | wg pubkey | sudo tee /etc/wireguard/server.pub >/dev/null
sudo chmod 600 /etc/wireguard/server.key
```

Wygeneruj **oddzielny** klucz klienta w aplikacji WireGuard na telefonie; nie kopiuj prywatnego klucza serwera na telefon. Utwórz `/etc/wireguard/wg0.conf` (podstaw rzeczywiste klucze, nie dosłowne nawiasy):

```ini
[Interface]
Address = 10.77.50.1/24
ListenPort = 51820
PrivateKey = <ZAWARTOSC_SERVER.KEY>

[Peer]
PublicKey = <KLUCZ_PUBLICZNY_TELEFONU>
AllowedIPs = 10.77.50.2/32
```

Profil telefonu:

```ini
[Interface]
Address = 10.77.50.2/32
PrivateKey = <KLUCZ_PRYWATNY_TELEFONU>

[Peer]
PublicKey = <ZAWARTOSC_SERVER.PUB>
Endpoint = [GLOBALNY_IPV6_UBUNTU]:51820
AllowedIPs = 10.77.50.1/32
PersistentKeepalive = 25
```

`AllowedIPs` telefonu ogranicza tunel do adresu VPN hosta; nie przekierowuje całego Internetu przez dom. Przy zmiennym prefiksie zastąp literał IPv6 nazwą DNS z aktualizowanym AAAA. Włącz tunel i sprawdź `sudo wg show` po połączeniu z telefonu:

```bash
sudo chmod 600 /etc/wireguard/wg0.conf
sudo systemctl enable --now wg-quick@wg0
sudo wg show
```

Do API na telefonie ustaw prosty przekaźnik TCP z adresu WireGuard do lokalnej Ollamy. Socket jest przypięty zarazem do `10.77.50.1` i interfejsu `wg0` (`SO_BINDTODEVICE`), więc nie nasłuchuje na `br-home`. Zainstaluj `socat` i utwórz `/etc/systemd/system/ollama-wg-proxy.service`:

```bash
sudo apt install socat
sudo systemctl edit --force --full ollama-wg-proxy.service
```

```ini
[Unit]
Description=Ollama API only on WireGuard
Requires=wg-quick@wg0.service ollama.service
After=wg-quick@wg0.service ollama.service

[Service]
ExecStart=/usr/bin/socat TCP4-LISTEN:11434,bind=10.77.50.1,so-bindtodevice=wg0,reuseaddr,fork TCP4:127.0.0.1:11434
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ollama-wg-proxy.service
sudo systemctl status ollama-wg-proxy.service --no-pager
```

Po połączeniu VPN otwórz na telefonie `http://10.77.50.1:11434/api/tags` lub ustaw ten adres API w prywatnym kliencie Ollamy. HTTP biegnie wewnątrz szyfrowanego tunelu WireGuard; nie używaj tego adresu bez VPN. Jeśli proxy nie startuje, sprawdź `journalctl -u ollama-wg-proxy.service -e`, `sudo wg show` i `ss -ltnp | grep 11434`. [Opcję `so-bindtodevice` opisuje podręcznik socat](https://man7.org/linux/man-pages/man1/socat.1.html). Nie ustawiaj `OLLAMA_HOST=0.0.0.0:11434`. Jeżeli celem jest VPN do **laboratorium OPNsense**, jego własny serwer WireGuard też wymaga osiągalnego WAN/portu przekazanego przez Play, osobnych reguł WAN i tunelu oraz działa tylko podczas pracy VM; patrz [instrukcja OPNsense Road Warrior](https://docs.opnsense.org/manual/how-tos/wireguard-client.html).

## Kiedy warto zmienić architekturę

Jeśli OPNsense ma naprawdę przejąć cały dom i VPN ma działać także podczas Windows, przenieś go na osobne urządzenie 24/7. Minimalny logiczny układ to `Play ONT/router → WAN OPNsense → LAN OPNsense → switch/AP → dom`. Zależnie od modelu Play może być potrzebny bridge mode, DMZ lub podwójny NAT; żadnej z tych opcji nie można tu potwierdzić bez modelu i warunków usługi. Dwa fizyczne interfejsy urządzenia OPNsense ułatwiają niezależny WAN/LAN. Gdy ma tylko jeden interfejs, zarządzalny switch z dwoma VLAN-ami rozdziela WAN i LAN na jednym kablu (router-on-a-stick); trzeba osobno skonfigurować tagowane porty i zabezpieczyć port WAN przed przeciekiem do LAN. Tania karta PCIe z natywnym, stabilnym sterownikiem jest zwykle lepsza jako stały port routera niż adapter USB, który może zmieniać identyfikację lub odłączać się. Dobór konkretnego modelu i ceny wymaga sprawdzenia wolnego slotu, chipsetu i aktualnego rynku. **Na obecnym komputerze z dual bootem zakup samej drugiej karty nie spełni wymagania ciągłości.**

## Test odbiorczy

1. Wyłącz Ubuntu i uruchom Windows. Telefon oraz inne urządzenia domowe nadal mają Internet po Wi-Fi/LAN Play.
2. Uruchom Ubuntu. `br-home` otrzymuje adres z Play, `br-lab` ma wyłącznie `10.77.10.2/24`, OPNsense ma WAN z Play i LAN `10.77.10.1/24`.
3. VM laboratoryjna uzyskuje adres z OPNsense; po zatrzymaniu OPNsense traci Internet, podczas gdy dom pozostaje online.
4. `rocminfo` widzi RX 9070 XT/`gfx1201`, a `ollama ps` pokazuje GPU podczas pracy `qwen3:4b`.
5. Z telefonu poza domowym Wi-Fi działa prywatny adres Tailscale Serve **albo** potwierdzony tunel WireGuard. Publiczny adres Play i port `11434` nie dają bezpośredniego dostępu do API.

Granica wariantu bez laptopa jest zamierzona: ciągłość Internetu domu zapewnia urządzenie Play, zaś OPNsense, laboratorium, VPN na Ubuntu i lokalne AI są dostępne tylko wtedy, gdy komputer działa pod Linuxem. Aby przejść na laptop jako główny router, trzeba potwierdzić jego CPU/RAM/dysk/porty, możliwość pracy 24/7, dostępny punkt Wi-Fi za nim oraz model urządzenia Play. Od tych danych zależą fizyczne podłączenie, koszt dodatkowej karty/switcha i sposób obsługi IPv6.
