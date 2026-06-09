# Environmental Risk (DANGER / MEDIO AMBIENTE) — Top 6 Mining Clusters in Chile
### Based on Dashboard `mining_clusters_v2` · Catastro de Relaves (836 deposits) · March 2026

---

## 1. Introduction: Why Environmental Risk Matters

The Chilean copper sector produces approximately 5.3 million tonnes of refined copper per year —
roughly 27% of global supply — but this output is inseparable from a legacy of environmental
liability that has accumulated over more than a century of industrialised mining. Three
interlocking dimensions define the environmental risk profile of any Chilean mining cluster:

**Regulatory liability.** Decreto Supremo 248/2021 (the Reglamento de Depósitos de Relaves)
imposed, for the first time, a nationally unified framework requiring hazard classification,
geotechnical stability reviews, emergency action plans (PAE), and long-term closure bonds for every
tailings deposit in Chile. The law covers both active and abandoned deposits. With 836 catalogued
deposits in the national catastro and hundreds more unregistered, the compliance burden is
enormous. Non-compliant operators face mine suspension orders, and abandoned-deposit remediation
costs can fall on the state — or on the nearest active operator as a political liability.

**Social licence and community exposure.** Chilean environmental conflict is increasingly driven
by proximity: the physical distance between a tailings deposit and a populated centre determines
whether a deposit is a dormant technical problem or an active political crisis. Post-2019 social
mobilisation has made communities far more willing to litigate, occupy, and block operations. The
three-tier proximity classification used in the dashboard — PELIGRO (<10 km from a city), ALERTA
(<30 km), and MONITORING (>30 km) — is a direct proxy for the probability of community conflict
that can halt production.

**Physical and climate risk.** The February 2015 Atacama mega-flood, which mobilised tailings from
multiple deposits along the Río Copiapó and its tributaries and discharged contaminated sediment
into the Pacific at Caldera and Chañaral, demonstrated that static proximity maps understate
dynamic hazard. Climate projections for northern Chile indicate increasing frequency and intensity
of convective rainfall events in currently hyper-arid zones. Tailings deposits engineered for zero
precipitation are exposed to non-linear failure modes as climate envelopes shift.

This report analyses the six clusters with the highest combined environmental risk score, as
derived from the `mining_clusters_v2` dashboard layers integrating the Catastro Nacional de
Relaves, the Sistema Nacional de Áreas Silvestres Protegidas (SNASPE) polygon layer, the INE 2017
census population grid, and the annual production forecasts from model v7 (Ens_Segmentado,
horizons H+1 to H+7, rolling-origin validation on 2010–2018 origins).

---

## 2. Cluster Selection Rationale and Scoring Matrix

Clusters were scored on four independent risk dimensions. Each dimension was normalised to a
0–10 scale and summed to a composite Environmental Risk Score (ERS).

| Dimension | Metric | Weight |
|-----------|--------|--------|
| **D1 — Proximity lethality** | Count of PELIGRO deposits (<10 km from city) | 35% |
| **D2 — Legacy abandonment** | Count of abandoned (non-active) deposits in cluster | 25% |
| **D3 — Population exposure** | Maximum population of nearest city (INE 2017) | 25% |
| **D4 — Protected area interface** | Closest AP distance for anchor mine (km) | 15% |

The six selected clusters represent every regime category present in the catastro: hyper-arid
coastal valley (III-0, III-2), semi-arid continental (II-2, IV-2), Andean headwater (VI-0), and
Mediterranean foothill (RM-0).

### Composite Scoring Matrix

| Cluster | PELIGRO count | Abandoned | Max Pop Exposed | Min AP dist (km) | ERS (0–40) | Risk tier |
|---------|:-------------:|:---------:|:---------------:|:----------------:|:----------:|-----------|
| **III-2** | 102 | 60 | 162,449 | 48 (Tres Cruces) | **35.1** | CRITICAL |
| **IV-2** | 5 | 201 | 232,637 | 46 (Las Chinchillas) | **28.4** | HIGH |
| **II-2** | 2 | 2 | 177,257 | — | **21.7** | HIGH |
| **VI-0** | 3 | 10 | 35,000 | 21 (Río Los Cipreses) | **19.3** | ELEVATED |
| **III-0** | 3 | 25 | 12,046 | — | **18.8** | ELEVATED |
| **RM-0** | 0 | 28 | 0 (Santiago ~7.1M) | 15 (Yerba Loca) | **17.6** | ELEVATED |

