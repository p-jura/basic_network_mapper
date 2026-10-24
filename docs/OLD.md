# Rejestr elementów odłożonych do old

Zgodnie z ustaleniem z 24 października 2026 r. zbędne lub zastąpione elementy najpierw odkładamy do `old/RRRR-MM-DD/<poprzednia-ścieżka>`. Usunięcie pozostaje częścią końcowych porządków po zakończeniu projektu. Zasady pracy zapisano w [AGENTS.md](../AGENTS.md).

`old/` jest tymczasowym miejscem wycofanych plików, a `docs/archiwum/` zawiera historyczną dokumentację do wglądu. Aplikacja nie powinna zależeć od plików w `old/`. Nie odkładamy tam sekretów ani prywatnych danych sieciowych.

Poniższe elementy zastąpiono i zachowano do końcowych porządków.

| Data | Poprzednia ścieżka | Ścieżka w old | Powód / zamiennik |
|---|---|---|---|
| 2026-10-24 | `docs/licencje/LICENSE.MIT.template.txt` | [old/2026-10-24/docs/licencje/LICENSE.MIT.template.txt](../old/2026-10-24/docs/licencje/LICENSE.MIT.template.txt) | Szablon z nieuzupełnionym polem uprawnionego zastąpiono podpisaną [licencją MIT](../LICENSE). Oryginalną zawartość zachowano bez zmian; aktywne odwołania prowadzą do `LICENSE`. |
