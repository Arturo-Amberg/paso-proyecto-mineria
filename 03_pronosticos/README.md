# 03_pronosticos — Modelos de Pronóstico de Producción

Dos modelos de pronóstico de producción de cobre: **anual** (1–7 años) y **mensual** (1–60 meses). Ambos usan ensambles de árboles de decisión con validación rolling-origin (sin filtración de datos futuros).

---

## Modelo Anual (`modelo_anual/`)

Predice producción anual (kt Cu) para **26 faenas**, horizontes 2026–2032.

**Mejor modelo**: `Ens_Segmentado` — LightGBM segmentado por tamaño de faena.

| Métrica | Valor |
|---------|-------|
| MAPE mediano | ~11% |
| Win Rate | 51.3% |
| Faenas | 26 |
| Horizontes | H+1 a H+7 (años) |
| Combinaciones de ensamble probadas | 90 |

| Archivo | Qué contiene |
|---------|-------------|
| `notebook_modelo_anual_lightgbm_ensemble_v10.ipynb` | Notebook completo: preprocesamiento, entrenamiento, validación rolling-origin, selección de ensamble |
| `ejecutar_pronostico_anual.py` | Script para correr el modelo desde consola sin abrir el notebook |
| `resultados/proyecciones_26_faenas_anuales_2026_2032.csv` | **Salida principal**: proyección de producción anual por faena y año |
| `resultados/proyecciones_escenarios_base_alcista_bajista.csv` | Tres escenarios: base (modelo), alcista (+15%), bajista (−15%) |
| `resultados/comparacion_todos_modelos_anuales_mape_wr.csv` | Scoreboard de todos los modelos probados: MAPE y Win Rate por horizonte y faena |

---

## Modelo Mensual (`modelo_mensual/`)

Predice producción mensual (kt Cu) para **28 faenas**, horizontes 2026–2032.

**Mejor modelo**: `LGB_Meta_Stack` — meta-stacking con segmentación Small/Med vs Large/Colossal.

| Métrica | Valor |
|---------|-------|
| MAPE mediano | ~10% |
| Win Rate | ~68% |
| Faenas | 28 |
| Horizontes | H+1 a H+60 (meses) |
| Combinaciones probadas | 540 |

| Archivo | Qué contiene |
|---------|-------------|
| `notebook_modelo_mensual_lightgbm_ensemble_v35.ipynb` | Notebook completo de entrenamiento y validación |
| `generar_proyecciones_mensuales.py` | Script para regenerar las proyecciones 2026–2032 |
| `resultados/proyecciones_28_faenas_mensuales_2026_2032.csv` | **Salida principal**: proyección mensual por faena y mes |
| `resultados/comparacion_todos_modelos_mensuales_mape_wr.csv` | Scoreboard V35: MAPE y Win Rate por horizonte |

---

## Metodología Común

- **Validación**: Rolling-origin con 9 orígenes (2010–2018), el modelo nunca ve datos futuros
- **Segmentación**: Faenas grandes/colosales se entrenan separadas de pequeñas/medianas
- **Variable predicha**: `log(Producción_H / Producción_origen)` — ratio logarítmico
- **Baseline de comparación**: naive ("la producción no cambia") — el modelo gana cuando el WR > 50%
- **Métrica primaria**: MAPE | **Métrica secundaria**: Win Rate
- **Limitación conocida**: El modelo subestima el cluster I-1 (Collahuasi + QB2) porque la expansión QB2 (de 13 kt en 2022 a 208 kt en 2024) ocurre después de todos los orígenes de entrenamiento
