# Analiza i poprawki promptu

> Materiał historyczny: laboratorium domowe i sprzęt. Nie określa bieżącego zakresu mappera Python. Aktualna dokumentacja: [spis treści](../../README.md).

Weryfikacja dokumentacji: 10 października 2026 r. Przygotowano prompt do wygenerowania instrukcji wdrożenia. Nie jest to potwierdzenie kompatybilności konkretnej płyty głównej ani przetestowana konfiguracja opisanego komputera.

Uzupełnienie od użytkownika: **Play, światłowód 300 Mb/s, automatycznie przydzielany IPv6**. Model routera/ONT, prędkość wysyłania, rodzaj IPv4, delegacja prefiksu i osiągalność z Internetu pozostają nieustalone. Automatyczny przydział nie oznacza sam w sobie, że prefiks się zmienia. Aktualny prompt traktuje IPv6 jako element projektu, z weryfikacją rzeczywistych możliwości łącza.

Najważniejszy konflikt to wymaganie natywnego dual-bootu przy routerze działającym w VM na Linuksie. Po uruchomieniu Windowsa środowisko Linux i jego VM nie pracują. Jeśli VM jest jedyną bramą domu, znika routing do Internetu i VPN obsługiwany przez tę VM. Zmiana hypervisora, GRUB-a czy liczby kart Ethernet nie rozwiązuje tej zależności. Trzeba zaakceptować przerwy, pozostawić obecny router jako bramę albo zapewnić stale działające środowisko routera.

| Problem w pierwotnej wersji | Poprawka i jej skutek |
|---|---|
| Router główny, codzienny komputer i dual-boot bez omówienia dostępności | Trzy jawne warianty architektury; wybór przed przełączeniem domu. |
| „Całkowicie wirtualnie” jako możliwy zamiennik fizycznego WAN/LAN | Laboratorium wirtualne oddzielono od routingu całego domu. Jedna karta dla fizycznego WAN i LAN wymaga odpowiedniej infrastruktury VLAN lub innej fizycznej ścieżki. |
| Druga NIC traktowana jako bezwarunkowo konieczna albo zbędna | Porównanie dwóch NIC, jednej NIC ze switchem 802.1Q i jednej NIC dla laboratorium. |
| ROCm i GPU passthrough użyte jak synonimy | Oddzielono backend obliczeniowy od sposobu udostępnienia urządzenia. Usługa/kontener może używać GPU hosta bez VFIO. |
| Obowiązkowa VM AI i „pełna wydajność” bez kontroli sprzętu | Prostsza usługa/kontener jako punkt wyjścia; VM z VFIO jako wariant po kontroli IOMMU, obrazu hosta i resetu GPU. Wydajność wymaga pomiaru. |
| „Najlepszy Linux” bez wersji i wymagań GPU | Ubuntu Desktop LTS z KVM jako preferencja dla komputera codziennego; wybór konkretnego wydania/kernelu oparty o macierz AMD i Ollamę. |
| Nieznany modem/operator potraktowany jak prosty kabel WAN | Dodano bridge/router, DHCP/PPPoE, VLAN ISP, IPv6, CGNAT/DS-Lite oraz zależności IPTV/telefonii. |
| Automatyczny IPv6 mógłby zostać błędnie uznany za gotowy dostęp zdalny | Dla światłowodu Play 300 Mb/s dodano sprawdzenie adresu globalnego, DHCPv6-PD, zapór, DDNS AAAA i dostępu klientów spoza domu. Nie zakłada się CGNAT/DS-Lite ani zmienności prefiksu bez sprawdzenia. |
| Brak roli fizycznego Wi-Fi | Punkt dostępowy i jego połączenie z LAN ujęto w topologii. VM routera sama nie zapewnia domowego Wi-Fi. |
| „Darmowe” utożsamione z „Open Source” | Osobno oznaczono Windows, firmware, SaaS Tailscale i licencje modeli. Koszt energii, sprzętu i publicznego endpointu rozlicza się oddzielnie. |
| Bezpieczne API utożsamione z samym VPN | Dodano adres nasłuchu, reguły hosta, uprawnienia klientów, uwierzytelnianie opcjonalnego UI i sprawdzenie ekspozycji kontenera. |
| Całe bezpieczeństwo przypisane OPNsense | Dodano granicę zaufania do hosta, ruch w tym samym LAN oraz VPN kończący się na hoście, które wymagają ochrony hosta. |
| Brak planu naprawy po utracie łączności | Konsola lokalna, stały adres zarządzania, laboratorium przed migracją, backup i fizyczny powrót do obecnego routera. |
| RAM bez rozróżnienia VM, kontenera i VRAM | Plan 4 GiB router / 12 GiB limit AI / 10 GiB system i pulpit / 6 GiB zapas; osobne rozliczenie VRAM i pomiary obciążenia. |

