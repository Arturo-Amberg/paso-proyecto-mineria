# 06_reportes — Reportes Analíticos por Cluster

Siete reportes detallados que analizan distintas dimensiones críticas de los 18 clusters mineros. Cada reporte selecciona los 6 clusters más relevantes para su dimensión y hace un análisis profundo con datos de producción, proyecciones del modelo y capas de infraestructura del dashboard.

**Empezar por**: `INDICE_Y_RESUMEN_EJECUTIVO.md`

---

## Reportes

| Archivo | Qué analiza | Hallazgo principal |
|---------|-------------|-------------------|
| `INDICE_Y_RESUMEN_EJECUTIVO.md` | Resumen de todos los clusters: producción, agua, electricidad, relaves, distancia al puerto, riesgo ambiental | La producción total cae ~13% al 2032; I-1 (QB2) es la única excepción al alza |
| `estres_hidrico_demanda_agua_por_cluster.md` | Demanda de agua estimada por cluster usando factores Cochilco (sulfuros 93 m³/t, óxidos 35 m³/t), fuentes de agua (desaladoras, acuífero, ríos), proyección 2026–2032 | Demanda total cae −25% al 2032; II-2 (Calama) tiene el mayor riesgo estructural por dependencia del acuífero Loa estresado; IV-1 (Los Pelambres) enfrenta conflicto social por el río Choapa |
| `demanda_electrica_por_cluster.md` | Consumo eléctrico estimado (factor 12 MWh/t), mix energético SING/SIC, nexo agua-energía (desaladoras), impacto de transición solar | II-0 (Escondida) consume ~16,332 GWh/año — más que toda la generación hidroeléctrica del SIC en un año normal; transición solar SING ahorra ~3,000 GWh/año de carbón al 2030 |
| `relaves_capacidad_y_riesgo_regulatorio.md` | Catastro de 836 depósitos (129 activos, 455 abandonados), capacidad remanente en años, DS 248/2021 | Capacidad remanente nacional: 9,569 Mm³; Escondida tiene ~16 años de vida útil en su TSF actual |
| `riesgo_ambiental_comunidades_cercanas.md` | Score de riesgo ambiental compuesto (D1: relaves <10 km de ciudad, D2: abandonados, D3: población expuesta, D4: áreas protegidas) | III-2 (Copiapó): 102 depósitos PELIGRO a <10 km de 162,449 personas — el cluster más crítico de Chile; episodio aluvión 2015 movilizó relaves hasta el Pacífico |
| `accesibilidad_logistica_puertos_y_vias.md` | Distancia al puerto más cercano, red ferroviaria FCAB, oleoductos de concentrado, rutas de camión, cuellos de botella | Caserones: 160 km de carretera de montaña sin ferrocarril ni oleoducto — peor accesibilidad de cualquier faena grande; Escondida tiene oleoducto de concentrado a Coloso |
| `incertidumbre_y_rendimiento_modelo_por_cluster.md` | Win Rate y MAPE por cluster en el modelo anual v7, qué clusters el modelo predice bien vs. mal y por qué | III-1 (Candelaria): 74.1% WR — mejor predictor; I-1 (QB2): 33.3% WR — el modelo pronostica 496 kt vs. ~860 kt real al 2026, por el quiebre estructural de QB2 post-entrenamiento |
| `oportunidades_cooperacion_infraestructura_compartida.md` | 5 zonas de cooperación inter-cluster, proyectos existentes y oportunidades identificadas | Collahuasi + QB2 construyen dos plantas desaladoras a 2.6 km de distancia — la oportunidad JV más obvia no aprovechada; planta desaladora Codelco Norte (EIA aprobado, 2025) puede abastecer al 108% de la demanda de II-2 |

---

## Nomenclatura de Clusters

Los clusters se nombran `[Región romana]-[número]`:
- **I** = Tarapacá, **II** = Antofagasta, **III** = Atacama, **IV** = Coquimbo, **VI** = O'Higgins, **RM** = Región Metropolitana
- El número es el índice del cluster dentro de esa región (0 = el más grande)

Ejemplo: `II-0` = Región de Antofagasta, cluster 0 → Escondida.
