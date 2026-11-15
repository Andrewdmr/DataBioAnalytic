"""
test_graph_algorithms.py

Checks the hand written algorithms against networkx, on small graphs whose
answer is known and on the real network of the app.

Run:  python scripts/test_graph_algorithms.py
"""

import os
import random
import sys
import unittest

import networkx as nx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph_algorithms import (UnionFind, bfs_neighborhood, build_adjacency,  # noqa: E402
                              dfs_components, edge_cost, kruskal_mst)
from network_data import APP_DATA_DIR, Network, apply_filters  # noqa: E402


def to_networkx(adj):
    g = nx.Graph()
    g.add_nodes_from(adj)
    for u in adj:
        for v, conf in adj[u].items():
            g.add_edge(u, v, cost=edge_cost(conf))
    return g


def random_graph(n, p, seed):
    rng = random.Random(seed)
    nodes = [f"P{i}" for i in range(n)]
    edges = [(a, b, round(rng.uniform(0.7, 1.0), 3))
             for i, a in enumerate(nodes) for b in nodes[i + 1:] if rng.random() < p]
    return build_adjacency(nodes, edges)


class SmallGraphTests(unittest.TestCase):
    """Hand checked examples."""

    def setUp(self):
        # A-B-C triangle, C-D, and E alone
        self.adj = build_adjacency("ABCDE", [("A", "B", 0.9), ("B", "C", 0.8),
                                             ("A", "C", 0.75), ("C", "D", 0.99)])

    def test_bfs_depths(self):
        self.assertEqual(bfs_neighborhood(self.adj, "A", 1), {"A": 0, "B": 1, "C": 1})
        self.assertEqual(bfs_neighborhood(self.adj, "A", 2), {"A": 0, "B": 1, "C": 1, "D": 2})
        self.assertEqual(bfs_neighborhood(self.adj, "Z", 2), {})

    def test_components(self):
        comps = dfs_components(self.adj)
        self.assertEqual(comps, [{"A", "B", "C", "D"}, {"E"}])

    def test_union_find(self):
        uf = UnionFind("ABCD")
        self.assertTrue(uf.union("A", "B"))
        self.assertFalse(uf.union("B", "A"))
        uf.union("C", "D")
        self.assertEqual(uf.groups, 2)
        self.assertNotEqual(uf.find("A"), uf.find("C"))

    def test_kruskal_drops_weakest_triangle_edge(self):
        mst = kruskal_mst(self.adj)
        self.assertEqual(len(mst), 3)  # 4 connected nodes -> 3 edges, E stays alone
        self.assertNotIn(("A", "C", 0.75), mst)


class CompareWithNetworkx(unittest.TestCase):
    """Same results as networkx on random graphs."""

    def test_random_graphs(self):
        for seed in range(20):
            adj = random_graph(60, 0.05, seed)
            g = to_networkx(adj)

            ours = sorted(sorted(c) for c in dfs_components(adj))
            ref = sorted(sorted(c) for c in nx.connected_components(g))
            self.assertEqual(ours, ref)

            our_cost = sum(edge_cost(c) for _u, _v, c in kruskal_mst(adj))
            ref_mst = nx.minimum_spanning_tree(g, weight="cost", algorithm="kruskal")
            ref_cost = sum(d["cost"] for _u, _v, d in ref_mst.edges(data=True))
            self.assertAlmostEqual(our_cost, ref_cost, places=9)
            self.assertEqual(len(kruskal_mst(adj)), ref_mst.number_of_edges())

            src = "P0"
            ref_depth = nx.single_source_shortest_path_length(g, src, cutoff=2)
            self.assertEqual(bfs_neighborhood(adj, src, 2), dict(ref_depth))


@unittest.skipUnless(os.path.exists(os.path.join(APP_DATA_DIR, "edges.csv")),
                     "run build_network.py first")
class RealNetworkTests(unittest.TestCase):
    """Same checks on the network used by the app."""

    @classmethod
    def setUpClass(cls):
        cls.net = Network()
        cls.g = to_networkx(cls.net.adj)

    def test_components_real(self):
        ours = [len(c) for c in dfs_components(self.net.adj)]
        ref = sorted((len(c) for c in nx.connected_components(self.g)), reverse=True)
        self.assertEqual(ours, ref)

    def test_mst_real(self):
        mst = kruskal_mst(self.net.adj)
        ref = nx.minimum_spanning_tree(self.g, weight="cost", algorithm="kruskal")
        self.assertEqual(len(mst), ref.number_of_edges())
        self.assertAlmostEqual(sum(edge_cost(c) for _u, _v, c in mst),
                               sum(d["cost"] for _u, _v, d in ref.edges(data=True)), places=6)

    def test_filters(self):
        res = apply_filters(self.net, center="ESR1", depth=1, max_nodes=10_000)
        self.assertEqual(set(res.nodes), set(self.net.adj["ESR1"]) | {"ESR1"})
        res = apply_filters(self.net, pathway="senalizacion_hormonal", min_confidence=0.9,
                            mst_only=True, max_nodes=10_000)
        self.assertEqual(len(res.edges), len(res.nodes) - res.components)
        res = apply_filters(self.net, max_nodes=50)
        self.assertTrue(res.truncated)
        self.assertEqual(len(res.nodes), 50)

    def test_centered_limit_keeps_most_reliable_partners(self):
        # With a center, the display limit must keep the partners with the
        # highest confidence towards the center (not the seeds first).
        k = 20
        res = apply_filters(self.net, center="AKT1", depth=1, min_confidence=0.7, max_nodes=k)
        conf = self.net.adj["AKT1"]
        expected = sorted(conf, key=lambda n: (-conf[n], n))[:k - 1]
        self.assertEqual(set(res.nodes), set(expected) | {"AKT1"})

    def test_limit_without_center_uses_open_targets(self):
        res = apply_filters(self.net, max_nodes=15)
        best = sorted(self.net.info, key=lambda n: (-self.net.info[n]["ot_score"],
                                                    -len(self.net.adj[n]), n))[:15]
        self.assertEqual(set(res.nodes), set(best))

    def test_search_ignores_star(self):
        self.assertEqual(self.net.find("akt1 *"), "AKT1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
