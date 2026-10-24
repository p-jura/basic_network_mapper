# Third-party notices — Etapy 2–3

Stan: 23 października 2026 r. Lista obejmuje zainstalowane zależności wykonawcze pakietu mapper-sieci i ich zależności pośrednie. Mapper importuje je dynamicznie, bez modyfikacji. Nie dołączamy triali, komercyjnych edycji, sterowników przechwytywania ani usługi SaaS. Nie jest to pełny spis zależności przyszłego panelu lub instalatora.

Teksty i noty skopiowano z rzeczywiście zainstalowanych dystrybucji do `third_party_licenses/`; zachowują autorów i warunki. Metadane zestawiono z dostępnymi tekstami, a brak pySerial opisano jawnie. Wykaz zawiera m.in. MIT, BSD, Apache, MIT-0, ISC, PSF, LGPL i MPL; zasoby Dash wskazują także CC BY i SIL OFL. Licencja głównego pakietu nie opisuje automatycznie wszystkich jego części. W przeanalizowanych warunkach nie stwierdzono opłat za urządzenia/funkcje; dystrybucja wymaga zachowania odpowiednich warunków.

**Uzupełnienie przeglądu z 24 października 2026 r.:** obecny katalog nie jest kompletnym pakietem zgodności dla instalatora. Ustalono dodatkowe LGPL 3 i noty MPL/BSD wewnątrz setuptools, skrócone noty oraz potrzebę weryfikacji zasobów JS. Szczegóły i nierozstrzygnięte kwestie opisuje [stan prawny i dystrybucja](licencje/STAN_PRAWNY_I_DYSTRYBUCJA.md). Własne elementy projektu mają [MIT z podpisem Pawel Juroszek (FL Development)](../LICENSE); nie zastępuje ona żadnej licencji komponentu.

| Komponent | Wersja | Licencja | Teksty / pochodzenie |
|---|---|---|---|
| bcrypt | 5.0.0 | Apache-2.0 | [1-LICENSE](../third_party_licenses/bcrypt/1-LICENSE) |
| cffi | 2.1.1 | MIT-0 | [1-LICENSE](../third_party_licenses/cffi/1-LICENSE) |
| cryptography | 50.0.2 | Apache-2.0 OR BSD-3-Clause | [1-LICENSE](../third_party_licenses/cryptography/1-LICENSE), [2-LICENSE.APACHE](../third_party_licenses/cryptography/2-LICENSE.APACHE), [3-LICENSE.BSD](../third_party_licenses/cryptography/3-LICENSE.BSD) |
| invoke | 3.0.3 | BSD-2-Clause | [1-LICENSE](../third_party_licenses/invoke/1-LICENSE) |
| markdown-it-py | 4.2.0 | MIT (tekst w paczce) | [1-LICENSE](../third_party_licenses/markdown-it-py/1-LICENSE), [2-LICENSE.markdown-it](../third_party_licenses/markdown-it-py/2-LICENSE.markdown-it) |
| mdurl | 0.1.2 | MIT (tekst w paczce) | [1-LICENSE](../third_party_licenses/mdurl/1-LICENSE) |
| netmiko | 4.8.0 | MIT | [1-LICENSE](../third_party_licenses/netmiko/1-LICENSE), [2-LICENSE](../third_party_licenses/netmiko/2-LICENSE) |
| ntc-templates | 9.3.0 | Apache-2.0 | [1-LICENSE](../third_party_licenses/ntc-templates/1-LICENSE), [2-LICENSE](../third_party_licenses/ntc-templates/2-LICENSE) |
| paramiko | 5.0.0 | LGPL-2.1 | [1-LICENSE](../third_party_licenses/paramiko/1-LICENSE) |
| psutil | 7.2.2 | BSD-3-Clause | [1-LICENSE](../third_party_licenses/psutil/1-LICENSE) |
| pyasn1 | 0.6.4 | BSD-2-Clause | [1-LICENSE.rst](../third_party_licenses/pyasn1/1-LICENSE.rst) |
| pycparser | 3.11 | BSD-3-Clause | [1-LICENSE](../third_party_licenses/pycparser/1-LICENSE) |
| pygments | 2.21.0 | BSD-2-Clause | [1-LICENSE](../third_party_licenses/pygments/1-LICENSE) |
| pynacl | 1.6.2 | Apache-2.0 | [1-LICENSE](../third_party_licenses/pynacl/1-LICENSE), [2-LICENSE.libsodium.txt](../third_party_licenses/pynacl/2-LICENSE.libsodium.txt) |
| pyserial | 3.5 | BSD-3-Clause (SPDX w serial/__init__.py) | [LICENSE_REFERENCE.txt](../third_party_licenses/pyserial/LICENSE_REFERENCE.txt) |
| pysnmp | 7.1.30 | BSD-2-Clause (tekst w paczce) | [1-LICENSE.rst](../third_party_licenses/pysnmp/1-LICENSE.rst) |
| pyyaml | 6.0.3 | MIT | [1-LICENSE](../third_party_licenses/pyyaml/1-LICENSE) |
| rich | 15.0.0 | MIT | [1-LICENSE](../third_party_licenses/rich/1-LICENSE) |
| scp | 0.16.2 | LGPL-2.1-or-later | [1-LICENSE.txt](../third_party_licenses/scp/1-LICENSE.txt) |
| textfsm | 2.1.0 | Apache License, Version 2.0 | [1-COPYING](../third_party_licenses/textfsm/1-COPYING), [2-LICENSE.txt](../third_party_licenses/textfsm/2-LICENSE.txt) |

