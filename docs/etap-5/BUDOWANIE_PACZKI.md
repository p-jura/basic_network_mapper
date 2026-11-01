# Odtworzenie paczki kandydata

Użyj Python 3.13 i przygotowanego venv projektu. Skrypt build_bundle.py korzysta z istniejącego packaging (biblioteka jest już zależnością), nie pobiera plików. Wejścia muszą być poza repozytorium: dokładne koła, źródła, licencje i jawny license-review.json. Nie dołączaj ENV, profili operatora, baz ani eksportów.

```sh
./.venv/bin/python packaging/build_bundle.py \
  --wheelhouse /lokalny/wheels-macos \
  --output /lokalny/nowy-wynik \
  --platform macos-arm64 --repo . \
  --licenses /lokalny/licenses --sources /lokalny/sources \
  --examples examples/snapshots --review /lokalny/license-review.json \
  --provenance /lokalny/provenance.json \
  --commit COMMIT_BAZY --tree-state dirty
```

Windows: osobny wheelhouse i --platform windows-x64. Builder sprawdza docelowe markery zależności niezależnie od OS gospodarza, a pip sprawdza pełny zestaw bez zainstalowanych pakietów i bez indeksu. Nie jest to odbiór wykonywania Windows. Pliki lock z konkretnego kandydata są w packaging/macos-arm64 i packaging/windows-x64. Przy innej zawartości zmieni się manifest i suma; nie nazywaj nowego pliku tą samą odebraną paczką bez powtórnej weryfikacji.

Własny wheel buduj w kopii zawierającej wyłącznie src, pyproject.toml i LICENSE, z istniejącym setuptools, przez pip wheel --no-index --no-deps --no-build-isolation. Sprawdź SQL/CSS i wersje metadanych. Dash-cytoscape 1.0.2 wymagał lokalnego build z oficjalnego sdist; provenance kandydata zawiera URL/hash i opis metody. Nie wymieniaj go na inny numer tylko z powodu braku binarnego koła.

Zachowaj pierwotne materiały w razie zastąpienia. Wyniki buildera mają status wewnętrznego kandydata; skrypt nie potwierdza praw do każdego komponentu i nie publikuje wydania. Fizyczne próby, materiały i końcowa akceptacja pozostają według karty.

Mechanizmy: [pip — hashe i wyłącznie koła](https://pip.pypa.io/en/stable/topics/secure-installs/), [pip download — platforma/ABI](https://pip.pypa.io/en/stable/cli/pip_download/), [Python — venv tworzy się w miejscu docelowym](https://docs.python.org/3.13/library/venv.html).