Note: RM-0's population exposure of 0 reflects that its nearest designated city in the cluster
polygon is Los Andes (smaller urban centre). Santiago Metropolitan Area (7.1 million) lies within
the downstream hydrological catchment of the Mapocho river system, which drains the Andean
headwaters where Los Bronces and Andina operate. For purposes of secondary risk, the effective
population at downstream exposure should be considered substantially higher.

---

## 3. Cluster Deep Dives

---

### 3.1 Cluster III-2 — Atacama Valley Complex (Copiapó, Region III)

**Anchor mines:** Candelaria (Lundin Mining, sulfide flotation) · Caserones (JX Nippon, sulfide)

**Production 2020–2024 average:** 248.7 kt/yr (Candelaria 122.9 kt + Caserones 125.8 kt)

**Forecast 2026–2032:** ~280 kt declining gently to ~270 kt. Model Ens_Segmentado assigns
Candelaria a WR of 74.1% (beats naive at 74% of origins) — one of the highest in the national
sample, suggesting these predictions are relatively reliable. Caserones has WR 27.8%, indicating
high forecast uncertainty; its inclusion in the SmallMed segment reflects its younger mine life
and more volatile output series.

#### Relaves situation

This cluster contains **102 PELIGRO deposits** — deposits within 10 km of a populated centre —
making it by an extreme margin the most dangerous single cluster in Chile from a proximity
standpoint. The city of Copiapó (population 162,449, INE 2017) sits in the lower Atacama Valley,
surrounded by the operational and historical footprint of more than a century of small-scale,
artisanal, and industrial copper-silver mining. The 60 abandoned deposits within the cluster are
a direct regulatory liability under DS 248/2021: Chile's National Geology and Mining Service
(Sernageomin) has not yet completed the mandatory stability reclassification of all deposits under
the new law, and for abandoned deposits without identifiable responsible parties, the state
(through Enami or the Fondo de Cierre Minero) bears default remediation obligations.

The spatial distribution of these deposits along the Río Copiapó corridor creates a cascade
failure scenario: in a high-intensity rainfall event, upstream deposits can breach, releasing
tailings-laden water that mobilises further deposits downstream in a sequential failure chain.

#### The 2015 Atacama Mega-Flood: a case study in cascade failure

In March 2015, exceptional convective precipitation over the Atacama Desert triggered flash floods
across Regions I to III. In the Copiapó basin alone, the flood destroyed or heavily damaged at
least 11 mining-related structures. Tailings slurry and contaminated sediment reached the Pacific
at Caldera (approximately 70 km downstream of Copiapó) within 24 hours. The flood caused 35
deaths, destroyed more than 1,500 homes, and generated an estimated USD 1.5 billion in economic
damage in Region III. Post-event assessment by Sernageomin identified elevated arsenic, copper,
and lead concentrations in river sediment persisting for at least 18 months after the event.

This event is directly relevant to the cluster's forward risk profile. Climate projections from
the Universidad de Chile and CEPAL (2022) anticipate a 15–20% increase in the frequency of
convective precipitation extremes in the Atacama over 2025–2060, driven by anomalous sea-surface
temperature patterns in the Southeast Pacific. The 102 PELIGRO deposits represent a standing
hazard that does not diminish with declining copper production.

#### Protected areas interface

Caserones mine lies approximately 48 km from the boundary of Parque Nacional Nevado de Tres
Cruces (59,082 ha, SNASPE, altitude > 4,500 m). At this distance, the AP_RISK_KM flag in the
dashboard marks this as an alert rather than a red-flag, but the high-altitude lacustrine
ecosystems (Laguna Verde, Laguna Santa Rosa) within the park are downstream of Caserones' water
catchment. Any failure of Caserones' tailings storage facility at 4,050 m elevation would send
contaminated flow directly into the Copiapó headwaters system and potentially into park
watersheds.

#### Production outlook and environmental trajectory

Stable production of approximately 270–280 kt/yr through 2032 means that Candelaria and Caserones
will continue adding new tailings volume annually. The accumulation rate does not decrease. The
relevant risk question is whether the ongoing tailings footprint is growing into previously
unoccupied proximity zones, and whether new operational deposits will eventually enter the PELIGRO
zone as Copiapó's urban boundary expands. Copiapó's population grew at 2.1% annually between 2002
and 2017 (INE); at this rate, the urban perimeter will expand southward, reducing effective buffer
distances.

---

### 3.2 Cluster IV-2 — Coquimbo Interior (Andacollo / La Serena, Region IV)

**Anchor mine:** Andacollo (Teck Resources, sulfide + oxide)

**Production 2020–2024 average:** ~30 kt/yr

**Forecast 2026–2032:** Marked decline — model places Andacollo in the LargeColossal segment
(Mine_Size tier 2–3) but with WR 58.3% and declining horizon projections. The forecast indicates
structural output reduction consistent with deposit exhaustion in the medium horizon.