## Dystrybucja

Źródła i adresy upstream zapisano w [inwentarzu](../third_party_licenses/inventory.json). Dla LGPL zachowujemy dostarczony tekst i odnośniki do źródeł; bundlowanie binariów i wymagany sposób udostępnienia odpowiednich źródeł sprawdzamy przy instalatorze w Etapie 5. Pakiet pySerial w obecnym venv nie dostarcza pełnego osobnego tekstu; zapisano referencję i deklarację SPDX — pełny tekst należy uzupełnić przed dołączeniem tej biblioteki do instalatora. W tym etapie zainstalowano lokalnie jedynie własny pakiet editable; bibliotek nie przebudowywano ani nie redystrybuowano w instalatorze.

## Etap 3: graf i opcjonalny podgląd

NetworkX używamy bez extras (bez numpy/scipy/matplotlib). Opcjonalny `mapper-sieci[preview]` używa zainstalowanych Dash/dash-cytoscape i ich zależności wykonawczych; bez cloud/Enterprise/CI extras. Niczego nie pobrano ani nie aktualizowano. Poniżej dodatkowe dystrybucje; dostępne teksty i noty, w tym komentarze dotyczące zasobów JS, zachowano lokalnie. Nie oznacza to kompletności informacji o każdym zasobie wewnątrz paczek ani przygotowania instalatora.

Wpis `setuptools — MIT` w tabeli opisuje główny pakiet. Dołączony `autocommand 2.2.2` ma LGPL 3 ([zachowany tekst](../third_party_licenses/setuptools/2-LICENSE)); dodatkowe noty MPL/BSD z zainstalowanego setuptools wymagają uzupełnienia przed jego redystrybucją. Dash 4.4.1 deklaruje setuptools jako zależność wykonawczą, więc trzeba zbadać jego obecność i zawartość w artefakcie wydania.

