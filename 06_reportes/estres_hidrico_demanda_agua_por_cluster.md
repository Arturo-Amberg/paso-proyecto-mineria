# Water Stress Analysis — Top 6 Mining Clusters in Chile
### Based on Dashboard `mining_clusters_v2` · March 2026

---

## Why Water?

Chilean copper mining operates in some of the driest terrain on Earth. The Atacama Desert
(Regions I–III) receives less than 1 mm of rainfall per year in many areas, while the Andean
clusters (Regions IV–VI) depend on snowmelt and glaciers that are contracting under climate
change. Water is simultaneously the **#1 operational constraint** and the **#1 social flashpoint**
for Chilean mining — DGA water rights disputes, community conflicts, and desalination investment
decisions all hinge on the numbers computed in this analysis.

The dashboard integrates four independent data layers for water:
1. **DGA Derechos de Agua** — 44,942 water-rights records (flow in L/s, year granted, type)
2. **Production-derived water estimates** — using Cochilco 2023/2024 differentiated factors
   (Sulfuros 93 m³/t · Óxidos 35 m³/t · Mixto 60 m³/t · Fundición 80 m³/t)
3. **Desaladora coverage** — operational desalination plants within 250 km (mining-exclusive flag)
4. **Production forecasts 2026–2032** — annual model v7 Ens_Segmentado projections

---

## Cluster Selection Rationale

The **6 clusters with the highest estimated annual water consumption** (2020–2024 average) were
selected. They account for **≈ 87% of modelled Chilean copper production** and span four distinct
hydrological regimes: coastal desalination, Atacama continental groundwater, high-altitude
Andean snowmelt, and Mediterranean river basins.

| Rank | Cluster | Top Mine | Avg Production (kt/yr) | Water Est. (M m³/yr) | Hydrological Regime |
|------|---------|----------|----------------------:|---------------------:|---------------------|
| 1 | **II-0** | Escondida | 1,213.6 | **107.8** | Coastal desalination (BHP) |
| 2 | **II-2** | Chuquicamata | 941.4 | **61.5** | Atacama continental groundwater |
| 3 | **I-1** | Collahuasi | 653.6 | **60.8** | High-altitude Andean + QB2 desal |
| 4 | **II-5** | Spence | 456.5 | **42.5** | Mixed: desal (BHP) + saline |
| 5 | **VI-0** | El Teniente | 403.3 | **37.5** | Andean watershed (Cachapoal) |
| 6 | **IV-1** | Los Pelambres | 326.9 | **30.4** | Choapa river basin |

---

## Cluster Deep Dives

---

### 1 · Cluster II-0 — Escondida Complex (Region II, Antofagasta)

**Mines:** Escondida (BHP, sulfide flotation) · Zaldívar (Antofagasta Minerals, SX-EW oxide)

**Production trajectory (kt/yr):**

| Year | Escondida | Zaldívar | Cluster Total |
|------|----------:|--------:|-------------:|
| 2018 | 1,243 | 94 | 1,337 |
| 2020 | 1,187 | 96 | 1,283 |
| 2022 | 1,054 | 89 | 1,143 |
| 2024 | 1,278 | 83 | 1,361 |

**Water demand (estimated):**
- Escondida: 93 m³/t (sulfide flotation) → **~119 M m³/yr in 2024**
- Zaldívar: 35 m³/t (oxide SX-EW) → ~2.9 M m³/yr
- **Cluster total 2024: ≈ 122 M m³/yr** — the single largest mining water consumer in Chile

**Desalination status:**
BHP's Escondida desalination plant (operational, mining-exclusive) is one of the largest
in South America. It supplies seawater — removing freshwater pressure on the Atacama basin.
This is the **benchmark desalination success story** in Chilean mining.

**Production forecast 2026–2032 (model v7):**

| Year | Pred (kt) | Water est. (M m³/yr) |
|------|----------:|---------------------:|
| 2026 | 1,425 | 128.1 |
| 2028 | 1,304 | 116.7 |
| 2030 | 1,235 | 109.7 |
| 2032 | 1,097 | 96.7 |

**Key insight:** The model forecasts a **-23% decline** in Escondida production by 2032
relative to 2026. Despite this, water demand remains above 96 M m³/yr — still the largest
single consumer. The declining trajectory reflects ore-grade deterioration at the world's
richest copper deposit. **Desalination capacity will need to remain operational even as
production falls**, since the water intensity (m³/t) stays constant while absolute demand
drops with production.

---

### 2 · Cluster II-2 — Calama / Codelco Complex (Region II, Antofagasta)

**Mines:** Chuquicamata (smelter) · Radomiro Tomic (oxide SX-EW) · Ministro Hales
(sulfide/moly) · El Abra (oxide SX-EW) · Gabriela Mistral (sulfide)

**Production trajectory (kt/yr):**

