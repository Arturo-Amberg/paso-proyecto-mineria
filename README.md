# Paso Proyecto Minería — Pronóstico de Producción de Cobre Chile

Sistema completo de pronóstico de producción de cobre para las principales faenas mineras de Chile (2026–2032). Trabajo de tesis que incluye clustering geoespacial, modelos de ensamble LightGBM, optimización zonal y un dashboard interactivo.

---

## Estructura del Proyecto

| Carpeta | Qué contiene |
|---------|-------------|
| [`01_datos/`](01_datos/) | Datos fuente (producción, precios, infraestructura) + dataset procesado listo para modelar |
| [`02_clustering/`](02_clustering/) | Agrupación de faenas en 18 clusters geoespaciales con HDBSCAN |
| [`03_pronosticos/`](03_pronosticos/) | Modelo anual (26 faenas, 2026–2032) y mensual (28 faenas, 2026–2032) |
| [`04_dashboard/`](04_dashboard/) | Script de construcción + dashboard HTML interactivo ya generado |
| [`05_optimizacion/`](05_optimizacion/) | Optimización espacial de zonas por cluster con análisis MCDM |
| [`06_reportes/`](06_reportes/) | Reportes analíticos por cluster: agua, energía, relaves, ambiente, logística |

---

## Resultados Clave

| Modelo | Faenas | Horizonte | MAPE mediano | Win Rate |
|--------|--------|-----------|-------------|---------|
| Mensual V35 (LGB Meta-Stack) | 28 | 1–60 meses | ~10% | ~68% |
| Anual V10 (Ens. Segmentado) | 26 | 1–7 años | ~11% | 51.3% |

- **Producción base 2024**: ~5,600 kt Cu/año (26 faenas modeladas)
- **Proyección 2032**: ~4,900 kt Cu/año (−13%, descenso por ley del mineral)
- **Excepción**: Cluster I-1 (Collahuasi + QB2) — el modelo subestima por la expansión QB2

---

## Cómo Empezar

```bash
# 1. Ver el dashboard ya construido (no requiere instalación)
open 04_dashboard/dashboard_mineria_chile_interactivo.html

# 2. Reproducir pronóstico mensual
jupyter notebook 03_pronosticos/modelo_mensual/notebook_modelo_mensual_lightgbm_ensemble_v35.ipynb

# 3. Reproducir pronóstico anual
jupyter notebook 03_pronosticos/modelo_anual/notebook_modelo_anual_lightgbm_ensemble_v10.ipynb

# 4. Reconstruir el dashboard desde cero
python 04_dashboard/construir_dashboard.py
```

---

## Flujo de Trabajo

```
01_datos/ ──► 02_clustering/ ──► 03_pronosticos/ ──► 04_dashboard/
(fuentes)      (18 clusters)      (modelos)           (visualización)
                                        │
                               05_optimizacion/  ──► 06_reportes/
                               (zonas óptimas)        (análisis)
```

---

## Dependencias

```
python >= 3.10
lightgbm, xgboost, scikit-learn, optuna
pandas, numpy, geopandas, shapely
hdbscan, matplotlib, seaborn, folium
```

---

## Nota: Archivo de Derechos de Agua

`DerechosAgua.xlsx` (~54 MB, 44,942 registros DGA) no está incluido por tamaño. Descargarlo desde el portal de la **Dirección General de Aguas (DGA)** y colocarlo en `01_datos/raw/`.
