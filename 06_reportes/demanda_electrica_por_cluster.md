# Electricity Demand Analysis — Top 6 Mining Clusters in Chile
### Based on Dashboard `mining_clusters_v2` · Annual Model v7 · March 2026

---

## 1. Why Electricity Matters for Copper Mining

Electricity is the single largest operating cost component in modern copper mining, representing
between 20% and 35% of total cash costs depending on ore grade, processing method, and altitude.
Unlike diesel or water, electricity is both a consumable input and a strategic asset: the grid
connection infrastructure that feeds a mine shapes its long-term viability, and the cleanliness of
that grid directly determines the mine's Scope 2 carbon footprint — a variable that has become
central to ESG-linked financing and international commodity pricing.

Chile's copper sector consumes approximately **35–38 TWh per year**, or roughly 30% of the
country's total electricity generation. Within this sector, the six largest clusters analyzed here
account for an estimated **46,131 GWh/yr** at 2020–2024 average production levels — more than the
entire residential electricity consumption of Santiago. Understanding how that demand evolves
between 2026 and 2032 matters for four interlinked reasons:

1. **Grid planning**: Chile's Sistema Eléctrico Nacional (SEN) must invest in transmission
   infrastructure years before demand materializes. Production forecast errors propagate into
   over- or under-investment in high-voltage lines serving isolated desert corridors.

2. **Carbon accounting**: Under Chile's Green Taxonomy and the Paris Agreement NDC commitments,
   Codelco, BHP, Anglo American, and Antofagasta Minerals (AMSA) all carry internal electricity
   decarbonization targets. The trajectory of demand determines the scale of renewable procurement
   needed.

3. **Water-energy nexus**: Desalination (increasingly dominant in northern Chile) and high-altitude
   pumping (critical for Quebrada Blanca Phase 2, 4,800 m elevation) convert electricity into
   water. The two resource analyses cannot be read independently.

4. **Forecast validation**: Annual model v7 predicts mine-level production 1–7 years ahead. Its
   economic implications are most tangible when translated into electricity GWh — a unit that
   regulators, utilities, and ESG analysts directly consume.

The dashboard uses a single production-to-electricity conversion factor of **12.0 MWh per metric
ton of fine copper produced**. This factor, derived from sector-level statistics published by
Cochilco (2022, 2023) and cross-checked against mine-level energy disclosures in sustainability
reports, is a weighted average across ore processing stages:

| Stage | Typical intensity (MWh/t) | Share of total |
|---|---|---|
| Crushing, grinding, flotation | 6.5–8.0 | ~60% |
| Smelting and refining (electrolytic) | 2.0–3.0 | ~20% |
| Ancillary (ventilation, pumping, services) | 1.5–2.5 | ~15% |
| Desalination and water supply | 0.3–1.5 | ~5% |
| **Total (blended)** | **~12.0** | 100% |

Intensity varies significantly by operation type: hydrometallurgical SX-EW plants are less
energy-intensive than flotation-smelter routes, while underground mines require substantially more
ventilation power than open-pit equivalents. The 12.0 MWh/t factor should therefore be treated as
a representative benchmark, not a precise plant-level estimate.

---

## 2. Cluster Selection Rationale

The six clusters were selected as those with the highest estimated annual electricity demand
(2020–2024 average). Together they represent approximately **82% of Chile's modelled copper
production** and span the full spectrum of grid contexts: SING (northern thermal/solar-dominated)
and SIC (central hydro/wind-dominated), now unified as the SEN but historically distinct in
resource mix and pricing.

| Cluster | Top Mine | Grid | Avg Prod 2020–24 (kt/yr) | Elec Demand (GWh/yr) | % of Total |
|---------|----------|------|------------------------|----------------------|-----------|
| II-0 | Escondida | SING | 1,213.6 | 14,563 | 31.6% |
| II-2 | Chuquicamata | SING | 941.4 | 11,297 | 24.5% |
| I-1 | Collahuasi + QB | SING | 653.6 | 7,844 | 17.0% |
| VI-0 | El Teniente | SIC | 403.3 | 4,840 | 10.5% |
| IV-1 | Los Pelambres | SIC | 326.9 | 3,922 | 8.5% |
| RM-0 | Los Bronces | SIC | 305.4 | 3,665 | 7.9% |
| **Total** | | | **3,844.2** | **46,131** | **100%** |

The Rank-1 cluster (II-0, Escondida) alone demands more electricity than the entire SIC grid
produced from hydropower in an average non-drought year during the 2010s. This underscores why
the mining sector's load profile dominates northern Chile's grid planning horizon.

---

## 3. Grid Context: SING vs. SIC

Chile physically unified the SING and SIC grids in November 2017 through the Cardones–Polpaico
500 kV transmission line, creating the SEN. However, the operational characteristics of the two
sub-systems remain distinct and continue to shape electricity prices and energy mix for the
clusters analyzed here.

**SING (Norte Grande, Clusters II-0, II-2, I-1)**

The northern grid was historically dominated by coal (Tocopilla, Mejillones) and gas turbines,
because the Atacama Desert has negligible hydropower. Since 2017, utility-scale solar PV has
expanded explosively: Atacama's Global Horizontal Irradiance (GHI) averages 7–8 kWh/m²/day,
among the highest on Earth. By 2024, solar and wind provided over 45% of SING-zone capacity,
with coal declining but still significant during night hours. The mining sector has been the
anchor customer for long-term solar Power Purchase Agreements (PPAs), enabling project financing
for multi-hundred-MW photovoltaic plants.

Key transmission assets serving the SING mining clusters include the 220/500 kV backbone from
Mejillones south through Atacama, with dedicated spur lines reaching Escondida (220 kV,
~80 km from the Paposo–Electrica Angamos corridor) and the altiplanic mines in Tarapacá/
Antofagasta via the Alto Loa substation complex.

**SIC (Centro-Sur, Clusters VI-0, IV-1, RM-0)**