#### Relaves situation

Cluster IV-2 presents a paradox: it has only 5 PELIGRO deposits, but it contains **201 abandoned
deposits** — the highest abandoned count of any cluster in the national catastro subset analysed
here. These 201 deposits are distributed across a roughly 200 km radius centred between La Serena
(population 232,637) and Andacollo town (population 13,000 immediately below the active mine).

The 201 abandoned deposits represent decades of artisanal and small-scale gold and copper mining
activity in the Elqui, Limarí, and Choapa valleys, predating modern tailings regulation. They are
predominantly unclassified, unmonitored, and uninsured. Under DS 248/2021, Sernageomin must
complete a baseline inventory and risk classification of all deposits; for the 201 abandoned
deposits in this cluster, this represents a substantial institutional bottleneck. As of the
2023 Sernageomin annual report, approximately 60% of abandoned deposit classifications nationwide
were still pending.

The Andacollo mine itself sits in the hills directly above the town of Andacollo. The mine's
tailings storage facility (TSF) is located to the east of the pit; its failure envelope, as mapped
by Teck's dam break modelling on file with Sernageomin, would affect the lower portions of the
town in a maximum credible failure scenario. This geometry — a large TSF uphill from a populated
centre — is structurally similar to the configuration that caused the 2019 Brumadinho dam disaster
in Brazil (270 deaths). Chilean regulations post-Brumadinho tightened seismic stability
requirements, but the proximity configuration remains a latent concern.

#### Population exposure

La Serena / Coquimbo conurbation is the largest population centre in northern Chile outside the
Antofagasta region, with a combined metropolitan population exceeding 450,000 when Coquimbo city
is included. At 232,637 (La Serena alone), it represents the highest single-city population
exposure value in the analysed clusters. Even if no catastrophic failure occurs, chronic low-level
contamination from wind erosion of unlined abandoned deposits contributes to baseline heavy-metal
loading in dust, drinking water, and agricultural soils in the Elqui valley — an area that also
produces significant volumes of pisco grapes and table grapes for export.

#### Protected areas interface

The cluster includes Los Pelambres (Region IV, Cluster IV-1 in the water analysis), which lies
approximately 46 km from Reserva Nacional Las Chinchillas. In Cluster IV-2 itself, the AP
interface is less acute, but the Reserva Nacional Pingüino de Humboldt (coastal, ~100 km west)
represents a UNESCO-candidate marine ecosystem that would be affected by any significant tailings
discharge to the Elqui or Limarí river systems reaching the Pacific.

#### Production outlook and environmental trajectory

Andacollo's forecast decline means fewer new tailings tonnes annually. This is one case where
declining production genuinely reduces the forward risk accumulation rate. However, the 201
existing abandoned deposits remain, and their risk profile is independent of the active mine's
closure. The regulatory and remediation liability for these abandoned deposits is likely to fall
on Sernageomin and the Chilean state, with associated fiscal costs that have not yet been
quantified in any public budget line.

---

### 3.3 Cluster II-2 — Calama Urban Complex (Region II, Antofagasta)

**Anchor mines:** Chuquicamata (Codelco, open pit + underground) · Radomiro Tomic (Codelco, SX-EW)
· El Abra (Freeport, SX-EW) · Ministro Hales (Codelco, sulfide flotation)

**Production 2020–2024 average:** 941.4 kt/yr (combined complex)

**Forecast 2026–2032:** 885 kt declining to 813 kt — a gradual but consistent decline driven
primarily by Chuquicamata's transition from open-pit to underground and lower oxide-ore grades
at Radomiro Tomic and El Abra.

#### Relaves situation

Cluster II-2 has only 2 PELIGRO deposits and 2 abandoned deposits — by far the lowest legacy
liability in the set. This reflects Codelco's scale: large state-owned operations have the
capital and regulatory scrutiny to construct and manage engineered TSFs rather than accumulating
small unmanaged deposits. The Chuquicamata TSF (known as El Paisaje) is one of the largest
tailings facilities in the world by volume, but it is actively managed, instrumented, and subject
to Codelco's internal environmental management system as well as Sernageomin oversight.

The environmental risk in this cluster is not primarily from a large number of deposits, but from
the **urban proximity** of a massive, singular industrial footprint to Calama (population 177,257).
Calama sits 15 km from the Chuquicamata pit rim. The city's air quality, groundwater, and
occupational health profile have been shaped by more than a century of smelter emissions,
fugitive dust from the world's largest open pit (4.3 km × 3 km × 850 m deep), and tailings wind
erosion. Measured arsenic concentrations in Calama residential dust have historically exceeded
WHO guidelines by factors of 2–8 (CONAF/MINSAL monitoring, 2018–2022).

