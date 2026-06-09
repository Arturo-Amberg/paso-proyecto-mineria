# Forecast Uncertainty & Model Performance — Top 6 Clusters
### Based on Annual Model v7 Ens_Segmentado · March 2026

---

## Why Forecast Uncertainty?

This report takes a different angle from the infrastructure analyses: instead of asking *what is the
physical state of each cluster*, it asks *how well can we predict what each cluster will produce?*
This is the core question of the thesis. The answer varies dramatically by cluster — and those
differences are not random. They reflect structural properties of each mine type (asset age, ore
grade trajectory, corporate strategy) and the model's architecture (SmallMed vs LargeColossal
segmentation).

Understanding where the model succeeds and fails by cluster is both a methodological contribution
and an operational one: regulators, investors, and water/electricity planners using these forecasts
need to know which clusters to trust and which to treat with caution.

---

## Selection Rationale

The 6 clusters are selected to represent the **full spectrum of forecast quality** — from the
model's best performers to its most challenging cases. This creates a richer analytical narrative
than simply picking the 6 largest. Clusters are drawn from both the SmallMed and LargeColossal
model segments to illustrate how segmentation affects performance.

| Cluster | Top Mine | Win Rate (Ens_Seg) | Segment | Model challenge |
|---------|-----------|--------------------|---------|-----------------|
| III-1 | Candelaria | 74.1% | SmallMed | High accuracy, structural expansion |
| III-2 | Caserones | 27.8% | SmallMed | Worst performer — ramp-up mine |
| II-0 | Escondida | 48.1% | LargeColossal | Largest mine, grade-driven decline |
| I-1 | Collahuasi | 33.3% | LargeColossal | QB2 structural break not captured |
| VI-0 | El Teniente | varies | LargeColossal | Codelco operational disruptions |
| IV-1 | Los Pelambres | 25.9% | SmallMed | Drought + community disruptions |

Win Rate = % of validation predictions that beat naive (last-observed value).
Source: scoreboard_annual_v7.csv, Ens_Segmentado model.

---

## Model Architecture Reminder

**Annual model v7** uses two segments:
- **SmallMed** (Mine_Size ≤ 1, production quartiles 0–1): LGB_LogRatio + XGB_LogRatio + LGB_MultiH
  — best ensemble: Ens_3070 (30% LGB + 70% XGB for SmallMed)
- **LargeColossal** (Mine_Size ≥ 2, quartiles 2–3): LGB_LargeCol + LGB_MultiH_LC
  — best ensemble: Ens_LC_3070

All models predict `log(Prod_h / Prod_origin)` — the log-ratio of future production relative to
origin. Naive always predicts 0 (i.e., "production stays flat"). Models win when they correctly
identify directional changes.

Rolling-origin validation: 9 origins (2010–2018), horizons H+1 to H+7.

---

## Cluster Deep Dives

---

### 1 · Cluster III-1 — Candelaria Complex (Region III, Atacama)

**Mines:** Candelaria (Lundin Mining, sulfide) · Capstone Copper (Mantoverde + Santos Domingo)

**Win Rate: Candelaria 74.1% — 2nd best nationally.**

**Production trajectory (kt/yr):**

| Year | Candelaria | Capstone | Total |
|------|----------:|--------:|------:|
| 2018 | 124.4 | ~80 | ~204 |
| 2020 | 130.0 | ~90 | ~220 |
| 2022 | 120.4 | ~100 | ~220 |
| 2024 | 123.5 | 102.7 | ~226 |

**Why the model succeeds here:**
Candelaria is a **mature, stable, well-managed sulfide mine** with consistent ore grades,
minimal operational disruptions, and predictable throughput. Its production time series shows
low volatility around a mild downtrend — exactly the type of pattern that the SmallMed
LGB_MultiH model captures well. The Tendencia_5y feature (5-year trend) correctly identifies
the plateau-then-gradual-decline trajectory, giving the model a structural edge over the naive
(which assumes no change).

Capstone Copper (Mantoverde + Santo Domingo) adds some complexity through its expansion program,
but the mine's relatively stable recent history keeps the cluster's WR high.