The central grid historically derived 45–60% of its generation from hydropower (Bio-Bio basin,
Maule basin), with gas and coal providing balancing capacity. The 2016–2020 megadrought — the
most severe sustained hydrological deficit in Chile in at least 60 years — reduced hydro
generation by roughly 30% and forced emergency coal dispatch. Since 2021, utility-scale wind
(Coquimbo, Atacama transition zone) and solar (Atacama-SIC feed through Cardones-Polpaico) have
grown rapidly, improving SIC resilience. For SIC-connected mines, electricity prices are now
increasingly determined by wind and solar spot prices rather than hydro reservoir levels.

---

## 4. Energy Mix and Renewable Share

The dashboard tracks nearby power generation capacity within a 150 km radius of each mine cluster,
categorized by technology: solar, eolico (wind), hidro (hydro), termica (coal/gas/diesel),
and otro (other). The `pct_renovable` variable captures the fraction of nearby installed capacity
from renewable sources (solar + wind + hydro).

**Indicative renewable shares by cluster (2024 estimates):**

| Cluster | Solar | Wind | Hydro | Thermal | pct_renovable |
|---------|-------|------|-------|---------|---------------|
| II-0 | ~38% | ~8% | <1% | ~54% | ~46% |
| II-2 | ~35% | ~5% | <1% | ~60% | ~40% |
| I-1 | ~30% | ~3% | ~2% | ~65% | ~35% |
| VI-0 | ~5% | ~12% | ~55% | ~28% | ~72% |
| IV-1 | ~18% | ~22% | ~20% | ~40% | ~60% |
| RM-0 | ~15% | ~18% | ~25% | ~42% | ~58% |

Note: These values reflect capacity mix within the 150 km radius buffer, which does not correspond
directly to actual generation delivered to the mine. Mines frequently contract electricity through
PPAs from plants outside their immediate geographic radius, transmitted through the backbone grid.
The `pct_renovable` metric is best interpreted as an indicator of the renewable character of the
local generation ecosystem rather than a precise procurement share.

---

## 5. Cluster Deep Dives

---

### 5.1 Cluster II-0 — Escondida (Region II, Atacama Desert)

**Operator**: BHP (57.5%), Rio Tinto (30%), JECO (12.5%)
**Mine type**: Open-pit; sulfide flotation + oxide SX-EW
**Grid**: SING / SEN northern node
**Altitude**: ~2,400 m above sea level
**Distance to coast**: ~155 km from Antofagasta port

#### Production Trajectory

Escondida is the world's largest copper mine and Chile's largest single electricity consumer.
Its production history over the 2018–2024 period reflects the tension between ore grade decline
and throughput expansion:

| Year | Production (kt) | Change |
|------|----------------|--------|
| 2018 | 1,243 | baseline |
| 2019 | ~1,190 | -4.3% |
| 2020 | 1,187 | -0.3% (pandemic year) |
| 2021 | ~1,180 | -0.6% |
| 2022 | 1,054 | -10.7% (grade decline) |
| 2023 | ~1,120 | +6.3% (recovery) |
| 2024 | 1,278 | +14.1% (new highs) |

The 2024 figure of 1,278 kt represents a multi-year high, driven by a combination of higher ore
grades in active mining zones and expanded concentrator throughput. However, the annual model v7
projects a declining trend from 2026 onward, consistent with long-term grade depletion curves
for the Escondida deposit.

#### Electricity Demand Calculation

At 12.0 MWh/t:

| Period | Production (kt) | Electricity (GWh/yr) |
|--------|----------------|----------------------|
| 2020–2024 avg | 1,213.6 | **14,563** |
| 2024 actual | 1,278 | 15,336 |
| 2026 forecast | 1,424.6 | 17,095 |
| 2032 forecast | 1,096.6 | 13,159 |

The 2026 forecast of 17,095 GWh/yr represents the highest electricity demand Escondida is
projected to require in any single year within the 2026–2032 window. The subsequent decline of
-23% to 13,159 GWh/yr by 2032 is material at the scale of the Chilean grid: it represents a
reduction of approximately 3,936 GWh/yr, equivalent to the entire average annual output of a
~500 MW baseload plant operating at 90% capacity factor.

The annual model v7 uses WR=48.1% for Escondida (Ens_Segmentado), indicating the ensemble
slightly underperforms the naive forecast. This reflects structural uncertainty in Escondida's
medium-term trajectory — grade variability, potential pit phase transitions, and BHP's capital
allocation decisions make it one of the harder mines to predict. Forecast users should treat the
2026–2032 electricity demand projections for II-0 with a confidence interval of approximately
±2,000 GWh/yr around the base scenario.

#### Grid Context and Renewable Transition

Escondida's location in the Atacama Desert creates both an energy challenge and an opportunity.
The SING grid historically relied on the Tocopilla and Mejillones coal plants, which provided
stable baseload power for the electricity-intensive grinding and flotation circuits that must run
24/7. Disruptions to this supply chain — notably Chile's loss of Argentine natural gas imports
in 2004 — triggered energy crises that directly constrained mine throughput.

BHP has responded to this vulnerability through a multi-pronged renewable energy strategy:
- Long-term PPAs with solar plants in the Antofagasta and Atacama regions
- Investment in the Kelar combined-cycle gas plant (517 MW) as flexible backup
- Studies for on-site solar installations on mine haul road corridors and tailings facilities

The Atacama solar resource is exceptional: GHI of 7–8 kWh/m²/day compares with 4–5 kWh/m²/day
in southern Spain or California's Mojave Desert. A 1,000 MW solar plant with a capacity factor
of 30% would generate approximately 2,628 GWh/yr — enough to cover ~18% of Escondida's projected
2026 electricity demand. Given BHP's stated 100% renewable ambition for Chilean operations by
2030, the trajectory of renewable procurement at Escondida is one of the most consequential
individual corporate decisions in Chile's energy transition.

The key infrastructure constraint is transmission, not generation: the 220 kV spur lines serving
Escondida were designed for the mine's 2000s-era load profile. As renewables (which are typically
located in optimal solar irradiance zones further inland or at different altitudes than the mine)
displace baseload thermal plants, the transmission network must be upgraded or reconfigured.
Camanchaca and Atacama solar zones are ~150–200 km from Escondida via the backbone network.

#### Forecast 2026–2032 Summary