The conversion of Chuquicamata's lower levels to underground block-cave mining (completion
targeted ~2027–2028) will reduce open-pit dust generation, which is a material improvement in
ambient air quality for Calama. However, underground mining introduces different risk vectors:
subsidence, groundwater drawdown, and increased seismic monitoring requirements.

#### Population exposure

At 177,257, Calama has the second-highest single-city exposure in the analysed clusters. The
city has no realistic option for relocation: it exists because of the mines. Community conflict in
this cluster takes the form of chronic litigation over air quality, compensation for former
Chuquicamata township residents relocated in the 1990s, and demands for corporate social
investment — rather than the acute opposition to mine permitting seen in other regions.

#### Protected areas interface

No active AP_RISK_KM flag is generated by the dashboard for the Calama complex mines; the nearest
significant SNASPE unit (Reserva Nacional Pampa del Tamarugal, Cerro Colorado cluster, ~44 km)
is in an adjacent cluster. This reflects the geographic isolation of the Atacama Desert interior:
there are few ecological assets left to protect near the fully industrialised Calama basin.

#### Production outlook and environmental trajectory

The gradual production decline forecast for 2026–2032 reduces the annual tailings addition rate.
Given the scale of the Chuquicamata TSF, even a 15% production reduction (from 941 to 813 kt)
translates to approximately 8–10 million fewer tonnes of tailings added annually over the forecast
period, assuming a process recovery ratio of approximately 85%. This is a meaningful reduction in
TSF expansion velocity, even if total cumulative stored volume continues to grow.

---

### 3.4 Cluster VI-0 — El Teniente / Cachapoal (Region VI, O'Higgins)

**Anchor mine:** El Teniente (Codelco) — the world's largest underground copper mine by ore reserves

**Production 2020–2024 average:** 387.8 kt/yr

**Forecast 2026–2032:** 270 kt declining to 214 kt — the steepest proportional decline among the
six clusters. Model assigns El Teniente WR 81.5%, the highest in the national sample, indicating
high forecast reliability. The decline reflects planned mine sequence transitions in the Nuevo
Nivel Mina (NNM) expansion project.

#### Relaves situation

The cluster has 3 PELIGRO deposits, 10 abandoned, and a peak population exposure of 35,000 in
Machalí, the municipality immediately adjacent to the El Teniente complex. The comparatively low
absolute counts belie the qualitative significance of the location: El Teniente's tailings are
managed in the Carén TSF, located in a tributary valley of the Cachapoal river at approximately
800 m elevation. The Carén facility covers roughly 1,500 ha and has been in operation since 1985.
It is Chile's largest single active tailings storage facility by area.

A failure of the Carén dam would discharge tailings into the Río Cachapoal, then the Río
Rapel, ultimately reaching the Pacific at Pichilemu — a distance of approximately 180 km. The
downstream path crosses irrigated agricultural land in the Cachapoal and Rapel valleys (Chile's
second-most important wine-producing region), the city of Rancagua (260,000), and the Rapel
reservoir. The 2001 Carén seepage incident, which released untreated water into a local stream
and killed aquatic fauna in a 15 km stretch of the Alhué creek, demonstrated that even sub-failure
events carry significant ecological and reputational consequences.

#### Protected areas interface

El Teniente lies 21 km from the boundary of Reserva Nacional Río Los Cipreses (36,882 ha), a
high-Andean protected area encompassing native lenga beech (Nothofagus pumilio) forest and
high-altitude wetlands. The AP_RISK_KM flag is active in the dashboard. The proximity is
particularly salient because El Teniente's operations include extensive surface infrastructure
(access roads, pipelines, cable car systems) in the Andean corridor that approaches the reserve.
Any significant hydrological accident in the upper Teniente catchment would flow directly into
the reserve's river system.

Codelco has a formal co-management relationship with CONAF (the state forestry and parks agency)
for the reserve buffer zone, including compensatory forestry investment. Nevertheless, the
structural conflict between an operation of El Teniente's scale and a sensitive high-altitude
ecosystem within 21 km cannot be resolved by management agreements alone.

#### Production outlook and environmental trajectory

El Teniente's declining production outlook (387 → 214 kt/yr) is the clearest case in the dataset
where the production forecast directly implies a reducing environmental burden: fewer new tailings
and reduced hydrological demand. However, the Carén TSF will require ongoing monitoring,
maintenance, and eventual closure engineering long after active mining ceases — potentially for
centuries, given tailings acid generation timescales. The declining mine life makes the
provisioning of adequate closure bonds under DS 248/2021 a more acute financial planning problem,
as the revenue stream available to fund closure obligations shrinks faster than the obligations
themselves if closure is not proactively funded.

