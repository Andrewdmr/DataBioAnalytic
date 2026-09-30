import os
import random
import pickle
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# ============================================================
# 0. CONFIGURACIÓN
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_DATOS = os.path.join(BASE_DIR, "datos_originales")
DIR_SUBGRAFOS = os.path.join(BASE_DIR, "subgrafos")
DIR_RESULTADOS = os.path.join(BASE_DIR, "resultados")

for d in [DIR_DATOS, DIR_SUBGRAFOS, DIR_RESULTADOS]:
    os.makedirs(d, exist_ok=True)

NOMBRE_PROCESO = "reparacion_adn"

GENES_SEMILLA = ["BRCA1", "BRCA2", "PALB2", "RAD51", "ATM","CHEK2", "BARD1", "BRIP1", "TP53"]

ARCHIVO_INFO = os.path.join(DIR_DATOS, "9606.protein.info.v12.0.txt")
ARCHIVO_LINKS = os.path.join(DIR_DATOS, "9606.protein.links.v12.0.txt.gz")

UMBRAL_CONFIANZA = 700
MIN_NODOS = 500
MAX_NODOS = 550

# ============================================================
# FUNCIÓN DE ESTADÍSTICAS
# ============================================================

def estadisticas(nombre, G, mst=None):
    print("\n" + "=" * 55)
    print(f"📊 {nombre}")
    print("=" * 55)
    print(f"Nodos:   {G.number_of_nodes():,}")
    print(f"Aristas: {G.number_of_edges():,}")
    if mst:
        print(f"Aristas MST: {mst.number_of_edges():,}")


# ============================================================
# 1. INFORMACIÓN DE PROTEÍNAS
# ============================================================

print("\n📂 Cargando información...")

info = pd.read_csv(ARCHIVO_INFO, sep="\t")
info.columns = [c.lstrip("#") for c in info.columns]

semilla = info[info["preferred_name"].isin(GENES_SEMILLA)]

ids_semilla = set(semilla["string_protein_id"])

id_a_nombre = dict(
    zip(info["string_protein_id"], info["preferred_name"])
)
print("\n🧬 Genes encontrados:")
print(semilla[["string_protein_id", "preferred_name"]].to_string(index=False))

print(f"\n✅ Semillas: "f"{len(ids_semilla)}/{len(GENES_SEMILLA)}")

# ============================================================
# 2. LEER INTERACCIONES
# ============================================================
print("\n📂 Leyendo interacciones...")

if not os.path.exists(ARCHIVO_LINKS):
    ARCHIVO_LINKS = os.path.join(DIR_DATOS,"9606.protein.links.v12.0.txt")

compression = "gzip" if ARCHIVO_LINKS.endswith(".gz") else None
filas = []

for bloque in pd.read_csv(
    ARCHIVO_LINKS,
    sep=r"\s+",
    compression=compression,
    chunksize=1_000_000
):
    bloque = bloque[
        bloque["combined_score"] > UMBRAL_CONFIANZA
    ]

    bloque = bloque[
        bloque["protein1"].isin(ids_semilla) |
        bloque["protein2"].isin(ids_semilla)
    ]

    if not bloque.empty:
        filas.append(bloque)

edges = pd.concat(filas, ignore_index=True)

edges["confianza"] = edges["combined_score"] / 1000
edges["costo"] = 1 - edges["confianza"]

print(f"✅ Interacciones: {len(edges):,}")


# ============================================================
# 3. CONSTRUIR GRAFO
# ============================================================
G = nx.Graph()
G.add_nodes_from(ids_semilla)

for _, e in edges.iterrows():
    G.add_edge(
        e["protein1"],
        e["protein2"],
        weight=e["confianza"],
        costo=e["costo"]
    )
estadisticas("GRAFO COMPLETO", G)

# ============================================================
# 4. DFS - COMPONENTES CONEXAS
# ============================================================
componentes = list(nx.connected_components(G))

