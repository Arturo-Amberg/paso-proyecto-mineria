"""
Optimización Espacial Zonal Minera
===================================
Para cada cluster minero, busca el punto óptimo dentro del espacio geográfico
del cluster que maximiza 5 funciones objetivo distintas usando un radio de 30 km.

El centro óptimo NO es el centroide — se encuentra mediante búsqueda en grilla.
"""

import json
import math
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.spatial import ConvexHull

warnings.filterwarnings("ignore")

BASE   = Path("/Users/mac/TrabajoTesis/Bases")
OUT    = Path("/Users/mac/TrabajoTesis/05_OptimizacionZonal/outputs")
OUT.mkdir(exist_ok=True)

RADIUS_KM  = 30
GRID_N     = 18        # NxN candidate grid per cluster (18×18 = 324 candidates)
PREFILTER_KM = 150     # pre-filter data to this radius from cluster centroid

# ═══════════════════════════════════════════════════════════════════════════
# 1. HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def haversine_vec(lat0, lon0, lats, lons):
    R = 6371.0
    dlat = np.radians(lats - lat0)
    dlon = np.radians(lons - lon0)
    a = (np.sin(dlat/2)**2
         + np.cos(np.radians(lat0)) * np.cos(np.radians(lats)) * np.sin(dlon/2)**2)
    return R * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))

def haversine_batch(lat_arr, lon_arr, ref_lats, ref_lons):
    """Distance from each (lat_arr[i],lon_arr[i]) to all (ref_lats, ref_lons).
    Returns shape (len(lat_arr), len(ref_lats))."""
    R = 6371.0
    lat_arr   = np.radians(lat_arr)[:,None]
    lon_arr   = np.radians(lon_arr)[:,None]
    ref_lats  = np.radians(ref_lats)[None,:]
    ref_lons  = np.radians(ref_lons)[None,:]
    dlat = ref_lats - lat_arr
    dlon = ref_lons - lon_arr
    a = np.sin(dlat/2)**2 + np.cos(lat_arr)*np.cos(ref_lats)*np.sin(dlon/2)**2
    return R * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))

def minmax(arr):
    lo, hi = arr.min(), arr.max()
    if hi == lo:
        return np.full_like(arr, 0.5, dtype=float)
    return (arr - lo) / (hi - lo)

# ═══════════════════════════════════════════════════════════════════════════
# 2. LOAD DATA
# ═══════════════════════════════════════════════════════════════════════════
print("Loading data…")

# SIGEX cluster membership (only clustered = cluster_final >= 0)
sigex_raw = pd.read_csv(BASE / "resultados_valles_mineros_final.csv")
sigex_raw = sigex_raw[sigex_raw["cluster_final"] >= 0].copy()
sigex_raw = sigex_raw.dropna(subset=["Latitud","Longitud"])

# All SIGEX faenas (for scoring within radius)
faenas = pd.read_csv(BASE / "faenas_with_accessibility.csv")
faenas = faenas.dropna(subset=["Latitud","Longitud"])

relaves = pd.read_csv(BASE / "CATASTRO_RELAVES_CHILE_OCT2025.csv")
relaves = relaves.dropna(subset=["LATITUD","LONGITUD"])

seia = pd.read_excel(BASE / "Proyectos_SEIA.xlsx")
seia_m = seia[seia["Sector Productivo"]=="Minería"].dropna(
    subset=["Latitud Punto Representativo","Longitud Punto Representativo"])

water = pd.read_csv(BASE/"plantas_desaladoras_combinado_final.csv", encoding="latin1")
water = water.dropna(subset=["Latitude","Longitude"])
water_op = water[water["Estado Operacional"]=="En operacion"].copy()

subs = pd.read_csv(BASE/"subestaciones.csv", encoding="latin1").dropna(subset=["Latitude","Longitude"])
lins = pd.read_csv(BASE/"lineas_transmision.csv", encoding="latin1").dropna(subset=["Latitude","Longitude"])
ports = pd.read_csv(BASE/"puertos.csv", encoding="latin1").dropna(subset=["latitude","longitude"])