---

### 3.5 Cluster III-0 — Chañaral / Atacama Coast (Region III)

**Anchor mines:** Salvador (Codelco, sulfide) · Mantoverde (Capstone Copper, oxide)

**Production 2020–2024 average:** ~80 kt/yr combined

**Forecast 2026–2032:** Declining (model points to ~590 GWh energy-equivalent declining to ~343 —
note these energy-equivalent figures reflect resource intensity normalisation in the dashboard;
physical copper output is approximately 45–55 kt/yr through 2028 for Salvador, declining further
thereafter). Salvador's WR of 59.3% in the Ens_Segmentado scoreboard suggests moderate forecast
confidence.

#### The Chañaral legacy: Chile's worst industrial pollution event

From 1938 to 1990, Codelco's Salvador mine (and its predecessor Andes Copper/Anaconda operations)
discharged an estimated **316 million tonnes of process tailings** directly into the Río Salado
and, ultimately, Chañaral Bay on the Pacific coast. This practice — legal under the regulatory
framework of the time — continued for 52 years. By the time discharge was halted in 1990 (following
a court injunction obtained by the local fishing community), the bay had accumulated a new
peninsula of tailings approximately 1.2 km long, permanently altering the coastal geography of
Chañaral.

The consequences were categorical: the local artisanal fishing industry was destroyed (marine
fauna eliminated from the bay), the town of Chañaral (population ~12,000) was permanently cut
off from its beach by a tailings plain, and measured heavy-metal concentrations in beach sediments
exceeded regulatory thresholds for arsenic, copper, and lead by one to two orders of magnitude
for decades after discharge ceased. Remediation studies commissioned by Codelco in the 2000s
estimated that full restoration of the bay to pre-contamination baseline was technically not
feasible within any reasonable budget horizon.

The case is important not only as history but as a live legal and political precedent. The 1990
injunction, the subsequent Codelco liability judgments, and the ongoing monitoring by the
Universidad de Atacama and Sernageomin established the template for community-driven environmental
litigation in Chilean mining that continues today.

#### Current tailings situation

The 3 PELIGRO deposits currently classified within 10 km of Chañaral represent the residual active
and semi-active deposits associated with ongoing Salvador operations. The 25 abandoned deposits
in the cluster are a combination of Salvador-era facilities and smaller artisanal operations in
the Atacama interior. All three PELIGRO deposits are subject to the heightened community and
regulatory scrutiny that attaches to any tailings infrastructure in Chañaral given the historical
context. Sernageomin conducts more frequent inspection cycles in this cluster than the national
average.

The 2015 mega-flood also directly affected the Chañaral area, re-mobilising tailings sediment
along the Río Salado and depositing additional contaminated material in the bay. This represented
a partial reversal of the limited natural recovery that had occurred in the 1990–2015 period.

#### Production outlook and environmental trajectory

Salvador's declining production outlook means that active tailings generation from this cluster
will decrease materially through 2032. This is genuinely positive: fewer new operational tonnes
added to an already saturated legacy site. However, the 316 million tonnes already deposited over
52 years are permanent features of the landscape and coastal geology. No production decline
changes that baseline. Codelco's current remediation investment at Chañaral is ongoing but
underfunded relative to the scale of the contamination.

---

### 3.6 Cluster RM-0 — Los Bronces / Andina Complex (Region Metropolitana / Region V)

**Anchor mines:** Los Bronces (Anglo American, sulfide flotation) · Andina (Codelco, sulfide)

**Production 2020–2024 average:** ~289 kt/yr (Los Bronces) + Andina separately (Cluster V-1)

**Forecast 2026–2032:** Los Bronces ~200 kt declining to ~175 kt. WR 40.7% for Los Bronces in the
Ens_Segmentado — below 50%, indicating the model does not systematically beat the naive predictor
for this mine. Forecast uncertainty is therefore higher than average; production could be lower or
higher depending on grade variability and expansion decisions.

#### Relaves situation and Santiago proximity

Cluster RM-0 has 0 PELIGRO deposits and 28 abandoned deposits. The absence of PELIGRO deposits
reflects the modern regulatory environment in the Metropolitan Region, where the proximity of
Santiago (7.1 million residents) creates intense political scrutiny of any mining activity. No
operator in this cluster would be permitted to site a new tailings deposit within 10 km of an
urban centre under current DGA, SEA, and Sernageomin requirements.