Preferowany punkt wyjścia to Ubuntu Desktop LTS, KVM/libvirt, OPNsense w VM i Ollama jako usługa lub kontener. Jest to rekomendacja projektowa dla komputera używanego na co dzień, a nie wynik testów tego sprzętu. Zachowuje cel OPNsense jako głównego routera wyłącznie w wariancie z zaakceptowanymi przerwami. Jeśli Internet ma działać podczas grania, najpierw trzeba wybrać pozostałą architekturę.

## Co potwierdzono w źródłach

- Oficjalna dokumentacja Ollamy wymienia RX 9070 XT wśród GPU obsługiwanych pod Linuksem przez ROCm. Nie trzeba z góry zakładać obejść dla niewspieranej karty. Nadal należy dobrać zgodną wersję systemu, sterownika i Ollamy. [Ollama — Hardware support](https://docs.ollama.com/gpu).
- Dokumentacja AMD zawiera RX 9070 XT w macierzy Radeon/ROCm, a macierz ROCm 7.2.1 wskazuje m.in. Ubuntu 24.04.4 Desktop z HWE. Strona informuje o przeniesieniu nowszej dokumentacji do dokumentacji ujednoliconej. Bezpośredni odczyt nowej macierzy podczas tej analizy zakończył się HTTP 429, więc nie potwierdzono najnowszego zestawu wersji. Prompt wymaga ponownej weryfikacji przy przygotowaniu instrukcji; nie wybiera dowolnego „najnowszego Ubuntu”. [AMD — Radeon Linux support matrices](https://rocm.docs.amd.com/projects/radeon-ryzen/en/latest/docs/compatibility/compatibilityrad/native_linux/native_linux_compatibility.html), [AMD — ujednolicona macierz do ponownego sprawdzenia](https://rocm.docs.amd.com/en/latest/compatibility/compatibility-matrix.html).
- Kontener Ollamy dla AMD korzysta z urządzeń `/dev/kfd` i `/dev/dri`. To dostęp kontenera do sterownika hosta, odrębny od przypisania GPU do VM przez VFIO. [Ollama — Docker](https://docs.ollama.com/docker), [Linux — VFIO](https://docs.kernel.org/driver-api/vfio.html).
- Ryzen 7 9800X3D posiada zintegrowaną grafikę Radeon. Możliwość użycia jej jako wyświetlacza hosta wymaga sprawdzenia płyty, wyjść obrazu i ustawień firmware. [AMD — specyfikacja 9800X3D](https://www.amd.com/en/products/processors/desktops/ryzen/9000-series/amd-ryzen-7-9800X3d.html).
- OPNsense podaje minimum 3 GB RAM dla instalacji wirtualnej oraz zalecenia wyłączenia offloadingu. 4 GiB to rozsądny punkt startowy prostego domowego routera; dodatkowe inspekcje ruchu wymagają ponownego doboru zasobów. [OPNsense — instalacja wirtualna](https://docs.opnsense.org/manual/virtuals.html), [OPNsense — dobór sprzętu](https://docs.opnsense.org/manual/hardware.html).
- Lokalny API Ollamy nie wymaga uwierzytelniania; samo udostępnienie portu nie zapewnia kontroli dostępu. [Ollama — Authentication](https://docs.ollama.com/api/authentication).
- Publikowanie portów w Dockerze może omijać reguły UFW. Wdrożenie musi sprawdzić realną ekspozycję usługi i reguły silnika kontenerowego. [Docker — Packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/).
- Tailscale oferuje darmowy plan Personal, ale jego zarządzany serwer koordynacyjny pozostaje własnościowy. Headscale jest niezależną otwartą implementacją, której utrzymanie i osiągalność trzeba zaprojektować. [Tailscale — free plans](https://tailscale.com/docs/reference/free-plans-discounts), [Tailscale — open source](https://tailscale.com/opensource).
- OPNsense dokumentuje zdalny dostęp WireGuard. Adresacja tunelu, `AllowedIPs`, reguły WAN i tunelu są osobnymi elementami konfiguracji. [OPNsense — WireGuard Road Warrior](https://docs.opnsense.org/manual/how-tos/wireguard-client.html).
- Istniejący bridge i domyślny NAT libvirt są różnymi trybami sieci. Prompt wymaga spójnej konfiguracji, aby nie dodać przypadkowo drugiego DHCP lub ścieżki omijającej firewall. [libvirt — Network XML](https://libvirt.org/formatnetwork.html).
- Instalacja obok Windowsa wymaga uwzględnienia BitLocker oraz rzeczywistego układu dysków. Osobne dyski ograniczają zależności rozruchu, ale nie zastępują backupu i klucza odzyskiwania. [Ubuntu — BitLocker during installation](https://ubuntu.com/desktop/docs/en/latest/reference/bitlocker-during-ubuntu-installation/).

## Dane potrzebne do przejścia od promptu do wdrożenia

1. Oczekiwana dostępność Internetu podczas pracy Windowsa i wyłączenia hosta.
2. Model/tryb routera/ONT Play i metoda WAN; rodzaj IPv4, długość/stabilność delegowanego prefiksu IPv6, ruch przychodzący oraz usługi dodatkowe. Operator, światłowód 300 Mb/s i automatyczny przydział IPv6 są już znane.
3. Modele switcha/AP, istniejąca adresacja oraz dostępne porty i okablowanie.
4. Model płyty/NIC, dostępny slot PCIe, działanie iGPU i grupy IOMMU, jeśli wybrano VFIO.
5. Układ dysków, wolne miejsce, UEFI/Secure Boot/BitLocker oraz miejsce na kopie poza hostem.

Gotowy prompt zapisano w `docs/archiwum/laboratorium/PROMPT_WDROZENIOWY.md`. Pytania o środowisko są częścią promptu; nie trzeba znać odpowiedzi, aby użyć go do rozpoczęcia projektowania. Odpowiedzi i testy są konieczne przed rzeczywistym przełączeniem sieci domowej.

## Konsekwencje IPv6 na łączu Play

Play opisuje IPv6 w materiałach pomocy, ale sama nazwa operatora nie ustala parametrów konkretnego światłowodu. Instrukcji dla usług mobilnych lub kablowych nie należy stosować do tego łącza bez potwierdzenia. [Play — informacje o IP i IPv6](https://www.play.pl/pomoc/wsparcie-techniczne/routery-i-modemy/ustawienia-i-funkcje-routerow-i-modemow/konfiguracja-stalego-adresu-ip-i-zmiana-adresacji-dns).

Adres WAN i delegowany prefiks to różne zasoby. OPNsense może potrzebować delegacji, aby zapewnić osobne podsieci IPv6 za routerem; IPv6 działający na obecnym kliencie tego nie potwierdza. Dlatego prompt wymaga kontroli DHCPv6-PD i możliwości routera Play. [OPNsense — IPv6 setup](https://docs.opnsense.org/manual/ipv6.html).

Osiągalny endpoint IPv6 może umożliwić bezpośredni WireGuard także przy ograniczeniach IPv4. Wymaga jednak odpowiedniego routingu i reguł zapór oraz dostępu IPv6 po stronie klienta. Nie jest to jeszcze potwierdzone dla tego łącza. [WireGuard — dokumentacja techniczna](https://www.wireguard.com/papers/wireguard.pdf).

Przy zmiennym adresie potrzebny jest aktualny rekord AAAA i obsługa ponownego rozwiązywania nazwy endpointu przez klienta. Oficjalny projekt udostępnia narzędzie do ponownego ustawiania endpointów z DNS; prompt wymaga sprawdzenia zachowania konkretnego klienta i testu po zmianie adresu. [WireGuard — reresolve-dns](https://github.com/WireGuard/wireguard-tools/blob/master/contrib/reresolve-dns/reresolve-dns.sh).

Zapora IPv6 musi zachować komunikaty konieczne do działania sieci, w tym ICMPv6 Packet Too Big; blokowanie całego ICMPv6 może powodować problemy z łącznością. Jednocześnie API AI i GUI administracyjne mają pozostać niedostępne od strony WAN. [RFC 4890 — filtrowanie ICMPv6](https://www.rfc-editor.org/info/rfc4890/).
