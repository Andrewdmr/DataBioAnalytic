"""Algoritmos de grafos implementados a mano (sin networkx).

Entrada común: `nodes` = lista de IDs (símbolos) y `edges` = lista de dicts con
`source`, `target`, `combined_score`, `weight` (= 1000 - combined_score).
"""
from __future__ import annotations


# ---------------------------------------------------------------------------
# Union-Find (Disjoint Set) con compresión de caminos y unión por rango
# ---------------------------------------------------------------------------
class UnionFind:
    def __init__(self, nodos):
        self.padre = {n: n for n in nodos}
        self.rango = {n: 0 for n in nodos}

    def find(self, x):
        raiz = x
        while self.padre[raiz] != raiz:
            raiz = self.padre[raiz]
        while self.padre[x] != raiz:           # compresión de caminos
            self.padre[x], x = raiz, self.padre[x]
        return raiz

    def union(self, a, b) -> bool:
        """Une los conjuntos de a y b. False si ya estaban unidos."""
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rango[ra] < self.rango[rb]:
            ra, rb = rb, ra
        self.padre[rb] = ra
        if self.rango[ra] == self.rango[rb]:
            self.rango[ra] += 1
        return True


def union_find(nodes, edges) -> dict:
    """Componentes conexos. IDs de componente 0..k-1 ordenados por tamaño desc."""
    uf = UnionFind(nodes)
    for e in edges:
        uf.union(e["source"], e["target"])

    grupos: dict[str, list[str]] = {}
    for n in nodes:
        grupos.setdefault(uf.find(n), []).append(n)
    ordenados = sorted(grupos.values(), key=lambda g: (-len(g), g[0]))

    componente = {}
    for cid, miembros in enumerate(ordenados):
        for n in miembros:
            componente[n] = cid
    return {
        "total_componentes": len(ordenados),
        "componente_por_proteina": componente,
        "tamanos": [len(g) for g in ordenados],
        "componentes": [sorted(g) for g in ordenados],
    }


# ---------------------------------------------------------------------------
# MST - Kruskal (peso = 1000 - combined_score)
# ---------------------------------------------------------------------------
def mst_kruskal(nodes, edges) -> dict:
    """Bosque de expansión mínima: ordena aristas por peso y añade las que no cierran ciclo."""
    uf = UnionFind(nodes)
    ids_mst = []
    peso_total = 0
    for e in sorted(edges, key=lambda e: e["weight"]):
        if uf.union(e["source"], e["target"]):
            ids_mst.append(e["id"])
            peso_total += e["weight"]
    en_mst = set(ids_mst)
    return {
        "aristas_mst": ids_mst,
        "total_aristas_mst": len(ids_mst),
        "peso_total": peso_total,
        "aristas": [{**e, "in_mst": e["id"] in en_mst} for e in edges],
    }


# ---------------------------------------------------------------------------
# DFS (profundidad limitada + profundización iterativa): ruta origen -> destino
# ---------------------------------------------------------------------------
def _adyacencia(nodes, edges):
    ady = {n: [] for n in nodes}
    for e in edges:
        ady[e["source"]].append((e["target"], e))
        ady[e["target"]].append((e["source"], e))
    for n in ady:                       # orden determinista
        ady[n].sort(key=lambda t: t[0])
    return ady


def _dfs_limitado(ady, origen, destino, limite, max_expansiones):
    """DFS iterativo que no pasa de `limite` saltos. Devuelve (nodos, aristas) o None."""
    ruta_nodos, ruta_aristas = [origen], []
    en_ruta = {origen}                       # evita ciclos dentro de la ruta actual
    pila = [iter(ady[origen])]
    expansiones = 0
    while pila:
        actual = ruta_nodos[-1]
        if actual == destino:
            return ruta_nodos, ruta_aristas
        avanzo = False
        if len(ruta_aristas) < limite:
            for vecino, arista in pila[-1]:
                if vecino in en_ruta:
                    continue
                expansiones += 1
                if expansiones > max_expansiones:
                    return None
                ruta_nodos.append(vecino)
                ruta_aristas.append(arista)
                en_ruta.add(vecino)
                pila.append(iter(ady[vecino]))
                avanzo = True
                break
        if not avanzo:                       # retroceso (backtracking)
            pila.pop()
            en_ruta.discard(ruta_nodos.pop())
            if ruta_aristas:
                ruta_aristas.pop()
    return None


