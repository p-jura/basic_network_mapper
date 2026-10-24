# Etap 3 — topologia, pewność przypisań i historia

Data: 23 października 2026 r. Status: **zaimplementowany; odbiór techniczny offline zakończony, wynik do zatwierdzenia**.

Etap 2 zatwierdzono w rozmowie słowami „Zatwierdzam wynik etapu 2”. Podstawa: [plan główny](../PLAN_STARTOWY.md), [karta decyzji](KARTA_ETAP_0.md) i [raport odbioru](../etap-2/ODBIOR_2026-10-23.md). Zatwierdzenie dotyczy przedstawionego wyniku z jawnymi ograniczeniami: rzeczywiste SNMP/SSH i Windows pozostają niezweryfikowane. Następnie użytkownik zatwierdził opisany Etap 3 słowami „zatwierdzam koduj”.

## 1. Rezultat

Z zapisanych snapshotów powstaje graf urządzeń/segmentów, przypisania portów z uzasadnieniem oraz historia zmian. Cały silnik działa offline, bez uruchamiania kolektorów. Własne reguły domenowe wykorzystują istniejące operacje grafowe NetworkX; nie dodajemy nowego produktu mapowania, usług ani CI/CD.

| Wejście | Oczekiwany wynik |
|---|---|
| Podstawowy LAN bez SNMP/SSH | Segment logiczny, endpointy IPv4/MAC, źródła i świeżość; port/VLAN pozostaje nieustalony |
| Snapshot ARP/FDB/VLAN/IF/LLDP | Infrastruktura, sąsiedztwo LLDP i kandydaci podłączenia hostów zgodnie z kontekstem oraz czasem |
| Kolejne porównywalne cykle | Historia obserwacji, powrotu i potwierdzonych zmian portu; braki/konflikty pokazane oddzielnie |

Pełny panel, filtry interaktywne i jego integracja pozostają Etapem 4. Wyniki Etapu 3 można sprawdzić przez CLI oraz JSON i prosty podgląd grafu. Nie uzależniamy odbioru reguł od dostępności zarządzalnego switcha — korzystamy z kontrolowanych snapshotów, a ograniczenia sprzętowe pozostają jawne.

## 2. Kolejność pracy

| Krok | Praca | Wynik |
|---|---|---|
| 3.1 | Kontrakt grafu i tożsamości | Rodzaje węzłów/relacji, stabilne identyfikatory w projekcie, dowody |
| 3.2 | Podstawowa mapa logiczna | Poprawny obraz istniejącego snapshotu LAN bez zgadywania kabli |
| 3.3 | Korelacja infrastruktury i portów | ARP/FDB/VLAN/IF/LLDP, uplinki i lista kandydatów |
| 3.4 | Confidence i ostrzeżenia | Deterministyczne poziomy z powodami, konflikty i niepełność |
| 3.5 | Trwałe wyniki i historia | Migracja bazy, porównania cykli, idempotencja przeliczenia |
| 3.6 | Odbiór offline | Krytyczne przypadki, rzeczywisty snapshot bez nowego skanu, raport |

Szacunek: **3–4 dni pracy** dla podstawowego zakresu i przygotowanych fixture'ów. Nowe warianty producentów, pełna identyfikacja MLAG/VRF i nieznane parsery nie są ukrytym dodatkiem do tego terminu.

## 3. Model grafu i tożsamości

Graf zawiera węzły segmentów, endpointów, urządzeń zarządzających i sąsiadów poznanych z LLDP. Każdy ma `project_id`, własny ID, dostępne IP/MAC/nazwy, źródła, czasy oraz stan pewności klasyfikacji. Brama z konfiguracji systemu jest oznaczona jako „brama według trasy”, jeśli brak dowodu odpowiedzi.

Relacje rozdzielamy według znaczenia:

