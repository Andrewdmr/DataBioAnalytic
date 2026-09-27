import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import os
import sys
import pickle

# ============================================================
# CONFIGURACIÓN DE RUTAS (relativas a la raíz del repo)
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_DATOS = os.path.join(BASE_DIR, "datos_originales")
DIR_SUBGRAFOS = os.path.join(BASE_DIR, "subgrafos")
DIR_RESULTADOS = os.path.join(BASE_DIR, "resultados")

# Crear carpetas si no existen
for d in [DIR_DATOS, DIR_SUBGRAFOS, DIR_RESULTADOS]:
    os.makedirs(d, exist_ok=True)

# ============================================================
# CONFIGURACIÓN DEL PROCESO
# ============================================================
NOMBRE_PROCESO = "reparacion_adn"
GENES_SEMILLA = ["BRCA1", "BRCA2", "PALB2", "RAD51", "ATM", 
                 "CHEK2", "BARD1", "BRIP1", "TP53"]

ARCHIVO_INFO = os.path.join(DIR_DATOS, "9606.protein.info.v12.0.txt")
ARCHIVO_LINKS = os.path.join(DIR_DATOS, "9606.protein.links.v12.0.txt")
UMBRAL_CONFIANZA = 700
NODOS_OBJETIVO = 500

# ============================================================
# VERIFICAR ARCHIVOS
# ============================================================
for archivo in [ARCHIVO_INFO, ARCHIVO_LINKS]:
    if not os.path.exists(archivo):
        print(f"❌ ERROR: No se encuentra '{archivo}'")
        print(f"   Colócalo en: {DIR_DATOS}")
        sys.exit(1)

print(f"✅ Procesando vía: {NOMBRE_PROCESO}")

# ============================================================
# 1. CARGAR INFO
# ============================================================
print("Cargando información de proteínas...")
df_info = pd.read_csv(ARCHIVO_INFO, sep="\t")

posibles_nombres = ['#string_protein_id', 'string_protein_id', 'protein_id']
col_id = next((n for n in posibles_nombres if n in df_info.columns), None)

if col_id is None:
    print(f"❌ No se encontró columna ID.")
    sys.exit(1)

df_info = df_info.rename(columns={col_id: 'protein_id', 'preferred_name': 'gene_name'})
mapa_nombres = dict(zip(df_info['protein_id'], df_info['gene_name']))
mapa_inverso = dict(zip(df_info['gene_name'], df_info['protein_id']))

ids_semilla = set()
print("\nBuscando genes semilla:")
for gen in GENES_SEMILLA:
    if gen in mapa_inverso:
        ids_semilla.add(mapa_inverso[gen])
        print(f"   ✅ {gen}")
    else:
        print(f"   ⚠️ No encontrado: {gen}")

# ============================================================
# 2. CARGAR Y FILTRAR LINKS
# ============================================================
print("\nLeyendo interacciones de alta confianza...")
compression = 'gzip' if ARCHIVO_LINKS.endswith('.gz') else None

lista_aristas = []
for i, chunk in enumerate(pd.read_csv(
    ARCHIVO_LINKS, sep=" ", compression=compression, chunksize=200000
)):
    chunk_filtrado = chunk[chunk['combined_score'] >= UMBRAL_CONFIANZA]
    lista_aristas.append(chunk_filtrado)
    if (i + 1) % 5 == 0:
        print(f"   Procesados {(i+1)*200000:,} registros...")

df_links = pd.concat(lista_aristas, ignore_index=True)
print(f"   Interacciones de alta confianza: {len(df_links)}")

# ============================================================
# 3. CONSTRUIR GRAFO
# ============================================================
print("\nConstruyendo el grafo...")
G = nx.from_pandas_edgelist(df_links, 'protein1', 'protein2', edge_attr='combined_score')

# Extraer subgrafo de reparación del ADN
vecinos = set(ids_semilla)
for id_semilla in ids_semilla:
    if id_semilla in G:
        vecinos.update(G.neighbors(id_semilla))

if len(vecinos) < NODOS_OBJETIVO:
    print(f"   Expandiendo a 2 saltos...")
    vecinos_2 = set(vecinos)
    for nodo in list(vecinos):
        if nodo in G:
            vecinos_2.update(G.neighbors(nodo))
    vecinos = vecinos_2

subgrafo_proceso = G.subgraph(vecinos).copy()
grados = dict(subgrafo_proceso.degree())
nodos_top_500 = sorted(grados, key=grados.get, reverse=True)[:NODOS_OBJETIVO]
subgrafo_500 = G.subgraph(nodos_top_500).copy()
subgrafo_500 = nx.relabel_nodes(subgrafo_500, mapa_nombres)

print(f"   Subgrafo: {subgrafo_500.number_of_nodes()} nodos, {subgrafo_500.number_of_edges()} aristas")

# ============================================================
# 4. GUARDAR EN CARPETAS CORRECTAS
# ============================================================
ruta_pkl = os.path.join(DIR_SUBGRAFOS, f"subgrafo_500_{NOMBRE_PROCESO}.pkl")
with open(ruta_pkl, 'wb') as f:
    pickle.dump((subgrafo_500, mapa_nombres), f)
print(f"✅ Guardado: {ruta_pkl}")

ruta_csv = os.path.join(DIR_SUBGRAFOS, f"mis_500_nodos_{NOMBRE_PROCESO}.csv")
aristas_subgrafo = nx.to_pandas_edgelist(subgrafo_500)
aristas_subgrafo.to_csv(ruta_csv, index=False)
print(f"✅ Guardado: {ruta_csv}")

# ============================================================
# 5. VISUALIZACIÓN
# ============================================================
plt.figure(figsize=(14, 14))
pos = nx.spring_layout(subgrafo_500, k=0.2, iterations=100, seed=42)

grados_viz = dict(subgrafo_500.degree())
tamaños = [grados_viz[n] * 5 + 20 for n in subgrafo_500.nodes()]
colores = ['red' if n in GENES_SEMILLA else 'lightblue' for n in subgrafo_500.nodes()]

nx.draw_networkx_nodes(subgrafo_500, pos, node_size=tamaños,
                       node_color=colores, alpha=0.8)
nx.draw_networkx_edges(subgrafo_500, pos, alpha=0.2, width=0.3)

etiquetas = {n: n for n in subgrafo_500.nodes() 
             if n in GENES_SEMILLA or grados_viz[n] > 15}
nx.draw_networkx_labels(subgrafo_500, pos, labels=etiquetas, 
                        font_size=8, font_weight='bold')

plt.title(f"Red de Reparación del ADN\n"
          f"{subgrafo_500.number_of_nodes()} nodos, "
          f"{subgrafo_500.number_of_edges()} aristas", fontsize=13)
plt.axis('off')

ruta_img = os.path.join(DIR_RESULTADOS, f"grafo_500_{NOMBRE_PROCESO}.png")
plt.savefig(ruta_img, dpi=300, bbox_inches='tight')
plt.show()
print(f"✅ Imagen: {ruta_img}")

print("\n🎉 ¡Listo! Envía los archivos .pkl y .csv al coordinador.")