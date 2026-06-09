# Mining Cluster Analysis Reports — Index
### Chilean Copper Mining · FinalResultsFolder · March 2026

All reports are based on the dashboard `mining_clusters_v2` (build_dashboard_v2.py) and the
annual model v7 Ens_Segmentado production forecasts (2026–2032). Each report independently
selects the 6 most analytically interesting clusters for its specific dimension.

---

## Reports

| File | Area | 6 Clusters Selected | Key Finding |
|------|------|---------------------|-------------|
| `water_stress_cluster_report.md` | Water stress | II-0, II-2, I-1, II-5, VI-0, IV-1 | Aggregate demand falls -25% by 2032; I-1 (QB2) is severely underestimated |
| `electricity_cluster_report.md` | Electricity demand & energy mix | II-0, II-2, I-1, VI-0, IV-1, RM-0 | SING solar transition saves ~3,000 GWh/yr of coal by 2030; II-0 alone consumes 17 TWh/yr |
| `relaves_cluster_report.md` | Tailings storage capacity | II-0, II-5, VI-0, II-1, III-2, RM-0 | National remaining capacity: 9,569 Mm³; Escondida TSF: ~16 years remaining |
| `danger_medioambiente_cluster_report.md` | Environmental risk | III-2, IV-2, II-2, VI-0, III-0, RM-0 | III-2 (Copiapó): 102 PELIGRO relaves near 162k people — worst in Chile |
| `accessibility_cluster_report.md` | Port/rail/logistics | II-2, I-1, II-0, III-2, IV-1, VI-0 | Caserones: 160km mountain road, no pipeline — worst accessibility of any large mine |
| `forecast_uncertainty_cluster_report.md` | Model performance by cluster | III-1, III-2, II-0, I-1, VI-0, IV-1 | QB2 structural break: model forecasts 496 kt vs ~860 kt reality for I-1 |
| `cooperation_projects_report.md` | Inter-mine cooperation & shared infrastructure | 5 zones (14 clusters) | Collahuasi + QB2 building two desal plants 2.6 km apart — clearest missed JV; BHP Zone B surplus reaches 40 Mm³/yr by 2032 |

---

## National Data Summary

| Metric | Value | Source |
|--------|-------|--------|
| Mines in model | 26 annual / 28 monthly | Produccion_Master.csv |
| Clusters in dashboard | ~18 + Ruido + Otros | 2_regional_davbou_hdbs.csv |
| Tailings deposits | 836 total (129 active) | CATASTRO_RELAVES_CHILE_OCT2025.csv |
| DGA water rights | 44,942 records | DerechosAgua.xlsx |
| Annual production (2024) | ~5,600 kt Cu total modelled | Produccion_Master.csv |
| Forecast horizon | 2026–2032 (H+1 to H+7) | projections_2026_2032.csv |
| Model win rate (all mines) | 51.3% (Ens_Segmentado) | scoreboard_annual_v7.csv |

---

## Cross-Report Cluster Summary

| Cluster | Top Mine | Prod 2024 (kt) | Water (M m³/yr) | Elec (GWh/yr) | Relaves cap (Mm³) | Port dist | Env. risk |
|---------|---------|---------------|-----------------|---------------|-------------------|-----------|-----------|
| II-0 | Escondida | 1,361 | 122 | 16,332 | 2,065 | 155km | Low (desal) |
| II-2 | Chuquicamata | 883 | 57 | 10,596 | 0.1 | 133km | Medium |
| I-1 | Collahuasi+QB | 767 | 71* | 9,204* | 861 | 164km | Low-Med |
| II-5 | Spence | 485 | 38 | 5,820 | 1,532 | 122km | Low-Med |
| VI-0 | El Teniente | 356 | 33 | 4,272 | 1,441 | 116km | Medium (AP) |
| IV-1 | Los Pelambres | 331 | 31 | 3,972 | 650 | 158km | High (river) |
| RM-0 | Los Bronces | 289 | 27 | 3,468 | 1,104 | 122km | Medium (AP) |
| III-2 | Caserones | 249 | 23 | 2,988 | 1,117 | 160km | HIGH (relaves) |
| III-1 | Candelaria | 226 | 21 | 2,712 | 0.6 | 65km | Low |
| II-1 | Centinela | 193 | 13 | 2,316 | 1,200 | 148km | Low |
| IV-2 | Andacollo | 30 | 1.8 | 360 | 206 | 41km | HIGH (city) |

*I-1 water/electricity likely 30–40% higher at full QB2 capacity (model underestimates structural break)

---

## Recurring "Small Victories"

Across all reports, a consistent pattern emerges:

1. **Aggregate production is declining.** The model v7 forecasts that Chile's top 6 clusters
   will produce ~13% less copper in 2032 than in 2026. This is an industry-wide headwind.

2. **Declining production = declining environmental footprint.** Less production means less
   water demand (-25% by 2032), less electricity (-18% by 2032), fewer new tailings added
   annually. The carbon and water intensity of Chilean copper is falling even without efficiency
   improvements.

3. **Infrastructure has excess capacity.** As production falls, desalination plants, pipelines,
   port capacity, and grid connections are increasingly oversized relative to mine needs. This
   reduces unit costs but raises fixed-cost recovery questions for operators.

4. **The exception: I-1 (Collahuasi + QB2).** This is the one cluster bucking the trend. QB2
   is a major structural growth driver that the model cannot capture. All planning for Region I
   should use QB2-adjusted scenarios rather than model outputs.

5. **Legacy liabilities persist regardless of production.** 455 abandoned relaves and multiple
   historically polluted sites (Chañaral, Copiapó valley) represent environmental obligations
   that don't shrink with declining production. The social license problem is decoupled from
   current output levels.

---

## Suggested Thesis Integration

Each report ends with specific "next steps." The cross-cutting recommendations are:

- **QB2 external scenario:** Build a QB2 production scenario (200/250/330 kt/yr) and re-run
  water, electricity, and logistics projections for I-1. This alone covers 3 reports.
- **v8 feature proposal:** Climate/drought index for IV-1 and V-1 mines; Codelco dummy variable;
  mine expansion flag (covers forecast uncertainty report).
- **Risk composite index:** Combine water stress + relaves danger + environmental proximity
  into a single cluster risk score. Visualize on dashboard as a choropleth layer.
- **DS 248/2021 compliance overlay:** Map abandoned relaves by regulatory compliance status.
  This connects the relaves and danger reports.

---

*All reports generated: March 2026 · TrabajoTesis / FinalResultsFolder*
*Dashboard: `04_Dashboard/outputs/mining_clusters_v2.html` (~5 MB)*
*Model: `03_Forecasting/annual_model/Modelo_Anual_FinalV1.ipynb` (v7)*