| Year | Chiq | RT | MH | El Abra | GM | Total |
|------|-----:|---:|---:|--------:|---:|------:|
| 2018 | 321 | 333 | 196 | 91 | 107 | 1,048 |
| 2020 | 401 | 261 | 171 | 72 | 102 | 1,007 |
| 2022 | 268 | 301 | 152 | 92 | 110 | 923 |
| 2024 | 289 | 270 | 122 | 99 | 103 | 883 |

**Water demand (estimated):**
- Mixed process types create a **blended water factor of ~65 m³/t cluster-average**
- Chuquicamata (smelter): 80 m³/t — highest intensity, processes concentrates from all Codelco Norte
- Radomiro Tomic + El Abra (oxide): 35 m³/t — efficient hydromet
- Gabriela Mistral + Ministro Hales (sulfide): 93 m³/t
- **Cluster total 2024: ≈ 57 M m³/yr**

**Hydrological risk — unique in Chile:**
This cluster depends almost entirely on **continental groundwater** from the Calama Basin
(Río Loa watershed). Unlike coastal clusters, no desalination pipeline exists at this scale.
The Loa aquifer is overexploited and Calama city itself (177,000 people) competes with mining
for the same source. Codelco has invested in recirculation systems, but structural freshwater
dependency persists.

**Production forecast 2026–2032:**

| Year | Pred (kt) | Water est. (M m³/yr) |
|------|----------:|---------------------:|
| 2026 | 885 | 56.2 |
| 2028 | 883 | 56.4 |
| 2030 | 860 | 54.1 |
| 2032 | 813 | 51.7 |

**Key insight:** Production and water demand are **declining gradually** (-8% by 2032).
The structural risk is not growth but **source depletion** — declining production will reduce
water demand, but the aquifer may already be past sustainable yield. Codelco's water reuse
investments are critical even as volumes shrink.

---

### 3 · Cluster I-1 — Collahuasi + Quebrada Blanca (Region I, Tarapacá)

**Mines:** Collahuasi (Glencore/Anglo, sulfide) · Quebrada Blanca QB2 (Teck, sulfide)

**Production trajectory (kt/yr):**

| Year | Collahuasi | QB (old/new) | Cluster Total |
|------|----------:|-------------:|-------------:|
| 2018 | 559 | 26 | 585 |
| 2020 | 629 | 13 | 642 |
| 2022 | 571 | 10 | 581 |
| 2023 | 573 | 64 | 637 |
| 2024 | 559 | **208** | **767** |

**The QB2 inflection:** Quebrada Blanca's Phase 2 expansion ramped from 13 kt (2022) to
208 kt (2024) — a **+1,500% volume increase** in two years. This is the most dramatic
structural water demand shock in any cluster during this period.

**Water demand (estimated):**
- Both mines: sulfide flotation at high altitude → 93 m³/t
- Collahuasi 2024: 559 × 1,000 × 93 / 1e6 = **52.0 M m³/yr**
- QB2 2024: 208 × 1,000 × 93 / 1e6 = **19.3 M m³/yr**
- **Cluster total 2024: ≈ 71.3 M m³/yr** (+38% vs 2022 due to QB2 alone)

**QB2 desalination solution:**
Teck's QB2 project includes a dedicated desalination plant on the Iquique coast with a
**4,800m elevation seawater pipeline** — one of the most ambitious water infrastructure
projects in Chilean mining history. This should cover QB2's new demand without freshwater
stress.

**Production forecast 2026–2032:**
Note: Model v7 was trained on data through 2024 but QB2 ramp effect is only partially captured
in rolling-origin validation (origins through 2018).

| Year | Pred (kt) | Water est. (M m³/yr) |
|------|----------:|---------------------:|
| 2026 | 496 | 46.2 |
| 2028 | 469 | 43.6 |
| 2030 | 421 | 39.1 |
| 2032 | 475 | 44.2 |

**Key insight:** The model **underestimates** I-1's likely future production — the QB2
structural break occurs after the training origins. Real 2026–2032 water demand is likely
**closer to 65–80 M m³/yr** once QB2 reaches full capacity (target ~330 kt/yr). This makes
I-1 the cluster with the **largest water forecast uncertainty** and greatest urgency for
desalination capacity planning.

---

### 4 · Cluster II-5 — Spence + Sierra Gorda Hub (Region II, Antofagasta)

**Mines:** Spence SGO (BHP, sulfide) · Sierra Gorda (KGHM, sulfide/oxide) · Lomas Bayas
(Lundin/Glencore, oxide)

**Production trajectory (kt/yr):**

| Year | Spence | Sierra Gorda | Lomas Bayas | Total |
|------|-------:|------------:|------------:|------:|
| 2018 | 176 | 102 | 73 | 351 |
| 2020 | 147 | 156 | 74 | 377 |
| 2022 | 245 | 173 | 72 | 490 |
| 2024 | 256 | 155 | 74 | 485 |

