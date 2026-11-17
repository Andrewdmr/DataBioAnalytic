"""Carga y cruce de datos STRING v12 + Open Targets (cáncer de mama).

Estrategia de memoria
---------------------
`9606.protein.links.v12.0.txt` pesa ~600 MB (~13.7 M filas). Se lee UNA sola vez
en chunks, descartando todo lo que esté por debajo de CACHE_MIN_SCORE y
codificando los IDs ENSP como enteros (int32). El resultado (unos pocos MB) se
guarda en `backend/cache/links_*.npz`, así los reinicios posteriores son
instantáneos. Los filtros por vía / min_score se aplican luego con numpy.
"""
from __future__ import annotations

import os
from functools import lru_cache

import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_DATOS = os.environ.get("DATOS_DIR", os.path.join(BASE_DIR, "datos_originales"))
DIR_CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")

ARCHIVO_INFO = os.path.join(DIR_DATOS, "9606.protein.info.v12.0.txt")
ARCHIVO_LINKS = os.path.join(DIR_DATOS, "9606.protein.links.v12.0.txt")
ARCHIVO_OT = os.path.join(DIR_DATOS, "opentargets_cancer_mama.tsv")

CACHE_MIN_SCORE = 400      # piso de score guardado en caché
DEFAULT_MIN_SCORE = 900
MAX_SCORE = 999
MAX_NODOS_DEFECTO = 150    # semillas + interactores con mayor association_score
PREFIJO_ENSP = "9606.ENSP"

# ---------------------------------------------------------------------------
# Vías biológicas (genes semilla de scripts/ y README.md) y colores neón
# (paleta de scripts/app2.py)
# ---------------------------------------------------------------------------
PATHWAYS: dict[str, list[str]] = {
    "ciclo_y_apoptosis": ["CDK4", "CDK6", "CCND1", "MYC", "PIK3CA",
                          "AKT1", "PTEN", "MDM2", "BCL2", "BAX"],
    "reparacion_adn": ["BRCA1", "BRCA2", "PALB2", "RAD51", "ATM",
                       "CHEK2", "BARD1", "BRIP1", "TP53"],
    "senalizacion_hormonal": ["ESR1", "ESR2", "PGR", "ERBB2", "EGFR",
                              "ERBB3", "ERBB4", "AR", "FOXA1", "GATA3"],
}
PATHWAY_COLORS: dict[str, str] = {
    "ciclo_y_apoptosis": "#aaff00",       # verde neón
    "reparacion_adn": "#ff0090",          # magenta neón
    "senalizacion_hormonal": "#00e5ff",   # cian neón
    "asociado": "#ffbb00",               # genes Open Targets sin vía
}
VIA_ASOCIADO = "asociado"
VIAS_VALIDAS = ["todas", *PATHWAYS]


# ---------------------------------------------------------------------------
# Carga de tablas
# ---------------------------------------------------------------------------
@lru_cache(maxsize=1)
def cargar_info() -> pd.DataFrame:
    """Tabla STRING info: ENSP -> símbolo. Columna `ensp` = entero."""
    info = pd.read_csv(ARCHIVO_INFO, sep="\t", usecols=[0, 1],
                       names=["string_protein_id", "symbol"], header=0)
    info["ensp"] = (info["string_protein_id"]
                    .str.replace(PREFIJO_ENSP, "", regex=False).astype("int64"))
    return info.drop_duplicates("symbol").reset_index(drop=True)


@lru_cache(maxsize=1)
def cargar_opentargets() -> pd.DataFrame:
    """Open Targets indexado por símbolo; 'No data' -> NaN."""
    ot = pd.read_csv(ARCHIVO_OT, sep="\t", na_values=["No data"])
    return ot.drop_duplicates("symbol").set_index("symbol")


def _ruta_cache() -> str:
    return os.path.join(DIR_CACHE, f"links_{CACHE_MIN_SCORE}.npz")