- `logical_membership`: obserwowany endpoint należy do zakresu logicznego; nie jest to kabel do routera;
- `lldp_adjacency`: sąsiedztwo potwierdzone odczytem LLDP, z identyfikatorami i dostępnym mapowaniem portów;
- `attachment_candidate`: kandydat portu/urządzenia pośredniczącego;
- `attachment`: przypisanie spełniające uzgodnione reguły, nadal z poziomem pewności i ograniczeniami.

Identyczne IP w innych projektach, VRF lub rozpoznanych segmentach nie łączą obiektów. Nazwa, OUI, `sysObjectID` i adres zarządzający nie są samodzielnym dowodem tożsamości fizycznego urządzenia. `collection_target` z Etapu 2 jest punktem odczytu, nie automatycznie jednym fizycznym chassis.

MAC w zgodnym segmencie i czasie pomaga dopasować interfejs między źródłami. Wiele jednoczesnych IP z jednym MAC bez dodatkowego dowodu może oznaczać proxy ARP lub współdzielenie; zachowujemy kandydaturę, nie scalamy wszystkich w jeden fizyczny komputer. Endpoint bez MAC ma tożsamość prowizoryczną. Zmiana DHCP nie może automatycznie przenieść historii poprzedniego urządzenia na nowego właściciela IP.

Dla wielu IP/MAC jednego urządzenia dopuszczamy powiązanie po dodatkowych zgodnych dowodach. Przy ich braku jawnie pozostaje nierozstrzygnięte. Stabilny rejestr ID ma być ograniczony do projektu i nie może zmieniać oryginalnych obserwacji.

## 4. Korelacja portów i VLAN-ów

1. Grupuj obserwacje według projektu, źródła, segmentu/kontekstu i czasu. Brak informacji o VRF nie oznacza, że dwa źródła na pewno są w tym samym VRF.
2. Połącz `bridge_port_map` z interfejsem właściwego urządzenia. Nie utożsamiaj bridge portu, `ifIndex` i lokalnego numeru LLDP.
3. Połącz FDB ID z dostępnymi VLAN-ami; współdzielone FDB zachowuje listę możliwości. Nie zastępuj `vlan_id=null` numerem FDB ani PVID-em bez potwierdzenia.
4. Połącz IPv4–MAC z kandydatami FDB w zgodnym kontekście. Wyklucz nieważne wpisy, port 0 i niepotwierdzone mapowanie do fizycznego interfejsu.
5. Zbuduj relacje LLDP tylko z pasujących identyfikatorów i subtype'ów; zdalna nazwa lub adres może być wskazówką, nie wymusza scalenia.
6. Oznacz porty prowadzące do dalszej znanej infrastruktury. MAC widoczny przez taki uplink nie staje się automatycznie bezpośrednim hostem tego portu.
7. Wybierz najbardziej bezpośredniego zgodnego kandydata z wykorzystaniem znanej ścieżki infrastruktury. Liczba MAC-ów i trunk są wskazówkami; minimalna liczba MAC-ów może rozstrzygać dopiero między zgodnymi kandydatami, nie zastępuje dowodu.
8. Przy remisie lub sprzecznych dowodach zachowaj alternatywy. AP, telefon z komputerem, hypervisor i niezarządzalny switch mogą pozostawić granicę „urządzenia za tym portem”, bez rozpoznania dokładnego kabla hosta.

Zatwierdzona reguła: **maksymalnie 5 minut rozbieżności czasów źródeł dla mocnego przypisania**, regulowane. Starsze lub rozciągnięte w czasie źródła pozostają dostępne, ale obniżają pewność i nie dają automatycznie potwierdzonej zmiany portu. Wielogodzinny cykl nie jest jednym atomowym stanem sieci.

LAG, stack i MLAG zachowujemy jako relacje logiczne tylko przy dostępnych dowodach. Sama nazwa `Po1` lub wspólny MAC nie wystarcza do odtworzenia fizycznych członków grupy. Jeśli snapshot tego nie zawiera, wynik jest niepełny; nie dopisujemy nowych odczytów sieciowych do silnika offline.

