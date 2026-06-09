"""
generate_projections_v33.py
───────────────────────────
Generates monthly projections 2026-2032 using the v33 model architecture:
  - RF + RollingMean ensemble (direct multi-horizon)
  - SM: α_short(H≤12)=0.3, α_mid(H=18)=0.6, α_long(H≥24)=0.9
  - LC: α=0.5
  - Train on all available data up to projection origin (2025-12-01)
  - Confidence intervals derived from rolling-origin validation errors

Output: outputs_best/projections_monthly_2026_2032.csv
"""

import os, math, warnings
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

warnings.filterwarnings("ignore")

# ─── Paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
BASE_DIR     = os.path.join(SCRIPT_DIR, "..", "..")
MASTER_PATH  = os.path.join(BASE_DIR, "01_Data", "processed", "1_master_thesis_data.csv")
META_PATH    = os.path.join(BASE_DIR, "01_Data", "processed", "metadata_minas.csv")
STOCK_PATH   = os.path.join(BASE_DIR, "01_Data", "processed", "owner_stock_prices.csv")
VAL_PREDS    = os.path.join(SCRIPT_DIR, "outputs_best", "all_predictions_monthly_v33.csv")
OUT_PATH     = os.path.join(SCRIPT_DIR, "outputs_best", "projections_monthly_2026_2032.csv")

# ─── Configuration ────────────────────────────────────────────────────────────
PROJECTION_ORIGIN = pd.Timestamp("2025-12-01")
HORIZONS = [1, 3, 6, 9, 12, 18, 24, 30, 36, 42, 48, 54, 60, 72, 84]

H_SHORT = {1, 3, 6, 9, 12}
H_MID   = {18}
# H_LONG  = everything else

ALPHA_SM_SHORT = 0.3
ALPHA_SM_MID   = 0.6
ALPHA_SM_LONG  = 0.9
ALPHA_LC       = 0.5

RF_PARAMS = dict(n_estimators=400, max_depth=12, min_samples_leaf=3,
                 max_features=0.5, n_jobs=-1, random_state=42)

EXCLUDE_MINES = {
    "haldeman", "altos de punitaqui", "tres valles",
    "pampa camarones", "michilla", "quebrada blanca", "spence", "cerro negro"
}

PANDEMIC_START  = pd.Timestamp("2020-03-01")
PANDEMIC_END    = pd.Timestamp("2021-12-31")
RECOVERY_START  = pd.Timestamp("2022-01-01")
RECOVERY_END    = pd.Timestamp("2023-12-31")

COMPANY_SIZE_MAP = {
    "escondida": 2, "chuquicamata": 2, "el teniente": 2, "andina": 2,
    "radomiro tomic": 2, "salvador": 2, "ministro hales": 2,
    "gabriela mistral": 2, "collahuasi": 2, "los bronces": 2,
    "lomas bayas": 2, "cerro colorado": 2, "el abra": 2,
    "los pelambres": 1, "centinela": 1, "centinela_oxidos": 1,
    "centinela_sulfuros": 1, "zaldivar": 1, "antucoya": 1, "andacollo": 1,
    "candelaria": 1, "caserones": 1, "sierra gorda": 1, "mantoverde": 1,
    "mantos blancos": 1, "ojos del salado": 1,
    "atacama kozan": 0, "franke": 0, "el soldado": 0, "otros": 0,
}

SIZE_LABELS = {0: "Small", 1: "Medium", 2: "Large", 3: "Colossal"}

# ─── 1. Load Data ─────────────────────────────────────────────────────────────
print("📂 Loading data...")
df_raw = pd.read_csv(MASTER_PATH)
df_raw["Date"]      = pd.to_datetime(df_raw["Date"])
df_raw["Match_Key"] = df_raw["Match_Key"].str.lower().str.strip()
if "Inversión (MMU$)" in df_raw.columns:
    df_raw.rename(columns={"Inversión (MMU$)": "Inversion"}, inplace=True)

# Fix centinela split
df_raw.loc[df_raw["Mine"].str.contains("xido",  na=False), "Match_Key"] = "centinela_oxidos"
df_raw.loc[df_raw["Mine"].str.contains("lfuro", na=False), "Match_Key"] = "centinela_sulfuros"

