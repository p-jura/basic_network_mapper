# Plan sprzętowy 150–400 zł dla domowej sieci

> Materiał historyczny: laboratorium domowe i sprzęt. Nie określa bieżącego zakresu mappera Python. Aktualna dokumentacja: [spis treści](../../README.md).

Stan: 10 października 2026 r. Budżet 150–400 zł, sprzęt używany jest akceptowany. Dostępne są: komputer Ryzen/Radeon z dual bootem, laptop prawdopodobnie i3 2. generacji z 2 GB RAM, urządzenie Play/UPC o nieznanym modelu oraz osobny router/AP Wi-Fi. Nie ma switcha VLAN. Łącze Play: 300 Mb/s i automatycznie przydzielany IPv6.

## Rekomendacja

**Najpierw sprawdź model laptopa i AP; dopiero potem kup części.** Najtańszą próbą jest rozbudowa laptopa, jeżeli obsługuje co najmniej 4 GB RAM, ma wbudowany port **Gigabit Ethernet** oraz USB 3. Za najlepszy docelowy zakup w tym budżecie uznaję jednak **kompletny używany terminal z 8 GB RAM, SSD i dwoma sprawdzonymi portami Gigabit Ethernet**, szczególnie gdy oba NIC są wewnętrzne PCIe — ma mniej podatnych na rozłączenie elementów niż stary laptop z adapterem USB. Kup go tylko po weryfikacji podzespołów i ceny całego zestawu. Jeśli nie znajdziesz takiej oferty do 400 zł, rozbuduj laptop po sprawdzeniu zgodności; gdy i to odpada, pozostaw Play jako bramę, a OPNsense uruchom jako laboratorium na komputerze głównym. **Nie kupuj adaptera ani RAM w ciemno.**