print(
    f"\n🔹 Componentes conexas (DFS): "
    f"{len(componentes)}"
)

for i, c in enumerate(
    sorted(componentes, key=len, reverse=True)[:5], 1
):
    print(f"   Componente {i}: {len(c):,} nodos")

# ============================================================
# 5. UNION-FIND
# ============================================================
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

grupos_uf = len({
    uf.find(n) for n in G.nodes()
})

print(f"\n🔹 Grupos Union-Find: {grupos_uf}")

# ============================================================
# 6. MST GLOBAL - KRUSKAL
# ============================================================

mst_global = nx.minimum_spanning_tree(
    G,
    weight="costo"
)
estadisticas(
    "GRAFO COMPLETO + MST",
    G,
    mst_global
)

# ============================================================
# 7. VISUALIZACIÓN DEL GRAFO COMPLETO
# ============================================================

print("\n🎨 Generando grafo completo...")

plt.figure(figsize=(14, 14))
ax = plt.gca()
ax.set_facecolor("#F7F9FC")

pos = nx.spring_layout(G,seed=42,k=0.35,iterations=80)
grados = dict(G.degree())
tamanos = [
    40 + grados[n] * 12
    for n in G.nodes()
]
colores = [
    "#E63946" if n in ids_semilla else "#4C78A8"for n in G.nodes()]

# Aristas según confianza
anchos = []
colores_aristas = []

for u, v, d in G.edges(data=True):
    confianza = d["weight"]
    anchos.append(0.3 + confianza * 2)

    if confianza >= 0.90:
        colores_aristas.append("#1B4332")
    elif confianza >= 0.80:
        colores_aristas.append("#40916C")
    else:
        colores_aristas.append("#A8B0B8")

nx.draw_networkx_edges(G, pos,width=anchos,edge_color=colores_aristas,alpha=0.35)
nx.draw_networkx_nodes(G, pos,node_size=tamanos,node_color=colores,edgecolors="white")

etiquetas = {
    n: id_a_nombre.get(n, n)
    for n in ids_semilla
}

nx.draw_networkx_labels(G, pos,labels=etiquetas,font_size=9,font_weight="bold")

plt.title(f"Red de interacción — {NOMBRE_PROCESO.upper()}\n"f"Nodos: {G.number_of_nodes():,} | "f"Aristas: {G.number_of_edges():,}",fontsize=18,fontweight="bold")

plt.axis("off")
ruta_img1 = os.path.join(DIR_RESULTADOS,f"grafo_completo_{NOMBRE_PROCESO}.png")
plt.savefig(ruta_img1,dpi=300,bbox_inches="tight",facecolor="#F7F9FC")
plt.close()
print(f"✅ {ruta_img1}")

# ============================================================
# 8. SUBGRAFO MAYOR
# ============================================================
print("\n🎨 Generando subgrafo...")
componente_mayor = max(componentes, key=len)

subG = G.subgraph(componente_mayor).copy()
mst_sub = nx.minimum_spanning_tree(subG,weight="costo")
estadisticas("COMPONENTE MAYOR",subG,mst_sub)

# ============================================================
# 9. SELECCIÓN ALEATORIA ENTRE 500 Y 550
# ============================================================
cantidad = random.randint(MIN_NODOS,MAX_NODOS)
semillas_presentes = (ids_semilla & set(subG.nodes()))
# Reservar espacio para las semillas
cantidad_interactores = (cantidad - len(semillas_presentes))
grados_sub = dict(subG.degree())
candidatos = [n for n in subG.nodes()if n not in semillas_presentes]

# Ordenar por grado
candidatos.sort(key=grados_sub.get,reverse=True)
nodos_finales = (list(semillas_presentes)+candidatos[:cantidad_interactores])

subG = subG.subgraph(nodos_finales).copy()

mst_sub = nx.minimum_spanning_tree(subG,weight="costo")

print(f"\n🎲 Tamaño aleatorio solicitado: {cantidad}")
estadisticas("SUBGRAFO FINAL",subG,mst_sub)