| Komponent | Wersja | Licencja/metadane | Teksty |
|---|---|---|---|
| annotated-types | 0.8.0 | MIT | [1-LICENSE](../third_party_licenses/annotated-types/1-LICENSE) |
| blinker | 1.9.0 | SEE LICENSE FILES | [1-LICENSE.txt](../third_party_licenses/blinker/1-LICENSE.txt) |
| certifi | 2026.7.22 | MPL-2.0 | [1-LICENSE](../third_party_licenses/certifi/1-LICENSE) |
| charset-normalizer | 3.5.2 | MIT | [1-LICENSE](../third_party_licenses/charset-normalizer/1-LICENSE) |
| click | 8.5.0 | BSD-3-Clause | [1-LICENSE.txt](../third_party_licenses/click/1-LICENSE.txt) |
| comm | 0.2.3 | BSD 3-Clause License | [1-LICENSE](../third_party_licenses/comm/1-LICENSE) |
| dash | 4.4.1 | MIT | [1-LICENSE](../third_party_licenses/dash/1-LICENSE), [2-async-export.js.LICENSE.txt](../third_party_licenses/dash/2-async-export.js.LICENSE.txt), [3-async-table.js.LICENSE.txt](../third_party_licenses/dash/3-async-table.js.LICENSE.txt), [4-async-datepicker.js.LICENSE.txt](../third_party_licenses/dash/4-async-datepicker.js.LICENSE.txt), [5-async-dropdown.js.LICENSE.txt](../third_party_licenses/dash/5-async-dropdown.js.LICENSE.txt), [6-async-markdown.js.LICENSE.txt](../third_party_licenses/dash/6-async-markdown.js.LICENSE.txt), [7-async-slider.js.LICENSE.txt](../third_party_licenses/dash/7-async-slider.js.LICENSE.txt), [8-async-upload.js.LICENSE.txt](../third_party_licenses/dash/8-async-upload.js.LICENSE.txt), [9-dash_core_components-shared.js.LICENSE.txt](../third_party_licenses/dash/9-dash_core_components-shared.js.LICENSE.txt), [10-dash_core_components.js.LICENSE.txt](../third_party_licenses/dash/10-dash_core_components.js.LICENSE.txt) |
| dash-cytoscape | 1.0.2 | MIT | [1-LICENSE](../third_party_licenses/dash-cytoscape/1-LICENSE) |
| flask | 3.1.3 | BSD-3-Clause | [1-LICENSE.txt](../third_party_licenses/flask/1-LICENSE.txt) |
| idna | 3.20 | BSD-3-Clause | [1-LICENSE.md](../third_party_licenses/idna/1-LICENSE.md) |
| importlib-metadata | 9.0.1 | Apache-2.0 | [1-LICENSE](../third_party_licenses/importlib-metadata/1-LICENSE) |
| itsdangerous | 2.2.0 | SEE LICENSE FILES | [1-LICENSE.txt](../third_party_licenses/itsdangerous/1-LICENSE.txt) |
| janus | 2.0.0 | Apache 2 | [1-LICENSE](../third_party_licenses/janus/1-LICENSE) |
| jinja2 | 3.1.6 | SEE LICENSE FILES | [1-LICENSE.txt](../third_party_licenses/jinja2/1-LICENSE.txt) |
| markupsafe | 3.0.4 | BSD-3-Clause | [1-LICENSE.txt](../third_party_licenses/markupsafe/1-LICENSE.txt) |
| narwhals | 2.27.1 | MIT | [1-LICENSE.md](../third_party_licenses/narwhals/1-LICENSE.md) |
| nest-asyncio | 1.6.0 | BSD | [1-LICENSE](../third_party_licenses/nest-asyncio/1-LICENSE) |
| networkx | 3.7 | BSD-3-Clause | [1-LICENSE.txt](../third_party_licenses/networkx/1-LICENSE.txt) |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause | [1-LICENSE](../third_party_licenses/packaging/1-LICENSE), [2-LICENSE.APACHE](../third_party_licenses/packaging/2-LICENSE.APACHE), [3-LICENSE.BSD](../third_party_licenses/packaging/3-LICENSE.BSD) |
| plotly | 7.1.0 | MIT | [1-LICENSE.txt](../third_party_licenses/plotly/1-LICENSE.txt) |
| pydantic | 2.14.0 | MIT | [1-LICENSE](../third_party_licenses/pydantic/1-LICENSE) |
| pydantic-core | 2.50.0 | MIT | [1-LICENSE](../third_party_licenses/pydantic-core/1-LICENSE) |
| requests | 2.34.2 | Apache-2.0 | [1-LICENSE](../third_party_licenses/requests/1-LICENSE), [2-NOTICE](../third_party_licenses/requests/2-NOTICE) |
| retrying | 1.4.2 | Apache-2.0 | [1-LICENSE.txt](../third_party_licenses/retrying/1-LICENSE.txt) |
| setuptools | 84.0.0 | MIT | [1-LICENSE](../third_party_licenses/setuptools/1-LICENSE), [2-LICENSE](../third_party_licenses/setuptools/2-LICENSE), [3-LICENSE](../third_party_licenses/setuptools/3-LICENSE), [4-LICENSE](../third_party_licenses/setuptools/4-LICENSE), [5-LICENSE](../third_party_licenses/setuptools/5-LICENSE), [6-LICENSE](../third_party_licenses/setuptools/6-LICENSE), [7-LICENSE](../third_party_licenses/setuptools/7-LICENSE), [8-LICENSE](../third_party_licenses/setuptools/8-LICENSE), [9-LICENSE](../third_party_licenses/setuptools/9-LICENSE), [10-LICENSE.APACHE](../third_party_licenses/setuptools/10-LICENSE.APACHE), [11-LICENSE.BSD](../third_party_licenses/setuptools/11-LICENSE.BSD), [12-LICENSE](../third_party_licenses/setuptools/12-LICENSE), [13-LICENSE](../third_party_licenses/setuptools/13-LICENSE), [14-LICENSE.txt](../third_party_licenses/setuptools/14-LICENSE.txt), [15-LICENSE](../third_party_licenses/setuptools/15-LICENSE) |
| typing-extensions | 4.16.0 | PSF-2.0 | [1-LICENSE](../third_party_licenses/typing-extensions/1-LICENSE) |
| typing-inspection | 0.4.4 | MIT | [1-LICENSE](../third_party_licenses/typing-inspection/1-LICENSE) |
| urllib3 | 2.8.0 | MIT | [1-LICENSE.txt](../third_party_licenses/urllib3/1-LICENSE.txt) |
| werkzeug | 3.1.9 | BSD-3-Clause | [1-LICENSE.txt](../third_party_licenses/werkzeug/1-LICENSE.txt) |
| zipp | 4.1.1 | MIT | [1-LICENSE](../third_party_licenses/zipp/1-LICENSE) |
