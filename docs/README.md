# Dokumentacja mappera sieci

Aktualny produkt to lokalny mapper Python **0.4.0**. Etap 4 jest wdrożony, zweryfikowany offline i zatwierdzony przez użytkownika 25 października 2026 r. Plan Etapu 5 jest gotowy do zatwierdzenia przed wdrożeniem. Panel nie uruchamia kolektorów przy starcie. Windows/NTFS i rzeczywiste SNMP/SSH pozostają niewykonanymi odbiorami. Raporty zachowują rozróżnienie prób i deklarowanego zakresu.

## Wymagania i decyzje

- [Wymagania projektu](WYMAGANIA_PROJEKTU.md).
- [Plan wdrożenia i granice etapów](PLAN_STARTOWY.md).
- [Karta ustaleń i historia zatwierdzeń](poradniki/KARTA_ETAP_0.md).
- [ADR-002 — model danych i kolektory](decisions/ADR-002-model-i-kolektory.md).
- [ADR-003 — topologia i historia](decisions/ADR-003-topologia-i-historia.md).
- [ADR-005 — sondy źródłowe, stan sieci i blokady projektów](decisions/ADR-005-bezpieczne-sondy-i-blokady.md).
- [ADR-006 — panel i kontroler zadań](decisions/ADR-006-panel-i-kontroler.md).
- [ADR-007 — pakowanie i odbiór wydania, propozycja](decisions/ADR-007-pakowanie-i-odbior-wydania.md).
- [ADR-004 — wybór MIT i warunki dystrybucji](decisions/ADR-004-licencja-i-dystrybucja.md).
- [Komponenty, licencje i noty](THIRD_PARTY_NOTICES.md); oryginalne teksty pozostają w [third_party_licenses](../third_party_licenses/).
- [MIT własnych elementów projektu — Pawel Juroszek (FL Development)](../LICENSE) i [stan prawny oraz warunki wydania](licencje/STAN_PRAWNY_I_DYSTRYBUCJA.md). Licencje bibliotek i zasobów zewnętrznych obowiązują odrębnie.

## Poradniki

| Etap | Zakres | Dokumenty |
|---|---|---|
| 0 | Założenia i karta decyzji | [Ustalenia](poradniki/ETAP_0_USTALENIA.md), [karta](poradniki/KARTA_ETAP_0.md) |
| 1 | Próba komponentów i odkrywanie podstawowe | [Komponenty](poradniki/ETAP_1_PROBA_KOMPONENTOW.md), [odkrywanie bez SNMP/SSH](poradniki/ETAP_1_ODKRYWANIE_PODSTAWOWE.md) |
| 2 | Model danych i kolektory | [Plan](poradniki/ETAP_2_MODEL_DANYCH_I_KOLEKTORY.md), [uruchomienie i odbiór](poradniki/ETAP_2_URUCHOMIENIE_I_ODBIOR.md) |
| 3 | Topologia, confidence i historia | [Plan](poradniki/ETAP_3_TOPOLOGIA_I_HISTORIA.md), [uruchomienie i odbiór](poradniki/ETAP_3_URUCHOMIENIE_I_ODBIOR.md) |
| 3.1 | Poprawki po review | [Plan i uruchomienie](poradniki/ETAP_3_1_POPRAWKI_PO_REVIEW.md), [raport](etap-3-1/RAPORT_ETAP_3_1.md) |
| 4 | Panel i pełny przepływ operatora — zatwierdzony | [Plan](poradniki/ETAP_4_PANEL_I_PRZEPLYW_OPERATORA.md), [uruchomienie i odbiór](poradniki/ETAP_4_URUCHOMIENIE_I_ODBIOR.md), [raport](etap-4/RAPORT_ETAP_4.md) |
| 5 | Odbiór i pakowanie MVP — propozycja | [Plan do zatwierdzenia](poradniki/ETAP_5_ODBIOR_I_PAKOWANIE_MVP.md), [karta prób — niewykonane](etap-5/KARTA_ODBIORU_ETAP_5.md) |

## Raporty i dowody odbioru