| Year | Prod (kt) | Elec (GWh/yr) | YoY change |
|------|----------|---------------|-----------|
| 2026 | 1,424.6 | 17,095 | — |
| 2027 | ~1,350 | ~16,200 | -5.2% |
| 2028 | ~1,280 | ~15,360 | -5.2% |
| 2029 | ~1,240 | ~14,880 | -3.1% |
| 2030 | ~1,180 | ~14,160 | -4.8% |
| 2031 | ~1,130 | ~13,560 | -4.2% |
| 2032 | 1,096.6 | 13,159 | -2.9% |

The steep initial decline after 2026 reflects the model's projection of reversion from the 2024
peak toward the long-run mean. If BHP's planned concentrator expansion (Escondida Water Supply
Phase 2, desalination capacity increase) materializes, actual demand in 2027–2028 could
diverge significantly upward from the base scenario.

---

### 5.2 Cluster II-2 — Chuquicamata Complex (Region II, Calama Basin)

**Operator**: Codelco (Norte Division)
**Mines**: Chuquicamata (underground conversion), Radomiro Tomic, Ministro Hales, El Abra (partial),
  Gabriela Mistral
**Mine type**: Transitioning from open-pit to block-cave underground (Chuqui); oxide SX-EW (RT, GM)
**Grid**: SING / SEN northern node
**Altitude**: ~2,200–2,600 m (varies by operation)

#### Production Trajectory

The II-2 cluster aggregates Codelco's Norte Division mines — historically the engine of Chilean
copper production. The aggregate production trend is structurally declining:

| Year | Aggregate Prod (kt) | Change |
|------|-------------------|--------|
| 2018 | 1,048 | baseline |
| 2020 | 1,007 | -3.9% |
| 2022 | 923 | -8.3% |
| 2024 | 883 | -4.3% |

This decline reflects a fundamental geological reality: the Chuquicamata open pit, which produced
copper for over a century, is approaching the economic limit of open-pit extraction. The
underground block-cave project (Chuqui Subterráneo) aims to access deeper ore but will take years
to ramp to full capacity. Meanwhile, Radomiro Tomic and Gabriela Mistral are oxide operations
whose reserves have a finite horizon, and Ministro Hales faces grade challenges.

Annual model v7 assigns per-mine WR scores of 29.6% (radomiro_tomic), 55.6% (ministro_hales),
and 29.6% (chuquicamata) in Ens_Segmentado — indicating substantial forecast difficulty for
the Codelco Norte mines specifically.

#### Electricity Demand Calculation

| Period | Production (kt) | Electricity (GWh/yr) |
|--------|----------------|----------------------|
| 2020–2024 avg | 941.4 | **11,297** |
| 2024 actual | 883 | 10,596 |
| 2026 forecast | 884.6 | 10,615 |
| 2032 forecast | 812.8 | 9,753 |

The forecast decline of -8% from 2026 to 2032 (approximately -862 GWh/yr) is more gradual than
Escondida's. This reflects the model's expectation that the underground transition at Chuqui will
partially offset declining open-pit volumes — though the timing and ramp-up curve of block-cave
production remains highly uncertain.

#### Energy-Intensive Operations: The Smelter Dimension

A critical distinction for II-2 is that Chuquicamata hosts one of Chile's major copper smelters.
The smelter processes not only concentrate from the cluster's own mines but also concentrate
trucked or railed from other Codelco divisions. Smelting and electrolytic refining are
substantially more electricity-intensive than concentrate production: flash furnace smelting
requires roughly 2.5–3.0 MWh/t of copper smelted, and electrolytic refining adds ~0.4 MWh/t.

The 12.0 MWh/t production factor used in the dashboard captures this to the extent that refined
copper production (ESFU — equivalent fine copper units) is the denominator in cluster-level
calculations. However, if the smelter's throughput increases (processing more external concentrate
from, say, Chuqui underground ramp-up or Sierra Gorda) while mine production stays flat, actual
electricity demand could exceed the model's projection. This is a known limitation of
production-factor-based estimates.

#### Historical Grid Dependence and Transition

The Tocopilla coal-fired plant (Norte Energía, formerly ENDESA-Edegel) historically supplied
the bulk of Chuquicamata's electricity under long-term contracts. This created a direct link
between Chilean copper output and coal generation — a significant Scope 2 emissions liability.

Since approximately 2018, Codelco has been contracting renewable energy for Norte Division
operations through tenders and PPAs. By 2024, approximately 40% of Codelco Norte's electricity
was contractually sourced from renewable plants. The coal Tocopilla units have been partially
decommissioned, reducing the cluster's thermal dependency. However, the cluster's pct_renovable
remains lower (~40%) than the broader SING trend due to the large baseload requirements of the
smelter and the Chuqui underground ventilation systems.

The underground conversion is particularly relevant for electricity: block-cave mining requires
continuous high-volume ventilation (forced draft fans consuming 10–15 MW continuously for a
large block-cave), plus ore handling (conveyor systems, shaft hoisting for workers) that did
not exist in the open-pit configuration. Codelco has acknowledged that Chuqui Subterráneo will
operate at higher electricity intensity per ton than the historical open-pit, partially offsetting
volumetric demand reductions from declining production.

#### Forecast 2026–2032 Summary

| Year | Prod (kt) | Elec (GWh/yr) | YoY change |
|------|----------|---------------|-----------|
| 2026 | 884.6 | 10,615 | — |
| 2027 | ~870 | ~10,440 | -1.6% |
| 2028 | ~855 | ~10,260 | -1.7% |
| 2029 | ~845 | ~10,140 | -1.2% |
| 2030 | ~835 | ~10,020 | -1.2% |
| 2031 | ~820 | ~9,840 | -1.8% |
| 2032 | 812.8 | 9,753 | -0.9% |

The gradual, near-linear decline differs from Escondida's more volatile trajectory and reflects
the model's treatment of Codelco Norte as a mature, slowly declining aggregate rather than a
dynamic single-mine system. A downside scenario where Chuqui underground ramp-up lags schedule
(a historically common outcome for block-cave projects globally) would push actual production
below 800 kt/yr by 2030, reducing electricity demand to approximately 9,600 GWh/yr.

---

### 5.3 Cluster I-1 — Collahuasi + Quebrada Blanca (Region I, Tarapacá Altiplano)