## 5. Confidence i ostrzeżenia

Proponujemy poziomy `high`, `medium`, `low`, `unknown`, bez pozornej procentowej dokładności. Obiekt wyniku zawiera identyfikatory obserwacji, reguły wspierające, konflikty, źródła nieaktualne/brakujące i listę kandydatów.

- `high`: jednoznaczny, zgodny kandydat przy poprawnych mapowaniach, kontekście i czasie, bez nierozstrzygniętego uplinku lub konfliktu;
- `medium`: kandydat ma dowody, ale brakuje części potwierdzenia, np. kompletnej infrastruktury;
- `low`: słaba lub nieaktualna wskazówka; nie traktujemy jej jako potwierdzonego portu;
- `unknown`: brak podstaw do przypisania albo nierozstrzygnięty konflikt.

Są to oceny przypisania, nie dowód fizycznego kabla. Sama świeża odpowiedź ICMP może potwierdzić odpowiedź hosta, lecz nie podwyższa pewności jego portu.

Ostrzeżenia obejmują: sprzeczne przypisania, wspólny MAC/proxy ARP, brak mapowania portu/VLAN-u, duży odstęp czasu, częściowe źródła, nieznaną agregację, cykl/redundancję i możliwy MAC flapping. Cykl w grafie nie jest dowodem aktywnej pętli. MAC flapping wymaga powtarzalnych zmian między portami w zgodnych kontekstach; dwa stare wpisy z różnych chwil nie wystarczają.

## 6. Historia

Porównujemy zakończone snapshoty dla zgodnego zakresu, interfejsu, kontekstu i zestawu odpowiedzialnych źródeł. Zmiana Wi-Fi/VPN lub zakresu nie staje się masowym zniknięciem hostów. Sam status `coverage_status=complete` nie gwarantuje, że źródło nadaje się do potwierdzania obecności wszystkich urządzeń.

Zdarzenia: pierwsza obserwacja, świeża odpowiedź/powrót, dłuższy brak obserwacji, potwierdzona zmiana portu oraz konflikt. Przy pierwszej obserwacji z cache zaznaczamy pochodzenie; nie opisujemy jej jako nowo podłączonego hosta.

Utrzymujemy wcześniejsze zasady: brak obserwacji po trzech udanych, porównywalnych odczytach właściwego zakresu, obejmujących co najmniej 30 minut. To stan obserwacji, nie pewne odłączenie. Błędy, ucięcia i niedostępne źródła nie zwiększają licznika. Stary cache nie resetuje go jako świeża obecność. Zmiana portu wymaga zgodnych dowodów, nie samej zmiany najlepszego słabego kandydata.

Przeliczenie tego samego snapshotu tymi samymi regułami nie tworzy ponownie zdarzeń. Pochodzenie `imported`/`synthetic` pozostaje widoczne; replay nie jest nowym żywym skanem.

## 7. Zapis i wersjonowanie

Propozycja migracji SQLite do v2: dodać rejestr tożsamości, wyniki topologii i zdarzenia historii, bez zmiany źródłowych obserwacji Etapu 2. Przed migracją wykonujemy backup SQLite; przy błędzie zachowujemy poprzednią bazę.

Wynik topologii wiążemy z wejściowym `snapshot_id` i `rules_version`. Zdarzenia mają unikalny klucz wynikający z porównywanych snapshotów, obiektu i rodzaju zmiany. Pełne przeliczenie jest deterministyczne i idempotentne; zmiana reguł ma nową wersję.

Eksport źródłowego snapshotu v1 nadal działa. Graf i historia dostają osobny format eksportu, aby nie złamać importu Etapu 2. Sekrety i rzeczywiste dane LAN nie trafiają do publicznych fixture'ów. Zasady retencji 7 dni snapshotów / 90 dni historii oraz budżet 2 GB pozostają, z ochroną aktualnego wyniku i ciągłości zdarzeń. Nie kasujemy chronionej historii przy okazji migracji.