df_raw["Production"]    = df_raw["Production"].fillna(0).clip(lower=0)
df_raw["Capital_Stock"] = df_raw["Capital_Stock"].fillna(0)
df_raw["Inv_Lag_48"]    = df_raw["Inv_Lag_48"].fillna(0)
df_raw["Has_Desal"]     = df_raw["Has_Desal"].fillna(0)
df_raw["Has_Energy"]    = df_raw["Has_Energy"].fillna(0)
df_raw["Cu_Price"]      = df_raw["Cu_Price"].ffill()
df_raw = df_raw[~df_raw["Match_Key"].isin(EXCLUDE_MINES)].reset_index(drop=True)
df_raw = df_raw.sort_values(["Match_Key", "Date"]).reset_index(drop=True)
df_raw = df_raw[df_raw["Date"] <= PROJECTION_ORIGIN]

MINES = sorted(df_raw["Match_Key"].unique().tolist())
print(f"   {len(MINES)} mines, data up to {PROJECTION_ORIGIN.date()}")

# ─── Load auxiliary data ──────────────────────────────────────────────────────
# Mine metadata (Is_Oxide from Type column)
is_oxide_map = {}
try:
    meta = pd.read_csv(META_PATH)
    meta["Mine_key"] = meta["Mine"].str.lower().str.strip()
    for _, row in meta.iterrows():
        mk = row["Mine_key"]
        is_oxide_map[mk] = 1 if "xido" in str(row.get("Type", "")).lower() else 0
except Exception as e:
    print(f"   ⚠ Metadata not loaded: {e}")

# Owner stock price → Stock_Level_Lag3 (log-normalized closing price, 3m lag)
owner_stock_map = {}  # mine_key → pd.Series indexed by Date
OWNER_TICKER_MAP = {
    "bhp": ["escondida", "spence", "cerro colorado"],
    "glencore": ["collahuasi", "lomas bayas"],
    "anglo american": ["los bronces", "el soldado"],
    "freeport": ["el abra"],
    "antofagasta": ["los pelambres", "zaldivar", "antucoya", "centinela_oxidos",
                    "centinela_sulfuros", "mantoverde", "mantos blancos"],
    "codelco": ["chuquicamata", "el teniente", "andina", "radomiro tomic",
                "salvador", "ministro hales", "gabriela mistral"],
}
TICKER_MAP = {
    "bhp": "BHP", "glencore": "GLEN.L", "anglo american": "AAL.L",
    "freeport": "FCX", "antofagasta": "ANTO.L", "codelco": None,
}
try:
    stocks = pd.read_csv(STOCK_PATH)
    stocks["Date"] = pd.to_datetime(stocks["Date"])
    for owner, mines in OWNER_TICKER_MAP.items():
        ticker = TICKER_MAP.get(owner)
        if ticker is None:
            continue
        s = stocks[stocks["Ticker"] == ticker].sort_values("Date").set_index("Date")["Close"]
        if len(s) == 0:
            continue
        s_log = np.log(s + 1e-6)
        s_norm = (s_log - s_log.mean()) / (s_log.std() + 1e-9)
        for mine in mines:
            owner_stock_map[mine] = s_norm
except Exception as e:
    print(f"   ⚠ Stock prices not loaded: {e}")

# Reserve life (static approximation from mine start year + typical reserve life)
# These are approximate — used as a feature, not a key driver
RESERVE_LIFE_MAP = {
    "escondida": 45, "chuquicamata": 35, "el teniente": 50, "andina": 40,
    "radomiro tomic": 20, "collahuasi": 50, "los pelambres": 30, "candelaria": 15,
    "antucoya": 20, "zaldivar": 20, "andacollo": 15, "caserones": 30,
    "sierra gorda": 35, "centinela_oxidos": 15, "centinela_sulfuros": 25,
    "mantos blancos": 20, "mantoverde": 25, "el abra": 15, "lomas bayas": 10,
    "cerro colorado": 10, "ojos del salado": 20, "ministro hales": 20,
    "gabriela mistral": 15, "salvador": 15, "los bronces": 25, "atacama kozan": 5,
    "franke": 5, "el soldado": 10, "otros": 15,
}

print("   Auxiliary data loaded ✓")