**Operators**: JX Nippon (44%), Anglo American (44%), Mitsui (12%) — Collahuasi;
  Teck (60%), Sumitomo (22.5%), Empresa Nacional de Minería ENAMI (17.5%) — QB
**Mine type**: Open-pit sulfide flotation (both)
**Grid**: SING / SEN northern node
**Altitude**: 4,300–4,800 m above sea level

#### Production Trajectory

This cluster combines two distinct operations with very different recent histories:

**Collahuasi** has been remarkably stable despite being one of the world's highest-altitude major
copper mines:

| Year | Collahuasi (kt) |
|------|----------------|
| 2018 | 559 |
| 2020 | ~540 |
| 2022 | ~550 |
| 2024 | 559 |

**Quebrada Blanca Phase 2** (QB2) represents one of the most significant structural breaks in
Chilean mining data, producing a step-change in cluster-level production from 2022 onward:

| Year | QB Production (kt) |
|------|-------------------|
| 2020 | ~5 (Phase 1 SX-EW) |
| 2021 | ~6 |
| 2022 | 10 (QB2 commissioning) |
| 2023 | ~150 (ramp-up) |
| 2024 | 208 (still ramping) |

QB2's nameplate capacity is ~316 kt/yr, suggesting substantial additional production growth
through 2025–2026 as the operation reaches steady-state. The annual model v7 explicitly excludes
Quebrada Blanca from training due to this structural break (QB2 jump: 9 → 207 kt), which means
the I-1 cluster forecast severely underestimates future demand. This is documented in the
forecast note: "real demand likely 7,000–9,000 GWh/yr" versus the model's projection of
5,700–5,958 GWh/yr.

#### Electricity Demand Calculation

| Period | Production (kt) | Electricity (GWh/yr) | Note |
|--------|----------------|----------------------|------|
| 2020–2024 avg | 653.6 | **7,844** | Includes QB2 ramp |
| 2024 actual | ~767 | ~9,204 | Collahuasi 559 + QB 208 |
| 2026 forecast (model) | 496.3 | 5,958 | QB excluded — underestimate |
| 2026 forecast (realistic) | ~650 | **~7,800** | QB2 at ~90% nameplate |
| 2032 forecast (model) | 475.0 | 5,700 | Same caveat |
| 2032 forecast (realistic) | ~780 | **~9,360** | If QB2 expands further |

The discrepancy between the model forecast and realistic demand is the largest of any cluster.
For thesis purposes, this is a valuable illustration of the model's limitation with structural
breaks — a known constraint acknowledged in the annual model v7 documentation.

#### The QB2 Energy Signature: Pumping at 4,800 m

QB2's desalination-to-mine pumping system is one of the most energy-intensive infrastructure
investments in Chilean mining history. The system:
- Draws seawater from a desalination plant at Patache (coastal, Region I)
- Pumps processed water approximately 248 km horizontally and 4,800 m vertically to the
  Collahuasi/QB altiplano
- Estimated energy consumption for pumping alone: **~300–350 GWh/yr** at full capacity

This pumping load is largely independent of copper production volume — it is a fixed operational
overhead once the system is running. It means the cluster's electricity intensity per ton of copper
produced is systematically higher than the 12.0 MWh/t benchmark, likely closer to 13–14 MWh/t.

Additionally, high altitude (4,300–4,800 m) affects:
- Electric motor efficiency (reduced air density requires derating of ~15–20%)
- Photovoltaic panel performance (lower temperature improves efficiency, but dust accumulation
  and UV degradation at altitude require more frequent maintenance)
- Transmission line insulation (corona discharge increases at low air pressure, requiring larger
  conductor spacing)

#### Grid Context

Collahuasi and QB are served by transmission lines descending from the altiplano to the
Alto Loa and Ujina substations, connecting to the SING backbone. The high altitude introduces
transmission reliability challenges: seismic activity, extreme cold nights (-20°C), and periodic
snowfall create maintenance burdens on the high-voltage lines.

Solar potential exists on the mid-altitude slopes (2,000–3,500 m) between the coast and the
altiplano, where irradiance remains excellent but conditions are somewhat less extreme than at
4,800 m. Several contracted solar plants for this cluster are located in this intermediate zone.
Wind resources are less consistent than at lower-altitude sites but can be significant during
Bolivian winter thermal convection events.

#### Forecast 2026–2032 Summary

| Year | Model Prod (kt) | Model Elec (GWh/yr) | Realistic Elec (GWh/yr) |
|------|----------------|---------------------|------------------------|
| 2026 | 496.3 | 5,958 | ~7,800 |
| 2028 | ~488 | ~5,856 | ~8,400 |
| 2030 | ~482 | ~5,784 | ~8,800 |
| 2032 | 475.0 | 5,700 | ~9,360 |

The realistic scenario assumes QB2 reaches nameplate capacity (~316 kt) by 2026–2027, Collahuasi
holds at ~559–580 kt, and possible expansion studies at both mines add 5–10% additional volume.
The gap between model and reality will widen throughout the forecast horizon if QB2 ramp-up
proceeds as planned.

---

### 5.4 Cluster VI-0 — El Teniente (Region VI, Cachapoal Andes)

