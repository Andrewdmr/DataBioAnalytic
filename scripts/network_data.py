"""
network_data.py

Loads the network built by build_network.py and applies the filters of the
application. Nothing here depends on tkinter, so this part can be tested
alone (see test_network.py).
"""

import csv
import os

from graph_algorithms import (build_adjacency, bfs_neighborhood,
                              dfs_components, kruskal_mst)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DATA_DIR = os.path.join(BASE_DIR, "datos_app")

PATHWAY_LABELS = {
    "reparacion_adn": "Reparacion del ADN",
    "senalizacion_hormonal": "Senalizacion hormonal",
    "ciclo_celular": "Ciclo celular y apoptosis",
}

# Seed genes get the color of their pathway. The other proteins share one
# neutral color: most of them belong to several pathways at the same time,
# so a color per pathway would not tell much (see the info panel instead).
PATHWAY_COLORS = {
    "reparacion_adn": "#ff0090",
    "senalizacion_hormonal": "#ffbb00",
    "ciclo_celular": "#aaff00",
}
OTHER_COLOR = "#4fa3ff"


class Network:
    """The whole protein network, loaded once at start."""

    def __init__(self, data_dir=APP_DATA_DIR):
        nodes_file = os.path.join(data_dir, "nodes.csv")
        edges_file = os.path.join(data_dir, "edges.csv")
        if not (os.path.exists(nodes_file) and os.path.exists(edges_file)):
            raise FileNotFoundError(
                "datos_app/nodes.csv or datos_app/edges.csv not found. "
                "Run first: python scripts/build_network.py")

        self.info = {}  # name -> dict(pathways, seed_of, ot_score, string_id)
        with open(nodes_file, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                self.info[row["name"]] = {
                    "string_id": row["string_id"],
                    "pathways": [p for p in row["pathways"].split(";") if p],
                    "seed_of": [p for p in row["seed_of"].split(";") if p],
                    "ot_score": float(row["ot_score"]),
                }

        self.edges = []  # (u, v, confidence)
        with open(edges_file, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                self.edges.append((row["source"], row["target"], float(row["confidence"])))

        self.adj = build_adjacency(self.info.keys(), self.edges)

    def find(self, text):
        """Case insensitive search. Return the exact name or None."""
        # The list shows seeds as "NAME *": ignore the star if it was copied
        key = text.replace("*", "").strip().upper()
        if not key:
            return None
        for name in self.info:
            if name.upper() == key:
                return name
        return None

    def suggestions(self, text, limit=5):
        key = text.replace("*", "").strip().upper()
        return sorted(n for n in self.info if n.upper().startswith(key))[:limit] if key else []

    def is_seed(self, name):
        return bool(self.info[name]["seed_of"])

    def color(self, name):
        seed_of = self.info[name]["seed_of"]
        return PATHWAY_COLORS[seed_of[0]] if seed_of else OTHER_COLOR


class FilterResult:
    def __init__(self):
        self.nodes = []          # names, in display order
        self.edges = []          # (u, v, confidence)
        self.total_nodes = 0     # nodes that passed the filters (before the display limit)
        self.total_edges = 0
        self.components = 0      # connected components of what is displayed (DFS)
        self.truncated = False
        self.message = ""


def apply_filters(net, pathway=None, min_confidence=0.7, center=None, depth=1,
                  mst_only=False, max_nodes=120):
    """Apply the filters in a fixed order and return a FilterResult.

    1. pathway          keep proteins of one pathway (None = all)
    2. min_confidence   keep interactions with confidence >= value
    3. center + depth   keep proteins at <= depth interactions from center (BFS)
    4. max_nodes        display limit (see below)
    5. mst_only         replace the edges by the Kruskal MST of what is left
    """
    res = FilterResult()

    # 1. Pathway
    if pathway:
        nodes = {n for n, d in net.info.items() if pathway in d["pathways"]}
    else:
        nodes = set(net.info)

    # 2. Confidence
    edges = [(u, v, c) for u, v, c in net.edges
             if c >= min_confidence and u in nodes and v in nodes]
    adj = build_adjacency(nodes, edges)

    # 3. Neighbourhood of a protein
    depths = None
    if center:
        if center not in adj:
            res.message = f"{center} no esta en la via elegida"
            return res
        depths = bfs_neighborhood(adj, center, depth)
        nodes = set(depths)
        edges = [(u, v, c) for u, v, c in edges if u in nodes and v in nodes]
        adj = build_adjacency(nodes, edges)

    res.total_nodes = len(nodes)
    res.total_edges = len(edges)

    # 4. Display limit (deterministic, no random).
    #    With a center: closest proteins first (BFS depth), then the most
    #    reliable link towards the previous level. Seeds get no priority, so
    #    the view shows the real best partners of the center, not our seeds.
    #    Without a center: the proteins most associated with breast cancer
    #    according to Open Targets (globalScore). Sorting by degree would show
    #    big protein complexes (mitochondrial complex I...) that have little
    #    to do with breast cancer.
    if len(nodes) > max_nodes:
        if center:
            best_link = {center: 1.0}
            for n in nodes:
                if n != center:
                    best_link[n] = max((c for m, c in adj[n].items()
                                        if depths[m] == depths[n] - 1), default=0.0)

            def priority(n):
                return (depths[n], -best_link[n], n)
        else:
            def priority(n):
                return (-net.info[n]["ot_score"], -len(adj[n]), n)
        nodes = set(sorted(nodes, key=priority)[:max_nodes])
        edges = [(u, v, c) for u, v, c in edges if u in nodes and v in nodes]
        adj = build_adjacency(nodes, edges)
        res.truncated = True

    # 5. Minimum spanning tree
    if mst_only:
        edges = kruskal_mst(adj)
        adj = build_adjacency(nodes, edges)

    res.nodes = sorted(nodes)
    res.edges = edges
    res.components = len(dfs_components(adj))
    return res