# Pre-extract numpy arrays for global data
f_lats  = faenas["Latitud"].values;     f_lons  = faenas["Longitud"].values
f_cats  = faenas["CategoriaFaena"].values
f_tipos = faenas["TipoInstalacion"].values

r_lats  = relaves["LATITUD"].values;   r_lons  = relaves["LONGITUD"].values
r_sta   = relaves["ESTADO_INSTALACION"].values
r_vol   = relaves["VOL_ACTUAL"].fillna(0).values

s_lats  = seia_m["Latitud Punto Representativo"].values
s_lons  = seia_m["Longitud Punto Representativo"].values
s_est   = seia_m["Estado del Proyecto"].values
s_inv   = seia_m["Inversión (MMU$)"].fillna(0).values

w_lats  = water_op["Latitude"].values;  w_lons  = water_op["Longitude"].values
w_cap   = water_op["Capacidad (Valor)"].fillna(0).values
wa_lats = water["Latitude"].values;     wa_lons = water["Longitude"].values

sub_lats = subs["Latitude"].values;   sub_lons = subs["Longitude"].values
lin_lats = lins["Latitude"].values;   lin_lons = lins["Longitude"].values
p_lats   = ports["latitude"].values;  p_lons   = ports["longitude"].values

print(f"  Faenas: {len(faenas)} | Relaves: {len(relaves)} | SEIA minería: {len(seia_m)}")
print(f"  Desaladoras op: {len(water_op)} | Subs: {len(subs)} | Líneas: {len(lins)}")

# ═══════════════════════════════════════════════════════════════════════════
# 3. BUILD CLUSTER LIST
# ═══════════════════════════════════════════════════════════════════════════
cluster_ids = [c for c in sigex_raw["Cluster_ID"].unique()
               if "RUIDO" not in str(c) and sigex_raw[sigex_raw["Cluster_ID"]==c].shape[0] >= 10]

print(f"\nClusters to optimize: {len(cluster_ids)}")

# ═══════════════════════════════════════════════════════════════════════════
# 4. SCORING FUNCTIONS (applied per candidate grid point)
# ═══════════════════════════════════════════════════════════════════════════