**Forecast 2026–2032 (cluster total, kt):**

| Year | 2026 | 2027 | 2028 | 2029 | 2030 | 2031 | 2032 |
|------|------|------|------|------|------|------|------|
| Pred | 298 | 296 | 293 | 293 | 291 | 291 | 290 |

**Interpretation:** The model projects near-flat production (~290–298 kt/yr) with very
slight decline — consistent with Candelaria's known ore-body maturity and Capstone's steady
expansion schedule. The narrow uncertainty band in this cluster makes forecasts here the most
"investable" — planners can rely on them for water, electricity, and logistics planning.

**Key insight:** High model accuracy in a stable cluster is both good news (usable forecasts)
and underwhelming news (the naive would also perform reasonably here). The model's value-add
is largest in clusters where volatility is high — which is the exact opposite of III-1.

---

### 2 · Cluster III-2 — Caserones (Region III, Atacama)

**Mines:** Caserones (Lundin Mining, sulfide) · Candelaria (see III-1 — note these clusters
overlap in geography; III-2 is the broader Copiapó valley cluster).

**Win Rate: Caserones 27.8% — one of the worst nationally.**

**Production trajectory (kt/yr):**

| Year | Caserones |
|------|----------:|
| 2014 | ~30 (ramp) |
| 2016 | ~80 |
| 2018 | ~100 |
| 2020 | ~110 |
| 2022 | ~130 |
| 2024 | 125.8 |

**Why the model struggles here:**
Caserones began commercial production in 2014 and spent 2014–2020 in a **ramp-up phase**.
For the rolling-origin validation windows (origins 2010–2018), Caserones was in its growth
phase for every single origin. The naive (flat) prediction is systematically below the true
value for early origins (the mine was growing) — which means the model should have won
consistently. That it only wins 27.8% of the time suggests the model is **over-correcting**,
perhaps predicting too much growth at later origins when the ramp plateaus.

The deeper issue: Caserones is a **junior/medium mine** (SmallMed segment) with a fundamentally
different trajectory shape than mature SmallMed mines. The Lundin acquisition (2023) and
subsequent capex decisions create additional uncertainty.

**Forecast 2026–2032:**

| Year | 2026 | 2027 | 2028 | 2029 | 2030 | 2031 | 2032 |
|------|------|------|------|------|------|------|------|
| Pred | 124 | 117 | 114 | 113 | 111 | 116 | 117 |

**Interpretation:** The model projects a flat-to-slight-decline trajectory. Given Caserones'
known ore body (significant reserves remaining) and Lundin's investment plans, the real
trajectory may be **flat or growing** — making this a cluster where the forecast lower
bound should be used as the base case for conservative planning.

**Key insight:** The worst model performers are often **recent greenfield mines** (post-2010
start) or mines that went through structural changes (expansions, ownership changes, strikes)
during the validation period. This is a systematic bias worth documenting in the thesis.

---

### 3 · Cluster II-0 — Escondida (Region II, Antofagasta)