**Operator**: Codelco (El Teniente Division)
**Mine type**: Underground block-cave (world's largest underground copper mine by volume)
**Grid**: SIC / SEN central node
**Altitude**: 2,000–3,000 m (underground workings extend from ~2,000 m to sea level equivalent)

#### Production Trajectory

El Teniente is the world's largest underground copper mine. Its production trajectory has been
declining since the early 2010s as the primary ore block matures and new development zones
(Nuevo Nivel Mina, Ten-5) ramp up slowly:

| Year | Production (kt) | Change |
|------|----------------|--------|
| 2018 | 465 | baseline |
| 2020 | ~420 | -9.7% |
| 2022 | ~400 | -4.8% |
| 2024 | 356 | -11.0% |

The 2024 figure of 356 kt represents a multi-decade low and reflects persistent operational
challenges: ore hardness increases in deeper zones, ventilation constraints, and the complexity
of sequencing multiple underground block-cave panels simultaneously.

Annual model v7 WR for el_teniente is 81.5% (Ens_Segmentado) — the highest in the scoreboard.
This exceptional forecast accuracy reflects the mine's stability and predictability despite
volume decline: the trajectory is consistent and well-captured by trend features.

#### Electricity Demand Calculation

| Period | Production (kt) | Electricity (GWh/yr) |
|--------|----------------|----------------------|
| 2020–2024 avg | 403.3 | **4,840** |
| 2024 actual | 356 | 4,272 |
| 2026 forecast | 270.0 | 3,240 |
| 2032 forecast | 214.0 | 2,568 |

The forecast decline from 3,240 to 2,568 GWh/yr (-21% over 2026–2032) is substantial. However,
it must be interpreted with caution: El Teniente's electricity demand does not scale linearly with
production because underground ventilation — which is the mine's largest single electricity load —
is partly fixed regardless of ore production levels.

**Ventilation energy at El Teniente** is estimated at 50–60 MW of continuous fan power for the
main ventilation circuits, equivalent to roughly 440–525 GWh/yr. This baseload component means
that even if production falls by 20%, electricity demand may only fall by 10–15% because the
ventilation infrastructure must continue operating to maintain workable air quality in the
deep underground workings. The 12.0 MWh/t factor thus overestimates the proportional demand
reduction at El Teniente relative to production decline.

#### SIC Grid Context and the Megadrought Legacy

El Teniente's SIC connection gave it historical access to Chile's cheapest electricity:
hydropower from the Maule and Rapel basins (notably Rapel dam, ~50 km from the mine). During
normal hydrological years, this made El Teniente one of the lowest-cost operations in Codelco's
portfolio from an electricity standpoint.

The 2016–2020 megadrought changed this calculus dramatically: hydro generation dropped, spot
prices in the SIC spiked, and Codelco faced electricity cost overruns at El Teniente. This event
accelerated Codelco's interest in contracting dedicated wind and solar capacity on the SIC,
including projects in Coquimbo and Atacama feeding south through the Cardones-Polpaico backbone.

By 2024, the SIC had recovered much of its hydrological margin (aided by La Niña precipitation
patterns in 2021–2022), but Codelco and other SIC-connected mining companies have maintained
their diversification strategy: hydro as baseload where available, supplemented by contracted
wind and solar to hedge against future drought events.

#### Declining Demand as a Grid Opportunity

A counterintuitive implication of El Teniente's declining trajectory: as the mine's electricity
demand decreases from ~4,840 GWh/yr (historical) toward ~2,568 GWh/yr (2032 projection), the
transmission infrastructure serving the mine becomes relatively oversized. The substations,
high-voltage lines, and grid connection capacity originally dimensioned for El Teniente's peak
load could potentially be repurposed to serve the growing Santiago metropolitan area (15–20 km
north-west) or green hydrogen projects in the Andes corridor, which require large amounts of
renewable electricity.

This is a rare case in mining where production decline creates grid capacity release — a
potential economic asset if properly planned.

#### Forecast 2026–2032 Summary

| Year | Prod (kt) | Elec (GWh/yr) | YoY change |
|------|----------|---------------|-----------|
| 2026 | 270.0 | 3,240 | — |
| 2027 | ~258 | ~3,096 | -4.4% |
| 2028 | ~248 | ~2,976 | -3.9% |
| 2029 | ~238 | ~2,856 | -4.0% |
| 2030 | ~228 | ~2,736 | -4.2% |
| 2031 | ~220 | ~2,640 | -3.5% |
| 2032 | 214.0 | 2,568 | -2.7% |

---

### 5.5 Cluster IV-1 — Los Pelambres (Region IV, Coquimbo Andes)

**Operator**: Antofagasta Minerals (AMSA) — Los Pelambres Mining
**Mine type**: Open-pit sulfide flotation
**Grid**: SIC / SEN
**Altitude**: ~3,100 m above sea level

#### Production Trajectory

Los Pelambres demonstrated strong recovery after a difficult 2022 (the lowest production year
since 2012), driven by water access constraints and lower ore grades:

| Year | Production (kt) | Change |
|------|----------------|--------|
| 2018 | 371 | baseline |
| 2020 | ~345 | -7.0% |
| 2022 | 284 | -17.7% |
| 2023 | ~310 | +9.2% |
| 2024 | 331 | +6.8% |

The recovery reflects a partial resolution of the water constraint (seawater desalination
connection) and grade improvements in currently active pit phases. Annual model v7 WR for
los_pelambres is 25.9% — the second-lowest in the scoreboard, indicating chronic
underperformance relative to naive in Ens_Segmentado. The LGB_MultiH sub-model performs better
(SmallMed segment), but Los Pelambres belongs to the LargeColossal segment (Mine_Size ≥ 2),
which appears to struggle with the mine's production volatility.

#### Electricity Demand Calculation

| Period | Production (kt) | Electricity (GWh/yr) |
|--------|----------------|----------------------|
| 2020–2024 avg | 326.9 | **3,922** |
| 2024 actual | 331 | 3,972 |
| 2026 forecast | 359.2 | 4,310 |
| 2032 forecast | 366.8 | 4,402 |

The forecast shows the most stable electricity demand profile of any cluster: a modest increase
from 4,310 to 4,402 GWh/yr over 2026–2032 (+2.1%). This stability reflects the model's
expectation of gradual, steady production recovery toward historical norms.

#### AMSA's Renewable Commitment

AMSA committed publicly to sourcing 100% of its Chilean operations' electricity from renewable
sources by 2022. This commitment covers Los Pelambres directly. The mechanism involves:
- Long-term PPAs with wind farms in the Coquimbo-Atacama transition zone
  (Pacific winds, consistent resource: capacity factor ~35–40%)
- Solar contracts feeding from the SIC's northern connection points
- Residual balancing through the SIC hydro-wind-solar mix

Los Pelambres' location in Region IV (Coquimbo) is particularly well-suited for a renewable
supply strategy: the region has Chile's best wind resources in the western SIC zone, and the
mine is within economic transmission distance of both Coquimbo coastal wind farms and
Atacama-edge solar plants. The 4,310–4,402 GWh/yr demand profile makes Los Pelambres a
predictable, long-term anchor for renewable PPA developers — a commercially attractive
customer from a project finance perspective.

#### Steady-State Demand: A Thesis Insight

The near-flat demand trajectory (4,310 → 4,402 GWh/yr) means Los Pelambres represents a
stable, predictable load in the SIC — rare in a sector dominated by declining or volatile
assets. For grid operators, this is valuable: it reduces forecast uncertainty for the
northernmost SIC transmission corridor. For AMSA, the stable demand simplifies renewable
procurement planning (contract volumes are known years in advance), potentially enabling
longer-duration PPAs with more favorable pricing.

#### Forecast 2026–2032 Summary

| Year | Prod (kt) | Elec (GWh/yr) | YoY change |
|------|----------|---------------|-----------|
| 2026 | 359.2 | 4,310 | — |
| 2027 | ~361 | ~4,332 | +0.5% |
| 2028 | ~362 | ~4,344 | +0.3% |
| 2029 | ~363 | ~4,356 | +0.3% |
| 2030 | ~364 | ~4,368 | +0.3% |
| 2031 | ~365 | ~4,380 | +0.3% |
| 2032 | 366.8 | 4,402 | +0.5% |

---

### 5.6 Cluster RM-0 — Los Bronces (Metropolitan Region, Santiago Andes)

**Operator**: Anglo American (50.1%), Anglo American Sur; Codelco (20%), Mitsui (20%), Mitsubishi (9.9%)
**Mine type**: Open-pit sulfide flotation
**Grid**: SIC / SEN (metropolitan node)
**Altitude**: ~3,500 m above sea level
**Distance to Santiago**: ~15 km from city limits; ~50 km from Santiago CBD

#### Production Trajectory

Los Bronces occupies a unique position in Chilean mining geography: it is the world's highest-
altitude major urban-adjacent copper mine, operating above 3,500 m but visible from Santiago on
clear winter days when snow covers the Andes.

| Year | Production (kt) | Change |
|------|----------------|--------|
| 2018 | ~320 | baseline |
| 2020 | ~305 | -4.7% |
| 2022 | ~298 | -2.3% |
| 2024 | ~289 | -3.0% |

The declining trajectory reflects ore grade reduction in the principal mining phase. Anglo
American has announced studies for a Los Bronces Integrated Project (LBIP) — an expansion that
would access deeper ore and potentially reverse the production decline — but investment decisions
and permitting timelines remain uncertain as of early 2026.

Annual model v7 WR for los_bronces is 40.7%, below the naive baseline, indicating persistent
difficulty forecasting this mine. This partly reflects the binary nature of an expansion decision
(production either accelerates significantly if LBIP is approved, or continues declining if not)
— a structural uncertainty that standard ML features cannot capture.

#### Electricity Demand Calculation

| Period | Production (kt) | Electricity (GWh/yr) |
|--------|----------------|----------------------|
| 2020–2024 avg | 305.4 | **3,665** |
| 2024 actual | ~289 | ~3,468 |
| 2026 forecast | 201.1 | 2,413 |
| 2032 forecast | 176.2 | 2,114 |

The forecast decline from 2,413 to 2,114 GWh/yr (-12.4% over 2026–2032) is relatively gradual,
and the 2026 figure of 2,413 GWh/yr is already substantially below the 2020–2024 average of
3,665 GWh/yr — indicating the model projects that recent production levels are still above what
the forecasting engine expects for the medium term.

#### Metropolitan Grid Connection: An Unusual Asset

Los Bronces' proximity to Santiago creates an electricity supply advantage without parallel
among Chile's major copper mines: access to the densest substation network in Chile. The
SIC's Santiago metropolitan area has multiple 220/500 kV substations (Cerro Navia, El Salto,
Alto Jahuel) within transmission reach of the mine's connection point. This means:
- Electricity supply reliability is among the highest of any mining cluster in Chile
  (N-1 redundancy from multiple substations)