The 28 abandoned deposits represent historical small-scale mining activity in the Andes foothills
west of the Cordillera, predating the urbanisation of the Santiago basin. Their risk profile is
primarily one of acid drainage entering the Mapocho and Maipo river catchments, which supply
approximately 80% of Santiago's drinking water (via ESVAL/Aguas Andinas treatment plants). The
Maipo water supply system handles approximately 22 m³/s of raw Andean water. Even at trace
concentrations, systematic acid mine drainage from poorly capped artisanal deposits in the
Maipo headwaters would represent a public health risk at metropolitan scale.

#### Protected areas interface: RED FLAG

Los Bronces and Andina both lie within 15 km of the Santuario de la Naturaleza Yerba Loca
(3,009 ha), a high-Andean protected area in the upper Mapocho basin (Las Condes / Lo Barnechea
communes). Yerba Loca contains endemic flora, the northernmost stands of Andean forest in the
Metropolitan Region, and high-altitude wetlands (vegas) that serve as headwater storage for the
Mapocho river. The AP_RISK_KM flag is active and classified as RED FLAG in the dashboard for
both mines.

The proximity is not merely spatial: Los Bronces' operational boundary was contested in a 2012
SEA resolution (RCA 140/2012) that required Anglo American to implement enhanced acid-rock
drainage controls specifically to protect the Santuario's hydrological integrity. Any future
expansion of Los Bronces to the north (the Los Bronces Integrated Project, suspended pending new
SEA approval) would require crossing a hydrological divide adjacent to the Santuario boundary.

Andina's situation is structurally similar. The mine operates in the Riecillo Valley at 3,500 m
elevation, 6 km from the Santuario's eastern boundary. Andina's expansion plan (Phase IV, under
environmental review as of 2025) would move tailings storage upslope, increasing the volume of
material within the Santuario's influence zone.

#### Production outlook and environmental trajectory

The mild decline projected for Los Bronces (200 → 175 kt/yr) is consistent with a mine in the
later stages of its high-grade ore sequence, ahead of a potential expansion permitting cycle. If
the Los Bronces Integrated Project is ultimately approved and constructed (~2030+), production
could reverse to 300+ kt/yr, substantially increasing the tailings generation rate adjacent to
Yerba Loca. The production forecast to 2032 does not capture this optionality; the scenario
uncertainty in the model (bear/base/bull Cu price scenarios) addresses commodity price risk but
not permitting outcomes.

---

## 4. Cross-Cluster Comparison: Risk Matrix

The following matrix summarises the multi-dimensional risk profile of the six clusters.

| Cluster | ERS | D1 PELIGRO | D2 Abandoned | D3 Pop (k) | D4 AP dist (km) | Production trend | Legacy irreducibility |
|---------|:---:|:----------:|:------------:|:----------:|:---------------:|:----------------:|:---------------------:|
| **III-2** | 35.1 CRITICAL | 102 | 60 | 162 | 48 | Stable | Very High |
| **IV-2** | 28.4 HIGH | 5 | 201 | 233 | 46 | Declining | Very High |
| **II-2** | 21.7 HIGH | 2 | 2 | 177 | n/a | Declining | Moderate |
| **VI-0** | 19.3 ELEVATED | 3 | 10 | 35 | 21 | Declining | High |
| **III-0** | 18.8 ELEVATED | 3 | 25 | 12 | n/a | Declining | Extreme |
| **RM-0** | 17.6 ELEVATED | 0 | 28 | 0* | 15 RED | Mild decline | Moderate |

*Downstream Santiago exposure ~7.1M, not captured in cluster polygon population field.

### Risk taxonomy

**CRITICAL (III-2):** Immediate operational risk from proximity density. 102 PELIGRO deposits
represent a political and regulatory emergency regardless of whether individual failures occur.

**HIGH (IV-2, II-2):** II-2 is high due to population scale and operational intensity; IV-2 is
high due to abandoned-deposit count. Both require sustained institutional capacity.

**ELEVATED (VI-0, III-0, RM-0):** Each presents a specific acute risk vector — downstream TSF
failure (VI-0), historical irreversibility (III-0), protected-area interface (RM-0) — that exceeds
the elevated classification threshold despite lower aggregate scores.

---

## 5. Key Findings

### 5.1 Chile's relaves crisis is primarily a legacy problem

Of the 836 deposits in the national catastro, approximately **455 are classified as abandoned** —
mines that ceased operation without completing closure plans, without implementing geotechnical
rehabilitation, and in most cases without establishing any financial closure bond. The six analysed
clusters account for 326 of these 455 abandoned deposits (72% concentration). This is not a
problem being created by current production; it is a problem inherited from mining activity
spanning the period 1880–2000, when tailings disposal regulation either did not exist or was not
enforced.