# ============================================================
# 10. VISUALIZACIÓN SUBGRAFO + MST
# ============================================================

plt.figure(figsize=(14, 14))
ax = plt.gca()
ax.set_facecolor("#F7F9FC")

pos_sub = nx.spring_layout(subG,seed=42,k=0.4,iterations=80)

grados_sub = dict(subG.degree())

tamanos_sub = [80 + grados_sub[n] * 8 for n in subG.nodes()]

colores_sub = [
    "#E63946" if n in ids_semilla else "#457B9D"
    for n in subG.nodes()
]

# Todas las aristas
nx.draw_networkx_edges(subG,pos_sub,edge_color="#B0B7C3",width=0.6,alpha=0.35)
# MST
nx.draw_networkx_edges(mst_sub,pos_sub,edge_color="#F4A261",width=2.5)
# Nodos
nx.draw_networkx_nodes(subG,pos_sub,node_color=colores_sub,node_size=tamanos_sub,edgecolors="white")

# Etiquetas
etiquetas_sub = {n: id_a_nombre.get(n, n) for n in subG.nodes()}

nx.draw_networkx_labels(subG,pos_sub,labels=etiquetas_sub,font_size=6)

plt.title(
    f"Subgrafo — {NOMBRE_PROCESO.upper()}\n"
    f"Nodos: {subG.number_of_nodes():,} | "
    f"Aristas: {subG.number_of_edges():,} | "
    f"MST: {mst_sub.number_of_edges():,}",
    fontsize=18,
    fontweight="bold"
)

plt.axis("off")
ruta_img2 = os.path.join(DIR_RESULTADOS,f"subgrafo_mst_{NOMBRE_PROCESO}.png")

plt.savefig(ruta_img2,dpi=300,bbox_inches="tight",facecolor="#F7F9FC")
plt.close()
print(f"✅ {ruta_img2}")

# ============================================================
# 11. GUARDAR SUBGRAFO
# ============================================================
subgrafo_final = nx.relabel_nodes(subG,id_a_nombre)
ruta_pkl = os.path.join(DIR_SUBGRAFOS,f"subgrafo_{subG.number_of_nodes()}_{NOMBRE_PROCESO}.pkl")
with open(ruta_pkl, "wb") as f:
    pickle.dump(
        (subgrafo_final, id_a_nombre),
        f
    )
ruta_csv = os.path.join(DIR_SUBGRAFOS,f"mis_{subG.number_of_nodes()}_nodos_{NOMBRE_PROCESO}.csv")
nx.to_pandas_edgelist(subgrafo_final).to_csv(ruta_csv,index=False)

# ============================================================
# 12. RESUMEN FINAL
# ============================================================
print("\n" + "=" * 60)
print("📊 RESUMEN FINAL")
print("=" * 60)
print(f"Semillas: "f"{len(ids_semilla)}/{len(GENES_SEMILLA)}")
print(f"Grafo completo: "f"{G.number_of_nodes():,} nodos | "f"{G.number_of_edges():,} aristas")
print(f"Componentes DFS: "f"{len(componentes)}")
print(f"Grupos Union-Find: "f"{grupos_uf}")
print(f"MST global: "f"{mst_global.number_of_edges():,} aristas")
print(f"Subgrafo final: "f"{subG.number_of_nodes():,} nodos | "f"{subG.number_of_edges():,} aristas")
print(f"MST subgrafo: "f"{mst_sub.number_of_edges():,} aristas")

# ============================================================
# TOP 10 HUBS
# ============================================================
grados_final = dict(subgrafo_final.degree())
print("\n🔝 TOP 10 HUBS")
for i, (nodo, grado) in enumerate(
    sorted(grados_final.items(),key=lambda x: x[1],reverse=True)[:10],
    1
):
    print(f"{i:2}. {nodo}: "f"{grado} conexiones")
print("\n🎉 ¡Proceso completado!")