# ─── 2. Mine Size at Projection Origin ────────────────────────────────────────
def compute_mine_size(df, origin_date):
    end   = origin_date - pd.DateOffset(months=1)
    start = origin_date - pd.DateOffset(months=13)
    avgs  = {}
    for m in MINES:
        sub = df[(df["Match_Key"] == m) & (df["Date"] >= start) & (df["Date"] <= end)]
        avgs[m] = float(sub["Production"].mean()) if len(sub) > 0 else 0.0
    vals = [v for v in avgs.values() if v > 0]
    if not vals:
        return {m: 0 for m in MINES}
    q25, q50, q75 = np.percentile(vals, 25), np.percentile(vals, 50), np.percentile(vals, 75)
    return {m: (0 if v <= q25 else 1 if v <= q50 else 2 if v <= q75 else 3)
            for m, v in avgs.items()}

ms_map = compute_mine_size(df_raw, PROJECTION_ORIGIN)
print(f"   Mine sizes computed: {dict(list(ms_map.items())[:5])} ...")

# ─── 3. Feature Engineering ───────────────────────────────────────────────────
def get_stock_level_lag3(mine, date):
    s = owner_stock_map.get(mine)
    if s is None:
        return 0.0
    lag_date = date - pd.DateOffset(months=3)
    # Find closest available date
    valid = s.index[s.index <= lag_date]
    if len(valid) == 0:
        return 0.0
    return float(s[valid[-1]])

def build_features_at_origin(df, ms_map, origin_date):
    df = df[df["Date"] <= origin_date].copy().sort_values(["Match_Key", "Date"])
    g  = df.groupby("Match_Key")

    df["Prod_Lag1"]  = g["Production"].shift(1)
    df["Prod_Lag12"] = g["Production"].shift(12)
    df["Prod_MA12"]  = g["Production"].transform(
        lambda x: x.shift(1).rolling(12, min_periods=3).mean())
    df["Tendencia_12m"] = g["Production"].transform(
        lambda x: x.shift(1).rolling(12, min_periods=6).apply(
            lambda v: np.polyfit(range(len(v)), v, 1)[0] if len(v) >= 6 else 0, raw=True))
    df["Mine_trend_slope_36m"] = g["Production"].transform(
        lambda x: x.shift(1).rolling(36, min_periods=12).apply(
            lambda v: np.polyfit(range(len(v)), v, 1)[0] if len(v) >= 12 else 0, raw=True))
    df["Prod_pct_change_m"]   = g["Production"].pct_change(1).fillna(0).clip(-2, 2)
    df["Prod_pct_change_36m"] = g["Production"].pct_change(36).fillna(0).clip(-2, 2)
    df["Month"]     = df["Date"].dt.month
    df["Month_sin"] = np.sin(2 * np.pi * df["Month"] / 12)
    df["Month_cos"] = np.cos(2 * np.pi * df["Month"] / 12)
    df["Mine_age"]  = g["Production"].transform(lambda x: ((x > 0).cumsum()).clip(upper=36))
    df["Mine_Size"]     = df["Match_Key"].map(ms_map).fillna(0)
    df["Company_Size"]  = df["Match_Key"].map(COMPANY_SIZE_MAP).fillna(0)
    nat_sum = df.groupby("Date")["Production"].transform("sum")
    df["Mine_share"]    = df["Production"] / (nat_sum + 1e-6)
    cu_med = df["Cu_Price"].rolling(24, min_periods=6).median()
    df["Cu_regime"]     = (df["Cu_Price"] > cu_med).astype(int)
    df["Peak_Prod"]     = g["Production"].transform(lambda x: x.expanding().max())
    df["Prod_vs_peak"]  = df["Production"] / (df["Peak_Prod"] + 1e-6)
    df["Is_Decline"]    = (df["Prod_pct_change_36m"] < -0.15).astype(int)
    df["Is_Terminal_Decline"] = ((df["Prod_vs_peak"] < 0.30) & (df["Tendencia_12m"] < 0)).astype(int)

    # Cu_Price_Lag12
    df_cu = df.drop_duplicates("Date").sort_values("Date")[["Date", "Cu_Price"]].copy()
    df_cu["Cu_Price_Lag12"] = df_cu["Cu_Price"].shift(12).ffill().bfill().fillna(df_cu["Cu_Price"].mean())
    df = df.merge(df_cu[["Date", "Cu_Price_Lag12"]], on="Date", how="left")

    # NatCorr_24m
    nat_prod_col = df.groupby("Date")["Production"].transform("sum")
    df["Nat_Prod_tmp"] = nat_prod_col
    def _natcorr(grp):
        return grp["Production"].shift(1).rolling(24, min_periods=12).corr(
            grp["Nat_Prod_tmp"].shift(1))
    df["NatCorr_24m"] = df.groupby("Match_Key", group_keys=False).apply(
        _natcorr).fillna(0)
    df.drop(columns=["Nat_Prod_tmp"], inplace=True)

    # Is_Oxide (static per mine)
    df["Is_Oxide"] = df["Match_Key"].map(is_oxide_map).fillna(0)

    # Reserve_Life (static approximation)
    df["Reserve_Life"] = df["Match_Key"].map(RESERVE_LIFE_MAP).fillna(20)

    # Stock_Level_Lag3
    df["Stock_Level_Lag3"] = [
        get_stock_level_lag3(m, d) for m, d in zip(df["Match_Key"], df["Date"])
    ]

    # SIGEX proxies (use Cu_Price momentum as a proxy for pipeline activity)
    df["SIGEX_Cu_InEval"] = df["Cu_Price"] / (df["Cu_Price"].rolling(24, min_periods=6).mean() + 1e-6)
    df["SIGEX_Cu_Total"]  = df["SIGEX_Cu_InEval"]  # same proxy
    df["Friction"]        = 0.5  # neutral default
    df["Shock_Intensity"] = 0.0  # no shock at projection time

    return df.fillna(0)