- Balancing capacity (demand response, flexible contracts) is more accessible than in
  remote desert locations
- The declining demand profile does not create isolated stranded assets — the grid was
  never exclusively built for the mine

Anglo American has committed to carbon neutrality in its Chilean operations by 2030. For Los
Bronces, this means contracting renewable electricity into the SIC's well-connected metropolitan
node, where wind (from the coast, ~100 km away) and Atacama solar (via the Cardones-Polpaico
line) are both available. The mine's declining load actually simplifies this transition: the
volume of renewable PPAs required decreases over the forecast horizon.

#### Community and Environmental Context

Los Bronces' location near Yerba Loca Protected Area (15 km) and the Santiago urban perimeter
means electricity use is not merely a cost variable but an environmental visibility issue.
Emissions from on-site diesel generators or indirect emissions from coal-sourced grid electricity
are scrutinized by Santiago-based media and civil society groups in a way that would not apply
to a remote Atacama mine. Anglo American's renewable transition strategy at Los Bronces thus
has a reputational dimension beyond pure cost optimization.

#### Forecast 2026–2032 Summary

| Year | Prod (kt) | Elec (GWh/yr) | YoY change |
|------|----------|---------------|-----------|
| 2026 | 201.1 | 2,413 | — |
| 2027 | ~198 | ~2,376 | -1.5% |
| 2028 | ~194 | ~2,328 | -2.0% |
| 2029 | ~191 | ~2,292 | -1.5% |
| 2030 | ~187 | ~2,244 | -2.1% |
| 2031 | ~181 | ~2,172 | -3.2% |
| 2032 | 176.2 | 2,114 | -2.7% |

Note: If the LBIP expansion is approved and begins commissioning in 2028–2030, actual production
could increase to 350–400 kt/yr, pushing electricity demand back above 4,000 GWh/yr — a scenario
entirely outside the current model's predictive capacity given the structural break it would entail.

---

## 6. Cross-Cluster Comparison

### 6.1 Demand Trajectory Table

