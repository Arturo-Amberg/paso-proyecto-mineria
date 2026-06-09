# 04_dashboard — Dashboard Interactivo de Minería Chile

Dashboard HTML con mapa Leaflet que muestra los 18 clusters mineros, las 26 faenas principales, sus proyecciones de producción 2026–2032 y métricas de infraestructura por cluster.

---

## Archivos

| Archivo | Qué contiene |
|---------|-------------|
| `dashboard_mineria_chile_interactivo.html` | **Dashboard ya construido** (~13 MB). Abrir directamente en el navegador, no requiere servidor ni instalación. (**archivo LFS**) |
| `construir_dashboard.py` | Script que genera el dashboard desde cero. Lee los CSVs de clustering y pronósticos y produce el HTML. |
| `datos_clusters_poligonos_y_centroides_para_mapa.json` | JSON con los 18 clusters: polígono convexo (`hull`), centroide, etiqueta, color, región. El script lo usa para dibujar las fronteras de cada cluster en el mapa Leaflet. |

---

## Cómo Ver el Dashboard

```bash
open 04_dashboard/dashboard_mineria_chile_interactivo.html   # macOS
# o simplemente hacer doble click en el archivo
```

## Cómo Reconstruir el Dashboard

```bash
python construir_dashboard.py
```

**Archivos que deben existir antes de ejecutar:**
- `../02_clustering/resultados/clusters_datos_completos_para_dashboard.csv`
- `../03_pronosticos/modelo_anual/resultados/proyecciones_26_faenas_anuales_2026_2032.csv`
- `../03_pronosticos/modelo_mensual/resultados/proyecciones_28_faenas_mensuales_2026_2032.csv`

---

## Qué Muestra el Dashboard

- **Mapa interactivo**: 18 clusters sobre Chile, círculos escalados por producción, coloreados por región
- **Panel por cluster** (click en el mapa): producción histórica + proyecciones 2026–2032, gráfico de barras
- **Métricas por cluster**: demanda de agua estimada (M m³/año), consumo eléctrico (GWh/año), capacidad remanente de relaves, distancia al puerto, tipo de acceso logístico
- **Tabla de faenas**: ranking por producción, empresa, tipo de mineral, proyección 2032