def compute_grid_scores(cand_lats, cand_lons,
                        pf_lats, pf_lons, pf_cats, pf_tipos,
                        pr_lats, pr_lons, pr_sta, pr_vol,
                        ps_lats, ps_lons, ps_est, ps_inv,
                        pw_lats, pw_lons, pw_cap,
                        pwa_lats, pwa_lons,
                        psub_lats, psub_lons,
                        plin_lats, plin_lons,
                        pp_lats, pp_lons):
    """
    For each candidate point, compute metrics within RADIUS_KM and return
    per-formula score arrays of shape (n_candidates,).
    """
    n = len(cand_lats)

    # ── distance matrices (n_candidates × n_sources) ──
    # Only run if source arrays are non-empty
    def safe_dist(clats, clons, rlats, rlons):
        if len(rlats) == 0:
            return np.full((len(clats), 1), 999.0)
        return haversine_batch(clats, clons, rlats, rlons)

    D_f   = safe_dist(cand_lats, cand_lons, pf_lats, pf_lons)    # (n, n_faenas)
    D_r   = safe_dist(cand_lats, cand_lons, pr_lats, pr_lons)    # (n, n_rel)
    D_s   = safe_dist(cand_lats, cand_lons, ps_lats, ps_lons)    # (n, n_seia)
    D_w   = safe_dist(cand_lats, cand_lons, pw_lats, pw_lons)    # (n, n_water_op)
    D_wa  = safe_dist(cand_lats, cand_lons, pwa_lats, pwa_lons)  # (n, n_water_all)
    D_sub = safe_dist(cand_lats, cand_lons, psub_lats, psub_lons)
    D_lin = safe_dist(cand_lats, cand_lons, plin_lats, plin_lons)
    D_p   = safe_dist(cand_lats, cand_lons, pp_lats, pp_lons)

    mask_r_km = RADIUS_KM

    # ── FAENAS metrics ──
    in_f = D_f <= mask_r_km                          # (n, n_faenas) bool
    catA_mask = (pf_cats == "CATEGORIA A")
    catB_mask = (pf_cats == "CATEGORIA B")
    catC_mask = (pf_cats == "CATEGORIA C")
    conc_mask = (pf_tipos == "PLANTA CONCENTRADORA")

    n_catA = (in_f & catA_mask).sum(axis=1).astype(float)
    n_catB = (in_f & catB_mask).sum(axis=1).astype(float)
    n_catC = (in_f & catC_mask).sum(axis=1).astype(float)
    n_conc = (in_f & conc_mask).sum(axis=1).astype(float)
    n_fac  = in_f.sum(axis=1).astype(float)

    # ── RELAVES metrics ──
    in_r       = D_r <= mask_r_km
    activo_m   = (pr_sta == "ACTIVO")
    abandon_m  = (pr_sta == "ABANDONADO")
    inact_m    = (pr_sta == "INACTIVO")

    n_rel_act  = (in_r & activo_m).sum(axis=1).astype(float)
    n_rel_aban = (in_r & abandon_m).sum(axis=1).astype(float)
    n_rel_inac = (in_r & inact_m).sum(axis=1).astype(float)
    # Volume: sum of log1p(vol) weighted by in-radius relaves
    vol_in_r   = np.where(in_r, pr_vol[None,:], 0.0)
    vol_logsum = np.log1p(vol_in_r).sum(axis=1)

    # ── SEIA metrics ──
    in_s       = D_s <= mask_r_km
    aprobado_m = (ps_est == "Aprobado")
    rechazo_m  = (ps_est == "Rechazado") | (ps_est == "No Admitido a Tramitación")
    encal_m    = (ps_est == "En Calificación")

    n_aprobados  = (in_s & aprobado_m).sum(axis=1).astype(float)
    n_rechazados = (in_s & rechazo_m).sum(axis=1).astype(float)
    n_encal      = (in_s & encal_m).sum(axis=1).astype(float)
    inv_in_s     = np.where(in_s & aprobado_m[None,:], ps_inv[None,:], 0.0)
    inv_aprobada = inv_in_s.sum(axis=1)

    # ── WATER metrics ──
    in_w      = D_w <= mask_r_km
    cap_in_w  = np.where(in_w, pw_cap[None,:], 0.0)
    cap_desal = cap_in_w.sum(axis=1)
    # Nearest desal (all, not just operational)
    dist_desal = D_wa.min(axis=1)

    # ── INFRA metrics ──
    n_subs = (D_sub <= mask_r_km).sum(axis=1).astype(float)
    n_lins = (D_lin <= mask_r_km).sum(axis=1).astype(float)
    dist_port = D_p.min(axis=1)

    # ══════════════════════════════════════════════════════════════════
    # FORMULA SCORES
    # ══════════════════════════════════════════════════════════════════

    # F1 — Productive Density
    # Weighted facility count, normalized by total facilities in radius
    # (+1 avoids div-by-zero)
    F1 = (3*n_catA + 2*n_catB + n_catC + 0.5*n_conc)

    # F2 — Environmental Liability (higher = more risk, shown as problem map)
    # Log-vol + active relaves dominate; SEIA rejections amplify
    F2 = (2.0*n_rel_act + 1.5*n_rel_aban + 0.8*n_rel_inac
          + 0.5*vol_logsum + 0.5*n_rechazados)

    # F3 — Investment Pipeline
    # Log of approved investment × count multiplier × pipeline bonus
    F3 = (np.log1p(inv_aprobada) * (1 + n_aprobados/10)
          * (1 + n_encal*0.2))

    # F4 — Water-Energy Nexus
    # Operational desalination capacity (proximity-weighted) × infra strength
    # Closer desalination = higher score; more substations = higher score
    desal_score = cap_desal / (1 + dist_desal/50)
    infra_score = np.sqrt(n_subs + n_lins*0.5 + 1)
    F4 = desal_score * infra_score

    # F5 — Net Composite Opportunity (main optimizer)
    # Normalise each sub-score within this grid before combining
    F1n = minmax(F1)
    F2n = minmax(F2)  # risk → we penalize
    F3n = minmax(F3)
    F4n = minmax(F4)

    F5 = 0.35*F1n + 0.30*F3n + 0.20*F4n - 0.15*F2n

    return {
        "F1": F1, "F2": F2, "F3": F3, "F4": F4, "F5": F5,
        # raw data for diagnostics at the optimal point
        "_n_catA": n_catA, "_n_catB": n_catB, "_n_catC": n_catC,
        "_n_conc": n_conc, "_n_fac": n_fac,
        "_n_rel_act": n_rel_act, "_n_rel_aban": n_rel_aban,
        "_inv_aprobada": inv_aprobada, "_n_aprobados": n_aprobados,
        "_n_rechazados": n_rechazados, "_n_encal": n_encal,
        "_cap_desal": cap_desal, "_dist_desal": dist_desal,
        "_n_subs": n_subs, "_n_lins": n_lins, "_dist_port": dist_port,
    }