print("🔧 Building features...")
df_feats = build_features_at_origin(df_raw.copy(), ms_map, PROJECTION_ORIGIN)

# Feature sets (matching v33)
BASE = [
    "Company_Size", "Prod_Lag1", "Prod_Lag12", "Mine_age",
    "Month_sin", "Prod_MA12", "Tendencia_12m",
    "Prod_pct_change_m", "Mine_trend_slope_36m", "Prod_vs_peak", "Mine_share",
]
FEATS_SM = BASE + [
    "Shock_Intensity", "SIGEX_Cu_InEval", "Friction",
    "Cu_Price_Lag12", "NatCorr_24m", "Stock_Level_Lag3",
    "Is_Oxide", "Reserve_Life", "Horizonte_feat",
    "Is_Recovery_Target", "Is_Terminal_Decline",
]
FEATS_LC = BASE + [
    "Shock_Intensity", "SIGEX_Cu_Total", "SIGEX_Cu_InEval",
    "Capital_Stock", "NatCorr_24m", "Stock_Level_Lag3",
    "Is_Oxide", "Reserve_Life", "Horizonte_feat",
    "Is_Recovery_Target", "Is_Terminal_Decline",
]

# ─── 4. Train RF on All Data (multi-horizon direct) ───────────────────────────
print("🏋️  Training RF models on all available data...")

tr_sm, tr_lc = [], []
for h_tr in HORIZONS:
    dh  = df_feats.copy()
    td  = dh["Date"] + pd.DateOffset(months=h_tr)
    dh["Target"]              = dh.groupby("Match_Key")["Production"].shift(-h_tr)
    dh["Horizonte_feat"]      = h_tr
    dh["Is_Recovery_Target"]  = ((td >= RECOVERY_START) & (td <= RECOVERY_END)).astype(int)
    dh["Is_Terminal_Decline"] = dh["Is_Terminal_Decline"]  # already set

    # Only use rows where target is observed (train window only — no future leakage)
    mask = (dh["Date"] <= PROJECTION_ORIGIN) & (td <= PROJECTION_ORIGIN) & (dh["Prod_Lag1"] > 0)
    sm_c = dh[mask & (dh["Mine_Size"] <= 1)].dropna(subset=FEATS_SM + ["Target", "Production"])
    lc_c = dh[mask & (dh["Mine_Size"] >= 2)].dropna(subset=FEATS_LC + ["Target", "Production"])
    if len(sm_c) > 0:
        tr_sm.append(sm_c)
    if len(lc_c) > 0:
        tr_lc.append(lc_c)

def make_xy(frames, feats):
    if not frames:
        return None, None
    dc = pd.concat(frames, ignore_index=True)
    if len(dc) < 20:
        return None, None
    y = np.clip(np.log((dc["Target"] + 1e-6) / (dc["Production"] + 1e-6)), -1.5, 1.5)
    return dc[feats].fillna(0).values, y.values

Xsm, ysm = make_xy(tr_sm, FEATS_SM)
Xlc, ylc = make_xy(tr_lc, FEATS_LC)

