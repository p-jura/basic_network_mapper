import argparse
import json
import threading
import time
import uuid
import webbrowser
from pathlib import Path
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener

import dash_cytoscape as cyto
from dash import Dash, Input, Output, ctx, html

ROOT = Path(__file__).resolve().parents[1]
snapshot = json.loads(
    (ROOT / "examples/snapshots/lab-001.json").read_text(encoding="utf-8")
)
parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=8050)
args = parser.parse_args()
if not 1024 <= args.port <= 65535:
    parser.error("Port musi należeć do zakresu 1024–65535")

cyto.load_extra_layouts()
app = Dash(__name__, serve_locally=True)
run_id = uuid.uuid4().hex
url = f"http://127.0.0.1:{args.port}"


@app.server.get("/_mapper_ready")
def ready():
    return run_id


app.layout = html.Div(
    [
        html.H2("Mapper — próba offline"),
        html.P("Dane syntetyczne; brak odczytów sieci."),
        html.Button("Pobierz PNG", id="png", n_clicks=0),
        html.Button("Pobierz SVG", id="svg", n_clicks=0),
        cyto.Cytoscape(
            id="map",
            elements=snapshot["elements"],
            layout={"name": "breadthfirst"},
            style={"width": "100%", "height": "60vh"},
            stylesheet=[
                {
                    "selector": "node",
                    "style": {"label": "data(label)", "background-color": "#2563eb"},
                },
                {"selector": "node[kind = 'switch']", "style": {"shape": "rectangle"}},
                {
                    "selector": "node[vlan = 20]",
                    "style": {"background-color": "#d97706"},
                },
                {
                    "selector": "edge",
                    "style": {"label": "data(label)", "font-size": 10},
                },
            ],
        ),
        html.Pre(id="details"),
    ]
)


@app.callback(Output("details", "children"), Input("map", "tapNodeData"))
def details(data):
    return json.dumps(data, ensure_ascii=False, indent=2) if data else "Wybierz węzeł"


@app.callback(
    Output("map", "generateImage"),
    Input("png", "n_clicks"),
    Input("svg", "n_clicks"),
    prevent_initial_call=True,
)
def export_image(_png, _svg):
    return {
        "type": ctx.triggered_id,
        "action": "download",
        "filename": "mapper-lab-001",
    }


def open_when_ready():
    opener = build_opener(ProxyHandler({}))
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        try:
            with opener.open(url + "/_mapper_ready", timeout=1) as response:
                if response.read().decode() == run_id:
                    try:
                        opened = webbrowser.open(url)
                    except webbrowser.Error:
                        opened = False
                    if not opened:
                        print(f"Otwórz panel ręcznie: {url}", flush=True)
                    return
        except (URLError, OSError):
            pass
        time.sleep(0.2)
    print(f"Nie potwierdzono gotowości panelu. Sprawdź terminal: {url}", flush=True)


if __name__ == "__main__":
    print(f"Panel lokalny: {url}", flush=True)
    threading.Thread(target=open_when_ready, daemon=True).start()
    app.run(host="127.0.0.1", port=args.port, debug=False, use_reloader=False)
