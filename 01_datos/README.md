# 01_datos — Datos del Proyecto

---

## `raw/` — Datos Fuente (sin modificar)

Todos los archivos de entrada originales usados en el pipeline.

| Archivo | Qué contiene |
|---------|-------------|
| `produccion_historica_mensual_faenas.xlsx` | Producción mensual de cobre (kt Cu) por faena, serie histórica completa |
| `produccion_historica_anual_top25_faenas.csv` | Producción anual de las 25 faenas más grandes |
| `precio_cobre_mensual_usd_libra.csv` | Precio mensual del cobre en USD/libra |
| `faenas_coordenadas_y_accesibilidad_logistica.csv` | 26 faenas con coordenadas GPS, distancia al puerto más cercano, acceso ferroviario y tipo de mineral |
| `proyectos_seia_evaluacion_ambiental.xlsx` | Proyectos mineros en el SEIA: estado (aprobado/rechazado/en revisión), inversión declarada, región |
| `catastro_836_depositos_relaves_chile_oct2025.csv` | Catastro nacional completo de relaves: 836 depósitos, 129 activos, volumen autorizado vs. depositado, estado (activo/inactivo/abandonado), coordenadas |
| `centrales_electricas_interconectadas.csv` | Centrales generadoras conectadas al SEN (tipo, capacidad MW, región) |
| `lineas_transmision_electrica_sen.csv` | Red de líneas de transmisión del Sistema Eléctrico Nacional |
| `subestaciones_electricas.csv` | Subestaciones de transformación con coordenadas |
| `estaciones_meteorologicas.csv` | Estaciones meteorológicas con coordenadas (usadas para variables climáticas del modelo) |
| `plantas_desaladoras_operativas_y_proyectadas.csv` | 17 plantas desaladoras operativas + 4 en construcción + 3 con EIA aprobado, capacidad l/s, operador, uso (minero/municipal) |
| `puertos_exportacion_cobre.csv` | Puertos de exportación con coordenadas, tamaño (Grande/Mediano/Pequeño), capacidad |
| `datos_clustering_valles_mineros.csv` | Base geoespacial del clustering: ~9.8M filas con puntos de interés por valle minero (**archivo LFS**) |

> **No incluido**: `DerechosAgua.xlsx` (~54 MB, 44,942 registros DGA de derechos de agua). Descargar desde la DGA y colocar aquí.

---

## `procesados/` — Datos Listos para Modelar

Archivos ya transformados que entran directamente a los notebooks de pronóstico y al script del dashboard.

| Archivo | Qué contiene |
|---------|-------------|
| `dataset_principal_entrenamiento_modelos.csv` | **Dataset maestro de entrenamiento**: producción mensual por faena + features de precio del cobre, tipo de cambio, lags (1–12 meses), características de la faena (tamaño, empresa, tipo de mineral). Entrada de ambos modelos. |
| `produccion_anual_historica_todas_faenas.csv` | Producción anual histórica de todas las faenas en formato largo. El dashboard la lee directamente para construir los gráficos de producción por cluster. |
| `produccion_mensual_cochilco_formato_dashboard.xlsx` | Producción mensual en el formato original COCHILCO que consume el dashboard (distinto al archivo de `Bases/` — tiene diferente estructura de columnas). |
| `metadata_faenas_mineras.csv` | Tabla de referencia por faena: región, empresa operadora, tipo de mineral (sulfuro/óxido/mixto), clasificación de tamaño (SmallMed / LargeColossal), coordenadas |
| `asignacion_clusters_final_faenas.csv` | Asignación final de cada faena a su cluster geoespacial (resultado del clustering DavBou HDBSCAN) |
| `puente_faenas_cluster_id_coordenadas_tier.csv` | Tabla puente entre nombre de faena y cluster: 40 filas con `Match_Key`, coordenadas lat/lon, `Cluster_ID_Asignado`, `Tier_Asignado` (ORO/PLATA/BRONCE) y crecimiento acumulado 4 años. Usada por el dashboard para vincular faenas al mapa. |

---

## `geoespacial/` — Capas GIS para el Mapa

Datos vectoriales usados como capas de contexto en el mapa interactivo.

### `areas_protegidas_snaspe/` — Áreas Silvestres Protegidas del Estado

Shapefile del SNASPE (Sistema Nacional de Áreas Silvestres Protegidas). El dashboard lo usa para mostrar la proximidad de faenas y relaves a parques nacionales y reservas.

| Archivo | Descripción |
|---------|-------------|
| `areas_protegidas_snaspe.shp` | Geometrías de polígonos (~92 MB, **LFS**) |
| `areas_protegidas_snaspe.dbf` | Atributos: nombre, tipo de área, superficie (**LFS**) |
| `areas_protegidas_snaspe.shx` | Índice espacial (**LFS**) |
| `areas_protegidas_snaspe.prj` | Sistema de coordenadas (WGS84) (**LFS**) |
| `areas_protegidas_snaspe.cpg` | Codificación de caracteres (**LFS**) |

### `proyectos_sigex_exploracion/` — Proyectos de Exploración Minera SIGEX

Registro SERNAGEOMIN de proyectos de exploración activos: 931 proyectos de cobre en los 14 clusters.

| Archivo | Descripción |
|---------|-------------|
| `catastro_proyectos_exploracion_minera_sigex.csv` | Tabla completa: nombre, empresa, región, tipo de mineral, etapa de exploración, coordenadas |
| `proyectos_sigex_geometrias.shp` | Puntos de ubicación de cada proyecto (**LFS**) |
| `proyectos_sigex_geometrias.dbf` | Atributos del shapefile (**LFS**) |
| `proyectos_sigex_geometrias.shx` | Índice espacial (**LFS**) |
| `proyectos_sigex_geometrias.prj` | Sistema de coordenadas (**LFS**) |