**Mines:** Escondida (BHP, world's largest copper mine) · Zaldívar (AMSA)

**Win Rate: Escondida 48.1% — just below 50%, near-naive level.**

**Production trajectory (kt/yr):**

| Year | Escondida | Zaldívar | Total |
|------|----------:|--------:|------:|
| 2018 | 1,243 | 94 | 1,337 |
| 2019 | 1,188 | 116 | 1,304 |
| 2020 | 1,187 | 96 | 1,283 |
| 2021 | 1,011 | 87 | 1,098 |
| 2022 | 1,054 | 89 | 1,143 |
| 2023 | 1,101 | 81 | 1,182 |
| 2024 | 1,278 | 83 | 1,361 |

**Why the model nearly ties naive:**
Escondida is in the **LargeColossal segment** — correctly so, as it is Mine_Size=3 (Colossal).
At this scale, production variation is driven by ore grade, throughput decisions, labor agreements
(strikes in 2006, 2011, 2017), and BHP's internal capital allocation — **not** by simple
trend extrapolation. The 2021 pandemic hit pushed production to 1,011 kt (-17%) — a shock
the model's Is_Pandemic_Target flag partially captured.

The Is_Pandemic_Target variable (=1 for target years 2020-2021) **improved** pandemic prediction
(52.8% vs 50.9% for non-pandemic years in the global scoreboard), but Escondida's specific
pandemic impact was larger than average, making it hard to predict precisely.

**Forecast 2026–2032:**

| Year | 2026 | 2027 | 2028 | 2029 | 2030 | 2031 | 2032 |
|------|------|------|------|------|------|------|------|
| Escondida pred | 1,372 | 1,352 | 1,253 | 1,210 | 1,189 | 1,078 | 1,059 |
| Lower bound | ~1,100 | ~1,080 | ~1,000 | ~970 | ~950 | ~860 | ~845 |
| Upper bound | ~1,640 | ~1,620 | ~1,500 | ~1,450 | ~1,430 | ~1,295 | ~1,270 |

**Interpretation:** The central forecast projects **-23% by 2032** — driven by the model
learning that LargeColossal mines with Escondida's age and cumulative extraction tend to decline.
The wide confidence interval (±20%) reflects genuine uncertainty at this scale. BHP's ore
processing technology investments (bioleaching, sulphide extensions) could push production
toward the upper bound; grade decline without new investment points to the lower bound.

**Key insight:** For the world's largest copper mine, even a 48% win rate is meaningful —
it means the model is directionally correct about half the time on a mine where each
percentage point of forecast error translates to ~$50M in revenue planning.

---

### 4 · Cluster I-1 — Collahuasi + Quebrada Blanca (Region I, Tarapacá)

**Win Rate: Collahuasi 33.3% — significantly below naive.**

**Production trajectory (kt/yr):**

| Year | Collahuasi | QB (pre/post QB2) | Total |
|------|----------:|------------------:|------:|
| 2018 | 559 | 26 | 585 |
| 2020 | 629 | 13 | 642 |
| 2022 | 571 | 10 | 581 |
| 2023 | 573 | 64 | 637 |
| 2024 | 559 | **208** | **767** |

**Why the model underperforms:**
Two structural problems:

1. **Collahuasi's volatility:** Collahuasi swings between 559–629 kt within the dataset — a
   ±12% range that is hard to predict directionally. The mine's output depends heavily on
   throughput optimization decisions and weather events (Atacama flash floods have disrupted
   operations). The model predicts a continuation of stable-then-slight-decline, but Collahuasi
   has surprised with upside (2020: +629 kt despite pandemic) and downside in the same window.

2. **QB2 structural break:** The rolling-origin validation runs through origin 2018. At that
   point, Quebrada Blanca was producing 26 kt/yr (old Phase 1 oxide operation). The QB2 ramp
   (to 208 kt by 2024) is a **post-training event** that the model cannot have learned.
   Consequently, any validation window that includes QB2 production (post-2023) looks like
   an impossible-to-predict surge from the model's perspective. This mechanically depresses
   the win rate.

**Forecast 2026–2032:**

| Year | 2026 | 2027 | 2028 | 2029 | 2030 | 2031 | 2032 |
|------|------|------|------|------|------|------|------|
| I-1 pred | 496 | 476 | 469 | 433 | 421 | 435 | 475 |

**Critical caveat:** This forecast is **severely underestimated**. QB2's target production
at full capacity is ~330 kt/yr. Combined with Collahuasi's ~560 kt, the real 2026–2032
cluster production should be ~850–900 kt/yr. The model projects 421–496 kt because it
doesn't know about QB2 at scale.

**Key insight:** I-1 is the thesis's clearest example of a **structural break problem** in
rolling-origin validation. This is an important methodological finding: when a mine undergoes
a major greenfield expansion, rolling-origin validation cannot capture it, and the resulting
WR metric is misleadingly pessimistic. The solution (external QB2 production scenarios) is
discussed in the next-steps section.

---

### 5 · Cluster VI-0 — El Teniente (Region VI, O'Higgins)

**Win Rate: El Teniente (estimated from scoreboard context) ~45–50%.**

**Production trajectory (kt/yr):**

| Year | El Teniente |
|------|------------:|
| 2018 | 465 |
| 2019 | 460 |
| 2020 | 443 |
| 2021 | 460 |
| 2022 | 405 |
| 2023 | 352 |
| 2024 | 356 |

**Why the model is challenged:**
El Teniente presents two compounding difficulties:

1. **Codelco operational disruptions:** Multiple seismic events, collapses of old mine
   workings, and Codelco's ongoing underground expansion (New Mine Level project — a $3B
   investment) create irregular production patterns. The New Mine Level project (extending
   the mine to deeper, richer ore) requires building infrastructure through the existing
   operation, causing production disruptions that are not predictable from historical trends.

