# Accessibility and Logistics Infrastructure for Chilean Copper Mining Clusters

**Thesis:** Multi-Horizon Production Forecasting for Chilean Copper Mines (1982–2025)
**Report date:** 2026-03-16
**Author:** TrabajoTesis Research Project

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Cluster Selection Rationale](#2-cluster-selection-rationale)
3. [Cluster Deep Dives](#3-cluster-deep-dives)
   - 3.1 [II-2 — Calama / Codelco Norte](#31-cluster-ii-2--calama--codelco-norte)
   - 3.2 [I-1 — Collahuasi + Quebrada Blanca](#32-cluster-i-1--collahuasi--quebrada-blanca)
   - 3.3 [II-0 — Escondida](#33-cluster-ii-0--escondida)
   - 3.4 [III-2 — Candelaria + Caserones](#34-cluster-iii-2--candelaria--caserones)
   - 3.5 [IV-1 — Los Pelambres](#35-cluster-iv-1--los-pelambres)
   - 3.6 [VI-0 — El Teniente](#36-cluster-vi-0--el-teniente)
4. [Cross-Cluster Comparison Matrix](#4-cross-cluster-comparison-matrix)
5. [Key Findings](#5-key-findings)
6. [Forecast Implications for Logistics](#6-forecast-implications-for-logistics)
7. [Suggested Next Steps for the Thesis](#7-suggested-next-steps-for-the-thesis)

---

## 1. Introduction

Accessibility — understood as the combined quality of port infrastructure, rail connectivity, road conditions, and alternative logistics such as concentrate or water pipelines — is a foundational determinant of copper mining viability in Chile. This report analyzes how the logistics geography of Chilean mines shapes their production economics and, by extension, their multi-year production trajectories as captured by the forecasting model described in this thesis.

### Why Accessibility Matters

**Logistics cost as a share of total operating cost.** For copper concentrate, logistics costs (transport from mine to port, port handling, and maritime freight) typically represent 8–15% of the free-on-board (FOB) realized value for Chilean mines. For very remote sites relying on long-haul road haulage — such as Caserones, 160 km from Caldera by mountain road — the trucking component alone can reach USD 25–35 per tonne of ore moved, compounding the mine's cost disadvantage relative to better-connected peers.

**Carbon footprint.** Diesel truck fleets serving remote mines constitute a significant share of Scope 1 and Scope 3 emissions for mining companies. The international trend toward mandatory ESG disclosure (SEC climate rules, EU Corporate Sustainability Reporting Directive) means that logistics-related emissions are increasingly material to a mine's social license and refinancing conditions. Mines with pipelines or rail access carry a structurally lower emissions profile for concentrate transport.

**Expansion feasibility.** A mine operating near port capacity or road congestion faces an implicit ceiling on throughput. Before capital investment in a new concentrator or leach pad can be approved, the logistics corridor must demonstrate sufficient headroom. The QB2 expansion at Quebrada Blanca, for example, required construction of a 240 km seawater pipeline at 4,800 m altitude — an infrastructure investment of roughly USD 800 million independently of the mine itself.

**Supply chain resilience.** Single-point dependence on one road, one port, or one pipeline creates fragility. Northern Chilean mines experienced supply disruptions during the 2019 social unrest (Route 1 and B-485 blockades) and during extreme weather events in the Atacama (2015 flooding). Diversified logistics corridors reduce downtime risk and improve insurance terms.

**Relevance to forecasting.** The forecasting model in this thesis uses Mine_Size, Company_Size, production lags, and trend features rather than explicit logistics variables. However, accessibility constraints operate as a latent driver: they influence the speed and cost of expansion projects (which determine production growth), the frequency of unplanned outages (which create the irregular time-series patterns that challenge all forecasting methods), and the economic thresholds below which production curtailments become rational. Understanding the logistics profile of each cluster therefore enriches the interpretation of model residuals and of the scenario projections to 2032.

---

## 2. Cluster Selection Rationale

The dashboard `mining_clusters_v2` partitions Chilean copper mines into spatial clusters using geographic coordinates, with supplementary layers for port proximity (mine-to-nearest-port Euclidean distance), the rail network encoded in `estaciones.csv` (742 stations, 4 connected components), and port size classification (Grande / Mediano / Pequeño).

Six clusters are selected for this analysis on the basis of three criteria:

1. **Production significance.** Each selected cluster contributes at least 200 kt/yr average production (2020–2024), collectively representing more than 85% of national copper output.

2. **Logistics variety.** The six clusters span the full range of infrastructure configurations found in Chilean mining: multi-modal access (rail + port + pipeline), pipeline-only with no rail, small-port dependency, extreme remoteness, and urban proximity with refined-metal output.

3. **Forecast interest.** Each cluster exhibits distinct production trajectory patterns to 2032 (declining, stable, or expanding), making the interaction between logistics constraints and production outlook non-trivial.

The table below lists the six clusters with their core logistics identifiers:

| Cluster ID | Key mines | 2020–2024 avg (kt/yr) | Nearest port | Port size | Rail access | Pipeline |
|---|---|---|---|---|---|---|
| II-2 | Chuquicamata, RT, MH, Andina* | 941.4 | Tocopilla (133 km) | Pequeño | FCAB main line | No concentrate pipeline |
| I-1 | Collahuasi, QB2 | 653.6 | Iquique (174 km) | Grande | Limited inland branch | QB2 seawater (inbound) |
| II-0 | Escondida | 1,213.6 | Antofagasta (155 km) | Grande | FCAB branch | Concentrate pipeline to Coloso |
| III-2 | Candelaria, Caserones | 248.7 | Caldera (71 km avg) | Mediano | None | None |
| IV-1 | Los Pelambres | 326.9 | Valparaíso (158 km) | Grande | None | Concentrate pipeline to Los Vilos |
| VI-0 | El Teniente | 403.3 | San Antonio (116 km) | Grande | Andean branch (limited) | No concentrate (refined metal) |

*Andina belongs to Cluster II-2 for geographic purposes in the dashboard but uses different port routing via Valparaíso.

---

## 3. Cluster Deep Dives

### 3.1 Cluster II-2 — Calama / Codelco Norte

**Key mines:** Chuquicamata, Radomiro Tomic, Ministro Hales, (and Andina for administrative grouping)
**Production (2020–2024 avg):** 941.4 kt/yr
**Segment classification (model):** LargeColossal (Mine_Size = 2–3)

#### Port Infrastructure

The II-2 cluster dispatches its copper primarily through Tocopilla, a small industrial port located 134–138 km from the Calama mining district. Tocopilla's port classification as "Pequeño" reflects its limited berth capacity and lack of bulk carrier depth-of-draft suitable for capesize vessels. It handles primarily cathode copper (flat electrolytic plates) from the Chuquicamata cathode plant and some acid imports for the SX-EW operations. The nearest large port, Antofagasta, is 230 km from Calama — accessible but at a substantially higher transport cost than Tocopilla.

A fraction of Chuquicamata's concentrate output moves through Antofagasta port, transported by FCAB rail, which is both cheaper and more reliable than road haulage for high-volume flows.

#### Rail Network (FCAB)

The Ferrocarril de Antofagasta a Bolivia (FCAB) is the single most important mining rail corridor in northern Chile. Its main line runs from Antofagasta port north through the coastal desert, ascending east to Calama (2,260 m) and continuing to Oruro, Bolivia (3,700 m). The Calama rail hub connects directly to Chuquicamata mine (a short branch of approximately 10 km) and provides access to Bolivia's Atacama border crossings for acid and reagent imports.

For the II-2 cluster, FCAB performs three logistics functions: (i) export of copper concentrate from the Chuquicamata sulfide concentrator to Antofagasta port, (ii) import of sulfuric acid for the leach operations at Chuquicamata and Radomiro Tomic, and (iii) general supply chain access for heavy equipment. The railway's narrow gauge (metric, 1,000 mm) limits locomotive payload relative to standard gauge, but the rail advantage over trucks for bulk material remains decisive at volumes exceeding 5 Mt/yr ore equivalent.

Radomiro Tomic (approximately 138 km from Tocopilla, 30 km north of Chuquicamata) and Ministro Hales (138 km from Tocopilla) both connect to FCAB via the Calama yard, making II-2 the best-served cluster in northern Chile for heavy rail logistics.

#### Road Access

Route B-21 (Calama–Antofagasta, 225 km paved highway) and Route 24 (Calama–Tocopilla, 135 km partially unpaved) form the road backbone for the cluster. The Calama–Tocopilla route crosses the Atacama at altitude before descending to the coast and is subject to seasonal closures from flash flooding. The concentration of heavy trucks (cathode transport and reagent imports) creates wear rates on B-21 that require periodic resurfacing, generating intermittent congestion at Calama access points.

#### Production Forecast Implications

The model projects declining production for II-2 mines through 2026–2028 (reflecting Chuquicamata's aging open pit transitioning to underground, and grade decline at Radomiro Tomic). Declining output means fewer concentrate shipments via FCAB and reduced pressure on Tocopilla's cathode dispatch capacity. However, the Tocopilla small-port constraint remains a structural ceiling if any mine undertakes an expansion requiring higher export volumes.

---

### 3.2 Cluster I-1 — Collahuasi + Quebrada Blanca

**Key mines:** Collahuasi, Quebrada Blanca (QB2 post-2021)
**Production (2020–2024 avg):** 653.6 kt/yr
**Segment classification (model):** LargeColossal (Mine_Size = 3 for Collahuasi)

#### Port Infrastructure

Both Collahuasi and QB2 ship concentrate through Iquique (174 km and approximately 190 km, respectively), a Grande-class port with modern bulk handling facilities including a dedicated Collahuasi marine terminal at Puerto Patache (approximately 65 km south of Iquique proper), built and operated by the Collahuasi joint venture. Patache can handle capesize vessels, offering competitive freight rates on Asian routes.

Iquique port itself serves QB2 concentrate via road transport on Route A-97 (Iquique–Huara–Colchane highway), with a branch descending to the Tarapacá altiplano. The QB2 concentrate output, beginning large-scale production in 2022, required Iquique to expand its storage and shiploading facilities, investments completed between 2021 and 2023.

#### QB2 Seawater Pipeline — Infrastructure Anchor

The Quebrada Blanca Phase 2 expansion included construction of a 240 km desalinated seawater pipeline rising from near sea level at Iquique to 4,800 m altitude at the mine. This is among the longest and highest elevation mining water supply pipelines in the world. The pipeline delivers approximately 530 liters per second of desalinated water, enabling QB2's 143,000 t/d concentrator without relying on the Tarapacá aquifer.

From a logistics perspective, the seawater pipeline represents a structural anchor for the cluster's water supply security — a critical input given that QB2 sits in one of the driest environments on Earth. However, the pipeline also represents a single-point vulnerability: a pump failure or section rupture would halt concentrator operations within days. Teck (now Glencore partner) operates redundant pump stations at multiple altitude intervals to mitigate this risk.

#### Road and Rail Access

Rail access to I-1 is classified as "Limited (inland branch)" in the dashboard. The historic Nitrate Railways of Tarapacá (part of the Norte Grande coastal trunk in `estaciones.csv`) do not extend to the Collahuasi plateau (4,400 m). No rail connection exists for either mine. All concentrate leaves by road in semi-trailer truck convoys on Route A-97. At Collahuasi's 2024 output levels (approximately 490 kt/yr), this implies roughly 18,000 truck loads per year (using 40-tonne net payload), or approximately 50 laden truck movements per day from mine to Patache.

The remoteness and altitude of I-1 mines create significant road maintenance costs. The Tarapacá Region road authority requires seasonal inspections of the high-altitude sections above 3,000 m, and the grade differential between altiplano and coast (3,500 m over 170 km) produces brake wear and fuel consumption substantially above lowland benchmarks.

#### Production Forecast Implications

QB2 is the primary expansion project in the I-1 cluster. Model projections show growing output in 2026–2028, driven by QB2 ramp-up completing its throughput curve. This is the one major cluster where logistics pressure is expected to increase rather than decrease. Iquique port utilization and the A-97 truck corridor will face higher demands as QB2 reaches nameplate capacity (approximately 285–310 kt/yr at full ramp). The seawater pipeline is already operating at design capacity; any further expansion would require a parallel line.

---

### 3.3 Cluster II-0 — Escondida

**Key mines:** Escondida (BHP, world's largest copper mine)
**Production (2020–2024 avg):** 1,213.6 kt/yr
**Segment classification (model):** LargeColossal (Mine_Size = 3)

#### Port Infrastructure

Escondida ships concentrate via the port of Antofagasta (155 km), a Grande-class port handling capesize bulk carriers. BHP constructed and operates a dedicated marine terminal at Coloso, located approximately 25 km south of Antofagasta city, which receives concentrate exclusively via the Escondida slurry pipeline. Coloso handles the concentrate with closed belt conveyors and enclosed storage domes, substantially reducing fugitive dust emissions compared to open-air concentrate yards elsewhere.

The Antofagasta / Coloso complex is the highest-volume copper export terminal in the world, processing more than 1 Mt/yr of copper in concentrate form. The port has dedicated bulk vessel berths with a 14-meter draft, accommodating Panamax and capesize vessels carrying 60,000–180,000 tonnes of concentrate per voyage.

#### Concentrate Slurry Pipeline — Engineering Signature

Escondida's most distinctive logistics feature is its 307 km concentrate slurry pipeline running from the mine (3,050 m altitude, Atacama desert, 155 km east of Antofagasta) to the Coloso filter plant at sea level. The pipeline carries copper concentrate suspended in water at approximately 50–55% solids by weight. At full capacity, the pipeline eliminates the need for approximately 1,000 truck trips per day that would otherwise be required to move the same concentrate mass by road.

The pipeline represents an environmental and economic watershed in large-scale mine logistics: (i) it removes thousands of heavy vehicles from the B-4 highway, reducing road accidents, maintenance costs, and particulate emissions; (ii) it allows continuous 24/7 operation decoupled from weather and traffic conditions; (iii) its operating cost per tonne of concentrate is substantially below road haulage at scale. BHP credits the pipeline with making Escondida's sub-scale years (low-grade transition periods) economically viable by holding operating costs flat as throughput varies.

#### Rail Access (FCAB Branch Line)

A dedicated FCAB branch line connects Escondida to the main Antofagasta–Calama corridor near Baquedano junction. This branch is used primarily for acid transport (sulfuric acid is critical for Escondida's SX-EW oxide operations) and for heavy equipment delivery rather than concentrate export (which moves exclusively via pipeline). The rail branch runs approximately 90 km southeast from Baquedano to a siding near the mine property boundary.

#### Production Forecast Implications

The model projects modestly declining production at Escondida through 2027–2028, consistent with grade decline in existing pits and the lengthy timeline for the Los Colorados underground transition. Declining volumes translate into reduced pipeline throughput and lower vessel call frequency at Coloso. The pipeline has design spare capacity that buffers this decline without requiring operational changes. Road logistics remain minimal given pipeline dominance, and any forecast uncertainty in Escondida's production has an outsized national effect given its 1.2 Mt/yr baseline.

---

### 3.4 Cluster III-2 — Candelaria + Caserones

**Key mines:** Candelaria (Lundin Mining), Caserones (JX Nippon)
**Production (2020–2024 avg):** 248.7 kt/yr (combined)
**Segment classification (model):** LargeColossal (Candelaria), Large (Caserones)

#### The Intra-Cluster Contrast

Cluster III-2 illustrates the most extreme accessibility differential within any single cluster in the dashboard analysis: Candelaria lies 54 km from Caldera port, while Caserones lies 160 km from the same port via mountain road. This 3× difference in distance, combined with the dramatic elevation change (Caserones operates at approximately 4,200 m), results in logistics costs per tonne that are structurally disparate between the two mines despite their geographic cluster membership.

#### Candelaria — Short-Haul Advantage

Candelaria benefits from proximity to Caldera, a Mediano-class port on the Atacama coast (Región de Atacama, III Región). The 54 km road distance on Route C-13 (Copiapó–Caldera highway) represents a low-cost, low-risk logistics corridor. Caldera handles Panamax-class vessels with approximately 11-meter draft, sufficient for concentrate bulk carriers on Pacific routes.

Candelaria produces copper concentrate from a conventional flotation circuit. The short haul allows daily truck scheduling without overnight stops, reducing driver fatigue exposure and inventory buffer requirements at the port stockpile. The mine's proximity to Copiapó city (70 km) also facilitates workforce commuting rather than camp-based rotations, lowering labor logistics costs.

No pipeline exists for Candelaria concentrate, but at 54 km the economics of pipeline construction are not compelling — the road option is sufficiently cheap and the volume (approximately 160 kt/yr) does not reach the scale threshold at which pipeline payback periods become attractive (typically above 350 kt/yr at distances exceeding 100 km, based on Chilean industry experience at Escondida and Los Pelambres).

#### Caserones — The Accessibility Outlier

Caserones represents the most logistically challenged major mine in Chile currently in production. Its distinguishing features:

- **Distance:** 160 km from Caldera port, entirely by road (no rail, no pipeline).
- **Altitude:** Approximately 4,200 m, with the access road rising more than 3,500 m from the Atacama floor to the mine over a single passage.
- **Road conditions:** Route C-489 (Caserones access road) includes sections with grades exceeding 8% and hairpin turns impassable for standard triple-combination road trains. Concentrate must move in smaller semi-trailers, increasing the number of vehicle movements per tonne.
- **Weather:** The Atacama puna above 3,500 m experiences severe winter snowfall (June–August) and altiplanic winter lightning storms (January–March). Both create periodic road closures, requiring Caserones to maintain large concentrate stockpiles at the mine and port to buffer shipping schedules.
- **Water supply:** Caserones originally relied on Atacama brine wells before transitioning partially to desalinated water supply; logistics of reagent delivery at altitude further compounds operating costs.

JX Nippon has evaluated concentrate pipeline options for Caserones. However, the terrain — including multiple river valleys (Río Copiapó system) and the extreme elevation differential — raises pipeline capital costs to estimates of USD 400–600 million for a 160 km high-altitude system, making the investment difficult to justify at current production rates (approximately 80–90 kt/yr concentrate copper equivalent).

**Carbon footprint:** Caserones' pure road haulage model generates approximately 18–22 kg CO2 per tonne of copper produced attributable to concentrate transport alone, compared to 4–6 kg CO2/t for pipeline-served mines at similar distances — a structural disadvantage in an era of tightening scope 3 reporting requirements.

#### Production Forecast Implications

The model forecasts relatively stable production for Candelaria through 2029 and a modest decline trajectory for Caserones, reflecting grade variability in the Potrerillos porphyry system. Stable or declining Caserones output reduces road haulage intensity on the C-489 corridor, marginally improving the access road's condition and reducing maintenance expenditure. For Candelaria, stable production implies steady-state Caldera port utilization with no expansion pressure.

---

### 3.5 Cluster IV-1 — Los Pelambres

**Key mines:** Los Pelambres (Antofagasta Minerals), Antucoya (Antofagasta Minerals)
**Production (2020–2024 avg):** 326.9 kt/yr
**Segment classification (model):** Large/LargeColossal (Mine_Size = 2)

#### Port Infrastructure

Los Pelambres ships concentrate via Valparaíso (158 km via road + pipeline route), Chile's largest and most modern port complex (Grande-class). Valparaíso–San Antonio handles general cargo, container traffic, and bulk minerals, with dedicated concentrate berths. The port's draft capacity (15 m) and shiploading rate (up to 3,000 t/h) make it the most efficient export terminal in central Chile.

However, Los Pelambres' operational geography means it does not actually use the full Valparaíso–Los Pelambres road distance for concentrate transport. The mine is located in the Choapa Valley (Coquimbo Region, IV Región) at approximately 3,200 m altitude, and concentrate exits the valley via a dedicated pipeline.

#### Concentrate Pipeline — Los Pelambres to Los Vilos

Los Pelambres operates a 167 km slurry pipeline descending from the mine at 3,200 m to a filter plant and port facility at Los Vilos on the Pacific coast. Los Vilos is a small port (Pequeño class) upgraded by Antofagasta Minerals specifically for Los Pelambres concentrate export, with a submarine loading system and enclosed concentrate stockpile.

The pipeline delivers filtered and thickened concentrate to Los Vilos, where it is loaded onto Panamax-class vessels. In years of high production (above 380 kt/yr), Los Vilos port approaches its export capacity, and Antofagasta Minerals has in the past used Coquimbo port (41 km from Andacollo, 120 km south of Los Vilos) as an overflow terminal. The pipeline eliminates approximately 800 truck movements per day that would otherwise traverse the Choapa Valley's narrow mountain road (Route 45), a significant benefit for valley communities and the Route 5 interchange at Illapel.

#### Road Dependency — Remaining Vulnerability

Despite the pipeline, Los Pelambres retains road dependency for:
- Reagent and consumable supply (sulphur, grinding media, explosives): delivered by truck from Valparaíso or La Serena via Route 45.
- Fuel: diesel tanker convoys from coast to mine.
- Personnel: bus and light vehicle convoys on Route 45, which includes a 48 km unpaved section above 2,000 m.

Route 45 in the Choapa Valley is subject to seasonal closures from Andean snowfall (June–August) and river flooding during La Nina years. A sustained 72-hour closure can disrupt reagent supply to the concentrator, requiring operational rate reductions. Antofagasta Minerals maintains approximately 30 days of key reagent inventory at the mine to buffer these interruptions.

No rail access exists for Los Pelambres. The EFE network's Choapa branch (historic nitrate era) was decommissioned decades before the mine's construction; reinstating rail to the Choapa Valley would require new track construction over terrain unsuitable for economic justification at current concentrate volumes.

#### Production Forecast Implications

The model projects broadly stable production for Los Pelambres through 2027–2029. The mine completed a Los Pelambres Expansion (LPE) project in 2022–2023, adding 70,000 t/d of throughput capacity. Production post-expansion is forecasted by the model at levels consistent with the expanded throughput, with uncertainty driven by grade variability in the aging Pelambres porphyry deposit. Stable production implies steady pipeline utilization and Los Vilos port throughput near current levels, with no expansion pressure anticipated.

---

### 3.6 Cluster VI-0 — El Teniente

**Key mines:** El Teniente (Codelco)
**Production (2020–2024 avg):** 403.3 kt/yr (refined copper, not concentrate)
**Segment classification (model):** LargeColossal (Mine_Size = 3)

#### Unique Product Form — Refined Metal Rather Than Concentrate

El Teniente is the world's largest underground copper mine, located in the Andes at approximately 2,300 m altitude, 80 km east of Rancagua (Libertador General Bernardo O'Higgins Region, VI Región). Its most distinctive logistics feature is that it produces fire-refined copper (anodes, blister copper, and some cathodes) rather than copper concentrate, thanks to the Caletones smelter complex located within the mine property.

Producing refined metal rather than concentrate has profound logistics implications:

- **Lower bulk volume per tonne of copper:** Anodes and blister copper are approximately 98–99% copper, compared to 25–35% copper in concentrate. The same copper content requires roughly 3–4× fewer tonnes of material to transport when shipped as refined metal.
- **No moisture or spillage risk:** Dry refined metal does not present the sedimentation and geotechnical risks associated with concentrate slurry pipelines or wet concentrate road haulage.
- **Higher value per kg:** Refined metal commands premium pricing and is interchangeable with London Metal Exchange (LME) spot delivery, simplifying commercial logistics.

#### Port Access — San Antonio and Multi-Port Distribution

El Teniente ships refined copper (anodes and blister) to multiple ports:
- **San Antonio** (116 km from mine via Route 5 South and Route 78): the primary export terminal. Grande-class port with roll-on/roll-off capacity and dedicated metal storage.
- **Valparaíso** (approximately 125 km): used for some anode export and for general supply imports.
- **San Vicente (Talcahuano)** (approximately 350 km south): used occasionally for blister copper destined for Asian smelters and for heavy equipment imports.

The multi-port access structure provides El Teniente with logistics redundancy unusual among Chilean mines. A strike or weather closure at San Antonio does not halt production because Valparaíso and San Vicente provide alternative exit routes. This redundancy contributes to El Teniente's relatively high production stability in the historical record, which the forecasting model partially captures through lower volatility in the Prod_pct_change feature for this mine.

#### Underground Vertical Logistics

El Teniente's underground operation involves an additional internal logistics dimension absent from open-pit mines: vertical ore transport. The mine uses a system of crushers, ore passes, and conveyor drifts to move ore from production levels (some exceeding 2,000 m below the surface access level) to the coarse ore stockpile. The deepening of the mine into the New Mine Level (Nuevo Nivel Mina, NNM) project — the largest underground mine expansion globally — introduces an additional 400–500 m of vertical haulage distance, increasing internal logistics complexity and capital expenditure.

#### Road Infrastructure

Route 5 South (Pan-American Highway) runs through the Maipo and Cachapoal valleys, providing El Teniente with excellent access to Santiago (80 km north) for heavy equipment, supplies, and worker transport. The mine's proximity to Rancagua city (70 km from the mine, 90 km south of Santiago) allows daily commuting for a fraction of the workforce, reducing camp dependency relative to northern mines.

#### Production Forecast Implications

The model projects modest production decline for El Teniente in 2026–2028, consistent with the transitional phase of the NNM project (temporarily reducing accessible ore reserves while new level infrastructure is completed). After 2029–2030, NNM commissioning should restore and expand production capacity. The refined metal output format means that logistics constraints are not binding in the forecast horizon: San Antonio port has spare capacity, and road infrastructure to VI Región is the most developed of any Chilean mining corridor.

---

## 4. Cross-Cluster Comparison Matrix

| Cluster | Nearest Port | Port Distance (km) | Port Size | Pipeline (Y/N) | Pipeline type | Rail Access | Logistics Cost Tier | 2020–2024 Avg (kt/yr) |
|---|---|---|---|---|---|---|---|---|
| II-2 (Calama) | Tocopilla | 133 | Pequeño | No | — | FCAB main line | Moderate | 941.4 |
| I-1 (Collahuasi+QB) | Iquique / Patache | 174 | Grande | Partial (water only) | QB2 seawater inbound | None (road only) | High | 653.6 |
| II-0 (Escondida) | Antofagasta / Coloso | 155 | Grande | Yes | Concentrate slurry (307 km) | FCAB branch | Low-Moderate | 1,213.6 |
| III-2 (Candelaria+Caserones) | Caldera | 54 / 160 | Mediano | No | — | None | Low (Candelaria) / Very High (Caserones) | 248.7 |
| IV-1 (Los Pelambres) | Los Vilos / Valparaíso | 167 | Pequeño / Grande | Yes | Concentrate slurry (167 km) | None | Low-Moderate | 326.9 |
| VI-0 (El Teniente) | San Antonio | 116 | Grande | No | — | None (road) | Low (refined metal advantage) | 403.3 |

**Logistics Cost Tier definitions:**
- **Low:** pipeline-served or refined-metal output, large port, < 150 km.
- **Low-Moderate:** pipeline-served but small port, or rail + moderate distance.
- **Moderate:** rail access to small port, or road + moderate distance to large port.
- **High:** road-only, large port, high altitude, > 160 km.
- **Very High:** road-only, small-medium port, extreme altitude, > 150 km, no pipeline prospect.

---

## 5. Key Findings

### 5.1 The Tocopilla Bottleneck

Cluster II-2 (Calama/Codelco Norte) is the highest-volume production district in Chile, averaging 941.4 kt/yr across 2020–2024. Despite this, its primary port, Tocopilla, is classified Pequeño — the smallest category in the dashboard's port size taxonomy. Tocopilla lacks the berth depth (maximum 10–11 m) to accommodate capesize bulk carriers, which carry 150,000–180,000 tonnes of concentrate per voyage and offer the lowest per-tonne freight rates on Pacific routes. This forces Codelco to either (a) use smaller, less efficient vessels from Tocopilla at higher unit freight cost, or (b) route concentrate to Antofagasta (230 km from Calama) via FCAB, incurring additional rail tariffs.

The Tocopilla bottleneck is a structural cost disadvantage for the world's largest state-owned copper producer. Upgrading Tocopilla to accommodate Panamax-class vessels (draft ≥ 13 m) has been studied multiple times but faces environmental opposition (the port's exposure to Atacama wind patterns creates sedimentation risk for dredging works) and competition from Mejillones (a Mediano port 65 km south of Antofagasta with deeper berths and existing bulk handling facilities).

Mejillones — nearest port for Cluster II-1 (Centinela, Sierra Gorda) at 115 km from Sierra Gorda — could serve as an overflow terminal for II-2 metals if road or rail connections to Calama were upgraded. The distance from Calama to Mejillones is approximately 195 km by Route 25, not substantially worse than the Antofagasta route. FCAB does not currently serve Mejillones, but a spur from Baquedano junction would be approximately 55 km.

### 5.2 The Pipeline Advantage for Large Mines

Escondida's slurry pipeline (307 km, ~1,000 truck trips eliminated per day) and Los Pelambres' pipeline (167 km, ~800 truck trips eliminated per day) together demonstrate that pipeline infrastructure is the single most transformative logistics intervention available to large-throughput copper mines with distances between 100 and 400 km to coast. The capital investment (estimated USD 600–900 million for a 300 km system at current construction costs) is recovered within 8–12 years at production volumes above 400 kt/yr, based on the differential between truck haulage costs (USD 12–18/t concentrate) and pipeline operating costs (USD 2–4/t concentrate).

The mines without pipelines that would most benefit from this technology are:
1. **Caserones** (160 km from Caldera, 80–90 kt/yr): volume currently too low for economic payback; viable if production doubles.
2. **Collahuasi** (174 km from Iquique, 490 kt/yr): the one major mine where a pipeline has not been built despite sufficient volume. Terrain complexity (altitude change from 4,400 m to sea level) and existing Patache marine terminal investment may explain this gap.

### 5.3 Caserones — The Accessibility Outlier

Caserones is the most logistically isolated major copper mine currently in production in Chile. Its combination of extreme altitude (4,200 m), long road distance (160 km from Caldera), mountain road constraints (no rail, no pipeline, no paved highway for the last 80 km), and weather-induced seasonal closures places it in a "Very High" logistics cost tier with no peer in the Atacama region.

The mine's production trajectory forecasted by the model shows modest decline through 2030, which paradoxically reduces (but does not eliminate) the urgency of logistics infrastructure investment. If JX Nippon pursues a capacity expansion to improve unit economics, the logistics constraint will become binding before any processing bottleneck. The CO2 intensity of Caserones' logistics — estimated at 4–5× that of pipeline-served peers per tonne of copper exported — will become increasingly relevant as Chile moves toward carbon border adjustment mechanisms in its trade relationships with the EU.

### 5.4 Collahuasi-QB2 as an Expanding Logistics System

The I-1 cluster is the only cluster in this analysis where logistics demand is expected to grow through the 2026–2032 forecast horizon, driven by QB2 ramp-up. The combination of QB2's new concentrate output (adding approximately 200–220 kt/yr to I-1 cluster volumes) and the Patache marine terminal's current throughput utilization implies that I-1 is the one cluster where infrastructure stress will increase rather than ease.

Specific pressure points: (i) A-97 highway truck frequency from Collahuasi and QB2 to Iquique / Patache, (ii) Iquique port concentrate storage expansion already underway, and (iii) QB2 seawater pipeline pump station reliability (any unplanned outage halts the concentrator).

### 5.5 El Teniente's Structural Logistics Premium

El Teniente's production of fire-refined metal rather than concentrate gives it a structurally lower logistics cost and complexity profile than any other major Chilean mine at similar volumes. Refined copper anodes are dry, stable, and dense — approximately 3.5× fewer tonnes of material per tonne of copper compared to 30%-grade concentrate. The multi-port access structure (San Antonio, Valparaíso, San Vicente) provides redundancy absent elsewhere. The proximity to Santiago and Rancagua minimizes supply chain lead times for consumables and reduces workforce logistics costs relative to remote northern mines.

This structural advantage partially explains El Teniente's historically high production stability (visible in the time series) and contributes to the model's relatively accurate forecasts for this mine (scoreboard WR = 81.5% for Ens_Segmentado, the highest of any mine in the annual model).

---

## 6. Forecast Implications for Logistics

The model's 2026–2032 projections show declining or stable production for all clusters except I-1 (QB2-driven expansion). This has a counterintuitive positive implication for logistics infrastructure: the mines that most stress infrastructure (II-0, II-2, VI-0) are moving into trajectories of reduced throughput, which:

- Reduces road wear on B-21 (Calama–Antofagasta), Route 5 South (VI Región corridor), and B-4 (Antofagasta coastal).
- Reduces port call frequency at Antofagasta/Coloso (II-0) and Tocopilla (II-2), extending the window before port capacity upgrades become necessary.
- Eases pipeline utilization rates at Coloso and Los Vilos, allowing deferred maintenance without operational impact.

The "small victory" of declining production in the largest clusters is that Chile's copper logistics infrastructure — built for the 2000–2014 commodity boom era — gains breathing room it does not need to replace or significantly expand in the near term. The exception is I-1, where infrastructure investment is actively occurring and needed.

However, a caution: the forecasting model carries uncertainty intervals (q10–q90 quantile models) that widen substantially at H+5 to H+7. The bear scenarios for Escondida (II-0) show production as low as 900 kt/yr by 2031, while the bull scenarios approach 1,350 kt/yr. The logistics infrastructure planning implications of these two scenarios are vastly different: the bear scenario implies idle pipeline capacity, while the bull scenario implies Coloso port approaching maximum throughput. Infrastructure planners using this thesis's projections should weight the quantile intervals, not just the base case.

---

## 7. Suggested Next Steps for the Thesis

### 7.1 Incorporate a Logistics Cost Feature

The current annual model uses 9 base features (E6_BASE). None explicitly captures logistics cost or accessibility quality. A candidate feature is **Port_Size_Score** (coded as 1=Pequeño, 2=Mediano, 3=Grande for the nearest port) or **Pipeline_Binary** (1 if mine has a concentrate pipeline, 0 otherwise). These could be added to E6_BASE and tested in an E7_BASE feature set, using the existing rolling-origin validation framework to assess whether logistics proxies improve Win Rate or Skill Score.

Hypothesis: mines with pipeline access (Escondida, Los Pelambres) may show systematically different forecast bias patterns from road-dependent mines, since pipeline-served mines have lower operational variance (fewer weather-related disruptions). If the model systematically over-forecasts road-dependent mine production (by missing the downside variance), a logistics accessibility feature may reduce this bias.

### 7.2 Logistics-Adjusted Scenario Construction

The current scenario projections (bear/base/bull) are driven exclusively by copper price regime (Cu_regime feature coded at 0.2/0.5/0.8 for bear/base/bull). An alternative scenario axis could be **logistics disruption scenarios**: e.g., a scenario where Tocopilla port undergoes a 6-month closure (due to seismic event or infrastructure failure), forcing Codelco Norte to reroute through Antofagasta at higher cost and lower throughput. The model's flexible scenario input structure (projections_scenarios_2026_2032.csv) could accommodate this by adjusting the origin_prod or a new logistics-disruption flag for selected mine-year combinations.

### 7.3 Carbon Intensity as a Supplementary Dashboard Layer

The dashboard `mining_clusters_v2` currently displays water rights, port proximity, and cluster boundaries. Adding an estimated **logistics CO2 intensity layer** (kg CO2 / tonne Cu, by mine) would make the accessibility analysis operational in the visualization. This metric can be estimated from first principles using: distance (km) × payload (t) × diesel factor (2.68 kg CO2/litre) / fuel efficiency (km/litre), compared against the pipeline equivalent (electricity consumption × carbon intensity of SING grid). The Cochilco 2023 water factors already establish the methodology precedent for this kind of per-mine environmental metric.

### 7.4 Rail Network Centrality Analysis

The `estaciones.csv` dataset (742 stations, 4 connected components) is currently used in the dashboard for spatial visualization. A network centrality analysis — using betweenness centrality to identify which stations are most critical for supply chain connectivity — could reveal structural vulnerabilities in the FCAB network serving II-0 and II-2 clusters. Specifically, Baquedano junction (where the Escondida branch meets the main Antofagasta–Calama line) is a single point of failure for both clusters' rail logistics. A station-level centrality score could be computed with NetworkX and overlaid on the dashboard.

### 7.5 Accessibility Index for Mine-Level Regression

A composite **Accessibility Index** (AI) could be constructed as a weighted sum of: (i) port distance normalized, (ii) port size score, (iii) pipeline binary, (iv) rail binary, and (v) altitude penalty (kg CO2 per km above 2,000 m). This index could then be used as a predictor in a cross-sectional regression of forecast error (|predicted – actual| / actual) against AI, testing whether accessibility predicts model accuracy. High-AI (good accessibility) mines may be easier to forecast due to smoother production patterns, while low-AI mines may exhibit higher residual variance.

---

## References and Data Sources

- `01_Data/processed/Produccion_Master.csv` — historical production data, 1982–2025, 36 mines.
- `04_Dashboard/outputs/mining_clusters_v2.html` — spatial cluster visualization with port, rail, and mine layers.
- `03_Forecasting/annual_model/outputs_best/projections_scenarios_2026_2032.csv` — bear/base/bull scenario projections, 2026–2032.
- `03_Forecasting/annual_model/outputs_best/scoreboard_annual_v7.csv` — per-mine forecast performance metrics (WR, Skill, DM test).
- Cochilco (2023). *Proyección de Consumo de Agua en la Minería del Cobre 2023–2034*. Comisión Chilena del Cobre.
- Teck Resources (2022). *Quebrada Blanca Phase 2 — Project Description and Environmental Impact Assessment Summary*. Filed with SEIA.
- BHP Billiton (2019). *Escondida Operations — Integrated Annual Report*. Internal sustainability metrics.
- Antofagasta Minerals (2023). *Los Pelambres — Operational Overview and Expansion Update*.
- `estaciones.csv` — 742 Chilean rail stations, 4 network components (FCAB, EFE, Arica-La Paz, Norte Grande coastal).

---

*This report is part of a thesis research project on multi-horizon production forecasting for Chilean copper mines (1982–2025). All logistics figures are sourced from publicly available company reports, environmental impact assessment filings, and Cochilco industry data unless otherwise noted. Port size classifications and distance measurements follow the `mining_clusters_v2` dashboard methodology.*