rf_sm = RandomForestRegressor(**RF_PARAMS).fit(Xsm, ysm) if Xsm is not None else None
rf_lc = RandomForestRegressor(**RF_PARAMS).fit(Xlc, ylc) if Xlc is not None else None
print(f"   RF SM: {len(Xsm) if Xsm is not None else 0} training samples")
print(f"   RF LC: {len(Xlc) if Xlc is not None else 0} training samples")

# ─── 5. RollingMean at Projection Origin ──────────────────────────────────────
rolling_mean = {}
for mine in MINES:
    s = df_raw[(df_raw["Match_Key"] == mine) & (df_raw["Date"] <= PROJECTION_ORIGIN)
               ].sort_values("Date")["Production"]
    tail = s.tail(36)
    rolling_mean[mine] = float(tail.mean()) if len(tail) >= 6 else (float(s.mean()) if len(s) > 0 else 0.0)

# ─── 6. Load Validation Errors for CI ─────────────────────────────────────────
# Per-mine, per-horizon quantile errors from v33 validation
ci_lower_q = {}  # mine → per-horizon dict: H → q15 of (pred-actual)/actual
ci_upper_q = {}  # mine → per-horizon dict: H → q85 of (pred-actual)/actual
ci_mine_mape = {}  # mine → overall MAPE fallback

try:
    val = pd.read_csv(VAL_PREDS)
    val = val[(val["Actual"] > 0) & (val["Pred"] > 0)]
    val["err_ratio"] = (val["Pred"] - val["Actual"]) / val["Actual"]
    val["ape"] = val["err_ratio"].abs()

    for mine, grp in val.groupby("Mine"):
        ci_mine_mape[mine] = float(grp["ape"].median())
        lo_h, hi_h = {}, {}
        for h, hgrp in grp.groupby("Horizonte"):
            lo_h[h] = float(np.percentile(hgrp["err_ratio"], 15))
            hi_h[h] = float(np.percentile(hgrp["err_ratio"], 85))
        ci_lower_q[mine] = lo_h
        ci_upper_q[mine] = hi_h

    print(f"   Validation CI loaded for {len(ci_mine_mape)} mines")
except Exception as e:
    print(f"   ⚠ Validation CI not loaded: {e}")

def get_ci(mine, h, pred):
    """Return (lower, upper) kt bounds around pred for given mine/horizon."""
    mape = ci_mine_mape.get(mine, 0.20)
    lo_q = ci_lower_q.get(mine, {}).get(h)
    hi_q = ci_upper_q.get(mine, {}).get(h)
    # Nearest available horizon fallback
    if lo_q is None or hi_q is None:
        avail = sorted(ci_lower_q.get(mine, {}).keys())
        if avail:
            nearest = min(avail, key=lambda x: abs(x - h))
            lo_q = ci_lower_q[mine].get(nearest, -mape)
            hi_q = ci_upper_q[mine].get(nearest,  mape)
        else:
            lo_q, hi_q = -mape, mape
    lower = pred * (1 + lo_q)
    upper = pred * (1 + hi_q)
    # Guarantee pred is inside [lower, upper]
    lower = min(lower, pred * (1 - abs(lo_q)))
    upper = max(upper, pred * (1 + abs(hi_q)))
    return max(0.0, round(lower, 3)), round(upper, 3)

# ─── 7. Generate Projections ──────────────────────────────────────────────────
print("🔮 Generating projections...")

def rf_predict(model, xv):
    if model is None:
        return np.nan
    try:
        return float(model.predict(xv)[0])
    except Exception:
        return np.nan

rows = []
origin_row = df_feats[df_feats["Date"] == PROJECTION_ORIGIN].copy()