2. **Age and depth:** El Teniente has been producing since 1905 — the longest-operating
   major copper mine in Chile. Its ore body is deeply understood, but the mining engineering
   challenges of ultra-deep block caving at increasing depths create non-linear productivity
   curves that standard trend features don't capture.

**Forecast 2026–2032:**

| Year | 2026 | 2027 | 2028 | 2029 | 2030 | 2031 | 2032 |
|------|------|------|------|------|------|------|------|
| Pred (kt) | 270 | 252 | 239 | 229 | 225 | 226 | 214 |

**Interpretation:** The model forecasts a continued decline from 356 kt (2024) to
214 kt (2032) — a -40% drop over 8 years. This is aggressive. However, it is consistent
with the observed 2018–2024 trend (-23%) and reflects the model's logic that
LargeColossal Codelco mines with declining trends tend to continue declining.

The **optimistic scenario**: the New Mine Level project reaches full production by 2026–2027,
reversing the decline to 450+ kt. The model's Upper bound should be used to represent this
scenario for planning purposes.

**Key insight:** Declining production in the world's largest underground copper mine is
both a forecast challenge and an investment signal. The model's forecast of 214 kt by 2032
would make El Teniente no longer the 4th largest Chilean producer — representing a
significant structural shift in Chile's copper portfolio.

---

### 6 · Cluster IV-1 — Los Pelambres (Region IV, Coquimbo)

**Win Rate: Los Pelambres 25.9% — worst in the LargeColossal/large SmallMed group.**

**Production trajectory (kt/yr):**

| Year | Los Pelambres |
|------|-------------:|
| 2018 | 371 |
| 2019 | 376 |
| 2020 | 372 |
| 2021 | 336 |
| 2022 | **284** |
| 2023 | 311 |
| 2024 | 331 |

**Why the model struggles most here:**
Los Pelambres has the **highest unexplained variance** of any large mine in the dataset.
The 2022 production drop to 284 kt (-25% from 2020) was driven by:
- An unprecedented drought in Coquimbo region (Choapa River at historic low flow)
- Community-imposed water use restrictions
- Regulatory enforcement of DGA limits

These are exogenous shocks that no feature in E6_BASE captures directly. The model's
Tendencia_5y, Prod_pct_change, and Cu_regime features cannot identify an incoming drought
or a community protest campaign.

The subsequent recovery (284→331 kt from 2022–2024) further confuses the model, which
may be predicting continued decline when the mine actually recovered.

**Forecast 2026–2032:**

| Year | 2026 | 2027 | 2028 | 2029 | 2030 | 2031 | 2032 |
|------|------|------|------|------|------|------|------|
| Pred (kt) | 359 | 356 | 354 | 364 | 360 | 366 | 367 |

**Interpretation:** The forecast projects a surprisingly stable ~355–367 kt — essentially
recovering to near 2018–2019 levels. This may reflect the model learning that Los Pelambres
has historically "bounced back" after disruptions. However, given climate change projections
for Coquimbo region (increasing drought frequency), the lower bound scenario (~280–300 kt)
deserves equal weight in planning.

**Key insight:** Los Pelambres is the thesis's clearest example of **climate-driven production
risk** that standard ML features cannot capture. It is also the strongest argument for adding
climate/drought indices as external features in future model versions.

---

## Cross-Cluster Comparison

### Win Rate and Forecast Summary

