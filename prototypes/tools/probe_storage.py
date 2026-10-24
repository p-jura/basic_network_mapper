import json
import sqlite3
import networkx as nx

with sqlite3.connect(":memory:") as db:
    db.execute("CREATE TABLE probe (project_id TEXT, payload TEXT)")
    db.execute("INSERT INTO probe VALUES (?, ?)", ("lab-001", json.dumps({"ok": True})))
    assert (
        db.execute(
            "SELECT COUNT(*) FROM probe WHERE project_id=?", ("lab-001",)
        ).fetchone()[0]
        == 1
    )

graph = nx.Graph()
graph.add_edge("sw1", "sw2")
graph.add_edge("sw1", "h1")
assert nx.has_path(graph, "h1", "sw2")
print("STORAGE_GRAPH_OK")