| Cluster | 2020-24 avg (GWh) | 2026 fcst (GWh) | 2032 fcst (GWh) | Change 26→32 | Trend |
|---------|------------------|-----------------|-----------------|-------------|-------|
| II-0 Escondida | 14,563 | 17,095 | 13,159 | -23.0% | Peak then decline |
| II-2 Chuquicamata | 11,297 | 10,615 | 9,753 | -8.1% | Gradual decline |
| I-1 Collahuasi+QB* | 7,844 | 5,958 | 5,700 | -4.3% | Flat (underestimated) |
| VI-0 El Teniente | 4,840 | 3,240 | 2,568 | -20.7% | Steep decline |
| IV-1 Los Pelambres | 3,922 | 4,310 | 4,402 | +2.1% | Stable/slight growth |
| RM-0 Los Bronces | 3,665 | 2,413 | 2,114 | -12.4% | Gradual decline |
| **Total** | **46,131** | **43,631** | **37,696** | **-13.6%** | **Declining** |

*I-1 model forecast excludes QB2; realistic 2026 estimate ~7,800 GWh/yr, 2032 ~9,360 GWh/yr.

### 6.2 Model Forecast Accuracy vs. Forecast Difficulty

| Cluster | Key Mine WR (v7) | Forecast Difficulty | Primary Source of Uncertainty |
|---------|-----------------|--------------------|-----------------------------|
| II-0 | 48.1% | High | Grade variability, expansion decisions |
| II-2 | 29.6–55.6% | Very high | Underground transition timing |
| I-1 | Excluded (QB) | Extreme | Structural break (QB2 ramp) |
| VI-0 | 81.5% | Low | Stable decline trajectory |
| IV-1 | 25.9% | High | Volume volatility, water constraints |
| RM-0 | 40.7% | High | Expansion optionality (LBIP) |

### 6.3 Grid Type and Renewable Readiness

| Cluster | Grid | Dominant Resource | pct_renovable (est.) | Transition Stage |
|---------|------|------------------|---------------------|-----------------|
| II-0 | SING | Solar | ~46% | Advanced (BHP PPAs active) |
| II-2 | SING | Solar | ~40% | Moderate (Codelco contracting) |
| I-1 | SING | Solar (mid-altitude) | ~35% | Early-moderate |
| VI-0 | SIC | Hydro + Wind | ~72% | Mature (hydro baseline) |
| IV-1 | SIC | Wind | ~60% | Advanced (AMSA 100% commitment) |
| RM-0 | SIC | Wind + Hydro | ~58% | Advanced (Anglo American 2030) |

### 6.4 Electricity Intensity Caveats

The 12.0 MWh/t factor provides consistency across clusters but masks real variation:

| Cluster | Adjusting factor | Estimated true intensity |
|---------|-----------------|------------------------|
| II-0 | SX-EW reduces, desalination adds | 11.5–12.5 MWh/t |
| II-2 | Smelter adds extra, underground conversion adds | 13.0–15.0 MWh/t |
| I-1 | 4,800 m pumping adds significantly | 13.5–14.5 MWh/t |
| VI-0 | Fixed ventilation load dilutes per-ton rate | 13.0–15.0 MWh/t at low production |
| IV-1 | Open-pit flotation, close to benchmark | 11.5–12.5 MWh/t |
| RM-0 | High altitude but straightforward flotation | 12.0–13.0 MWh/t |

---

## 7. Key Findings

### 7.1 Total Demand is Declining — A Carbon Dividend

Summing across the six clusters, modelled electricity demand is projected to fall from
approximately 43,631 GWh/yr in 2026 to 37,696 GWh/yr by 2032 — a reduction of 5,935 GWh/yr
(-13.6%). This represents a significant carbon-footprint implication even without any
improvement in the grid's renewable share:

Assuming a 2024 SEN average grid emission factor of approximately 0.25 t CO₂/MWh (down from
~0.50 t CO₂/MWh in 2016 due to rapid solar and wind expansion), the projected demand reduction
translates to:

**Avoided annual emissions by 2032 vs. 2026: ~1.48 Mt CO₂/yr**

This is equivalent to removing approximately 640,000 passenger cars from the road, or about
4% of Chile's total annual greenhouse gas emissions. Critically, this reduction occurs
passively — driven by mine production decline rather than active decarbonization investment.
It represents a "small victory" that is easy to overlook in mine-by-mine analysis but becomes
visible only at the cluster or national level.

If the SEN's emission factor continues falling toward 0.15 t CO₂/MWh by 2030 (consistent with
Chile's trajectory), the avoided emissions from the same demand reduction would be:
**~0.89 Mt CO₂/yr** — still material, and additive to the decarbonization happening on the
supply side of the grid.

### 7.2 The Escondida Peak-and-Decline Pattern Dominates System Dynamics

Cluster II-0 (Escondida) contributes 39% of total modelled electricity demand at its 2026 peak
(17,095 GWh/yr). Its subsequent decline to 13,159 GWh/yr by 2032 — a reduction of 3,936 GWh/yr
— is larger than the entire electricity demand of the Los Bronces mine. This means Escondida's
production trajectory effectively sets the ceiling for northern Chile's electricity demand growth.
Grid operators who plan SING capacity additions based on historical growth trends risk
over-investing in transmission infrastructure that will be underutilized within the forecast
horizon.

### 7.3 The Quebrada Blanca Gap: Model Limitations Matter for Infrastructure

The I-1 cluster illustrates a critical limitation: when a structural break (QB2's step-change
from ~10 to ~316 kt nameplate capacity) occurs, the rolling-origin model trained on historical
data cannot account for it. The result is an 1,800–3,600 GWh/yr underestimate of cluster demand
by 2026–2032. For a thesis framing this as a forecasting system, this gap demonstrates why
model outputs should always be accompanied by known-exclusion flags, and why domain knowledge
(mine expansion plans, commissioning dates, nameplate capacities) must supplement statistical
models for energy planning purposes.

### 7.4 El Teniente: The Ventilation Floor Effect

The projection of El Teniente's electricity demand declining proportionally with production
(-21% by 2032) likely overstates the real reduction. The mine's underground ventilation system
requires a near-constant 440–525 GWh/yr regardless of production volume. As production falls
toward ~214 kt/yr, the ventilation load represents an increasing share of total electricity
consumption, pushing actual intensity above the 12.0 MWh/t benchmark. The electricity demand
floor for El Teniente — the level below which demand cannot decline as long as the mine operates
underground — is approximately 1,500–2,000 GWh/yr.