Przewidywane moduły: `topology/identity.py`, `topology/engine.py`, `topology/confidence.py`, `topology/history.py`, mała migracja i adapter CLI. Zakres zatwierdzono 23 października 2026 r.

## 8. Odbiór i minimalne sprawdzenia

| Przypadek | Wymagany wynik |
|---|---|
| Zwykły LAN bez SNMP | Poprawne endpointy i segment, brak wymyślonego portu/VLAN-u |
| Jeden host widoczny na switchu dostępowym i uplinku | Zgodny kandydat przy liściu, zachowane dowody z uplinku |
| Bridge port inny od ifIndex; współdzielone FDB | Właściwe mapowanie lub jawna niejednoznaczność VLAN-u |
| Konflikt portów, stary cache i źródła z odległych chwil | Alternatywy i obniżenie pewności, bez fałszywej zmiany portu |
| Identyczne IP w innych projektach/VRF; wspólny MAC | Brak nieuprawnionego scalenia |
| Awaria switcha, częściowy cykl lub zmiana zakresu | Brak masowych zdarzeń zniknięcia |
| Trzy właściwe cykle i co najmniej 30 min | Dłuższy brak obserwacji zgodnie z regułą, bez deklaracji odłączenia |
| Powtórne przeliczenie i restart | Te same ID/wynik, brak duplikacji zdarzeń, poprawny odczyt |
| Cykl grafu lub zmiany FDB w czasie | Rozróżnienie redundancji, konfliktu i podejrzenia flappingu |

Wystarczy mały zestaw krytycznych fixture'ów, bez CI/CD i wielkiej macierzy. Rzeczywisty snapshot z Etapu 2 przeliczymy lokalnie bez nowych sond; jego prywatna adresacja nie trafi do repozytorium. Wynik SNMP/SSH na próbkach nie zostanie nazwany potwierdzeniem na sprzęcie.

## 9. Kryterium zakończenia i decyzje

Etap kończy się, gdy działa podstawowa mapa logiczna, korelacja na kontrolowanej topologii, jawne confidence/konflikty, trwała historia i idempotentny replay. Raport podaje użyte dane, reguły, testy, ograniczenia oraz wynik migracji. Przed Etapem 4 przedstawiamy wynik do zatwierdzenia.

Do zatwierdzenia teraz: opisany zakres, jakościowe poziomy confidence, propozycja okna 5 minut i migracja bazy do v2 z trzema obszarami danych pochodnych. Nie otwieramy ponownie zatwierdzonego stosu, IPv4, trybu tylko do odczytu i braku CI/CD. Plan nie upoważnia do kolejnego aktywnego skanu.

## 10. Wykonanie

Wersja 0.3.0 realizuje opisany zakres. Przeszło 26 testów krytycznych, migracja v1→v2, replay i przeliczenie rzeczywistego snapshotu LAN bez nowych sond. Szczegóły: [raport](../etap-3/RAPORT_ETAP_3.md) i [poradnik uruchomienia](ETAP_3_URUCHOMIENIE_I_ODBIOR.md). Wynik nie jest jeszcze odbiorem użytkownika ani rozpoczęciem Etapu 4.

Implementacja wybiera konserwatywny wariant przy brakach: nieznany kontekst pozostaje osobny dla punktu odczytu; cache bez wieku obniża confidence; wiele nierozstrzygniętych portów pozostaje kandydaturami. Liczba MAC-ów nie rozstrzyga sama. Automatyczny licznik braku świeżej odpowiedzi dotyczy hostów wcześniej odpowiadających ICMP, w identycznym zbiorze celów i przy kompletnym cyklu. Nie wyprowadza zniknięcia z samej pustej FDB/ARP. Podejrzenie flappingu wymaga co najmniej trzech naprzemiennych mocnych zmian w oknie czasowym reguł (domyślnie 300 s).
