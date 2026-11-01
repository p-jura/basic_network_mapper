# ADR-008 — interpretacja lokalnego ARP i wersjonowanie poprawek LAN

Data: 2026-10-25. Status: przyjęty do wdrożenia poleceniem użytkownika „ok dzialaj wedlug planu”. Zakres: LAN-01/LAN-02/LAN-03 z [odbioru LAN](../etap-4/ODBIOR_LAN_2026-10-25.md), przed pakowaniem Etapu 5.

## Decyzje przed kodem

1. Reguły 2, aplikacja 0.4.1. MAC zerowy, rozgłoszeniowy i grupowy nie identyfikuje endpointu w ARP ani FDB. W lokalnym kontekście maska zaobserwowanego interfejsu /0–/30 wyklucza adres sieci i broadcast; wybrany CIDR sond może być węższy i sam nie dowodzi maski. Bez dowodu maski zachowujemy wpis unicast; /31 i /32 zachowują wszystkie adresy. Nigdy nie odrzucamy adresu tylko z powodu końcówki .255. Dla zarządzającego ARP bez maski nie zgadujemy granic podsieci. Surowe obserwacje pozostają niezmienione, także te wykluczone z mapy.
2. Wybrane local_interface tworzymy przed interpretacją sąsiadów, w dokładnym kontekście projektu/interfejsu/zakresu. Cache dla tego samego lokalnego IPv4 staje się dowodem przy lokalnym interfejsie, nie drugim hostem. MAC z cache jest osobnym `neighbor_mac_claims`, nigdy zweryfikowanym MAC lokalnej karty. Ostrzeżenie LOCAL_IP_NEIGHBOR_CLAIM ujawnia brak niezależnego potwierdzenia, a wiele różnych MAC zachowuje IP_MAC_CONFLICT. Nie scala to innych kontekstów ani nie pozwala przypisywać portu lokalnemu interfejsowi z niezweryfikowanego cache.
3. Nowy wynik i historia mają `2:skew=...`; build odtwarza chronologicznie zachowane źródła, osobno od reguł 1. Nie porównuje granicy wersji jako zniknięcia/przeniesienia hostów. Stare grafy i zdarzenia pozostają w bazie. Domyślna historia oraz panel pokazują aktualne reguły; CLI nadal pozwala jawnie wybrać starą wersję. Nowa historia zaczyna się od najstarszego zachowanego snapshotu, nie od usuniętych źródeł. Bez migracji źródeł v1/SQLite v2.
4. Formularz ładuje zapisany wybór razem z jego opcją listy; bez automatycznego odczytu sieci. Osobny przycisk odczytu lokalnych interfejsów zachowuje wybór również, gdy karta jest niedostępna; aktualność sprawdza preview. Zapis/start/preview wymagają formularza załadowanego dla wybranego projektu. Niekompletna para interfejs/CIDR daje błąd przed zapisem; świadome wyczyszczenie obu pól wyłącza podstawową ścieżkę.

## Odbiór i granice

Małe testy: grupowe/zerowe MAC w ARP i FDB, prefiksy /23,/24,/31,/32, własny IP i konflikt, izolacja kontekstów, niezmienność źródeł i starego wyniku, ponowny build bez duplikacji zdarzeń, ładowanie/podgląd formularza bez sond. Następnie replay prywatnego snapshotu LAN i prawdziwa przeglądarka z syntetycznym adapterem. Brak nowych skanów, zależności, CI/CD i deklaracji odbioru Windows/SNMP/SSH.
