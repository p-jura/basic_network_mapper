# ADR-003 — topologia i historia offline

Data: 2026-10-23. Status: zatwierdzone przez użytkownika („zatwierdzam koduj”).

Podstawa: poradnik Etapu 3. Zatwierdzono zakres, confidence high/medium/low/unknown, regulowane okno 300 s oraz migrację SQLite v2 z backupem przed zmianą. Nie upoważnia to do nowego skanu.

Źródłowe snapshoty i eksport/import pozostają v1. Dodajemy rejestr tożsamości, wyniki grafu i niezależną historię (90 dni). Rejestr ID jest izolowany per projekt i kontekst. IP ani nazwa nie są identyfikatorem chassis. Relacje logiczne, LLDP, kandydatury i przypisania mają osobne typy i dowody. Brak danych nie oznacza odłączenia.

NetworkX (BSD-3-Clause, zainstalowana wersja 3.7) dostarcza algorytmy grafowe. Podgląd korzysta z istniejącego Dash/dash-cytoscape, bez CDN, kolekcji ani pełnego panelu Etapu 4. Bez nowych usług i CI/CD.

Historię budujemy chronologicznie. Klucz reguł obejmuje wersję i okno czasowe; ponowne przeliczenie nie dopisuje zdarzeń. Po retencji zachowujemy stan porównawczy w ostatnim wyniku. Źródła częściowe lub nieporównywalne nie zwiększają licznika braku obserwacji. Trzy poprawne próby obejmujące przynajmniej 30 minut oznaczają dłuższy brak obserwacji, nigdy pewne odłączenie.
