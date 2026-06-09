# 02_clustering — Agrupación Geoespacial de Faenas en 18 Clusters

Agrupa las faenas mineras del norte y centro de Chile en clusters homogéneos usando HDBSCAN con validación DBCV. El resultado son **18 clusters regionales** que representan valles mineros o zonas operacionales compartidas.

---

## Archivos

| Archivo | Qué contiene |
|---------|-------------|
| `notebook_clustering_hdbscan_18_grupos.ipynb` | Notebook completo: exploración de datos, entrenamiento HDBSCAN, selección de hiperparámetros con Optuna (200 trials, función objetivo: −DBCV), visualización de clusters y exportación de resultados |

---

## Resultados (`resultados/`)

| Archivo | Qué contiene |
|---------|-------------|
| `clusters_18grupos_asignacion_dbcv.csv` | Asignación final de cada faena a su cluster usando validación DBCV — **resultado principal** (18 clusters + clase Noise) |
| `clusters_datos_completos_para_dashboard.csv` | Tabla expandida con cada cluster + todas sus métricas de infraestructura: agua estimada, demanda eléctrica, volumen de relaves, distancia al puerto, tipo de acceso. Entrada directa del dashboard. |
| `mapa_clusters_interactivo.html` | Mapa Leaflet con los 18 clusters visualizados sobre Chile. Abrir en el navegador. (**archivo LFS**) |

---

## Clusters Resultantes

Los clusters se nombran `[Región romana]-[número]`. Ejemplos de los más relevantes:

| Cluster | Faena Ancla | Producción 2024 (kt/año) |
|---------|------------|------------------------:|
| II-0 | Escondida (BHP) | 1,361 |
| II-2 | Chuquicamata + Codelco Norte | 883 |
| I-1 | Collahuasi + Quebrada Blanca QB2 | 767 |
| II-5 | Spence + Sierra Gorda | 485 |
| VI-0 | El Teniente (Codelco) | 356 |
| IV-1 | Los Pelambres (AMSA) | 331 |

Ver `06_reportes/INDICE_Y_RESUMEN_EJECUTIVO.md` para el listado completo con todas las métricas.

---

## Metodología

- **Algoritmo**: HDBSCAN (Hierarchical Density-Based Spatial Clustering)
- **Espacio de features**: coordenadas geográficas + variables operacionales de cada faena
- **Validación interna**: índice DBCV (Density-Based Clustering Validation)
- **Optimización de hiperparámetros**: Optuna, 200 trials
