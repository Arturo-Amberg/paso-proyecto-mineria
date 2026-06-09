# 05_optimizacion — Optimización Espacial de Zonas por Cluster

Para cada uno de los 18 clusters, identifica la zona óptima de 30 km de radio que maximiza un conjunto de funciones objetivo ligadas a productividad, infraestructura compartida, inversión futura y riesgo ambiental.

---

## Archivos

| Archivo | Qué contiene |
|---------|-------------|
| `optimizacion_zonas_por_cluster.py` | Algoritmo principal. Evalúa una grilla de centros de zona dentro de cada cluster y calcula los 5 scores (F1–F5) para cada punto. |
| `analisis_sensibilidad_mcdm.py` | Análisis de sensibilidad MCDM. Varía los pesos de F1–F5 sistemáticamente y evalúa si el ranking de zonas cambia, validando la robustez del resultado. |
| `resultados/zonas_optimas_por_cluster.json` | Coordenadas del centro óptimo por cluster + scores F1–F5 + métricas de infraestructura de la zona ganadora |
| `resultados/ranking_sensibilidad_mcdm.csv` | Ranking de clusters bajo diferentes esquemas de pesos MCDM |

---

## Funciones Objetivo

| Función | Qué mide | Peso base |
|---------|----------|-----------|
| F1 — Densidad productiva | Faenas de categoría A/B/C + concentradoras dentro del radio de 30 km | 35% |
| F2 — Riesgo ambiental | Depósitos de relaves + proyectos SEIA rechazados (penalización) | −15% |
| F3 — Pipeline de inversión | Capital SEIA aprobado en la zona (proxy de proyectos futuros) | 30% |
| F4 — Nexo agua-energía | Plantas desaladoras + subestaciones eléctricas dentro del radio | 20% |
| F5 — Oportunidad compuesta | 0.35·F1 + 0.30·F3 + 0.20·F4 − 0.15·F2 | (combinada) |

---

## Cómo Ejecutar

```bash
# Generar zonas óptimas (produce zonas_optimas_por_cluster.json)
python optimizacion_zonas_por_cluster.py

# Análisis de sensibilidad (produce ranking_sensibilidad_mcdm.csv)
python analisis_sensibilidad_mcdm.py
```

**Datos que deben estar disponibles:**
- `../01_datos/raw/catastro_836_depositos_relaves_chile_oct2025.csv`
- `../01_datos/raw/proyectos_seia_evaluacion_ambiental.xlsx`
- `../01_datos/raw/plantas_desaladoras_operativas_y_proyectadas.csv`
- `../02_clustering/resultados/clusters_datos_completos_para_dashboard.csv`
