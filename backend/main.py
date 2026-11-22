"""API REST - Red de proteínas cáncer de mama. Ejecutar: uvicorn main:app --reload"""
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator

import algoritmos as alg
import loader

app = FastAPI(title="DataBioAnalytic API", version="1.1")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

MIN_SCORE_Q = Query(loader.DEFAULT_MIN_SCORE, ge=loader.CACHE_MIN_SCORE, le=loader.MAX_SCORE)
MAX_NODOS_Q = Query(loader.MAX_NODOS_DEFECTO, ge=10, le=1000)


def _subgrafo(via: str, min_score: int, max_nodos: int = loader.MAX_NODOS_DEFECTO) -> dict:
    try:
        return loader.construir_grafo(via, min_score, max_nodos)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except FileNotFoundError as exc:
        raise HTTPException(500, f"Archivo de datos no encontrado: {exc.filename}")


def _ids(g: dict) -> list[str]:
    return [n["id"] for n in g["nodes"]]


@app.get("/api/grafo")
def grafo(via: str = "todas", min_score: int = MIN_SCORE_Q, max_nodos: int = MAX_NODOS_Q):
    _subgrafo(via, min_score, max_nodos)
    return loader.grafo_cytoscape(via, min_score, max_nodos)


@app.get("/api/algoritmos/union-find")
def api_union_find(via: str = "todas", min_score: int = MIN_SCORE_Q, max_nodos: int = MAX_NODOS_Q):
    g = _subgrafo(via, min_score, max_nodos)
    return alg.union_find(_ids(g), g["edges"])


@app.get("/api/algoritmos/mst")
def api_mst(via: str = "todas", min_score: int = MIN_SCORE_Q, max_nodos: int = MAX_NODOS_Q):
    g = _subgrafo(via, min_score, max_nodos)
    return alg.mst_kruskal(_ids(g), g["edges"])


@app.get("/api/algoritmos/dfs")
def api_dfs(origen: str = "ESR1", destino: str = "TP53", via: str = "todas",
            min_score: int = MIN_SCORE_Q, max_nodos: int = MAX_NODOS_Q,
            evitar_directo: bool = True,
            min_saltos: int = Query(2, ge=1, le=10), max_saltos: int = Query(7, ge=1, le=10)):
    g = _subgrafo(via, min_score, max_nodos)
    return alg.dfs_ruta(_ids(g), g["edges"], origen.upper(), destino.upper(),
                        evitar_directo, min_saltos, max_saltos)


@app.get("/api/algoritmos/flujo-maximo")
def api_flujo_maximo(origen: str = "ESR1", destino: str = "TP53", via: str = "todas",
                     min_score: int = MIN_SCORE_Q, max_nodos: int = MAX_NODOS_Q):
    g = _subgrafo(via, min_score, max_nodos)
    origen, destino = origen.strip().upper(), destino.strip().upper()
    ids = set(_ids(g))
    faltan = [x for x in (origen, destino) if x not in ids]
    if faltan:
        raise HTTPException(404, f"No están en el subgrafo actual: {faltan}")
    if origen == destino:
        raise HTTPException(400, "origen y destino deben ser distintos")
    return alg.ford_fulkerson(_ids(g), g["edges"], origen, destino)


class KnockoutIn(BaseModel):
    gen: Optional[str] = None            # compatibilidad: un solo gen
    genes: Optional[list[str]] = None    # knockout múltiple
    via: str = "todas"
    min_score: int = Field(loader.DEFAULT_MIN_SCORE, ge=loader.CACHE_MIN_SCORE, le=loader.MAX_SCORE)
    max_nodos: int = Field(loader.MAX_NODOS_DEFECTO, ge=10, le=1000)

    @model_validator(mode="after")
    def _unificar(self):
        lista = list(self.genes or [])
        if self.gen:
            lista.append(self.gen)
        lista = [g.strip().upper() for g in lista if g.strip()]
        if not lista:
            raise ValueError("Envía 'gen' o 'genes'")
        self.genes = list(dict.fromkeys(lista))
        return self


@app.post("/api/simulacion/knockout")
def api_knockout(body: KnockoutIn):
    g = _subgrafo(body.via, body.min_score, body.max_nodos)
    semillas = [n["id"] for n in g["nodes"] if n["is_seed"]]
    res = alg.knockout(_ids(g), g["edges"], body.genes, semillas)
    if not res["encontrado"]:
        raise HTTPException(404, res["motivo"])
    return res


@app.get("/api/proteina/{symbol}")
def api_proteina(symbol: str, min_score: int = Query(400, ge=0, le=1000)):
    try:
        det = loader.detalle_proteina(symbol, min_score)
    except FileNotFoundError as exc:
        raise HTTPException(500, f"Archivo de datos no encontrado: {exc.filename}")
    if det is None:
        raise HTTPException(404, f"Proteína '{symbol}' no encontrada")
    return det