# ═══════════════════════════════════════════════════════════════════════════
# 5. MAIN LOOP
# ═══════════════════════════════════════════════════════════════════════════

FORMULAS = {
    "F1": {"name": "Densidad Productiva",
           "desc": "Concentración de faenas de alto valor (Cat-A/B/C + concentradoras)",
           "color": "#22c55e", "maximize": True},
    "F2": {"name": "Pasivo Ambiental",
           "desc": "Zona de mayor presión de relaves y rechazo regulatorio (problema)",
           "color": "#ef4444", "maximize": True},
    "F3": {"name": "Pipeline de Inversión",
           "desc": "Concentración de inversión aprobada por SEIA",
           "color": "#f59e0b", "maximize": True},
    "F4": {"name": "Nexo Hídrico-Energético",
           "desc": "Mejor acceso combinado a agua desalada e infraestructura eléctrica",
           "color": "#38bdf8", "maximize": True},
    "F5": {"name": "Oportunidad Neta Compuesta",
           "desc": "Equilibrio óptimo: oportunidad productiva + inversión + agua − riesgo ambiental",
           "color": "#a78bfa", "maximize": True},
}

results = []
errors = []

for cid in cluster_ids:
    clust_pts = sigex_raw[sigex_raw["Cluster_ID"] == cid]
    clat_pts  = clust_pts["Latitud"].values
    clon_pts  = clust_pts["Longitud"].values
    n_pts     = len(clat_pts)

    centroid_lat = clat_pts.mean()
    centroid_lon = clon_pts.mean()

    # ── Build candidate grid ──────────────────────────────────────
    # Bounding box with 20% padding
    pad_lat = max(0.15, (clat_pts.max()-clat_pts.min())*0.15)
    pad_lon = max(0.15, (clon_pts.max()-clon_pts.min())*0.15)
    lat_min = clat_pts.min() - pad_lat;  lat_max = clat_pts.max() + pad_lat
    lon_min = clon_pts.min() - pad_lon;  lon_max = clon_pts.max() + pad_lon

    grid_lats = np.linspace(lat_min, lat_max, GRID_N)
    grid_lons = np.linspace(lon_min, lon_max, GRID_N)
    glon, glat = np.meshgrid(grid_lons, grid_lats)
    cand_lats = glat.ravel()
    cand_lons = glon.ravel()

    # ── Pre-filter global data to ±PREFILTER_KM of cluster centroid ──
    def pf(lats, lons):
        d = haversine_vec(centroid_lat, centroid_lon, lats, lons)
        mask = d <= PREFILTER_KM
        return lats[mask], lons[mask], mask

    pf_lats, pf_lons, mf = pf(f_lats, f_lons)
    pf_cats  = f_cats[mf];   pf_tipos = f_tipos[mf]

    pr_lats, pr_lons, mr = pf(r_lats, r_lons)
    pr_sta = r_sta[mr];      pr_vol  = r_vol[mr]

    ps_lats, ps_lons, ms = pf(s_lats, s_lons)
    ps_est = s_est[ms];      ps_inv  = s_inv[ms]

    pw_lats, pw_lons, mw  = pf(w_lats, w_lons)
    pw_cap = w_cap[mw]
    pwa_lats, pwa_lons, _ = pf(wa_lats, wa_lons)

    psub_lats, psub_lons, _ = pf(sub_lats, sub_lons)
    plin_lats, plin_lons, _ = pf(lin_lats, lin_lons)
    pp_lats,   pp_lons,   _ = pf(p_lats,   p_lons)

    try:
        scores = compute_grid_scores(
            cand_lats, cand_lons,
            pf_lats, pf_lons, pf_cats, pf_tipos,
            pr_lats, pr_lons, pr_sta, pr_vol,
            ps_lats, ps_lons, ps_est, ps_inv,
            pw_lats, pw_lons, pw_cap,
            pwa_lats, pwa_lons,
            psub_lats, psub_lons,
            plin_lats, plin_lons,
            pp_lats, pp_lons,
        )
    except Exception as e:
        errors.append((cid, str(e)))
        print(f"  ERROR {cid}: {e}")
        continue

    # ── Per-formula optimal ──
    formula_results = {}
    for fname, fmeta in FORMULAS.items():
        raw_scores = scores[fname]
        norm_scores = minmax(raw_scores)  # 0–1 for comparison
        best_idx = int(np.argmax(raw_scores))
        worst_idx = int(np.argmin(raw_scores))

        opt_lat = float(cand_lats[best_idx])
        opt_lon = float(cand_lons[best_idx])
        opt_score_norm = float(norm_scores[best_idx])

        # Distance from cluster centroid to this optimal point
        dist_from_centroid = float(haversine_vec(centroid_lat, centroid_lon,
                                                  np.array([opt_lat]), np.array([opt_lon]))[0])

        # Diagnostic metrics at optimal point
        diag = {k.lstrip("_"): float(scores[k][best_idx])
                for k in scores if k.startswith("_")}

        # Score surface for heatmap (GRID_N × GRID_N, row-major lat=rows, lon=cols)
        surface_norm = norm_scores.reshape(GRID_N, GRID_N).tolist()

        formula_results[fname] = {
            "formula_name": fmeta["name"],
            "formula_desc": fmeta["desc"],
            "color": fmeta["color"],
            "maximize": fmeta["maximize"],
            "opt_lat": opt_lat,
            "opt_lon": opt_lon,
            "score_norm": round(opt_score_norm, 4),
            "dist_from_centroid_km": round(dist_from_centroid, 2),
            "diagnostics": {k: round(v, 2) for k, v in diag.items()},
            "score_surface": surface_norm,
        }

    # Cluster boundary polygon (convex hull of cluster facilities)
    if n_pts >= 3:
        try:
            pts2d = np.column_stack([clon_pts, clat_pts])
            hull = ConvexHull(pts2d)
            hull_pts = pts2d[hull.vertices].tolist()
            hull_pts.append(hull_pts[0])  # close polygon
        except Exception:
            hull_pts = [[clon_pts.min(), clat_pts.min()],
                        [clon_pts.max(), clat_pts.min()],
                        [clon_pts.max(), clat_pts.max()],
                        [clon_pts.min(), clat_pts.max()],
                        [clon_pts.min(), clat_pts.min()]]
    else:
        hull_pts = []

    # Agreement: do F1, F3, F4, F5 agree on the same zone?
    f5_lat = formula_results["F5"]["opt_lat"]
    f5_lon = formula_results["F5"]["opt_lon"]
    convergence = {}
    for fname in ["F1","F3","F4"]:
        d = float(haversine_vec(f5_lat, f5_lon,
                                np.array([formula_results[fname]["opt_lat"]]),
                                np.array([formula_results[fname]["opt_lon"]]))[0])
        convergence[fname] = round(d, 2)
    avg_convergence = float(np.mean(list(convergence.values())))

    # Grid metadata (shared across formulas)
    grid_meta = {
        "lat_min": float(lat_min), "lat_max": float(lat_max),
        "lon_min": float(lon_min), "lon_max": float(lon_max),
        "grid_n": GRID_N,
        "cand_lats": [round(v,6) for v in cand_lats.tolist()],
        "cand_lons": [round(v,6) for v in cand_lons.tolist()],
    }

    record = {
        "cluster_id": cid,
        "region": cid.split("-")[0],
        "n_cluster_facilities": int(n_pts),
        "centroid_lat": round(centroid_lat, 6),
        "centroid_lon": round(centroid_lon, 6),
        "radius_km": RADIUS_KM,
        "hull_polygon": hull_pts,       # [[lon,lat], ...] for Leaflet
        "grid_meta": grid_meta,
        "formulas": formula_results,
        "convergence_km": convergence,
        "avg_convergence_km": round(avg_convergence, 2),
    }
    results.append(record)
    print(f"  ✓ {cid:<25} | pts={n_pts:>3} | "
          f"F5 opt=({formula_results['F5']['opt_lat']:.3f},{formula_results['F5']['opt_lon']:.3f}) "
          f"Δ={formula_results['F5']['dist_from_centroid_km']:.1f}km | "
          f"convergence={avg_convergence:.1f}km")