OPNsense podaje minimum 3 GB RAM, a dla zakresu 151–350 Mb/s „rozsądna” konfiguracja to 4 GB RAM i 40 GB SSD. 2 GB obecnego laptopa nie spełnia tej granicy ([OPNsense Hardware](https://docs.opnsense.org/manual/hardware.html)).

| Wariant | Koszt zakupów orientacyjnie | Co zyskujesz | Główny warunek/ograniczenie |
|---|---:|---|---|
| Rozbudowa laptopa | ok. **90–160 zł** za RAM + drugi Ethernet; opcjonalny SSD podnosi koszt | najniższy koszt startu, wbudowana zdrowa bateria może przetrwać krótki zanik zasilania | musi mieć RAM rozbudowywalny, USB 3 i stabilną pracę 24/7; USB NIC trzeba testować |
| Kompletny używany terminal/router x86 | **około 220–400 zł**, tylko jeśli oferta zawiera zasilacz, SSD, RAM i 2 działające porty Gigabit | zwykle wygodniejsza praca ciągła i mniej elementów laptopowych | trzeba potwierdzić chipsety obu NIC, nie ufać samej frazie „Dual LAN” |
| Nowy N100 z 2–4 portami LAN | dziś wyraźnie ponad 400 zł | większy zapas pod IDS/VPN i przyszłe 2,5 Gb/s | poza tym budżetem; zakup można odłożyć |

Powyższe kwoty to **orientacyjne ceny ofertowe**, nie gwarancja dostępności. Przykłady sprawdzone przy tworzeniu planu: moduły 4 GB DDR3 SO-DIMM bywają oferowane za około [49 zł](https://kupcochcesz.pl/pamiec-ram-ddr3-4gb-pc3-12800-1600mhz-cl11) lub [65 zł](https://www.apollo.pl/produkt/ddr3-sodimm-4gb1600-cl11%2C4389.html), a adapter USB 3 Gigabit opisywany jako RTL8153 za [36,90 zł](https://interlook.pl/product-pol-2696-Karta-sieciowa-adapter-USB-3-0-Gigabit-Ethernet-10-100-1000-Mbps-RTL8153-S3J-8153.html). Konkretna pamięć musi pasować do laptopa: DDR3 i DDR3L, napięcie, liczba slotów oraz limit BIOS mogą się różnić. Sterownik `ure` FreeBSD wymienia RTL8153, ale zgodność konkretnego adaptera i stabilność 300 Mb/s należy potwierdzić na OPNsense ([FreeBSD `ure(4)`](https://man.freebsd.org/cgi/man.cgi?apropos=0&manpath=FreeBSD+13.5-RELEASE&query=ure&sektion=4)).

Przykładowa używana oferta deklaruje [HP t620, 8 GB RAM, SSD 120 GB, 2× LAN za 220 zł](https://www.olx.pl/d/oferta/terminal-hp-t620-8gb-ram-120gb-ssd-dual-lan-home-assistant-CID99-ID1bYwS6.html?search_reason=search%7Corganic). To **przykład ceny, nie zweryfikowany wybór sprzętu**: przed zakupem poproś o zdjęcie obu gniazd RJ45, identyfikatory kart z `lspci -nn`/`lsusb` albo `pciconf -lv` w OPNsense, zdjęcie zasilacza i informację o możliwości zwrotu. Drugi port może być wewnętrznym adapterem USB i nie dawać przewagi nad rozbudowanym laptopem. Tanie terminale bez dysku, zasilacza lub risera PCIe mogą po skompletowaniu przekroczyć 400 zł. Nowy N100 z dwoma LAN jest oferowany przykładowo za [1522 zł](https://www.mobilator.pl/minipc--przemyslowe/z-procesorem-intel-atom); dziś nie wnosi korzyści proporcjonalnej do tego budżetu i łącza 300 Mb/s.

Kompletowanie używanego terminala z części rzadko jest tu okazją: sama używana czteroportowa karta Intel i350 w przykładowej ofercie kosztuje około [244 zł](https://shoplet.pl/karty-sieciowe/24642-karta-sieciowa-intelu-i350-t4-high-profile-4x-ethernet.html?download_pdf=), a potrzebne mogą być jeszcze riser, SSD i zasilacz. Porównuj **sumę** z ceną gotowego urządzenia.

## Co dokładnie kupić w pierwszym wariancie

1. **RAM:** docelowo 4 GB minimum, 8 GB jeśli laptop obsługuje tę pojemność i cena jest rozsądna. Najpierw odczytaj model i aktualne moduły. Nie zakładaj, że „2 GB” oznacza wolny slot; mogą być dwa moduły po 1 GB.
2. **Drugi Ethernet:** jeśli laptop ma USB 3, adapter USB-A 3 Gigabit na chipset RTL8153 jest tanim kandydatem do testu. Wbudowany Ethernet przeznacz na LAN, a USB na WAN: ewentualne rozłączenie adaptera powinno przynajmniej zostawić dostęp administracyjny z LAN. Sprawdź po restarcie nazwy interfejsów i nie przypisuj WAN/LAN wyłącznie według kolejności wykrycia. Jeśli laptop ma tylko USB 2 lub wbudowany Ethernet 100 Mb/s, tego wariantu nie wybieraj dla łącza 300 Mb/s.
3. **Dysk:** jeśli jest sprawny SSD ≥40 GB, wykorzystaj go. Stary HDD można użyć do próby, ale przed pracą 24/7 sprawdź SMART i miej kopię konfiguracji; zakup nowego SSD zwiększa koszt. Przykładowy 128 GB SATA kosztuje około [120–160 zł](https://www.x-kom.pl/p/575329-dysk-ssd-patriot-128gb-25-sata-ssd-p210.html), więc wariant z nowym dyskiem może przekroczyć najtańszy używany terminal.
4. **Wi-Fi i porty LAN:** użyj posiadanego routera w trybie AP/bridge za LAN OPNsense, z wyłączonym DHCP/NAT. Potwierdź, że jego porty są **gigabitowe**; model 100 Mb/s ograniczy komputer i Wi-Fi do około 100 Mb/s. Jeśli portów LAN za OPNsense zabraknie, dołóż później prosty switch 5-portowy Gigabit, np. klasy [TP-Link LS1005G](https://www.tp-link.com/pl/home-networking/soho-switch/ls1005g/). Switch VLAN nie jest potrzebny przy dwóch portach Ethernet routera.

Przed zamówieniem wykonaj na laptopie `msinfo32` i sprawdź Menedżer urządzeń w Windows albo — w Linuxie — `lscpu`, `free -h`, `lsusb -t`, `lspci -nn`, `lsblk -o NAME,SIZE,MODEL`. Zanotuj pełny model z naklejki. Na zapasowym routerze/AP sprawdź model, tryb AP oraz czy porty mają 1 Gb/s. Potwierdź w urządzeniu Play, czy możliwy jest bridge mode lub delegacja IPv6 do routera za nim. **Jeśli Play nie przekaże DHCPv6-PD, sama nowa maszyna z OPNsense nie zachowa automatycznie IPv6 w sieci domowej** ([OPNsense IPv6](https://docs.opnsense.org/manual/ipv6.html)).

## Koszt utrzymania i rozwój

Router działa 8760 godzin rocznie. Różnica **10 W zmierzona na gniazdku** to 87,6 kWh rocznie; pomnóż tę wartość przez własną cenę 1 kWh, by porównać stary laptop z terminalem. Przykładowo przy hipotetycznej stawce 1 zł/kWh daje to 87,60 zł rocznie na każde dodatkowe 10 W. Nie zakładaj poboru na podstawie TDP procesora — zmierz całe urządzenie wraz z zasilaczem. Stan baterii laptopa, chłodzenie i automatyczny start po powrocie zasilania też wpływają na niezawodność.

Rozszerzaj sieć etapami. Najpierw dwa porty 1 Gb/s, OPNsense, AP i jeden zakres LAN wystarczą dla 300 Mb/s. Gdy zechcesz osobną sieć gościnną lub IoT, dokup zarządzalny switch **i** sprawdź obsługę VLAN/oddzielnych SSID w AP; sam switch nie rozdzieli Wi-Fi. Gdy łącze wzrośnie ponad 1 Gb/s albo włączysz ciężkie IDS/IPS, rozważ urządzenie N100/N150 z 8 GB RAM, SSD i 2–4 portami Intel 2,5 Gb/s. Wtedy zachowasz konfigurację OPNsense i AP, wymieniając tylko bramę. Lokalna Ollama zostaje na komputerze z Radeonem; jej dostępność 24/7 wymaga osobnej maszyny AI i jest odrębną inwestycją.

## Warunek przełączenia całego domu

Kupione części nie wystarczają same w sobie. Najpierw uruchom OPNsense **za** Play i podłącz jednego klienta testowego za jego LAN. Potwierdź przez kilka dni 300 Mb/s, brak zrywania USB, poprawne wznawianie po zanikach prądu i wymagany poziom IPv6. Zanim przeniesiesz komputer do gier za OPNsense, sprawdź model Play oraz wpływ ewentualnego podwójnego NAT na gry/port forwarding. Jeśli bridge mode lub delegacja prefiksu IPv6 są niedostępne, Play może pozostać główną bramą, a OPNsense obsługiwać wybrane urządzenia lub laboratorium. Szczegółowe etapy i testy są w [przewodniku wdrożenia](PRZEWODNIK_WDROZENIA.md).
