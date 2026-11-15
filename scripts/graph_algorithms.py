"""
graph_algorithms.py

Graph algorithms written by hand (no networkx) so each member can explain
them during the presentation. networkx is only used in the tests, to check
that our results are the same.

The graph is undirected and stored as an adjacency dictionary:
    adj[u] = {v: confidence, ...}
The cost of an edge is 1 - confidence (same as TB1): the most reliable
interactions are the cheapest ones.

Complexities (V = number of nodes, E = number of edges):
    bfs_neighborhood     O(V + E)
    dfs_components       O(V + E)
    UnionFind            almost O(1) per operation (path compression + union by rank)
    kruskal_mst          O(E log E)   (the sort dominates)
"""

from collections import deque


def edge_cost(confidence):
    return 1.0 - confidence


def build_adjacency(nodes, edges):
    """nodes: iterable of ids, edges: iterable of (u, v, confidence)."""
    adj = {n: {} for n in nodes}
    for u, v, conf in edges:
        if u in adj and v in adj and u != v:
            adj[u][v] = conf
            adj[v][u] = conf
    return adj


# ------------------------------------------------------------------
# BFS: proteins at distance <= max_depth from a source protein
# ------------------------------------------------------------------
def bfs_neighborhood(adj, source, max_depth):
    """Return {node: depth} for every node reachable in max_depth steps or less.

    BFS visits the graph level by level, so the first time a node is found
    its depth is the minimum number of interactions from the source.
    """
    if source not in adj:
        return {}
    depth = {source: 0}
    queue = deque([source])
    while queue:
        u = queue.popleft()
        if depth[u] == max_depth:
            continue
        for v in adj[u]:
            if v not in depth:
                depth[v] = depth[u] + 1
                queue.append(v)
    return depth


# ------------------------------------------------------------------
# DFS: connected components
# ------------------------------------------------------------------
def dfs_components(adj):
    """Return the list of connected components (each one a set of nodes),
    the biggest first.

    Iterative DFS with an explicit stack (a recursive version could hit the
    Python recursion limit on a network of 1500+ proteins).
    """
    visited = set()
    components = []
    for start in adj:
        if start in visited:
            continue
        component = set()
        stack = [start]
        visited.add(start)
        while stack:
            u = stack.pop()
            component.add(u)
            for v in adj[u]:
                if v not in visited:
                    visited.add(v)
                    stack.append(v)
        components.append(component)
    components.sort(key=len, reverse=True)
    return components


# ------------------------------------------------------------------
# Union-Find (UFDS)
# ------------------------------------------------------------------
class UnionFind:
    def __init__(self, elements):
        self.parent = {e: e for e in elements}
        self.rank = {e: 0 for e in elements}
        self.groups = len(self.parent)

    def find(self, x):
        # Path compression: every node on the way points directly to the root
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a, b):
        """Join the groups of a and b. Return False if they were already together."""
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        # Union by rank: the smaller tree goes under the bigger one
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        self.groups -= 1
        return True


# ------------------------------------------------------------------
# Kruskal: minimum spanning tree (forest if the graph is not connected)
# ------------------------------------------------------------------
def kruskal_mst(adj):
    """Return the list of MST edges (u, v, confidence).

    Edges are sorted by cost (1 - confidence) and added one by one if they
    do not close a cycle. Union-Find tells in almost O(1) whether u and v
    are already connected. Ties are broken by node names so the result is
    always the same.
    """
    edges = [(edge_cost(conf), u, v, conf)
             for u in adj for v, conf in adj[u].items() if u < v]
    edges.sort()
    uf = UnionFind(adj.keys())
    mst = []
    for _cost, u, v, conf in edges:
        if uf.union(u, v):
            mst.append((u, v, conf))
            if len(mst) == len(adj) - 1:
                break
    return mst