**Water demand (estimated):**
- Spence (sulfide flotation, post-SGO expansion): 93 m³/t → 23.8 M m³/yr in 2024
- Sierra Gorda (sulfide/oxide mixed): ~75 m³/t blended → 11.6 M m³/yr
- Lomas Bayas (oxide SX-EW): 35 m³/t → 2.6 M m³/yr
- **Cluster total 2024: ≈ 38 M m³/yr**

**Multi-company water dynamics:**
BHP (Spence) has access to desalination via its Atacama network; KGHM (Sierra Gorda) relies
more heavily on DGA-registered groundwater rights. Lomas Bayas' oxide process is water-
efficient relative to the cluster. This creates a **two-tier water security** within the
same geographic cluster.

**Production forecast 2026–2032:**

| Year | Pred (kt) | Water est. (M m³/yr) |
|------|----------:|---------------------:|
| 2026 | 246 | 22.9 |
| 2028 | 203 | 18.9 |
| 2030 | 198 | 18.4 |
| 2032 | 173 | 16.1 |

**Key insight:** This cluster is in **structural decline** (-30% production by 2032).
Water demand follows proportionally, which is unusual — typically water stress *increases*
as ore grades fall (more ore processed per tonne of copper). Here, absolute demand falls,
reducing but not eliminating pressure on the Atacama water budget.

---

### 5 · Cluster VI-0 — El Teniente (Region VI, O'Higgins)

