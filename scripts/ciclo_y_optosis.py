import os
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# ---------------------------------------------------------------
# 0. Configuracion
# ---------------------------------------------------------------
DIR_DATOS = "."
NOMBRE_PROCESO = "ciclo_celular_apoptosis"
GENES_SEMILLA = ["CDK4", "CDK6", "CCND1", "MYC", "PIK3CA",
                 "AKT1", "PTEN", "MDM2", "BCL2", "BAX"]

ARCHIVO_INFO = os.path.join(DIR_DATOS, "9606.protein.info.v12.0.txt")
ARCHIVO_LINKS = os.path.join(DIR_DATOS, "9606.protein.links.v12.0.txt.gz")
UMBRAL_CONFIANZA = 700

# ---------------------------------------------------------------
# 1. Mapear genes semilla (simbolo) -> ID de proteina de STRING
# ---------------------------------------------------------------
info = pd.read_csv(ARCHIVO_INFO, sep="\t")
info.columns = [c.lstrip("#") for c in info.columns]

semilla_info = info[info["preferred_name"].isin(GENES_SEMILLA)]
print("Genes semilla encontrados en STRING:")
print(semilla_info[["string_protein_id", "preferred_name"]].to_string(index=False))

encontrados = set(semilla_info["preferred_name"])
faltantes = set(GENES_SEMILLA) - encontrados
if faltantes:
    print(f"\n¡Atencion! Estos genes NO se encontraron (revisar el simbolo): {faltantes}")

ids_semilla = set(semilla_info["string_protein_id"])

# ---------------------------------------------------------------
# 2. Leer protein.links y quedarnos con las interacciones de alta
#    confianza que involucran a algun gen semilla (expansion a
#    interactores de primer grado)
# ---------------------------------------------------------------
print("\nLeyendo protein.links.txt.gz (puede tardar uno o dos minutos)...")
filas_utiles = []
lector = pd.read_csv(ARCHIVO_LINKS, sep=" ", chunksize=1_000_000)
for bloque in lector:
    bloque = bloque[bloque["combined_score"] > UMBRAL_CONFIANZA]
    bloque = bloque[
        bloque["protein1"].isin(ids_semilla) | bloque["protein2"].isin(ids_semilla)
    ]
    if not bloque.empty:
        filas_utiles.append(bloque)

edges_df = pd.concat(filas_utiles, ignore_index=True)
edges_df["confianza"] = edges_df["combined_score"] / 1000.0
edges_df["costo"] = 1 - edges_df["confianza"]
print(f"Interacciones de alta confianza encontradas: {len(edges_df)}")

# ---------------------------------------------------------------
# 3. Construir el grafo
# ---------------------------------------------------------------
G = nx.Graph()
G.add_nodes_from(ids_semilla)  # asegura que las semillas queden, aunque queden aisladas
for _, fila in edges_df.iterrows():
    G.add_edge(fila["protein1"], fila["protein2"],
               weight=fila["confianza"], costo=fila["costo"])

print(f"\nNodos totales: {G.number_of_nodes()}")
print(f"Aristas totales: {G.number_of_edges()}")

if G.number_of_nodes() < 500:
    print("Atencion: quedaron menos de 500 nodos. Se puede bajar un poco el "
          "umbral de confianza, o agregar mas genes semilla.")
elif G.number_of_nodes() > 3000:
    print("Atencion: la red quedo muy grande. Se puede subir el umbral de "
          "confianza (ej. score > 800 o 900) para quedarse con menos nodos.")

# ---------------------------------------------------------------
# 4. Mapeo id -> nombre de gen (para etiquetar las visualizaciones)
# ---------------------------------------------------------------
id_a_nombre = dict(zip(info["string_protein_id"], info["preferred_name"]))

# ---------------------------------------------------------------
# 5. DFS -> componentes conexas
# ---------------------------------------------------------------
componentes = list(nx.connected_components(G))
print(f"Componentes conexas (DFS): {len(componentes)}")

# ---------------------------------------------------------------
# 6. Union-Find (implementacion propia)
# ---------------------------------------------------------------
class UnionFind:
    def __init__(self, nodos):
        self.padre = {n: n for n in nodos}
        self.rango = {n: 0 for n in nodos}

    def find(self, x):
        while self.padre[x] != x:
            self.padre[x] = self.padre[self.padre[x]]
            x = self.padre[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.rango[ra] < self.rango[rb]:
            ra, rb = rb, ra
        self.padre[rb] = ra
        if self.rango[ra] == self.rango[rb]:
            self.rango[ra] += 1


uf = UnionFind(G.nodes())
for u, v in G.edges():
    uf.union(u, v)
print(f"Grupos formados por Union-Find: {len({uf.find(n) for n in G.nodes()})}")

# ---------------------------------------------------------------
# 7. MST (costo = 1 - confianza)
# ---------------------------------------------------------------
mst_global = nx.minimum_spanning_tree(G, weight="costo")
print(f"Aristas en el MST: {mst_global.number_of_edges()}")

# ---------------------------------------------------------------
# 8. Visualizacion 1: grafo completo (genes semilla resaltados en rojo)
# ---------------------------------------------------------------
plt.figure(figsize=(14, 14))
pos = nx.spring_layout(G, seed=42, k=0.2)
es_semilla = [n in ids_semilla for n in G.nodes()]
nx.draw(
    G, pos,
    node_size=[90 if s else 10 for s in es_semilla],
    node_color=["red" if s else "#a8d0f0" for s in es_semilla],
    edge_color="gray", width=0.15, with_labels=False,
)
plt.title(f"Grafo completo - {NOMBRE_PROCESO}\n(rojo = genes semilla, azul = interactores)")
plt.savefig(f"grafo_completo_{NOMBRE_PROCESO}.png", dpi=200, bbox_inches="tight")
plt.close()

# ---------------------------------------------------------------
# 9. Visualizacion 2: subgrafo (componente mas grande), MST resaltado,
#    con nombres de gen como etiquetas
# ---------------------------------------------------------------
componente_mayor = max(componentes, key=len)
subG = G.subgraph(componente_mayor).copy()
mst_sub = nx.minimum_spanning_tree(subG, weight="costo")
etiquetas = {n: id_a_nombre.get(n, n) for n in subG.nodes()}

plt.figure(figsize=(12, 12))
pos_sub = nx.spring_layout(subG, seed=42, k=0.4)
nx.draw_networkx_nodes(subG, pos_sub, node_size=150, node_color="#a8d0f0")
nx.draw_networkx_edges(subG, pos_sub, edge_color="lightgray", width=0.6)
nx.draw_networkx_edges(mst_sub, pos_sub, edge_color="red", width=1.8)
nx.draw_networkx_labels(subG, pos_sub, labels=etiquetas, font_size=6)
plt.title(f"Subgrafo (componente mas grande) - {NOMBRE_PROCESO}\n(MST en rojo)")
plt.savefig(f"subgrafo_mst_{NOMBRE_PROCESO}.png", dpi=200, bbox_inches="tight")
plt.close()

print(f"\nListo. Se generaron: grafo_completo_{NOMBRE_PROCESO}.png y subgrafo_mst_{NOMBRE_PROCESO}.png")