for h in HORIZONS:
    target_date = PROJECTION_ORIGIN + pd.DateOffset(months=h)
    is_rec = int(RECOVERY_START <= target_date <= RECOVERY_END)
    is_term = 0  # at projection time, terminal decline is static

    for mine in MINES:
        mine_row = origin_row[origin_row["Match_Key"] == mine]
        if mine_row.empty:
            continue

        r = mine_row.iloc[0]
        orig_prod = float(r["Production"])
        if orig_prod <= 0:
            orig_prod = rolling_mean.get(mine, 1.0)

        ms       = ms_map.get(mine, 0)
        is_sm    = ms <= 1
        feats    = FEATS_SM if is_sm else FEATS_LC
        segment  = "SM" if is_sm else "LC"

        # Build feature vector for this horizon
        r_copy = r.copy()
        r_copy["Horizonte_feat"]      = h
        r_copy["Is_Recovery_Target"]  = is_rec
        r_copy["Is_Terminal_Decline"] = is_term
        xv = r_copy[feats].fillna(0).values.reshape(1, -1)

        # RF prediction (log-ratio → actual production)
        model = rf_sm if is_sm else rf_lc
        log_ratio = rf_predict(model, xv)
        if not math.isnan(log_ratio):
            rf_pred = max(0.0, math.exp(log_ratio) * (orig_prod + 1e-6))
        else:
            rf_pred = np.nan

        # RollingMean prediction (horizon-independent anchor)
        rm_pred = rolling_mean.get(mine, orig_prod)

        # Alpha blending
        if is_sm:
            if h in H_SHORT:
                alpha = ALPHA_SM_SHORT
            elif h in H_MID:
                alpha = ALPHA_SM_MID
            else:
                alpha = ALPHA_SM_LONG
        else:
            alpha = ALPHA_LC

        if not math.isnan(rf_pred):
            pred = max(0.0, alpha * rf_pred + (1 - alpha) * rm_pred)
        else:
            pred = rm_pred

        naive_pred = orig_prod  # flat naive

        lower, upper = get_ci(mine, h, pred)

        # Compute confidence interval: blend RF individual tree variance with quantile CI
        try:
            # RF per-tree predictions → std for additional uncertainty
            tree_preds = np.array([
                max(0.0, math.exp(float(t.predict(xv)[0])) * (orig_prod + 1e-6))
                for t in model.estimators_[:50]
            ]) if model is not None else np.array([pred])
            rf_std = float(np.std(tree_preds))
            # Widen CI if RF has high variance
            ci_extra = rf_std * 0.5
            lower = max(0.0, min(lower, pred - ci_extra))
            upper = max(upper, pred + ci_extra)
        except Exception:
            pass

        rows.append({
            "Mine":        mine,
            "ForecastDate": target_date.strftime("%Y-%m-%d"),
            "Horizonte":   h,
            "Pred":        round(pred, 4),
            "Naive_Pred":  round(naive_pred, 4),
            "Lower":       round(lower, 4),
            "Upper":       round(upper, 4),
            "Origin_Prod": round(orig_prod, 4),
            "Mine_Size":   ms,
            "Size_Label":  SIZE_LABELS.get(ms, "Small"),
            "Company_Size": int(r.get("Company_Size", COMPANY_SIZE_MAP.get(mine, 0))),
            "Segment":     segment,
        })

df_proj = pd.DataFrame(rows)
print(f"   Generated {len(df_proj)} rows for {df_proj['Mine'].nunique()} mines")

# ─── 8. Sanity check ──────────────────────────────────────────────────────────
df_proj["ci_ok"] = (df_proj["Lower"] <= df_proj["Pred"]) & (df_proj["Pred"] <= df_proj["Upper"])
ci_pass = df_proj["ci_ok"].mean() * 100
print(f"   CI check: {ci_pass:.1f}% rows have Lower ≤ Pred ≤ Upper")

growth_cap = 2.5
df_proj["growth_ratio"] = df_proj["Pred"] / df_proj["Origin_Prod"].clip(lower=0.1)
runaway = (df_proj["growth_ratio"] > growth_cap).sum()
if runaway > 0:
    print(f"   ⚠ {runaway} rows with Pred > {growth_cap}x Origin — capping")
    mask = df_proj["growth_ratio"] > growth_cap
    df_proj.loc[mask, "Pred"]  = (df_proj.loc[mask, "Origin_Prod"] * growth_cap).round(4)
    df_proj.loc[mask, "Upper"] = df_proj.loc[mask, "Pred"]
    df_proj.loc[mask, "Lower"] = (df_proj.loc[mask, "Pred"] * 0.75).round(4)

df_proj.drop(columns=["ci_ok", "growth_ratio"], inplace=True)

# ─── 9. Sample output ─────────────────────────────────────────────────────────
print()
print("Sample — Escondida:")
esc = df_proj[df_proj["Mine"] == "escondida"][["ForecastDate","Horizonte","Pred","Lower","Upper","Naive_Pred"]]
print(esc.to_string(index=False))

# ─── 10. Save ─────────────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
df_proj.to_csv(OUT_PATH, index=False)
print()
print(f"✅ Saved → {OUT_PATH}")
print(f"   Shape: {df_proj.shape}")