@lru_cache(maxsize=1)
def cargar_links() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Devuelve (a, b, score) con aristas únicas (a<b) y score >= CACHE_MIN_SCORE."""
    ruta = _ruta_cache()
    if os.path.exists(ruta):
        d = np.load(ruta)
        return d["a"], d["b"], d["s"]

    info = cargar_info()
    validos = set(info["ensp"].tolist())
    partes = []
    lector = pd.read_csv(ARCHIVO_LINKS, sep=" ", chunksize=1_000_000,
                         dtype={"protein1": "string", "protein2": "string",
                                "combined_score": "int32"})
    for bloque in lector:
        bloque = bloque[bloque["combined_score"] >= CACHE_MIN_SCORE]
        a = bloque["protein1"].str[len(PREFIJO_ENSP):].astype("int64")
        b = bloque["protein2"].str[len(PREFIJO_ENSP):].astype("int64")
        mask = (a < b) & a.isin(validos) & b.isin(validos)  # STRING lista A-B y B-A
        partes.append(pd.DataFrame({"a": a[mask].astype("int32"),
                                    "b": b[mask].astype("int32"),
                                    "s": bloque.loc[mask, "combined_score"].astype("int16")}))
    df = pd.concat(partes, ignore_index=True)
    os.makedirs(DIR_CACHE, exist_ok=True)
    np.savez_compressed(ruta, a=df["a"].to_numpy(), b=df["b"].to_numpy(), s=df["s"].to_numpy())
    return df["a"].to_numpy(), df["b"].to_numpy(), df["s"].to_numpy()


def _score_ot(symbol: str) -> float:
    ot = cargar_opentargets()
    if symbol in ot.index:
        v = ot.at[symbol, "globalScore"]
        if pd.notna(v):
            return round(float(v), 4)
    return 0.0


# ---------------------------------------------------------------------------
# Construcción del subgrafo filtrado
# ---------------------------------------------------------------------------
def _semillas(via: str) -> dict[str, list[str]]:
    """symbol -> lista de vías a las que pertenece, para la vía pedida."""
    if via not in VIAS_VALIDAS:
        raise ValueError(f"Vía inválida '{via}'. Opciones: {VIAS_VALIDAS}")
    vias = PATHWAYS if via == "todas" else {via: PATHWAYS[via]}
    out: dict[str, list[str]] = {}
    for nombre, genes in vias.items():
        for g in genes:
            out.setdefault(g, []).append(nombre)
    return out


@lru_cache(maxsize=32)
def construir_grafo(via: str = "todas", min_score: int = DEFAULT_MIN_SCORE,
                    max_nodos: int = MAX_NODOS_DEFECTO) -> dict:
    """Grafo = semillas de la(s) vía(s) + genes con mayor association_score de Open Targets.

    Los nodos se eligen SIN exigir conexión con una semilla; después se cargan
    solo las aristas entre esos nodos con combined_score >= min_score, de modo
    que al subir el umbral aparecen islas reales.
    Retorna dict con `nodes` y `edges` (source/target = símbolos,
    `combined_score`, `weight` = 1000 - score).
    """
    min_score = min(max(int(min_score), CACHE_MIN_SCORE), MAX_SCORE)
    info = cargar_info()
    ensp_a_sym = dict(zip(info["ensp"], info["symbol"]))
    sym_a_ensp = dict(zip(info["symbol"], info["ensp"]))

    semillas = _semillas(via)
    vias_de_gen: dict[str, list[str]] = {}          # pertenencia a cualquier vía
    for nombre, genes in PATHWAYS.items():
        for g in genes:
            vias_de_gen.setdefault(g, []).append(nombre)

    # ---- selección de nodos: semillas + top Open Targets hasta max_nodos
    simbolos = [g for g in semillas if g in sym_a_ensp][:max_nodos]
    ya = set(simbolos)
    ot = cargar_opentargets()["globalScore"].dropna().sort_values(ascending=False)
    for g in ot.index:
        if len(simbolos) >= max_nodos:
            break
        if g not in ya and g in sym_a_ensp:
            simbolos.append(g)
            ya.add(g)
    nodos_ids = [int(sym_a_ensp[g]) for g in simbolos]

    # ---- aristas inducidas entre esos nodos
    a, b, s = cargar_links()
    arr_nodos = np.array(nodos_ids, dtype=np.int32)
    m = (s >= min_score) & np.isin(a, arr_nodos) & np.isin(b, arr_nodos)
    a, b, s = a[m], b[m], s[m]
    edges, grado = [], {n: 0 for n in nodos_ids}
    for ea, eb, es in zip(a.tolist(), b.tolist(), s.tolist()):
        sa, sb = ensp_a_sym[ea], ensp_a_sym[eb]
        edges.append({"id": f"{sa}--{sb}", "source": sa, "target": sb,
                      "combined_score": es, "weight": 1000 - es})
        grado[ea] += 1
        grado[eb] += 1

    # ---- nodos
    nodes = []
    for sym, n in zip(simbolos, nodos_ids):
        vias_nodo = vias_de_gen.get(sym) or [VIA_ASOCIADO]
        nodes.append({
            "id": sym, "label": sym, "string_id": f"{PREFIJO_ENSP}{n:011d}",
            "via": vias_nodo[0], "vias": vias_nodo,
            "color": PATHWAY_COLORS[vias_nodo[0]],
            "association_score": _score_ot(sym),
            "is_seed": sym in semillas, "degree": grado[n], "is_hub": False,
        })
    hub = max(nodes, key=lambda x: x["degree"]) if nodes else None
    if hub:
        hub["is_hub"] = True
    return {"nodes": nodes, "edges": edges, "hub": hub["id"] if hub else None,
            "via": via, "min_score": min_score}


def grafo_cytoscape(via: str = "todas", min_score: int = DEFAULT_MIN_SCORE,
                    max_nodos: int = MAX_NODOS_DEFECTO) -> dict:
    """Formato `elements` de Cytoscape.js."""
    g = construir_grafo(via, min_score, max_nodos)
    return {
        "via": via, "min_score": g["min_score"], "hub": g["hub"],
        "total_nodos": len(g["nodes"]), "total_aristas": len(g["edges"]),
        "colores_vias": PATHWAY_COLORS,
        "elements": {"nodes": [{"data": n} for n in g["nodes"]],
                     "edges": [{"data": e} for e in g["edges"]]},
    }


def detalle_proteina(symbol: str, min_score: int = CACHE_MIN_SCORE) -> dict | None:
    """Detalle de Open Targets + interacciones directas (todas las del cache)."""
    info = cargar_info()
    fila = info[info["symbol"].str.upper() == symbol.upper()]
    if fila.empty:
        return None
    symbol, ensp = fila.iloc[0]["symbol"], int(fila.iloc[0]["ensp"])
    ensp_a_sym = dict(zip(info["ensp"], info["symbol"]))
    a, b, s = cargar_links()
    m = ((a == ensp) | (b == ensp)) & (s >= min_score)
    vecinos = [{"symbol": ensp_a_sym[int(y if x == ensp else x)], "combined_score": int(sc)}
               for x, y, sc in zip(a[m].tolist(), b[m].tolist(), s[m].tolist())]
    vecinos.sort(key=lambda v: v["combined_score"], reverse=True)

    ot = cargar_opentargets()
    ot_data = None
    if symbol in ot.index:
        ot_data = {k: (None if pd.isna(v) else (v.item() if hasattr(v, "item") else v))
                   for k, v in ot.loc[symbol].items()}
    vias = [v for v, genes in PATHWAYS.items() if symbol in genes]
    return {"symbol": symbol, "string_id": f"{PREFIJO_ENSP}{ensp:011d}",
            "vias": vias, "color": PATHWAY_COLORS[vias[0]] if vias else None,
            "association_score": _score_ot(symbol), "opentargets": ot_data,
            "total_interacciones": len(vecinos), "interacciones": vecinos}