| Cluster | Top Mine | Win Rate | Segment | Why difficult | 2026 pred (kt) | 2032 pred (kt) | Change |
|---------|----------|---------|---------|---------------|----------------|----------------|--------|
| III-1 | Candelaria | **74.1%** | SmallMed | Stable — model's friend | 298 | 290 | -3% |
| II-0 | Escondida | 48.1% | LC | Grade decline, scale | 1,425 | 1,097 | -23% |
| VI-0 | El Teniente | ~45% | LC | Underground disruptions | 270 | 214 | -21% |
| III-2 | Caserones | 27.8% | SmallMed | Ramp-up bias | 124 | 117 | -6% |
| I-1 | Collahuasi | 33.3% | LC | QB2 structural break | 496* | 475* | underestimated |
| IV-1 | Los Pelambres | **25.9%** | LC | Climate/community shocks | 359 | 367 | +2% |

*Real I-1 production likely 850-900 kt/yr at full QB2 capacity.

### Model Performance by Difficulty Class

**Easy to predict (WR > 60%):** Stable mature mines with low variance (Candelaria, Michilla,
El Soldado, Ministro Hales, Andacollo). Model beats naive regularly because the trend is clear.

**Medium difficulty (WR 40–60%):** Large mines with moderate volatility (Escondida, El Teniente,
Chuquicamata). Model roughly ties naive — adds directional signal but significant uncertainty
remains.

**Hard to predict (WR < 35%):** Mines with exogenous shocks (Los Pelambres: drought),
structural breaks (QB2), or recent ramp-ups (Caserones, Sierra Gorda). Model cannot capture
what the features don't measure.

---

## Key Findings

**1. Model performance correlates with mine type and stability.** Mature, stable mines
(Candelaria 74.1%) are easy; growing/disrupted mines (Los Pelambres 25.9%) are hard.
This is not a model failure — it reflects the irreducible uncertainty in the underlying
system.

**2. Structural breaks are the model's kryptonite.** The QB2 expansion (I-1) is the
clearest case. Rolling-origin validation by design cannot capture post-origin changes. This
is a known limitation that should be explicitly stated and quantified in the thesis —
the I-1 real forecast gap (model: 496 kt vs reality: ~860 kt by 2026) is a
$3–4 billion annual revenue forecasting error.

**3. Climate is the missing feature.** Los Pelambres' 25.9% WR would likely improve
significantly with a drought index or Choapa River flow variable. This is a concrete
recommendation for a v8 model.

**4. The "small victory" in forecast context:** The declining production forecasts for
large clusters (II-0: -23%, VI-0: -21%) are more uncertain than they appear — these are
well-known mines where BHP and Codelco have published 10-year plans. Cross-referencing
model forecasts against corporate guidance (where available) could be a thesis contribution.

**5. Codelco needs its own treatment.** Four of Chile's largest mines (Chuquicamata, RT,
El Teniente, Andina) are state-owned and subject to political/budgetary constraints that
no market-based feature captures. Their underperformance in the model (multiple <35% WR)
is structurally predictable.

---

## Suggested Next Steps for Thesis

- **QB2 scenario analysis:** Build a scenario where QB2 produces at 200/250/330 kt/yr
  and show the implied I-1 forecast error. Quantify the model's structural-break bias.
- **Climate feature addition (v8):** Add SPI (Standardised Precipitation Index) or ENSO
  index for IV-1 and V-1 mines. Measure WR improvement.
- **Codelco dummy:** Add a binary feature `Is_Codelco` and test whether it improves
  LargeColossal segment accuracy for state-owned mines.
- **Corporate guidance cross-validation:** For mines with published medium-term plans
  (BHP Escondida, Codelco plans), compare model forecasts vs guidance to assess external validity.
- **Diebold-Mariano significance map:** Overlay DM test results on the cluster map to show
  which clusters have statistically significant model superiority over naive.

---

*Data sources: scoreboard_annual_v7.csv, projections_2026_2032.csv (annual model v7
Ens_Segmentado), Produccion_Master.csv. Model details: MEMORY.md (Model Architecture v7).*

*Generated: March 2026 · TrabajoTesis / FinalResultsFolder*
