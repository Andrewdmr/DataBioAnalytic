# DataBioAnalytic — Plataforma de Análisis de Redes Biológicas en Cáncer de Mama

Aplicación Full-Stack para la exploración topológica y simulación de perturbaciones sobre redes de interacción proteína-proteína (PPI) asociadas al **cáncer de mama**, integrando datos de **STRING v12** y **Open Targets**.

---

## Arquitectura y Stack Tecnológico

El proyecto separa el motor de procesamiento bioinformático y ejecución de algoritmos de grafos de la visualización interactiva en navegador:

* **Backend (`backend/`):** Python 3, **FastAPI**, **Pandas** y **NumPy**. Implementación explícita de algoritmos de grafos sin cajas negras y generación de caché comprimida (`.npz`) para consulta en milisegundos.
* **Frontend (`frontend/`):** **React 18**, **TypeScript**, **Vite**, **Tailwind CSS**, **Cytoscape.js** (`react-cytoscapejs`) y **Lucide Icons**.
* **Fuentes de Datos (`datos_originales/`):**
  * `9606.protein.info.v12.0.txt` (mapeo de identificadores `ENSP` humanos a símbolos oficiales de genes).
  * `9606.protein.links.v12.0.txt` (interacciones proteína-proteína con `combined_score`).
  * `opentargets_cancer_mama.tsv` (puntuaciones de asociación gen-enfermedad en carcinoma de mama).

---

## Vías Biológicas Analizadas

La red filtra y clasifica los genes semilla y proteínas asociadas en tres ejes clave de la biología tumoral mamaria:

| Vía Biológica | Identificador | Color en Interfaz | Genes Semilla Representativos |
| :--- | :--- | :--- | :--- |
| **Ciclo Celular y Apoptosis** | `ciclo_y_apoptosis` | Verde neón (`#aaff00`) | `TP53`, `CDK4`, `CDK6`, `CCND1`, `RB1`, `BCL2`, `CASP3` |
| **Reparación de ADN** | `reparacion_adn` | Magenta neón (`#ff0090`) | `BRCA1`, `BRCA2`, `ATM`, `ATR`, `CHEK2`, `PALB2`, `PARP1` |
| **Señalización Hormonal** | `senalizacion_hormonal` | Cian neón (`#00e5ff`) | `ESR1`, `ESR2`, `PGR`, `ERBB2`, `EGFR`, `FOXA1`, `GATA3` |
| **Asociados Open Targets** | `asociado` | Ámbar (`#ffbb00`) | Top genes por `association_score` fuera de las semillas |

---

## Algoritmos Implementados (`backend/algoritmos.py`)

1. **Union-Find (Disjoint Set con compresión de caminos):**
   * Detecta componentes conexos e islas funcionales al variar el umbral de confianza (`min_score`).
   * *Comportamiento observado:* A `min_score = 900` (150 nodos, 462 aristas) se identifican 34 islas; al elevar a `min_score = 950` (339 aristas) la red se fragmenta en 47 sub-redes independientes.
2. **Árbol de Expansión Mínima — MST (Kruskal):**
   * Utiliza como peso $w = 1000 - \text{combined\_score}$ para conservar la columna vertebral de interacciones de mayor confianza experimental y funcional, atenuando el ruido visual en el grafo.
3. **Búsqueda en Profundidad — DFS (Iterativo con control de saltos):**
   * Traza cascadas de señalización entre un nodo `origen` y un nodo `destino` con soporte para `evitar_directo=True` y `min_saltos`, revelando mediadores intermedios (ej. `ESR1 → AKT1 → TP53`) en lugar de atajos triviales de un solo enlace.
4. **Simulación de Knockout Simple y Múltiple (Letalidad Sintética):**
   * Permite inhibir uno o varios genes simultáneamente (ej. `BRCA1 + PARP1` o `TP53 + AKT1`), recalculando el grafo para identificar proteínas recién aisladas y pares de genes semilla que pierden conectividad entre sí.

---

## Estructura del Repositorio

```text
DataBioAnalytic/
├── backend/
│   ├── algoritmos.py         # Implementación de Union-Find, Kruskal (MST), DFS y Knockout
│   ├── loader.py             # Cruce de STRING v12 + Open Targets y gestión de caché .npz
│   ├── main.py               # Endpoints REST con FastAPI
│   └── requirements.txt      # Dependencias de Python
├── frontend/
│   ├── src/
│   │   ├── components/       # Lienzo Cytoscape, paneles laterales, inspector y controles
│   │   ├── api.ts            # Cliente HTTP hacia FastAPI
│   │   └── types.ts          # Tipado TypeScript de nodos, aristas y respuestas
│   ├── package.json
│   └── vite.config.ts
├── datos_originales/         # Archivos fuente de STRING y Open Targets (ignorados en Git)
├── scripts/                  # Prototipos iniciales y scripts exploratorios por vía
└── .gitignore
```

---

## Instalación y Ejecución Local

> **Nota sobre los datos:** Por su tamaño (~600 MB), los archivos de `datos_originales/` no están incluidos en el repositorio. Colócalos en `datos_originales/` antes del primer arranque; el backend generará automáticamente `backend/cache/links_400.npz` en la primera ejecución.

### 1. Levantar el Backend (Terminal 1)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

La API quedará disponible en `http://localhost:8000/api` (documentación interactiva Swagger en `http://localhost:8000/docs`).

### 2. Levantar el Frontend (Terminal 2)

```bash
cd frontend
npm install
npm run dev
```

Abre `http://localhost:5173` en tu navegador. Si necesitas apuntar a otra URL de backend, configura la variable de entorno `VITE_API`.

---

## Endpoints Principales de la API

* `GET /api/grafo?via=todas&min_score=900&max_nodos=150` — Devuelve nodos, aristas y el nodo `hub` principal formateados para Cytoscape.js.
* `GET /api/algoritmos/union-find` — Agrupa los nodos del subgrafo actual por componente conexo.
* `GET /api/algoritmos/mst` — Identifica las aristas pertenecientes al Árbol de Expansión Mínima.
* `GET /api/algoritmos/dfs?origen=ESR1&destino=TP53&min_saltos=2&evitar_directo=true` — Calcula rutas de señalización multi-salto.
* `POST /api/simulacion/knockout` — Simula la eliminación de una lista de genes (`{"genes": ["BRCA1", "PARP1"]}`) y reporta el impacto topológico.
* `GET /api/proteina/{symbol}` — Retorna metadatos de Open Targets e interacciones directas de un gen específico.