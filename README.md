# Análisis de Red de Proteínas — Cáncer de Mama

# 📑 Estructura del Proyecto

```text
\DataBioAnalytic\
│
├── 📁 datos_originales\
│   ├── 9606.protein.info.v12.0.txt             # Datos de STRING
│   ├── 9606.protein.links.v12.0.txt            # Datos de STRING
│   └── opentargets_cancer_mama.tsv             # Datos de Open Targets
│
├── 📁 scripts\
│   ├── proceso_reparacion_adn.py               # Diego
│   ├── señalizacion_hormonal.py                # Compañero 1
│   ├── ciclo_y_optosis.py                      # Compañero 2
│   ├── unir_equipo.py                          # Coordinador
│   └── analisis_algoritmos.py                  # Análisis final
│
├── 📁 subgrafos\
│   ├── subgrafo_500_reparacion_adn.pkl         # Tú
│   ├── subgrafo_500_senalizacion_hormonal.pkl  # Compañero 1
│   └── subgrafo_500_ciclo_celular.pkl          # Compañero 2
│
├── 📁 resultados\
│   ├── grafo_equipo_cancer_mama.png
│   ├── grafo_mst_equipo.png
│   ├── grafo_componentes.png
│   ├── aristas_equipo_cancer_mama.csv
│   └── metricas_equipo_cancer_mama.csv
```

### 🔗 Fuentes de datos
* Los datos de asociaciones de cáncer de mama se descargaron desde la [Plataforma de Open Targets](https://platform.opentargets.org/disease/MONDO_0007254/associations).

---
Proyecto de análisis computacional de una red de interacciones proteína-proteína
asociada al cáncer de mama, usando datos de STRING y Open Targets.

## Integrantes y Procesos Biológicos

| Integrante | Proceso | Genes Semilla |
|------------|---------|---------------|
| [Diego] | Reparación del ADN | BRCA1, BRCA2, PALB2, RAD51, ATM, CHEK2, BARD1, BRIP1, TP53 |
| [Gaspar] | Señalización hormonal | ESR1, ESR2, PGR, ERBB2, EGFR, ERBB3, ERBB4, AR, FOXA1, GATA3 |
| [Nicolas] | Ciclo celular y apoptosis | CDK4, CDK6, CCND1, MYC, PIK3CA, AKT1, PTEN, MDM2, BCL2, BAX |

## Algoritmos aplicados
- DFS / Union-Find → Componentes conectados
- MST (Kruskal) → Árbol de expansión mínima

## Estructura del proyecto
- `datos_originales/`: Archivos crudos de STRING (no incluidos en el repo)
- `scripts/`: Códigos Python
- `subgrafos/`: Subgrafos generados (.pkl)
- `resultados/`: Imágenes y CSVs de salida