### 7.5 Los Pelambres as a Renewable PPA Anchor

The only cluster with slightly growing forecast demand (IV-1, +2.1% over 2026–2032) is also
the most straightforwardly renewable-ready: AMSA's 100% renewable commitment, the cluster's
access to Coquimbo wind resources, and its predictable demand profile make it an ideal anchor
client for renewable project developers needing long-term, stable off-take agreements. This
contrasts sharply with Escondida (volatile demand, renewal of large-scale contracts at risk
during demand decline periods) or El Teniente (declining demand makes long-term contracts
harder to justify).

### 7.6 Underground Mining Increases Specific Electricity Intensity

Two of the six clusters are undergoing or contemplating transitions from open-pit to underground
mining: II-2 (Chuquicamata underground, ongoing) and RM-0 (Los Bronces LBIP, potential).
In both cases, underground mining increases specific electricity intensity (MWh/t) due to
ventilation, hoisting, and dewatering loads. If these transitions materialize at scale, the
actual electricity demand decline in these clusters will be smaller than the production-based
forecast suggests — or electricity demand could grow even if production volumes decline.

---

## 8. Limitations and Assumptions

1. **Production factor uniformity**: The 12.0 MWh/t factor does not distinguish between
   open-pit vs. underground operations, oxide vs. sulfide processing, or mines with and without
   on-site smelting. Actual cluster-level intensities vary by at least ±20%.

2. **QB2 exclusion from model**: The I-1 cluster projections underestimate real electricity
   demand by 1,800–3,600 GWh/yr through 2032. Any analysis relying on I-1 model outputs for
   energy planning purposes should apply an explicit QB2 addendum using Teck's public production
   guidance (nameplate ~316 kt/yr, with potential Phase 3 expansion studies).

3. **Expansion optionality**: LBIP (RM-0), Escondida concentrator expansions, and Collahuasi
   expansion studies are not captured by the model. Binary expansion decisions create forecast
   distributions that are bimodal rather than normal — standard confidence intervals
   underrepresent this tail risk.

4. **Grid emission factor trajectory**: The CO₂ savings calculations above assume the SEN
   emission factor follows Chile's announced decarbonization trajectory. Delays in coal plant
   retirements or extreme droughts reducing hydro availability could increase the factor,
   amplifying the value of demand reduction in carbon terms.

5. **150 km radius energy mix**: The `pct_renovable` metric in the dashboard reflects nearby
   capacity, not procured electricity. Actual renewable shares in PPAs can differ substantially
   from local capacity mix, especially for SING mines that contract solar plants distributed
   across large geographic areas.

---

## 9. Suggested Next Steps for the Thesis

1. **QB2-adjusted I-1 forecast**: Create a supplementary projection for the I-1 cluster that
   adds QB2's production separately (using Teck's public guidance) to the model's Collahuasi-only
   forecast. Present this as a "structural-break correction" case study demonstrating where
   domain knowledge overrides statistical extrapolation.

2. **Underground intensity adjustment**: For II-2 (Chuqui underground) and VI-0 (El Teniente),
   develop intensity curves that vary MWh/t by production level (higher intensity at low volume
   due to fixed ventilation loads). This would improve electricity demand forecast accuracy even
   if production forecasts remain unchanged.

3. **Scenario electricity demand**: The annual model already generates bear/base/bull production
   scenarios (Cu price percentiles 0.2/0.5/0.8). Apply these to electricity demand to produce
   a three-scenario demand forecast per cluster, which could directly inform Cochilco or CNE
   (National Energy Commission) planning documents.

4. **Renewable transition timeline cross-reference**: Overlay each mine company's stated
   renewable electricity commitment date against the forecast demand profile to identify whether
   the procurement volume needed to fulfill commitments is consistent with projected production.

5. **Stranded asset analysis**: For VI-0 and RM-0, where demand is declining significantly,
   quantify the replacement value of transmission infrastructure that will be underutilized,
   and assess whether this infrastructure could be repurposed for grid-scale energy storage,
   green hydrogen projects, or urban load growth.

6. **Annual model accuracy vs. electricity demand error**: Compute the propagated forecast
   error for each cluster's electricity demand forecast (model WR% → production error distribution
   → GWh error band). This would contextualize the 2026–2032 demand projections with uncertainty
   quantification directly relevant to infrastructure planning.

---

## Appendix: Cluster Summary Cards

| Parameter | II-0 | II-2 | I-1 | VI-0 | IV-1 | RM-0 |
|-----------|------|------|-----|------|------|------|
| Top mine | Escondida | Chuquicamata | Collahuasi | El Teniente | Los Pelambres | Los Bronces |
| Operator | BHP | Codelco | JX/AA/Mitsui | Codelco | AMSA | Anglo American |
| Grid zone | SING | SING | SING | SIC | SIC | SIC |
| Altitude (m) | 2,400 | 2,200 | 4,300–4,800 | 2,000–3,000 | 3,100 | 3,500 |
| Mine type | Open-pit | OP+U/G | Open-pit | Underground | Open-pit | Open-pit |
| 2024 Prod (kt) | 1,278 | 883 | ~767 | 356 | 331 | ~289 |
| 2024 Elec (GWh) | 15,336 | 10,596 | ~9,204 | 4,272 | 3,972 | ~3,468 |
| 2026 Elec (GWh) | 17,095 | 10,615 | 5,958 | 3,240 | 4,310 | 2,413 |
| 2032 Elec (GWh) | 13,159 | 9,753 | 5,700 | 2,568 | 4,402 | 2,114 |
| Change 26→32 | -23.0% | -8.1% | -4.3% | -20.7% | +2.1% | -12.4% |
| Key challenge | Grade decline | Underground transition | QB2 break | Ventilation floor | Water volatility | Expansion uncertainty |
| pct_renovable | ~46% | ~40% | ~35% | ~72% | ~60% | ~58% |
| Model WR (key mine) | 48.1% | 29.6% | — | 81.5% | 25.9% | 40.7% |

---

*Report generated from dashboard `mining_clusters_v2` outputs and annual model v7 projections.*
*Production factor: 12.0 MWh/t (Cochilco 2022/2023 sector average).*
*Date: March 2026.*