def dfs_ruta(nodes, edges, origen: str, destino: str, evitar_directo: bool = True,
             min_saltos: int = 2, max_saltos: int = 7,
             max_expansiones: int = 500_000) -> dict:
    """Ruta de señalización por DFS.

    Si `evitar_directo` y existe arista origen-destino, se ignora temporalmente
    para forzar una ruta multi-salto. Se prueban límites de profundidad
    crecientes (min_saltos..max_saltos): 7 saltos = hasta 6 intermediarios.
    """
    conjunto = set(nodes)
    if origen not in conjunto or destino not in conjunto:
        return {"encontrada": False, "motivo": "origen o destino no están en el subgrafo",
                "nodos": [], "aristas": []}

    par = {origen, destino}
    directas = [e for e in edges if {e["source"], e["target"]} == par]
    ignorada = bool(evitar_directo and directas and origen != destino)
    if ignorada:
        edges = [e for e in edges if {e["source"], e["target"]} != par]
    ady = _adyacencia(nodes, edges)

    inicio = min_saltos if ignorada or not directas else 1
    for limite in range(max(inicio, 1), max_saltos + 1):
        res = _dfs_limitado(ady, origen, destino, limite, max_expansiones)
        if res:
            nodos_ruta, aristas_ruta = res
            return {"encontrada": True, "origen": origen, "destino": destino,
                    "longitud": len(aristas_ruta), "nodos": nodos_ruta,
                    "intermedios": nodos_ruta[1:-1], "aristas": aristas_ruta,
                    "arista_directa_ignorada": ignorada}
    return {"encontrada": False, "nodos": [], "aristas": [],
            "arista_directa_ignorada": ignorada,
            "motivo": f"no hay ruta multi-salto de hasta {max_saltos} saltos"
                      if ignorada else f"no hay ruta de hasta {max_saltos} saltos"}


# ---------------------------------------------------------------------------
# Simulación knockout (uno o varios genes: terapias combinadas)
# ---------------------------------------------------------------------------
def knockout(nodes, edges, genes, semillas=None) -> dict:
    """Elimina `genes` y compara Union-Find y MST antes/después.

    `semillas`: IDs de genes semilla; se usan para reportar los pares de
    semillas que dejaron de estar conectados entre sí.
    """
    genes = list(dict.fromkeys(genes))
    conjunto = set(nodes)
    faltan = [g for g in genes if g not in conjunto]
    if faltan or not genes:
        return {"encontrado": False,
                "motivo": f"no están en el subgrafo: {faltan}" if faltan else "lista de genes vacía"}

    antes_uf = union_find(nodes, edges)
    antes_mst = mst_kruskal(nodes, edges)

    inhibidos = set(genes)
    nodes2 = [n for n in nodes if n not in inhibidos]
    edges2 = [e for e in edges if e["source"] not in inhibidos and e["target"] not in inhibidos]
    despues_uf = union_find(nodes2, edges2)
    despues_mst = mst_kruskal(nodes2, edges2)
    comp_antes = antes_uf["componente_por_proteina"]
    comp_despues = despues_uf["componente_por_proteina"]

    # Aislados: sin ninguna arista tras el knockout
    grado = {n: 0 for n in nodes2}
    for e in edges2:
        grado[e["source"]] += 1
        grado[e["target"]] += 1
    grado_antes = {n: 0 for n in nodes}
    for e in edges:
        grado_antes[e["source"]] += 1
        grado_antes[e["target"]] += 1
    # solo cuentan los que QUEDARON aislados por el knockout (no los ya aislados)
    aislados = sorted(n for n, g in grado.items() if g == 0 and grado_antes[n] > 0)
    previamente_aislados = sum(1 for n, g in grado.items() if g == 0 and grado_antes[n] == 0)

    # Pierden conexión: en las islas que contenían un gen inhibido, todo lo que
    # no quedó en el fragmento mayor.
    islas_afectadas = {comp_antes[g] for g in genes}
    perdieron = []
    for isla in islas_afectadas:
        fragmentos: dict[int, list[str]] = {}
        for n in nodes2:
            if comp_antes[n] == isla:
                fragmentos.setdefault(comp_despues[n], []).append(n)
        if fragmentos:
            principal = max(fragmentos.values(), key=len)
            perdieron += [n for f in fragmentos.values() if f is not principal for n in f]
    perdieron = sorted(set(perdieron))

    # Pares de semillas conectados antes y desconectados después
    pares = []
    sem = sorted(n for n in (semillas or []) if n in set(nodes2))
    for i, a in enumerate(sem):
        for b in sem[i + 1:]:
            if comp_antes[a] == comp_antes[b] and comp_despues[a] != comp_despues[b]:
                pares.append([a, b])

    mst_antes, mst_despues = set(antes_mst["aristas_mst"]), set(despues_mst["aristas_mst"])
    return {
        "encontrado": True, "genes": genes, "gen": genes[0] if len(genes) == 1 else None,
        "proteinas_aisladas": aislados,
        "previamente_aislados": previamente_aislados,
        "proteinas_perdieron_conexion": perdieron,
        "pares_semilla_desconectados": pares,
        "total_pares_desconectados": len(pares),
        "total_afectadas": len(set(aislados) | set(perdieron)),
        "aristas_eliminadas": len(edges) - len(edges2),
        "union_find": {
            "componentes_antes": antes_uf["total_componentes"],
            "componentes_despues": despues_uf["total_componentes"],
            "componente_por_proteina": comp_despues,
        },
        "mst": {
            "aristas_antes": len(mst_antes), "aristas_despues": len(mst_despues),
            "peso_antes": antes_mst["peso_total"], "peso_despues": despues_mst["peso_total"],
            "aristas_mst_perdidas": sorted(mst_antes - mst_despues),
            "aristas_mst_nuevas": sorted(mst_despues - mst_antes),
            "aristas_mst": despues_mst["aristas_mst"],
        },
    }