- [Etap 1 — raport](etap-1/RAPORT_ETAP_1.md).
- [Etap 2 — raport](etap-2/RAPORT_ETAP_2.md) i [odbiór 23 października 2026](etap-2/ODBIOR_2026-10-23.md).
- [Etap 4 — rzeczywisty odbiór LAN: kolekcja OK, dwa błędy mapy](etap-4/ODBIOR_LAN_2026-10-25.md).
- [Etap 4 — raport](etap-4/RAPORT_ETAP_4.md), [dowody zbiorcze](etap-4/ODBIOR_2026-10-25.json) i [syntetyczny panel](etap-4/PANEL_ETAP_4.png).
- [Etap 3 — raport](etap-3/RAPORT_ETAP_3.md) i [podgląd przykładu](etap-3/PODGLAD_ETAP_3.jpg).

Raporty rozróżniają testy syntetyczne, odczyty rzeczywiste i obszary niezweryfikowane. W repozytorium są wyłącznie przykłady; prywatne adresacje, poświadczenia, bazy i eksporty odbioru pozostają poza nim. Nie dodawaj rzeczywistych danych sieci przy porządkowaniu dokumentów.

## Niezależne review i działania naprawcze

[Weryfikacja review z 24 października 2026 r.](reviews/REVIEW_2026-10-24.md) zawiera ocenę wszystkich uwag, dowody, pokrycie planem i propozycję krótkiego kroku 3.1 przed integracją aktywnej kolekcji z panelem. Analiza poprzedziła autoryzację i wdrożenie 3.1. Aktualny wynik opisuje [raport poprawek](etap-3-1/RAPORT_ETAP_3_1.md); analiza 0.3.0 pozostaje historycznym punktem odniesienia.

## Prototypy komponentów

Katalog `prototypes/` zawiera wcześniejsze próby Etapu 1, zachowane oddzielnie od właściwej aplikacji w `src/mapper/`:

- [Panel offline](../prototypes/tools/probe_panel.py) i [syntetyczny snapshot](../prototypes/examples/snapshots/lab-001.json).
- [Próba SQLite i NetworkX](../prototypes/tools/probe_storage.py).
- [Pomocniczy launcher](../prototypes/tools/run_probe.py); pliki `probe_snmp.py` i `probe_ssh.py` pozostają pustymi szablonami, więc launcher nie potwierdza działania tych protokołów.

Aktualne kolektory i CLI są w `src/mapper/`. Katalog prototypów przemianowano z wcześniejszego `probie` 24 października 2026 r.; zawartość skryptów i snapshotu zachowano.

## Archiwum

Te dokumenty dotyczą odrębnych wcześniejszych prac i nie zastępują planu mappera Python:

- Flutter/Dart: [plan MVP](archiwum/flutter-dart/PLAN_APLIKACJI_TOPOLOGII_MVP.md), [poradnik Etapów 0–1](archiwum/flutter-dart/PORADNIK_ETAP_0_1.md).
- Laboratorium: [przewodnik](archiwum/laboratorium/PRZEWODNIK_WDROZENIA.md), [plan sprzętowy](archiwum/laboratorium/PLAN_SPRZETOWY_150-400_ZL.md), [prompt](archiwum/laboratorium/PROMPT_WDROZENIOWY.md), [analiza promptu](archiwum/laboratorium/ANALIZA_PROMPTU.md).

- [Rejestr elementów odłożonych do old](OLD.md).

## Układ i zasady ścieżek

```text
docs/
  README.md
  WYMAGANIA_PROJEKTU.md
  PLAN_STARTOWY.md
  THIRD_PARTY_NOTICES.md
  poradniki/
  decisions/
  licencje/
  etap-1/
  etap-2/
  etap-3/
  etap-3-1/
  etap-4/
  etap-5/
  reviews/
  licencje/
  archiwum/
    flutter-dart/
    laboratorium/
```

Odnośniki Markdown są względne wobec danego dokumentu. Polecenia i ścieżki kodu w przykładach odnoszą się do katalogu głównego repozytorium, chyba że podano inaczej. `README.md` i `AGENTS.md` w głównym katalogu są punktami wejścia, a pliki upstream w `third_party_licenses/` zachowują oryginalne lokalizacje i treść. `.gitattributes` wyłącza normalizację oraz kontrolę białych znaków tylko dla `third_party_licenses/`, aby zachować oryginalne teksty upstream.

Główny katalog roboczy od 22 października 2026 r.: `/Users/paweljuroszek/all_projects/other/Maper sieci`. Wcześniejszy: `/Users/paweljuroszek/Documents/ChatGPT/Home Lan`; poprzednich kopii nie modyfikujemy. Układ dokumentacji uporządkowano 24 października 2026 r. przed pierwszym commitem; zmiana nie zatwierdza nowego etapu ani nie zmienia wymagań produktu.