DS 248/2021 is the first legal instrument that requires systematic inventory, risk classification,
and closure planning for abandoned deposits. However, the law's implementation is constrained by:

1. Sernageomin's institutional capacity (approximately 180 inspection engineers nationwide) being
   insufficient to process 455+ abandoned deposit classifications within the law's five-year
   timeline.
2. The absence of a dedicated state remediation fund (Fondo de Cierre Minero) with adequate
   capitalisation. The current fund has authorised capital of approximately USD 200 million, which
   is insufficient for the scale of remediation required in Region III alone.
3. Legal ambiguity about successor liability for abandoned deposits where the original operating
   entity no longer exists.

The **production forecasts through 2032 do not reduce this legacy**. Even as output from the
modelled 26 mines declines from a combined ~4,500 kt/yr to ~3,900 kt/yr, the 455 abandoned
deposits continue to generate acid drainage, wind-blown dust, and geotechnical risk entirely
independently of whether any active copper mine is operating.

### 5.2 The "small victory" of declining production

There is one genuinely positive environmental signal in the production forecasts. For clusters
where the forecast shows declining output — principally VI-0 (El Teniente), II-2 (Calama complex),
and III-0 (Salvador) — the rate of **new tailings accumulation** decreases proportionally.

Assuming an average copper recovery of 88% from a combined concentrate-and-SX-EW process, each
tonne of copper cathode/concentrate produced generates approximately 100–130 tonnes of tailings
(depending on ore grade). A production decline of 600 kt/yr across the modelled portfolio from
2024 to 2032 corresponds to a reduction in new tailings generation of approximately **60–80
million tonnes per year** by 2032 relative to the 2024 baseline.

This is meaningful from a TSF expansion velocity standpoint: active TSFs that were projected to
require new cell construction in 2028–2030 under stable production scenarios may now have
sufficient current capacity to absorb declining production without expensive expansion projects.
This reduces capital expenditure requirements and, importantly, reduces the footprint of new
geotechnical infrastructure being added to already-stressed cluster environments.

However, this small victory does not reduce the closure liability associated with existing stored
volumes. A TSF that holds 2.0 billion tonnes of tailings requires essentially the same perpetual
maintenance and monitoring as one that holds 2.1 billion tonnes.

### 5.3 The protected-areas interface as a binding constraint on expansion

For three of the six clusters — VI-0 (21 km from Río Los Cipreses), RM-0 (15 km from Yerba Loca),
and IV-2 (46 km from Las Chinchillas) — the proximity of SNASPE units represents a hard
constraint on any future expansion that requires new tailings footprint. Chile's SEA environmental
assessment process requires a Biodiversity Addendum for projects within 30 km of a protected area,
and the Yerba Loca and Río Los Cipreses interfaces in particular have demonstrated capacity to
generate legal challenges that delay or block new RCA permits (see the Los Bronces Integrated
Project history and Codelco Andina Phase IV record).

The production forecasts do not explicitly incorporate permitting risk. The base scenario assumes
operations continue at model-predicted volumes. Any scenario in which expansion is blocked by
protected-area litigation would likely produce an earlier and steeper production decline than the
base forecast, particularly for Los Bronces (RM-0) where the next decade of mine plan depends on
accessing deeper ore bodies that require new surface infrastructure.

### 5.4 Copiapó as a national regulatory priority

The 102 PELIGRO deposits in Cluster III-2, concentrated in a valley of 162,000 people with a
documented history of flood-driven tailings mobilisation, constitute the single highest-priority
environmental risk issue in Chilean copper mining as measured by the dashboard metrics. No other
cluster in the national dataset approaches this proximity density. The combination of active
Candelaria and Caserones operations (stable forecast, continuing to add tailings), 60 abandoned
deposits, and documented climate risk from convective rainfall intensification makes this cluster
the most urgent candidate for a comprehensive, Sernageomin-led proximity risk audit under the
DS 248/2021 classification framework.

---

## 6. Suggested Next Steps

### 6.1 Quantitative composite risk scores for production forecasting integration

The ERS matrix developed in this report uses ordinal normalisation. A statistically rigorous
version would assign each cluster a continuous risk score incorporating:

- Geotechnical failure probability (from Sernageomin stability classifications, where available)
- Population-weighted exposure (integration of INE census grid with flood-path modelling)
- Protected-area hydrological connectivity (flow-path analysis, not straight-line distance)
- DS 248/2021 compliance gap (fraction of deposits unclassified)