# ---------------------------------------------------------------------------
# Ford-Fulkerson (Edmonds-Karp): flujo máximo y corte mínimo
# ---------------------------------------------------------------------------
def ford_fulkerson(nodos, aristas, origen: str, destino: str) -> dict:
    """Flujo máximo origen -> destino con BFS sobre el grafo residual.

    Cada interacción no dirigida de STRING se modela como dos aristas dirigidas
    opuestas con capacidad = combined_score.
    """
    from collections import deque

    residual: dict[str, dict[str, int]] = {n: {} for n in nodos}
    capacidad: dict[tuple[str, str], int] = {}
    id_arista: dict[frozenset, str] = {}
    for e in aristas:
        u, v, c = e["source"], e["target"], int(e["combined_score"])
        residual[u][v] = c
        residual[v][u] = c
        capacidad[(u, v)] = capacidad[(v, u)] = c
        id_arista[frozenset((u, v))] = e["id"]

    flujo_maximo = 0
    caminos_aumento = 0
    while True:
        # --- BFS: camino de aumento más corto en el grafo residual
        padre = {origen: None}
        cola = deque([origen])
        while cola and destino not in padre:
            u = cola.popleft()
            for v, cap in residual[u].items():
                if cap > 0 and v not in padre:
                    padre[v] = u
                    cola.append(v)
        if destino not in padre:
            break

        # --- cuello de botella del camino y actualización del residual
        cuello, v = float("inf"), destino
        while padre[v] is not None:
            cuello = min(cuello, residual[padre[v]][v])
            v = padre[v]
        v = destino
        while padre[v] is not None:
            u = padre[v]
            residual[u][v] -= cuello
            residual[v][u] += cuello
            v = u
        flujo_maximo += int(cuello)
        caminos_aumento += 1

    # --- flujo neto por arista no dirigida: capacidad - residual(u,v)
    aristas_flujo = []
    for e in aristas:
        u, v = e["source"], e["target"]
        neto = capacidad[(u, v)] - residual[u][v]
        if neto != 0:
            a, b = (u, v) if neto > 0 else (v, u)
            aristas_flujo.append({"id": e["id"], "source": a, "target": b,
                                  "flujo": abs(neto), "capacidad": capacidad[(u, v)]})

    # --- corte mínimo: aristas entre S (alcanzable en el residual) y el resto
    alcanzables = {origen}
    cola = deque([origen])
    while cola:
        u = cola.popleft()
        for v, cap in residual[u].items():
            if cap > 0 and v not in alcanzables:
                alcanzables.add(v)
                cola.append(v)
    corte_minimo = []
    for e in aristas:
        u, v = e["source"], e["target"]
        if (u in alcanzables) != (v in alcanzables):
            a, b = (u, v) if u in alcanzables else (v, u)
            corte_minimo.append({"id": e["id"], "source": a, "target": b,
                                 "capacidad": capacidad[(u, v)]})

    return {"origen": origen, "destino": destino, "flujo_maximo": flujo_maximo,
            "caminos_aumento": caminos_aumento, "aristas_flujo": aristas_flujo,
            "corte_minimo": corte_minimo,
            "nodos_lado_fuente": len(alcanzables)}
