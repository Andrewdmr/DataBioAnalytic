# Análisis de Red de Proteínas — Cáncer de Mama

Proyecto de análisis computacional de una red de interacciones proteína-proteína
asociada al cáncer de mama, usando datos de STRING y Open Targets.

## Integrantes y Procesos Biológicos

| Integrante | Proceso | Genes Semilla |
|------------|---------|---------------|
| [Diego] | Reparación del ADN | BRCA1, BRCA2, PALB2, RAD51, ATM, CHEK2, BARD1, BRIP1, TP53 |
| [Compañero 1] | Señalización hormonal | ESR1, ESR2, PGR, ERBB2, EGFR, ERBB3, ERBB4, AR, FOXA1, GATA3 |
| [Compañero 2] | Ciclo celular y apoptosis | CDK4, CDK6, CCND1, MYC, PIK3CA, AKT1, PTEN, MDM2, BCL2, BAX |

## Algoritmos aplicados
- DFS / Union-Find → Componentes conectados
- MST (Kruskal) → Árbol de expansión mínima

## Estructura del proyecto
- `datos_originales/`: Archivos crudos de STRING (no incluidos en el repo)
- `scripts/`: Códigos Python
- `subgrafos/`: Subgrafos generados (.pkl)
- `resultados/`: Imágenes y CSVs de salida