This score could be incorporated into the production forecast as a regulatory risk discount factor:
mines in CRITICAL clusters would carry a higher probability of unplanned production interruption
from regulatory intervention, effectively widening forecast confidence intervals.

### 6.2 Closure bond adequacy assessment

The DS 248/2021 framework requires operators to post closure bonds proportional to estimated
remediation costs. Current bond requirements are calculated using Sernageomin's standard
cost-per-hectare tariff schedule, which was last updated in 2019. Given inflation in civil
engineering and earthworks costs since 2019 (approximately 35% cumulative in Chile as of 2026),
the real value of existing bonds may be materially insufficient. A recalculation using 2026
construction costs for the six cluster TSFs would provide a regulatory gap estimate directly
relevant to Codelco's and Anglo American's balance sheet planning.

### 6.3 DS 248/2021 compliance timeline mapping

A cluster-by-cluster compliance status map — linking each of the 326 abandoned deposits analysed
here to their current classification status in Sernageomin's system — would convert the
aggregate statistics in this report into an actionable audit tool. The key output would be a
ranked list of unclassified PELIGRO deposits, prioritised for emergency baseline surveys. This
work is technically feasible using the Catastro Nacional de Relaves public API and would represent
a two-month research project.

### 6.4 Chañaral long-term monitoring integration

The Chañaral Bay contamination (316 Mt discharged 1938–1990) represents a natural experiment in
passive tailings dispersion over decadal timescales. The Universidad de Atacama's ongoing sediment
monitoring programme (2015–present) provides a time series that could be used to parameterise
dispersion models for other coastal-adjacent tailings scenarios in Clusters III-2 and IV-2. This
would improve the physical hazard component of future ERS calculations and provide empirical
calibration for transport models required under DS 248/2021's emergency action plans.

### 6.5 Protected-area permitting risk as a forecast scenario

The production forecasting model currently uses three Cu price scenarios (bear/base/bull) to
generate projection ranges. A fourth scenario dimension — permitting delay — would be particularly
relevant for RM-0 (Los Bronces Integrated Project) and potentially IV-2 and VI-0. Incorporating
permitting risk into scenario construction would require coordination with SEA's public
administrative record and could substantially improve the external validity of the H+5 to H+7
forecasts for mines in protected-area proximity zones.

---

## 7. Conclusions

The environmental risk profile of Chilean copper mining is defined by a fundamental asymmetry:
production activity is bounded in time, but environmental liability is (in practice) permanent.
The 455 abandoned deposits in the national catastro were created by mines that ceased operation
decades ago, yet they continue to generate acid drainage, dust, and geotechnical risk that is
independent of current production decisions.

The six clusters analysed here concentrate 326 of these abandoned deposits and between them
expose populations totalling over 600,000 people to first-order proximity risk. Cluster III-2
(Copiapó) stands apart as a CRITICAL priority: 102 PELIGRO deposits near a city of 162,000,
in a valley with documented flood-driven tailings mobilisation and a projected increase in
convective precipitation frequency, constitute a regulatory and public safety emergency that
has not been fully absorbed into operational risk pricing by the sector.

The production forecasts from model v7 (Ens_Segmentado) deliver a modest but genuine positive
signal: declining output across most clusters will reduce the annual rate of new tailings
accumulation by 60–80 million tonnes per year relative to 2024 by the early 2030s. This reduces
TSF expansion pressure and marginally improves the ratio of active-management resources to
active-generation volume. It does not, however, reduce closure liability, alter the condition of
existing abandoned deposits, or change the physical geography of a bay in Chañaral that received
316 million tonnes of tailings over 52 years.

The most important analytical gap between the current dashboard and a fully integrated
environmental risk assessment is the absence of dynamic failure-probability modelling: straight-line
distance to a protected area or to a city is a useful first filter but is not a substitute for
flow-path analysis, geotechnical stability classification, and population-weighted consequence
assessment. DS 248/2021 provides the regulatory mandate and the data collection framework to
close this gap; the research priority is to link Sernageomin's classification output to
mine-level production forecasts, so that regulatory risk becomes an endogenous input to the
forecasting model rather than an external caveat.

---

*Report prepared March 2026. Data sources: Catastro Nacional de Relaves (Sernageomin, 836
deposits); SNASPE protected-area polygon layer (CONAF 2024); INE Census 2017 population grid;
DS 248/2021 (Ministerio de Minería); annual production model v7 Ens_Segmentado (rolling-origin
validation 2010–2018, Modelo_Anual_FinalV1.ipynb). All proximity distances computed as
straight-line (Haversine) in the mining_clusters_v2 dashboard unless otherwise noted.*