# ═══════════════════════════════════════════════════════════════════════════
# 6. EVALUATION & ITERATION CHECK
# ═══════════════════════════════════════════════════════════════════════════
print(f"\n{'='*70}")
print(f"SPATIAL OPTIMIZATION — SUMMARY ({len(results)} clusters)")
print(f"{'='*70}")

# Check: are optimal points meaningfully displaced from centroid?
displacements = [r["formulas"]["F5"]["dist_from_centroid_km"] for r in results]
conv_vals     = [r["avg_convergence_km"] for r in results]

print(f"\nF5 displacement from centroid:")
print(f"  mean={np.mean(displacements):.1f} km | max={np.max(displacements):.1f} km | min={np.min(displacements):.1f} km")
print(f"\nFormula convergence (dist between F1/F3/F4 optima and F5):")
print(f"  mean={np.mean(conv_vals):.1f} km | max={np.max(conv_vals):.1f} km")

print(f"\n{'─'*70}")
print(f"{'Cluster':<25} {'F5_score':>8} {'Δ_centroid':>11} {'Conv':>8} {'F5 Opt Driver'}")
print(f"{'─'*70}")
ranked = sorted(results, key=lambda r: r["formulas"]["F5"]["score_norm"], reverse=True)
for r in ranked:
    f5 = r["formulas"]["F5"]
    d = f5["diagnostics"]
    # Identify what drives F5 at its optimal point
    drivers = []
    if d.get("n_catA",0) >= 3: drivers.append(f"CatA={int(d['n_catA'])}")
    if d.get("inv_aprobada",0) > 50: drivers.append(f"SEIA={d['inv_aprobada']:.0f}MMU$")
    if d.get("cap_desal",0) > 0: drivers.append(f"Desal={d['cap_desal']:.0f}lps")
    driver_str = " | ".join(drivers) if drivers else "—"
    print(f"{r['cluster_id']:<25} {f5['score_norm']:>8.3f} {f5['dist_from_centroid_km']:>10.1f}km "
          f"{r['avg_convergence_km']:>6.1f}km  {driver_str}")

# ── Evaluator: check if optimization is adding value ──────────────────────
mean_disp = np.mean(displacements)
frac_displaced = np.mean([d > 5 for d in displacements])

print(f"\n[EVALUADOR]")
if mean_disp < 3:
    print("⚠️  Desplazamiento medio bajo (<3km). Los datos podrían estar muy agrupados.")
    print("   Sugerencia: aumentar RADIUS_KM o GRID_N para mayor resolución.")
elif frac_displaced > 0.7:
    print(f"✅ El {frac_displaced*100:.0f}% de los clusters tiene óptimo desplazado >5km del centroide.")
    print("   La optimización espacial agrega valor real frente al uso del centroide.")
else:
    print(f"✅ Desplazamiento medio: {mean_disp:.1f} km. Optimización coherente.")

if errors:
    print(f"\n⚠️  Errors: {errors}")

# ═══════════════════════════════════════════════════════════════════════════
# 7. SAVE
# ═══════════════════════════════════════════════════════════════════════════
out_path = OUT / "spatial_optimization.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\nSaved → {out_path}  ({len(results)} clusters, {out_path.stat().st_size//1024} KB)")
print("Ready for dashboard_optimizacion.html")