**Mines:** El Teniente (Codelco, world's largest underground copper mine, sulfide)

**Production trajectory (kt/yr):**

| Year | El Teniente |
|------|------------:|
| 2018 | 465 |
| 2020 | 443 |
| 2022 | 405 |
| 2023 | 352 |
| 2024 | 356 |

**Water demand (estimated):**
- Pure sulfide underground mine: 93 m³/t
- **2024: ≈ 33.1 M m³/yr**

**Hydrological profile — qualitatively different from the north:**
El Teniente operates in the Andean foothills of the Cachapoal watershed. Unlike the Atacama
clusters, rainfall exists here (~500 mm/yr at lower elevations), and the mine draws from
Andean streams. The **critical concern is glacial retreat**: the mine operates at 2,000–3,600m
elevation where Andean glaciers and snow cover are contracting. Long-term (post-2035) water
security depends on the health of the upper Cachapoal and Tinguiririca watersheds.

**Production forecast 2026–2032:**

| Year | Pred (kt) | Water est. (M m³/yr) |
|------|----------:|---------------------:|
| 2026 | 270 | 25.1 |
| 2028 | 239 | 22.2 |
| 2030 | 225 | 20.9 |
| 2032 | 214 | 19.9 |

**Key insight:** The model forecasts **-21% production by 2032**, continuing a decline that
began in 2018. For water, this means absolute demand shrinks from 25 to 20 M m³/yr —
apparently reducing pressure. However, the **quality dimension** matters: as ore grades
decline, more rock is processed per tonne of copper, potentially increasing water per tonne
even as total production falls. El Teniente is also the only major mine in a Mediterranean
climate, making it the **bellwether for glacier-dependent water security** in Chilean copper.

---

### 6 · Cluster IV-1 — Los Pelambres (Region IV, Coquimbo)

**Mines:** Los Pelambres (Antofagasta Minerals, sulfide) · Tres Valles (minor, oxide)

**Production trajectory (kt/yr):**

| Year | Los Pelambres |
|------|-------------:|
| 2018 | 371 |
| 2020 | 372 |
| 2021 | 336 |
| 2022 | 284 |
| 2023 | 311 |
| 2024 | 331 |

**Water demand (estimated):**
- Sulfide flotation: 93 m³/t
- **2024: ≈ 30.8 M m³/yr**

**The Choapa conflict:**
Los Pelambres draws water from the Choapa River basin — a critical freshwater source for
agricultural communities (vineyards, avocados, olive groves) in semi-arid Coquimbo. This is
the **most acute social conflict** of any cluster analyzed: community organizations have
repeatedly blocked mine expansions over water allocation. The 2022 production drop (-24%
from 2020) reflects operational disruptions partly related to drought and water restrictions.
The mine's DGA water rights and any expansion plans are subject to intense community scrutiny.

**Production forecast 2026–2032:**

| Year | Pred (kt) | Water est. (M m³/yr) |
|------|----------:|---------------------:|
| 2026 | 359 | 33.4 |
| 2028 | 354 | 33.0 |
| 2030 | 360 | 33.5 |
| 2032 | 367 | 34.1 |

**Key insight:** Unlike northern clusters, Los Pelambres is forecast to be **broadly stable**
(+2% by 2032 from 2026). Water demand essentially plateaus at ~33–34 M m³/yr. For a river-fed
operation in an area experiencing accelerated drought, stable high demand is not neutral —
it becomes **increasingly constraining** as the Choapa's natural flow declines with climate
change. This cluster illustrates that the water stress problem is not just about absolute
consumption but about **consumption relative to a shrinking supply**.

---

## Cross-Cluster Comparison

### Water Demand Summary (M m³/yr)

| Cluster | 2024 actual est. | 2026 forecast | 2032 forecast | Trend |
|---------|----------------:|-------------:|-------------:|-------|
| II-0 (Escondida) | ~122 | 128.1 | 96.7 | ↓ Declining |
| II-2 (Calama) | ~57 | 56.2 | 51.7 | ↓ Gradual decline |
| I-1 (Collahuasi+QB) | ~71 | 46.2* | 44.2* | ↑ Likely underestimated |
| II-5 (Spence hub) | ~38 | 22.9 | 16.1 | ↓ Sharp decline |
| VI-0 (El Teniente) | ~33 | 25.1 | 19.9 | ↓ Declining |
| IV-1 (Los Pelambres) | ~31 | 33.4 | 34.1 | → Stable/slight growth |
| **Total 6 clusters** | **~352** | **~312** | **~263** | **↓ -25% by 2032** |

*I-1 forecast likely underestimates true demand due to QB2 post-training structural break

### Water Source Matrix

| Cluster | Desalination | Continental GW | River/Andean | Risk Level |
|---------|:-----------:|:--------------:|:-----------:|:----------:|
| II-0 | ✅ BHP (operational) | — | — | Low–Medium |
| II-2 | ❌ None at scale | ✅ Loa aquifer (stressed) | — | **High** |
| I-1 | ✅ QB2 (new) | — | ✅ High-altitude | Medium |
| II-5 | ⚠️ BHP only (Spence) | ✅ Atacama GW (KGHM) | — | Medium |
| VI-0 | ❌ None | — | ✅ Cachapoal (glacier risk) | Medium |
| IV-1 | ❌ None | — | ✅ Choapa (community conflict) | **High** |

---

## Key Findings

**1. Aggregate demand is declining.** Total water demand across the 6 clusters falls from
~352 M m³/yr (2024) to ~263 M m³/yr (2032) — a -25% reduction driven by Escondida's ore
grade decline and II-5's structural contraction. This is a counterintuitive "small victory":
the water footprint of Chilean copper is contracting even as global demand for the metal grows.

**2. I-1 is the biggest uncertainty.** Quebrada Blanca's QB2 expansion adds ~19 M m³/yr of
new demand that the model cannot fully capture (post-origin structural break). The real 2032
water demand for I-1 may be 50–80 M m³/yr rather than the modelled 44 M m³/yr. Desalination
infrastructure is in place, but capacity planning must account for this.

**3. Two clusters face structural water insecurity.** II-2 (Calama) depends on a stressed
continental aquifer with no viable desalination alternative at scale. IV-1 (Los Pelambres)
draws from a river basin in a region experiencing drought intensification and fierce community
opposition. These clusters cannot solve their water problem by simply building a pipe to the sea.

**4. Process type is a key lever.** Zaldívar (oxide SX-EW, 35 m³/t) uses 2.7× less water
per tonne than Escondida (sulfide flotation, 93 m³/t), despite being in the same cluster. For
Chile's future copper portfolio, **process-mix planning is as important as location** for water
sustainability. Radomiro Tomic and El Abra (both oxide) similarly reduce II-2's blended factor.

**5. El Teniente is a climate-change sentinel.** The only high-production mine in a temperate
Andean watershed, its long-term water security depends on glacial health — a variable entirely
outside mining operators' control. Its declining production reduces short-term pressure but
does not resolve the structural vulnerability.

---

## Suggested Next Steps for Thesis

- **Stress-test I-1**: rerun projection with QB2 at target capacity (330 kt/yr) to quantify
  the true 2026–2032 water demand gap and desalination adequacy.
- **II-2 aquifer scenario**: model a 20% reduction in Loa aquifer yield and its impact on
  feasible production. Links directly to the tail of the forecast distribution (Lower bound).
- **IV-1 community risk index**: combine water demand stability with Choapa drought projections
  (IPCC SSP2-4.5) to produce a "social conflict risk score" per year through 2032.
- **Dashboard enhancement**: add a "Water Source Risk" layer toggle that colors clusters by the
  source matrix above — desalination (green), Andean (yellow), stressed aquifer/river (red).

---

*Data sources: Produccion_Master.csv (annual 2018–2024), projections_2026_2032.csv (model v7
Ens_Segmentado), Cochilco 2023/2024 water intensity factors, DGA Derechos de Agua (44,942
records), build_dashboard_v2.py infrastructure layers.*

*Generated: March 2026 · TrabajoTesis / FinalResultsFolder*
