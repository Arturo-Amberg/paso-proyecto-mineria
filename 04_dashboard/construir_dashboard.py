#!/usr/bin/env python3
"""
Mining Cluster Dashboard Builder v2  (updated)
Changes vs v1:
  - Estaciones (train stations) + connecting track polylines
  - SEIA upcoming projects layer (En Calificación + Aprobado ≥ 50 MMU$)
  - Mining-only desaladora utilization
  - Cluster named after top-producing mine
  - Company % control breakdown per cluster
  - Tiers removed
"""

import os, re, json, csv, math, sys
from collections import defaultdict
from difflib import SequenceMatcher

import pandas as pd
import numpy as np
from scipy.spatial import ConvexHull, QhullError
from shapely.geometry import MultiPoint, Point as _ShapelyPoint, Polygon as _ShPoly
from shapely.ops import unary_union as _shapely_union
from shapely import concave_hull as _shapely_concave_hull

# ─── PATHS ────────────────────────────────────────────────────────────────────
BASE        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARED      = os.path.join(BASE, "01_Data", "shared")
PROCESSED   = os.path.join(BASE, "01_Data", "processed")
CLUSTER_DIR = os.path.join(BASE, "02_Clustering", "outputs")
RAW_DIR     = os.path.join(BASE, "01_Data", "raw")
OUTPUT_DIR  = os.path.join(BASE, "04_Dashboard", "outputs")
OUTPUT_HTML = os.path.join(OUTPUT_DIR, "mining_clusters_v2.html")
OUTPUT_IDX  = os.path.join(OUTPUT_DIR, "index.html")
OPT_JSON    = os.path.join(BASE, "05_OptimizacionZonal", "outputs", "optimization_data.json")
FORECAST_ANNUAL_DIR  = os.path.join(BASE, "03_Forecasting", "03_annual_model",  "outputs_best")
FORECAST_MONTHLY_DIR = os.path.join(BASE, "03_Forecasting", "04_monthly_model", "outputs_best")

# ─── CONFIG ───────────────────────────────────────────────────────────────────
WATER_M3_PER_TON   = 80.0   # m³ per tonne Cu — calibrated: BHP ~3000 lps / ~1400 kt ≈ 67-80
DESAL_UTIL_RATE    = 0.90   # operational utilisation factor for desaladoras (BHP benchmark: 90%)
ELEC_MWH_PER_TON   = 12.0
INFRA_RADIUS_KM    = 150
DESAL_RADIUS_KM    = 250
RELAVE_RADIUS_KM   = 200
DEFAULT_YEAR       = 2025
ZOOM_THRESHOLD     = 9
TRAIN_GAP_KM       = 80   # gap that signals a new rail line segment
OUTLIER_KM         = 103  # max km from cluster centroid for a faena to be included
SIGEX_CSV   = os.path.join(SHARED, "ProyectosSIGEX", "ProyectosSIGEX.csv")

REGION_NAMES = {
    "I": "Tarapacá", "II": "Antofagasta", "III": "Atacama",
    "IV": "Coquimbo", "V": "Valparaíso", "VI": "O'Higgins",
    "RM": "Metropolitana", "XV": "Arica y Parinacota",
}

# Maps desaladora operator tokens → mine match_key fragments (subsidiaries included)
# BHP → escondida + spence + cerro colorado (all BHP-operated mines)
COMPANY_MINE_MAP = {
    "bhp":            ["escondida", "spence", "cerro colorado"],
    "codelco":        ["chuquicamata", "radomiro tomic", "ministro hales",
                       "gabriela mistral", "salvador", "andina", "el teniente"],
    "lundin":         ["candelaria"],
    "antofagasta":    ["los pelambres", "centinela", "antucoya", "michilla", "zaldivar"],
    "teck":           ["quebrada blanca", "andacollo"],
    "glencore":       ["lomas bayas"],
    "capstone":       ["capstone", "mantoverde", "santo domingo"],
    "mantos copper":  ["mantoverde", "mantos"],
    "mantos":         ["mantoverde", "mantos"],
    "anglo american": ["los bronces"],
    "collahuasi":     ["collahuasi"],
    "pelambres":      ["los pelambres"],
    "centinela":      ["centinela"],
    "kghm":           ["sierra gorda"],
    "caserones":      ["caserones"],
    "sierra gorda":   ["sierra gorda"],
}

CLUSTER_PALETTE = [
    "#FF6B6B","#FF8E53","#FFC857","#4ECDC4","#45B7D1",
    "#96E6A1","#DDA0DD","#F0A500","#61D2B4","#4FC3F7",
    "#039BE5","#7986CB","#9575CD","#BA68C8","#F06292",
    "#FF7043","#FFCA28","#66BB6A","#26A69A","#42A5F5",
    "#EC407A","#AB47BC","#7E57C2",
]

ESTADO_COLORS = {
    "ACTIVA":"#22c55e","ACTIVO":"#22c55e",
    "INACTIVA":"#f59e0b","INACTIVO":"#f59e0b",
    "ABANDONADO":"#ef4444","ABANDONADA":"#ef4444",
    "ELIMINADO":"#6b7280","ELIMINADA":"#6b7280",
    "CERRADA":"#6b7280",
}

TRAIN_COLORS = [
    "#a78bfa","#34d399","#fb923c","#60a5fa","#f472b6",
    "#fbbf24","#4ade80","#38bdf8","#c084fc","#f87171",
    "#6ee7b7","#fdba74","#93c5fd","#f9a8d4","#fde68a",
    "#86efac","#7dd3fc","#e879f9","#fca5a5","#a3e635",
]

HARBOR_SIZE_LABELS = {'L':'Grande','M':'Mediano','S':'Pequeño','V':'Muy pequeño','T':'Tidal only'}

# Significant Chilean cities/towns for relaves population-risk analysis
# Coordinates: WGS84 decimal degrees; poblacion: census estimate ~2017-2024
CIUDADES_CHILE = [
    # XV — Arica y Parinacota
    {"nombre":"Arica",           "region":"XV",  "poblacion":222543, "lat":-18.477, "lon":-70.321},
    {"nombre":"Putre",           "region":"XV",  "poblacion":2500,   "lat":-18.194, "lon":-69.564},
    # I — Tarapacá
    {"nombre":"Iquique",         "region":"I",   "poblacion":216419, "lat":-20.214, "lon":-70.151},
    {"nombre":"Alto Hospicio",   "region":"I",   "poblacion":128748, "lat":-20.272, "lon":-70.099},
    {"nombre":"Pozo Almonte",    "region":"I",   "poblacion":14892,  "lat":-20.259, "lon":-69.788},
    {"nombre":"Huara",           "region":"I",   "poblacion":4100,   "lat":-19.996, "lon":-69.772},
    {"nombre":"Pica",            "region":"I",   "poblacion":5068,   "lat":-20.492, "lon":-69.328},
    # II — Antofagasta
    {"nombre":"Antofagasta",     "region":"II",  "poblacion":361873, "lat":-23.650, "lon":-70.399},
    {"nombre":"Calama",          "region":"II",  "poblacion":177257, "lat":-22.466, "lon":-68.929},
    {"nombre":"Tocopilla",       "region":"II",  "poblacion":24591,  "lat":-22.091, "lon":-70.199},
    {"nombre":"Mejillones",      "region":"II",  "poblacion":14018,  "lat":-23.097, "lon":-70.453},
    {"nombre":"Taltal",          "region":"II",  "poblacion":9877,   "lat":-25.401, "lon":-70.489},
    {"nombre":"María Elena",     "region":"II",  "poblacion":7046,   "lat":-22.351, "lon":-69.661},
    {"nombre":"Sierra Gorda",    "region":"II",  "poblacion":3100,   "lat":-22.893, "lon":-69.308},
    {"nombre":"Baquedano",       "region":"II",  "poblacion":2000,   "lat":-23.332, "lon":-69.844},
    # III — Atacama
    {"nombre":"Copiapó",         "region":"III", "poblacion":162449, "lat":-27.370, "lon":-70.334},
    {"nombre":"Caldera",         "region":"III", "poblacion":16750,  "lat":-27.065, "lon":-70.796},
    {"nombre":"Chañaral",        "region":"III", "poblacion":12046,  "lat":-26.350, "lon":-70.618},
    {"nombre":"Diego de Almagro","region":"III", "poblacion":18503,  "lat":-26.369, "lon":-70.047},
    {"nombre":"Vallenar",        "region":"III", "poblacion":51249,  "lat":-28.570, "lon":-70.760},
    {"nombre":"Huasco",          "region":"III", "poblacion":9800,   "lat":-28.468, "lon":-71.228},
    {"nombre":"Tierra Amarilla", "region":"III", "poblacion":13012,  "lat":-27.484, "lon":-70.276},
    {"nombre":"Potrerillos",     "region":"III", "poblacion":2800,   "lat":-26.427, "lon":-69.488},
    # IV — Coquimbo
    {"nombre":"La Serena",       "region":"IV",  "poblacion":232637, "lat":-29.907, "lon":-71.252},
    {"nombre":"Coquimbo",        "region":"IV",  "poblacion":227801, "lat":-29.953, "lon":-71.342},
    {"nombre":"Ovalle",          "region":"IV",  "poblacion":109799, "lat":-30.601, "lon":-71.198},
    {"nombre":"Illapel",         "region":"IV",  "poblacion":34734,  "lat":-31.630, "lon":-71.168},
    {"nombre":"Salamanca",       "region":"IV",  "poblacion":15000,  "lat":-31.774, "lon":-70.958},
    {"nombre":"Andacollo",       "region":"IV",  "poblacion":13000,  "lat":-30.233, "lon":-71.082},
    {"nombre":"Vicuña",          "region":"IV",  "poblacion":21000,  "lat":-30.032, "lon":-70.704},
    {"nombre":"Los Vilos",       "region":"IV",  "poblacion":18000,  "lat":-31.909, "lon":-71.511},
    # V — Valparaíso
    {"nombre":"Valparaíso",      "region":"V",   "poblacion":276791, "lat":-33.047, "lon":-71.619},
    {"nombre":"Los Andes",       "region":"V",   "poblacion":65700,  "lat":-32.833, "lon":-70.600},
    {"nombre":"San Felipe",      "region":"V",   "poblacion":69700,  "lat":-32.751, "lon":-70.724},
    {"nombre":"Cabildo",         "region":"V",   "poblacion":13000,  "lat":-32.412, "lon":-71.085},
    # RM — Metropolitana
    {"nombre":"Santiago",        "region":"RM",  "poblacion":7112808,"lat":-33.447, "lon":-70.673},
    # VI — O'Higgins
    {"nombre":"Rancagua",        "region":"VI",  "poblacion":237685, "lat":-34.170, "lon":-70.744},
    {"nombre":"Machalí",         "region":"VI",  "poblacion":35000,  "lat":-34.177, "lon":-70.646},
    {"nombre":"Rengo",           "region":"VI",  "poblacion":43000,  "lat":-34.414, "lon":-70.863},
]
CIUDAD_DANGER_KM = 10   # relave within this radius → critical risk to population
CIUDAD_ALERT_KM  = 30   # within this radius → elevated risk
CIUDAD_MIN_POP   = 2000 # minimum population to consider

# ─── UTILITIES ────────────────────────────────────────────────────────────────
def haversine(lat1,lon1,lat2,lon2):
    R=6371.0; d2r=math.pi/180
    dlat=(lat2-lat1)*d2r; dlon=(lon2-lon1)*d2r
    a=math.sin(dlat/2)**2+math.cos(lat1*d2r)*math.cos(lat2*d2r)*math.sin(dlon/2)**2
    return 2*R*math.asin(math.sqrt(min(1.0,a)))

def fuzzy(a,b):
    return SequenceMatcher(None,str(a).lower().strip(),str(b).lower().strip()).ratio()

def pf(v,default=0.0):
    try:    return float(v)
    except: return default

def normalize_cluster_id(raw):
    return re.sub(r'\s*\([^)]+\)\s*$','',str(raw)).strip()

def convex_hull_coords(points):
    """Fallback convex hull (used when shapely concave hull fails)."""
    pts=np.array([(p[0],p[1]) for p in points
                  if not (math.isnan(p[0]) or math.isnan(p[1]))])
    if len(pts)==0: return []
    if len(pts)<3:
        c=pts.mean(axis=0); r=0.08
        return [[float(c[0]+r*math.sin(2*math.pi*i/24)),
                 float(c[1]+r*math.cos(2*math.pi*i/24))] for i in range(25)]
    center=pts.mean(axis=0); pts_exp=center+(pts-center)*1.08
    try:
        hull=ConvexHull(pts_exp); verts=pts_exp[hull.vertices]
        return [[float(v[0]),float(v[1])] for v in np.vstack([verts,verts[:1]])]
    except QhullError:
        lo_lat,hi_lat=float(pts[:,0].min()),float(pts[:,0].max())
        lo_lon,hi_lon=float(pts[:,1].min()),float(pts[:,1].max()); buf=0.05
        return [[lo_lat-buf,lo_lon-buf],[hi_lat+buf,lo_lon-buf],
                [hi_lat+buf,hi_lon+buf],[lo_lat-buf,hi_lon+buf],[lo_lat-buf,lo_lon-buf]]

def cluster_hull_coords(points, radius=0.15, min_core_radius=0.18):
    """Organic hull: large overlapping bubbles per installation merge into a smooth
    blob.  A minimum core circle at the centroid is always included, guaranteeing
    a rounded centre even when faenas are sparse or far apart.  No simplify() call
    so the outline stays smooth with no sharp corners."""
    pts = np.array([(p[0], p[1]) for p in points
                    if not (math.isnan(p[0]) or math.isnan(p[1]))])
    if len(pts) == 0: return []
    center = pts.mean(axis=0)
    if len(pts) < 2:
        return [[float(center[0] + min_core_radius*math.sin(2*math.pi*i/64)),
                 float(center[1] + min_core_radius*math.cos(2*math.pi*i/64))] for i in range(65)]
    try:
        RES = 64  # segments per quarter-circle → much smoother curves
        # Use ALL points so every faena gets its own circle
        blob = _shapely_union([_ShapelyPoint(p[0], p[1]).buffer(radius, resolution=RES) for p in pts])
        # Protected core circle at centroid
        core = _ShapelyPoint(float(center[0]), float(center[1])).buffer(min_core_radius, resolution=RES)
        blob = _shapely_union([blob, core])
        # Closing: 0.38° ≈ 42 km radius.  Bridges Antucoya's ~73 km gap from
        # the Centinela complex — the resulting bridge is ~0.40° wide, which
        # survives the opening pass below (needs > 2×0.17 = 0.34°).
        blob = blob.buffer(0.38, resolution=RES).buffer(-0.38, resolution=RES)
        # Fallback: if still disconnected, stitch centroids then re-close
        if blob.geom_type == "MultiPolygon":
            stitches = _shapely_union([g.centroid.buffer(0.30, resolution=RES) for g in blob.geoms])
            blob = _shapely_union([blob, stitches]).buffer(0.05, resolution=RES).buffer(-0.05, resolution=RES)
            if blob.geom_type == "MultiPolygon":
                blob = max(blob.geoms, key=lambda g: g.area)
        # Opening: pulls outline tight like a taut rope
        blob = blob.buffer(-0.17, resolution=RES).buffer(0.17, resolution=RES)
        # If opening severed a bridge, re-stitch once
        if blob.geom_type == "MultiPolygon":
            blob = blob.buffer(0.22, resolution=RES).buffer(-0.12, resolution=RES)
            if blob.geom_type == "MultiPolygon":
                blob = max(blob.geoms, key=lambda g: g.area)
        if blob.is_empty: raise ValueError("empty blob")
        if blob.geom_type == "MultiPolygon":
            blob = max(blob.geoms, key=lambda g: g.area)
        coords = list(blob.exterior.coords)
        return [[float(c[0]), float(c[1])] for c in coords]
    except Exception:
        return convex_hull_coords(points)

def load_csv(path):
    if not os.path.exists(path):
        print(f"  ⚠️  Missing: {os.path.basename(path)}")
        return []
    for enc in ["utf-8-sig","latin-1","cp1252"]:
        try:
            with open(path,newline="",encoding=enc) as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
    return []

# ─── STEP 1: CLUSTER DATA ─────────────────────────────────────────────────────
print("📂 Loading cluster data …")
df_main=pd.read_csv(os.path.join(CLUSTER_DIR,"2_regional_dbcv_hdbs.csv"))
df_main["Latitud"]=pd.to_numeric(df_main["Latitud"],errors="coerce")
df_main["Longitud"]=pd.to_numeric(df_main["Longitud"],errors="coerce")
df_main=df_main.dropna(subset=["Latitud","Longitud"])
df_main=df_main[(df_main["Latitud"]!=0)&(df_main["Longitud"]!=0)]

all_cids=sorted(df_main["Cluster_ID"].unique(),key=lambda x:(x=="Ruido",x))
color_map={"Ruido":"#6b7280"}; cidx=0
for cid in all_cids:
    if cid!="Ruido":
        color_map[cid]=CLUSTER_PALETTE[cidx%len(CLUSTER_PALETTE)]; cidx+=1

# ── FAENA CLUSTER OVERRIDES ───────────────────────────────────────────────────
# Force specific companies' faenas into a given cluster (overrides HDBSCAN assignment).
FAENA_COMPANY_OVERRIDES = {
    "SOCIEDAD CONTRACTUAL MINERA FRANKE": "II-4",  # Mina Franke → II-4 (user override)
    "MINERA HMC S.A.":                    "II-1",  # Faena Michilla → II-1 (user override)
    "MINERA ANTUCOYA LIMITADA":           "II-6",  # Mina Antucoya → Spence cluster (user override)
    "MINERA LUMINA COPPER CHILE LTDA":    "III-3", # Caserones → Atacama interior
    "MINERA LOS PELAMBRES":               "IV-1",  # Faena Los Pelambres → Coquimbo
}
for company, target_cid in FAENA_COMPANY_OVERRIDES.items():
    mask = df_main["NombreEmpresa"].str.upper().str.strip() == company.upper()
    df_main.loc[mask, "Cluster_ID"] = target_cid
    n = mask.sum()
    if n: print(f"   Faena override: {company} → {target_cid} ({n} rows)")

# ── FAENA NAME OVERRIDES ──────────────────────────────────────────────────────
# For CODELCO divisions (same NombreEmpresa) — override by exact faena name.
FAENA_NAME_OVERRIDES = {
    "CODELCO CHILE DIVISION SALVADOR":          "III-1",  # Atacama — División Salvador
    "CODELCO CHILE DIVISION ANDINA":            "V-1",    # Andina → Valparaíso cluster (border zone)
    "DIVISIÓN GABRIELA MISTRAL":                "II-2",   # CODELCO Gaby → Calama cluster
    # SCM EL ABRA already lands in II-2 naturally — no override needed
}
for fname, target_cid in FAENA_NAME_OVERRIDES.items():
    mask = df_main["NombreFaena"].str.upper().str.strip() == fname.upper()
    df_main.loc[mask, "Cluster_ID"] = target_cid
    n = mask.sum()
    if n: print(f"   Faena name override: {fname} → {target_cid} ({n} rows)")

# ── OUTLIER FILTER EXCEPTIONS ─────────────────────────────────────────────────
# Bypass BOTH the OUTLIER_KM AND the secondary stretch filter.
# COMPANY-level: all faenas of that company are exempt (use when the whole mine is displaced).
# FAENA-level: only the named faena(s) are exempt (use when only specific installs are displaced).
OUTLIER_EXEMPT_COMPANIES = {
    "SOCIEDAD CONTRACTUAL MINERA FRANKE",  # All installs registered Region II but physically ~200km south
}
OUTLIER_EXEMPT_FAENAS = {
    "FAENA MICHILLA",          # HMC — 78km from II-3 centroid, valid assignment
    "EXPLORACIONES II REGION", # HMC — exploration, same II-3 belt
}

# ── PER-CLUSTER DISTANCE CAPS ────────────────────────────────────────────────
# Override OUTLIER_KM for specific clusters that need tighter bounds.
# Installations beyond this cap are dropped regardless of company size.
CLUSTER_MAX_KM = {
    "V-0": 60,   # Valparaíso coast — keeps CODELCO Ventanas smelter (59km), drops scattered outliers
    "II-2": 25,  # Calama/Chuquicamata belt — drops Gargamel (36km) and any fringe faenas
}

# ── COMPLETELY EXCLUDED FAENAS ────────────────────────────────────────────────
# Faenas removed from the dashboard entirely — not shown on map, not counted in any cluster.
EXCLUDED_FAENAS = {
    "MINA SANTA ANA",           # INVERSIONES MOYA GUTIERREZ SPA — V-0, isolated outlier
    "MINA SANTA ANA - PUNTO 3", # LUIS ESCOBAR LEON — V-0, isolated outlier
}
if EXCLUDED_FAENAS:
    _excl_upper = {f.upper() for f in EXCLUDED_FAENAS}
    _excl_mask = df_main["NombreFaena"].str.upper().str.strip().isin(_excl_upper)
    n_excl = int(_excl_mask.sum())
    df_main = df_main[~_excl_mask].copy()
    if n_excl: print(f"   Excluded faenas: {n_excl} rows removed ({', '.join(EXCLUDED_FAENAS)})")

# ── RM → V-1 MERGE ───────────────────────────────────────────────────────────
# RM clusters unified and connected to the Valparaíso-Andina cluster (V-1).
for rm_cid in ["RM-0", "RM-2"]:
    n = (df_main["Cluster_ID"] == rm_cid).sum()
    df_main.loc[df_main["Cluster_ID"] == rm_cid, "Cluster_ID"] = "V-1"
    if n: print(f"   RM merge: {rm_cid} → V-1 ({n} rows)")

# ── HIDDEN CLUSTERS ───────────────────────────────────────────────────────────
# Clusters reassigned to Ruido before rendering (dropped from dashboard display).
HIDDEN_CLUSTERS = {"III-3"}
for hcid in list(HIDDEN_CLUSTERS):
    n = (df_main["Cluster_ID"] == hcid).sum()
    df_main.loc[df_main["Cluster_ID"] == hcid, "Cluster_ID"] = "Ruido"
    if n: print(f"   Hidden cluster: {hcid} → Ruido ({n} rows)")

# ─── STEP 2: CLUSTER & FAENA OBJECTS ─────────────────────────────────────────
print("🗺️  Computing cluster area blobs …")
cluster_pts=defaultdict(list); faena_rows=defaultdict(list)
all_installations_raw=[]   # one entry per CSV row, used for map markers

for _,row in df_main.iterrows():
    cid=str(row["Cluster_ID"]); lat,lon=float(row["Latitud"]),float(row["Longitud"])
    cluster_pts[cid].append((lat,lon))
    fid=int(row["IdFaena"])
    inst={
        "lat":lat,"lon":lon,
        "nombre":      str(row.get("NombreFaena","") or ""),
        "nombre_inst": str(row.get("NombreInstalacion","") or ""),
        "empresa":     str(row.get("NombreEmpresa","") or ""),
        "region":      str(row.get("RegionFaena","") or ""),
        "provincia":   str(row.get("ProvinciaFaena","") or ""),
        "comuna":      str(row.get("ComunaFaena","") or ""),
        "categoria":   str(row.get("CategoriaFaena","") or ""),
        "estado":      str(row.get("Estado","") or ""),
        "tipo_inst":   str(row.get("TipoInstalacion","") or ""),
        "recurso":     str(row.get("RecursoMineroInstalacion","") or ""),
        "id_faena":    fid,
        "cluster_id":  cid,
    }
    faena_rows[(cid,fid)].append(inst)
    all_installations_raw.append(inst)

# ── Filter: centroid = mean of per-faena positions (each mine counts once) ────
# Two-pass approach: pass 1 removes gross outliers; pass 2 re-checks with the
# tighter centroid produced after those outliers are gone (avoids centroid drift).
print(f"✂️  Filtering installations > {OUTLIER_KM} km from cluster centroid …")

def _build_centroids(faena_rows_dict, cids):
    """Compute per-cluster centroid as mean of per-faena positions."""
    centroids = {}
    for cid in cids:
        fpos = []
        for (fcid, fid), rows in faena_rows_dict.items():
            if fcid != cid: continue
            fpos.append((sum(r["lat"] for r in rows)/len(rows),
                         sum(r["lon"] for r in rows)/len(rows)))
        if fpos:
            centroids[cid] = (sum(p[0] for p in fpos)/len(fpos),
                               sum(p[1] for p in fpos)/len(fpos))
    return centroids

def _filter_faenas(faena_rows_dict, centroids):
    """Remove faenas whose centroid exceeds the effective_km cap. Returns drop count."""
    _exempt_co = {c.upper() for c in OUTLIER_EXEMPT_COMPANIES}
    _exempt_fn = {f.upper() for f in OUTLIER_EXEMPT_FAENAS}
    dropped = 0
    for key in list(faena_rows_dict.keys()):
        cid, fid = key
        if cid not in centroids: continue
        rows = faena_rows_dict[key]
        flat = sum(r["lat"] for r in rows)/len(rows)
        flon = sum(r["lon"] for r in rows)/len(rows)
        emp = rows[0].get("empresa","").upper().strip() if rows else ""
        nom = rows[0].get("nombre","").upper().strip()  if rows else ""
        if emp in _exempt_co or nom in _exempt_fn: continue
        eff_km = CLUSTER_MAX_KM.get(cid, OUTLIER_KM)
        if haversine(flat, flon, *centroids[cid]) > eff_km:
            del faena_rows_dict[key]; dropped += 1
    return dropped

init_centroids = _build_centroids(faena_rows, all_cids)
removed_f      = _filter_faenas(faena_rows, init_centroids)

# Pass 2 — recompute centroid from survivors, catch anything newly exposed
init_centroids = _build_centroids(faena_rows, all_cids)
removed_f2     = _filter_faenas(faena_rows, init_centroids)
if removed_f2:
    print(f"   2nd-pass (tight centroids): {removed_f2} additional faenas removed")

# ── IQR-based within-cluster outlier removal ──────────────────────────────────
# Removes lone faenas far from the cluster's dense core.
# Threshold = Q75 + IQR_K * IQR, floored at IQR_MIN_KM so small clusters don't over-shrink.
IQR_K       = 1.5
IQR_MIN_KM  = 25.0
_exempt_iqr_co = {c.upper() for c in OUTLIER_EXEMPT_COMPANIES}
_exempt_iqr_fn = {f.upper() for f in OUTLIER_EXEMPT_FAENAS}
_iqr_dropped = 0
for cid in list(all_cids):
    if cid == "Ruido": continue
    keys = [(fcid, fid) for (fcid, fid) in list(faena_rows.keys()) if fcid == cid]
    if len(keys) < 4: continue
    fpos  = [(sum(r["lat"] for r in faena_rows[k])/len(faena_rows[k]),
              sum(r["lon"] for r in faena_rows[k])/len(faena_rows[k])) for k in keys]
    cent  = (sum(p[0] for p in fpos)/len(fpos), sum(p[1] for p in fpos)/len(fpos))
    dists = [haversine(p[0], p[1], *cent) for p in fpos]
    q75   = float(np.percentile(dists, 75))
    q25   = float(np.percentile(dists, 25))
    fence = max(q75 + IQR_K * (q75 - q25), IQR_MIN_KM)
    for key, d in zip(keys, dists):
        rows_k = faena_rows[key]
        emp  = rows_k[0].get("empresa","").upper().strip() if rows_k else ""
        nom  = rows_k[0].get("nombre","").upper().strip()  if rows_k else ""
        if emp in _exempt_iqr_co or nom in _exempt_iqr_fn: continue
        if d > fence:
            del faena_rows[key]; _iqr_dropped += 1
if _iqr_dropped:
    init_centroids = _build_centroids(faena_rows, all_cids)   # refresh after IQR trim
    print(f"   IQR filter (K={IQR_K}, min={IQR_MIN_KM}km): {_iqr_dropped} lone faenas removed")

# Filter individual installation rows (for map markers — each row checked separately)
all_installations=[]; ruido_installations=[]
for inst in all_installations_raw:
    cid=inst["cluster_id"]
    if cid=="Ruido":
        ruido_installations.append({
            "lat":round(inst["lat"],6),"lon":round(inst["lon"],6),
            "nombre":inst["nombre"],"empresa":inst["empresa"],
            "region":inst["region"],"categoria":inst["categoria"],
            "tipo_inst":inst["tipo_inst"],"recurso":inst["recurso"],
            "estado":inst["estado"].upper() if inst["estado"] else "DESCONOCIDO",
        })
        continue
    if cid not in init_centroids: continue
    exempt = (inst.get("empresa","").upper().strip() in {c.upper() for c in OUTLIER_EXEMPT_COMPANIES}
              or inst.get("nombre","").upper().strip() in {f.upper() for f in OUTLIER_EXEMPT_FAENAS})
    _eff_km = CLUSTER_MAX_KM.get(cid, OUTLIER_KM)
    if exempt or haversine(inst["lat"],inst["lon"],*init_centroids[cid])<=_eff_km:
        all_installations.append({
            "lat":        round(inst["lat"],6),
            "lon":        round(inst["lon"],6),
            "nombre":     inst["nombre"],
            "nombre_inst":inst["nombre_inst"],
            "empresa":    inst["empresa"],
            "region":     inst["region"],
            "provincia":  inst["provincia"],
            "comuna":     inst["comuna"],
            "categoria":  inst["categoria"],
            "estado":     inst["estado"].upper() if inst["estado"] else "DESCONOCIDO",
            "tipo_inst":  inst["tipo_inst"],
            "recurso":    inst["recurso"],
            "id_faena":   inst["id_faena"],
            "cluster_id": cid,
        })

# ── Secondary stretch filter ──────────────────────────────────────────────────
# Drop isolated outlier installations (small miners far from centroid that stretch
# the convex hull without contributing meaningful coverage).
# Rule: installation >STRETCH_KM from centroid AND company has ≤2 installs in that cluster.
STRETCH_KM = 80
_exempt_upper = {c.upper() for c in OUTLIER_EXEMPT_COMPANIES}
_cluster_company_count: dict = {}
for _inst in all_installations:
    _k = (_inst["cluster_id"], _inst["empresa"].upper().strip())
    _cluster_company_count[_k] = _cluster_company_count.get(_k, 0) + 1

_stretch_dropped = 0
_all_tight = []
_exempt_upper = {c.upper() for c in OUTLIER_EXEMPT_COMPANIES}
_exempt_fn_upper = {f.upper() for f in OUTLIER_EXEMPT_FAENAS}
for inst in all_installations:
    cid = inst["cluster_id"]
    emp = inst["empresa"].upper().strip()
    nom = inst["nombre"].upper().strip()
    if emp in _exempt_upper or nom in _exempt_fn_upper:
        _all_tight.append(inst); continue
    if cid not in init_centroids:
        _all_tight.append(inst); continue
    d = haversine(inst["lat"], inst["lon"], *init_centroids[cid])
    if d > STRETCH_KM and _cluster_company_count.get((cid, emp), 0) <= 2:
        _stretch_dropped += 1
        continue
    _all_tight.append(inst)
all_installations = _all_tight
print(f"   Stretch filter (>{STRETCH_KM}km, ≤2 installs/company): {_stretch_dropped} removed")

# Rebuild cluster_pts from filtered individual installations (consistent hulls)
cluster_pts=defaultdict(list)
for inst in all_installations:
    cluster_pts[inst["cluster_id"]].append((inst["lat"],inst["lon"]))
print(f"   Faenas filtered: {removed_f} removed — {len(faena_rows)} sidebar groups remain")
print(f"   Installations: {len(all_installations_raw)} → {len(all_installations)} map markers")

clusters={}
for cid in all_cids:
    pts=cluster_pts[cid]
    hull=cluster_hull_coords(pts) if cid!="Ruido" else []
    clat=sum(p[0] for p in pts)/len(pts) if pts else -29.0
    clon=sum(p[1] for p in pts)/len(pts) if pts else -70.0
    prefix=cid.split("-")[0] if cid!="Ruido" else "Ruido"
    rname=REGION_NAMES.get(prefix,prefix)
    sub=cid.split("-")[1] if "-" in cid else ""
    clusters[cid]={
        "id":cid, "region":rname,
        "label":(f"{rname} — Sub-clúster {sub}" if cid!="Ruido"
                 else "Sin Clasificar (Ruido HDBSCAN)"),
        "color":color_map[cid],
        "hull":hull,
        "center":[round(clat,5),round(clon,5)],
        "num_installations":len(pts),
        "top_mine":"",       # filled below
        "top_empresas":[],   # filled below
        "production":{},"water_est":{},"elec_est":{},
        "elec_capacity_mwh":0.0,"water_capacity_m3":0.0,
        "relaves_count":0,"relaves_vol_disponible":0.0,"relaves":[],
    }

# ── Overlap reduction ─────────────────────────────────────────────────────────
# Where two cluster hulls overlap, erode each by a fixed amount to reduce (not
# necessarily eliminate) the overlap.  Only clusters that actually intersect
# another are touched.
_OVERLAP_ERODE = 0.07  # degrees ≈ 7 km shrink per overlapping cluster
_OVERLAP_ERODE_OVERRIDE = {"II-4": 0.02}  # cluster-specific erosion overrides
_hull_geoms: dict = {}
for _cid, _cl in clusters.items():
    if _cid in ("Ruido", "Otros") or len(_cl["hull"]) < 3:
        continue
    try:
        _hull_geoms[_cid] = _ShPoly(_cl["hull"])
    except Exception:
        pass

_erode_set: set = set()
_cids_list = list(_hull_geoms.keys())
for _i in range(len(_cids_list)):
    for _j in range(_i + 1, len(_cids_list)):
        _a = _hull_geoms[_cids_list[_i]]
        _b = _hull_geoms[_cids_list[_j]]
        if _a.intersects(_b) and not _a.touches(_b):
            if _a.intersection(_b).area > 0.001:
                _erode_set.add(_cids_list[_i])
                _erode_set.add(_cids_list[_j])

for _cid in _erode_set:
    _g = _hull_geoms[_cid].buffer(-_OVERLAP_ERODE_OVERRIDE.get(_cid, _OVERLAP_ERODE))
    if not _g.is_empty:
        if _g.geom_type == "MultiPolygon":
            _g = max(_g.geoms, key=lambda g: g.area)
        clusters[_cid]["hull"] = [[float(c[0]), float(c[1])] for c in _g.exterior.coords]
print(f"   Overlap reduction: {len(_erode_set)} clusters eroded ({', '.join(sorted(_erode_set))})")

# Synthetic "Otros" cluster — catch-all for mines that don't belong in any real cluster.
# Assign mines here via MANUAL_OVERRIDES to prevent them from contaminating other clusters.
clusters["Otros"] = {
    "id": "Otros", "region": "—",
    "label": "Otros — Minas no clasificadas",
    "color": "#6b7280",
    "hull": [], "center": [-29.0, -70.0],
    "num_installations": 0, "top_mine": "—", "top_empresas": [],
    "production": {}, "water_est": {}, "elec_est": {},
    "elec_capacity_mwh": 0.0, "water_capacity_m3": 0.0,
    "relaves_count": 0, "relaves_vol_disponible": 0.0, "relaves": [],
}

# ── Nearest city for each cluster ─────────────────────────────────────────────
# Stored as cluster["nearest_city"] / ["nearest_city_km"] for display and
# used as intermediate step in the geographic mine-assignment fallback.
for cid, cluster in clusters.items():
    if cid in ("Ruido", "Otros"):
        cluster["nearest_city"] = None; cluster["nearest_city_km"] = None; continue
    clat, clon = cluster["center"]
    best_d, best_city = float("inf"), None
    for city in CIUDADES_CHILE:
        d = haversine(clat, clon, city["lat"], city["lon"])
        if d < best_d:
            best_d, best_city = d, city
    cluster["nearest_city"]    = best_city["nombre"] if best_city else None
    cluster["nearest_city_km"] = round(best_d, 1)    if best_city else None

# Build reverse index: city name → list of (distance, cid) sorted nearest-first
_city_to_clusters: dict = defaultdict(list)
for cid, cluster in clusters.items():
    if cluster.get("nearest_city"):
        _city_to_clusters[cluster["nearest_city"]].append(
            (cluster["nearest_city_km"], cid))
for name in _city_to_clusters:
    _city_to_clusters[name].sort()

all_faenas=[]
for (cid,fid),rows in faena_rows.items():
    if cid not in clusters: continue
    lat=sum(r["lat"] for r in rows)/len(rows)
    lon=sum(r["lon"] for r in rows)/len(rows)
    estados=[r["estado"].upper() for r in rows if r["estado"]]
    estado=max(set(estados),key=estados.count) if estados else "DESCONOCIDO"
    all_faenas.append({
        "name":rows[0]["nombre"],    # NombreFaena for display
        "id_faena":fid,
        "cluster_id":cid,
        "lat":round(lat,6),"lon":round(lon,6),
        "empresa":rows[0]["empresa"],"region":rows[0]["region"],
        "provincia":rows[0]["provincia"],"comuna":rows[0]["comuna"],
        "categoria":rows[0]["categoria"],"estado":estado,
        "num_installations":len(rows),"match_key":None,"production":{},
    })

# ─── STEP 2b: CATEGORY DIVERSITY + PROCESS TYPE PER CLUSTER ──────────────────
import unicodedata as _ud, math as _math

def _norm(s):
    """Strip accents for robust ASCII substring matching (Ó→O, Á→A …)."""
    return _ud.normalize("NFD", str(s)).encode("ascii","ignore").decode()

def _cat_key(cat_raw):
    c = str(cat_raw).upper()
    if "CATEGORIA A" in c or c == "A": return "A"
    if "CATEGORIA B" in c or c == "B": return "B"
    if "CATEGORIA C" in c or c == "C": return "C"
    if "CATEGORIA D" in c or c == "D": return "D"
    return "SIN"

def _rec_key(rec_raw):
    r = _norm(str(rec_raw)).upper()   # accent-normalised: ÓXIDOS → OXIDOS
    has_ox = "OXID" in r
    has_su = "SULFUR" in r
    if has_ox and has_su: return "Mixto"
    if has_ox:  return "Óxidos"
    if has_su:  return "Sulfuros"
    if r and r != "NAN": return "Polimetálico"
    return None

cluster_cat = defaultdict(lambda: {"A":0,"B":0,"C":0,"D":0,"SIN":0})
cluster_rec = defaultdict(lambda: {"Óxidos":0,"Sulfuros":0,"Mixto":0,"Polimetálico":0})
cluster_tipo = defaultdict(lambda: defaultdict(int))   # TipoInstalacion counts
# Count by INSTALLATION (not faena) — each row in all_installations is one physical installation
for inst in all_installations:
    cid = inst["cluster_id"]
    if cid not in clusters: continue
    # Category: CategoriaFaena — same for all installations of a faena, but we count per inst
    cat = _cat_key(inst.get("categoria",""))
    cluster_cat[cid][cat] += 1
    # Recurso: RecursoMineroInstalacion — varies per installation
    rk = _rec_key(inst.get("recurso",""))
    if rk: cluster_rec[cid][rk] += 1
    # TipoInstalacion breakdown (top types per cluster)
    ti = inst.get("tipo_inst","").strip()
    if ti: cluster_tipo[cid][ti] += 1

for cid, cluster in clusters.items():
    if cid == "Ruido": continue
    cat_d = dict(cluster_cat.get(cid, {"A":0,"B":0,"C":0,"D":0,"SIN":0}))
    rec_d = dict(cluster_rec.get(cid, {"Óxidos":0,"Sulfuros":0,"Mixto":0,"Polimetálico":0}))
    # Shannon diversity index H (on categories A-D only, excludes SIN)
    counts = [v for k,v in cat_d.items() if k != "SIN" and v > 0]
    total  = sum(counts)
    H = -sum((n/total)*_math.log(n/total) for n in counts) if total > 0 else 0.0
    if   total == 0:  div_grade = "Sin datos"
    elif H == 0.0:    div_grade = "Monoproducto"
    elif H < 0.5:     div_grade = "Baja"
    elif H < 1.0:     div_grade = "Media"
    else:             div_grade = "Alta"
    # Top 6 TipoInstalacion for this cluster
    tipo_raw = dict(cluster_tipo.get(cid, {}))
    top_tipo = sorted(tipo_raw.items(), key=lambda x: -x[1])[:6]
    cluster["cat_dist"]        = cat_d
    cluster["recurso_dist"]    = rec_d
    cluster["tipo_dist"]       = dict(top_tipo)
    cluster["diversity_h"]     = round(H, 3)
    cluster["diversity_grade"] = div_grade
print(f"   Category & recurso diversity computed for {sum(1 for c in cluster_cat)} clusters")

# ─── STEP 2c: ACTIVE FAENAS BY CATEGORY + EMPLOYMENT ESTIMATE ────────────────
print("👷 Computing active faenas by category + employment estimates …")
# Workers per faena by category (representative Chilean mining averages)
# Cat A ≥400 workers (real avg ~5,000 for Gran Minería), B 200–400, C ≤80, D ≤12
WORKERS_PER_CAT = {"A": 5000, "B": 300, "C": 40, "D": 6, "SIN": 10}
cluster_active_cat = defaultdict(lambda: {"A":0,"B":0,"C":0,"D":0,"SIN":0})
for _f in all_faenas:
    _cid = _f["cluster_id"]
    if _cid not in clusters: continue
    if _f["estado"].upper() not in ("ACTIVA","ACTIVO"): continue
    _cat = _cat_key(_f.get("categoria",""))
    cluster_active_cat[_cid][_cat] += 1
for cid, cluster in clusters.items():
    if cid in ("Ruido","Otros"): continue
    _ac = dict(cluster_active_cat.get(cid, {"A":0,"B":0,"C":0,"D":0,"SIN":0}))
    cluster["active_faenas_by_cat"] = _ac
    cluster["emp_estimate"] = sum(_ac.get(k,0)*v for k,v in WORKERS_PER_CAT.items())
print(f"   Active faena counts computed for {len(cluster_active_cat)} clusters")

# ─── STEP 3: COMPANY % CONTROL ────────────────────────────────────────────────
print("🏢 Computing company control …")
cluster_empresa_faenas=defaultdict(lambda:defaultdict(set))
for (cid,fid),rows in faena_rows.items():
    emp=rows[0]["empresa"].strip()
    if emp: cluster_empresa_faenas[cid][emp].add(fid)   # count unique IdFaena

for cid,cluster in clusters.items():
    ec={e:len(fs) for e,fs in cluster_empresa_faenas[cid].items()}
    total=sum(ec.values())
    top=sorted(ec.items(),key=lambda x:-x[1])[:6]
    cluster["top_empresas"]=[
        {"empresa":e,"faenas":n,"pct":round(n/total*100,1)} for e,n in top
    ] if total>0 else []
    cluster["total_empresas"]=len(ec)

# ─── STEP 4: PRODUCTION MATCHING ─────────────────────────────────────────────
print("📊 Matching production data …")
df_bridge=pd.read_csv(os.path.join(CLUSTER_DIR,"07_analisis_final_minas_clusters.csv"))
df_prod=pd.read_csv(os.path.join(PROCESSED,"Produccion_Master.csv"))

valid_cids=set(all_cids) | {"Otros"}
mine_to_cluster={}
for _,row in df_bridge.iterrows():
    mk=str(row["Match_Key"]).lower().strip()
    base=normalize_cluster_id(str(row["Cluster_ID_Asignado"]))
    if base not in valid_cids:
        prefix=base.split("-")[0]
        cands=sorted([c for c in valid_cids if c.startswith(prefix+"-") and c!="Ruido"])
        base=cands[0] if cands else None
    if base: mine_to_cluster[mk]=base

# ── MINE LOCATIONS (lat, lon) — definitive geographic coordinates ─────────────
# Used for: (1) geographic cluster-assignment fallback, (2) mine roster display.
# Sources: CMC, SERNAGEOMIN, Cochilco, OpenStreetMap.
MINE_LOCATIONS = {
    # Region XV — Arica y Parinacota
    "pampa camarones":               (-19.043, -70.167),
    # Region I — Tarapacá
    "collahuasi":                    (-20.983, -68.703),
    "cerro colorado":                (-20.457, -69.383),
    "quebrada blanca":               (-20.817, -68.817),
    "atacama kozan":                 (-20.467, -69.717),
    # Region II — Antofagasta
    "escondida":                     (-24.267, -69.050),
    "spence":                        (-22.617, -69.200),
    "zaldivar":                      (-24.333, -68.983),
    "lomas bayas":                   (-23.600, -70.083),
    "michilla":                      (-23.167, -70.617),
    "mantos blancos":                (-23.033, -70.467),
    "centinela_centinela_sulfuros_": (-22.367, -68.783),
    "centinela_centinela_óxidos_":   (-22.383, -68.817),
    "antucoya":                      (-23.783, -69.400),
    "el abra":                       (-21.700, -68.600),
    "sierra gorda":                  (-22.817, -69.367),
    "chuquicamata":                  (-22.317, -68.917),
    "radomiro tomic":                (-22.200, -69.017),
    "ministro hales":                (-22.350, -68.883),
    "gabriela mistral":              (-23.183, -69.150),
    # Region III — Atacama
    "salvador":                      (-26.250, -69.533),
    "caserones":                     (-27.133, -69.183),
    "capstone copper (4)":           (-27.967, -70.883),
    "mantoverde":                    (-27.967, -70.883),
    "candelaria":                    (-27.517, -70.583),
    "franke":                        (-27.383, -70.250),
    "haldeman":                      (-26.183, -70.417),
    "cerro negro":                   (-26.917, -70.317),
    # Region IV — Coquimbo
    "los pelambres":                 (-31.817, -70.783),
    "andacollo":                     (-30.233, -71.067),
    "tres valles":                   (-31.533, -71.267),
    "altos de punitaqui":            (-30.767, -71.467),
    # Region V — Valparaíso
    "andina":                        (-33.167, -70.283),
    "los bronces":                   (-33.167, -70.317),
    "el soldado":                    (-32.567, -70.967),
    # Region VI — O'Higgins
    "el teniente":                   (-34.167, -70.567),
}

# ── MANUAL OVERRIDES ─────────────────────────────────────────────────────────
# Each override is sourced from the Cluster_ID_Final assigned to that mine's
# CATEGORIA A faena in cluster_final_dashboard_full.csv.  Bridge file
# naming (e.g. "CODELCO CHILE DIVISION X") often fails fuzzy match, and the
# bridge itself may assign the wrong cluster.  Overrides always win over bridge.
MANUAL_OVERRIDES = {
    # ── Region I — Tarapacá ──────────────────────────────────────────────────
    "collahuasi":                    "I-0",    # faena UJINA (Collahuasi SCM) → I-0; bridge wrongly I-1
    "quebrada blanca":               "I-0",    # faena QUEBRADA BLANCA (Teck) → I-0; bridge wrongly I-1
    "cerro colorado":                "I-1",    # faena MINA CERRO COLORADO → I-1; bridge wrongly I-0
    # ── Region II — Antofagasta ──────────────────────────────────────────────
    "chuquicamata":                  "II-2",   # faena CODELCO CHILE DIVISION CHUQUICAMATA → II-2
    "radomiro tomic":                "II-2",   # faena CODELCO CHILE DIVISION RADOMIRO TOMIC → II-2
    "ministro hales":                "II-2",   # faena CODELCO CHILE DIVISIÓN MINISTRO HALES → II-2
    "gabriela mistral":              "II-2",   # CODELCO Gaby — faena in Ruido, geographically Calama
    "el abra":                       "II-2",   # faena EL ABRA (SCM El Abra) → II-2
    "escondida":                     "II-0",   # faena MINA ESCONDIDA → II-0
    "zaldivar":                      "II-0",   # faena ZALDIVAR → II-0
    "centinela_centinela_óxidos_":   "II-6",   # faena CENTINELA OXIDO → II-6
    "centinela_centinela_sulfuros_": "II-6",   # faena CENTINELA SULFUROS → II-6
    "spence":                        "II-6",   # faena MINA SPENCE → II-6
    "sierra gorda":                  "II-6",   # faena SIERRA GORDA (SCM Sierra Gorda) → II-6; bridge wrongly II-5
    "antucoya":                      "II-6",   # faena MINA ANTUCOYA → II-6
    "franke":                        "II-4",   # faena MINA FRANKE → II-4 (user override)
    "mantos blancos":                "II-5",   # faena MANTOS BLANCOS (Mantos Copper) → II-5; bridge wrongly II-1
    "michilla":                      "II-1",   # faena FAENA MICHILLA (HMC) → II-1 (user override)
    "lomas bayas":                   "II-3",   # faena in Ruido; geographically nearest II-3
    # ── Region III — Atacama ─────────────────────────────────────────────────
    "salvador":                      "III-1",  # faena CODELCO CHILE DIVISION SALVADOR → III-1; bridge wrongly III-0
    "mantoverde":                    "III-1",  # faena MANTO VERDE → III-1
    "capstone copper (4)":           "III-1",  # Capstone Copper umbrella (same complex as mantoverde)
    # ── Region V — Valparaíso ────────────────────────────────────────────────
    "el soldado":                    "V-0",    # faena DIVISION EL SOLDADO → V-0; bridge wrongly V-1
    "cerro negro":                   "V-0",    # faena CERRO NEGRO → V-0; bridge wrongly V-1
    # ── Región Metropolitana ─────────────────────────────────────────────────
    "andina":                        "V-1",    # faena CODELCO CHILE DIVISION ANDINA → V-1
    "los bronces":                   "RM-0",   # faena LOS BRONCES-LAS TÓRTOLAS → RM-0
    # ── Region VI — O'Higgins ────────────────────────────────────────────────
    "el teniente":                   "VI-0",   # faena CODELCO CHILE DIVISION EL TENIENTE → VI-0
    # ── Geographically misassigned ───────────────────────────────────────────
    "haldeman":                      "Otros",  # Region III mine (lat -26.2), wrongly in I-0 (Tarapacá)
    "atacama kozan":                 "II-1",   # Coordinates in Region I/II area (not III where bridge puts it)
}
for mk, cid in MANUAL_OVERRIDES.items():
    if cid in valid_cids:
        mine_to_cluster[mk] = cid
# "Otros" Excel column is not in the bridge file — register manually
mine_to_cluster["otros_excel"] = "Otros"
print(f"   Applied {len(MANUAL_OVERRIDES)} manual overrides")

faena_name_pairs=[(str(r["NombreFaena"]).lower(),str(r["Cluster_ID"]))
                  for _,r in df_main.drop_duplicates("NombreFaena").iterrows()]

mine_prod=defaultdict(dict)
for _,row in df_prod.iterrows():
    mk=str(row["Match_Key"]).lower().strip()
    mine_prod[mk][int(row["Anio"])]=pf(row.get("Produccion"))

cluster_prod=defaultdict(lambda:defaultdict(float))
matched={}
for mk,by_year in mine_prod.items():
    cid=None
    if mk in mine_to_cluster:
        cid=mine_to_cluster[mk]
    else:
        best_s,best_mk=0,None
        for k in mine_to_cluster:
            s=fuzzy(mk,k)
            if s>best_s: best_s,best_mk=s,k
        if best_s>=0.75:
            cid=mine_to_cluster[best_mk]
        else:
            best_s,best_cid=0,None
            for fname,fcid in faena_name_pairs:
                s=fuzzy(mk,fname)
                if s>best_s: best_s,best_cid=s,fcid
            if best_s>=0.70: cid=best_cid
    if cid and cid in clusters:
        matched[mk]=cid
        for yr,p in by_year.items(): cluster_prod[cid][yr]+=p

for cid,cluster in clusters.items():
    by_yr=dict(cluster_prod[cid])
    cluster["production"]={str(y):round(v,3) for y,v in sorted(by_yr.items())}
    cluster["water_est"]={str(y):round(v*1000*WATER_M3_PER_TON,0) for y,v in sorted(by_yr.items())}
    cluster["elec_est"]={str(y):round(v*1000*ELEC_MWH_PER_TON,0)  for y,v in sorted(by_yr.items())}

# ── City-mediated mine → cluster assignment for ALL production mines ────────────
# For every mine in MINE_LOCATIONS with production data:
#   1) find its nearest city, 2) find the cluster whose centroid is nearest that city,
#   3) assign the mine there (overrides previous assignment if the city route gives
#      a better geographic fit).
# Mines already in MANUAL_OVERRIDES keep their override — city route only applies
# to mines NOT explicitly listed there.
geo_matched = 0
for mk, (lat, lon) in MINE_LOCATIONS.items():
    if mk in MANUAL_OVERRIDES:
        continue  # explicit override wins — do not city-reassign
    if mk not in mine_prod:
        continue  # no production data

    # Step 1 — mine's nearest city
    mine_best_d_city, mine_nearest_city = float("inf"), None
    for city in CIUDADES_CHILE:
        d = haversine(lat, lon, city["lat"], city["lon"])
        if d < mine_best_d_city:
            mine_best_d_city, mine_nearest_city = d, city["nombre"]

    # Step 2 — cluster that shares that nearest city (pick the spatially closest one)
    best_d, best_cid = float("inf"), None
    if mine_nearest_city and mine_nearest_city in _city_to_clusters:
        for _cd, cid in _city_to_clusters[mine_nearest_city]:
            d = haversine(lat, lon, clusters[cid]["center"][0], clusters[cid]["center"][1])
            if d < best_d:
                best_d, best_cid = d, cid

    # Step 3 — direct-distance fallback if no city match
    if best_cid is None:
        for cid, cluster in clusters.items():
            if cid in ("Ruido", "Otros"): continue
            d = haversine(lat, lon, cluster["center"][0], cluster["center"][1])
            if d < best_d:
                best_d, best_cid = d, cid

    if best_d <= 150 and best_cid:
        matched[mk] = best_cid
        mine_to_cluster[mk] = best_cid
        for yr, p in mine_prod[mk].items():
            cluster_prod[best_cid][yr] += p
        geo_matched += 1
        city_tag = f" via {mine_nearest_city}" if mine_nearest_city else ""
        print(f"   Geo-match: {mk} → {best_cid} ({best_d:.0f} km{city_tag})")

# Refresh cluster production dicts with geographic additions
for cid, cluster in clusters.items():
    by_yr = dict(cluster_prod[cid])
    cluster["production"]    = {str(y): round(v, 3) for y, v in sorted(by_yr.items())}
    cluster["water_est"]     = {str(y): round(v*1000*WATER_M3_PER_TON, 0) for y, v in sorted(by_yr.items())}
    cluster["elec_est"]      = {str(y): round(v*1000*ELEC_MWH_PER_TON, 0)  for y, v in sorted(by_yr.items())}
print(f"   Geographic fallback: {geo_matched} new mine-cluster assignments")

# ─── STEP 4b: MONTHLY PRODUCTION DATA ────────────────────────────────────────
print("📅 Loading monthly production data …")
MONTHLY_MINE_MAP = {
    "Chuquicamata":         "chuquicamata",
    "Radomiro Tomic":       "radomiro tomic",
    "Ministro Hales":       "ministro hales",
    "Salvador":             "salvador",
    "Andina":               "andina",
    "El Teniente":          "el teniente",
    "Gabriela Mistral":     "gabriela mistral",
    "Escondida":            "escondida",
    "Spence":               "spence",
    "Cerro Colorado":       "cerro colorado",
    "Lomas Bayas":          "lomas bayas",
    "Collahuasi":           "collahuasi",
    "Los Bronces":          "los bronces",
    "El Soldado":           "el soldado",
    "El Abra":              "el abra",
    "Candelaria":           "candelaria",
    "Caserones":            "caserones",
    "Mantos Blancos":       "mantos blancos",
    "Mantoverde":           "mantoverde",
    "Capstone Copper":      "capstone copper (4)",
    "Los Pelambres":        "los pelambres",
    "Zaldívar":             "zaldivar",
    "Centinela (súlfuros)": "centinela_centinela_sulfuros_",
    "Centinela (óxidos)":   "centinela_centinela_óxidos_",
    "Antucoya":             "antucoya",
    "Quebrada Blanca":      "quebrada blanca",
    "Andacollo":            "andacollo",
    "Michilla":             "michilla",
    "Haldeman":             "haldeman",
    "Sierra Gorda":         "sierra gorda",
    "Atacama Kozan":        "atacama kozan",
    "Tres Valles":          "tres valles",
    "Franke":               "franke",
    "Altos de Punitaqui":   "altos de punitaqui",
    "Cerro Negro":          "cerro negro",
    "Pampa Camarones":      "pampa camarones",
    "Otros":                "otros_excel",      # aggregated "Otros" column → cluster Otros
}
try:
    df_mon_raw = pd.read_excel(os.path.join(RAW_DIR,"produccionMensual.xlsx"), header=None)
    # Row 6 = column headers (mine names), rows 7+ = data
    header_row = df_mon_raw.iloc[6].tolist()
    # Build col_idx → cluster_id map
    mon_col_to_cid = {}
    for i, col_name in enumerate(header_row):
        mk = MONTHLY_MINE_MAP.get(str(col_name).strip())
        if mk and mk in mine_to_cluster:
            mon_col_to_cid[i] = mine_to_cluster[mk]
    cluster_prod_mon = defaultdict(lambda: defaultdict(float))
    import datetime as _dt
    for _, row in df_mon_raw.iloc[7:].iterrows():
        date_val = row.iloc[0]
        # Accept both datetime.datetime and pd.Timestamp; skip year-only subtotal rows
        if not isinstance(date_val, (_dt.datetime, pd.Timestamp)): continue
        date_str = pd.Timestamp(date_val).strftime("%Y-%m")
        for col_idx, cid in mon_col_to_cid.items():
            val = pf(row.iloc[col_idx])
            if val and val > 0:
                cluster_prod_mon[cid][date_str] += val
    for cid, cluster in clusters.items():
        by_date = dict(cluster_prod_mon.get(cid,{}))
        cluster["production_monthly"] = {k: round(v,3) for k,v in sorted(by_date.items())}
    n_mon = sum(len(v) for v in cluster_prod_mon.values())
    print(f"   Monthly data: {n_mon} cluster-month values across {len(cluster_prod_mon)} clusters")
except Exception as e:
    print(f"   ⚠ Monthly data skipped: {e}")
    for cid, cluster in clusters.items():
        cluster["production_monthly"] = {}

# ─── STEP 4c: DERECHOS DE AGUA (DGA) ─────────────────────────────────────────
print("🌊 Loading Derechos de Agua …")
AGUA_RADIUS_KM = 150

def _utm_to_latlon_vec(E_arr, N_arr, zone_arr):
    """Vectorized UTM → decimal lat/lon (WGS84, Southern hemisphere)."""
    a = 6378137.0; e2 = 0.00669437999014; k0 = 0.9996
    e_prime2 = e2 / (1 - e2)
    lon0 = np.radians((zone_arr.astype(float) - 1) * 6 - 180 + 3)
    x = E_arr - 500000.0
    y = N_arr - 10000000.0
    M = y / k0
    e1 = (1 - np.sqrt(1 - e2)) / (1 + np.sqrt(1 - e2))
    mu = M / (a * (1 - e2/4 - 3*e2**2/64 - 5*e2**3/256))
    phi1 = (mu + (3*e1/2 - 27*e1**3/32)*np.sin(2*mu)
               + (21*e1**2/16 - 55*e1**4/32)*np.sin(4*mu)
               + (151*e1**3/96)*np.sin(6*mu) + (1097*e1**4/512)*np.sin(8*mu))
    N1 = a / np.sqrt(1 - e2*np.sin(phi1)**2)
    T1 = np.tan(phi1)**2; C1 = e_prime2 * np.cos(phi1)**2
    R1 = a * (1 - e2) / (1 - e2*np.sin(phi1)**2)**1.5
    D = x / (N1 * k0)
    lat = phi1 - (N1*np.tan(phi1)/R1) * (D**2/2 - (5+3*T1+10*C1-4*C1**2-9*e_prime2)*D**4/24)
    lon = lon0 + (D - (1+2*T1+C1)*D**3/6) / np.cos(phi1)
    return np.degrees(lat), np.degrees(lon)

AGUA_UNIT_TO_LS = {
    'Lt/s':1.0,'l/s':1.0,'lts/s':1.0,
    'm3/s':1000.0,
    'm3/año':1000.0/(365.25*24*3600), 'm3/año':1000.0/(365.25*24*3600),
    'Mm3/año':1e9/(365.25*24*3600),
    'Lt/min':1/60,'l/min':1/60,
    'm3/h':1000/3600,'m3/hora':1000/3600,
    'm3/mes':1000/(30.44*24*3600),
    'm3/dia':1000/(24*3600),'m3/día':1000/(24*3600),
    'Lt/h':1/3600,
    'm3/min':1000/60,
}

try:
    _agua_cols = {
        'Uso del Agua':'uso','Tipo Derecho':'tipo',
        'Naturaleza del Agua':'naturaleza',
        'UTM \nNorte \nCaptación\n(m)':'utm_n',
        'UTM \nEste \nCaptación\n(m)':'utm_e',
        'Huso':'huso',
        'Caudal \nAnual\nProm \n':'caudal',
        'Unidad de \nCaudal':'unidad',
        'Año':'anio',
    }
    df_agua = pd.read_excel(
        os.path.join(SHARED,"DerechosAgua.xlsx"), header=6,
        usecols=list(_agua_cols.keys())
    ).rename(columns=_agua_cols)

    utm_n = pd.to_numeric(df_agua['utm_n'], errors='coerce')
    utm_e = pd.to_numeric(df_agua['utm_e'], errors='coerce')
    huso  = pd.to_numeric(df_agua['huso'].astype(str).str.strip(), errors='coerce').fillna(19).clip(18,19)
    valid = (utm_n >= 3.5e6) & (utm_n <= 7.9e6) & (utm_e >= 2e5) & (utm_e <= 8e5)
    df_v = df_agua[valid].copy()
    df_v['_n'] = utm_n[valid].values; df_v['_e'] = utm_e[valid].values
    df_v['_z'] = huso[valid].values.astype(int)

    lats, lons = _utm_to_latlon_vec(df_v['_e'].values.astype(float),
                                     df_v['_n'].values.astype(float),
                                     df_v['_z'].values)
    df_v['lat'] = lats; df_v['lon'] = lons
    geo_ok = (df_v['lat']>-56)&(df_v['lat']<-17)&(df_v['lon']>-76)&(df_v['lon']<-63)
    df_v = df_v[geo_ok].copy()

    # Vectorized haversine assignment to nearest cluster
    _R = 6371.0
    cid_list_a = [c for c in clusters if c != 'Ruido']
    _cen = np.deg2rad(np.array([clusters[c]['center'] for c in cid_list_a]))
    _pts = np.deg2rad(df_v[['lat','lon']].values)
    _dlat = _pts[:,0:1] - _cen[:,0]; _dlon = _pts[:,1:2] - _cen[:,1]
    _ah = np.sin(_dlat/2)**2 + np.cos(_pts[:,0:1])*np.cos(_cen[:,0])*np.sin(_dlon/2)**2
    _dist = 2*_R*np.arcsin(np.sqrt(np.clip(_ah,0,1)))
    _nidx = np.argmin(_dist, axis=1); _ndist = _dist[np.arange(len(_dist)), _nidx]
    df_v = df_v[_ndist <= AGUA_RADIUS_KM].copy()
    df_v['assigned_cid'] = np.array(cid_list_a)[_nidx[_ndist <= AGUA_RADIUS_KM]]

    # Normalize columns
    df_v['tipo'] = df_v['tipo'].astype(str).str.strip()
    df_v['nat_clean'] = df_v['naturaleza'].astype(str).apply(
        lambda x: 'Subterránea' if 'ubterr' in x else ('Superficial' if 'uperficial' in x else x.strip()))
    df_v['uso'] = df_v['uso'].astype(str).str.strip().replace({'nan':'','NaN':'','None':''})
    caudal_raw = pd.to_numeric(df_v['caudal'].astype(str).str.replace(',','.', regex=False), errors='coerce')
    factor = df_v['unidad'].astype(str).str.strip().map(AGUA_UNIT_TO_LS).fillna(0.0)
    df_v['flow_ls'] = (caudal_raw * factor).clip(lower=0)
    anio_n = pd.to_numeric(df_v['anio'], errors='coerce')
    df_v['anio_int'] = anio_n.where((anio_n>=1990)&(anio_n<=2025))

    for cid in cid_list_a:
        sub = df_v[df_v['assigned_cid']==cid]
        if len(sub)==0:
            clusters[cid]['agua']={'count':0,'tipo':{},'naturaleza':{},'uso':{},'total_ls':0.0,'by_year':{}}
            continue
        tipo_c  = {str(k):int(v) for k,v in sub['tipo'].value_counts().items()}
        nat_c   = {str(k):int(v) for k,v in sub['nat_clean'].value_counts().items()}
        uso_c   = {str(k):int(v) for k,v in sub[sub['uso']!='']['uso'].value_counts().head(6).items()}
        total_ls= float(sub['flow_ls'].fillna(0).sum())
        yr_c    = {str(int(k)):int(v) for k,v in sub['anio_int'].dropna()
                       .astype(int).value_counts().sort_index().items()}
        clusters[cid]['agua']={
            'count':int(len(sub)),'tipo':tipo_c,'naturaleza':nat_c,
            'uso':dict(sorted(uso_c.items(),key=lambda x:-x[1])),
            'total_ls':round(total_ls,1),'by_year':yr_c,
        }
    print(f"   Derechos de Agua: {len(df_v)} registros → {sum(1 for c in cid_list_a if clusters[c].get('agua',{}).get('count',0)>0)} clústeres")
except Exception as e:
    import traceback; traceback.print_exc()
    print(f"   ⚠ Derechos de Agua skipped: {e}")
    for cid, cluster in clusters.items():
        cluster['agua']={'count':0,'tipo':{},'naturaleza':{},'uso':{},'total_ls':0.0,'by_year':{}}

# ─── STEP 4d: PRODUCTION RANKING BY COMPANY ────────────────────────────────────
print("🏭 Company production ranking …")
df_meta = pd.read_csv(os.path.join(PROCESSED,"metadata_minas.csv"))
_mine_holding = {}
for _, _mr in df_meta.iterrows():
    _mk = str(_mr.get('Mine','')).lower().strip()
    _h  = str(_mr.get('Holding', _mr.get('Owner',''))).strip()
    if _mk and _mk != 'nan': _mine_holding[_mk] = _h

_PROD_YEARS = list(range(2020,2026))
cluster_prod_by_co = defaultdict(lambda: defaultdict(float))
for mk, cid in matched.items():
    _h = _mine_holding.get(mk)
    if not _h:
        _best_s, _best_h = 0, None
        for _m, _hh in _mine_holding.items():
            _s = fuzzy(mk, _m)
            if _s > _best_s: _best_s, _best_h = _s, _hh
        _h = _best_h if _best_s >= 0.7 else 'Otros'
    for yr in _PROD_YEARS:
        p = mine_prod[mk].get(yr, 0)
        if p: cluster_prod_by_co[cid][_h] += p

for cid, cluster in clusters.items():
    if cid == 'Ruido': continue
    co_prod = cluster_prod_by_co.get(cid, {})
    total   = sum(co_prod.values())
    ranked  = sorted(co_prod.items(), key=lambda x: -x[1])
    cluster['prod_by_company'] = [
        {'co': co, 'kt_avg': round(kt/len(_PROD_YEARS), 1),
         'pct': round(kt/total*100, 1) if total>0 else 0}
        for co, kt in ranked[:6]
    ]
print(f"   Company prod ranking: {len(cluster_prod_by_co)} clusters")

# ─── STEP 4d-bis: MINE ROSTER PER CLUSTER ─────────────────────────────────────
print("📋 Building mine roster per cluster …")
_ROSTER_YEARS = list(range(2020, 2026))
cluster_mine_roster = defaultdict(list)
for mk, cid in matched.items():
    avg_p = sum(mine_prod[mk].get(y, 0) for y in _ROSTER_YEARS) / len(_ROSTER_YEARS)
    holding = _mine_holding.get(mk)
    if not holding:
        for _m, _h in _mine_holding.items():
            if fuzzy(mk, _m) >= 0.7: holding = _h; break
    holding = holding or "Otros"
    peak_p = max((mine_prod[mk].get(y, 0) for y in mine_prod[mk]), default=0)
    lat, lon = MINE_LOCATIONS.get(mk, (None, None))
    cluster_mine_roster[cid].append({
        "name":    mk.title(),
        "mk":      mk,
        "holding": holding,
        "avg_prod": round(avg_p, 1),
        "peak_prod": round(peak_p, 1),
        "lat": lat, "lon": lon,
    })

for cid, cluster in clusters.items():
    if cid == "Ruido": continue
    roster = sorted(cluster_mine_roster.get(cid, []), key=lambda r: -r["avg_prod"])
    total_cl = sum(r["avg_prod"] for r in roster)
    for r in roster:
        r["pct"] = round(r["avg_prod"] / total_cl * 100, 1) if total_cl > 0 else 0
    cluster["mine_roster"] = roster
print(f"   Mine roster: {sum(len(c.get('mine_roster',[])) for c in clusters.values())} mine-cluster pairs")

# ─── STEP 4e: DIFFERENTIATED WATER ESTIMATES ──────────────────────────────────
# Mine-type weighted water factor per cluster.
# Sources: Cochilco "Consumo de agua en la minería del cobre" 2023/2024
#   Sulfide flotation (national avg):  ~90-95 m³/t Cu  (Escondida ~82.7, industry ~92.9)
#   Oxide SX-EW:                       ~35 m³/t Cu     (hydromet — confirmed Cochilco)
#   Mixed operations:                  ~60 m³/t Cu     (blended sulfide + oxide)
#   Smelter/Fundición:                 ~80 m³/t Cu     (Codelco benchmark)
# NOTE: Previous values (Sulfuros=280, Mixto=140) were outlier-mine figures
#   (Sierra Gorda ~280.7, Salvador ~369.8) — NOT national averages.
#   Using them inflated cluster water demand ~3× and made desal coverage unrealistically low.
WATER_FACTOR = {'Sulfuros':93.0,'Oxidos':35.0,'Mixto':60.0,'Fundicion':80.0}
WATER_FACTOR_DEFAULT = 90.0

_mine_type_map = {}
for _, _mr in df_meta.iterrows():
    _mk = str(_mr.get('Mine','')).lower().strip()
    _t  = str(_mr.get('Type','')).strip()
    if _mk and _mk != 'nan': _mine_type_map[_mk] = _t

for cid, cluster in clusters.items():
    if cid == 'Ruido': continue
    by_yr = dict(cluster_prod[cid])
    if not by_yr: continue
    mines_in_cl = [mk for mk, c in matched.items() if c == cid]
    total_w = 0.0; wf_sum = 0.0
    for mk in mines_in_cl:
        avg_p = sum(mine_prod[mk].get(y, 0) for y in range(2020, 2025)) / 5.0
        mtype = _mine_type_map.get(mk)
        if not mtype:
            for _m, _t2 in _mine_type_map.items():
                if fuzzy(mk, _m) >= 0.75: mtype = _t2; break
        wf_sum += avg_p * WATER_FACTOR.get(mtype, WATER_FACTOR_DEFAULT)
        total_w += avg_p
    wf = round(wf_sum / total_w, 1) if total_w > 0 else WATER_FACTOR_DEFAULT
    cluster['water_est']   = {str(y): round(v*1000*wf, 0) for y,v in sorted(by_yr.items())}
    cluster['water_factor'] = wf
print(f"   Water factors: {sorted({c.get('water_factor',0) for c in clusters.values() if c.get('water_factor')})}")

# Per-faena production
for faena in all_faenas:
    nc=faena["name"].lower().strip()
    for mk,cid in matched.items():
        if cid==faena["cluster_id"] and fuzzy(nc,mk)>=0.75:
            faena["match_key"]=mk
            faena["production"]={str(y):round(v,3) for y,v in mine_prod[mk].items()}
            break

# ─── Mine segmentation + trend per cluster ────────────────────────────────────
GRAN_KT  = 400   # kt/yr threshold Gran minería
MED_KT   = 50    # kt/yr threshold Mediana / Pequeña
cluster_seg   = defaultdict(lambda: {"Gran":0,"Mediana":0,"Pequeña":0})
cluster_trend = defaultdict(list)
for mk, cid in matched.items():
    recent = {y: mine_prod[mk][y] for y in range(2019,2025) if y in mine_prod[mk]}
    if not recent: continue
    max_p = max(recent.values())
    key = "Gran" if max_p >= GRAN_KT else ("Mediana" if max_p >= MED_KT else "Pequeña")
    cluster_seg[cid][key] += 1
    sy = sorted(recent.items())
    if len(sy) >= 3:
        early = sum(v for _,v in sy[:2])/2; late = sum(v for _,v in sy[-2:])/2
        if early>0: cluster_trend[cid].append((late-early)/early*100)
for cid,cluster in clusters.items():
    if cid=="Ruido": continue
    # Use catastro-based counts (active_faenas_by_cat) for Gran/Mediana/Pequeña —
    # more comprehensive than production-matched mines (which only cover ~26 tracked mines).
    _ac = cluster.get("active_faenas_by_cat", {})
    seg = {
        "Gran":    _ac.get("A", 0),
        "Mediana": _ac.get("B", 0),
        "Pequeña": _ac.get("C", 0) + _ac.get("D", 0),
    }
    trends = cluster_trend.get(cid,[])
    avg_t  = sum(trends)/len(trends) if trends else None
    cluster["mine_segments"] = seg
    cluster["mine_count"]    = sum(seg.values())
    cluster["trend_label"]   = ("Creciendo" if avg_t and avg_t>5 else
                                 "Declinando" if avg_t and avg_t<-5 else
                                 "Estable" if avg_t is not None else "—")
    cluster["trend_pct"]     = round(avg_t,1) if avg_t is not None else None
print(f"   Mine segments (catastro-based) computed for {sum(1 for c in clusters.values() if c.get('mine_segments'))} clusters")

# ─── Build cluster → company group mapping (for desaladora matching) ──────────
cluster_company_groups = defaultdict(set)  # cid → set of company_tokens
for mk, cid in matched.items():
    for comp_tok, mine_keys in COMPANY_MINE_MAP.items():
        if any(mk_part in mk.lower() for mk_part in mine_keys):
            cluster_company_groups[cid].add(comp_tok)
print(f"   Company-cluster groups: {sum(len(v) for v in cluster_company_groups.values())} assignments")

# ─── STEP 5: CLUSTER NAMING FROM TOP MINE ────────────────────────────────────
print("🏷️  Naming clusters from top producer …")
cluster_top_prod=defaultdict(float)
cluster_top_name={}
for mk,cid in matched.items():
    for yr in [2025,2024,2023,2022,2021,2020]:
        if yr in mine_prod[mk]:
            p=mine_prod[mk][yr]
            if p>cluster_top_prod[cid]:
                cluster_top_prod[cid]=p
                cluster_top_name[cid]=mk.title()
            break

for cid,cluster in clusters.items():
    if cid in cluster_top_name and cluster_top_prod[cid]>0:
        cluster["top_mine"]=cluster_top_name[cid]
    else:
        cl_faenas=[f for f in all_faenas if f["cluster_id"]==cid]
        if cl_faenas:
            top=max(cl_faenas,key=lambda f:f["num_installations"])
            cluster["top_mine"]=top["name"][:35]
        else:
            cluster["top_mine"]=cid

# ─── STEP 6: RELAVES ─────────────────────────────────────────────────────────
print("♻️  Loading relaves …")
df_rel=pd.read_csv(os.path.join(SHARED,"CATASTRO_RELAVES_CHILE_OCT2025.csv"),encoding="utf-8-sig")
df_rel["LATITUD"]=pd.to_numeric(df_rel["LATITUD"],errors="coerce")
df_rel["LONGITUD"]=pd.to_numeric(df_rel["LONGITUD"],errors="coerce")
df_rel=df_rel.dropna(subset=["LATITUD","LONGITUD"])
relaves_all=[]
for _,row in df_rel.iterrows():
    lat,lon=float(row["LATITUD"]),float(row["LONGITUD"])
    va=pf(row.get("VOL_AUTORIZADO")); vac=pf(row.get("VOL_ACTUAL"))
    relaves_all.append({
        "empresa":str(row.get("NOMBRE_EMPRESA_O_PRODUCTOR_MINERO","") or ""),
        "faena":str(row.get("NOMBRE_FAENA","") or ""),
        "instalacion":str(row.get("NOMBRE_INSTALACION","") or ""),
        "tipo":str(row.get("TIPO_DEPOSITO","") or ""),
        "estado":str(row.get("ESTADO_INSTALACION","") or "").upper(),
        "recurso":str(row.get("RECURSO","") or ""),
        "vol_autorizado":va,"vol_actual":vac,
        "vol_disponible":round(max(0.0,va-vac),0),
        "lat":round(lat,6),"lon":round(lon,6),
    })
cluster_relaves=defaultdict(list)
for rel in relaves_all:
    bd,bc=float("inf"),None
    for cid,cluster in clusters.items():
        if cid=="Ruido": continue
        d=haversine(rel["lat"],rel["lon"],cluster["center"][0],cluster["center"][1])
        if d<bd: bd,bc=d,cid
    if bc and bd<RELAVE_RADIUS_KM:
        cluster_relaves[bc].append({**rel,"dist_km":round(bd,1)})
for cid,rlist in cluster_relaves.items():
    clusters[cid]["relaves"]=rlist
    clusters[cid]["relaves_count"]=len(rlist)
    clusters[cid]["relaves_vol_disponible"]=round(sum(r["vol_disponible"] for r in rlist),0)

# ── Per-relave: city proximity risk ──────────────────────────────────────────
print("🏘️  Computing relaves → city proximity …")
_ciud_filt = [c for c in CIUDADES_CHILE if c["poblacion"] >= CIUDAD_MIN_POP]
_rel_danger_count = 0
for rel in relaves_all:
    _best_d, _best_c = float("inf"), None
    for _c in _ciud_filt:
        _d = haversine(rel["lat"], rel["lon"], _c["lat"], _c["lon"])
        if _d < _best_d:
            _best_d, _best_c = _d, _c
    if _best_c and _best_d <= CIUDAD_ALERT_KM:
        rel["ciudad_km"]   = round(_best_d, 1)
        rel["ciudad_nombre"] = _best_c["nombre"]
        rel["ciudad_pop"]  = _best_c["poblacion"]
        rel["ciudad_risk"] = "PELIGRO" if _best_d <= CIUDAD_DANGER_KM else "ALERTA"
        if _best_d <= CIUDAD_DANGER_KM: _rel_danger_count += 1
    else:
        rel["ciudad_km"]   = None
        rel["ciudad_nombre"] = None
        rel["ciudad_pop"]  = None
        rel["ciudad_risk"] = None
# Propagate to cluster_relaves (which hold refs to same dicts)
_alert_total = sum(1 for r in relaves_all if r.get("ciudad_risk"))
print(f"   Relaves near cities: {_rel_danger_count} PELIGRO (<{CIUDAD_DANGER_KM}km) | {_alert_total} total (<{CIUDAD_ALERT_KM}km)")

# Cluster-level city-risk summary
for cid, rlist in cluster_relaves.items():
    clusters[cid]["relaves_ciudad_peligro"] = sum(1 for r in rlist if r.get("ciudad_risk")=="PELIGRO")
    clusters[cid]["relaves_ciudad_alerta"]  = sum(1 for r in rlist if r.get("ciudad_risk")=="ALERTA")
    # Highest-risk relave near a city for this cluster
    _cr = [r for r in rlist if r.get("ciudad_risk")]
    _cr.sort(key=lambda r: r.get("ciudad_km", 999))
    clusters[cid]["relaves_ciudad_top"] = (
        {"instalacion": _cr[0]["instalacion"] or _cr[0]["faena"],
         "ciudad": _cr[0]["ciudad_nombre"], "km": _cr[0]["ciudad_km"],
         "pop": _cr[0]["ciudad_pop"], "riesgo": _cr[0]["ciudad_risk"],
         "estado": _cr[0]["estado"]}
        if _cr else None
    )

# ─── STEP 7: INFRASTRUCTURE ───────────────────────────────────────────────────
print("⚡ Loading infrastructure …")

# Energy type classifier (from TIPO field of centrales_combinadas)
def classify_central_tipo(tipo):
    t = str(tipo).lower()
    if any(x in t for x in ("fotovoltaico","solar","csp")): return "solar"
    if any(x in t for x in ("eolico","eólico","eólic")):     return "eolico"
    if any(x in t for x in ("hidraul","hidrául")):           return "hidro"
    if "termoel" in t:                                        return "termica"
    return "otro"

# Tokens that identify a mining-company-exclusive desaladora
DESAL_EXCL_TOKENS = [
    "bhp","codelco","lundin","capstone","antofagasta","collahuasi",
    "teck","glencore","anglo american","spence","escondida","candelaria",
    "centinela","caserones","quebrada blanca","los pelambres","pelambres",
    "minera escondida","minera spence",
]

def read_infra(path,lat_col,lon_col):
    items=[]
    for row in load_csv(path):
        lat=pf(row.get(lat_col)); lon=pf(row.get(lon_col))
        if lat and lon: items.append({**row,"lat":round(lat,6),"lon":round(lon,6)})
    return items

subestaciones_raw=read_infra(os.path.join(SHARED,"subestaciones.csv"),"Latitude","Longitude")
centrales_raw=read_infra(os.path.join(SHARED,"centrales_combinadas.csv"),"Latitude","Longitude")
desaladoras_raw=read_infra(os.path.join(SHARED,"plantas_desaladoras_combinado_final.csv"),"Latitud","Longitud")
puertos_raw=read_infra(os.path.join(SHARED,"puertos.csv"),"latitude","longitude")
puertos=[{"nombre":r.get("portName",""),"numero":r.get("portNumber",""),
           "tamano":HARBOR_SIZE_LABELS.get(r.get("harborSize",""),r.get("harborSize","")),
           "lat":r["lat"],"lon":r["lon"]}
         for r in puertos_raw if -56<r["lat"]<-17 and -76<r["lon"]<-63]
print(f"  Puertos:       {len(puertos)} (Chile)")

real_centers=[(clusters[c]["center"][0],clusters[c]["center"][1]) for c in clusters if c!="Ruido"]
def near_cluster(lat,lon,max_km):
    return any(haversine(lat,lon,c[0],c[1])<max_km for c in real_centers)

subestaciones=[{"nombre":r.get("NOMBRE",""),"propiedad":r.get("PROPIEDAD",""),
                "tension":r.get("TENSION",""),"tipo":r.get("TIPO",""),
                "lat":r["lat"],"lon":r["lon"]}
               for r in subestaciones_raw if near_cluster(r["lat"],r["lon"],INFRA_RADIUS_KM)]

centrales=[{"nombre":r.get("NOMBRE",""),"propiedad":r.get("PROPIEDAD",""),
             "tipo":r.get("TIPO",""),"combustible":r.get("COMBUSTIBL",""),
             "potencia_mw":pf(r.get("POTENCIAMW")),"fuente":r.get("FUENTE",""),
             "lat":r["lat"],"lon":r["lon"]}
            for r in centrales_raw if near_cluster(r["lat"],r["lon"],INFRA_RADIUS_KM)]

def desal_operativa(estado):
    e=str(estado).lower().strip()
    return e in ("operativo","operativa","en operación","en operacion","en operacion","operating","en operacion\xa0")

desaladoras=[]
for r in desaladoras_raw:
    emp  = str(r.get("Empresa / Titular","") or r.get("Empresa/Operador","") or "")
    sector = str(r.get("Sector","") or r.get("Uso/Aplicacion","") or "")
    uso  = sector.lower()
    if not emp or emp=="Empresa / Titular": continue   # skip duplicate header rows
    excl = any(t in emp.lower() for t in DESAL_EXCL_TOKENS)
    desaladoras.append({
        "empresa":        emp,
        "nombre":         r.get("Nombre de la Planta",""),
        "region":         r.get("Región","") or r.get("Region",""),
        "uso":            sector,
        "estado":         r.get("Estado","") or r.get("Estado Operacional",""),
        "capacidad_lps":  pf(r.get("Capacidad (L/s)") or r.get("Capacidad (Valor)")),
        "mining":         "miner" in uso,
        "operativa":      desal_operativa(r.get("Estado","") or r.get("Estado Operacional","")),
        "exclusiva":      excl,
        "lat":            r["lat"],
        "lon":            r["lon"],
    })

print(f"  Subestaciones: {len(subestaciones_raw)} → {len(subestaciones)} near clusters")
print(f"  Centrales:     {len(centrales_raw)} → {len(centrales)} near clusters")
print(f"  Desaladoras:   {len(desaladoras)} (mining: {sum(1 for d in desaladoras if d['mining'])})")

# Pre-compute number of production clusters per region prefix (for water sharing)
prod_clusters_by_region = defaultdict(int)
for cid,cluster in clusters.items():
    if cid=="Ruido": continue
    if sum(float(v) for v in cluster.get("production",{}).values()) > 0:
        prod_clusters_by_region[cid.split("-")[0]] += 1

# Capacity per cluster — energy mix + water with exclusivity logic
for cid,cluster in clusters.items():
    if cid=="Ruido": continue
    clat,clon=cluster["center"]
    region_prefix = cid.split("-")[0]
    nc=sorted([c for c in centrales if haversine(clat,clon,c["lat"],c["lon"])<INFRA_RADIUS_KM],
               key=lambda c:haversine(clat,clon,c["lat"],c["lon"]))[:20]
    nd=sorted([d for d in desaladoras if haversine(clat,clon,d["lat"],d["lon"])<DESAL_RADIUS_KM],
               key=lambda d:haversine(clat,clon,d["lat"],d["lon"]))[:12]

    # ── Energy mix ───────────────────────────────────────────────────────────
    emix = {"solar":0.0,"eolico":0.0,"hidro":0.0,"termica":0.0,"otro":0.0}
    for c in nc:
        emix[classify_central_tipo(c["tipo"])] += c["potencia_mw"]
    total_mw = sum(emix.values())
    pct_ren = round((emix["solar"]+emix["eolico"]+emix["hidro"])/max(total_mw,0.001)*100,1)
    cluster["elec_capacity_mwh"]=round(total_mw*8760,0)
    cluster["energy_mix"]={k:round(v,1) for k,v in emix.items()}
    cluster["pct_renovable"]=pct_ren

    # ── Water: only operational mining desaladoras ────────────────────────────
    nd_mining_oper=[d for d in nd if d["mining"] and d["operativa"]]

    def matches_cluster(d):
        """True if this exclusive desaladora's company owns a mine in this cluster.
        Uses COMPANY_MINE_MAP so BHP's Spence SGO also serves the Escondida cluster."""
        emp_lower = d["empresa"].lower()
        for comp_tok, mine_keys in COMPANY_MINE_MAP.items():
            if comp_tok in emp_lower or any(m in emp_lower for m in mine_keys):
                return comp_tok in cluster_company_groups.get(cid, set())
        # Fallback: token-based match against top_empresas
        top_emp_lower = [e["empresa"].lower() for e in cluster.get("top_empresas", [])]
        for tok in DESAL_EXCL_TOKENS:
            if tok in emp_lower:
                return any(tok in emp for emp in top_emp_lower)
        return False

    nd_excl   = [d for d in nd_mining_oper if     d["exclusiva"] and matches_cluster(d)]
    nd_shared = [d for d in nd_mining_oper if not d["exclusiva"]]
    n_region  = max(1, prod_clusters_by_region.get(region_prefix,1))
    cap_excl   = sum(d["capacidad_lps"]*31536*DESAL_UTIL_RATE for d in nd_excl)
    cap_shared = sum(d["capacidad_lps"]*31536*DESAL_UTIL_RATE for d in nd_shared) / n_region

    # How many clusters in this region share each company's desaladora
    company_region_n = defaultdict(int)
    for other_cid in clusters:
        if other_cid == "Ruido" or not other_cid.startswith(region_prefix): continue
        for comp_tok in cluster_company_groups.get(other_cid, set()):
            company_region_n[comp_tok] += 1

    # Water demand for utilization computation (m³/year at default year)
    water_demand_m3 = cluster.get("water_est", {}).get(str(DEFAULT_YEAR), 0)
    if not water_demand_m3:
        we = cluster.get("water_est", {})
        water_demand_m3 = we.get(max(we.keys())) if we else 0

    # Build nearby_desaladoras list with per-cluster utilization info
    nearby_desal = []
    for d in sorted(nd, key=lambda x: haversine(clat, clon, x["lat"], x["lon"])):
        if not d["mining"]: continue
        is_excl_match = d["exclusiva"] and matches_cluster(d)
        is_shared     = not d["exclusiva"]
        available     = is_excl_match or is_shared
        # Effective capacity allocated to this cluster
        if is_excl_match:
            emp_lower = d["empresa"].lower()
            n_comp = 1
            for comp_tok, mine_keys in COMPANY_MINE_MAP.items():
                if comp_tok in emp_lower or any(m in emp_lower for m in mine_keys):
                    n_comp = max(1, company_region_n.get(comp_tok, 1))
                    break
            eff_cap = d["capacidad_lps"] * 31536 * DESAL_UTIL_RATE / n_comp
        elif is_shared:
            eff_cap = d["capacidad_lps"] * 31536 * DESAL_UTIL_RATE / n_region
        else:
            eff_cap = 0
        cover_pct = round(eff_cap / max(water_demand_m3, 1) * 100, 1) if eff_cap > 0 else 0
        nearby_desal.append({
            "empresa":      d["empresa"],
            "nombre":       d["nombre"],
            "uso":          d["uso"],
            "estado":       d["estado"],
            "capacidad_lps":d["capacidad_lps"],
            "cap_m3_year":  round(d["capacidad_lps"] * 31536, 0),
            "mining":       d["mining"],
            "operativa":    d["operativa"],
            "exclusiva":    d["exclusiva"],
            "excl_match":   is_excl_match,
            "available":    available,
            "cover_pct":    cover_pct,
            "lat":          d["lat"],
            "lon":          d["lon"],
            "dist_km":      round(haversine(clat, clon, d["lat"], d["lon"]), 1),
        })

    cluster["water_capacity_m3"]       =round(sum(d["capacidad_lps"]*31536 for d in nd),0)
    cluster["water_mining_capacity_m3"]=round(cap_excl+cap_shared,0)
    cluster["water_excl_count"]        =len(nd_excl)
    cluster["water_shared_count"]      =len(nd_shared)
    cluster["n_region_clusters"]       =n_region
    cluster["nearby_desaladoras"]      =nearby_desal

    # ── Relaves activos ───────────────────────────────────────────────────────
    rels=cluster.get("relaves",[])
    cluster["relaves_activos_count"]=sum(1 for r in rels if r["estado"] in ("ACTIVO","ACTIVA"))
    cluster["relaves_activos_vol"]=round(
        sum(r["vol_disponible"] for r in rels if r["estado"] in ("ACTIVO","ACTIVA")),0)

    # ── TSF fill-up years estimation ─────────────────────────────────────────
    # Tailings volume generated per kt Cu produced (m³/kt), by process type:
    #   Sulfuros (flotation, ~0.6% grade): ~100,000 m³/kt
    #   Mixto:                              ~70,000 m³/kt
    #   Oxidos (heap leach, minimal TSF):   ~15,000 m³/kt
    #   Fundicion (concentrates only):       ~5,000 m³/kt
    _TAIL_M3_PER_KT = {'Sulfuros':100_000,'Mixto':70_000,'Oxidos':15_000,'Fundicion':5_000}
    _annual_tail_m3 = 0.0
    for _mr in cluster.get("mine_roster", []):
        _mk2 = _mr["mk"]; _avg_p = _mr["avg_prod"]
        _mtype = _mine_type_map.get(_mk2)
        if not _mtype:
            for _m2,_t2 in _mine_type_map.items():
                if fuzzy(_mk2,_m2)>=0.75: _mtype=_t2; break
        _annual_tail_m3 += _avg_p * _TAIL_M3_PER_KT.get(_mtype, 90_000)
    _activos_vol = cluster.get("relaves_activos_vol", 0) or 0
    if _annual_tail_m3 > 0 and _activos_vol > 0:
        cluster["relaves_tsf_years"] = round(_activos_vol / _annual_tail_m3, 1)
    else:
        cluster["relaves_tsf_years"] = None
    cluster["relaves_annual_tailings_m3"] = round(_annual_tail_m3, 0)

# ─── STEP 8: ESTACIONES + TRAIN LINES ────────────────────────────────────────
print("🚂 Building train network …")
est_rows=load_csv(os.path.join(SHARED,"estaciones.csv"))
estaciones_pts=[]
for r in est_rows:
    try:
        lat=float(r["latitude"]); lon=float(r["longitude"])
        if lat and lon: estaciones_pts.append({"name":r["name"],"lat":round(lat,6),"lon":round(lon,6)})
    except: pass

def build_train_lines(pts, lat_north_split=-28.5, norte_coastal_lon=-69.8,
                      comp_km=55, efe_connect=55, norte_connect=70,
                      branch_max_km=180):
    """
    Chile railroad visualization — 3 N-S trunk lines + E-W branch spurs.

    Based on the actual station dataset (742 stations, 4 connected components):

    Trunk A — EFE Central/Sur (576 stations, lat -42 to -28.5):
      Direction-aware greedy starting S→N with rolling-longitude reference
      and strong N-S bias.  E-W mining spurs and remote outliers become branches.

    Trunk B — Norte Grande coastal (94 of 166 northern stations, lon ≤ -69.8):
      Pre-filtered to the coastal N-S strip (Antofagasta→Iquique→Arica).
      The 72 inland stations (FCAB, mining railways) attach as E-W branches
      to their nearest coastal station.

    Trunk C — Arica-La Paz (20 stations, isolated component, lat -18.5 to -17.5):
      Small isolated component sorted S→N.

    Trunk D — Far south cluster (10 stations, isolated, lat -42.5 to -41.9):
      Southern Chiloé area, sorted S→N.

    Branches: isolated station(s) + EFE outliers + Norte inland mines.
    """
    n = len(pts)
    if n == 0:
        return [], []

    # ── BFS connected components ──────────────────────────────────────────────
    adj = defaultdict(list)
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine(pts[i]["lat"], pts[i]["lon"],
                          pts[j]["lat"], pts[j]["lon"])
            if d <= comp_km:
                adj[i].append(j)
                adj[j].append(i)

    visited = [False] * n
    components = []
    for start in range(n):
        if visited[start]:
            continue
        comp, queue = [], [start]
        visited[start] = True
        while queue:
            cur = queue.pop(0)
            comp.append(cur)
            for nb in adj[cur]:
                if not visited[nb]:
                    visited[nb] = True
                    queue.append(nb)
        components.append(comp)
    components.sort(key=len, reverse=True)

    # ── Helper: direction-aware greedy N-S path ───────────────────────────────
    def ns_greedy(indices, connect_km, ns_bias=1.5, max_lon_dev=0.7, alpha=0.04):
        """
        Direction-aware greedy path biased toward northward movement.
        Rolling longitude reference (alpha = smoothing) constrains E-W drift.
        Returns (path_indices, unvisited_indices).
        """
        if not indices:
            return [], []
        start = min(indices, key=lambda i: pts[i]["lat"])
        path = [start]
        used = {start}
        ref_lon = pts[start]["lon"]

        while True:
            cur = path[-1]
            cands = []
            for j in indices:
                if j in used:
                    continue
                if abs(pts[j]["lon"] - ref_lon) > max_lon_dev:
                    continue   # too far E or W from current reference
                d = haversine(pts[cur]["lat"], pts[cur]["lon"],
                              pts[j]["lat"],  pts[j]["lon"])
                if d <= connect_km:
                    cands.append((d, j))
            if not cands:
                break

            if len(path) < 2:
                # No heading yet: pick northernmost within constraints
                nxt = max(cands, key=lambda x: pts[x[1]]["lat"])[1]
            else:
                dlat_p = pts[cur]["lat"] - pts[path[-2]]["lat"]
                dlon_p = pts[cur]["lon"] - pts[path[-2]]["lon"]
                pmag   = (dlat_p**2 + dlon_p**2)**0.5 + 1e-10
                best, nxt = float("-inf"), cands[0][1]
                for d, j in cands:
                    dlat = pts[j]["lat"] - pts[cur]["lat"]
                    dlon = pts[j]["lon"] - pts[cur]["lon"]
                    jmag = (dlat**2 + dlon**2)**0.5 + 1e-10
                    dot  = (dlat_p*dlat + dlon_p*dlon) / (pmag * jmag)
                    north_reward = ns_bias * max(0.0, dlat / jmag)
                    ew_penalty   = 0.4 * abs(dlon) / jmag
                    score = 2.0*dot + north_reward - ew_penalty - d/connect_km
                    if score > best:
                        best, nxt = score, j

            path.append(nxt)
            used.add(nxt)
            # Slowly drift reference lon toward chosen station
            ref_lon = alpha * pts[nxt]["lon"] + (1.0 - alpha) * ref_lon

        unvisited = [j for j in indices if j not in used]
        return path, unvisited

    # ── Helper: attach leaves to nearest trunk stations ───────────────────────
    def make_branches(leaves, trunk_indices, max_km):
        result = []
        for leaf in leaves:
            best_d, best_anchor = float("inf"), None
            for t in trunk_indices:
                d = haversine(pts[leaf]["lat"], pts[leaf]["lon"],
                              pts[t]["lat"],   pts[t]["lon"])
                if d < best_d:
                    best_d, best_anchor = d, t
            if best_anchor is not None and best_d <= max_km:
                result.append({
                    "coords":   [[pts[best_anchor]["lat"], pts[best_anchor]["lon"]],
                                 [pts[leaf]["lat"],        pts[leaf]["lon"]]],
                    "stations": [pts[best_anchor], pts[leaf]],
                    "is_trunk": False,
                })
        return result

    trunks   = []
    branches = []
    all_trunk_idx = []   # union of all trunk station indices (for small-comp attachment)

    # ── TRUNK A: EFE Central/Sur ──────────────────────────────────────────────
    giant     = components[0]
    efe_group = [i for i in giant if pts[i]["lat"] <= lat_north_split]
    efe_path, efe_leaves = ns_greedy(efe_group, connect_km=efe_connect,
                                     ns_bias=1.5, max_lon_dev=0.9, alpha=0.04)
    if len(efe_path) >= 3:
        trunks.append({
            "coords":   [[pts[i]["lat"], pts[i]["lon"]] for i in efe_path],
            "stations": [pts[i] for i in efe_path],
            "is_trunk": True,
        })
        all_trunk_idx.extend(efe_path)
    branches.extend(make_branches(efe_leaves, efe_path, branch_max_km))

    # ── TRUNK B: Norte Grande coastal N-S strip ───────────────────────────────
    norte_group = [i for i in giant if pts[i]["lat"] > lat_north_split]
    # Coastal = westernmost stations (lon ≤ norte_coastal_lon)
    coastal_idx = [i for i in norte_group if pts[i]["lon"] <= norte_coastal_lon]
    inland_idx  = [i for i in norte_group if pts[i]["lon"] >  norte_coastal_lon]

    norte_path, norte_leaves = ns_greedy(coastal_idx, connect_km=norte_connect,
                                         ns_bias=2.0, max_lon_dev=0.5, alpha=0.02)
    if len(norte_path) >= 3:
        trunks.append({
            "coords":   [[pts[i]["lat"], pts[i]["lon"]] for i in norte_path],
            "stations": [pts[i] for i in norte_path],
            "is_trunk": True,
        })
        all_trunk_idx.extend(norte_path)
    # Unvisited coastal + all inland → branches off coastal trunk
    branches.extend(make_branches(norte_leaves + inland_idx,
                                  norte_path or coastal_idx, branch_max_km))

    # ── TRUNKS C, D …: small isolated components ─────────────────────────────
    for comp in components[1:]:
        if len(comp) >= 4:
            sorted_c = sorted(comp, key=lambda i: pts[i]["lat"])
            trunks.append({
                "coords":   [[pts[i]["lat"], pts[i]["lon"]] for i in sorted_c],
                "stations": [pts[i] for i in sorted_c],
                "is_trunk": True,
            })
            all_trunk_idx.extend(sorted_c)
        else:
            # Lone stations → branch to nearest known trunk station
            branches.extend(make_branches(comp, all_trunk_idx, 500))

    return trunks, branches

_train_trunks, _train_branches = build_train_lines(estaciones_pts)

# Assign colors: each trunk gets a distinct color; branches inherit their trunk color
_TRUNK_COLORS = ["#a78bfa", "#34d399", "#fb923c"]
_BRANCH_COLOR_DEFAULT = "#60a5fa"

train_lines = []
for i, tr in enumerate(_train_trunks):
    col = _TRUNK_COLORS[i % len(_TRUNK_COLORS)]
    train_lines.append({
        "coords":   tr["coords"],
        "stations": tr["stations"],
        "color":    col,
        "is_trunk": True,
        "weight":   2.5,
    })

for br in _train_branches:
    # Find nearest trunk by distance to its first station
    best_d, best_col = float("inf"), _BRANCH_COLOR_DEFAULT
    for i, tr in enumerate(_train_trunks):
        for node in tr["stations"]:
            d = haversine(br["stations"][0]["lat"], br["stations"][0]["lon"],
                          node["lat"], node["lon"])
            if d < best_d:
                best_d = d
                best_col = _TRUNK_COLORS[i % len(_TRUNK_COLORS)]
    train_lines.append({
        "coords":   br["coords"],
        "stations": br["stations"],
        "color":    best_col,
        "is_trunk": False,
        "weight":   1.4,
    })

print(f"  Estaciones: {len(estaciones_pts)}, Trunks: {len(_train_trunks)}, Branches: {len(_train_branches)}")

# ─── STEP 9: SIGEX PROJECTS (from shapefile) ─────────────────────────────────
print("🏗️  Loading SIGEX projects …")

# Stage classification based on study-type codes (suffix -001 = has it, -002 = doesn't)
def sigex_etapa(row):
    if (row.get("Estudio_Es","")=="ESPREF-001"
            or row.get("Plano_Mina","")=="PMIN-001"
            or row.get("EstimaciÃ³","")=="REC-001"):
        return "Factibilidad"
    if row.get("Base_Datos","")=="BDS-001":
        return "Sondajes"
    if row.get("Levantam_2","")=="LEVGF-001":
        return "Geofísica"
    if (row.get("Levantam_1","")=="BDGQ-001"
            or row.get("Mapas_Geol","")=="MGG-001"):
        return "Prospección"
    return "Exploración Inicial"

SIGEX_ETAPA_META = {
    "Factibilidad":       {"icon":"💎","color":"#a78bfa","label":"Factibilidad / Proyecto Maduro"},
    "Sondajes":           {"icon":"⚙️","color":"#f59e0b","label":"Con Sondajes"},
    "Geofísica":          {"icon":"📡","color":"#38bdf8","label":"Exploración Geofísica"},
    "Prospección":        {"icon":"🔭","color":"#4ade80","label":"Prospección Geológica"},
    "Exploración Inicial":{"icon":"🏴","color":"#94a3b8","label":"Exploración Inicial"},
}

sigex_projects=[]
try:
    sigex_rows=load_csv(SIGEX_CSV)
    for row in sigex_rows:
        lat=pf(row.get("Latitude",0)); lon=pf(row.get("Longitude",0))
        if not lat or not lon: continue
        if not (-56<lat<-15 and -76<lon<-65): continue
        recurso_raw = str(row.get("Recurso_Pr","") or "").strip()
        # Keep only copper-related projects (Cu primary or co-product)
        if not recurso_raw.startswith("Cu") and "Cu" not in recurso_raw: continue
        estado=str(row.get("Estado","") or "").strip()
        etapa=sigex_etapa(row)
        fecha_raw=str(row.get("Fecha_Ingr","") or "")
        fecha=f"{fecha_raw[:4]}-{fecha_raw[4:6]}-{fecha_raw[6:8]}" if len(fecha_raw)==8 else fecha_raw
        sigex_projects.append({
            "nombre":  str(row.get("Nombre_Pro","") or "")[:80],
            "empresa": str(row.get("Entidad_In","") or ""),
            "rut":     str(row.get("RUT","") or "").strip(),
            "recurso": recurso_raw,
            "region":  str(row.get("Región","") or row.get("Region","") or ""),
            "estado":  estado,
            "etapa":   etapa,
            "fecha":   fecha,
            "enlace":  str(row.get("Enlace_Pro","") or ""),
            "lat":round(lat,6),"lon":round(lon,6),
        })
    from collections import Counter
    etapa_counts=Counter(p["etapa"] for p in sigex_projects)
    for et,cnt in etapa_counts.most_common():
        print(f"  {SIGEX_ETAPA_META[et]['icon']} {et}: {cnt}")
    print(f"  Total: {len(sigex_projects)}")
except Exception as e:
    print(f"  ⚠️  SIGEX load failed: {e}")
seia_projects = sigex_projects   # alias so rest of code stays consistent

# ─── STEP 9b: SIGEX PER CLUSTER ──────────────────────────────────────────────
print("📍 Assigning SIGEX projects to clusters …")
_SIGEX_RADIUS_KM = 120
# Tokens that identify large/medium mining companies in SIGEX Entidad_In field
_SIGEX_GRANDES_TOKENS = [
    "codelco", "bhp", "freeport", "teck", "anglo american", "antofagasta minerals",
    "glencore", "rio tinto", "vale", "sumitomo", "lundin", "kghm", "barrick",
    "gold fields", "newmont", "capstone", "enami", "angloamerican",
]
def _is_grandes_medianas(empresa):
    e = empresa.lower()
    return any(tok in e for tok in _SIGEX_GRANDES_TOKENS)

for cid, cluster in clusters.items():
    if cid in ("Ruido","Otros"): continue
    _clat, _clon = cluster["center"]
    _nearby = [p for p in sigex_projects
               if haversine(_clat, _clon, p["lat"], p["lon"]) <= _SIGEX_RADIUS_KM]
    cluster["sigex_total"]              = len(_nearby)
    cluster["sigex_factibilidad"]       = sum(1 for p in _nearby if p["etapa"] == "Factibilidad")
    cluster["sigex_exploracion"]        = sum(1 for p in _nearby if p["etapa"] != "Factibilidad")
    cluster["sigex_grandes_medianas"]   = sum(1 for p in _nearby
                                              if p["etapa"] != "Factibilidad"
                                              and _is_grandes_medianas(p["empresa"]))
_n_with_sigex = sum(1 for c in clusters.values() if c.get("sigex_total",0)>0)
print(f"   Clusters con proyectos SIGEX: {_n_with_sigex}")

# ─── STEP 9a: SIGEX SONDAJES CLUSTERING ───────────────────────────────────────
print("🔩 Clustering SIGEX Sondajes …")
_SIGEX_CLUSTER_PALETTE = [
    "#e41a1c","#377eb8","#4daf4a","#984ea3","#ff7f00","#a65628","#f781bf",
    "#66c2a5","#fc8d62","#8da0cb","#e78ac3","#a6d854","#ffd92f","#e5c494",
    "#1f78b4","#b2df8a","#33a02c","#fb9a99","#e31a1c","#fdbf6f","#cab2d6",
    "#6a3d9a","#ffff99","#b15928","#8dd3c7","#ffffb3","#bebada","#fb8072",
    "#80b1d3","#fdb462","#b3de69","#fccde5","#d9d9d9","#bc80bd","#ccebc5",
]
sigex_sondajes_clusters = []
try:
    import numpy as _np
    _sond = [p for p in sigex_projects if p["etapa"] == "Sondajes"]
    if len(_sond) >= 5:
        _coords = _np.array([[p["lat"], p["lon"]] for p in _sond])
        _ruts   = _np.array([p["rut"] for p in _sond])
        _EPS_KM = 10
        _eps_rad = _EPS_KM / 6371.0
        from sklearn.cluster import DBSCAN as _DBSCAN
        _cl = _DBSCAN(eps=_eps_rad, min_samples=2, metric='haversine').fit(_np.radians(_coords))
        _labels = _cl.labels_.tolist()
        _n_cl = len(set(_labels)) - (1 if -1 in _labels else 0)
        for p, lbl in zip(_sond, _labels):
            color = _SIGEX_CLUSTER_PALETTE[lbl % len(_SIGEX_CLUSTER_PALETTE)] if lbl >= 0 else "#6b7280"
            rec = p.get("recurso","")
            rec_g = "Cobre" if rec.startswith("Cu") else "Oro" if rec.startswith("Au") else "Hidrocarburos" if "Hidro" in rec else "Hierro" if rec.startswith("Fe") else "Otro"
            reg = str(p.get("region","") or "").upper()
            for pre in ["REGIÓN DE ","REGIÓN DEL ","REGION DE ","REGION DEL "]:
                reg = reg.replace(pre,"")
            reg = reg.strip()
            sigex_sondajes_clusters.append({**p, "cluster_id": lbl, "color": color, "recurso_grupo": rec_g, "region_norm": reg})
        _n_noise = sum(1 for l in _labels if l < 0)
        print(f"  ✅ {_n_cl} clusters | {len(_sond)-_n_noise} asignados | {_n_noise} ruido")
    else:
        sigex_sondajes_clusters = [{**p, "cluster_id": -1, "color": "#6b7280"} for p in _sond]
        print("  ⚠️  Muy pocos sondajes para clustering")
except Exception as _e:
    print(f"  ⚠️  Clustering SIGEX fallido: {_e}")

# ─── STEP 9b: ÁREAS PROTEGIDAS ────────────────────────────────────────────────
print("🌿 Loading Áreas Protegidas …")
AP_PATH = os.path.join(SHARED,"areasProtegidas","Areas Protegidas.shp")
AP_DESIG_COLOR = {
    "Parque Nacional":                  "#16a34a",
    "Reserva Nacional":                 "#4ade80",
    "Monumento Natural":                "#fbbf24",
    "Santuario de la Naturaleza":       "#67e8f9",
    "Reserva de la Biófera":            "#c084fc",
    "Reserva Forestal":                 "#a3e635",
    "Bien Nacional Protegido":          "#fb923c",
    "Conservación Privada y Comunitaria":"#94a3b8",
    "Área Marina Costera Protegida":    "#38bdf8",
    "Parque Marino":                    "#0ea5e9",
    "Reserva Marina":                   "#7dd3fc",
    "Paisaje de Conservación":          "#86efac",
}
areas_protegidas_geojson = {"type":"FeatureCollection","features":[]}
try:
    import shapefile as _shp
    from shapely.geometry import shape as _shape, mapping as _mapping
    _sf = _shp.Reader(AP_PATH, encoding='latin-1')
    _fn = [f[0] for f in _sf.fields[1:]]
    _feats = []
    for _sr in _sf.shapeRecords():
        _props = dict(zip(_fn, _sr.record))
        for _k, _v in _props.items():
            if hasattr(_v,'item'): _props[_k] = _v.item()
        try:
            _g = _shape(_sr.shape.__geo_interface__)
            if _g.centroid.y < -42: continue          # skip far south
            _g_s = _g.simplify(0.01, preserve_topology=True)
            _desig = str(_props.get('designacio',''))
            _props['color'] = AP_DESIG_COLOR.get(_desig,'#94a3b8')
            _feats.append({'type':'Feature','geometry':_mapping(_g_s),'properties':_props})
        except Exception: pass
    areas_protegidas_geojson = {"type":"FeatureCollection","features":_feats}
    ap_centroids = []
    for feat in _feats:
        try:
            _gc = _shape(feat['geometry'])
            _cc = _gc.centroid
            ap_centroids.append({
                "lat":   round(_cc.y, 5),
                "lon":   round(_cc.x, 5),
                "nombre": str(feat['properties'].get('nombre_ap',
                             feat['properties'].get('nombr_ap',''))),
                "desig":  str(feat['properties'].get('designacio','')),
                "color":  feat['properties'].get('color','#94a3b8'),
            })
        except Exception: pass
    print(f"   Áreas Protegidas: {len(_feats)} features")
except Exception as e:
    print(f"   ⚠ Áreas Protegidas skipped: {e}")
    ap_centroids = []

# ─── STEP 9c: PER-MINE RISK INDICATORS ───────────────────────────────────────
print("⚠️  Computing per-mine risk indicators …")
RELAVE_DANGER_KM = 25   # direct danger zone around mine
RELAVE_ALERT_KM  = 60   # alert zone
AP_RISK_KM       = 30   # protected area within this radius = compliance risk

for cid, cluster in clusters.items():
    if cid in ("Ruido", "Otros"): continue
    # Build cluster-level desal capacity denominator
    cl_roster = cluster.get("mine_roster", [])
    cl_desal_m3 = cluster.get("water_mining_capacity_m3", 0)
    cl_elec_mwh = cluster.get("elec_capacity_mwh", 0)
    # Total weighted water demand for this cluster (for proportional share)
    cl_water_total = 0.0
    for _mr in cl_roster:
        _mtype = _mine_type_map.get(_mr["mk"])
        if not _mtype:
            for _m2, _t2 in _mine_type_map.items():
                if fuzzy(_mr["mk"], _m2) >= 0.75: _mtype = _t2; break
        cl_water_total += _mr["avg_prod"] * 1000 * WATER_FACTOR.get(_mtype, WATER_FACTOR_DEFAULT)

    for mine in cl_roster:
        mk2 = mine["mk"]
        lat2, lon2 = MINE_LOCATIONS.get(mk2, (None, None))
        if lat2 is None:
            mine["risk"] = {}; continue

        # ── Relaves proximity ─────────────────────────────────────────────────
        danger_rel = {"ACTIVO": 0, "INACTIVO": 0, "ABANDONADO": 0}
        alert_rel  = {"ACTIVO": 0, "INACTIVO": 0, "ABANDONADO": 0}
        for rel in relaves_all:
            _d = haversine(lat2, lon2, rel["lat"], rel["lon"])
            _est = rel["estado"]
            _key = ("ACTIVO" if _est in ("ACTIVO","ACTIVA") else
                    "INACTIVO" if _est in ("INACTIVO","INACTIVA") else
                    "ABANDONADO" if _est in ("ABANDONADO","ABANDONADA") else None)
            if _key:
                if _d <= RELAVE_DANGER_KM:   danger_rel[_key] += 1
                elif _d <= RELAVE_ALERT_KM:  alert_rel[_key] += 1

        # ── Protected areas proximity ─────────────────────────────────────────
        nearest_ap_d  = float("inf")
        nearest_ap_nm = None
        nearest_ap_dg = None
        for _ap in ap_centroids:
            _d = haversine(lat2, lon2, _ap["lat"], _ap["lon"])
            if _d < nearest_ap_d:
                nearest_ap_d  = _d
                nearest_ap_nm = _ap["nombre"]
                nearest_ap_dg = _ap["desig"]

        # ── Port proximity ────────────────────────────────────────────────────
        nearest_port_d  = float("inf")
        nearest_port_nm = None
        for _p in puertos:
            _d = haversine(lat2, lon2, _p["lat"], _p["lon"])
            if _d < nearest_port_d:
                nearest_port_d  = _d
                nearest_port_nm = _p["nombre"]

        # ── Water & electricity demand ────────────────────────────────────────
        avg_prod2 = mine["avg_prod"]  # kt/year
        mtype2 = _mine_type_map.get(mk2)
        if not mtype2:
            for _m2, _t2 in _mine_type_map.items():
                if fuzzy(mk2, _m2) >= 0.75: mtype2 = _t2; break
        wf2 = WATER_FACTOR.get(mtype2, WATER_FACTOR_DEFAULT)
        water_demand_m3 = round(avg_prod2 * 1000 * wf2, 0) if avg_prod2 > 0 else 0
        mine_water_total = water_demand_m3
        mine_share_w = mine_water_total / cl_water_total if cl_water_total > 0 else 0
        desal_avail_m3 = cl_desal_m3 * mine_share_w          # cl_desal_m3 already at 90% util
        desal_pct = round(desal_avail_m3 / mine_water_total * 100, 1) if mine_water_total > 0 else 0

        elec_demand_mwh = round(avg_prod2 * 1000 * ELEC_MWH_PER_TON, 0) if avg_prod2 > 0 else 0
        cl_prod_total = sum(m3["avg_prod"] for m3 in cl_roster)
        elec_share = avg_prod2 / cl_prod_total if cl_prod_total > 0 else 0
        grid_avail_mwh = cl_elec_mwh * elec_share
        grid_pct = round(grid_avail_mwh / elec_demand_mwh * 100, 1) if elec_demand_mwh > 0 else 0

        # ── Compose risk dict ─────────────────────────────────────────────────
        mine["risk"] = {
            "relaves_danger":      danger_rel,
            "relaves_alert":       alert_rel,
            "total_danger":        sum(danger_rel.values()),
            "total_alert":         sum(alert_rel.values()),
            "ap_km":    round(nearest_ap_d, 1) if nearest_ap_nm else None,
            "ap_nombre": nearest_ap_nm[:60] if nearest_ap_nm else None,
            "ap_desig":  nearest_ap_dg if nearest_ap_dg else None,
            "ap_flag":   nearest_ap_d <= AP_RISK_KM if nearest_ap_nm else False,
            "port_km":   round(nearest_port_d, 1) if nearest_port_nm else None,
            "port_name": nearest_port_nm if nearest_port_nm else None,
            "water_demand_m3": water_demand_m3,
            "water_factor":    wf2,
            "mine_type":       mtype2 or "Unknown",
            "desal_pct":       min(desal_pct, 999.0),
            "elec_demand_mwh": elec_demand_mwh,
            "grid_pct":        min(grid_pct, 999.0),
        }
print(f"   Risk indicators: {sum(1 for cl in clusters.values() for m in cl.get('mine_roster',[]) if m.get('risk'))} mines")

# ─── STEP 9.5: FORECAST DATA ─────────────────────────────────────────────────
print("🔮 Loading forecast data …")
try:
    sb_ann = pd.read_csv(os.path.join(FORECAST_ANNUAL_DIR, "scoreboard_annual_v10.csv"))
    sb_ann["Mine"] = sb_ann["Mine"].str.lower().str.strip()
    if "WR%" in sb_ann.columns:
        sb_ann["WR"] = sb_ann["WR%"] / 100.0
    if "Hfoc%" in sb_ann.columns:
        sb_ann["Hfoc"] = sb_ann["Hfoc%"] / 100.0
    if "TrimMAPE_Sk%" in sb_ann.columns and "Skill" not in sb_ann.columns:
        sb_ann["Skill"] = sb_ann["TrimMAPE_Sk%"]

    sb_mon = pd.read_csv(os.path.join(FORECAST_MONTHLY_DIR, "scoreboard_monthly_v10.csv"))
    sb_mon["Mine"] = sb_mon["Mine"].str.lower().str.strip()
    if "WR%" in sb_mon.columns:
        sb_mon["WR"] = sb_mon["WR%"] / 100.0
    if "Hfoc%" in sb_mon.columns:
        sb_mon["Hfoc"] = sb_mon["Hfoc%"] / 100.0
    if "TrimMAPE_Sk%" in sb_mon.columns and "Skill" not in sb_mon.columns:
        sb_mon["Skill"] = sb_mon["TrimMAPE_Sk%"]
    mon_dict = {row["Mine"]: row for _, row in sb_mon.iterrows()}

    # Load DM test results (per-mine Diebold-Mariano statistical significance)
    dm_ann_dict, dm_mon_dict = {}, {}
    try:
        dm_ann_df = pd.read_csv(os.path.join(FORECAST_ANNUAL_DIR, "dm_annual.csv"),
                                keep_default_na=False)
        dm_ann_df["Mine"] = dm_ann_df["Mine"].str.lower().str.strip()
        dm_ann_dict = {row["Mine"]: row for _, row in dm_ann_df.iterrows()}
    except Exception: pass
    try:
        dm_mon_df = pd.read_csv(os.path.join(FORECAST_MONTHLY_DIR, "dm_monthly.csv"),
                                keep_default_na=False)
        dm_mon_df["Mine"] = dm_mon_df["Mine"].str.lower().str.strip()
        dm_mon_dict = {row["Mine"]: row for _, row in dm_mon_df.iterrows()}
    except Exception: pass

    def _dm_p(row):
        if row is None: return None
        try:
            f = float(row["p_value"])
            return None if f != f else round(f, 4)
        except: return None

    def _dm_s(row):
        if row is None: return None
        v = str(row.get("Sig", "")).strip()
        return v if v and v != "nan" else None

    pred_ann = pd.read_csv(os.path.join(FORECAST_ANNUAL_DIR, "all_predictions_annual_v10.csv"))
    pred_ann["Mine"] = pred_ann["Mine"].str.lower().str.strip()
    pred_filt = pred_ann[
        (pred_ann["Exp"] == "Ens_Segmentado") & (pred_ann["Origin"] == 2018)
    ].sort_values("Horizonte")

    # MdAPE per mine (annual, all validation origins)
    mdape_ann = {}
    try:
        _av = pred_ann[pred_ann["Exp"] == "Ens_Segmentado"].copy()
        _av = _av[(_av["Actual"] > 0) & (_av["Pred"] > 0)]
        _av["ape"] = abs(_av["Actual"] - _av["Pred"]) / _av["Actual"] * 100
        mdape_ann = _av.groupby("Mine")["ape"].median().round(1).to_dict()
    except Exception: pass

    def _safe(v):
        try:
            f = float(v)
            return round(f, 2) if not math.isnan(f) else None
        except Exception:
            return None

    # ── Per-mine MAPE from validation (for CI repair) ─────────────────────────
    _val_mape_ann: dict = {}
    try:
        _av2 = pred_ann[pred_ann["Exp"] == "Ens_Segmentado"].copy()
        _av2 = _av2[(_av2["Actual"] > 0) & (_av2["Pred"] > 0)]
        _av2["ape"] = abs(_av2["Actual"] - _av2["Pred"]) / _av2["Actual"]
        _val_mape_ann = _av2.groupby("Mine")["ape"].median().to_dict()
    except Exception: pass

    def _repair_ci(pred_list, lower_list, upper_list, mine_key):
        """Ensure pred is inside [lower, upper]. Fixes inverted or shifted intervals."""
        mape = _val_mape_ann.get(mine_key, 0.22)  # fallback 22%
        out_l, out_u = [], []
        for p, lo, hi in zip(pred_list, lower_list, upper_list):
            if p is None:
                out_l.append(None); out_u.append(None); continue
            # Sort lo/hi first
            lo_s, hi_s = (min(lo, hi), max(lo, hi)) if (lo is not None and hi is not None) else (lo, hi)
            # If pred is still outside sorted band, fall back to validation-MAPE band
            if lo_s is None or hi_s is None or p < lo_s or p > hi_s:
                margin = p * mape
                lo_s = p - margin
                hi_s = p + margin
            out_l.append(round(lo_s, 2))
            out_u.append(round(hi_s, 2))
        return out_l, out_u

    # Load future projections 2026-2032
    proj_path = os.path.join(FORECAST_ANNUAL_DIR, "projections_2026_2032.csv")
    proj_dict = {}   # mine → {year: {pred, lower, upper, naive}}
    try:
        df_proj = pd.read_csv(proj_path)
        df_proj["Mine"] = df_proj["Mine"].str.lower().str.strip()
        for mk_p, grp in df_proj.groupby("Mine"):
            grp = grp.sort_values("ForecastYear")
            pred_l   = [_safe(v) for v in grp["Pred"]]
            lower_l  = [_safe(v) for v in grp["Lower"]]
            upper_l  = [_safe(v) for v in grp["Upper"]]
            lower_l, upper_l = _repair_ci(pred_l, lower_l, upper_l, mk_p)
            proj_dict[mk_p] = {
                "years":  grp["ForecastYear"].astype(int).tolist(),
                "pred":   pred_l,
                "lower":  lower_l,
                "upper":  upper_l,
                "naive":  [_safe(v) for v in grp["Naive_Pred"]],
            }
        print(f"   Projections loaded: {len(proj_dict)} mines")
    except Exception as ep:
        print(f"   ⚠ Projections not found ({ep}) — run generate_projections.py first")

    # ── Monthly projections 2026-2032 ─────────────────────────────────────
    # Note: the monthly projections CSV can have prediction drift at long horizons
    # (due to model extrapolation). Cap predictions at 2.5x origin_prod; if a mine
    # exceeds that, fall back to the annual projection ÷ 12 for a conservative trend.
    proj_m_dict = {}
    try:
        df_proj_m = pd.read_csv(os.path.join(FORECAST_MONTHLY_DIR,
                                              "projections_monthly_2026_2032.csv"))
        df_proj_m["Mine"] = df_proj_m["Mine"].str.lower().str.strip()
        _MON_GROWTH_CAP = 2.5   # max allowed ratio of pred/origin at any horizon
        for mk_p, grp in df_proj_m.groupby("Mine"):
            grp = grp.sort_values("Horizonte")
            origin_prod = grp["Origin_Prod"].iloc[0] if "Origin_Prod" in grp.columns else None
            pred_raw   = [_safe(v) for v in grp["Pred"]]
            naive_raw  = [_safe(v) for v in grp["Naive_Pred"]]
            lower_raw  = [_safe(v) for v in grp["Lower"]]
            upper_raw  = [_safe(v) for v in grp["Upper"]]
            # Detect runaway predictions
            _runaway = (origin_prod and origin_prod > 0 and
                        any(p is not None and p > origin_prod * _MON_GROWTH_CAP
                            for p in pred_raw))
            if _runaway:
                # Fall back to annual projection ÷ 12 as monthly trend
                ann_data = proj_dict.get(mk_p, {})
                ann_years = ann_data.get("years", [])
                ann_pred  = ann_data.get("pred",  [])
                ann_lo    = ann_data.get("lower", [])
                ann_hi    = ann_data.get("upper", [])
                _ann_map  = {y: (p, lo, hi) for y, p, lo, hi in zip(ann_years, ann_pred, ann_lo, ann_hi)}
                new_pred, new_lo, new_hi = [], [], []
                for dt in grp["ForecastDate"]:
                    yr = int(str(dt)[:4])
                    if yr in _ann_map and _ann_map[yr][0] is not None:
                        p_m = _ann_map[yr][0] / 12.0
                        lo_m = _ann_map[yr][1] / 12.0
                        hi_m = _ann_map[yr][2] / 12.0
                    elif origin_prod:
                        p_m = origin_prod; lo_m = origin_prod * 0.8; hi_m = origin_prod * 1.2
                    else:
                        p_m = lo_m = hi_m = None
                    new_pred.append(round(p_m, 3) if p_m is not None else None)
                    new_lo.append(round(lo_m, 3) if lo_m is not None else None)
                    new_hi.append(round(hi_m, 3) if hi_m is not None else None)
                pred_raw, lower_raw, upper_raw = new_pred, new_lo, new_hi
            # Repair CI
            lower_raw, upper_raw = _repair_ci(pred_raw, lower_raw, upper_raw, mk_p)
            proj_m_dict[mk_p] = {
                "months": grp["ForecastDate"].tolist(),
                "pred":   pred_raw,
                "lower":  lower_raw,
                "upper":  upper_raw,
                "naive":  naive_raw,
            }
        _runaway_count = sum(
            1 for mk_p, grp in df_proj_m.groupby("Mine")
            if (grp["Origin_Prod"].iloc[0] > 0 if "Origin_Prod" in grp.columns else False) and
               any(_safe(v) is not None and _safe(v) > grp["Origin_Prod"].iloc[0] * _MON_GROWTH_CAP
                   for v in grp["Pred"])
        )
        print(f"   Monthly projections loaded: {len(proj_m_dict)} mines ({_runaway_count} fallback to annual÷12)")
    except Exception as ep_m:
        print(f"   ⚠ Monthly projections not found ({ep_m})")

    # ── Annual scenarios (bear / base / bull copper price) ─────────────────────
    proj_scenarios_dict = {}
    try:
        df_proj_sc = pd.read_csv(os.path.join(FORECAST_ANNUAL_DIR,
                                              "projections_scenarios_2026_2032.csv"))
        df_proj_sc["Mine"] = df_proj_sc["Mine"].str.lower().str.strip()
        for _mk_sc, _grp_sc in df_proj_sc.groupby("Mine"):
            proj_scenarios_dict[_mk_sc] = {}
            for _sc, _sg in _grp_sc.groupby("Scenario"):
                _sg = _sg.sort_values("ForecastYear")
                proj_scenarios_dict[_mk_sc][_sc] = {
                    "years": _sg["ForecastYear"].astype(int).tolist(),
                    "pred":  [_safe(v) for v in _sg["Pred"]],
                    "lower": [_safe(v) for v in _sg["Lower"]] if "Lower" in _sg.columns else [],
                    "upper": [_safe(v) for v in _sg["Upper"]] if "Upper" in _sg.columns else [],
                }
        print(f"   Annual scenarios: {len(proj_scenarios_dict)} mines × 3 scenarios")
    except Exception as _ep_sc:
        print(f"   ⚠ Annual scenarios not found ({_ep_sc})")

    # ── Monthly scenarios ──────────────────────────────────────────────────────
    proj_m_scenarios_dict = {}
    try:
        df_proj_m_sc = pd.read_csv(os.path.join(FORECAST_MONTHLY_DIR,
                                                 "projections_scenarios_monthly_2026_2032.csv"))
        df_proj_m_sc["Mine"] = df_proj_m_sc["Mine"].str.lower().str.strip()
        for _mk_sc, _grp_sc in df_proj_m_sc.groupby("Mine"):
            proj_m_scenarios_dict[_mk_sc] = {}
            for _sc, _sg in _grp_sc.groupby("Scenario"):
                _sg = _sg.sort_values("Horizonte")
                proj_m_scenarios_dict[_mk_sc][_sc] = {
                    "months": _sg["ForecastDate"].tolist(),
                    "pred":   [_safe(v) for v in _sg["Pred"]],
                    "lower":  [_safe(v) for v in _sg["Lower"]],
                    "upper":  [_safe(v) for v in _sg["Upper"]],
                }
        print(f"   Monthly scenarios: {len(proj_m_scenarios_dict)} mines × 3 scenarios")
    except Exception as _ep_m_sc:
        print(f"   ⚠ Monthly scenarios not found ({_ep_m_sc})")

    # ── Monthly validation series + WR by horizon (per mine) ──────────────
    series_m_dict = {}
    wr_by_h_dict  = {}
    mdape_mon     = {}
    try:
        pred_mon = pd.read_csv(os.path.join(FORECAST_MONTHLY_DIR,
                                             "all_predictions_monthly_v10.csv"))
        pred_mon["Mine"] = pred_mon["Mine"].str.lower().str.strip()
        # Derive TargetDate from Origin + Horizonte if column not present
        if "TargetDate" not in pred_mon.columns:
            pred_mon["_Origin_dt"] = pd.to_datetime(pred_mon["Origin"])
            pred_mon["TargetDate"] = pred_mon.apply(
                lambda r: (r["_Origin_dt"] + pd.DateOffset(months=int(r["Horizonte"]))).strftime("%Y-%m"),
                axis=1)
            pred_mon.drop(columns=["_Origin_dt"], inplace=True)
        # Determine best-ensemble label: prefer Ens_Segmentado, fall back to most common Exp
        _best_exp_m = "Ens_Segmentado" if "Exp" in pred_mon.columns and (pred_mon["Exp"] == "Ens_Segmentado").any() \
                      else (pred_mon["Exp"].value_counts().index[0] if "Exp" in pred_mon.columns else None)
        _mask_exp_m = (pred_mon["Exp"] == _best_exp_m) if _best_exp_m else pd.Series(True, index=pred_mon.index)
        LAST_ORIGIN = pred_mon[_mask_exp_m]["Origin"].max()
        pred_last   = pred_mon[pred_mon["Origin"] == LAST_ORIGIN].copy()

        # Validation series from last origin
        for mk_m, grp_m in pred_last.groupby("Mine"):
            sub = grp_m[_mask_exp_m.reindex(grp_m.index, fill_value=True)].sort_values("Horizonte")
            if len(sub) == 0:
                sub = grp_m.sort_values("Horizonte")
            if len(sub) == 0:
                continue
            series_m_dict[mk_m] = {
                "dates":  sub["TargetDate"].tolist(),
                "actual": [_safe(v) for v in sub["Actual"]],
                "pred":   [_safe(v) for v in sub["Pred"]],
                "naive":  [_safe(v) for v in sub["Naive_Pred"]],
            }

        # WR by horizon (all origins): recompute Beats_Naive
        for mk_m, grp_all in pred_mon.groupby("Mine"):
            sub = grp_all[_mask_exp_m.reindex(grp_all.index, fill_value=True)].copy()
            if len(sub) == 0:
                sub = grp_all.copy()
            if len(sub) == 0:
                continue
            sub["_BN"] = (sub["Model_Error"] < sub["Naive_Error"]).astype(int)
            wr_h = sub.groupby("Horizonte")["_BN"].mean()
            wr_by_h_dict[mk_m] = {
                "horizons": wr_h.index.tolist(),
                "wr":       [round(float(v), 3) for v in wr_h.values],
            }

        # MdAPE per mine (monthly, all validation origins)
        _mv = pred_mon[_mask_exp_m.reindex(pred_mon.index, fill_value=True)].copy()
        _mv = _mv[(_mv["Actual"] > 0) & (_mv["Pred"] > 0)]
        _mv["ape"] = abs(_mv["Actual"] - _mv["Pred"]) / _mv["Actual"] * 100
        mdape_mon = _mv.groupby("Mine")["ape"].median().round(1).to_dict()

        print(f"   Monthly series: {len(series_m_dict)} mines | WR-by-H: {len(wr_by_h_dict)}")
    except Exception as ep_m2:
        print(f"   ⚠ Monthly validation series failed ({ep_m2})")

    # Nearest-city lookup for all mines in MINE_LOCATIONS
    _mine_city_lookup: dict = {}
    for _mk, (_lat, _lon) in MINE_LOCATIONS.items():
        _bd, _bc = float("inf"), None
        for _city in CIUDADES_CHILE:
            _d = haversine(_lat, _lon, _city["lat"], _city["lon"])
            if _d < _bd: _bd, _bc = _d, _city["nombre"]
        _mine_city_lookup[_mk] = (_bc, round(_bd, 1))

    _HIDDEN_MINES = {"capstone copper (4)"}  # excluded from forecast display

    # Build Size_Label lookup from projections (scoreboard v10 doesn't carry it)
    _size_label_dict: dict = {}
    try:
        _df_sl = pd.read_csv(os.path.join(FORECAST_ANNUAL_DIR, "projections_2026_2032.csv"))
        _df_sl["Mine"] = _df_sl["Mine"].str.lower().str.strip()
        for _mk_sl, _grp_sl in _df_sl.groupby("Mine"):
            if "Size_Label" in _grp_sl.columns:
                _size_label_dict[_mk_sl] = str(_grp_sl["Size_Label"].iloc[0])
    except Exception:
        pass

    mine_forecast = {}
    for _, row in sb_ann.iterrows():
        mk = row["Mine"]
        if mk in _HIDDEN_MINES:
            continue
        mp = pred_filt[pred_filt["Mine"] == mk].sort_values("Horizonte")
        series = {
            "years":   mp["ForecastYear"].astype(int).tolist(),
            "actual":  [_safe(v) for v in mp["Actual"]],
            "pred":    [_safe(v) for v in mp["Pred"]],
            "naive":   [_safe(v) for v in mp["Naive_Pred"]],
            "sarimax": [_safe(v) for v in mp["SARIMAX_Pred"]],
        }
        # Per-mine historical production (2000-2025) for projection chart
        hist_raw = mine_prod.get(mk, {})
        history = {str(y): round(v, 2) for y, v in hist_raw.items()
                   if v is not None and v > 0 and y >= 2000}
        # Monthly-scale history: annual ÷ 12 → same unit as monthly projections (kt/month)
        history_m = {str(y): round(v / 12.0, 3) for y, v in hist_raw.items()
                     if v is not None and v > 0 and y >= 2000}
        mon_row = mon_dict.get(mk)
        dm_row_a = dm_ann_dict.get(mk)
        dm_row_m = dm_mon_dict.get(mk)
        mine_forecast[mk] = {
            "wr":       round(float(row["WR"]),   4),
            "mase":     round(float(row["MASE"]),  3),
            "skill":    round(float(row["Skill"]), 1),
            "size":     _size_label_dict.get(mk, "Unknown"),
            "mdape":    float(mdape_ann[mk]) if mk in mdape_ann else None,
            "dm_p":     _dm_p(dm_row_a),
            "dm_sig":   _dm_s(dm_row_a),
            "wr_m":     round(float(mon_row["WR"]),    4) if mon_row is not None else None,
            "mase_m":   round(float(mon_row["MASE"]), 3) if mon_row is not None and "MASE" in mon_row.index and pd.notna(mon_row.get("MASE")) else None,
            "skill_m":  round(float(mon_row["Skill"]),  1) if mon_row is not None else None,
            "mdape_m":  float(mdape_mon[mk]) if mk in mdape_mon else None,
            "dm_p_m":   _dm_p(dm_row_m),
            "dm_sig_m": _dm_s(dm_row_m),
            "series":   series,
            "history":  history,
            "history_m": history_m,
            "proj":     proj_dict.get(mk, {}),
            "proj_m":   proj_m_dict.get(mk, {}),
            "proj_scenarios":   proj_scenarios_dict.get(mk, {}),
            "proj_m_scenarios": proj_m_scenarios_dict.get(mk, {}),
            "series_m": series_m_dict.get(mk, {}),
            "wr_by_h":  wr_by_h_dict.get(mk, {}),
            "nearest_city":    _mine_city_lookup.get(mk.lower().replace("_"," "), (None, None))[0],
            "nearest_city_km": _mine_city_lookup.get(mk.lower().replace("_"," "), (None, None))[1],
        }

    # ── Monthly-only mines (not in annual scoreboard) ─────────────────────────
    for _, row_m in sb_mon.iterrows():
        mk = row_m["Mine"]
        if mk in mine_forecast or mk in _HIDDEN_MINES:
            continue  # already added from annual loop, or hidden
        hist_raw = mine_prod.get(mk, {})
        history   = {str(y): round(v, 2)       for y, v in hist_raw.items()
                     if v is not None and v > 0 and y >= 2000}
        history_m = {str(y): round(v / 12.0, 3) for y, v in hist_raw.items()
                     if v is not None and v > 0 and y >= 2000}
        dm_row_m = dm_mon_dict.get(mk)
        _wr_m_val   = float(row_m["WR"])   if pd.notna(row_m.get("WR"))    else None
        _mase_m_val = float(row_m["MASE"]) if pd.notna(row_m.get("MASE"))  else None
        _sk_m_val   = float(row_m["Skill"])if pd.notna(row_m.get("Skill")) else None
        mine_forecast[mk] = {
            "wr":       None,
            "mase":     None,
            "skill":    None,
            "size":     _size_label_dict.get(mk, None),
            "mdape":    None,
            "dm_p":     None,
            "dm_sig":   None,
            "wr_m":     round(_wr_m_val,   4) if _wr_m_val   is not None else None,
            "mase_m":   round(_mase_m_val, 3) if _mase_m_val is not None else None,
            "skill_m":  round(_sk_m_val,   1) if _sk_m_val   is not None else None,
            "mdape_m":  float(mdape_mon[mk]) if mk in mdape_mon else None,
            "dm_p_m":   _dm_p(dm_row_m),
            "dm_sig_m": _dm_s(dm_row_m),
            "series":   {},
            "history":  history,
            "history_m": history_m,
            "proj":     {},
            "proj_m":   proj_m_dict.get(mk, {}),
            "proj_scenarios":   {},
            "proj_m_scenarios": proj_m_scenarios_dict.get(mk, {}),
            "series_m": series_m_dict.get(mk, {}),
            "wr_by_h":  wr_by_h_dict.get(mk, {}),
            "nearest_city":    _mine_city_lookup.get(mk.lower().replace("_"," "), (None, None))[0],
            "nearest_city_km": _mine_city_lookup.get(mk.lower().replace("_"," "), (None, None))[1],
        }

    for cid in clusters:
        clusters[cid]["forecast"] = {"mines": {}}
    for mk, fdata in mine_forecast.items():
        cid = mine_to_cluster.get(mk)
        if cid and cid in clusters:
            clusters[cid]["forecast"]["mines"][mk] = fdata

    attached = sum(1 for cl in clusters.values() if cl["forecast"]["mines"])
    print(f"   {len(mine_forecast)} mines loaded → attached to {attached} clusters")
except Exception as e:
    print(f"   ⚠ Forecast data skipped: {e}")
    import traceback; traceback.print_exc()
    for cid in clusters:
        clusters[cid].setdefault("forecast", {"mines": {}})

# ─── STEP 9b: SUBTEL — FIBRA ÓPTICA + SEÑAL TELEFÓNICA ───────────────────────
import urllib.request, urllib.parse, ssl as _ssl

# macOS ships without updated CA bundle for some govt sites — unverified context is acceptable here
_ssl_ctx = _ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = _ssl.CERT_NONE

def _round_coords(geom, decimals=5):
    """Round GeoJSON geometry coordinates in-place to reduce JSON size."""
    t = geom.get("type","")
    coords = geom.get("coordinates")
    if coords is None:
        return
    def rnd(c):
        if isinstance(c[0], (int, float)):
            return [round(c[0], decimals), round(c[1], decimals)]
        return [rnd(x) for x in c]
    geom["coordinates"] = rnd(coords)

def fetch_arcgis_layer(service_url, label="", bbox=None, max_features=None,
                       out_fields="*", paginate=True):
    """Fetch features from an ArcGIS FeatureServer layer as GeoJSON.
    bbox: (xmin, ymin, xmax, ymax) in WGS84 to spatially filter.
    max_features: cap total features.
    out_fields: comma-separated field names to fetch (reduces payload size).
    paginate: False for MapServers that don't support resultRecordCount/resultOffset.
    """
    base_q = service_url.rstrip("/") + "/query"
    page_size = min(1000, max_features) if max_features else 1000
    params_base = {
        "where": "1=1", "outFields": out_fields, "f": "geojson",
        "outSR": "4326",
    }
    if paginate:
        params_base["resultRecordCount"] = str(page_size)
    if bbox:
        params_base["geometry"] = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
        params_base["geometryType"] = "esriGeometryEnvelope"
        params_base["inSR"] = "4326"
        params_base["spatialRel"] = "esriSpatialRelIntersects"
    features = []
    offset = 0
    while True:
        params = dict(params_base)
        if offset > 0:
            params["resultOffset"] = str(offset)
        url = base_q + "?" + urllib.parse.urlencode(params)
        try:
            with urllib.request.urlopen(url, timeout=30, context=_ssl_ctx) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            if offset == 0:
                print(f"   ⚠ SUBTEL {label} failed: {e}")
            break
        batch = data.get("features", [])
        for feat in batch:
            if "geometry" in feat and feat["geometry"]:
                _round_coords(feat["geometry"])
        features.extend(batch)
        if not paginate:
            break
        if len(batch) < page_size:
            break
        if max_features and len(features) >= max_features:
            break
        offset += len(batch)
    return features

print("🌐 Fetching SUBTEL data (fibra óptica + señal telefónica) …")

SUBTEL_BASE = "https://licancabur.subtel.gob.cl/server/rest/services"
# Bounding box covering Chile's copper mining regions (Regions XV, I, II, III, IV + V)
# lon_min, lat_min, lon_max, lat_max  (WGS84)
MINING_BBOX = (-73.0, -35.0, -65.5, -17.0)

# ── Fibra óptica ──────────────────────────────────────────────────────────────
# 1) Silica Networks 2024 (FeatureServer)
SILICA_BASE = f"{SUBTEL_BASE}/Silica_Networks_of213_2024/FeatureServer"
fibra_features = []
for layer_id, lbl in [(19, "Troncal"), (2, "Tendidos"), (21, "Sitios"), (20, "POIIT")]:
    feats = fetch_arcgis_layer(f"{SILICA_BASE}/{layer_id}", lbl,
                               out_fields="name,descriptio")
    for f in feats:
        f.setdefault("properties", {})["_layer"] = lbl
    fibra_features.extend(feats)
    print(f"   Fibra – {lbl}: {len(feats)} features")

# 2) Red Troncal ClaroVTR (MapServer/1 — polylines con capacidad Gbps)
# No usa bbox porque el MapServer no soporta filtro espacial vía query params
feats_clvtr = fetch_arcgis_layer(
    f"{SUBTEL_BASE}/Red_Troncal_ClaroVTR/MapServer/1",
    "Red_Troncal_ClaroVTR",
    out_fields="NOMB_RED,CAPACIDAD,TIPO_TENDI,Gbps",
    paginate=False,
)
for f in feats_clvtr:
    f.setdefault("properties", {})["_layer"] = "Red_Troncal"
fibra_features.extend(feats_clvtr)
print(f"   Fibra – Red_Troncal ClaroVTR: {len(feats_clvtr)} features")

fibra_geojson = {"type": "FeatureCollection", "features": fibra_features}

# ── Señal telefónica ──────────────────────────────────────────────────────────
# 1) Estaciones de Eficiencia (grid de cobertura) — muestra 1000/operador
EF_SERVICES = [
    (f"{SUBTEL_BASE}/Estaciones_Eficiencia_Claro/FeatureServer/0",    "Claro"),
    (f"{SUBTEL_BASE}/Estaciones_Eficiencia_Entel/FeatureServer/0",    "Entel"),
    (f"{SUBTEL_BASE}/Estaciones_Eficiencia_Movistar/FeatureServer/0", "Movistar"),
    (f"{SUBTEL_BASE}/Estaciones_Eficiencia_Wom/FeatureServer/0",      "Wom"),
]
senal_features = []
for svc_url, operador in EF_SERVICES:
    feats = fetch_arcgis_layer(svc_url, operador, bbox=MINING_BBOX, max_features=1000,
                               out_fields="banda,eficiencia,region")
    for f in feats:
        p = f.setdefault("properties", {})
        p["_operador"] = operador
        p["_tipo"]     = "eficiencia"
    senal_features.extend(feats)
    print(f"   Señal eficiencia – {operador}: {len(feats)} features")

# 2) Torres físicas 4G/5G (nov 2025) — todas dentro de bbox minero
TORRE_SERVICES = [
    (f"{SUBTEL_BASE}/Claro_4G_nov2025/FeatureServer/0",    "Claro",    "4G"),
    (f"{SUBTEL_BASE}/Claro_5G_nov2025/FeatureServer/0",    "Claro",    "5G"),
    (f"{SUBTEL_BASE}/Entel_4G_nov2025/FeatureServer/0",    "Entel",    "4G"),
    (f"{SUBTEL_BASE}/Entel_5G_nov2025/FeatureServer/0",    "Entel",    "5G"),
    (f"{SUBTEL_BASE}/Movistar_4G_nov2025/FeatureServer/0", "Movistar", "4G"),
    (f"{SUBTEL_BASE}/Movistar_5G_nov2025/FeatureServer/0", "Movistar", "5G"),
    (f"{SUBTEL_BASE}/Wom_4G_nov2025/FeatureServer/0",      "Wom",      "4G"),
    (f"{SUBTEL_BASE}/Wom_5G_nov2025/FeatureServer/0",      "Wom",      "5G"),
]
for svc_url, operador, gen in TORRE_SERVICES:
    feats = fetch_arcgis_layer(svc_url, f"{operador}_{gen}", bbox=MINING_BBOX,
                               out_fields="empresa,tecnologí,tipo_zona_,codigo_est")
    for f in feats:
        p = f.setdefault("properties", {})
        p["_operador"] = operador
        p["_tipo"]     = "torre"
        p["_gen"]      = gen
    senal_features.extend(feats)
    print(f"   Señal torres – {operador} {gen}: {len(feats)} features")

senal_geojson = {"type": "FeatureCollection", "features": senal_features}
print(f"   Total fibra={len(fibra_features)}, señal={len(senal_features)}")

# ─── STEP 10: FINAL DATA BUNDLE ──────────────────────────────────────────────
all_years=sorted({int(y) for c in clusters.values() for y in c["production"]})
min_yr=min(all_years) if all_years else 1990
max_yr=max(all_years) if all_years else 2025

data_bundle={
    "clusters":clusters,
    "faenas":all_faenas,          # grouped by IdFaena — used for sidebar detail
    "installations":all_installations,  # one per CSV row — used for map markers
    "ruido_installations":ruido_installations,  # unassigned (HDBSCAN noise)
    "subestaciones":subestaciones,
    "centrales":centrales,
    "desaladoras":desaladoras,
    "relaves":relaves_all,
    "train_lines":train_lines,
    "estaciones":estaciones_pts,
    "seia":seia_projects,
    "sigex_meta":SIGEX_ETAPA_META,
    "sigex_sondajes_clusters": sigex_sondajes_clusters,
    "areas_protegidas":areas_protegidas_geojson,
    "fibra":fibra_geojson,
    "senal":senal_geojson,
    "puertos":puertos,
    "ciudades":CIUDADES_CHILE,
    "config":{
        "default_year":DEFAULT_YEAR,"min_year":min_yr,"max_year":max_yr,
        "water_factor":WATER_M3_PER_TON,"elec_factor":ELEC_MWH_PER_TON,
        "zoom_threshold":ZOOM_THRESHOLD,"estado_colors":ESTADO_COLORS,
    },
}
data_json=json.dumps(data_bundle,ensure_ascii=False,separators=(",",":"))

# ─── STEP 10b: OPTIMIZATION DATA ──────────────────────────────────────────────
print("🎯 Loading optimization data …")
_opt_slim = {"clusters": {}, "validation": {}, "radius_km": 12}
try:
    with open(OPT_JSON, encoding="utf-8") as _f:
        _opt_raw = json.load(_f)
    _opt_slim["validation"] = _opt_raw.get("validation", {})
    _opt_slim["radius_km"]  = _opt_raw.get("radius_km", 12)
    for _cid, _cl in _opt_raw.get("clusters", {}).items():
        _slim_cl = {
            "id": _cl.get("id", _cid),
            "label": _cl.get("label", _cid),
            "centroid": _cl.get("centroid", []),
            "stats": _cl.get("stats", {}),
            "exploration_sites": _cl.get("exploration_sites", [])[:15],
            "seia_projects": [p for p in _cl.get("seia_projects", [])
                              if p.get("estado") == "Aprobado"][:12],
            "models": {},
        }
        for _mkey in ["M1", "M3", "M4", "M5", "M7", "TM", "LP", "FM", "RE", "DH"]:
            _m = _cl.get("models", {}).get(_mkey, {})
            if _m:
                _mdata = {k: v for k, v in _m.get("data", {}).items() if k != "surface"}
                _slim_cl["models"][_mkey] = {
                    "name": _m.get("name", ""),
                    "formula": _m.get("formula", ""),
                    "color": _m.get("color", ""),
                    "data": _mdata,
                }
        _slim_cl["pillar_scores"] = _cl.get("stats", {}).get("pillar_scores", {})
        _slim_cl["cts_label"]     = _cl.get("stats", {}).get("cts_label", "")
        _slim_cl["cts_n_growing"]   = _cl.get("stats", {}).get("cts_n_growing", 0)
        _slim_cl["cts_n_declining"] = _cl.get("stats", {}).get("cts_n_declining", 0)
        _opt_slim["clusters"][_cid] = _slim_cl
    print(f"   ✓ {len(_opt_slim['clusters'])} clusters loaded")
except FileNotFoundError:
    print(f"   ⚠  {OPT_JSON} not found — optimization layer disabled")
opt_json = json.dumps(_opt_slim, ensure_ascii=False, separators=(",", ":"))

# ─── STEP 11: HTML ────────────────────────────────────────────────────────────
print("🎨 Building HTML …")

html = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>⛏️ Dashboard Minero Chile</title>
<link  rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}

/* ═══════════════════════════════════════════════════════
   iOS LIGHT THEME — SF Pro, system white, semantic blue
   ═══════════════════════════════════════════════════════ */
:root{
  /* System background layers */
  --bg:   oklch(99.2% 0.002 248);
  --bg2:  oklch(96.5% 0.005 248);
  --bg3:  oklch(91.5% 0.006 248);
  --bg4:  oklch(83%   0.008 248);
  /* Accent: iOS blue */
  --accent:  oklch(57% 0.2 251);
  --accent2: oklch(49% 0.17 260);
  /* Status — iOS semantic */
  --green: oklch(53% 0.19 152);
  --red:   oklch(53% 0.22 24);
  /* Labels */
  --text:  oklch(17% 0.008 248);
  --text2: oklch(46% 0.01  248);
  --text3: oklch(62% 0.008 248);
  --sidebar:480px;
  /* Blue tints */
  --blue-tint:   rgba(0,122,255,0.07);
  --blue-border: rgba(0,122,255,0.22);
  --blue-glow:   rgba(0,122,255,0.12);
  /* Separator */
  --sep: rgba(60,60,67,0.13);
  /* Optimization panel (white overlay) */
  --opt-bg:     rgba(255,255,255,0.95);
  --opt-border: rgba(60,60,67,0.15);
  --opt-accent: #f59e0b;
}

html,body{height:100%;overflow:hidden;font-family:-apple-system,BlinkMacSystemFont,'SF Pro Text',system-ui,'Segoe UI',sans-serif;
          background:var(--bg);color:var(--text);font-size:13px}
#app{display:flex;height:100vh}
#sidebar{width:var(--sidebar);min-width:var(--sidebar);height:100%;
         background:var(--bg2);
         display:flex;flex-direction:column;position:relative;
         border-right:1px solid var(--sep);overflow:hidden;z-index:1000}
#map{flex:1;height:100%}

/* SIGEX FILTER BOX */
#sigex-box{display:none;position:absolute;top:8px;right:8px;z-index:1100;
           background:rgba(255,255,255,0.95);border:1px solid var(--sep);border-radius:12px;
           padding:10px 12px;width:220px;font-size:11px;overflow:hidden;
           box-shadow:0 4px 20px rgba(0,0,0,.1);backdrop-filter:blur(16px);
           -webkit-backdrop-filter:blur(16px)}
#sigex-box.open{display:block}
.sf-section{margin-bottom:8px}
.sf-label{font-size:10px;font-weight:600;color:var(--text3);text-transform:uppercase;
          letter-spacing:.06em;margin-bottom:4px}
.sf-pills{display:flex;flex-wrap:wrap;gap:3px}
.sf-pill{font-size:10px;padding:2px 7px;border-radius:10px;border:1px solid var(--bg4);
         background:var(--bg);color:var(--text2);cursor:pointer;transition:all .15s;white-space:nowrap}
.sf-pill.on{border-color:var(--accent);color:var(--accent);background:var(--blue-tint)}
.sf-select{width:100%;background:var(--bg);border:1px solid var(--bg4);
           color:var(--text);border-radius:8px;padding:3px 6px;font-size:11px}
#sigex-count{font-size:10px;color:var(--text3);margin-top:6px;padding-top:6px;
             border-top:1px solid var(--sep)}

/* FORECAST COLUMN */
#fc-tab{width:14px;flex-shrink:0;height:100%;background:var(--bg3);
        border-right:1px solid var(--sep);cursor:pointer;display:none;
        align-items:center;justify-content:center;transition:background .15s;z-index:999}
#fc-tab:hover{background:var(--bg4)}
#fc-tab-icon{color:var(--accent);font-size:13px;font-weight:700;user-select:none;
             writing-mode:horizontal-tb;line-height:1}
#forecast-col{width:0;overflow:hidden;transition:width .3s ease;background:var(--bg);
              border-right:1px solid var(--sep);flex-shrink:0;height:100%;
              display:flex;flex-direction:column}
#forecast-col.open{width:390px}
#fc-inner{width:390px;height:100%;overflow-y:auto;padding:12px 14px;
          scrollbar-width:thin;scrollbar-color:var(--bg4) transparent}

/* HEADER */
#s-header{padding:14px 16px 10px;
          border-bottom:1px solid var(--sep);
          background:rgba(248,248,250,0.9);backdrop-filter:blur(20px);
          -webkit-backdrop-filter:blur(20px);flex-shrink:0}
#s-title{font-size:17px;font-weight:700;letter-spacing:-.02em;
         color:var(--text);margin-bottom:8px}
#s-title span{color:var(--accent);font-weight:600}
.year-row{display:none;align-items:center;gap:8px}
.year-label{font-size:12px;color:var(--text2);font-weight:500}
#year-val{font-size:15px;font-weight:700;color:var(--accent);min-width:38px;
          font-variant-numeric:tabular-nums}
#year-slider{flex:1;accent-color:var(--accent);cursor:pointer}

/* LAYER BUTTONS */
#layer-controls{display:flex;flex-wrap:wrap;gap:5px;padding:8px 12px;
                border-bottom:1px solid var(--sep);
                background:var(--bg2);flex-shrink:0}
.layer-btn{display:flex;align-items:center;gap:5px;padding:4px 10px;
           border-radius:20px;border:1px solid var(--bg4);cursor:pointer;
           font-size:11px;background:var(--bg);color:var(--text2);
           transition:all .15s ease;user-select:none;white-space:nowrap}
.layer-btn:hover{background:var(--blue-tint);border-color:var(--blue-border);color:var(--accent)}
.layer-btn.active{border-color:var(--blue-border);color:var(--accent);background:var(--blue-tint)}
.layer-btn .dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}

/* PILLAR PANEL */
#pilar-panel{position:fixed;bottom:36px;right:12px;z-index:2000;
  background:var(--opt-bg);border:1px solid var(--opt-border);border-top:2px solid var(--opt-accent);border-radius:8px;
  padding:9px 10px;width:188px;box-shadow:0 8px 24px rgba(0,0,0,0.12);
  display:none;font-size:12px;color:var(--text); transition: width 0.2s ease;
  backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);
  max-height:85vh; overflow-y:auto; scrollbar-width:thin; scrollbar-color:var(--text3) transparent;}
#pilar-panel.open{display:block}
#pilar-panel.expanded{width:360px}
#pilar-panel h4{font-size:10px;font-weight:700;color:var(--text3);text-transform:uppercase;
  letter-spacing:.07em;margin-bottom:8px}
.pilar-row{display:flex;align-items:center;gap:8px;cursor:pointer;
  border-radius:7px;padding:5px 6px;transition:background .12s;user-select:none}
.pilar-row:hover{background:rgba(0,0,0,0.04)}
.pilar-row input[type=checkbox]{accent-color:var(--opt-accent);width:13px;height:13px;cursor:pointer;flex-shrink:0}
.pilar-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.pilar-label{flex:1;color:var(--text);font-size:12px;line-height:1.3}
.pilar-label b{font-family:monospace;font-weight:700;font-size:11px;color:var(--text2)}

/* INLINE PILLAR DETAIL */
.pilar-inline-detail{margin:4px 0 8px 12px; padding:10px 12px; 
  background:#ffffff; 
  border:1px solid #e2e8f0;
  border-left:3px solid var(--opt-border); 
  border-radius:8px; display:none;
  box-shadow:0 4px 12px rgba(0,0,0,0.15);}
.pid-title{font-size:12px;font-weight:700;color:#0f172a;margin-bottom:3px}
.pid-sub{font-size:10px;color:#64748b;margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid #e2e8f0}
.sc-header{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px}
.sc-title{font-size:14px;font-weight:700;color:#f1f5f9;line-height:1.25}
.sc-sub{font-size:10px;color:#94a3b8;margin-top:3px}
.sc-close{background:none;border:none;cursor:pointer;color:#94a3b8;font-size:16px;line-height:1;padding:0;flex-shrink:0}
.sc-close:hover{color:#f1f5f9}
.sc-pilar-block{border-top:1px solid rgba(255,255,255,0.08);padding:8px 0 5px}
.sc-pilar-block:first-child{border-top:none;padding-top:0}
.sc-pilar-head{display:flex;align-items:center;gap:5px;margin-bottom:3px}
.sc-pid{font-family:monospace;font-size:11px;font-weight:700;width:22px;flex-shrink:0}
.sc-bar-wrap{flex:1;height:5px;background:#2d3140;border-radius:3px;overflow:hidden}
.sc-bar-fill{height:100%;border-radius:3px}
.sc-pct{font-size:11px;font-weight:600;width:28px;text-align:right;flex-shrink:0}
.sc-rank{font-size:10px;color:#94a3b8;width:48px;text-align:right;flex-shrink:0}
.sc-formula{
  font-family: 'SF Mono', Consolas, 'Courier New', monospace;
  font-size: 10px;
  color: #2563eb; 
  background: rgba(59, 130, 246, 0.06);
  border: 1px solid rgba(59, 130, 246, 0.2);
  padding: 6px 8px 6px 6px;
  border-radius: 6px;
  margin: 4px 0 8px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  letter-spacing: 0.01em;
  white-space:normal;word-break:break-word;line-height:1.4;
}
.sc-formula::before {
  content: 'ƒ(x)';
  background: #3b82f6;
  color: #ffffff;
  padding: 2px 5px;
  border-radius: 4px;
  font-size: 8px;
  font-family: -apple-system, sans-serif;
  font-weight: 800;
  letter-spacing: 0;
  flex-shrink:0;
  box-shadow: 0 1px 2px rgba(59,130,246,0.3);
}
/* Stats table per pillar */
.sc-stats-tbl{width:100%;border-collapse:collapse;margin:4px 0 2px;font-size:9.5px}
.sc-stats-tbl th{text-align:left;color:#64748b;font-weight:600;padding:2px 6px;border-bottom:1px solid #e2e8f0}
.sc-stats-tbl td{padding:2px 6px;color:#334155}
.sc-stats-tbl td:last-child{text-align:right;font-family:monospace;font-weight:600;color:#0f172a}
.sc-stats-tbl tr:nth-child(even) td{background:#f8fafc}
.sc-drivers{display:flex;flex-direction:column;gap:3px;margin-top:3px}
.sc-driver{font-size:9.5px;padding:3px 8px;border-radius:6px;line-height:1.5;
  display:flex;align-items:baseline;gap:4px}
.sc-driver-name{font-weight:600}
.sc-driver-why{color:inherit;opacity:.85;font-style:italic}
.sc-driver.grow{background:#dcfce7;color:#166534;border:1px solid #bbf7d0}
.sc-driver.decline{background:#fee2e2;color:#991b1b;border:1px solid #fecaca}
.sc-driver.neutral{background:#f1f5f9;color:#334155;border:1px solid #e2e8f0}
.sc-no-markers{font-size:9px;color:#64748b;margin-top:4px;padding:3px 6px;
  background:#f8fafc;border-radius:5px;font-style:italic;border:1px solid #e2e8f0}
.sc-tm-insight{margin-top:8px;padding:8px 10px;background:#dcfce7;border-radius:9px;
  font-size:11px;color:#064e3b;line-height:1.6;border:1px solid #86efac;border-left:3px solid #059669}
.sc-explain{font-size:9px;color:#475569;margin-top:3px;padding:3px 8px;line-height:1.5;font-style:italic}

/* SEARCH */
#search-wrap{padding:8px 12px;border-bottom:1px solid var(--sep);
             background:var(--bg2);flex-shrink:0}
#search-input{width:100%;background:var(--bg3);border:1px solid transparent;
              color:var(--text);border-radius:10px;padding:6px 12px;font-size:13px;
              outline:none;transition:border-color .15s,box-shadow .15s,background .15s}
#search-input::placeholder{color:var(--text3)}
#search-input:focus{background:var(--bg);border-color:var(--accent);
                    box-shadow:0 0 0 3px var(--blue-glow)}

/* BODY */
#s-body{flex:1;overflow-y:auto;scrollbar-width:thin;
        scrollbar-color:var(--bg4) transparent}
*{scrollbar-width:thin;scrollbar-color:var(--bg4) transparent}
#s-body::-webkit-scrollbar{width:4px}
#s-body::-webkit-scrollbar-track{background:transparent}
#s-body::-webkit-scrollbar-thumb{background:var(--bg4);border-radius:2px}
#s-body::-webkit-scrollbar-thumb:hover{background:var(--text3)}

/* CLUSTER LIST */
#cluster-list{padding:8px 12px}
.cl-item{display:flex;align-items:center;gap:10px;padding:9px 10px;
         border-radius:10px;cursor:pointer;transition:background .15s;
         margin-bottom:2px}
.cl-item:hover{background:var(--bg3)}
.cl-item.selected{background:var(--blue-tint);outline:1px solid var(--blue-border)}
.cl-dot{width:13px;height:13px;border-radius:4px;flex-shrink:0}
.cl-mine{font-size:13px;font-weight:600;line-height:1.2;color:var(--text)}
.cl-sub{font-size:11px;color:var(--text3);margin-top:1px}
.cl-right{text-align:right;font-size:11px;color:var(--text2);flex-shrink:0}

/* CLUSTER DETAIL */
#cluster-detail{display:none;padding:14px 16px}
#back-btn{display:flex;align-items:center;gap:5px;cursor:pointer;
          color:var(--accent);font-size:15px;margin-bottom:16px;
          background:none;border:none;padding:0;transition:opacity .12s;font-weight:400}
#back-btn:hover{opacity:0.7}
.det-id{font-size:22px;font-weight:700;letter-spacing:-.02em;color:var(--text)}
.det-region{font-size:13px;color:var(--text2);margin-top:3px;font-weight:400}
.det-mine{font-size:13px;color:var(--accent);margin-top:4px;font-weight:500}

/* KPI */
.kpi-row{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin:14px 0}
.kpi{background:var(--bg);border-radius:12px;padding:10px 8px;text-align:center;
     box-shadow:0 1px 3px rgba(0,0,0,.06),0 0 0 1px var(--sep)}
.kpi-val{font-size:18px;font-weight:700;color:var(--accent);
         font-variant-numeric:tabular-nums}
.kpi-lbl{font-size:9px;color:var(--text3);margin-top:3px;text-transform:uppercase;
         letter-spacing:.5px;font-weight:500}

/* SECTION TITLE */
.sec{font-size:11px;font-weight:600;color:var(--text3);text-transform:uppercase;
     letter-spacing:.06em;margin:14px 0 8px;display:flex;align-items:center;gap:6px}

/* CHART */
.chart-wrap{background:var(--bg);border:1px solid var(--sep);
            border-radius:12px;padding:10px;
            margin-bottom:6px;position:relative;height:155px;
            box-shadow:0 1px 4px rgba(0,0,0,.05)}

/* CAPACITY BARS */
.cap-item{margin-bottom:9px}
.cap-row{display:flex;justify-content:space-between;font-size:11px;margin-bottom:3px}
.cap-bar-bg{height:6px;border-radius:3px;background:var(--bg3);overflow:hidden}
.cap-bar{height:100%;border-radius:3px;transition:width .4s}
.cap-note{font-size:10px;color:var(--text3);margin-top:2px}

/* EMPRESA CHART */
.emp-row{display:flex;align-items:center;gap:7px;margin-bottom:5px}
.emp-name{font-size:11px;color:var(--text);width:200px;overflow:hidden;
           text-overflow:ellipsis;white-space:nowrap;flex-shrink:0}
.emp-bar-wrap{flex:1;height:14px;background:var(--bg3);border-radius:3px;overflow:hidden}
.emp-bar{height:100%;border-radius:3px;display:flex;align-items:center;
         padding-left:5px;font-size:9px;font-weight:700;color:#fff;
         min-width:14px;transition:width .4s}
.emp-pct{font-size:10px;color:var(--text2);width:34px;text-align:right;flex-shrink:0}

/* RELAVES TABLE */
.rel-table{width:100%;border-collapse:collapse;font-size:11px}
.rel-table th{background:var(--bg2);color:var(--text2);padding:5px 6px;text-align:left;font-weight:600}
.rel-table td{padding:4px 6px;border-bottom:1px solid var(--sep)}
.rel-table tr:last-child td{border-bottom:none}
.rel-filter-btn{background:var(--bg);border:1px solid var(--bg4);color:var(--text2);
  border-radius:14px;padding:3px 9px;font-size:10px;cursor:pointer;display:flex;align-items:center;gap:2px;
  transition:background .15s,border-color .15s}
.rel-filter-btn:hover{background:var(--bg3)}
.rel-filter-btn.active{background:var(--blue-tint);border-color:var(--accent);color:var(--accent)}
.rel-ctrl-wrap{background:rgba(255,255,255,0.97);border:1px solid var(--sep);
  border-radius:12px;padding:7px 8px;backdrop-filter:blur(20px);
  -webkit-backdrop-filter:blur(20px);min-width:130px;
  box-shadow:0 4px 20px rgba(0,0,0,.12)}
.rel-ctrl-title{font-size:11px;font-weight:600;color:var(--text);margin-bottom:6px;
  display:flex;align-items:center;justify-content:space-between;gap:6px}
#rel-ctrl-count{font-size:9px;font-weight:400;color:var(--text3)}
.rel-ctrl-btn{display:flex;align-items:center;width:100%;background:transparent;
  border:none;color:var(--text2);font-size:11px;padding:4px 5px;border-radius:7px;cursor:pointer;
  text-align:left;transition:background .12s}
.rel-ctrl-btn:hover{background:var(--bg3)}
.rel-ctrl-btn.active{background:var(--blue-tint);color:var(--accent);font-weight:600}
.e-dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:3px}

/* MINE ROSTER TABLE */
.mine-table{width:100%;border-collapse:collapse;font-size:11px;margin-bottom:4px}
.mine-table th{background:var(--bg2);color:var(--text2);padding:5px 6px;font-weight:600;
               white-space:nowrap}
.mine-table th:nth-child(3),.mine-table th:nth-child(4){text-align:right}
.mine-table td{padding:4px 6px;border-bottom:1px solid var(--sep)}
.mine-table td:nth-child(3),.mine-table td:nth-child(4){text-align:right}
.mine-table tr:last-child td{border-bottom:none}
.mine-table tr:hover td{background:var(--bg2)}
.mine-table .pct-bar{display:inline-block;height:5px;border-radius:2px;
                     vertical-align:middle;margin-right:4px;background:var(--accent);
                     opacity:0.7;transition:width .3s}

/* RATIO PANEL */
.ratio-grid{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:8px}
.ratio-card{background:var(--bg);border-radius:12px;padding:10px;
            border:1px solid var(--sep);text-align:center}
.ratio-formula{font-size:10px;color:var(--text3);margin-bottom:3px;font-style:italic}
.ratio-val{font-size:18px;font-weight:700;color:var(--accent2);line-height:1}
.ratio-desc{font-size:9px;color:var(--text3);margin-top:2px}

/* INFRA LIST */
.infra-list{display:flex;flex-direction:column;gap:4px;margin-top:4px}
.infra-item{display:flex;align-items:center;gap:7px;padding:7px 10px;
            background:var(--bg);border-radius:10px;font-size:11px;cursor:pointer;
            border:1px solid var(--sep);transition:background .12s}
.infra-item:hover{background:var(--bg2)}
.infra-icon{font-size:13px;width:18px;text-align:center}
.infra-name{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.infra-dist{font-size:10px;color:var(--text3)}

/* FAENAS */
.faena-list{max-height:260px;overflow-y:auto;scrollbar-width:thin;
            scrollbar-color:var(--bg3) transparent}
.faena-item{display:flex;align-items:center;gap:8px;padding:6px 8px;
            border-radius:8px;cursor:pointer;transition:background .12s}
.faena-item:hover{background:var(--bg3)}
.f-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.f-name{flex:1;font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.f-meta{font-size:10px;color:var(--text3)}
.scroll-hint{text-align:center;color:var(--text3);font-size:10px;padding:7px;font-style:italic}

/* MINING DESAL BADGE */
.mining-badge{display:inline-block;background:rgba(0,122,255,0.1);color:var(--accent);
              font-size:9px;padding:1px 5px;border-radius:10px;
              font-weight:700;margin-left:5px;vertical-align:middle}

/* LEAFLET */
.leaflet-container{background:#f0ede8 !important}
.cluster-tooltip,.faena-tooltip{
  background:rgba(255,255,255,0.97);color:var(--text);
  border:1px solid var(--sep);
  border-radius:8px;font-size:12px;padding:5px 10px;
  box-shadow:0 4px 16px rgba(0,0,0,.12)}
.infra-marker{width:25px;height:25px;border-radius:50%;display:flex;
              align-items:center;justify-content:center;font-size:12px;
              border:2px solid rgba(255,255,255,.7);cursor:pointer;
              box-shadow:0 1px 4px rgba(0,0,0,.25)}
.i-sub{background:#7c2d12} .i-cen{background:#7f1d1d}
.i-des{background:#1e3a8a} .i-des-mining{background:#1e40af;border-color:rgba(0,122,255,0.5);border-width:2.5px}
.i-rel{background:#3d1708} .i-seia-ec{background:#7c2d12}
.i-seia-ap{background:#14532d} .i-est{background:#1e1b4b}
.leaflet-div-icon{background:transparent;border:none}

/* TOOLTIP */
#tip{position:fixed;pointer-events:none;background:rgba(255,255,255,0.97);color:var(--text);
     border:1px solid var(--sep);
     border-radius:10px;padding:7px 11px;font-size:11px;
     z-index:9999;display:none;
     box-shadow:0 4px 20px rgba(0,0,0,.12);
     max-width:260px;line-height:1.5}

/* SIGEX legend pill */
.seia-legend{display:flex;flex-wrap:wrap;align-items:center;gap:6px 10px;
             font-size:10px;margin:5px 0 8px;padding:6px 10px;
             background:var(--bg);border-radius:10px;
             border:1px solid var(--sep)}
.sl-dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:3px}

/* RANK + YOY BADGES */
.rank-badge{display:inline-flex;align-items:center;justify-content:center;
            width:20px;height:20px;border-radius:5px;font-size:9px;font-weight:700;
            background:var(--bg3);color:var(--text3);flex-shrink:0}
.rank-badge.top3{background:rgba(0,122,255,0.1);color:var(--accent);
                 border:1px solid rgba(0,122,255,0.25)}
.yoy{font-size:9px;font-weight:700;padding:1px 4px;border-radius:3px;white-space:nowrap;margin-left:3px}
.yoy-pos{background:rgba(52,199,89,0.12);color:#1a8e3e}
.yoy-neg{background:rgba(255,59,48,0.1);color:#c0392b}
.yoy-neu{background:var(--bg3);color:var(--text3)}

/* NATIONAL TOTAL BAR */
#nat-total{font-size:11px;color:var(--text2);margin-top:8px;padding-top:8px;
           border-top:1px solid var(--sep);display:flex;align-items:center;
           justify-content:space-between;flex-wrap:wrap;gap:4px}
#nat-total b{color:var(--text);font-weight:600}

/* TREND / LIFECYCLE BADGE */
.trend-badge{display:inline-flex;align-items:center;gap:4px;padding:2px 8px;
             border-radius:12px;font-size:10px;font-weight:600}
.trend-up  {background:rgba(52,199,89,0.1);color:#1a8e3e}
.trend-flat{background:rgba(255,149,0,0.1);color:#c47a00}
.trend-down{background:rgba(255,59,48,0.1);color:#c0392b}
.trend-nd  {background:var(--bg3);color:var(--text3)}

/* SPARKLINE inline SVG wrapper */
.sparkline-wrap{display:flex;justify-content:flex-end;margin:3px 0 2px}

/* RISK PANEL */
.risk-badge{display:inline-flex;align-items:center;gap:3px;padding:1px 6px;
            border-radius:10px;font-size:9px;font-weight:600;white-space:nowrap}
.risk-hi{background:rgba(255,59,48,0.1);color:#c0392b;border:1px solid rgba(255,59,48,0.2)}
.risk-md{background:rgba(255,149,0,0.1);color:#c47a00;border:1px solid rgba(255,149,0,0.2)}
.risk-lo{background:rgba(52,199,89,0.1);color:#1a8e3e;border:1px solid rgba(52,199,89,0.2)}
.risk-na{background:var(--bg3);color:var(--text3)}
/* Risk rows: full-border tint, no side stripe */
.mine-risk-row{display:flex;flex-direction:column;gap:4px;padding:8px 10px;
              background:var(--bg);border-radius:10px;margin-bottom:4px;
              border:1px solid var(--sep)}
.mine-risk-row.danger{background:rgba(255,59,48,0.04);border-color:rgba(255,59,48,0.15)}
.mine-risk-row.alert{background:rgba(255,149,0,0.04);border-color:rgba(255,149,0,0.15)}
.mine-risk-row.ok{background:rgba(52,199,89,0.04);border-color:rgba(52,199,89,0.15)}
.mine-risk-grid{display:grid;grid-template-columns:1fr 1fr;gap:3px 10px;font-size:10px;color:var(--text2)}

/* PORT MARKER */
.i-pue{background:#0c4a6e}

/* SCENARIO TOGGLE */
.sc-btn{background:var(--bg);border:1px solid var(--bg4);color:var(--text3);
        border-radius:6px;padding:2px 7px;font-size:9px;cursor:pointer;
        transition:all .15s;font-weight:500}
.sc-btn.active{background:var(--blue-tint);border-color:var(--blue-border);
               color:var(--accent);font-weight:700}

/* CIUDAD LAYER */
.i-pob{background:#581c87;border-color:#e879f9;border-width:2px}

/* ── OPT CLUSTER DETAIL (left sidebar) ──────────────────────────────────── */
#opt-cluster-section{border-top:1px solid var(--sep);margin-top:12px;padding-top:4px}
.opt-score-table{width:100%;border-collapse:separate;border-spacing:0 3px;margin-bottom:8px}
.opt-score-row{cursor:default;border-radius:8px}
.opt-score-row td{padding:5px 7px;vertical-align:middle}
.opt-score-row td:first-child{border-radius:8px 0 0 8px;padding-left:9px}
.opt-score-row td:last-child{border-radius:0 8px 8px 0;padding-right:9px}
.opt-score-row:hover td{background:var(--bg3)}
.opt-mid{font-size:11px;font-weight:700;font-family:ui-monospace,monospace}
.opt-mname{font-size:10px;color:var(--text2);max-width:120px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.opt-bar-wrap{width:60px}
.opt-bar-bg{height:4px;background:var(--bg3);border-radius:2px;overflow:hidden}
.opt-bar-fill{height:100%;border-radius:2px;transition:width .35s}
.opt-pct{font-size:10px;font-weight:700;font-family:ui-monospace,monospace;text-align:right;white-space:nowrap;min-width:40px}
.opt-m-dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:4px;vertical-align:middle;flex-shrink:0}
.opt-conv-row{display:flex;align-items:center;gap:6px;margin-bottom:5px}
.opt-conv-bar{flex:1;height:5px;background:var(--bg3);border-radius:3px;overflow:hidden}
.opt-conv-fill{height:100%;border-radius:3px;transition:width .4s}
.opt-exp-item{display:flex;align-items:center;gap:6px;padding:4px 6px;border-radius:7px;
              font-size:10px;transition:background .12s}
.opt-exp-item:hover{background:var(--bg3)}
.opt-exp-name{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--text)}
.opt-exp-tipo{font-size:9px;color:var(--text3);white-space:nowrap}
.opt-radius-label{font-size:9px;color:var(--text3);margin-top:3px;margin-bottom:8px;
                  padding:3px 8px;background:rgba(52,199,89,0.08);border:1px solid rgba(52,199,89,0.2);
                  border-radius:6px;display:inline-block}

/* ── OPT PANEL ──────────────────────────────────────────────────────────── */
#opt-panel{
  display:none;position:absolute;top:8px;right:8px;z-index:1100;width:260px;
  background:rgba(255,255,255,0.92);
  border:1px solid var(--sep);border-radius:16px;overflow:hidden;
  box-shadow:0 8px 32px rgba(0,0,0,.1),0 2px 8px rgba(0,0,0,.06);
  backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
  transition:box-shadow .2s;
  font-family:-apple-system,BlinkMacSystemFont,'SF Pro Text',system-ui,sans-serif}
#opt-panel.open{display:block}
#opt-panel:hover{box-shadow:0 10px 40px rgba(0,0,0,.14),0 2px 10px rgba(0,0,0,.08)}
.op-accent{height:3px;background:linear-gradient(to right,var(--accent),#5ac8fa 55%,transparent)}
.op-head{padding:10px 14px 7px;border-bottom:1px solid var(--sep)}
.op-title{font-size:12px;font-weight:700;color:var(--accent);letter-spacing:.02em;
  display:flex;align-items:center;gap:5px}
.op-sub{font-size:10px;color:var(--text3);margin-top:2px;min-height:13px;
  transition:color .2s}
.op-sub b{color:var(--text);font-weight:600}
.op-chart-wrap{display:flex;justify-content:center;padding:6px 0 2px}
/* Legend */
.op-legend{padding:2px 14px 8px;display:flex;flex-direction:column;gap:5px}
.op-leg-row{display:flex;align-items:flex-start;gap:7px}
.op-leg-dot{width:6px;height:6px;border-radius:50%;flex-shrink:0;margin-top:3px}
.op-leg-name{font-size:10px;font-weight:600;color:var(--text2);line-height:1.3}
.op-leg-desc{font-size:9px;color:var(--text3);line-height:1.35}
/* Score rows */
.op-scores{padding:4px 14px 9px;display:flex;flex-direction:column;gap:7px}
.op-sc-row{display:flex;align-items:center;gap:6px}
.op-sc-dot{width:6px;height:6px;border-radius:50%;flex-shrink:0}
.op-sc-name{font-size:9px;font-weight:600;color:var(--text3);width:62px;
  flex-shrink:0;white-space:nowrap;letter-spacing:.01em}
.op-sc-track{flex:1;height:4px;background:var(--bg3);border-radius:2px;
  position:relative;overflow:visible}
.op-sc-fill{height:100%;border-radius:2px;position:absolute;top:0;
  transition:width .35s cubic-bezier(.4,0,.2,1)}
.op-sc-fill.norm{left:0}
.op-sc-fill.inv{right:0}
.op-sc-val{font-size:10px;font-weight:700;width:38px;text-align:right;
  flex-shrink:0;font-variant-numeric:tabular-nums;letter-spacing:-.01em;color:var(--text)}
/* Validation bar */
.op-val{padding:7px 14px 9px;border-top:1px solid var(--sep);
  display:flex;gap:6px;flex-wrap:wrap}
.op-pill{font-size:9px;font-weight:700;padding:2px 8px;border-radius:9px;
  letter-spacing:.03em;white-space:nowrap}
.op-pill-g{background:rgba(52,199,89,.1);color:#1a8e3e;border:1px solid rgba(52,199,89,.22)}
.op-pill-a{background:rgba(255,149,0,.1);color:#c47a00;border:1px solid rgba(255,149,0,.22)}
</style>
</head>
<body>
<div id="app">

<!-- ══════════════════ SIDEBAR ══════════════════ -->
<div id="sidebar">
  <div id="s-header">
    <div id="s-title">Dashboard Minero <span>Chile</span></div>
    <div class="year-row">
      <span class="year-label">Año</span>
      <input id="year-slider" type="range" min="1982" max="2025" value="2025" step="1"/>
      <span id="year-val">2025</span>
    </div>
    <div id="nat-total"></div>
  </div>

  <div id="layer-controls">
    <button type="button" class="layer-btn" id="btn-sub"   onclick="toggleLayer('sub')">
      <div class="dot" style="background:#7c2d12"></div>Subestaciones
    </button>
    <button type="button" class="layer-btn" id="btn-cen"   onclick="toggleLayer('cen')">
      <div class="dot" style="background:#7f1d1d"></div>Centrales
    </button>
    <button type="button" class="layer-btn" id="btn-des"   onclick="toggleLayer('des')">
      <div class="dot" style="background:#1e3a8a"></div>Desaladoras
    </button>
    <button type="button" class="layer-btn" id="btn-rel"   onclick="toggleLayer('rel')">
      <div class="dot" style="background:#3d1708"></div>Relaves
    </button>
    <button type="button" class="layer-btn" id="btn-seia"  onclick="toggleLayer('seia')">
      <div class="dot" style="background:#f59e0b"></div>SIGEX Sondajes
    </button>
    <button type="button" class="layer-btn" id="btn-sigexotros" onclick="toggleLayer('sigexotros')">
      <div class="dot" style="background:#94a3b8"></div>SIGEX Otros
    </button>
    <button type="button" class="layer-btn" id="btn-train" onclick="toggleLayer('train')">
      <div class="dot" style="background:#a78bfa"></div>Ferrocarriles
    </button>
    <button type="button" class="layer-btn" id="btn-ruido" onclick="toggleLayer('ruido')">
      <div class="dot" style="background:#6b7280"></div>Sin Clúster
    </button>
    <button type="button" class="layer-btn" id="btn-ap" onclick="toggleLayer('ap')">
      <div class="dot" style="background:#16a34a"></div>Áreas Prot.
    </button>
    <button type="button" class="layer-btn" id="btn-fibra" onclick="toggleLayer('fibra')">
      <div class="dot" style="background:#f97316"></div>Fibra Óptica
    </button>
    <button type="button" class="layer-btn" id="btn-senal" onclick="toggleLayer('senal')">
      <div class="dot" style="background:#a855f7"></div>Señal Telef.
    </button>
    <button type="button" class="layer-btn" id="btn-pue"   onclick="toggleLayer('pue')">
      <div class="dot" style="background:#0ea5e9"></div>Puertos
    </button>
    <button type="button" class="layer-btn" id="btn-pob"   onclick="toggleLayer('pob')">
      <div class="dot" style="background:#e879f9"></div>Ciudades
    </button>
    <button type="button" class="layer-btn" id="btn-opt" onclick="togglePilarPanel()">
      <div class="dot" style="background:#a78bfa"></div>Pilares ▾
    </button>
  </div>

  <div id="search-wrap">
    <input id="search-input" type="text" placeholder="Buscar clúster o faena …"
           oninput="onSearch(this.value)"/>
  </div>

  <div id="s-body">
    <div id="cluster-list"></div>

    <div id="cluster-detail">
      <button id="back-btn" onclick="deselectCluster()">← Volver a clústeres</button>

      <div class="det-id"    id="det-id"></div>
      <div class="det-region" id="det-label"></div>
      <div class="det-mine"   id="det-mine"></div>
      <div id="det-trend" style="margin-top:6px"></div>
      <button type="button" onclick="toggleForecastCol()" style="margin-top:10px;width:100%;background:var(--blue-tint);border:1px solid var(--blue-border);color:var(--accent);border-radius:10px;padding:8px 12px;font-size:12px;font-weight:600;cursor:pointer;text-align:center;font-family:inherit;">Ver pronóstico del modelo →</button>

      <div class="kpi-row">
        <div class="kpi"><div class="kpi-val" id="kpi-prod">—</div>
             <div class="kpi-lbl" title="Producción anual promedio 2020–2025, en miles de toneladas métricas">Producción (kTM)</div></div>
        <div class="kpi"><div class="kpi-val" id="kpi-faenas">—</div>
             <div class="kpi-lbl" title="Número de faenas e instalaciones en el clúster">Instalaciones</div></div>
        <div class="kpi"><div class="kpi-val" id="kpi-water">—</div>
             <div class="kpi-lbl" title="Producción actual como porcentaje del máximo histórico del clúster">% del Pico Hist.</div></div>
        <div class="kpi"><div class="kpi-val" id="kpi-elec">—</div>
             <div class="kpi-lbl" title="Tasa de Crecimiento Anual Compuesta de producción en los últimos 5 años (CAGR)">CAGR 5 Años</div></div>
        <div class="kpi"><div class="kpi-val" id="kpi-relaves">—</div>
             <div class="kpi-lbl" title="Depósitos de relaves (residuos mineros) actualmente en operación">Relaves Activos</div></div>
        <div class="kpi"><div class="kpi-val" id="kpi-ren">—</div>
             <div class="kpi-lbl" title="Porcentaje de la capacidad eléctrica instalada proveniente de fuentes renovables">% Energía Renv.</div></div>
      </div>

      <!-- ── 1. INDICADORES DEL VALLE (hidden) ── -->
      <div style="display:none">
        <div class="kpi-val" id="kpi-prod-growth">—</div>
        <div class="kpi-val" id="kpi-emp-growth">—</div>
      </div>

      <!-- ── 2. OPERACIONES EN EL VALLE ─────────────────────────────────── -->
      <div class="sec">Operaciones en el Valle
        <span id="op-total-badge" style="font-weight:400;font-size:10px;color:var(--text3)"></span>
      </div>
      <div id="operaciones-panel" style="margin-bottom:8px"></div>

      <!-- ── 3. PRODUCCIÓN HISTÓRICA + CHART ────────────────────────────── -->
      <div class="sec">Producción histórica</div>
      <div style="display:none">
        <button id="prod-toggle-anual"></button>
        <button id="prod-toggle-mensual"></button>
      </div>
      <div class="chart-wrap"><canvas id="prod-chart"></canvas></div>

      <!-- ── 4. MINAS DEL CLÚSTER ───────────────────────────────────────── -->
      <div class="sec">Minas del clúster
        <span id="roster-total" style="font-weight:400;font-size:10px;color:var(--text3)"></span>
      </div>
      <table class="mine-table">
        <thead>
          <tr>
            <th>Mina</th>
            <th>Empresa</th>
            <th>Prod. avg<br><span style="font-weight:400;font-size:9px">kt/año 2020-25</span></th>
            <th>% clúster</th>
          </tr>
        </thead>
        <tbody id="mine-roster-tbody"></tbody>
      </table>

      <!-- ── 5. FAENAS DEL CLÚSTER ──────────────────────────────────────── -->
      <div class="sec">Faenas del clúster</div>
      <div class="faena-list" id="faena-list-det"></div>

      <!-- ── 6. DIVERSIDAD DEL CLÚSTER (hidden) ── -->
      <div style="display:none">
        <div id="div-mine-count"></div>
        <div id="div-h-badge"></div>
        <div id="cat-stacked-bar"></div>
        <div id="cat-legend"></div>
        <div id="recurso-chips"></div>
        <div id="tipo-dist-panel"></div>
        <div id="mine-seg-panel"></div>
      </div>

      <!-- ── 7. CONTROL POR EMPRESA (hidden) ── -->
      <div style="display:none">
        <span id="emp-total"></span>
        <div id="empresa-bars"></div>
      </div>

      <!-- ── 8. PRODUCCIÓN POR EMPRESA (hidden — redundante con minas) ── -->
      <div style="display:none"><div id="prod-company-bars"></div></div>

      <!-- ── 9. PRODUCCIÓN POR MINA ──────────────────────────────────────── -->
      <div class="sec">Producción por mina
        <span style="font-weight:400;font-size:10px;color:var(--text3)">prom. 2020-2025</span>
      </div>
      <div id="prod-mine-bars"></div>

      <!-- ── 10. DERECHOS DE AGUA ────────────────────────────────────────── -->
      <div class="sec">Derechos de Agua (DGA)
        <span id="agua-count-badge" style="font-size:10px;font-weight:600;color:var(--accent);margin-left:auto"></span>
      </div>
      <div style="font-size:10px;color:var(--text3);margin-bottom:5px">Tipo (Consuntivo / No Consuntivo)</div>
      <div id="agua-tipo-bar" style="height:14px;border-radius:4px;overflow:hidden;display:flex;align-items:stretch;margin-bottom:4px"></div>
      <div id="agua-tipo-legend" style="display:flex;gap:8px;margin-bottom:7px;font-size:10px;flex-wrap:wrap"></div>
      <div style="font-size:10px;color:var(--text3);margin-bottom:5px">Naturaleza (Subterránea / Superficial)</div>
      <div id="agua-nat-bar" style="height:10px;border-radius:4px;overflow:hidden;display:flex;align-items:stretch;margin-bottom:4px"></div>
      <div id="agua-nat-legend" style="display:flex;gap:8px;margin-bottom:7px;font-size:10px;flex-wrap:wrap"></div>
      <div id="agua-uso-panel" style="margin-bottom:6px"></div>
      <div style="display:none">
        <div id="agua-year-spark"></div>
        <div id="agua-year-label"></div>
      </div>

      <!-- ── 11. ENERGÍA LOCAL ───────────────────────────────────────────── -->
      <div class="sec">Energía local
        <span id="ren-badge" style="margin-left:auto;font-size:10px;font-weight:400"></span>
      </div>
      <div class="cap-item">
        <div class="cap-row">
          <span>Capacidad instalada &lt;150 km</span>
          <span id="cap-elec-val" style="color:var(--accent)">—</span>
        </div>
        <div class="cap-bar-bg">
          <div class="cap-bar" id="cap-elec-bar" style="background:var(--accent);width:0%"></div>
        </div>
        <div class="cap-note" id="cap-elec-pct"></div>
      </div>
      <div id="energy-mix-wrap" style="margin-top:5px;display:flex;flex-direction:column;gap:3px"></div>

      <!-- ── 12. AGUA DESALADA ───────────────────────────────────────────── -->
      <div class="sec">Agua desalada — Minería
        <span class="mining-badge">MINERÍA</span>
      </div>
      <div class="cap-item">
        <div class="cap-row">
          <span id="cap-water-label">Desaladoras mineras operativas</span>
          <span id="cap-water-val" style="color:var(--accent2)">—</span>
        </div>
        <div class="cap-bar-bg">
          <div class="cap-bar" id="cap-water-bar" style="background:#38bdf8;width:0%"></div>
        </div>
        <div class="cap-note" id="cap-water-pct"></div>
      </div>
      <div id="desal-excl-note" style="font-size:10px;color:var(--text3);margin-top:4px;line-height:1.5"></div>

      <!-- ── 13. RELAVES ─────────────────────────────────────────────────── -->
      <div class="sec">Relaves
        <span id="rel-total" style="font-weight:400;font-size:10px;color:var(--text3)"></span>
      </div>
      <div id="tsf-summary" style="margin-bottom:8px"></div>
      <div id="rel-filter-btns" style="display:flex;gap:5px;flex-wrap:wrap;margin-bottom:7px"></div>
      <div id="rel-wrap">
        <table class="rel-table">
          <thead><tr><th>Instalación</th><th>Tipo</th><th>Estado</th><th>Vol. Disp. (m³)</th><th>Ciudad cercana</th></tr></thead>
          <tbody id="rel-tbody"></tbody>
        </table>
      </div>

      <!-- ── 14. ANÁLISIS DE RIESGO ─────────────────────────────────────── -->
      <div class="sec">Análisis de Riesgo del Clúster</div>
      <div id="risk-kpi-row" style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:5px;margin-bottom:8px"></div>
      <div id="risk-mine-panel" style="margin-bottom:8px"></div>

      <!-- ── 15. CENTRALES CERCANAS ─────────────────────────────────────── -->
      <div class="sec">Centrales cercanas</div>
      <div class="infra-list" id="infra-cen"></div>

      <!-- ── 16-17. DESALADORAS + RATIOS (hidden — redundante/técnico) ── -->
      <div style="display:none">
        <div class="infra-list" id="infra-des"></div>
        <div id="ratio-grid"></div>
      </div>

      <!-- ── 18. OPTIMIZACIÓN ESPACIAL (visible when OPT layer is active) ── -->
      <div id="opt-cluster-section" style="display:none">
        <div class="sec" style="color:var(--accent)">Potencial de Expansión Minera</div>
        <div class="opt-radius-label" id="opt-radius-label">Radio de análisis: — km</div>

        <!-- Score table for all models -->
        <table class="opt-score-table" id="opt-score-table"></table>

        <!-- KPIs from optimization stats -->
        <div class="kpi-row" id="opt-kpi-row" style="grid-template-columns:1fr 1fr 1fr;margin:8px 0"></div>

        <!-- Convergence bars -->
        <div class="sec" style="font-size:9px;margin:10px 0 6px">🔗 Convergencia hacia M5 (NPPI)</div>
        <div id="opt-conv-bars"></div>

        <!-- SEIA projects -->
        <div class="sec" style="font-size:9px;margin:10px 0 6px">⚙️ Proyectos SEIA aprobados en zona</div>
        <table class="data-table" id="opt-seia-table"></table>

        <!-- Exploration sites -->
        <div class="sec" style="font-size:9px;margin:10px 0 6px">🔍 Sitios de exploración</div>
        <div id="opt-explor-list" style="max-height:160px;overflow-y:auto;margin-bottom:6px"></div>

        <!-- Relaves -->
        <div class="sec" style="font-size:9px;margin:10px 0 6px">♻️ Relaves (top 5 por volumen)</div>
        <table class="data-table" id="opt-rel-table"></table>
      </div>

    </div>
  </div>
</div>


<!-- ══════════════════ FORECAST TAB + COLUMN ══════════════════ -->
<div id="fc-tab" onclick="toggleForecastCol()" title="Pronóstico del modelo">
  <span id="fc-tab-icon">›</span>
</div>
<div id="forecast-col">
  <div id="fc-inner">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
      <span style="font-size:13px;font-weight:700;color:var(--text)">Pronóstico del Modelo</span>
    </div>

    <!-- Mine chips — all forecast mines as clickable grade badges -->
    <div id="fc-mine-chips" style="display:flex;flex-wrap:wrap;gap:5px;margin-bottom:10px"></div>

    <!-- Mine selector (hidden fallback for JS value tracking) -->
    <select id="fc-mine-select" onchange="onFcMineChange()"
      style="width:100%;background:var(--bg3);color:var(--text);border:1px solid var(--bg4);
             border-radius:5px;padding:3px 6px;font-size:10px;cursor:pointer;margin-bottom:10px">
    </select>

    <!-- Nearest city tag (populated by JS on mine change) -->
    <div id="fc-mine-city" style="display:none;margin-bottom:10px;padding:5px 9px;
         background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.2);
         border-radius:7px;font-size:10px;color:var(--text2)"></div>

    <!-- ① MEJOR MODELO -->
    <div style="font-size:10px;font-weight:700;color:var(--accent);letter-spacing:.05em;
                margin-bottom:6px;padding-bottom:4px;border-bottom:1px solid var(--bg4)">
      MEJOR MODELO
    </div>
    <div id="fc-best-compare" style="display:flex;gap:8px;margin-bottom:8px"></div>
    <div style="font-size:9px;color:var(--text3);margin-bottom:3px">
      Proyección 2026–2032 · Modelo ganador
    </div>
    <div class="chart-wrap" style="height:185px"><canvas id="fc-best-chart"></canvas></div>

    <!-- ② PRONÓSTICO ANUAL (collapsible) -->
    <div onclick="toggleFcSection('ann')"
         style="display:flex;align-items:center;justify-content:space-between;cursor:pointer;
                font-size:10px;font-weight:700;color:var(--text2);letter-spacing:.04em;
                margin:14px 0 0;padding:5px 0 4px;border-bottom:1px solid var(--bg4)">
      <span>PRONÓSTICO ANUAL</span>
      <span id="fc-ann-arrow" style="color:var(--accent);font-size:12px">›</span>
    </div>
    <div id="fc-ann-body" style="display:none;padding-top:6px">
      <div id="fc-ann-metrics" style="display:flex;gap:10px;margin-bottom:6px"></div>
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:3px">
        <span style="font-size:9px;color:var(--text3)">Proyección 2026–2032 · Ens_Segmentado</span>
        <div style="display:flex;gap:3px" id="sc-toggle">
          <button class="sc-btn active" onclick="setScenario('base')" id="sc-base">Base</button>
          <button class="sc-btn" onclick="setScenario('bear')" id="sc-bear">Bear</button>
          <button class="sc-btn" onclick="setScenario('bull')" id="sc-bull">Bull</button>
        </div>
      </div>
      <div class="chart-wrap" style="height:185px"><canvas id="fc-proj-chart"></canvas></div>
      <div style="font-size:9px;color:var(--text3);margin:10px 0 3px">
        Validación origen 2018 → H+1–H+7
      </div>
      <div class="chart-wrap" style="height:155px"><canvas id="fc-chart"></canvas></div>
    </div>

    <!-- ③ Tabla calidad (simplificada) -->
    <div onclick="toggleFcSection('tbl')"
         style="display:flex;align-items:center;justify-content:space-between;cursor:pointer;
                font-size:10px;font-weight:700;color:var(--text2);letter-spacing:.04em;
                margin:14px 0 0;padding:5px 0 4px;border-bottom:1px solid var(--bg4)">
      <span>CALIDAD POR MINA</span>
      <span id="fc-tbl-arrow" style="color:var(--accent);font-size:12px">›</span>
    </div>
    <div id="fc-tbl-body" style="display:none;padding-top:6px">
      <!-- canvas placeholders needed by JS even if section hidden -->
      <canvas id="fc-proj-chart-m" style="display:none"></canvas>
      <canvas id="fc-wr-h-chart"   style="display:none"></canvas>
      <canvas id="fc-chart-m"      style="display:none"></canvas>
      <div id="fc-mon-metrics"     style="display:none"></div>
      <div style="overflow-x:auto;margin-bottom:10px">
        <table class="rel-table" id="fc-quality-table">
          <thead>
            <tr>
              <th>Mina</th>
              <th style="text-align:right">WR% Anual</th>
              <th style="text-align:right">WR% Mensual</th>
              <th style="text-align:center">Calidad</th>
            </tr>
          </thead>
          <tbody id="fc-quality-tbody"></tbody>
        </table>
      </div>
      <div style="font-size:10px;color:var(--text2);font-weight:600;margin-bottom:4px">
        Win Rate por mina <span style="font-size:9px;font-weight:400;color:var(--text3)">vs naïve (50%)</span>
      </div>
      <div class="chart-wrap" style="height:195px"><canvas id="fc-wr-chart"></canvas></div>
    </div>

  </div>
</div>

<!-- ══════════════════ MAP ══════════════════ -->
<div id="map">
  <div id="sigex-box">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
      <span style="font-weight:700;color:var(--text)">⚙️ Sondajes SIGEX</span>
      <span id="sigex-total-badge" style="font-size:9px;padding:1px 6px;border-radius:8px;
            background:rgba(245,158,11,0.12);color:#f59e0b;border:1px solid rgba(245,158,11,0.3)"></span>
    </div>
    <div class="sf-section">
      <div class="sf-label">Recurso</div>
      <div class="sf-pills" id="sf-recurso"></div>
    </div>
    <div class="sf-section">
      <div class="sf-label">Región</div>
      <select class="sf-select" id="sf-region" onchange="applySignexFilters()">
        <option value="">Todas</option>
      </select>
    </div>
    <div class="sf-section">
      <div class="sf-label">Empresa</div>
      <select class="sf-select" id="sf-empresa" onchange="applySignexFilters()">
        <option value="">Todas</option>
      </select>
    </div>
    <div id="sigex-count"></div>
  </div>

  <!-- OPT PANEL -->
  <div id="opt-panel">
    <div class="op-accent"></div>
    <div class="op-head">
      <div class="op-title">🎯 Modelos de Expansión Minera</div>
      <div class="op-sub" id="op-sub">Hover sobre un valle en el mapa</div>
    </div>
    <div class="op-chart-wrap">
      <canvas id="opt-radar" width="190" height="180"></canvas>
    </div>
    <div id="op-legend" class="op-legend">
      <div class="op-leg-row">
        <div class="op-leg-dot" style="background:#a78bfa"></div>
        <div><div class="op-leg-name">M1 — KDE Exploración</div>
             <div class="op-leg-desc">Densidad KDE de sitios de exploración activos (Scott bandwidth)</div></div>
      </div>
      <div class="op-leg-row">
        <div class="op-leg-dot" style="background:#38bdf8"></div>
        <div><div class="op-leg-name">M3 — Gravedad Producción</div>
             <div class="op-leg-desc">Atracción gravitacional por producción Cat-A/B y distancia</div></div>
      </div>
      <div class="op-leg-row">
        <div class="op-leg-dot" style="background:#ef4444"></div>
        <div><div class="op-leg-name">M4 — Riesgo Ambiental ↓</div>
             <div class="op-leg-desc">Pasivos: relaves, protección SNASPE (mayor = más riesgo)</div></div>
      </div>
      <div class="op-leg-row">
        <div class="op-leg-dot" style="background:#22c55e"></div>
        <div><div class="op-leg-name">M5 — NPPI Integrado</div>
             <div class="op-leg-desc">∛(M1·SEIA·Reservas)·(1+0.5·M3ₙ)/(1+0.5·M4ₙ)</div></div>
      </div>
      <div class="op-leg-row">
        <div class="op-leg-dot" style="background:#f59e0b"></div>
        <div><div class="op-leg-name">M7 — ECI Competencia</div>
             <div class="op-leg-desc">M5 ajustado por barrera Porter Π=ln(1+P_proj)/ln(1+P_max)</div></div>
      </div>
    </div>
    <div id="op-scores" class="op-scores" style="display:none"></div>
    <div class="op-val">
      <div class="op-pill op-pill-g" id="op-hit-pill">✓ — hit rate</div>
      <div class="op-pill op-pill-a" id="op-lift-pill">⚡ — lift</div>
    </div>
  </div>
</div>
</div>
<div id="tip"></div>

<!-- ══════════════════ SCRIPT ══════════════════ -->
<script>
const RAW = """ + data_json + r""";
const OPT = """ + opt_json + r""";

// ── STATE ────────────────────────────────────────────────────────────────────
let selectedCluster = null;
let currentYear     = RAW.config.default_year;
let flags = {sub:false,cen:false,des:false,rel:false,seia:false,sigexotros:false,train:false,ruido:false,ap:false,fibra:false,senal:false,pue:false,pob:false,opt:false};
let prodChart = null;
let currentProdMode  = 'annual';   // 'annual' | 'monthly'
let currentClusterData = null;     // last-opened cluster object (for re-render on mode change)
let currentPeakYr    = null;
let fcChart      = null;
let fcWrChart    = null;
let fcProjChart  = null;
let fcBestChart  = null;
let fcProjChartM = null;
let fcChartM     = null;
let fcWrHChart   = null;
let fcColOpen    = false;
let fcSections   = {ann:false, mon:false, tbl:false};
let currentScenario = 'base';
let _optRadiusCircle = null;

function setScenario(sc){
  currentScenario = sc;
  ['base','bear','bull'].forEach(s=>{
    const b=document.getElementById('sc-'+s);
    if(b) b.classList.toggle('active', s===sc);
  });
  // Rebuild projection chart with new scenario
  const mk = document.getElementById('fc-mine-select')?.value;
  if(!mk || !currentClusterData) return;
  const d = (currentClusterData.forecast||{}).mines?.[mk];
  if(d) buildFcProjectionChart(d, mk);
}

function toggleFcSection(sec){
  fcSections[sec] = !fcSections[sec];
  const body  = document.getElementById('fc-'+sec+'-body');
  const arrow = document.getElementById('fc-'+sec+'-arrow');
  if(!body) return;
  body.style.display = fcSections[sec] ? 'block' : 'none';
  if(arrow) arrow.textContent = fcSections[sec] ? '‹' : '›';
  if(fcSections[sec] && currentClusterData){
    const mk = document.getElementById('fc-mine-select').value;
    const d  = (currentClusterData.forecast||{}).mines?.[mk];
    if(!d) return;
    if(sec==='ann'){ buildFcProjectionChart(d,mk); buildFcChart(d,mk); buildFcAnnMetrics(d); }
    if(sec==='tbl'){ buildFcWrChart((currentClusterData.forecast||{})); }
  }
}

function setProdMode(mode){
  currentProdMode = mode;
  // Update button styles
  const aBtn = document.getElementById('prod-toggle-anual');
  const mBtn = document.getElementById('prod-toggle-mensual');
  if(!aBtn || !mBtn) return;
  if(mode === 'annual'){
    aBtn.style.cssText='font-size:9px;font-weight:700;padding:2px 8px;border-radius:4px;border:none;cursor:pointer;transition:all .2s;background:var(--accent);color:#000';
    mBtn.style.cssText='font-size:9px;font-weight:700;padding:2px 8px;border-radius:4px;border:none;cursor:pointer;transition:all .2s;background:transparent;color:var(--text2)';
  } else {
    mBtn.style.cssText='font-size:9px;font-weight:700;padding:2px 8px;border-radius:4px;border:none;cursor:pointer;transition:all .2s;background:var(--accent2);color:#000';
    aBtn.style.cssText='font-size:9px;font-weight:700;padding:2px 8px;border-radius:4px;border:none;cursor:pointer;transition:all .2s;background:transparent;color:var(--text2)';
  }
  if(currentClusterData) buildProductionChart(currentClusterData, currentPeakYr);
}

// ── MAP ───────────────────────────────────────────────────────────────────────
const map = L.map('map',{zoomControl:true,preferCanvas:true}).setView([-29,-70],5);

const baseMaps = {
  "Dark (Carto)": L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',{
    attribution:'© <a href="https://openstreetmap.org">OpenStreetMap</a> © <a href="https://carto.com">CARTO</a>',
    maxZoom:19
  }),
  "Light (Carto)": L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',{
    attribution:'© <a href="https://openstreetmap.org">OpenStreetMap</a> © <a href="https://carto.com">CARTO</a>',
    maxZoom:19
  }),
  "Satellite": L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{
    attribution:'© <a href="https://www.esri.com">Esri</a> — Esri, USGS, NOAA',
    maxZoom:19
  }),
  "Terrain": L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',{
    attribution:'© <a href="https://openstreetmap.org">OpenStreetMap</a> © <a href="https://opentopomap.org">OpenTopoMap</a>',
    maxZoom:17
  }),
  "Voyager (Carto)": L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',{
    attribution:'© <a href="https://openstreetmap.org">OpenStreetMap</a> © <a href="https://carto.com">CARTO</a>',
    maxZoom:19
  }),
};
baseMaps["Light (Carto)"].addTo(map);
L.control.layers(baseMaps, null, {position:'topright', collapsed:true}).addTo(map);

const lgs = {
  areasProtegidas: L.featureGroup(),           // áreas protegidas (toggle, off by default)
  clusterPolys: L.featureGroup().addTo(map),  // cluster polygons (always visible)
  faenas:       L.featureGroup().addTo(map),  // shown at zoom >= threshold
  ruido:        L.featureGroup(),
  sigexOtros:   L.featureGroup(),
  subestaciones:L.featureGroup(),
  centrales:    L.featureGroup(),
  desaladoras:  L.featureGroup(),
  relaves:      L.featureGroup(),
  seia:         L.featureGroup(),
  train:        L.featureGroup(),
  fibra:        L.featureGroup(),
  senal:        L.featureGroup(),
  puertos:    L.featureGroup(),
  ciudades:   L.featureGroup(),
  optLayer:   L.featureGroup(),
};

// ── FIBRA ÓPTICA layer build ──────────────────────────────────────────────────
(function(){
  const FIBRA_STYLE = {
    'Troncal':     {color:'#fbbf24', weight:2.5, opacity:0.85},
    'Tendidos':    {color:'#f97316', weight:1.5, opacity:0.7},
    'Red_Troncal': {color:'#38bdf8', weight:2,   opacity:0.8},
  };
  const FIBRA_PT_COLOR = {'Sitios':'#fb923c','POIIT':'#fcd34d'};
  L.geoJSON(RAW.fibra, {
    style: f => {
      const lyr = f.properties._layer || '';
      return FIBRA_STYLE[lyr] || {color:'#f97316', weight:1, opacity:0.6};
    },
    pointToLayer: (f, latlng) => {
      const lyr = f.properties._layer || '';
      const col = FIBRA_PT_COLOR[lyr] || '#f97316';
      return L.circleMarker(latlng, {radius:3, color:col, fillColor:col,
                                      fillOpacity:0.8, weight:1});
    },
    onEachFeature: (f, layer) => {
      const p = f.properties;
      const lyr  = p._layer || '';
      const name = p.name || p.descriptio || p.NOMB_RED || '';
      const cap  = p.Gbps ? ` · ${p.Gbps} Gbps` : (p.CAPACIDAD ? ` · ${p.CAPACIDAD}` : '');
      const tipo = p.TIPO_TENDI ? `<br><span style="opacity:.7">${p.TIPO_TENDI}</span>` : '';
      layer.on('mouseover', e => showTip(e,
        `<b style="color:#f97316">🔶 Fibra Óptica</b><br>
         <b>${lyr}</b>${name ? '<br>'+name : ''}${cap}${tipo}`));
      layer.on('mouseout', () => hideTip());
    }
  }).addTo(lgs.fibra);
})();

// ── SEÑAL TELEFÓNICA layer build ──────────────────────────────────────────────
(function(){
  const OP_COLOR = {
    'Claro':    '#ef4444',
    'Entel':    '#3b82f6',
    'Movistar': '#22c55e',
    'Wom':      '#e879f9',
  };
  L.geoJSON(RAW.senal, {
    pointToLayer: (f, latlng) => {
      const p   = f.properties;
      const op  = p._operador || '';
      const col = OP_COLOR[op] || '#a855f7';
      const isTorre = p._tipo === 'torre';
      return L.circleMarker(latlng, {
        radius:      isTorre ? 5 : 2.5,
        color:       col,
        fillColor:   col,
        fillOpacity: isTorre ? 0.9 : 0.55,
        weight:      isTorre ? 1.5 : 0.8,
      });
    },
    onEachFeature: (f, layer) => {
      const p   = f.properties;
      const op  = p._operador || '';
      const col = OP_COLOR[op] || '#a855f7';
      if (p._tipo === 'torre') {
        const gen  = p._gen || '';
        const zona = p['tipo_zona_'] || p.tipo_zona_ || '';
        const cod  = p.codigo_est || '';
        layer.on('mouseover', e => showTip(e,
          `<b style="color:${col}">📡 ${op} ${gen}</b> <span style="opacity:.7">Torre</span>
           ${cod  ? '<br>'+cod : ''}
           ${zona ? '<br><span style="opacity:.6">'+zona+'</span>' : ''}`));
      } else {
        const banda  = p.banda || '';
        const ef     = p.eficiencia != null ? (+p.eficiencia).toFixed(1)+'%' : '';
        const region = p.region || '';
        layer.on('mouseover', e => showTip(e,
          `<b style="color:${col}">📡 ${op}</b> <span style="opacity:.6">Cobertura</span>
           ${banda  ? '<br><span style="opacity:.8">'+banda+'</span>' : ''}
           ${ef     ? ' · Ef: '+ef : ''}
           ${region ? '<br><span style="opacity:.6">'+region+'</span>' : ''}`));
      }
      layer.on('mouseout', () => hideTip());
    }
  }).addTo(lgs.senal);
})();

// ── ÁREAS PROTEGIDAS layer build ─────────────────────────────────────────────
(function(){
  const AP_DESIG_COLOR={
    'Parque Nacional':'#16a34a','Reserva Nacional':'#4ade80',
    'Monumento Natural':'#fbbf24','Santuario de la Naturaleza':'#67e8f9',
    'Reserva de la Biófera':'#c084fc','Reserva Forestal':'#a3e635',
    'Bien Nacional Protegido':'#fb923c',
    'Conservación Privada y Comunitaria':'#94a3b8',
    'Área Marina Costera Protegida':'#38bdf8','Parque Marino':'#0ea5e9',
    'Reserva Marina':'#7dd3fc','Paisaje de Conservación':'#86efac',
  };
  L.geoJSON(RAW.areas_protegidas, {
    style: f => {
      const col = f.properties.color || '#94a3b8';
      return {color:col, weight:0.8, opacity:0.7, fillColor:col, fillOpacity:0.18};
    },
    onEachFeature:(f,layer)=>{
      const p=f.properties;
      const haStr = p.ha ? `${(+p.ha).toLocaleString('es-CL',{maximumFractionDigits:0})} ha` : '';
      layer.on('mouseover', e=>showTip(e,
        `<b style="color:${p.color||'#fff'}">${p.designacio}</b><br>
         <b>${p.nombre_ap}</b><br>
         ${p.region}<br>
         ${haStr}`));
      layer.on('mouseout', ()=>hideTip());
    }
  }).addTo(lgs.areasProtegidas);
})();

// ── HELPERS ───────────────────────────────────────────────────────────────────
const fmtProd  = v => v ? (+v).toFixed(1)           : '—';
const fmtWater = v => v ? (v/1e6).toFixed(3)        : '—';
const fmtElec  = v => v ? (v/1e3).toFixed(1)        : '—';
const fmtNum   = n => n>=1e9?(n/1e9).toFixed(2)+'B':n>=1e6?(n/1e6).toFixed(2)+'M':n>=1e3?(n/1e3).toFixed(1)+'k':(+n).toFixed(1);

function hav(la1,lo1,la2,lo2){
  const R=6371,d2r=Math.PI/180,dlat=(la2-la1)*d2r,dlon=(lo2-lo1)*d2r;
  const a=Math.sin(dlat/2)**2+Math.cos(la1*d2r)*Math.cos(la2*d2r)*Math.sin(dlon/2)**2;
  return 2*R*Math.asin(Math.sqrt(a));
}

function showTip(e,html){
  const t=document.getElementById('tip');
  t.innerHTML=html; t.style.display='block';
  t.style.left=(e.originalEvent.clientX+14)+'px';
  t.style.top=(e.originalEvent.clientY+10)+'px';
}
function hideTip(){ document.getElementById('tip').style.display='none'; }

function divIcon(emoji,cls){
  return L.divIcon({html:`<div class="infra-marker ${cls}">${emoji}</div>`,
                    className:'',iconSize:[25,25],iconAnchor:[12,12]});
}

// ── TRAIN LINES + STATIONS ─────────────────────────────────────────────────
// Trunks = 3 main N-S corridors (solid, heavier line)
// Branches = E-W spurs to mines / ports (dashed, thinner)
function buildTrainLayer(){
  lgs.train.clearLayers();
  RAW.estaciones.forEach(st => {
    const m = L.circleMarker([st.lat, st.lon], {
      radius: 2.5, color: '#a78bfa', fillColor: '#a78bfa',
      fillOpacity: 0.85, weight: 1,
    });
    m.on('mouseover', e => showTip(e, `🚂 <b>${st.name}</b>`));
    m.on('mouseout', () => hideTip());
    lgs.train.addLayer(m);
  });
}

// ── CLUSTER POLYGONS ──────────────────────────────────────────────────────────
function initClusterPolygons(){
  lgs.clusterPolys.clearLayers();
  Object.values(RAW.clusters).forEach(cl=>{
    if(!cl.hull||cl.hull.length<3) return;
    const poly=L.polygon(cl.hull,{
      color:cl.color,fillColor:cl.color,fillOpacity:0.28,weight:2,opacity:0.8,
      smoothFactor:0
    });
    cl._poly=poly;
    poly.on('click',()=>selectCluster(cl.id));
    poly.on('mouseover',e=>{
      if(selectedCluster!==cl.id) poly.setStyle({fillOpacity:0.48,weight:3});
      const prod=cl.production[String(currentYear)];
      showTip(e,`<b style="color:${cl.color}">${cl.id}</b> — ${cl.label}<br>
        🏆 <b>${cl.top_mine}</b><br>
        📈 ${currentYear}: <b>${prod?fmtProd(prod)+' kTM':'—'}</b><br>
        📍 ${RAW.installations.filter(i=>i.cluster_id===cl.id).length} instalaciones`);
    });
    poly.on('mouseout',()=>{
      if(selectedCluster!==cl.id) poly.setStyle({fillOpacity:0.28,weight:2});
      hideTip();
    });
    lgs.clusterPolys.addLayer(poly);
  });
}

// ── OPTIMIZACIÓN ESPACIAL LAYER (todos los modelos) ──────────────────────────
(function(){
  const MDEF = [
    {key:'M1', short:'M1 KDE Expl.',    color:'#a78bfa', inverted:false},
    {key:'M3', short:'M3 Gravedad',     color:'#38bdf8', inverted:false},
    {key:'M4', short:'M4 Riesgo',       color:'#ef4444', inverted:true},
    {key:'M5', short:'M5 NPPI',         color:'#22c55e', inverted:false},
    {key:'M7', short:'M7 ECI',          color:'#f59e0b', inverted:false},
  ];

  // Hull colour gradient by M7 score
  function scoreColor(s){
    const st=[[0,127,29,29],[.25,234,111,18],[.5,250,191,36],[.75,134,239,172],[1,34,197,94]];
    let i=0; while(i<st.length-2&&s>st[i+1][0])i++;
    const [t0,r0,g0,b0]=st[i],[t1,r1,g1,b1]=st[i+1];
    const t=(t1===t0)?0:(s-t0)/(t1-t0);
    const l=(a,b)=>Math.round(a+t*(b-a));
    return `rgb(${l(r0,r1)},${l(g0,g1)},${l(b0,b1)})`;
  }

  const optPanel = document.getElementById('opt-panel');

  // ── Radar chart init ──────────────────────────────────────────────────────
  const radarCanvas = document.getElementById('opt-radar');
  if(radarCanvas && window.Chart){
    window._optChart = new Chart(radarCanvas.getContext('2d'), {
      type:'radar',
      data:{
        labels:['M1 KDE','M3 Grav.','M4 Riesgo','M5 NPPI','M7 ECI'],
        datasets:[{
          data:[.5,.5,.5,.5,.5],
          backgroundColor:'rgba(100,116,139,0.12)',
          borderColor:'rgba(100,116,139,0.35)',
          borderWidth:1.5,
          borderDash:[4,3],
          pointRadius:3,
          pointBackgroundColor:'rgba(100,116,139,0.5)',
          pointHoverRadius:0,
        }]
      },
      options:{
        animation:{duration:320,easing:'easeInOutQuart'},
        scales:{r:{
          min:0,max:1,
          ticks:{display:false,stepSize:.25},
          grid:{color:'rgba(51,65,85,0.65)',lineWidth:1},
          angleLines:{color:'rgba(51,65,85,0.5)',lineWidth:1},
          pointLabels:{font:{size:9,family:"'Segoe UI',sans-serif"},color:'#475569'},
        }},
        plugins:{legend:{display:false},tooltip:{enabled:false}},
        responsive:false,
      }
    });
  }

  // Validation pills
  const val = OPT.validation || {};
  const hitPill  = document.getElementById('op-hit-pill');
  const liftPill = document.getElementById('op-lift-pill');
  if(hitPill && val.catA_hit_rate_pct != null)
    hitPill.textContent  = `✓ ${val.catA_hit_rate_pct}% hit rate (${val.catA_hits}/${val.catA_total})`;
  if(liftPill && val.lift != null)
    liftPill.textContent = `⚡ ${val.lift}× lift`;

  // ── Update panel on hover ─────────────────────────────────────────────────
  function showOptCluster(cl, rawCl){
    const sub = document.getElementById('op-sub');
    if(sub) sub.innerHTML = `<b>${cl.id}</b> — ${rawCl?.label||cl.label}`;

    // Radar data: M4 inverted (high risk = small polygon area)
    const scores = MDEF.map(m=>{
      const v = cl.models?.[m.key]?.data?.score_norm ?? 0;
      return m.inverted ? 1-v : v;
    });
    if(window._optChart){
      // Build per-point gradient using model colors
      const ds = window._optChart.data.datasets[0];
      ds.data            = scores;
      ds.backgroundColor = 'rgba(167,139,250,0.13)';
      ds.borderColor     = '#a78bfa';
      ds.borderWidth     = 2;
      ds.borderDash      = [];
      ds.pointRadius     = 3;
      ds.pointBackgroundColor = MDEF.map(m=>m.color);
      window._optChart.update();
    }

    // Score rows
    document.getElementById('op-legend').style.display = 'none';
    const scEl = document.getElementById('op-scores');
    scEl.style.display = 'flex';
    scEl.innerHTML = MDEF.map(m=>{
      const raw = cl.models?.[m.key]?.data?.score_norm ?? null;
      const pct = raw != null ? Math.round(raw*100) : 0;
      const barPct = m.inverted ? 100-pct : pct;
      const label  = m.inverted ? `Riesgo ${pct}%` : `${pct}%`;
      const glow   = `box-shadow:0 0 6px ${m.color}55`;
      return `<div class="op-sc-row">
        <div class="op-sc-dot" style="background:${m.color}"></div>
        <div class="op-sc-name">${m.short}</div>
        <div class="op-sc-track">
          <div class="op-sc-fill ${m.inverted?'inv':'norm'}"
               style="width:${barPct}%;background:${m.color};${glow}"></div>
        </div>
        <div class="op-sc-val" style="color:${m.color}">${label}</div>
      </div>`;
    }).join('');
  }

  function resetOptPanel(){
    const sub = document.getElementById('op-sub');
    if(sub) sub.textContent = 'Hover sobre un valle en el mapa';
    if(window._optChart){
      const ds = window._optChart.data.datasets[0];
      ds.data=[.5,.5,.5,.5,.5];
      ds.backgroundColor='rgba(100,116,139,0.12)';
      ds.borderColor='rgba(100,116,139,0.35)';
      ds.borderWidth=1.5; ds.borderDash=[4,3];
      ds.pointRadius=3; ds.pointBackgroundColor='rgba(100,116,139,0.5)';
      window._optChart.update();
    }
    document.getElementById('op-legend').style.display='flex';
    document.getElementById('op-scores').style.display='none';
  }
  window.resetOptPanel = resetOptPanel;

  // ── Map layer ─────────────────────────────────────────────────────────────
  Object.values(OPT.clusters).forEach(cl=>{
    const rawCl  = RAW.clusters[cl.id];
    if(!rawCl||!rawCl.hull||rawCl.hull.length<3) return;
    const m7score = cl.models?.M7?.data?.score_norm ?? 0;
    const m5dat   = cl.models?.M5?.data;
    const color   = scoreColor(m7score);

    const poly = L.polygon(rawCl.hull,{
      color,fillColor:color,fillOpacity:.4,weight:2.5,opacity:.9,smoothFactor:0});
    poly.on('mouseover', e=>{showOptCluster(cl,rawCl);
      showTip(e,`<b style="color:${color}">🎯 ${cl.id}</b> — ${rawCl.label}`);});
    poly.on('mouseout',  ()=>{resetOptPanel();hideTip();});
    poly.on('click',     ()=>selectCluster(cl.id));
    lgs.optLayer.addLayer(poly);

    if(m5dat?.lat!=null && m5dat?.lon!=null){
      const m5s = m5dat.score_norm ?? 0;
      const sz  = Math.round(10 + m5s*9);
      const starIcon = L.divIcon({
        html:`<div style="font-size:${sz}px;line-height:1;
          filter:drop-shadow(0 0 4px ${color}) drop-shadow(0 0 2px #000)">⭐</div>`,
        className:'',iconAnchor:[sz/2,sz/2]});
      const mk = L.marker([m5dat.lat,m5dat.lon],{icon:starIcon,zIndexOffset:600});
      mk.on('mouseover', e=>{showOptCluster(cl,rawCl);
        showTip(e,`<b style="color:${color}">⭐ Mejor punto M5 — ${cl.id}</b><br>
          M5: <b>${Math.round(m5s*100)}%</b> · M7: <b>${Math.round(m7score*100)}%</b><br>
          Dist. mina: <b>${m5dat.dist_km?.toFixed(1)||'?'} km</b>`);});
      mk.on('mouseout', ()=>{resetOptPanel();hideTip();});
      mk.on('click',    ()=>selectCluster(cl.id));
      lgs.optLayer.addLayer(mk);
    }
  });

  window._optLegendHook = function(key){
    if(key!=='opt') return;
    if(flags['opt']) optPanel?.classList.add('open');
    else {
      optPanel?.classList.remove('open');
      resetOptPanel();
      // Hide radius circle when OPT layer is turned off
      if(_optRadiusCircle){ map.removeLayer(_optRadiusCircle); _optRadiusCircle=null; }
    }
    // Toggle opt cluster section in sidebar
    const sec=document.getElementById('opt-cluster-section');
    if(sec){
      if(flags.opt && selectedCluster) fillOptClusterDetail(selectedCluster);
      else sec.style.display='none';
    }
    // Rebuild cluster list to show/hide score badges
    if(!selectedCluster) buildClusterList();
  };
})();

// ── FAENA MARKERS ────────────────────────────────────────────────────────────
function buildFaenaMarkers(){
  lgs.faenas.clearLayers(); lgs.ruido.clearLayers();
  RAW.installations.forEach(inst=>{
    const color=RAW.clusters[inst.cluster_id]?.color||'#6b7280';
    const ec=RAW.config.estado_colors[inst.estado]||'#6b7280';
    const m=L.circleMarker([inst.lat,inst.lon],{
      radius:5,color:'#fff',fillColor:color,fillOpacity:0.85,weight:1.2});
    m.on('mouseover',e=>showTip(e,
      `<b>${inst.nombre}</b><br>
       <span style="color:var(--text2)">${inst.tipo_inst||inst.categoria}</span><br>
       ${inst.empresa}<br>${inst.comuna}, R.${inst.region}<br>
       <span style="color:${ec}">● ${inst.estado}</span>`));
    m.on('mouseout',()=>hideTip());
    m.on('click',()=>openInstallationPopup(inst));
    lgs.faenas.addLayer(m);
  });
  // Ruido (unassigned by HDBSCAN) — shown only when toggle is on
  (RAW.ruido_installations||[]).forEach(inst=>{
    const ec=RAW.config.estado_colors[inst.estado]||'#6b7280';
    const m=L.circleMarker([inst.lat,inst.lon],{
      radius:3.5,color:'#374151',fillColor:'#6b7280',fillOpacity:0.45,weight:1});
    m.on('mouseover',e=>showTip(e,
      `<b>${inst.nombre}</b><br>
       <span style="color:#f59e0b">⚠ Sin clúster asignado</span><br>
       ${inst.empresa}<br>${inst.tipo_inst||inst.categoria} · R.${inst.region}<br>
       <span style="color:${ec}">● ${inst.estado}</span>`));
    m.on('mouseout',()=>hideTip());
    lgs.ruido.addLayer(m);
  });
  if(!map.hasLayer(lgs.faenas)) lgs.faenas.addTo(map);
  if(flags.ruido && !map.hasLayer(lgs.ruido)) lgs.ruido.addTo(map);
}

function showFaenas(cid){
  lgs.faenas.clearLayers();
  const color=RAW.clusters[cid]?.color||'#6b7280';
  RAW.installations.filter(inst=>inst.cluster_id===cid).forEach(inst=>{
    const ec=RAW.config.estado_colors[inst.estado]||'#6b7280';
    const m=L.circleMarker([inst.lat,inst.lon],{
      radius:6,color:'#fff',fillColor:color,fillOpacity:0.92,weight:1.5});
    m.on('mouseover',e=>{m.setRadius(9);showTip(e,
      `<b>${inst.nombre}</b><br>
       <span style="color:var(--text2)">${inst.tipo_inst||inst.categoria}</span><br>
       ${inst.empresa}<br>${inst.comuna}`);});
    m.on('mouseout',()=>{m.setRadius(6);hideTip();});
    m.on('click',()=>openInstallationPopup(inst));
    lgs.faenas.addLayer(m);
  });
  if(!map.hasLayer(lgs.faenas)) lgs.faenas.addTo(map);
}

function openInstallationPopup(inst){
  const color=RAW.clusters[inst.cluster_id]?.color||'#6b7280';
  const ec=RAW.config.estado_colors[inst.estado]||'#6b7280';
  // Look up parent faena production
  const faena=RAW.faenas.find(f=>f.id_faena===inst.id_faena);
  const prod=faena?.production ? Object.entries(faena.production).sort(([a],[b])=>a-b).slice(-5) : [];
  const prodStr=prod.length ? prod.map(([y,v])=>`${y}: <b>${v} kTM</b>`).join('<br>') : '';
  L.popup({maxWidth:290,className:'cluster-tooltip'})
   .setLatLng([inst.lat,inst.lon])
   .setContent(`<div style="font-size:12px">
     <div style="font-weight:700;color:${color};margin-bottom:4px">${inst.nombre}</div>
     <div style="color:var(--accent2);font-size:11px;margin-bottom:3px">${inst.tipo_inst||inst.categoria}</div>
     <div>${inst.empresa}</div>
     <div style="color:#94a3b8;font-size:11px">${inst.recurso||'—'} · R.${inst.region} · ${inst.comuna}</div>
     <div style="margin:5px 0"><span style="color:${ec}">● ${inst.estado}</span></div>
     ${prodStr?`<div style="margin-top:5px;font-size:11px;color:#94a3b8">📈 Producción faena:<br>${prodStr}</div>`:''}
   </div>`).openOn(map);
}

// ── INFRA LAYERS ─────────────────────────────────────────────────────────────
function buildInfraLayers(){
  // Subestaciones
  lgs.subestaciones.clearLayers();
  RAW.subestaciones.forEach(s=>{
    const m=L.marker([s.lat,s.lon],{icon:divIcon('⚡','i-sub')});
    m.on('mouseover',e=>showTip(e,`<b>${s.nombre}</b><br>${s.propiedad}<br>${s.tension} kV · ${s.tipo}`));
    m.on('mouseout',()=>hideTip());
    lgs.subestaciones.addLayer(m);
  });

  // Centrales
  lgs.centrales.clearLayers();
  RAW.centrales.forEach(c=>{
    const m=L.marker([c.lat,c.lon],{icon:divIcon('🏭','i-cen')});
    m.on('mouseover',e=>showTip(e,`<b>${c.nombre}</b><br>${c.propiedad}<br>${c.tipo} · ${c.potencia_mw} MW<br>${c.combustible}`));
    m.on('mouseout',()=>hideTip());
    lgs.centrales.addLayer(m);
  });

  // Desaladoras (mining ones get special icon)
  lgs.desaladoras.clearLayers();
  RAW.desaladoras.forEach(d=>{
    const cls=d.mining?'i-des-mining':'i-des';
    const m=L.marker([d.lat,d.lon],{icon:divIcon(d.mining?'💧⛏':'💧',cls)});
    m.on('mouseover',e=>showTip(e,
      `<b>${d.nombre}</b>${d.mining?' <span style="color:var(--accent)">⛏ Minería</span>':''}<br>
       ${d.empresa}<br>${d.region}<br>
       ${d.capacidad_lps} lps · ${d.estado}`));
    m.on('mouseout',()=>hideTip());
    lgs.desaladoras.addLayer(m);
  });

  // Relaves — built via buildRelaveLayer() so filter can rebuild
  buildRelaveLayer();

  // SIGEX Sondajes — coloured by cluster_id (only sondajes, filterable)
  buildSignexLayer();

  // Puertos
  lgs.puertos.clearLayers();
  (RAW.puertos||[]).forEach(p=>{
    const m=L.marker([p.lat,p.lon],{icon:divIcon('⚓','i-pue')});
    m.on('mouseover',e=>showTip(e,
      `⚓ <b>${p.nombre}</b><br>Tamaño: ${p.tamano||'—'}<br>Nº ${p.numero||'—'}`));
    m.on('mouseout',()=>hideTip());
    lgs.puertos.addLayer(m);
  });

  // Ciudades / Poblaciones
  lgs.ciudades.clearLayers();
  (RAW.ciudades||[]).forEach(c=>{
    const r = Math.max(5, Math.min(22, Math.sqrt(c.poblacion/600)));
    const m = L.circleMarker([c.lat, c.lon], {
      radius: r, color:'#e879f9', fillColor:'#e879f9', fillOpacity:0.25, weight:1.5,
    });
    m.on('mouseover', e=>showTip(e,
      `🏘️ <b>${c.nombre}</b><br>Región ${c.region}<br>Población: <b>${c.poblacion.toLocaleString('es-CL')}</b>`));
    m.on('mouseout', ()=>hideTip());
    lgs.ciudades.addLayer(m);
  });
}

// ── LAYER TOGGLE ─────────────────────────────────────────────────────────────
const layerMap={sub:lgs.subestaciones,cen:lgs.centrales,des:lgs.desaladoras,
                rel:lgs.relaves,seia:lgs.seia,sigexotros:lgs.sigexOtros,train:lgs.train,ruido:lgs.ruido,
                ap:lgs.areasProtegidas,fibra:lgs.fibra,senal:lgs.senal,
                pue:lgs.puertos,pob:lgs.ciudades,opt:lgs.optLayer};
// ── RELAVE MAP FILTER ─────────────────────────────────────────────────────────
let relMapFilter = 'TODOS';

const REL_MAP_ESTADOS = [
  {key:'TODOS',           label:'Todos',      col:'#94a3b8'},
  {key:'ACTIVO',          label:'Activo',     col:'#22c55e'},
  {key:'INACTIVO',        label:'Inactivo',   col:'#f59e0b'},
  {key:'ABANDONADO',      label:'Abandonado', col:'#ef4444'},
  {key:'EN CONSTRUCCION', label:'En Constr.', col:'#38bdf8'},
];

function buildRelaveLayer(){
  lgs.relaves.clearLayers();
  const data = relMapFilter === 'TODOS'
    ? RAW.relaves
    : RAW.relaves.filter(r => r.estado === relMapFilter);
  data.forEach(r=>{
    const ec=RAW.config.estado_colors[r.estado]||'#6b7280';
    const riskCol = r.ciudad_risk==='PELIGRO'?'#ef4444':r.ciudad_risk==='ALERTA'?'#f97316':'#3d1708';
    const riskBorder = r.ciudad_risk ? '2.5px solid '+riskCol : '1px solid rgba(255,255,255,0.15)';
    const m=L.marker([r.lat,r.lon],{icon:L.divIcon({
      html:`<div class="infra-marker" style="background:${riskCol}33;border:${riskBorder}">♻️</div>`,
      className:'',iconSize:[25,25],iconAnchor:[12,12]
    })});
    const ciudadStr = r.ciudad_nombre
      ? `<br><span style="color:${r.ciudad_risk==='PELIGRO'?'#ef4444':'#f97316'}">⚠ ${r.ciudad_risk}: ${r.ciudad_km}km de ${r.ciudad_nombre} (${(r.ciudad_pop||0).toLocaleString('es-CL')} hab.)</span>`
      : '';
    m.on('mouseover',e=>showTip(e,
      `<b>${r.instalacion||r.faena}</b><br>${r.empresa}<br>
       <span style="color:${ec}">● ${r.estado}</span> · ${r.tipo}<br>
       Vol. autorizado: ${fmtNum(r.vol_autorizado)} m³<br>
       Vol. actual:     ${fmtNum(r.vol_actual)} m³<br>
       Vol. disponible: <b>${fmtNum(r.vol_disponible)} m³</b>${ciudadStr}`));
    m.on('mouseout',()=>hideTip());
    lgs.relaves.addLayer(m);
  });
  // Update counter badge on ctrl
  const badge = document.getElementById('rel-ctrl-count');
  if(badge) badge.textContent = data.length + ' relaves';
  // Sync active state of ctrl buttons
  document.querySelectorAll('.rel-ctrl-btn').forEach(b =>
    b.classList.toggle('active', b.dataset.key === relMapFilter));
}

// Build Leaflet custom control for relave filter
const RelaveCtrl = L.Control.extend({
  options: {position:'topleft'},
  onAdd: function(){
    const wrap = L.DomUtil.create('div','rel-ctrl-wrap');
    wrap.id = 'rel-map-ctrl';
    wrap.style.display = 'none';
    wrap.innerHTML = '<div class="rel-ctrl-title">♻️ Relaves <span id="rel-ctrl-count"></span></div>';
    L.DomEvent.disableClickPropagation(wrap);
    REL_MAP_ESTADOS.forEach(e=>{
      const btn = L.DomUtil.create('button','rel-ctrl-btn',wrap);
      btn.dataset.key = e.key;
      btn.innerHTML = `<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${e.col};margin-right:4px;vertical-align:middle"></span>${e.label}`;
      btn.onclick = ()=>{
        relMapFilter = e.key;
        buildRelaveLayer();
      };
    });
    return wrap;
  }
});
new RelaveCtrl().addTo(map);

// ── SIGEX clustering helpers ─────────────────────────────────────────────────
function convexHull(pts){
  // Graham scan — pts = [[lat,lon], ...]
  if(pts.length < 3) return pts;
  pts = pts.slice().sort((a,b)=>a[1]-b[1]||a[0]-b[0]);
  const cross=(O,A,B)=>(A[1]-O[1])*(B[0]-O[0])-(A[0]-O[0])*(B[1]-O[1]);
  const lower=[], upper=[];
  for(const p of pts){ while(lower.length>=2&&cross(lower[lower.length-2],lower[lower.length-1],p)<=0)lower.pop(); lower.push(p); }
  for(const p of [...pts].reverse()){ while(upper.length>=2&&cross(upper[upper.length-2],upper[upper.length-1],p)<=0)upper.pop(); upper.push(p); }
  upper.pop(); lower.pop();
  return lower.concat(upper);
}

// ── SIGEX filter state ───────────────────────────────────────────────────────
const sigexFilters = {recurso: new Set(), region: '', empresa: ''};
let sigexMarkers = [];
let sigexPolygons = [];

function buildSignexLayer(){
  lgs.seia.clearLayers();
  sigexMarkers = [];
  sigexPolygons = [];
  const data = RAW.sigex_sondajes_clusters || [];

  // Group by cluster for polygon drawing
  const clGroups = {};
  data.forEach(s=>{ if(s.cluster_id>=0){ (clGroups[s.cluster_id]||(clGroups[s.cluster_id]={pts:[],col:s.color})).pts.push([s.lat,s.lon]); } });

  // Draw convex hull polygons per cluster
  Object.entries(clGroups).forEach(([cid, {pts, col}])=>{
    const hull = convexHull(pts);
    if(hull.length < 2) return;
    const poly = L.polygon(hull, {
      color: col, fillColor: col, fillOpacity: 0.15, weight: 1.5, opacity: 0.7,
      dashArray: null,
    });
    poly.on('mouseover', e=>{ poly.setStyle({fillOpacity:0.3}); showTip(e,`<b style="color:${col}">Cluster ${cid}</b><br>${pts.length} sondajes`); });
    poly.on('mouseout', ()=>{ poly.setStyle({fillOpacity:0.15}); hideTip(); });
    sigexPolygons.push({poly, cluster_id:parseInt(cid), col});
    lgs.seia.addLayer(poly);
  });

  // Draw individual markers
  data.forEach(s=>{
    const col = s.color || '#6b7280';
    const isNoise = s.cluster_id < 0;
    const clLabel = isNoise ? 'Sin cluster' : `Cluster ${s.cluster_id}`;
    const m = L.circleMarker([s.lat, s.lon], {
      radius: isNoise ? 3 : 5, color: col, fillColor: col,
      fillOpacity: isNoise ? 0.3 : 0.9, weight: isNoise ? 0.5 : 1.2,
    });
    m.on('mouseover', e=>showTip(e,
      `<b style="color:${col}">⚙️ ${clLabel}</b><br>
       <b>${s.nombre}</b><br>${s.empresa}<br>
       ⛏️ ${s.recurso||'—'}<br>Estado: ${s.estado}
       ${s.enlace?'<br><span style="color:var(--accent);font-size:10px">🔗 Ver en SIGEX</span>':''}`));
    m.on('mouseout', ()=>hideTip());
    if(s.enlace) m.on('click',()=>window.open(s.enlace,'_blank'));
    sigexMarkers.push({marker:m, data:s});
    lgs.seia.addLayer(m);
  });
  initSignexBox();
  buildSignexOtrosLayer();
}

function applySignexFilters(){
  sigexFilters.region  = document.getElementById('sf-region')?.value  || '';
  sigexFilters.empresa = document.getElementById('sf-empresa')?.value || '';
  lgs.seia.clearLayers();
  let visible = 0;
  // Collect visible cluster IDs from filtered markers
  const visibleClusters = new Set();
  sigexMarkers.forEach(({marker, data})=>{
    const okRec = sigexFilters.recurso.size===0 || sigexFilters.recurso.has(data.recurso_grupo||'');
    const okReg = !sigexFilters.region  || data.region_norm===sigexFilters.region;
    const okEmp = !sigexFilters.empresa || data.empresa===sigexFilters.empresa;
    if(okRec && okReg && okEmp){ lgs.seia.addLayer(marker); visible++; if(data.cluster_id>=0) visibleClusters.add(data.cluster_id); }
  });
  // Re-draw polygons only for visible clusters
  sigexPolygons.forEach(({poly, cluster_id})=>{ if(visibleClusters.has(cluster_id)) lgs.seia.addLayer(poly); });
  const cnt = document.getElementById('sigex-count');
  if(cnt) cnt.textContent = `${visible} de ${sigexMarkers.length} sondajes · ${visibleClusters.size} clusters`;
}

function toggleSfPill(group, value, el){
  const set = sigexFilters[group];
  if(set.has(value)){ set.delete(value); el.classList.remove('on'); }
  else              { set.add(value);    el.classList.add('on'); }
  applySignexFilters();
}

function buildSignexOtrosLayer(){
  lgs.sigexOtros.clearLayers();
  (RAW.seia||[]).filter(s=>s.etapa!=='Sondajes').forEach(s=>{
    const meta = RAW.sigex_meta[s.etapa]||{icon:'🔍',color:'#94a3b8',label:s.etapa};
    const m = L.circleMarker([s.lat,s.lon],{
      radius:4, color:meta.color, fillColor:meta.color,
      fillOpacity:0.7, weight:1,
    });
    m.on('mouseover',e=>showTip(e,
      `<b style="color:${meta.color}">${meta.icon} ${meta.label}</b><br>
       <b>${s.nombre}</b><br>${s.empresa}<br>
       ⛏️ ${s.recurso||'—'}<br>Estado: ${s.estado}
       ${s.enlace?'<br><span style="color:var(--accent);font-size:10px">🔗 Ver en SIGEX</span>':''}`));
    m.on('mouseout',()=>hideTip());
    if(s.enlace) m.on('click',()=>window.open(s.enlace,'_blank'));
    lgs.sigexOtros.addLayer(m);
  });
}

function initSignexBox(){
  const data = RAW.sigex_sondajes_clusters || [];
  const nClusters = new Set(data.filter(d=>d.cluster_id>=0).map(d=>d.cluster_id)).size;
  // badge
  const badge = document.getElementById('sigex-total-badge');
  if(badge) badge.textContent = `${data.length} · ${nClusters} cl`;
  // recurso pills
  const recursos = [...new Set(data.map(d=>d.recurso_grupo||''))].sort();
  const rDiv = document.getElementById('sf-recurso');
  if(rDiv){ rDiv.innerHTML=''; recursos.forEach(r=>{
    const p=document.createElement('span'); p.className='sf-pill'; p.textContent=r;
    p.onclick=()=>toggleSfPill('recurso',r,p); rDiv.appendChild(p);
  });}
  // region select
  const regiones = [...new Set(data.map(d=>d.region_norm||''))].filter(Boolean).sort();
  const regSel = document.getElementById('sf-region');
  if(regSel){ regSel.innerHTML='<option value="">Todas las regiones</option>';
    regiones.forEach(r=>{ const o=document.createElement('option'); o.value=r; o.textContent=r; regSel.appendChild(o); }); }
  // empresa select (top 15)
  const empCount={};
  data.forEach(d=>{ empCount[d.empresa]=(empCount[d.empresa]||0)+1; });
  const topEmps=Object.entries(empCount).sort((a,b)=>b[1]-a[1]).slice(0,15).map(([e])=>e);
  const empSel=document.getElementById('sf-empresa');
  if(empSel){ empSel.innerHTML='<option value="">Todas las empresas</option>';
    topEmps.forEach(e=>{ const o=document.createElement('option'); o.value=e; o.textContent=`${e.slice(0,28)} (${empCount[e]})`; empSel.appendChild(o); }); }
  // count
  const cnt=document.getElementById('sigex-count');
  if(cnt) cnt.textContent=`${data.length} de ${data.length} sondajes · ${nClusters} clusters`;
}

function toggleLayer(key){
  flags[key]=!flags[key];
  const btn=document.getElementById('btn-'+key);
  if(flags[key]){ layerMap[key].addTo(map); btn.classList.add('active'); }
  else           { map.removeLayer(layerMap[key]); btn.classList.remove('active'); }
  if(key==='rel'){
    const ctrl = document.getElementById('rel-map-ctrl');
    if(ctrl) ctrl.style.display = flags[key] ? 'block' : 'none';
  }
  if(key==='seia'){
    const box = document.getElementById('sigex-box');
    if(box) box.classList.toggle('open', flags[key]);
  }
  if(window._optLegendHook) window._optLegendHook(key);
}

// ── TREND + SPARKLINE HELPERS ────────────────────────────────────────────────
function classifyTrend(cl, year) {
  const yrs = [];
  for(let y=year-4; y<=year; y++) if((cl.production[String(y)]||0) > 0) yrs.push(y);
  if(yrs.length < 3) return {label:'Sin datos', cls:'trend-nd', icon:'—'};
  const vals = yrs.map(y => cl.production[String(y)]);
  const n=yrs.length, mx=yrs.reduce((s,y)=>s+y,0)/n, mv=vals.reduce((s,v)=>s+v,0)/n;
  let num=0, den=0;
  for(let i=0;i<n;i++){num+=(yrs[i]-mx)*(vals[i]-mv);den+=(yrs[i]-mx)**2;}
  const pct = mv>0 ? (den>0?num/den:0)/mv*100 : 0;
  if(pct > 3)  return {label:'Creciendo', cls:'trend-up',   icon:'▲'};
  if(pct < -3) return {label:'Declinando', cls:'trend-down', icon:'▼'};
  return {label:'Estable', cls:'trend-flat', icon:'→'};
}

function getSparkline(cl, year) {
  const yrs = [], W=42, H=18, bw=5, gap=2;
  for(let y=year-5;y<=year;y++) yrs.push(y);
  const vals = yrs.map(y => cl.production[String(y)]||0);
  if(vals.every(v=>v===0)) return '';
  const maxV = Math.max(...vals, 0.001);
  const bars = vals.map((v,i) => {
    const h = Math.max(2, Math.round(v/maxV*(H-2)));
    const x = i*(bw+gap);
    const col = i===yrs.length-1 ? '#f59e0b' : (v>0 ? '#334155' : '#1e293b');
    return `<rect x="${x}" y="${H-h}" width="${bw}" height="${h}" fill="${col}" rx="1"/>`;
  }).join('');
  return `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" style="flex-shrink:0;display:block;opacity:0.9">${bars}</svg>`;
}

// ── CLUSTER LIST ─────────────────────────────────────────────────────────────
const EMPRESA_COLORS=[
  '#f59e0b','#38bdf8','#4ade80','#f472b6','#a78bfa',
  '#fb923c','#34d399','#60a5fa','#f87171','#c084fc'
];
function buildClusterList(filter=''){
  const wrap=document.getElementById('cluster-list');
  wrap.innerHTML='';
  const lc=filter.toLowerCase();
  const SIDEBAR_HIDDEN=new Set(['Ruido','Otros','V-1','III-3']);
  const all=Object.values(RAW.clusters).filter(cl=>!SIDEBAR_HIDDEN.has(cl.id));
  const show = (lc ? all.filter(cl =>
    cl.id.toLowerCase().includes(lc) || cl.label.toLowerCase().includes(lc) ||
    cl.top_mine.toLowerCase().includes(lc)) : all)
    .sort((a,b) => (b.production[String(currentYear)]||0) - (a.production[String(currentYear)]||0));

  show.forEach((cl, idx) => {
    const yr    = String(currentYear);
    const prod  = cl.production[yr];
    const prevP = cl.production[String(currentYear - 1)];
    const yoyPct = (prod && prevP && prevP > 0) ? ((prod - prevP) / prevP * 100) : null;
    const yoyHtml = yoyPct !== null
      ? `<span class="yoy ${yoyPct >= 5 ? 'yoy-pos' : yoyPct <= -5 ? 'yoy-neg' : 'yoy-neu'}">${yoyPct >= 0 ? '▲' : '▼'}${Math.abs(yoyPct).toFixed(0)}%</span>`
      : '';
    const rank = idx + 1;
    const top1 = cl.top_empresas[0];
    const trend = classifyTrend(cl, currentYear);
    const spark = getSparkline(cl, currentYear);
    const instCount = RAW.installations.filter(i=>i.cluster_id===cl.id).length;
    const div = document.createElement('div');
    div.className = 'cl-item' + (selectedCluster === cl.id ? ' selected' : '');
    div.id = 'cli-' + cl.id;
    // OPT score badge: show M7 ECI when OPT layer is active
    const optCl   = flags.opt ? OPT.clusters[cl.id] : null;
    const m7s     = optCl?.models?.M7?.data?.score_norm;
    const m5s     = optCl?.models?.M5?.data?.score_norm;
    const optBadge = optCl
      ? `<div style="display:flex;gap:3px;margin-top:2px">
          <span style="font-size:8px;font-weight:700;padding:1px 5px;border-radius:8px;
            background:rgba(245,158,11,0.15);color:#f59e0b;border:1px solid rgba(245,158,11,0.3)">
            M7 ${m7s!=null?Math.round(m7s*100):'—'}%</span>
          <span style="font-size:8px;font-weight:700;padding:1px 5px;border-radius:8px;
            background:rgba(34,197,94,0.12);color:#22c55e;border:1px solid rgba(34,197,94,0.25)">
            M5 ${m5s!=null?Math.round(m5s*100):'—'}%</span>
        </div>`
      : '';
    div.innerHTML = `
      <div class="rank-badge${rank <= 3 ? ' top3' : ''}">#${rank}</div>
      <div class="cl-dot" style="background:${cl.color};margin-left:2px"></div>
      <div style="flex:1;min-width:0">
        <div class="cl-mine">${cl.top_mine}</div>
        <div class="cl-sub">${cl.id} · ${cl.label.split('—')[0].trim()}</div>
        ${top1?`<div style="font-size:10px;color:var(--text3);margin-top:1px">${top1.empresa.length>28?top1.empresa.slice(0,28)+'…':top1.empresa} (${top1.pct}%)</div>`:''}
        ${optBadge}
      </div>
      <div class="cl-right" style="display:flex;flex-direction:column;align-items:flex-end;gap:2px">
        <div>${prod ? fmtProd(prod) + ' kTM' : '—'} ${yoyHtml}</div>
        <div class="sparkline-wrap">${spark}</div>
        <div style="display:flex;align-items:center;gap:4px">
          <span class="trend-badge ${trend.cls}" style="font-size:8px;padding:1px 5px">${trend.icon} ${trend.label}</span>
          <span style="color:var(--text3);font-size:10px">${instCount}</span>
        </div>
      </div>`;
    div.onclick = () => selectCluster(cl.id);
    wrap.appendChild(div);
  });
  if(!show.length) wrap.innerHTML='<div class="scroll-hint">Sin resultados</div>';
}

// ── SELECT / DESELECT CLUSTER ────────────────────────────────────────────────
function selectCluster(cid){
  selectedCluster=cid;
  const cl=RAW.clusters[cid]; if(!cl) return;
  Object.values(RAW.clusters).forEach(c=>{
    if(!c._poly) return;
    c._poly.setStyle(c.id===cid?{fillOpacity:0.52,weight:3.5}:{fillOpacity:0.10,weight:1});
  });
  if(cl._poly) map.fitBounds(cl._poly.getBounds(),{padding:[30,30]});
  showFaenas(cid);
  document.getElementById('cluster-list').style.display='none';
  document.getElementById('cluster-detail').style.display='block';
  try { fillClusterDetail(cid); } catch(e) { console.error('fillClusterDetail error:', e); }
  
  if(document.getElementById('pilar-panel')?.classList.contains('open')&&OPT.clusters[cid]){
    try { refreshAllInlineDetails(); } catch(e) { console.error('refreshAllInlineDetails error:', e); }
  }
}

function deselectCluster(){
  selectedCluster=null;
  Object.values(RAW.clusters).forEach(c=>{
    if(c._poly) c._poly.setStyle({fillOpacity:0.28,weight:2});
  });
  lgs.faenas.clearLayers();
  if(map.getZoom()<RAW.config.zoom_threshold) lgs.faenas.clearLayers();
  else buildFaenaMarkers();
  document.getElementById('cluster-list').style.display='';
  document.getElementById('cluster-detail').style.display='none';
  buildClusterList();
  document.getElementById('fc-tab').style.display='none';
  document.getElementById('forecast-col').classList.remove('open');
  document.getElementById('fc-tab-icon').textContent='›';
  fcColOpen=false;
  if(fcProjChart){ fcProjChart.destroy(); fcProjChart=null; }
  if(fcChart)    { fcChart.destroy();     fcChart=null; }
  if(fcWrChart)  { fcWrChart.destroy();   fcWrChart=null; }
  // Remove optimization radius circle
  if(_optRadiusCircle){ map.removeLayer(_optRadiusCircle); _optRadiusCircle=null; }
  // Hide opt cluster section
  const _ocs=document.getElementById('opt-cluster-section');
  if(_ocs) _ocs.style.display='none';
}

// ── CLUSTER DETAIL ────────────────────────────────────────────────────────────
function fillClusterDetail(cid){
  const cl=RAW.clusters[cid];
  const yr=String(currentYear);
  const prod=cl.production[yr]||0;
  const wEst=cl.water_est[yr]||0;
  const eEst=cl.elec_est[yr]||0;
  const faenas=RAW.faenas.filter(f=>f.cluster_id===cid);
  const installs=RAW.installations.filter(i=>i.cluster_id===cid);

  // Compute production rank among all clusters
  const allSorted = Object.values(RAW.clusters).filter(c=>c.id!=='Ruido')
    .sort((a,b) => (b.production[String(currentYear)]||0) - (a.production[String(currentYear)]||0));
  const rank = allSorted.findIndex(c=>c.id===cid) + 1;
  const prevProd = cl.production[String(currentYear-1)] || 0;
  const yoyPct2 = (prod && prevProd > 0) ? ((prod - prevProd) / prevProd * 100) : null;
  const yoyStr = yoyPct2 !== null
    ? ` <span style="color:${yoyPct2>=5?'#22c55e':yoyPct2<=-5?'#ef4444':'#94a3b8'};font-size:11px">${yoyPct2>=0?'▲':'▼'}${Math.abs(yoyPct2).toFixed(1)}% vs ${currentYear-1}</span>`
    : '';

  document.getElementById('det-id').innerHTML = `Clúster ${cid} <span style="font-size:12px;font-weight:500;color:var(--text2)">#${rank} productor${rank<=3?' 🥇🥈🥉'.split('')[rank-1]:''}</span>`;
  document.getElementById('det-label').textContent  = cl.label;
  document.getElementById('det-mine').innerHTML = `🏆 ${cl.top_mine}${yoyStr}`;
  document.getElementById('kpi-prod').textContent   = fmtProd(prod);
  document.getElementById('kpi-faenas').textContent  = installs.length;

  // % del pico histórico
  const allProds = Object.entries(cl.production).filter(([,v])=>v>0).sort(([,a],[,b])=>b-a);
  const peakV  = allProds.length ? allProds[0][1] : 0;
  const peakYr = allProds.length ? Number(allProds[0][0]) : null;
  const pctPeak = peakV>0 && prod>0 ? prod/peakV*100 : 0;
  const kpiPeak = document.getElementById('kpi-water');
  kpiPeak.textContent  = pctPeak>0 ? `${pctPeak.toFixed(0)}%` : '—';
  kpiPeak.style.color  = pctPeak>=90?'#22c55e':pctPeak>=60?'#f59e0b':'#ef4444';
  kpiPeak.title = peakYr ? `Pico: ${peakV.toFixed(1)} kTM en ${peakYr}` : '';

  // CAGR 5 años
  const prodY5 = cl.production[String(currentYear-5)] || 0;
  const cagr5y = prodY5>0 && prod>0 ? (Math.pow(prod/prodY5, 0.2)-1)*100 : null;
  const kpiCagr = document.getElementById('kpi-elec');
  kpiCagr.textContent = cagr5y!==null ? `${cagr5y>=0?'+':''}${cagr5y.toFixed(1)}%/a` : '—';
  kpiCagr.style.color = cagr5y===null?'var(--text2)':cagr5y>3?'#22c55e':cagr5y<-3?'#ef4444':'#f59e0b';

  // ── Indicadores del Valle: producción YoY + empleo estimado
  const kpiProdGrowth = document.getElementById('kpi-prod-growth');
  kpiProdGrowth.textContent = yoyPct2!==null ? `${yoyPct2>=0?'+':''}${yoyPct2.toFixed(1)}%` : '—';
  kpiProdGrowth.style.color = yoyPct2===null?'var(--text2)':yoyPct2>5?'#22c55e':yoyPct2<-5?'#ef4444':'#f59e0b';
  kpiProdGrowth.title = `Variación anual vs ${currentYear-1}`;
  const empEst = cl.emp_estimate || 0;
  const empGrowthPct = yoyPct2!==null ? yoyPct2*0.6 : null;
  const kpiEmpGrowth = document.getElementById('kpi-emp-growth');
  kpiEmpGrowth.textContent = empGrowthPct!==null ? `${empGrowthPct>=0?'+':''}${empGrowthPct.toFixed(1)}%` : '—';
  kpiEmpGrowth.style.color = empGrowthPct===null?'var(--text2)':empGrowthPct>3?'#22c55e':empGrowthPct<-3?'#ef4444':'#f59e0b';
  kpiEmpGrowth.title = empEst>0 ? `Empleo directo est.: ~${empEst.toLocaleString()} trabajadores (elasticidad 0.6×)` : '';

  // ── Operaciones en el Valle
  const _ac = cl.active_faenas_by_cat || {};
  const _cd = cl.cat_dist || {};
  const _catA = _ac['A']||0, _catB = _ac['B']||0, _catC = _ac['C']||0, _catD = _ac['D']||0;
  const _catSmall = _catC + _catD;
  const _totalOps = _catA + _catB + _catSmall;
  const _instA = _cd['A']||0, _instB = _cd['B']||0, _instC = _cd['C']||0, _instD = _cd['D']||0;
  const _instSmall = _instC + _instD;
  const _sigexFact     = cl.sigex_factibilidad     || 0;
  const _sigexExpl     = cl.sigex_exploracion      || 0;
  const _sigexGranMed  = cl.sigex_grandes_medianas || 0;
  document.getElementById('op-total-badge').textContent = _totalOps>0 ? `(${_totalOps} faenas activas)` : '';
  const _opPanel = document.getElementById('operaciones-panel');
  _opPanel.innerHTML = `
    <table style="width:100%;border-collapse:collapse;font-size:11px;margin-bottom:6px">
      <thead><tr>
        <th style="background:var(--bg3);color:var(--text2);padding:5px 6px;text-align:left;font-weight:600">Tipo</th>
        <th style="background:var(--bg3);color:var(--text2);padding:5px 6px;text-align:right;font-weight:600;font-size:10px">Faenas</th>
        <th style="background:var(--bg3);color:var(--text2);padding:5px 6px;text-align:right;font-weight:600;font-size:10px">Inst.</th>
        <th style="background:var(--bg3);color:var(--text2);padding:5px 6px;text-align:left;font-size:10px;font-weight:600">Referencia</th>
      </tr></thead>
      <tbody>
        <tr><td style="padding:4px 6px;border-bottom:1px solid var(--bg3)">
          <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#f59e0b;margin-right:4px"></span>Gran Minería</td>
          <td style="padding:4px 6px;border-bottom:1px solid var(--bg3);text-align:right;font-weight:700;color:#f59e0b">${_catA||'—'}</td>
          <td style="padding:4px 6px;border-bottom:1px solid var(--bg3);text-align:right;color:#f59e0b;opacity:0.7">${_instA||'—'}</td>
          <td style="padding:4px 6px;border-bottom:1px solid var(--bg3);font-size:10px;color:var(--text3)">Cat. A (≥ 400 trab.)</td></tr>
        <tr><td style="padding:4px 6px;border-bottom:1px solid var(--bg3)">
          <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#38bdf8;margin-right:4px"></span>Mediana Minería</td>
          <td style="padding:4px 6px;border-bottom:1px solid var(--bg3);text-align:right;font-weight:700;color:#38bdf8">${_catB||'—'}</td>
          <td style="padding:4px 6px;border-bottom:1px solid var(--bg3);text-align:right;color:#38bdf8;opacity:0.7">${_instB||'—'}</td>
          <td style="padding:4px 6px;border-bottom:1px solid var(--bg3);font-size:10px;color:var(--text3)">Cat. B (200–400 trab.)</td></tr>
        <tr><td style="padding:4px 6px;border-bottom:1px solid var(--bg3)">
          <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#4ade80;margin-right:4px"></span>Pequeña Minería</td>
          <td style="padding:4px 6px;border-bottom:1px solid var(--bg3);text-align:right;font-weight:700;color:#4ade80">${_catSmall||'—'}</td>
          <td style="padding:4px 6px;border-bottom:1px solid var(--bg3);text-align:right;color:#4ade80;opacity:0.7">${_instSmall||'—'}</td>
          <td style="padding:4px 6px;border-bottom:1px solid var(--bg3);font-size:10px;color:var(--text3)">Cat. C (≤ 80) + Cat. D (≤ 12 trab.)</td></tr>
        <tr><td style="padding:4px 6px;border-bottom:1px solid var(--bg3)">
          <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#fb923c;margin-right:4px"></span>Expl. Gdes/Med. empresas</td>
          <td colspan="2" style="padding:4px 6px;border-bottom:1px solid var(--bg3);text-align:right;font-weight:700;color:#fb923c">${_sigexGranMed||'—'}</td>
          <td style="padding:4px 6px;border-bottom:1px solid var(--bg3);font-size:10px;color:var(--text3)">Expl. SIGEX (gdes/med.)</td></tr>
        <tr style="border-top:2px solid var(--bg3)">
          <td style="padding:4px 6px;border-bottom:1px solid var(--bg3);font-weight:600">Total Operaciones Activas</td>
          <td colspan="2" style="padding:4px 6px;border-bottom:1px solid var(--bg3);text-align:right;font-weight:800">${_totalOps||'—'}</td>
          <td style="padding:4px 6px;border-bottom:1px solid var(--bg3);font-size:10px;color:var(--text3)">faenas activas</td></tr>
        <tr><td style="padding:4px 6px;border-bottom:1px solid var(--bg3)">
          <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#a78bfa;margin-right:4px"></span>Proyectos Greenfield</td>
          <td colspan="2" style="padding:4px 6px;border-bottom:1px solid var(--bg3);text-align:right;font-weight:700;color:#a78bfa">${_sigexFact||'—'}</td>
          <td style="padding:4px 6px;border-bottom:1px solid var(--bg3);font-size:10px;color:var(--text3)">Factibilidad (SIGEX)</td></tr>
        <tr><td style="padding:4px 6px">
          <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#94a3b8;margin-right:4px"></span>Exploración SIGEX</td>
          <td colspan="2" style="padding:4px 6px;text-align:right;font-weight:700;color:#94a3b8">${_sigexExpl||'—'}</td>
          <td style="padding:4px 6px;font-size:10px;color:var(--text3)">en 120 km del valle</td></tr>
        <tr style="border-top:2px solid var(--bg3);background:rgba(99,102,241,0.07)">
          <td style="padding:5px 6px;font-weight:600">👷 Empleo directo est.</td>
          <td colspan="2" style="padding:5px 6px;text-align:right;font-weight:800;color:#818cf8">~${empEst>0?empEst.toLocaleString():'—'}</td>
          <td style="padding:5px 6px;font-size:10px;color:var(--text3)">trabajadores (estimado)</td></tr>
      </tbody>
    </table>
  `;

  // Trend lifecycle badge
  const trend = classifyTrend(cl, currentYear);
  document.getElementById('det-trend').innerHTML =
    `<span class="trend-badge ${trend.cls}">${trend.icon} ${trend.label}</span>` +
    (peakYr ? `<span style="font-size:10px;color:var(--text3);margin-left:8px">Pico: <b style="color:var(--text)">${peakV.toFixed(0)} kTM</b> en ${peakYr}</span>` : '');

  currentClusterData = cl;
  currentPeakYr      = peakYr;
  buildProductionChart(cl, peakYr);
  buildForecastPanel(cl);
  buildRiskPanel(cl);

  // ── Category diversity (A/B/C/D) stacked bar + Shannon H badge
  const catDef = [
    {key:'A',   label:'Gran Minería (A)',    color:'#f59e0b'},
    {key:'B',   label:'Mediana Minería (B)', color:'#38bdf8'},
    {key:'C',   label:'Pequeña Minería (C)', color:'#4ade80'},
    {key:'D',   label:'Pirquineros (D)',      color:'#c084fc'},
    {key:'SIN', label:'Sin Categoría',        color:'#475569'},
  ];
  const catDist     = cl.cat_dist || {};
  const totalInst   = Object.values(catDist).reduce((a,b)=>a+b,0);
  document.getElementById('div-mine-count').textContent =
    totalInst>0 ? `(${totalInst} instalaciones)` : '';

  // Shannon diversity badge
  const H     = cl.diversity_h  ?? null;
  const grade = cl.diversity_grade || '';
  const badge = document.getElementById('div-h-badge');
  const gradeColor = {Alta:'#4ade80',Media:'#f59e0b',Baja:'#fb923c',Monoproducto:'#94a3b8','Sin datos':'#475569'};
  if(H !== null && grade !== 'Sin datos'){
    const gc = gradeColor[grade] || '#94a3b8';
    badge.textContent=`H=${H.toFixed(2)} · ${grade}`;
    badge.style.cssText=`font-size:10px;font-weight:700;padding:2px 7px;border-radius:10px;
      background:${gc}25;color:${gc};border:1px solid ${gc}50`;
  } else { badge.textContent=''; badge.style.cssText=''; }

  // Stacked bar
  const bar = document.getElementById('cat-stacked-bar');
  bar.innerHTML='';
  const leg = document.getElementById('cat-legend');
  leg.innerHTML='';
  catDef.forEach(c=>{
    const n = catDist[c.key]||0;
    if(!n) return;
    const pct = totalInst>0 ? n/totalInst*100 : 0;
    // minimum 3px so even small categories are visible
    const seg = document.createElement('div');
    seg.style.cssText=`flex:${pct} 0 3px;background:${c.color};height:100%;
      transition:flex .3s;min-width:3px`;
    seg.title=`${c.label}: ${n} (${pct.toFixed(1)}%)`;
    bar.appendChild(seg);
    const lbl = document.createElement('span');
    lbl.style.cssText=`display:inline-flex;align-items:center;gap:3px`;
    lbl.innerHTML=`<span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${c.color}"></span>
      <b style="color:${c.color}">${c.key}</b>\u00a0${n} <span style="color:var(--text3)">(${pct.toFixed(0)}%)</span>`;
    leg.appendChild(lbl);
  });
  if(!totalInst) bar.innerHTML='<div style="flex:1;background:var(--bg3);height:100%"></div>';

  // ── Process type chips (Óxidos / Sulfuros / Mixto / Polimetálico)
  const recDef = [
    {key:'Óxidos',       color:'#7dd3fc', icon:'🔵'},
    {key:'Sulfuros',     color:'#fb923c', icon:'🟠'},
    {key:'Mixto',        color:'#c084fc', icon:'🟣'},
    {key:'Polimetálico', color:'#94a3b8', icon:'💎'},
  ];
  const recDist = cl.recurso_dist || {};
  const totalRec = Object.values(recDist).reduce((a,b)=>a+b,0);
  const recWrap = document.getElementById('recurso-chips');
  recWrap.innerHTML='';
  recDef.forEach(r=>{
    const n = recDist[r.key]||0;
    if(!n) return;
    const pct = totalRec>0 ? Math.round(n/totalRec*100) : 0;
    const chip = document.createElement('div');
    chip.style.cssText=`padding:3px 8px;border-radius:12px;font-size:10px;font-weight:600;
      background:rgba(255,255,255,0.05);border:1px solid ${r.color}40;color:${r.color};
      display:flex;align-items:center;gap:4px`;
    chip.innerHTML=`${r.icon} ${r.key} <span style="color:var(--text3)">${n} · ${pct}%</span>`;
    recWrap.appendChild(chip);
  });
  if(!totalRec) recWrap.innerHTML='<span style="font-size:11px;color:var(--text3);font-style:italic">Sin datos proceso</span>';

  // ── TipoInstalacion breakdown (top 6 types)
  const tipoPanel = document.getElementById('tipo-dist-panel');
  tipoPanel.innerHTML='';
  const tipoDist = cl.tipo_dist || {};
  const tipoEntries = Object.entries(tipoDist).sort((a,b)=>b[1]-a[1]);
  if(tipoEntries.length){
    const tipoTotal = Object.values(tipoDist).reduce((a,b)=>a+b,0);
    const header = document.createElement('div');
    header.style.cssText='font-size:10px;font-weight:600;color:var(--text2);margin-bottom:4px;text-transform:uppercase;letter-spacing:.5px';
    header.textContent='Tipos de Instalación';
    tipoPanel.appendChild(header);
    tipoEntries.forEach(([tipo,n])=>{
      const pct = tipoTotal>0 ? n/tipoTotal*100 : 0;
      const row = document.createElement('div');
      row.style.cssText='display:flex;align-items:center;gap:6px;margin-bottom:3px';
      row.innerHTML=`
        <div style="flex:1;min-width:0;font-size:10px;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis"
             title="${tipo}">${tipo}</div>
        <div style="width:70px;background:var(--bg3);border-radius:2px;height:5px;flex-shrink:0">
          <div style="width:${pct.toFixed(1)}%;height:100%;background:#38bdf8;border-radius:2px"></div>
        </div>
        <div style="font-size:9px;color:var(--text3);width:28px;text-align:right;flex-shrink:0">${n}</div>`;
      tipoPanel.appendChild(row);
    });
  }

  // ── Mine segment panel (Gran / Mediana / Pequeña) — catastro SERNAGEOMIN-based
  const seg = cl.mine_segments || {};
  const segPanel = document.getElementById('mine-seg-panel');
  segPanel.innerHTML='';
  const segDefs=[
    {key:'Gran',   color:'#f59e0b',icon:'🏔️', label:'Gran',    desc:'Cat. A (≥ 400 trabajadores)'},
    {key:'Mediana',color:'#38bdf8',icon:'⛏️', label:'Mediana', desc:'Cat. B (200–400 trabajadores)'},
    {key:'Pequeña',color:'#a3e635',icon:'🪨', label:'Pequeña', desc:'Cat. C (≤ 80) + D (≤ 12 trab.)'},
  ];
  const totalMines = Object.values(seg).reduce((a,b)=>a+b,0);
  segDefs.forEach(s=>{
    const n=seg[s.key]||0;
    if(n===0 && totalMines>0) return;
    const pct=totalMines>0?Math.round(n/totalMines*100):0;
    const box=document.createElement('div');
    box.title=s.desc;
    box.style.cssText=`flex:1;min-width:70px;background:var(--bg3);border-radius:7px;
      padding:6px 8px;border-left:3px solid ${s.color};cursor:default`;
    box.innerHTML=`<div style="font-size:18px;line-height:1">${s.icon}</div>
      <div style="font-size:13px;font-weight:700;color:${s.color};margin-top:2px">${n}</div>
      <div style="font-size:10px;color:var(--text3)">${s.label}</div>
      ${totalMines>0?`<div style="font-size:9px;color:var(--text3)">${pct}%</div>`:''}`;
    segPanel.appendChild(box);
  });
  if(totalMines===0){
    segPanel.innerHTML='<div style="font-size:11px;color:var(--text3);font-style:italic">Sin datos de segmento</div>';
  }

  // ── Company breakdown
  document.getElementById('emp-total').textContent =
    cl.total_empresas>6 ? `(+${cl.total_empresas-6} empresas más)` : '';
  const empWrap=document.getElementById('empresa-bars');
  empWrap.innerHTML='';
  cl.top_empresas.forEach((e,i)=>{
    const col=EMPRESA_COLORS[i%EMPRESA_COLORS.length];
    const row=document.createElement('div');
    row.className='emp-row';
    const nameEl=document.createElement('div');
    nameEl.className='emp-name'; nameEl.title=e.empresa;
    nameEl.textContent=e.empresa;
    const barWrap=document.createElement('div'); barWrap.className='emp-bar-wrap';
    const bar=document.createElement('div'); bar.className='emp-bar';
    bar.style.width=Math.max(e.pct,5)+'%'; bar.style.background=col;
    bar.textContent=e.pct>10?`${e.pct}%`:'';
    barWrap.appendChild(bar);
    const pctEl=document.createElement('div'); pctEl.className='emp-pct';
    pctEl.textContent=e.pct+'%';
    row.appendChild(nameEl); row.appendChild(barWrap); row.appendChild(pctEl);
    empWrap.appendChild(row);
  });
  if(!cl.top_empresas.length) empWrap.innerHTML='<div class="scroll-hint">Sin datos</div>';

  // ── Production by company (kt/año promedio 2020-2025)
  const prodCoWrap=document.getElementById('prod-company-bars');
  prodCoWrap.innerHTML='';
  const prodByCo=cl.prod_by_company||[];
  if(prodByCo.length){
    prodByCo.forEach((e,i)=>{
      const col=EMPRESA_COLORS[i%EMPRESA_COLORS.length];
      const row=document.createElement('div'); row.className='emp-row';
      const nameEl=document.createElement('div'); nameEl.className='emp-name';
      nameEl.title=e.co; nameEl.textContent=e.co;
      const barWrap=document.createElement('div'); barWrap.className='emp-bar-wrap';
      const bar=document.createElement('div'); bar.className='emp-bar';
      bar.style.width=Math.max(e.pct,5)+'%'; bar.style.background=col;
      bar.textContent=e.pct>12?`${e.pct}%`:'';
      barWrap.appendChild(bar);
      const pctEl=document.createElement('div'); pctEl.className='emp-pct';
      pctEl.textContent=`${e.kt_avg.toFixed(0)} kt`;
      pctEl.title=`${e.pct}% del total del clúster`;
      row.appendChild(nameEl); row.appendChild(barWrap); row.appendChild(pctEl);
      prodCoWrap.appendChild(row);
    });
  } else {
    prodCoWrap.innerHTML='<div style="font-size:11px;color:var(--text3);font-style:italic;padding:4px 0">Sin datos de producción por empresa</div>';
  }

  // ── Production by mine
  const prodMineWrap=document.getElementById('prod-mine-bars');
  prodMineWrap.innerHTML='';
  const mineRoster=cl.mine_roster||[];
  if(mineRoster.length){
    mineRoster.forEach((r,i)=>{
      const col=EMPRESA_COLORS[i%EMPRESA_COLORS.length];
      const row=document.createElement('div'); row.className='emp-row';
      const nameEl=document.createElement('div'); nameEl.className='emp-name';
      nameEl.title=r.name; nameEl.textContent=r.name;
      const barWrap=document.createElement('div'); barWrap.className='emp-bar-wrap';
      const bar=document.createElement('div'); bar.className='emp-bar';
      bar.style.width=Math.max(r.pct,5)+'%'; bar.style.background=col;
      bar.textContent=r.pct>12?`${r.pct}%`:'';
      barWrap.appendChild(bar);
      const pctEl=document.createElement('div'); pctEl.className='emp-pct';
      pctEl.textContent=`${r.avg_prod.toFixed(0)} kt`;
      pctEl.title=`${r.pct}% del clúster · ${r.holding}`;
      row.appendChild(nameEl); row.appendChild(barWrap); row.appendChild(pctEl);
      prodMineWrap.appendChild(row);
    });
  } else {
    prodMineWrap.innerHTML='<div style="font-size:11px;color:var(--text3);font-style:italic;padding:4px 0">Sin datos de producción por mina</div>';
  }

  // ── Derechos de Agua (DGA)
  const agua=cl.agua||{};
  const aguaCount=agua.count||0;
  const aguaLs=agua.total_ls||0;
  document.getElementById('agua-count-badge').textContent=
    aguaCount>0?`${aguaCount.toLocaleString()} reg · ${Math.round(aguaLs).toLocaleString()} L/s`:'Sin registros cercanos';

  function _aguaStacked(barId, legId, data, colMap){
    const barEl=document.getElementById(barId); const legEl=document.getElementById(legId);
    barEl.innerHTML=''; legEl.innerHTML='';
    const tot=Object.values(data).reduce((a,b)=>a+b,0);
    if(!tot){barEl.innerHTML='<div style="flex:1;background:var(--bg3);height:100%"></div>'; return;}
    Object.entries(data).sort((a,b)=>b[1]-a[1]).forEach(([k,v])=>{
      const pct=v/tot*100; const col=colMap[k]||'#94a3b8';
      const seg=document.createElement('div');
      seg.style.cssText=`flex:${pct} 0 3px;background:${col};height:100%;min-width:3px`;
      seg.title=`${k}: ${v} (${pct.toFixed(1)}%)`; barEl.appendChild(seg);
      const lbl=document.createElement('span');
      lbl.style.cssText='display:inline-flex;align-items:center;gap:3px';
      lbl.innerHTML=`<span style="display:inline-block;width:7px;height:7px;border-radius:2px;background:${col}"></span><span style="color:var(--text)">${k}</span><span style="color:var(--text3)"> ${v}</span>`;
      legEl.appendChild(lbl);
    });
  }
  _aguaStacked('agua-tipo-bar','agua-tipo-legend',agua.tipo||{},
    {'Consuntivo':'#f59e0b','No Consuntivo':'#38bdf8'});
  _aguaStacked('agua-nat-bar','agua-nat-legend',agua.naturaleza||{},
    {'Subterránea':'#c084fc','Superficial':'#4ade80','Superficial y Corriente':'#86efac'});

  // Uso breakdown
  const usoPanel=document.getElementById('agua-uso-panel'); usoPanel.innerHTML='';
  const usoDGA=agua.uso||{}; const usoTotal=Object.values(usoDGA).reduce((a,b)=>a+b,0);
  const usoCols=['#f59e0b','#38bdf8','#4ade80','#c084fc','#f87171','#94a3b8'];
  if(usoTotal>0){
    const usoHeader=document.createElement('div');
    usoHeader.style.cssText='font-size:10px;color:var(--text3);margin-bottom:4px';
    usoHeader.textContent='Uso del Agua (top 6)'; usoPanel.appendChild(usoHeader);
    Object.entries(usoDGA).sort((a,b)=>b[1]-a[1]).slice(0,6).forEach(([uso,n],i)=>{
      const pct=n/usoTotal*100; const col=usoCols[i%usoCols.length];
      const row=document.createElement('div');
      row.style.cssText='display:flex;align-items:center;gap:6px;margin-bottom:3px';
      row.innerHTML=`<div style="flex:1;min-width:0;font-size:10px;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="${uso}">${uso}</div>
        <div style="width:60px;background:var(--bg3);border-radius:2px;height:5px;flex-shrink:0">
          <div style="width:${pct.toFixed(1)}%;height:100%;background:${col};border-radius:2px"></div>
        </div>
        <div style="font-size:9px;color:var(--text3);width:28px;text-align:right;flex-shrink:0">${n}</div>`;
      usoPanel.appendChild(row);
    });
  }

  // Year sparkline
  const byYear=agua.by_year||{}; const yearKeys=Object.keys(byYear).sort();
  const sparkEl=document.getElementById('agua-year-spark');
  const yearLbl=document.getElementById('agua-year-label');
  sparkEl.innerHTML='';
  if(yearKeys.length>0){
    const maxV=Math.max(...Object.values(byYear));
    yearKeys.forEach(yr=>{
      const v=byYear[yr]; const h=maxV>0?Math.round(v/maxV*28)+2:2;
      const bar=document.createElement('div');
      bar.style.cssText=`flex:1;height:${h}px;background:#38bdf8;border-radius:2px 2px 0 0;min-width:2px;opacity:${0.4+v/maxV*0.6}`;
      bar.title=`${yr}: ${v} derechos`; sparkEl.appendChild(bar);
    });
    const peakEntry=Object.entries(byYear).sort((a,b)=>b[1]-a[1])[0];
    yearLbl.textContent=`${yearKeys[0]}–${yearKeys[yearKeys.length-1]} · Pico: ${peakEntry[1]} en ${peakEntry[0]}`;
  } else { yearLbl.textContent='Sin fechas conocidas'; }

  // ── KPI: Relaves activos
  const relAct = cl.relaves_activos_count||0;
  const relVol = cl.relaves_activos_vol||0;
  const kpiRel = document.getElementById('kpi-relaves');
  kpiRel.textContent = relAct>0 ? relAct : '—';
  kpiRel.style.color = relAct>0?'#f59e0b':'var(--text3)';
  kpiRel.title = relVol>0 ? `Vol. disp.: ${fmtNum(relVol)} m³` : '';

  // ── KPI: % Renovable
  const pctRen = cl.pct_renovable||0;
  const kpiRen = document.getElementById('kpi-ren');
  kpiRen.textContent = pctRen>0 ? `${pctRen.toFixed(0)}%` : '—';
  kpiRen.style.color = pctRen>=60?'#22c55e':pctRen>=30?'#f59e0b':'#ef4444';

  // ── Electricity capacity + energy mix ────────────────────────────────────
  const eCap=cl.elec_capacity_mwh||0;
  const ePct=eCap>0?Math.min(110,(eEst/eCap)*100):0;
  document.getElementById('cap-elec-val').textContent=
    eCap ? `${fmtElec(eCap)} GWh/año` : 'Sin centrales cercanas';
  document.getElementById('cap-elec-bar').style.width=ePct+'%';
  document.getElementById('cap-elec-bar').style.background=ePct>90?'#ef4444':ePct>60?'#f59e0b':'#22c55e';
  document.getElementById('cap-elec-pct').textContent=eCap
    ? `Uso est.: ${ePct.toFixed(1)}% de la capacidad instalada local`
    : 'Abastecido desde la red nacional (SEN)';

  // Renovable badge
  document.getElementById('ren-badge').innerHTML = pctRen>0
    ? `<span class="trend-badge ${pctRen>=60?'trend-up':pctRen>=30?'trend-flat':'trend-down'}">${pctRen.toFixed(0)}% renovable</span>`
    : '';

  // Energy mix bars
  const mixWrap = document.getElementById('energy-mix-wrap');
  mixWrap.innerHTML = '';
  const emix = cl.energy_mix || {};
  const totalMW = Object.values(emix).reduce((s,v)=>s+v,0);
  const mixDefs = [
    {key:'solar',  label:'☀️ Solar/CSP', col:'#fbbf24'},
    {key:'eolico', label:'💨 Eólico',    col:'#34d399'},
    {key:'hidro',  label:'💧 Hidro',     col:'#38bdf8'},
    {key:'termica',label:'🔥 Térmica',   col:'#f87171'},
    {key:'otro',   label:'⚙️ Otro',      col:'#94a3b8'},
  ];
  mixDefs.forEach(({key,label,col}) => {
    const mw = emix[key]||0; if(mw<=0) return;
    const pct = totalMW>0 ? mw/totalMW*100 : 0;
    const row=document.createElement('div');
    row.style.cssText='display:flex;align-items:center;gap:6px;font-size:10px';
    row.innerHTML=`<span style="width:80px;color:var(--text2);flex-shrink:0">${label}</span>
      <div style="flex:1;height:5px;background:var(--bg3);border-radius:3px;overflow:hidden">
        <div style="height:100%;width:${pct.toFixed(1)}%;background:${col};border-radius:3px"></div>
      </div>
      <span style="width:42px;text-align:right;color:var(--text2)">${mw.toFixed(0)} MW</span>`;
    mixWrap.appendChild(row);
  });

  // ── Water capacity (operational mining desaladoras only, exclusivity-aware) ──
  const wCap=cl.water_mining_capacity_m3||0;
  // Coverage = how much of estimated need is met by nearby desalination
  const wCovPct = (wEst>0 && wCap>0) ? Math.min(100, wCap/wEst*100) : (wCap>0 ? 100 : 0);
  const nReg = cl.n_region_clusters||1;
  const wExcl=cl.water_excl_count||0, wShar=cl.water_shared_count||0;
  const wFactor = cl.water_factor || 155;
  document.getElementById('cap-water-label').textContent=
    wCap>0 ? `Excl.: ${wExcl} · Compartidas: ${wShar} (÷${nReg} clúster/s región)` : 'Sin desaladoras mineras operativas';
  document.getElementById('cap-water-val').textContent=
    wCap ? `${fmtWater(wCap)} Mm³/año` : 'abastecimiento continental';
  document.getElementById('cap-water-bar').style.width=wCovPct+'%';
  document.getElementById('cap-water-bar').style.background=
    wCap===0?'#475569':wCovPct>=70?'#22c55e':wCovPct>=30?'#f59e0b':'#ef4444';
  const wEstMm3 = fmtWater(wEst);
  document.getElementById('cap-water-pct').textContent=wCap
    ? `Demanda est.: ${wEstMm3} Mm³/año · Cobertura desalación: ${wCovPct.toFixed(0)}%`
    : `Demanda est.: ${wEstMm3} Mm³/año · sin desalación operativa cercana`;
  document.getElementById('desal-excl-note').innerHTML = wCap>0
    ? `⚠️ Compartidas ÷${nReg} clústeres · Factor hídrico: <b>${wFactor} m³/t Cu</b>`
    : `<span style="color:var(--text3)">Factor hídrico: <b>${wFactor} m³/t Cu</b> (fuentes continentales)</span>`;

  // ── Relaves
  const rels=cl.relaves||[];
  document.getElementById('rel-total').textContent=
    rels.length>0?`${rels.length} instalac. · Vol. disp. total: ${fmtNum(cl.relaves_vol_disponible)} m³`:'';

  // ── TSF fill-up time indicator ────────────────────────────────────────────
  const tsfDiv = document.getElementById('tsf-summary');
  const tsfYrs = cl.relaves_tsf_years;
  const annualTail = cl.relaves_annual_tailings_m3 || 0;
  if (tsfYrs !== null && tsfYrs !== undefined) {
    const urgency = tsfYrs < 10 ? '#ef4444' : tsfYrs < 20 ? '#f59e0b' : '#22c55e';
    const urgencyLabel = tsfYrs < 10 ? 'CRÍTICO' : tsfYrs < 20 ? 'ATENCIÓN' : 'ESTABLE';
    // Bar fills left→right as remaining years approach 0 (fuller TSF = more urgent)
    const fillPct = Math.min(100, Math.max(0, (1 - tsfYrs / 30) * 100)).toFixed(0);
    tsfDiv.innerHTML = `
      <div style="background:rgba(255,255,255,0.04);border-radius:6px;padding:8px 10px;border-left:3px solid ${urgency}">
        <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:5px">
          <span style="font-size:11px;font-weight:600;color:var(--text1)">⏳ Vida útil estimada del TSF</span>
          <span style="font-size:14px;font-weight:700;color:${urgency}">${tsfYrs.toFixed(1)} años
            <span style="font-size:9px;padding:1px 5px;border-radius:3px;background:${urgency}22;margin-left:3px">${urgencyLabel}</span>
          </span>
        </div>
        <div style="background:var(--bg3);border-radius:3px;height:6px;overflow:hidden;margin-bottom:5px">
          <div style="height:100%;width:${fillPct}%;background:${urgency};border-radius:3px;transition:width .4s"></div>
        </div>
        <div style="font-size:10px;color:var(--text3);line-height:1.5">
          Vol. activo disponible: <b>${fmtNum(cl.relaves_activos_vol||0)} m³</b> ·
          Tasa anual estimada: <b>${fmtNum(annualTail)} m³/año</b>
        </div>
        <div style="font-size:9px;color:var(--text3);margin-top:2px;font-style:italic">
          ⚙ Estimación basada en producción promedio 2020–2024 y factores Cochilco: Sulfuros 100k · Mixto 70k · Óxidos 15k m³/kt Cu
        </div>
      </div>`;
  } else if ((cl.relaves_activos_count||0) > 0) {
    tsfDiv.innerHTML = `<div style="font-size:10px;color:var(--text3);font-style:italic;padding:4px 0">
      TSF activos presentes pero sin datos de producción suficientes para estimar vida útil.</div>`;
  } else {
    tsfDiv.innerHTML = '';
  }

  // Build filter buttons
  const REL_ESTADOS=[
    {key:'TODOS',      label:'Todos',         col:'#94a3b8'},
    {key:'ACTIVO',     label:'Activo',        col:'#22c55e'},
    {key:'INACTIVO',   label:'Inactivo',      col:'#f59e0b'},
    {key:'ABANDONADO', label:'Abandonado',    col:'#ef4444'},
    {key:'EN CONSTRUCCION', label:'En Constr.', col:'#38bdf8'},
  ];
  let relFilter='TODOS';
  const btnWrap=document.getElementById('rel-filter-btns');
  btnWrap.innerHTML='';

  function renderRelTable(){
    const filtered = relFilter==='TODOS' ? rels : rels.filter(r=>r.estado===relFilter);
    const tbody=document.getElementById('rel-tbody');
    tbody.innerHTML='';
    if(!filtered.length){
      tbody.innerHTML='<tr><td colspan="5" style="color:var(--text3);font-style:italic">Sin relaves para este filtro</td></tr>';
      return;
    }
    filtered.slice(0,20).forEach(r=>{
      const ec=RAW.config.estado_colors[r.estado]||'#6b7280';
      const tr=document.createElement('tr');
      tr.innerHTML=`<td>${r.instalacion||r.faena}</td><td>${r.tipo}</td>
        <td><span class="e-dot" style="background:${ec}"></span>${r.estado}</td>
        <td>${fmtNum(r.vol_disponible)}</td>
        <td style="font-size:10px;${r.ciudad_risk==='PELIGRO'?'color:#ef4444;font-weight:700':r.ciudad_risk==='ALERTA'?'color:#f97316':'color:var(--text3)'}">
          ${r.ciudad_nombre ? r.ciudad_risk+' '+r.ciudad_km+'km<br><span style="font-size:9px">'+r.ciudad_nombre+'</span>' : '—'}
        </td>`;
      tbody.appendChild(tr);
    });
    if(filtered.length>20){
      const tr=document.createElement('tr');
      tr.innerHTML=`<td colspan="5" style="color:var(--text3);font-style:italic">… y ${filtered.length-20} más</td>`;
      tbody.appendChild(tr);
    }
  }

  REL_ESTADOS.forEach(e=>{
    const count = e.key==='TODOS' ? rels.length : rels.filter(r=>r.estado===e.key).length;
    if(e.key!=='TODOS' && count===0) return; // hide empty states
    const btn=document.createElement('button');
    btn.className='rel-filter-btn';
    btn.dataset.key=e.key;
    btn.innerHTML=`<span class="e-dot" style="background:${e.col};margin-right:3px"></span>${e.label} <b>${count}</b>`;
    btn.onclick=()=>{
      relFilter=e.key;
      btnWrap.querySelectorAll('.rel-filter-btn').forEach(b=>b.classList.toggle('active', b.dataset.key===e.key));
      renderRelTable();
    };
    if(e.key===relFilter) btn.classList.add('active');
    btnWrap.appendChild(btn);
  });

  if(!rels.length){
    document.getElementById('rel-tbody').innerHTML=
      '<tr><td colspan="5" style="color:var(--text3);font-style:italic">Sin relaves asignados</td></tr>';
  } else {
    renderRelTable();
  }

  // ── Nearby centrales
  const clat=cl.center[0],clon=cl.center[1];
  const nc=RAW.centrales
    .map(c=>({...c,d:hav(clat,clon,c.lat,c.lon)}))
    .filter(c=>c.d<150).sort((a,b)=>a.d-b.d).slice(0,6);
  const infC=document.getElementById('infra-cen');
  infC.innerHTML=nc.length?'':'<div style="color:var(--text3);font-size:11px;font-style:italic">Sin centrales &lt;150 km</div>';
  const tipoIcon={'Fotovoltaico':'☀️','Eolico':'💨','Eólico':'💨',
    'Hidraulica Pasada':'💧','Hidráulica Pasada':'💧','Hidraulica Embalse':'💧',
    'Termoelectrica':'🔥','Termoeléctrica':'🔥','CSP':'☀️'};
  nc.forEach(c=>{
    const ico=tipoIcon[c.tipo]||'⚡';
    const isRen=!c.tipo.toLowerCase().includes('termoel');
    const col=isRen?'#22c55e':'#f87171';
    const div=document.createElement('div'); div.className='infra-item';
    div.innerHTML=`<span class="infra-icon">${ico}</span>
      <div style="flex:1;min-width:0">
        <div class="infra-name">${c.nombre}</div>
        <div style="font-size:10px;color:var(--text3)">${c.tipo} · ${c.potencia_mw} MW
          <span style="color:${col};font-weight:700;margin-left:3px">${isRen?'RENV':'TERM'}</span>
        </div>
      </div>
      <div class="infra-dist">${c.d.toFixed(0)} km</div>`;
    div.onclick=()=>map.flyTo([c.lat,c.lon],12);
    infC.appendChild(div);
  });

  // ── Nearby desaladoras (from pre-computed cluster data with utilization)
  const nd=(cl.nearby_desaladoras||[])
    .sort((a,b)=>{
      if(a.operativa!==b.operativa) return a.operativa?-1:1;
      if(a.available!==b.available) return a.available?-1:1;
      return a.dist_km-b.dist_km;
    }).slice(0,8);
  const infD=document.getElementById('infra-des');
  infD.innerHTML=nd.length?'':'<div style="color:var(--text3);font-size:11px;font-style:italic">Sin desaladoras mineras &lt;250 km</div>';
  nd.forEach(d=>{
    let badge;
    if(!d.available){
      badge=`<span style="font-size:9px;font-weight:700;color:#6b7280;margin-left:4px;background:rgba(107,114,128,0.12);padding:1px 4px;border-radius:3px">OTRA EMP.</span>`;
    } else if(d.exclusiva){
      badge=`<span style="font-size:9px;font-weight:700;color:#f87171;margin-left:4px;background:rgba(239,68,68,0.1);padding:1px 4px;border-radius:3px">EXCL.</span>`;
    } else {
      badge=`<span style="font-size:9px;font-weight:700;color:var(--accent);margin-left:4px;background:var(--blue-tint);padding:1px 4px;border-radius:3px">COMPART.</span>`;
    }
    const opBadge=d.operativa
      ?`<span style="color:#22c55e;font-weight:700">● Operativa</span>`
      :`<span style="color:#94a3b8">◌ ${d.estado}</span>`;
    const coverPctCapped=Math.min(100,d.cover_pct);
    const barColor=coverPctCapped>80?'#22c55e':coverPctCapped>40?'#f59e0b':'#38bdf8';
    const coverLabel=d.cover_pct>100?`≥${d.cover_pct.toFixed(0)}% (supera demanda est.)`:`${d.cover_pct.toFixed(1)}% de la demanda est.`;
    const coverBar=d.available && d.operativa && d.cover_pct>0
      ?`<div style="margin-top:3px;background:rgba(255,255,255,0.06);border-radius:3px;height:4px;overflow:hidden">
           <div style="height:100%;width:${coverPctCapped}%;background:${barColor};transition:width .3s"></div>
         </div>
         <div style="font-size:9px;color:var(--text3);margin-top:1px">Cubre ${coverLabel}</div>`
      :``;
    const div=document.createElement('div'); div.className='infra-item';
    div.style.opacity=d.operativa?'1':'0.55';
    div.innerHTML=`<span class="infra-icon">💧</span>
      <div style="flex:1;min-width:0">
        <div class="infra-name">${d.nombre}${badge}</div>
        <div style="font-size:10px;color:var(--text3)">${d.capacidad_lps} lps · ${opBadge}</div>
        <div style="font-size:10px;color:var(--text3)">${d.empresa}</div>
        ${coverBar}
      </div>
      <div class="infra-dist">${d.dist_km} km</div>`;
    div.onclick=()=>map.flyTo([d.lat,d.lon],12);
    infD.appendChild(div);
  });

  // ── Mine roster table ─────────────────────────────────────────────────────
  const roster = cl.mine_roster || [];
  document.getElementById('roster-total').textContent =
    roster.length ? `(${roster.length} mina${roster.length>1?'s':''})` : '';
  const rtbody = document.getElementById('mine-roster-tbody');
  rtbody.innerHTML = '';
  if(!roster.length){
    rtbody.innerHTML = '<tr><td colspan="4" style="color:var(--text3);font-style:italic;padding:6px">Sin datos</td></tr>';
  } else {
    roster.forEach((m, idx) => {
      const col = EMPRESA_COLORS[idx % EMPRESA_COLORS.length];
      const pctW = Math.max(3, m.pct);
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td style="font-weight:600;color:var(--text)">${m.name}</td>
        <td style="color:var(--text2);max-width:130px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
            title="${m.holding}">${m.holding}</td>
        <td>${m.avg_prod > 0 ? m.avg_prod.toFixed(1) : '—'}</td>
        <td>
          <span class="pct-bar" style="width:${pctW}px;background:${col}"></span>
          <span style="color:${col};font-weight:700">${m.pct}%</span>
        </td>`;
      if(m.lat && m.lon){
        tr.style.cursor = 'pointer';
        tr.title = `Ir a ${m.name}`;
        tr.onclick = () => map.flyTo([m.lat, m.lon], 11);
      }
      rtbody.appendChild(tr);
    });
  }

  // ── Category ratio cards (A=Gran Minería, B=Mediana, C=Pequeña, D=Artesanal) ──
  const catR = cl.cat_dist || {};
  const cA   = catR.A || 0;
  const cB   = catR.B || 0;
  const cC   = catR.C || 0;
  const cD   = catR.D || 0;

  function ratioStr(a, b){
    if(b === 0) return a > 0 ? '∞' : '—';
    const v = a / b;
    return v >= 10 ? v.toFixed(0) : v.toFixed(1);
  }

  const ratios = [
    {
      formula: 'A / (B+C+D)',
      val:     ratioStr(cA, cB+cC+cD),
      desc:    `Gran minería (${cA}) vs resto (${cB+cC+cD})`,
    },
    {
      formula: '(A+B) / (C+D)',
      val:     ratioStr(cA+cB, cC+cD),
      desc:    `Gran+Mediana (${cA+cB}) vs Pequeña+Artesanal (${cC+cD})`,
    },
    {
      formula: 'A / B',
      val:     ratioStr(cA, cB),
      desc:    `Cat A: ${cA} faenas · Cat B: ${cB} faenas`,
    },
    {
      formula: 'C / D',
      val:     ratioStr(cC, cD),
      desc:    `Cat C: ${cC} faenas · Cat D: ${cD} faenas`,
    },
  ];

  const rGrid = document.getElementById('ratio-grid');
  rGrid.innerHTML = '';
  ratios.forEach(r => {
    const card = document.createElement('div');
    card.className = 'ratio-card';
    card.innerHTML = `
      <div class="ratio-formula">${r.formula}</div>
      <div class="ratio-val">${r.val}</div>
      <div class="ratio-desc">${r.desc}</div>`;
    rGrid.appendChild(card);
  });

  // ── Faenas list  (sorted by category A→B→C→D→SIN)
  const catOrder={'CATEGORIA A':0,'CATEGORIA B':1,'CATEGORIA C':2,'CATEGORIA D':3,'SIN CATEGORIA':4};
  const catColorMap={'CATEGORIA A':'#f59e0b','CATEGORIA B':'#38bdf8',
    'CATEGORIA C':'#4ade80','CATEGORIA D':'#c084fc','SIN CATEGORIA':'#475569'};
  const catLabelMap={'CATEGORIA A':'A','CATEGORIA B':'B',
    'CATEGORIA C':'C','CATEGORIA D':'D','SIN CATEGORIA':'SIN'};
  const fSorted=[...faenas].sort((a,b)=>
    (catOrder[a.categoria]??99)-(catOrder[b.categoria]??99));
  const fList=document.getElementById('faena-list-det');
  fList.innerHTML='';
  fSorted.forEach(f=>{
    const ec=RAW.config.estado_colors[f.estado]||'#6b7280';
    const catKey=f.categoria||'SIN CATEGORIA';
    const catColor=catColorMap[catKey]||'#475569';
    const catLabel=catLabelMap[catKey]||'?';
    const div=document.createElement('div'); div.className='faena-item';
    div.innerHTML=`
      <div style="width:6px;border-radius:2px;align-self:stretch;background:${catColor};flex-shrink:0;margin-right:6px"></div>
      <div class="f-dot" style="background:${ec};flex-shrink:0"></div>
      <div style="flex:1;min-width:0">
        <div class="f-name">${f.name}</div>
        <div class="f-meta">${f.empresa} · ${f.comuna}</div>
      </div>
      <div style="display:flex;flex-direction:column;align-items:flex-end;gap:2px;flex-shrink:0">
        <span style="font-size:9px;font-weight:700;padding:1px 5px;border-radius:4px;
          background:${catColor}22;color:${catColor};border:1px solid ${catColor}44">${catLabel}</span>
        <span style="font-size:9px;color:var(--text3)">${f.num_installations} inst.</span>
      </div>`;
    div.onclick=()=>{ map.flyTo([f.lat,f.lon],13); openFaenaPopup(f); };
    fList.appendChild(div);
  });
  // Populate optimization section if OPT layer is active
  fillOptClusterDetail(cid);
}

// ── OPTIMIZATION CLUSTER DETAIL (sidebar) ────────────────────────────────────
function fillOptClusterDetail(cid){
  const sec = document.getElementById('opt-cluster-section');
  if(!sec) return;
  if(!flags.opt){ sec.style.display='none'; return; }
  const oc = OPT.clusters[cid];
  if(!oc){ sec.style.display='none'; return; }
  sec.style.display='block';

  const MDEF=[
    {key:'M1',short:'M1 KDE Exploración',color:'#a78bfa',inverted:false},
    {key:'M3',short:'M3 Gravedad Prod.',  color:'#38bdf8',inverted:false},
    {key:'M4',short:'M4 Riesgo Amb.',     color:'#ef4444',inverted:true },
    {key:'M5',short:'M5 NPPI Integrado',  color:'#22c55e',inverted:false},
    {key:'M7',short:'M7 ECI Competencia', color:'#f59e0b',inverted:false},
  ];

  // Radius label
  const rKm = OPT.radius_km || 12;
  const rLbl = document.getElementById('opt-radius-label');
  if(rLbl) rLbl.textContent = `📍 Radio de análisis: ${rKm} km`;

  // Score table
  const tbl = document.getElementById('opt-score-table');
  if(tbl){
    tbl.innerHTML = MDEF.map(m=>{
      const d   = oc.models[m.key]?.data || {};
      const pct = d.score_norm!=null ? Math.round(d.score_norm*100) : 0;
      const bar = m.inverted ? 100-pct : pct;
      const lbl = m.inverted ? `Riesgo ${pct}%` : `${pct}%`;
      return `<tr class="opt-score-row">
        <td><span class="opt-m-dot" style="background:${m.color}"></span></td>
        <td class="opt-mid" style="color:${m.color}">${m.key}</td>
        <td class="opt-mname">${m.short}</td>
        <td class="opt-bar-wrap"><div class="opt-bar-bg"><div class="opt-bar-fill" style="width:${bar}%;background:${m.color}"></div></div></td>
        <td class="opt-pct" style="color:${m.color}">${lbl}</td>
      </tr>`;
    }).join('');
  }

  // KPIs from stats
  const st = oc.stats || {};
  const kpiRow = document.getElementById('opt-kpi-row');
  if(kpiRow){
    const fmtInv = v => v>=1000 ? (v/1000).toFixed(1)+'B$' : (v||0).toFixed(0)+'M$';
    kpiRow.innerHTML = [
      {v:st.n_catA||0,         l:'Cat-A'},
      {v:st.n_explor_total||0, l:'Exploración'},
      {v:st.n_seia_approved||0,l:'SEIA Aprobados'},
      {v:fmtInv(st.inv_approved_MMU||0), l:'Inv. Aprobada'},
      {v:st.n_rel_active||0,   l:'Relaves Activos'},
      {v:st.n_rel_abandoned||0,l:'Abandonados'},
    ].map(k=>`<div class="kpi"><div class="kpi-val" style="font-size:15px">${k.v}</div>
      <div class="kpi-lbl">${k.l}</div></div>`).join('');
  }

  // Convergence bars (all except M5 which is reference)
  const m5s = oc.models?.M5?.data?.score_norm ?? 0;
  const convEl = document.getElementById('opt-conv-bars');
  if(convEl){
    convEl.innerHTML = MDEF.filter(m=>m.key!=='M5').map(m=>{
      const s   = oc.models?.[m.key]?.data?.score_norm ?? 0;
      const disp= m.inverted ? 1-s : s;
      const pct = Math.round(disp*100);
      return `<div class="opt-conv-row">
        <div style="width:28px;font-size:9px;font-weight:700;color:${m.color}">${m.key}</div>
        <div class="opt-conv-bar"><div class="opt-conv-fill" style="width:${pct}%;background:${m.color}"></div></div>
        <div style="width:28px;font-size:9px;font-weight:700;text-align:right;color:${m.color}">${pct}%</div>
      </div>`;
    }).join('') +
    `<div style="font-size:9px;color:var(--text3);margin-top:5px">
      M5 NPPI: <b style="color:#22c55e">${Math.round(m5s*100)}%</b> ·
      M7 ECI: <b style="color:#f59e0b">${Math.round((oc.models?.M7?.data?.score_norm??0)*100)}%</b>
    </div>`;
  }

  // SEIA table
  const seiaProjs = oc.seia_projects || [];
  const seiaTbl = document.getElementById('opt-seia-table');
  if(seiaTbl){
    if(!seiaProjs.length){
      seiaTbl.innerHTML='<tr><td style="color:var(--text3);font-size:10px;padding:6px">Sin proyectos aprobados en zona</td></tr>';
    } else {
      seiaTbl.innerHTML = '<thead><tr><th>Proyecto</th><th style="text-align:right">Inv (MMU$)</th></tr></thead><tbody>'+
        seiaProjs.map(p=>{
          const nm = p.name.length>42 ? p.name.slice(0,40)+'…' : p.name;
          return `<tr><td>${nm}</td><td style="text-align:right;font-weight:700;color:var(--accent)">${p.inv?.toFixed(0)||'—'}</td></tr>`;
        }).join('')+'</tbody>';
    }
  }

  // Exploration list
  const expSites = oc.exploration_sites || [];
  const expList  = document.getElementById('opt-explor-list');
  if(expList){
    if(!expSites.length){
      expList.innerHTML='<div class="opt-exp-item"><span style="color:var(--text3)">Sin sitios de exploración activos</span></div>';
    } else {
      expList.innerHTML = expSites.map(e=>`<div class="opt-exp-item">
        <span>🔍</span>
        <span class="opt-exp-name">${(e.empresa||'—').replace('LTDA.','').trim()}</span>
        <span class="opt-exp-tipo">${(e.tipo||'').replace('EXPLORACION DE ','')}</span>
      </div>`).join('');
    }
  }

  // Relaves table
  const topRel = (st.top_relaves||[]).slice(0,5);
  const relTbl = document.getElementById('opt-rel-table');
  if(relTbl){
    if(!topRel.length){
      relTbl.innerHTML='<tr><td style="color:var(--text3);font-size:10px;padding:6px">Sin relaves registrados</td></tr>';
    } else {
      const estCls = e => e==='ACTIVO'?'Aprobado':e==='INACTIVO'?'Calificacion':'Otro';
      relTbl.innerHTML = '<thead><tr><th>Faena</th><th>Estado</th><th>Tipo</th></tr></thead><tbody>'+
        topRel.map(r=>`<tr>
          <td>${r.faena||'—'}</td>
          <td><span class="estado-badge estado-${estCls(r.estado)}">${r.estado||'?'}</span></td>
          <td style="color:var(--text3);font-size:9px">${(r.tipo||'').replace('TRANQUE DE ','')||'—'}</td>
        </tr>`).join('')+'</tbody>';
    }
  }

  // Draw radius circle on map around best M5 point
  if(_optRadiusCircle){ map.removeLayer(_optRadiusCircle); _optRadiusCircle=null; }
  const m5dat = oc.models?.M5?.data;
  if(m5dat?.lat!=null && m5dat?.lon!=null){
    _optRadiusCircle = L.circle([m5dat.lat, m5dat.lon], {
      radius: rKm*1000,
      color:'#22c55e', weight:1.5,
      fillColor:'#22c55e', fillOpacity:0.04,
      dashArray:'7 5', interactive:false,
    }).addTo(map);
  }
}

// ── PRODUCTION CHART ─────────────────────────────────────────────────────────
function buildProductionChart(cl, peakYr){
  if(prodChart){ prodChart.destroy(); prodChart=null; }
  const ctx = document.getElementById('prod-chart').getContext('2d');

  if(currentProdMode === 'monthly'){
    // ── MONTHLY MODE ──────────────────────────────────────────────────────────
    const monProd = cl.production_monthly || {};
    const labels  = Object.keys(monProd).sort();
    const vals    = labels.map(k => monProd[k] || 0);
    if(!labels.length){
      ctx.clearRect(0,0,ctx.canvas.width,ctx.canvas.height);
      ctx.fillStyle='#64748b'; ctx.font='12px sans-serif'; ctx.textAlign='center';
      ctx.fillText('Sin datos mensuales para este clúster', ctx.canvas.width/2, ctx.canvas.height/2);
      return;
    }
    // Find current month label
    const nowLabel = new Date().toISOString().slice(0,7);
    const ci = labels.indexOf(nowLabel);
    // Monthly peak
    const peakVal = Math.max(...vals);
    const peakIdx = vals.indexOf(peakVal);

    prodChart = new Chart(ctx,{
      type:'line',
      data:{
        labels,
        datasets:[{
          label:'Producción mensual (kTM)',
          data:vals,
          borderColor:'rgba(167,139,250,0.85)',
          backgroundColor:'rgba(167,139,250,0.07)',
          borderWidth:1.5, fill:true, tension:0.2,
          pointRadius: labels.map((_,i)=>(i===ci||i===peakIdx)?5:0),
          pointHoverRadius:6,
          pointBackgroundColor: labels.map((_,i)=>
            i===ci?'#f59e0b': i===peakIdx?'#ef4444':'rgba(167,139,250,0.6)'),
        }]
      },
      options:{
        responsive:true, maintainAspectRatio:false,
        plugins:{
          legend:{display:false},
          tooltip:{callbacks:{label:c=>{
            const p=c.parsed.y;
            const lbl=labels[c.dataIndex];
            const isPeak=(c.dataIndex===peakIdx);
            return `${lbl}: ${p.toFixed(2)} kTM${isPeak?' 🏆 Máx.':''}`;
          }}}
        },
        scales:{
          x:{ticks:{color:'#64748b',font:{size:8},maxRotation:45,maxTicksLimit:18},
             grid:{color:'rgba(100,116,139,0.1)'}},
          y:{ticks:{color:'#64748b',font:{size:9}},
             grid:{color:'rgba(100,116,139,0.12)'}}
        }
      }
    });

  } else {
    // ── ANNUAL MODE (default) ─────────────────────────────────────────────────
    const years = Object.keys(cl.production).map(Number).sort((a,b)=>a-b);
    const vals  = years.map(y=>cl.production[String(y)]||0);
    if(!years.length) return;
    const ci    = years.indexOf(currentYear);
    const pi    = peakYr ? years.indexOf(peakYr) : -1;
    const peakV = pi>=0 ? vals[pi] : 0;

    // Per-mine history lines
    const _MINE_COLORS = [
      'rgba(251,191,36,0.65)','rgba(167,139,250,0.65)','rgba(34,197,94,0.65)',
      'rgba(251,113,133,0.65)','rgba(96,165,250,0.65)','rgba(251,146,60,0.65)',
      'rgba(20,184,166,0.65)','rgba(192,132,252,0.65)','rgba(245,101,101,0.65)',
      'rgba(56,189,248,0.5)'
    ];
    const mineDatasets = [];
    const fcMines = (cl.forecast||{}).mines || {};
    let _ci = 0;
    Object.entries(fcMines).forEach(([mk, fd]) => {
      const hist = fd.history || {};
      const mVals = years.map(y => hist[String(y)] ?? null);
      if(mVals.every(v=>v===null)) return;
      const col = _MINE_COLORS[_ci % _MINE_COLORS.length]; _ci++;
      mineDatasets.push({
        label: fcMineName(mk),
        data: mVals,
        borderColor: col,
        backgroundColor: 'transparent',
        borderWidth: 1, fill: false, tension: 0.2, order: 3,
        pointRadius: 0, pointHoverRadius: 4,
      });
    });

    prodChart = new Chart(ctx,{
      type:'line',
      data:{
        labels:years,
        datasets:[
          {
            label:'Producción (kTM)',
            data:vals,
            borderColor:'rgba(56,189,248,0.9)',
            backgroundColor:'rgba(56,189,248,0.07)',
            borderWidth:2, fill:true, tension:0.3, order:2,
            pointBackgroundColor:years.map((_,i)=>
              i===ci?'#f59e0b': i===pi?'#ef4444':'rgba(56,189,248,0.5)'),
            pointRadius:years.map((_,i)=>(i===ci||i===pi)?6:2.5),
            pointHoverRadius:8,
          },
          {
            label:'Pico histórico',
            data: peakV>0 ? years.map(()=>peakV) : [],
            borderColor:'rgba(239,68,68,0.22)',
            borderWidth:1, borderDash:[5,4],
            pointRadius:0, fill:false, tension:0, order:1,
          },
          ...mineDatasets
        ]
      },
      options:{
        responsive:true, maintainAspectRatio:false,
        plugins:{
          legend:{
            display: mineDatasets.length > 0,
            position:'bottom',
            labels:{color:'#64748b',font:{size:8},boxWidth:10,padding:6,
              filter: item => item.datasetIndex !== 1}
          },
          tooltip:{callbacks:{label:ctx=>{
            if(ctx.datasetIndex===1) return null;
            if(ctx.datasetIndex>=2){
              return `${ctx.dataset.label}: ${ctx.parsed.y!=null?ctx.parsed.y.toFixed(1)+' kTM':'—'}`;
            }
            const yr=years[ctx.dataIndex];
            const p=ctx.parsed.y;
            const isPeak=(yr===peakYr);
            return [
              `Producción: ${p.toFixed(1)} kTM${isPeak?' 🏆 Máx. histórico':''}`,
              `Agua est.: ${((cl.water_est[String(yr)]||0)/1e6).toFixed(3)} Mm³`,
              `Elec. est.: ${((cl.elec_est[String(yr)]||0)/1e3).toFixed(1)} GWh`
            ].filter(Boolean);
          }}}
        },
        scales:{
          x:{ticks:{color:'#64748b',font:{size:9},maxRotation:45,maxTicksLimit:10},
             grid:{color:'rgba(100,116,139,0.12)'}},
          y:{ticks:{color:'#64748b',font:{size:9}},
             grid:{color:'rgba(100,116,139,0.12)'}}
        }
      }
    });
  }
}

// ── FORECAST PANEL ───────────────────────────────────────────────────────────
// Returns effective WR for grading: annual if available, else monthly, else 0
function fcEffWr(d){ return d.wr ?? d.wr_m ?? 0; }
function fcGrade(wr){
  if(wr==null) return '?';
  if(wr>=0.70) return 'A';
  if(wr>=0.50) return 'B';
  if(wr>=0.40) return 'C';
  return 'F';
}
function fcGradeColor(wr){
  if(wr==null) return '#94a3b8';
  if(wr>=0.70) return '#22c55e';
  if(wr>=0.50) return '#a3e635';
  if(wr>=0.40) return '#f59e0b';
  return '#ef4444';
}
function fcMineName(k){
  return k.replace('centinela_centinela_sulfuros_','centinela sulfuros')
          .replace('centinela_centinela_óxidos_','centinela óxidos')
          .replace('capstone copper (4)','capstone copper')
          .replace(/_/g,' ');
}

function toggleForecastCol(){
  const col  = document.getElementById('forecast-col');
  const icon = document.getElementById('fc-tab-icon');
  fcColOpen = !fcColOpen;
  col.classList.toggle('open', fcColOpen);
  icon.textContent = fcColOpen ? '‹' : '›';
  if(fcColOpen && currentClusterData){
    setTimeout(()=>{
      const fc = (currentClusterData.forecast||{});
      const mk = document.getElementById('fc-mine-select').value;
      if(mk && fc.mines?.[mk]){
        const d = fc.mines[mk];
        buildFcBestChart(d, mk);
        buildFcCompare(d);
        if(fcSections.ann){ buildFcProjectionChart(d,mk); buildFcChart(d,mk); buildFcAnnMetrics(d); }
        if(fcSections.tbl){ buildFcWrChart(fc); }
      }
    }, 320);
  }
}

function buildFcProjectionChart(d, mk){
  if(fcProjChart){ fcProjChart.destroy(); fcProjChart=null; }
  const ctx = document.getElementById('fc-proj-chart').getContext('2d');
  const hist = d.history || {};
  const _sc = currentScenario || 'base';
  const proj = (d.proj_scenarios && d.proj_scenarios[_sc]
    && (d.proj_scenarios[_sc].years||[]).length > 0)
    ? {...d.proj, pred: d.proj_scenarios[_sc].pred, lower: d.proj_scenarios[_sc].lower, upper: d.proj_scenarios[_sc].upper}
    : (d.proj || {});

  // Combine: history years (≥2010) + projection years
  const histYears = Object.keys(hist).map(Number).filter(y=>y>=2010).sort((a,b)=>a-b);
  const projYears = (proj.years || []);
  const allLabels = [...histYears.map(String), ...projYears.map(String)];
  const splitIdx  = histYears.length;  // index where forecast starts

  const histVals = histYears.map(y => hist[String(y)] ?? null);
  // Bridge: last history point + first forecast point for continuity
  const predVals = allLabels.map((yr,i) => {
    if(i < splitIdx - 1) return null;
    if(i === splitIdx - 1) return hist[yr] ?? null;  // anchor at 2025
    const pi = projYears.indexOf(Number(yr));
    return pi>=0 ? (proj.pred?.[pi] ?? null) : null;
  });
  const naiveVals = allLabels.map((yr,i) => {
    if(i < splitIdx - 1) return null;
    if(i === splitIdx - 1) return hist[yr] ?? null;
    const pi = projYears.indexOf(Number(yr));
    return pi>=0 ? (proj.naive?.[pi] ?? null) : null;
  });
  const lowerVals = allLabels.map((yr,i) => {
    if(i < splitIdx - 1) return null;
    if(i === splitIdx - 1) return hist[yr] ?? null;
    const pi = projYears.indexOf(Number(yr));
    return pi>=0 ? (proj.lower?.[pi] ?? null) : null;
  });
  const upperVals = allLabels.map((yr,i) => {
    if(i < splitIdx - 1) return null;
    if(i === splitIdx - 1) return hist[yr] ?? null;
    const pi = projYears.indexOf(Number(yr));
    return pi>=0 ? (proj.upper?.[pi] ?? null) : null;
  });

  // Vertical separator annotation via a dataset with null except at split boundary
  const sepYear = String(histYears[histYears.length-1] ?? 2025);

  fcProjChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: allLabels,
      datasets: [
        // Upper bound (invisible line for fill)
        {
          label: '_upper',
          data: upperVals,
          borderColor: 'transparent',
          backgroundColor: 'rgba(245,158,11,0.12)',
          fill: '+1',
          pointRadius: 0, tension: 0.25, order: 5,
        },
        // Lower bound
        {
          label: '_lower',
          data: lowerVals,
          borderColor: 'transparent',
          backgroundColor: 'rgba(245,158,11,0.12)',
          fill: false,
          pointRadius: 0, tension: 0.25, order: 5,
        },
        // Historical production
        {
          label: 'Histórico',
          data: histVals.concat(new Array(projYears.length).fill(null)),
          borderColor: 'rgba(56,189,248,0.85)',
          backgroundColor: 'rgba(56,189,248,0.07)',
          borderWidth: 2, fill: true, tension: 0.25, order: 1,
          pointRadius: allLabels.map((_,i)=> i===splitIdx-1 ? 5 : 1.5),
          pointHoverRadius: 5,
          pointBackgroundColor: 'rgba(56,189,248,0.8)',
        },
        // Projection (dashed)
        {
          label: 'Proyección ML',
          data: predVals,
          borderColor: '#f59e0b',
          borderWidth: 2, fill: false, tension: 0.25, order: 2,
          borderDash: [6,3],
          pointRadius: allLabels.map((_,i)=> i>=splitIdx ? 3 : 0),
          pointHoverRadius: 5,
          pointBackgroundColor: '#f59e0b',
        },
        // Naïve flat line
        {
          label: 'Naïve',
          data: naiveVals,
          borderColor: 'rgba(100,116,139,0.5)',
          borderWidth: 1, fill: false, tension: 0, order: 3,
          borderDash: [2,5],
          pointRadius: 0,
        },
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      interaction: {mode:'index', intersect:false},
      plugins: {
        legend: {
          display: true,
          labels: {
            color:'#94a3b8', font:{size:9}, boxWidth:14, padding:7,
            usePointStyle:true,
            filter: item => !item.text.startsWith('_'),
          }
        },
        tooltip: {
          filter: item => !item.dataset.label.startsWith('_'),
          callbacks: {
            label: c => {
              const v = c.parsed.y;
              if(v==null) return null;
              const yr = Number(allLabels[c.dataIndex]);
              const suffix = yr > 2025 ? ' (proyección)' : '';
              return `${c.dataset.label}: ${v.toFixed(1)} kTM${suffix}`;
            },
            afterBody: (items) => {
              const i = items[0]?.dataIndex;
              if(i==null) return;
              const yr = Number(allLabels[i]);
              if(yr > 2025){
                const pi = projYears.indexOf(yr);
                const lo = proj.lower?.[pi], hi = proj.upper?.[pi];
                if(lo!=null && hi!=null)
                  return [`Banda: ${lo.toFixed(1)} – ${hi.toFixed(1)} kTM`];
              }
            }
          }
        },
        annotation: undefined,
      },
      scales: {
        x: {
          ticks: {
            color: c => Number(allLabels[c.index]) > 2025 ? '#f59e0b' : '#64748b',
            font: {size:9}, maxRotation:0,
          },
          grid: {
            color: c => Number(allLabels[c.index]) === 2025 ? 'rgba(245,158,11,0.4)' : 'rgba(100,116,139,0.08)',
            lineWidth: c => Number(allLabels[c.index]) === 2025 ? 2 : 1,
          }
        },
        y: {
          ticks: {color:'#64748b', font:{size:9}},
          grid:  {color:'rgba(100,116,139,0.12)'},
          title: {display:true, text:'kTM', color:'#475569', font:{size:8}}
        }
      }
    }
  });
}

// ── METRIC BADGES ────────────────────────────────────────────────────────────
function metricBadge(label, val, color, note=''){
  return `<div style="background:var(--bg3);border-radius:6px;padding:4px 8px;min-width:0">
    <div style="font-size:8px;color:var(--text3);margin-bottom:1px">${label}</div>
    <div style="font-size:11px;font-weight:700;color:${color}">${val}</div>
    ${note?`<div style="font-size:8px;color:var(--text3)">${note}</div>`:''}
  </div>`;
}
function buildFcAnnMetrics(d){
  const el = document.getElementById('fc-ann-metrics');
  if(!el) return;
  if(d.wr==null){ el.innerHTML='<span style="font-size:9px;color:var(--text3)">Sin modelo anual para esta mina</span>'; return; }
  const skillC = d.skill>0?'#22c55e':d.skill<-5?'#ef4444':'#f59e0b';
  const dmC = d.dm_p==null?'#64748b':d.dm_p<0.05?'#22c55e':d.dm_p<0.10?'#f59e0b':'#94a3b8';
  const dmV = d.dm_sig&&d.dm_sig.length>0 ? d.dm_sig : (d.dm_p!=null?'n.s.':'—');
  el.innerHTML =
    metricBadge('Win Rate', (d.wr*100).toFixed(0)+'%', fcGradeColor(d.wr), fcGrade(d.wr)) +
    metricBadge('MASE', d.mase.toFixed(3), d.mase<=1?'#22c55e':'#ef4444', d.mase<=1?'<1 ✓':'≥1') +
    metricBadge('Skill', (d.skill>=0?'+':'')+d.skill.toFixed(1)+'%', skillC) +
    (d.mdape!=null?metricBadge('MdAPE', d.mdape.toFixed(1)+'%','#94a3b8','típico'):'') +
    (d.dm_p!=null?metricBadge('DM test', dmV, dmC, 'p='+d.dm_p.toFixed(3)):'');
}
function buildFcMonMetrics(d){
  const el = document.getElementById('fc-mon-metrics');
  if(!el) return;
  if(d.wr_m==null){ el.innerHTML='<span style="font-size:9px;color:var(--text3)">Sin datos mensuales</span>'; return; }
  const skillC = (d.skill_m||0)>0?'#22c55e':(d.skill_m||0)<-5?'#ef4444':'#f59e0b';
  const dmCm = d.dm_p_m==null?'#64748b':d.dm_p_m<0.05?'#22c55e':d.dm_p_m<0.10?'#f59e0b':'#94a3b8';
  const dmVm = d.dm_sig_m&&d.dm_sig_m.length>0 ? d.dm_sig_m : (d.dm_p_m!=null?'n.s.':'—');
  el.innerHTML =
    metricBadge('Win Rate', (d.wr_m*100).toFixed(0)+'%', fcGradeColor(d.wr_m), fcGrade(d.wr_m)) +
    metricBadge('MASE', d.mase_m!=null?d.mase_m.toFixed(3):'—', d.mase_m!=null&&d.mase_m<=1?'#22c55e':'#ef4444') +
    metricBadge('Skill', d.skill_m!=null?(d.skill_m>=0?'+':'')+d.skill_m.toFixed(1)+'%':'—', skillC) +
    (d.mdape_m!=null?metricBadge('MdAPE', d.mdape_m.toFixed(1)+'%','#94a3b8','típico'):'') +
    (d.dm_p_m!=null?metricBadge('DM test', dmVm, dmCm, 'p='+d.dm_p_m.toFixed(3)):'');
}

// ── BEST MODEL COMPARE BADGES ─────────────────────────────────────────────────
function buildFcCompare(d){
  const el = document.getElementById('fc-best-compare');
  if(!el) return;
  const wrA = d.wr, wrM = d.wr_m;
  const annWins = wrM==null || wrA >= wrM;
  function badge(label, wr, isWinner){
    if(wr==null) return `<div style="flex:1;background:var(--bg3);border-radius:8px;padding:6px 8px;
      border:1px solid var(--bg4);opacity:0.4">
      <div style="font-size:8px;color:var(--text3)">${label}</div>
      <div style="font-size:10px;color:var(--text3)">sin datos</div></div>`;
    const gc = fcGradeColor(wr);
    const border = isWinner ? `2px solid ${gc}` : '1px solid var(--bg4)';
    const glow   = isWinner ? `box-shadow:0 0 8px ${gc}40` : '';
    return `<div style="flex:1;background:var(--bg3);border-radius:8px;padding:6px 8px;
      border:${border};${glow};cursor:pointer" onclick="">
      <div style="font-size:8px;color:var(--text3);margin-bottom:2px">${label}${isWinner?' 🏆':''}</div>
      <div style="font-size:14px;font-weight:800;color:${gc}">${(wr*100).toFixed(0)}%</div>
      <div style="font-size:9px;color:${gc};font-weight:700">Grado ${fcGrade(wr)}</div>
    </div>`;
  }
  el.innerHTML = badge('ANUAL', wrA, annWins) + badge('MENSUAL', wrM, !annWins);
}

// ── BEST CHART (winning model's projection) ───────────────────────────────────
function buildFcBestChart(d, mk){
  if(fcBestChart){ fcBestChart.destroy(); fcBestChart=null; }
  const wrA = d.wr, wrM = d.wr_m;
  const annWins = wrM==null || wrA >= wrM;
  const ctx = document.getElementById('fc-best-chart').getContext('2d');
  if(annWins){
    _drawProjChart(ctx, d, 'annual', v=>{ fcBestChart=v; });
  } else {
    _drawProjChart(ctx, d, 'monthly', v=>{ fcBestChart=v; });
  }
}

function _drawProjChart(ctx, d, mode, cb){
  const hist = d.history || {};
  const proj = mode==='annual' ? (d.proj||{}) : (d.proj_m||{});
  const isMonthly = mode==='monthly';
  const histSrc   = isMonthly ? (d.history_m || d.history || {}) : (d.history || {});
  const histYears  = Object.keys(histSrc).map(Number).filter(y=>y>=2010).sort((a,b)=>a-b);
  const projLabels = isMonthly
    ? (proj.months||[]).map(m=>m.slice(0,7))   // "2026-01"
    : (proj.years||[]).map(String);
  const splitIdx = histYears.length;

  // History values (annual scale for annual, monthly scale for monthly)
  const histVals  = histYears.map(y=>histSrc[String(y)]??null);
  const allLabels = [...histYears.map(String), ...projLabels];

  // Prediction / lower / upper — offset by splitIdx
  const predArr  = proj.pred   || [];
  const lowerArr = proj.lower  || [];
  const upperArr = proj.upper  || [];
  const naiveArr = proj.naive  || [];

  function projVal(arr, i){
    if(i < splitIdx-1) return null;
    if(i === splitIdx-1) return histSrc[String(histYears[histYears.length-1])] ?? null;
    return arr[i-splitIdx] ?? null;
  }
  const predVals  = allLabels.map((_,i)=>projVal(predArr,i));
  const lowerVals = allLabels.map((_,i)=>projVal(lowerArr,i));
  const upperVals = allLabels.map((_,i)=>projVal(upperArr,i));
  const naiveVals = allLabels.map((_,i)=>projVal(naiveArr,i));

  const accentC = mode==='annual'?'#f59e0b':'#a78bfa';
  const chart = new Chart(ctx,{
    type:'line',
    data:{ labels:allLabels, datasets:[
      {label:'_upper',data:upperVals,borderColor:'transparent',backgroundColor:`${accentC}18`,fill:'+1',pointRadius:0,tension:.3,order:5},
      {label:'_lower',data:lowerVals,borderColor:'transparent',backgroundColor:`${accentC}18`,fill:false,pointRadius:0,tension:.3,order:5},
      {label:'Histórico',data:histVals.concat(new Array(projLabels.length).fill(null)),
       borderColor:'rgba(56,189,248,0.85)',backgroundColor:'rgba(56,189,248,0.07)',
       borderWidth:2,fill:true,tension:.3,order:1,
       pointRadius:allLabels.map((_,i)=>i===splitIdx-1?5:0),pointHoverRadius:5,pointBackgroundColor:'rgba(56,189,248,0.8)'},
      {label:'Proyección ML',data:predVals,borderColor:accentC,borderWidth:2,fill:false,tension:.3,
       borderDash:[6,3],order:2,pointRadius:allLabels.map((_,i)=>i>=splitIdx?2:0),pointHoverRadius:4,pointBackgroundColor:accentC},
      {label:'Naïve',data:naiveVals,borderColor:'rgba(100,116,139,0.45)',borderWidth:1,fill:false,
       tension:0,order:3,borderDash:[2,5],pointRadius:0},
    ]},
    options:{
      responsive:true,maintainAspectRatio:false,
      interaction:{mode:'index',intersect:false},
      plugins:{
        legend:{display:true,labels:{color:'#94a3b8',font:{size:9},boxWidth:14,padding:6,usePointStyle:true,
          filter:item=>!item.text.startsWith('_')}},
        tooltip:{
          filter:item=>!item.dataset.label.startsWith('_'),
          callbacks:{
            label:c=>{ const v=c.parsed.y; if(v==null)return null;
              const lbl=isMonthly?allLabels[c.dataIndex]:Number(allLabels[c.dataIndex]);
              const isFut=isMonthly?(lbl>='2026-01'):(lbl>2025);
              return `${c.dataset.label}: ${v.toFixed(1)} kTM${isFut?' (proj.)':''}`;
            }
          }
        }
      },
      scales:{
        x:{ticks:{color:c=>{ const v=allLabels[c.index]; const isFut=isMonthly?(v>='2026-01'):(Number(v)>2025); return isFut?accentC:'#64748b'; },
            font:{size:8},maxRotation:isMonthly?45:0,
            maxTicksLimit:isMonthly?12:undefined},
           grid:{color:c=>{ const v=allLabels[c.index]; const isFut=isMonthly?(v>='2026-01'):(Number(v)>2025);
             return isFut?`${accentC}30`:'rgba(100,116,139,0.08)'; }}},
        y:{ticks:{color:'#64748b',font:{size:9}},grid:{color:'rgba(100,116,139,0.12)'},
           title:{display:true,text:isMonthly?'kTM/mes':'kTM/año',color:'#475569',font:{size:8}}}
      }
    }
  });
  cb(chart);
}

// ── MONTHLY PROJECTION CHART ──────────────────────────────────────────────────
function buildFcProjMonthly(d, mk){
  if(fcProjChartM){ fcProjChartM.destroy(); fcProjChartM=null; }
  const ctx = document.getElementById('fc-proj-chart-m');
  if(!ctx) return;
  _drawProjChart(ctx.getContext('2d'), d, 'monthly', v=>{ fcProjChartM=v; });
}

// ── MONTHLY VALIDATION CHART ──────────────────────────────────────────────────
function buildFcChartMonthly(d, mk){
  if(fcChartM){ fcChartM.destroy(); fcChartM=null; }
  const ctx = document.getElementById('fc-chart-m');
  if(!ctx) return;
  const s = d.series_m;
  if(!s || !s.dates || !s.dates.length){
    ctx.getContext('2d').clearRect(0,0,ctx.width,ctx.height); return;
  }
  const labels = s.dates.map(d=>d.slice(0,7));
  fcChartM = new Chart(ctx.getContext('2d'),{
    type:'line',
    data:{ labels, datasets:[
      {label:'Actual',data:s.actual,borderColor:'rgba(255,255,255,0.85)',
       borderWidth:1.5,fill:false,tension:.2,pointRadius:0,pointHoverRadius:4},
      {label:'Pred ML',data:s.pred,borderColor:'#a78bfa',borderWidth:1.5,
       fill:false,tension:.2,borderDash:[5,3],pointRadius:0,pointHoverRadius:4},
      {label:'Naïve',data:s.naive,borderColor:'rgba(100,116,139,0.4)',borderWidth:1,
       fill:false,tension:0,borderDash:[2,4],pointRadius:0},
    ]},
    options:{
      responsive:true,maintainAspectRatio:false,
      interaction:{mode:'index',intersect:false},
      plugins:{
        legend:{display:true,labels:{color:'#94a3b8',font:{size:9},boxWidth:12,padding:6,usePointStyle:true}},
        tooltip:{callbacks:{label:c=>{ const v=c.parsed.y; if(v==null)return null; return `${c.dataset.label}: ${v.toFixed(1)} kTM`; }}}
      },
      scales:{
        x:{ticks:{color:'#64748b',font:{size:8},maxRotation:45,maxTicksLimit:10},
           grid:{color:'rgba(100,116,139,0.08)'}},
        y:{ticks:{color:'#64748b',font:{size:9}},grid:{color:'rgba(100,116,139,0.12)'},
           title:{display:true,text:'kTM',color:'#475569',font:{size:8}}}
      }
    }
  });
}

// ── WR BY HORIZON CHART ───────────────────────────────────────────────────────
function buildFcWrByHorizon(d, mk){
  if(fcWrHChart){ fcWrHChart.destroy(); fcWrHChart=null; }
  const ctx = document.getElementById('fc-wr-h-chart');
  if(!ctx) return;
  const wh = d.wr_by_h || {};
  if(!(wh.horizons||[]).length){
    ctx.getContext('2d').clearRect(0,0,ctx.width,ctx.height); return;
  }
  const labels = wh.horizons.map(h=>h+'m');
  const wrs    = wh.wr.map(v=>+(v*100).toFixed(1));
  const colors = wrs.map(w=>w>=70?'rgba(34,197,94,0.75)':w>=50?'rgba(163,230,53,0.75)':w>=40?'rgba(245,158,11,0.75)':'rgba(239,68,68,0.75)');
  fcWrHChart = new Chart(ctx.getContext('2d'),{
    type:'bar',
    data:{ labels, datasets:[
      {label:'Win Rate',data:wrs,backgroundColor:colors,borderRadius:2,order:2},
      {label:'Naïve 50%',type:'line',data:wh.horizons.map(()=>50),
       borderColor:'rgba(239,68,68,0.5)',borderWidth:1.5,borderDash:[4,3],
       pointRadius:0,fill:false,order:1},
    ]},
    options:{
      responsive:true,maintainAspectRatio:false,
      plugins:{
        legend:{display:true,labels:{color:'#94a3b8',font:{size:9},boxWidth:12,padding:6,usePointStyle:true}},
        tooltip:{callbacks:{label:c=>{ if(c.datasetIndex===1)return 'Naïve: 50%';
          return `WR H+${wh.horizons[c.dataIndex]}m: ${c.parsed.y.toFixed(1)}%`; }}}
      },
      scales:{
        x:{ticks:{color:'#64748b',font:{size:8},maxRotation:0},grid:{color:'rgba(100,116,139,0.08)'}},
        y:{min:0,max:100,ticks:{color:'#64748b',font:{size:9},callback:v=>v+'%'},
           grid:{color:'rgba(100,116,139,0.12)'},
           title:{display:true,text:'Win Rate %',color:'#475569',font:{size:8}}}
      }
    }
  });
}

// ── FORECAST PANEL INIT ───────────────────────────────────────────────────────
function buildForecastPanel(cl){
  const tab = document.getElementById('fc-tab');
  const fc = cl.forecast || {};
  const mines = Object.keys(fc.mines || {});
  if(!mines.length){ tab.style.display='none'; return; }
  tab.style.display='flex';

  // Sort mines by effective WR descending (annual if available, else monthly)
  const sorted = mines.slice().sort((a,b)=>fcEffWr(fc.mines[b]) - fcEffWr(fc.mines[a]));

  // ── Mine chips — one clickable badge per mine ─────────────────────────────
  const chipsEl = document.getElementById('fc-mine-chips');
  if(chipsEl){
    chipsEl.innerHTML = '';
    sorted.forEach((mk, i) => {
      const d   = fc.mines[mk];
      const eff = fcEffWr(d);
      const gc  = fcGradeColor(eff);
      const g   = fcGrade(eff);
      const isMonOnly = d.wr == null;
      const chip = document.createElement('div');
      chip.dataset.mk = mk;
      chip.style.cssText = `cursor:pointer;padding:4px 9px;border-radius:20px;font-size:9px;
        font-weight:700;border:1.5px solid ${gc}60;color:${gc};background:${gc}12;
        transition:all .15s;white-space:nowrap`;
      const wrLabel = isMonOnly
        ? `M:${(d.wr_m*100).toFixed(0)}%`
        : `${(d.wr*100).toFixed(0)}%`;
      chip.innerHTML = `${fcMineName(mk)} <span style="opacity:.7">${g}${isMonOnly?' ≈':''}</span>`;
      chip.title = isMonOnly
        ? `Solo mensual — WR M: ${(d.wr_m!=null?(d.wr_m*100).toFixed(0)+'%':'—')}  |  ${d.nearest_city||''}`
        : `WR anual: ${(d.wr*100).toFixed(0)}%  |  ${d.nearest_city||''}`;
      chip.onclick = () => {
        document.getElementById('fc-mine-select').value = mk;
        // Highlight active chip
        chipsEl.querySelectorAll('div').forEach(c=>{
          const cd = fc.mines[c.dataset.mk];
          const cgc = fcGradeColor(fcEffWr(cd));
          c.style.background = `${cgc}12`;
          c.style.borderColor = `${cgc}60`;
        });
        chip.style.background = `${gc}35`;
        chip.style.borderColor = gc;
        onFcMineChange();
      };
      chipsEl.appendChild(chip);
      if(i===0){ chip.style.background=`${gc}35`; chip.style.borderColor=gc; }
    });
  }

  // Populate hidden selector (keeps JS value tracking working)
  const sel = document.getElementById('fc-mine-select');
  sel.innerHTML='';
  sorted.forEach(mk=>{
    const d = fc.mines[mk];
    const opt = document.createElement('option');
    opt.value = mk;
    const wrA = d.wr!=null?(d.wr*100).toFixed(0)+'%':'—';
    const wrM = d.wr_m!=null?(d.wr_m*100).toFixed(0)+'%':'—';
    opt.textContent = `${fcMineName(mk)}  —  A:${wrA} M:${wrM}  [${fcGrade(fcEffWr(d))}]`;
    sel.appendChild(opt);
  });

  // Build quality table
  const tbody = document.getElementById('fc-quality-tbody');
  tbody.innerHTML='';
  sorted.forEach(mk=>{
    const d = fc.mines[mk];
    const eff = fcEffWr(d);
    const g = fcGrade(eff);
    const gc = fcGradeColor(eff);
    const wrA = d.wr!=null?(d.wr*100).toFixed(0)+'%':'—';
    const wrM = d.wr_m!=null?(d.wr_m*100).toFixed(0)+'%':'—';
    const tr = document.createElement('tr');
    tr.style.cursor='pointer';
    tr.onclick=()=>{ sel.value=mk; onFcMineChange(); };
    tr.innerHTML=`
      <td style="font-weight:600;color:var(--text);white-space:nowrap">${fcMineName(mk)}</td>
      <td style="text-align:right;color:${d.wr!=null?gc:'#64748b'};font-weight:700">${wrA}</td>
      <td style="text-align:right;color:${d.wr_m!=null?fcGradeColor(d.wr_m):'#94a3b8'}">${wrM}</td>
      <td style="text-align:center">
        <span style="font-size:9px;font-weight:700;padding:1px 5px;border-radius:8px;
                     background:${gc}20;color:${gc};border:1px solid ${gc}50">${g}</span>
      </td>`;
    tbody.appendChild(tr);
  });

  // Build best model section
  const d0 = fc.mines[sorted[0]];
  buildFcBestChart(d0, sorted[0]);
  buildFcCompare(d0);

  // Rebuild open sections
  if(fcSections.ann){ buildFcProjectionChart(d0,sorted[0]); buildFcChart(d0,sorted[0]); buildFcAnnMetrics(d0); }
  if(fcSections.tbl){ buildFcWrChart(fc); }
}

function onFcMineChange(){
  const cl = currentClusterData;
  if(!cl) return;
  const mk = document.getElementById('fc-mine-select').value;
  const d  = (cl.forecast||{}).mines?.[mk];
  if(!d) return;

  // Sync chip highlight
  const chipsEl = document.getElementById('fc-mine-chips');
  if(chipsEl) chipsEl.querySelectorAll('div[data-mk]').forEach(c=>{
    const cmd = c.dataset.mk;
    const gc  = fcGradeColor((cl.forecast.mines[cmd]||{}).wr||0);
    c.style.background   = cmd===mk ? `${gc}35` : `${gc}12`;
    c.style.borderColor  = cmd===mk ? gc : `${gc}60`;
  });

  // Nearest city tag above the chart
  const cityEl = document.getElementById('fc-mine-city');
  if(cityEl){
    if(d.nearest_city){
      cityEl.style.display = 'block';
      cityEl.innerHTML = `📍 Ciudad más cercana: <strong>${d.nearest_city}</strong>`
        + (d.nearest_city_km != null ? ` <span style="color:var(--text3)">(${d.nearest_city_km} km)</span>` : '');
    } else {
      cityEl.style.display = 'none';
    }
  }

  buildFcBestChart(d, mk);
  buildFcCompare(d);
  if(fcSections.ann){ buildFcProjectionChart(d,mk); buildFcChart(d,mk); buildFcAnnMetrics(d); }
}

function updateFcGradeBadge(d){
  // kept for backward compat — no longer used but safe to keep
}

function buildFcChart(d, mk){
  if(fcChart){ fcChart.destroy(); fcChart=null; }
  const ctx = document.getElementById('fc-chart').getContext('2d');
  const s = d.series;
  if(!s || !s.years.length){ ctx.clearRect(0,0,ctx.canvas.width,ctx.canvas.height); return; }

  fcChart = new Chart(ctx,{
    type:'line',
    data:{
      labels: s.years,
      datasets:[
        {
          label:'Actual',
          data: s.actual,
          borderColor:'rgba(255,255,255,0.85)',
          backgroundColor:'rgba(255,255,255,0.04)',
          borderWidth:2, fill:false, tension:0.25, order:1,
          pointRadius:4, pointHoverRadius:6,
          pointBackgroundColor:'rgba(255,255,255,0.8)',
        },
        {
          label:'Ens_Segmentado',
          data: s.pred,
          borderColor:'#f59e0b',
          borderWidth:2, fill:false, tension:0.25, order:2,
          borderDash:[6,3],
          pointRadius:3, pointHoverRadius:5,
          pointBackgroundColor:'#f59e0b',
        },
        {
          label:'SARIMAX',
          data: s.sarimax,
          borderColor:'#38bdf8',
          borderWidth:1.5, fill:false, tension:0.25, order:3,
          borderDash:[3,4],
          pointRadius:2, pointHoverRadius:4,
          pointBackgroundColor:'#38bdf8',
        },
        {
          label:'Naïve',
          data: s.naive,
          borderColor:'rgba(100,116,139,0.55)',
          borderWidth:1, fill:false, tension:0, order:4,
          borderDash:[2,5],
          pointRadius:0,
        },
      ]
    },
    options:{
      responsive:true, maintainAspectRatio:false,
      interaction:{mode:'index', intersect:false},
      plugins:{
        legend:{
          display:true,
          labels:{color:'#94a3b8', font:{size:9}, boxWidth:14, padding:8, usePointStyle:true}
        },
        tooltip:{
          callbacks:{
            label:c=>{
              const v=c.parsed.y;
              if(v==null) return null;
              return `${c.dataset.label}: ${v.toFixed(1)} kTM`;
            }
          }
        }
      },
      scales:{
        x:{ticks:{color:'#64748b',font:{size:9},maxRotation:0}, grid:{color:'rgba(100,116,139,0.1)'}},
        y:{ticks:{color:'#64748b',font:{size:9}}, grid:{color:'rgba(100,116,139,0.12)'},
           title:{display:true,text:'kTM',color:'#475569',font:{size:8}}}
      }
    }
  });
}

function buildFcWrChart(fc){
  if(fcWrChart){ fcWrChart.destroy(); fcWrChart=null; }
  const ctx = document.getElementById('fc-wr-chart').getContext('2d');
  const mines = Object.keys(fc.mines).sort((a,b)=>fcEffWr(fc.mines[b]) - fcEffWr(fc.mines[a]));
  const wrs   = mines.map(m=>(fcEffWr(fc.mines[m])*100));
  const colors= wrs.map(wr=>wr>=70?'rgba(34,197,94,0.75)':wr>=50?'rgba(163,230,53,0.75)':wr>=40?'rgba(245,158,11,0.75)':'rgba(239,68,68,0.75)');
  const labels= mines.map(m=>{
    const n=fcMineName(m);
    return n.length>13 ? n.slice(0,12)+'…' : n;
  });

  fcWrChart = new Chart(ctx,{
    type:'bar',
    data:{
      labels,
      datasets:[
        {
          label:'Win Rate %',
          data:wrs,
          backgroundColor:colors,
          borderRadius:3,
          order:2,
        },
        {
          label:'Naïve (50%)',
          type:'line',
          data:mines.map(()=>50),
          borderColor:'rgba(239,68,68,0.5)',
          borderWidth:1.5,
          borderDash:[5,4],
          pointRadius:0,
          fill:false,
          order:1,
        }
      ]
    },
    options:{
      responsive:true, maintainAspectRatio:false,
      plugins:{
        legend:{display:true, labels:{color:'#94a3b8',font:{size:9},boxWidth:12,padding:6,usePointStyle:true}},
        tooltip:{
          callbacks:{
            label:c=>{
              if(c.datasetIndex===1) return 'Naïve: 50%';
              const mk=mines[c.dataIndex];
              const d=fc.mines[mk];
              const lines=[`WR: ${c.parsed.y.toFixed(1)}%  [${fcGrade(fcEffWr(d))}]`];
              const maseV=d.mase!=null?d.mase:d.mase_m;
              const skillV=d.skill!=null?d.skill:d.skill_m;
              if(maseV!=null||skillV!=null)
                lines.push(`MASE: ${maseV!=null?maseV.toFixed(3):'—'}  Skill: ${skillV!=null?(skillV>=0?'+':'')+skillV.toFixed(1)+'%':'—'}`);
              if(d.wr_m!=null) lines.push(`WR mensual: ${(d.wr_m*100).toFixed(0)}%`);
              return lines;
            }
          }
        }
      },
      scales:{
        x:{ticks:{color:'#64748b',font:{size:8},maxRotation:35}, grid:{color:'rgba(100,116,139,0.08)'}},
        y:{min:0,max:100,
           ticks:{color:'#64748b',font:{size:9},callback:v=>v+'%'},
           grid:{color:'rgba(100,116,139,0.12)'},
           title:{display:true,text:'Win Rate %',color:'#475569',font:{size:8}}}
      }
    }
  });
}

// ── RISK PANEL ──────────────────────────────────────────────────────────────
function buildRiskPanel(cl){
  const roster = cl.mine_roster || [];
  const risks  = roster.map(m=>m.risk).filter(r=>r&&Object.keys(r).length>0);
  if(!risks.length){
    document.getElementById('risk-kpi-row').innerHTML='<span style="font-size:10px;color:var(--text3)">Sin datos de riesgo</span>';
    document.getElementById('risk-mine-panel').innerHTML=''; return;
  }

  // Cluster-level aggregates
  const totalDanger    = risks.reduce((s,r)=>s+(r.total_danger||0),0);
  const totalAbandoned = risks.reduce((s,r)=>s+(r.relaves_danger?.ABANDONADO||0),0);
  const minesNearAP    = risks.filter(r=>r.ap_flag).length;
  const totalWater     = risks.reduce((s,r)=>s+(r.water_demand_m3||0),0);
  const waterDesal     = risks.reduce((s,r)=>s+(r.water_demand_m3||0)*(r.desal_pct||0)/100,0);
  const desal_pct_cl   = totalWater>0 ? Math.min(waterDesal/totalWater*100,999) : 0;

  const relC = totalDanger>5?'#ef4444':totalDanger>0?'#f59e0b':'#22c55e';
  const apC  = minesNearAP>0?'#f59e0b':'#22c55e';
  const wC   = desal_pct_cl<20?'#ef4444':desal_pct_cl<50?'#f59e0b':'#22c55e';

  document.getElementById('risk-kpi-row').innerHTML=`
    <div class="kpi"><div class="kpi-val" style="color:${relC}">${totalDanger}</div>
      <div class="kpi-lbl">Relaves &lt;25km</div></div>
    <div class="kpi"><div class="kpi-val" style="color:${apC}">${minesNearAP}</div>
      <div class="kpi-lbl">Minas ↔ Área Prot.</div></div>
    <div class="kpi"><div class="kpi-val" style="color:${wC}">${desal_pct_cl.toFixed(0)}%</div>
      <div class="kpi-lbl">Cobertura Desal.</div></div>`;

  // Per-mine risk cards
  let mineHtml = '';
  roster.forEach(mine=>{
    const r = mine.risk;
    if(!r||!Object.keys(r).length) return;
    const hasHiRisk = r.total_danger>0 || r.ap_flag;
    const hasMdRisk = r.total_alert>0;
    const rowCls = hasHiRisk?'danger':hasMdRisk?'alert':'ok';
    const relBadge = r.total_danger>0
      ? `<span class="risk-badge risk-hi">⚠ ${r.total_danger} relave${r.total_danger>1?'s':''} &lt;25km</span>`
      : r.total_alert>0
        ? `<span class="risk-badge risk-md">${r.total_alert} relaves &lt;60km</span>`
        : `<span class="risk-badge risk-lo">✓ Sin relaves cerca</span>`;
    const apBadge = r.ap_km!=null
      ? (r.ap_flag
        ? `<span class="risk-badge risk-md" title="${r.ap_nombre}">🌿 ${r.ap_km}km (${(r.ap_desig||'').slice(0,12)})</span>`
        : `<span class="risk-badge risk-lo">🌿 ${r.ap_km}km</span>`)
      : '';
    const desBadge = r.desal_pct!=null
      ? `<span class="risk-badge ${r.desal_pct<20?'risk-hi':r.desal_pct<60?'risk-md':'risk-lo'}">💧 ${r.desal_pct.toFixed(0)}% desal</span>`
      : '';
    const elecBadge = r.grid_pct!=null && r.grid_pct>0
      ? `<span class="risk-badge ${r.grid_pct<50?'risk-md':'risk-lo'}">⚡ ${r.grid_pct.toFixed(0)}% red</span>`
      : '';
    const portBadge = r.port_km!=null
      ? `<span class="risk-badge risk-na">⚓ ${r.port_km}km ${r.port_name||''}</span>`
      : '';
    const waterFmt = r.water_demand_m3>=1e6
      ? (r.water_demand_m3/1e6).toFixed(2)+' Mm³/a'
      : r.water_demand_m3>=1e3
        ? (r.water_demand_m3/1e3).toFixed(0)+' km³×10⁻³/a'
        : (r.water_demand_m3||0)+' m³/a';
    const elecFmt = r.elec_demand_mwh>=1e6
      ? (r.elec_demand_mwh/1e6).toFixed(2)+' TWh/a'
      : (r.elec_demand_mwh/1e3).toFixed(0)+' GWh/a';

    // Relaves detail breakdown
    const relDetail = Object.entries(r.relaves_danger||{}).filter(([,v])=>v>0)
      .map(([k,v])=>`<span style="color:${k==='ACTIVO'?'#22c55e':k==='ABANDONADO'?'#ef4444':'#f59e0b'}">${k}: ${v}</span>`)
      .join(' · ');
    const relDetailAlert = Object.entries(r.relaves_alert||{}).filter(([,v])=>v>0)
      .map(([k,v])=>`<span style="color:${k==='ACTIVO'?'#22c55e':k==='ABANDONADO'?'#ef4444':'#f59e0b'}">${k}: ${v}</span>`)
      .join(' · ');

    mineHtml += `<div class="mine-risk-row ${rowCls}">
      <div style="font-size:11px;font-weight:700;color:var(--text);margin-bottom:4px">${mine.name}</div>
      <div style="display:flex;flex-wrap:wrap;gap:3px;margin-bottom:4px">
        ${relBadge}${apBadge}${desBadge}${elecBadge}${portBadge}
      </div>
      <div class="mine-risk-grid">
        <span>💧 Demanda agua: <b>${waterFmt}</b></span>
        <span>💧 Tipo: ${r.mine_type||'—'} (${r.water_factor||'—'} m³/t)</span>
        <span>⚡ Demanda elec: <b>${elecFmt}</b></span>
        ${r.ap_nombre?`<span title="${r.ap_nombre}">🌿 ${(r.ap_nombre||'').slice(0,35)}</span>`:''}
        ${relDetail?`<span style="grid-column:1/-1">↯ Peligro &lt;25km: ${relDetail}</span>`:''}
        ${relDetailAlert?`<span style="grid-column:1/-1">△ Alerta &lt;60km: ${relDetailAlert}</span>`:''}
      </div>
    </div>`;
  });
  const relavesPeligro = (cl.relaves||[]).filter(r=>r.ciudad_risk==='PELIGRO').length;
  const relavesAlerta  = (cl.relaves||[]).filter(r=>r.ciudad_risk==='ALERTA').length;
  const topCiudadRisk  = cl.relaves_ciudad_top || null;
  let pobHtml = '';
  if(relavesPeligro > 0 || relavesAlerta > 0){
    const topStr = topCiudadRisk
      ? `<div style="font-size:10px;margin-top:4px;padding:4px 7px;background:rgba(239,68,68,0.1);border-radius:5px;border-left:3px solid #ef4444">
           ⚠ Caso crítico: <b>${topCiudadRisk.instalacion}</b> · ${topCiudadRisk.km}km de <b>${topCiudadRisk.ciudad}</b> (${(topCiudadRisk.pop||0).toLocaleString('es-CL')} hab.)
         </div>` : '';
    pobHtml = `<div style="margin-bottom:8px;padding:7px 9px;background:rgba(239,68,68,0.07);border-radius:7px;border:1px solid rgba(239,68,68,0.25)">
      <div style="font-size:10px;font-weight:700;color:#f87171;margin-bottom:4px">🏘️ Riesgo Poblacional — Relaves</div>
      <div style="display:flex;gap:10px;font-size:10px">
        <span><b style="color:#ef4444">${relavesPeligro}</b> PELIGRO (&lt;10km)</span>
        <span><b style="color:#f97316">${relavesAlerta}</b> ALERTA (&lt;30km)</span>
      </div>${topStr}
    </div>`;
  }
  document.getElementById('risk-mine-panel').innerHTML = pobHtml + (mineHtml ||
    '<span style="font-size:10px;color:var(--text3)">Sin minas con coordenadas</span>');
}

// ── NATIONAL TOTAL ───────────────────────────────────────────────────────────
function updateNationalTotal(){
  const all = Object.values(RAW.clusters).filter(cl=>cl.id!=='Ruido');
  const yr  = String(currentYear);
  const total  = all.reduce((s,cl)=>s+(cl.production[yr]||0), 0);
  const prevYr = String(currentYear-1);
  const prev   = all.reduce((s,cl)=>s+(cl.production[prevYr]||0), 0);
  const chg    = prev > 0 ? ((total-prev)/prev*100) : null;
  const chgHtml = chg !== null
    ? `<span style="color:${chg>=5?'#22c55e':chg<=-5?'#ef4444':'#94a3b8'}">${chg>=0?'▲':'▼'}${Math.abs(chg).toFixed(1)}%</span>`
    : '';
  const active = all.filter(cl=>cl.production[yr]>0).length;
  document.getElementById('nat-total').innerHTML =
    `<span>Total Chile: <b>${total.toFixed(0)} kTM</b> ${chgHtml}</span>` +
    `<span style="color:var(--text3)">${active}/${all.length} clústeres activos</span>`;
}

// ── YEAR SLIDER ───────────────────────────────────────────────────────────────
const sl=document.getElementById('year-slider');
sl.min=RAW.config.min_year; sl.max=RAW.config.max_year; sl.value=RAW.config.default_year;
sl.addEventListener('input',function(){
  currentYear=+this.value;
  document.getElementById('year-val').textContent=currentYear;
  buildClusterList();
  updateNationalTotal();

  if(selectedCluster) {
    fillClusterDetail(selectedCluster);
    refreshAllInlineDetails();
  }
});

// ── SEARCH ────────────────────────────────────────────────────────────────────
function onSearch(val){ if(!selectedCluster) buildClusterList(val); }

// ── ZOOM ────────────────────────────────────────────────────────────────────
map.on('zoomend',()=>{
  const z=map.getZoom();
  if(z>=RAW.config.zoom_threshold){
    if(selectedCluster) showFaenas(selectedCluster);
    else { lgs.faenas.clearLayers(); buildFaenaMarkers(); }
  } else if(!selectedCluster){
    lgs.faenas.clearLayers();
  }
});

// ── INIT ────────────────────────────────────────────────────────────────────
buildTrainLayer();
initClusterPolygons();
buildInfraLayers();
buildClusterList();
updateNationalTotal();
// ESC to deselect cluster
document.addEventListener('keydown', e => { if(e.key==='Escape' && selectedCluster) deselectCluster(); });
// Faenas shown at zoom >= threshold via the zoomend handler
// (map starts at zoom 5, so they start hidden)
map.fire('zoomend');

// SIGEX legend — one pill per exploration stage
if(RAW.seia.length>0){
  const etapaCounts={};
  RAW.seia.forEach(s=>{ etapaCounts[s.etapa]=(etapaCounts[s.etapa]||0)+1; });
  const pills=Object.entries(RAW.sigex_meta).map(([k,v])=>{
    const n=etapaCounts[k]||0;
    return `<span title="${v.label}" style="white-space:nowrap">
      <span class="sl-dot" style="background:${v.color}"></span>${v.icon} <b>${n}</b></span>`;
  }).join('');
  const leg=document.createElement('div');
  leg.className='seia-legend';
  leg.innerHTML=`<span style="color:var(--accent);font-weight:700;flex-shrink:0">SIGEX&nbsp;${RAW.seia.length}</span>${pills}`;
  document.getElementById('s-body').prepend(leg);
}

console.log('⛏️  Dashboard v2 loaded —',
  Object.keys(RAW.clusters).length,'clusters |',RAW.faenas.length,'faenas |',
  RAW.train_lines.length,'train lines |',RAW.seia.length,'SIGEX projects |',
  (RAW.puertos||[]).length,'puertos');

// ── PILAR PANEL ───────────────────────────────────────────────────────────────
const PILAR_META = {
  TM:{color:'#059669', label:'Trayectoria', key:'trajectory', desc:'TM = Σ(wᵢ·δᵢ)/Σwᵢ  wᵢ=P̂2026ᵢ/dᵢ²  δᵢ=P̂2032/P̂2026−1 [corregido]'},
  LP:{color:'#7c3aed', label:'Potencial',   key:'potential',  desc:'LP = (0.5·KDEₙ + 0.5·Prospₙ) / (1 + 0.5·Prodₙ)'},
  FM:{color:'#dc2626', label:'Fricción',    key:'friction',   desc:'FM = 0.5·Relaves + 0.3·Áreas_Prot + 0.2·SEIA_Rechaz  [1/d²]'},
  RE:{color:'#2563eb', label:'Recursos',    key:'resources',  desc:'RE = 0.3·Agua + 0.2·Energía + 0.2·Puertos + 0.3·CadenaValor'},
  DH:{color:'#0891b2', label:'Densidad',    key:'density',    desc:'DH = Σ pop^0.3 / max(dᵢ,5km)²  [gravedad mercado laboral]'},
};
const activePilars = new Set();
const pilarMarkers = {};   // cid → {TM:marker, LP:marker, ...}
const pilarLayer   = L.featureGroup().addTo(map);

// Pre-compute ranks for each pillar across all clusters
const PILAR_RANKS = {};
Object.keys(PILAR_META).forEach(pid=>{
  const key = PILAR_META[pid].key;
  const sorted = Object.keys(OPT.clusters)
    .filter(cid=>OPT.clusters[cid].pillar_scores?.[key]!=null)
    .sort((a,b)=>{
      const va = OPT.clusters[a].pillar_scores[key];
      const vb = OPT.clusters[b].pillar_scores[key];
      return vb-va;  // all pillars: higher=better (FM: more friction = rank #1)
    });
  PILAR_RANKS[pid]={};
  sorted.forEach((cid,i)=>{ PILAR_RANKS[pid][cid]=i+1; });
});

// Normalise pillar scores cross-cluster
const PILAR_NORMS = {};
Object.keys(PILAR_META).forEach(pid=>{
  const key = PILAR_META[pid].key;
  const vals = Object.values(OPT.clusters).map(cl=>cl.pillar_scores?.[key]||0);
  const mn=Math.min(...vals), mx=Math.max(...vals);
  PILAR_NORMS[pid]={mn,mx};
});
function normPilar(pid,raw){
  const {mn,mx}=PILAR_NORMS[pid];
  if(mx===mn) return 0.5;
  return Math.max(0,Math.min(1,(raw-mn)/(mx-mn)));
}

function togglePilarPanel(){
  const panel=document.getElementById('pilar-panel');
  panel.classList.toggle('open');
  const btn = document.getElementById('btn-opt');
  if(btn) btn.classList.toggle('active', panel.classList.contains('open'));
  // If panel is closed, reset layout
  if(!panel.classList.contains('open')) {
    panel.classList.remove('expanded');
    document.querySelectorAll('.pilar-inline-detail').forEach(el=>el.style.display='none');
  }
}

function togglePilar(pid){
  const chk=document.getElementById('chk-'+pid);
  const detail=document.getElementById('pilar-detail-'+pid);
  const panel=document.getElementById('pilar-panel');
  
  const pilarMapLayers = {
    'DA': ['des'],
    'IE': ['sub', 'cen', 'pue', 'train'],
    'RM': ['rel', 'ap'],
    'TE': ['fibra', 'senal'],
    'FM': ['pob', 'seia']
  };

  if(activePilars.has(pid)){
    activePilars.delete(pid);
    if(chk) chk.checked=false;
    if(detail) detail.style.display='none';
    // Turn off related layers
    (pilarMapLayers[pid]||[]).forEach(l => { if(flags[l]) toggleLayer(l); });

    if(activePilars.size===0){ 
      panel.classList.remove('expanded');
      rebuildPilarMarkers(); 
      return; 
    }
  } else {
    activePilars.add(pid);
    if(chk) chk.checked=true;
    if(detail) detail.style.display='block';
    panel.classList.add('expanded');
    // Turn on related layers
    (pilarMapLayers[pid]||[]).forEach(l => { if(!flags[l]) toggleLayer(l); });
  }
  rebuildPilarMarkers();
  
  // Find which pillar to use as reference for top ranking
  const activePid = activePilars.has(pid) ? pid : Array.from(activePilars)[activePilars.size - 1];
  
  // Find target cluster: selected one, or top-ranked for the active pillar
  const target = (selectedCluster && OPT.clusters[selectedCluster])
    ? selectedCluster
    : Object.keys(PILAR_RANKS[activePid]||{}).sort((a,b)=>(PILAR_RANKS[activePid][a]||99)-(PILAR_RANKS[activePid][b]||99))[0];
  
  if(target) {
    try { renderPilarInline(activePid, target); } catch(e) { console.error('Inline render error:', e); }
    if(!selectedCluster) {
      try { selectCluster(target); } catch(e) { console.error('selectCluster error:', e); }
    }
  }
}

function rebuildPilarMarkers(){
  pilarLayer.clearLayers();
  Object.keys(pilarMarkers).forEach(cid=>{ delete pilarMarkers[cid]; });
  if(activePilars.size===0) return;
  const n=Object.keys(OPT.clusters).length;
  activePilars.forEach(pid=>{
    let placed=0;
    Object.entries(OPT.clusters).forEach(([cid,cl])=>{
      const m=cl.models?.[pid];
      if(!m?.data?.lat){
        console.warn(`Pilar ${pid}: cluster ${cid} sin coordenadas — marker omitido`);
        return;
      }
      if(!pilarMarkers[cid]) pilarMarkers[cid]={};
      const meta=PILAR_META[pid];
      const d=m.data;
      const rawScore=cl.pillar_scores?.[meta.key]||0;
      const norm=normPilar(pid,rawScore);
      const r=norm;
      const sz=Math.round(7+r*8);
      const rank=PILAR_RANKS[pid]?.[cid]||n;
      const icon=L.divIcon({
        html:`<div style="width:${sz*2}px;height:${sz*2}px;border-radius:50%;
          background:${meta.color};opacity:0.88;border:2px solid white;
          box-shadow:0 0 8px ${meta.color}99;display:flex;align-items:center;justify-content:center;
          font-size:${sz>9?9:7}px;font-weight:700;color:white">${rank<=5?rank:''}</div>`,
        className:'',iconAnchor:[sz,sz]});
      const mk=L.marker([d.lat,d.lon],{icon,zIndexOffset:700+Object.keys(PILAR_META).indexOf(pid)*10});
      mk.on('click',(e)=>{L.DomEvent.stopPropagation(e);showPilarScorecard(cid);});
      mk.on('mouseover',(e)=>{
        const pct=Math.round(norm*100);
        showTip(e,`<b style="color:${meta.color}">${pid} · ${meta.label}</b><br>${cl.label||cid}<br>Rank #${rank}/${n} &nbsp; ${pct}%`);
      });
      mk.on('mouseout',()=>hideTip());
      pilarLayer.addLayer(mk);
      pilarMarkers[cid][pid]=mk;
      placed++;
    });
    if(placed===0) console.warn(`Pilar ${pid}: ningún cluster tiene coordenadas de modelo`);
  });
}

// Semantic rationale per pillar + driver type
function _driveWhy(pid, info, name){
  const i=(info||'').toLowerCase(), n=(name||'').toLowerCase();
  if(pid==='TM'){
    return info.includes('+')?'eleva trayectoria zonal':'deprime trayectoria zonal';
  }
  if(pid==='FM'){
    if(i.includes('activo'))  return 'relave activo → ↑ fricción';
    if(i.includes('rechaz'))  return 'rechazo SEIA → ↑ riesgo regulatorio';
    if(i.includes('eliminad')||i.includes('abandon')) return 'relave inactivo → fricción baja';
    return 'presión ambiental acumulada';
  }
  if(pid==='LP'){
    if(i.includes('explor')) return 'exploración → potencial no desarrollado';
    if(i.includes('aprobad')) return 'SEIA aprobado → inversión futura activa';
    if(i.includes('pipeline')) return 'proyecto en cartera → presión brownfield';
    return 'señal de actividad prospectiva';
  }
  if(pid==='RE'){
    if(i.includes('fundici')||i.includes('refiner')||n.includes('fundici')||n.includes('refiner')) return 'cadena de valor integrada';
    if(i.includes('kv')||i.includes('s/e')||i.includes('subestac')||n.includes('subestac')) return 'nodo energético disponible';
    if(i.includes('desalad')||i.includes('l/s')||n.includes('desalad')||n.includes('planta')) return 'seguridad hídrica cubierta';
    if(i.includes('puerto')||n.includes('puerto')) return 'logística de exportación próxima';
    return 'infraestructura de soporte';
  }
  if(pid==='DH'){
    return 'concentración de fuerza laboral';
  }
  return '';
}

function renderPilarInline(pid, cid) {
  const detail=document.getElementById('pilar-detail-'+pid);
  if(!detail) return;
  
  const cl=OPT.clusters[cid]; 
  if(!cl) {
    detail.innerHTML=`<div class="sc-no-markers">Sin datos para clúster actual</div>`;
    return;
  }
  const rawCl=RAW.clusters[cid]||{};
  const cName = cl.label||rawCl.label||cid;
  const n=Object.keys(OPT.clusters).length;
  const meta = PILAR_META[pid];
  const key=meta.key;
  
  const rawScore=cl.pillar_scores?.[key]??0;
  const norm=normPilar(pid,rawScore);
  const pct=Math.round(norm*100);
  const rank=PILAR_RANKS[pid]?.[cid]||n;
  const rankMedal=rank===1?'🥇 ':rank===2?'🥈 ':rank===3?'🥉 ':'';
  const rankLabel=`${rankMedal}#${rank}/${n}`;
  const {mn,mx}=PILAR_NORMS[pid];
  const fmtNum=v=>typeof v==='number'?(Math.abs(v)<0.01&&v!==0?v.toExponential(2):v.toFixed(3)):'-';

  const formula=cl.models?.[pid]?.formula||meta.desc;

  const statsHtml=`<div class="pid-title">${cName}</div>
    <div class="pid-sub">Ranking en ${pid}: ${rankLabel}</div>
    <table class="sc-stats-tbl">
    <tr><th>Métrica</th><th>Valor</th></tr>
    <tr><td>Score bruto</td><td>${fmtNum(rawScore)}</td></tr>
    <tr><td>Mín. (clústeres)</td><td>${fmtNum(mn)}</td></tr>
    <tr><td>Máx. (clústeres)</td><td>${fmtNum(mx)}</td></tr>
    <tr><td>Normalizado</td><td>${pct}%</td></tr>
  </table>`;

  let explain='';
  if(pid==='TM'){
    if(pct>=70) explain='Producción zonal crece fuerte → atractiva para inversión.';
    else if(pct>=40) explain='Trayectoria estable, sin señales claras de expansión.';
    else explain='Declive productivo regional → riesgo de desinversión.';
  } else if(pid==='LP'){
    if(pct>=70) explain='Alta exploración y cartera SEIA → potencial no explotado.';
    else if(pct>=40) explain='Potencial moderado: algunos proyectos activos.';
    else explain='Zona madura con poca exploración nueva.';
  } else if(pid==='FM'){
    if(pct>=70) explain='Alta fricción ambiental: relaves activos, rechazos SEIA → riesgo regulatorio elevado.';
    else if(pct>=40) explain='Fricción moderada: pasivos ambientales presentes.';
    else explain='Baja fricción ambiental → menor resistencia regulatoria.';
  } else if(pid==='RE'){
    if(pct>=70) explain='Infraestructura abundante (agua, energía, puertos).';
    else if(pct>=40) explain='Recursos parciales: alguna infraestructura disponible.';
    else explain='Déficit de infraestructura → costos logísticos altos.';
  } else if(pid==='DH'){
    if(pct>=70) explain='Alta concentración laboral → fácil acceso a personal.';
    else if(pct>=40) explain='Densidad laboral moderada en la zona.';
    else explain='Baja densidad humana → difícil reclutar localmente.';
  }

  const drivers=(cl.models?.[pid]?.data?.drivers)||[];
  let driverHtml='';
  if(drivers.length>0){
    const seen=new Set();
    const tags=drivers.slice(0,4).map(dr=>{
      const info=(dr.info||'');
      const nm=dr.name||'';
      const key2=nm.slice(0,18)+info.slice(0,10);
      if(seen.has(key2)) return '';
      seen.add(key2);
      const why=_driveWhy(pid,info,nm);
      let cls='neutral', arrow='';
      if(pid==='TM'){
        cls=info.includes('+')?'grow':'decline';
        arrow=info.includes('+')?'▲ ':'▼ ';
      } else if(pid==='FM'){
        cls=(info.toLowerCase().includes('activo')||info.toLowerCase().includes('rechaz'))?'decline':'neutral';
      } else if(pid==='LP' || pid==='RE' || pid==='DH'){
        cls='grow';
        arrow='▲ ';
      }
      const shortName=nm.length>20?nm.slice(0,20)+'…':nm;
      return `<div class="sc-driver ${cls}">
        <span class="sc-driver-name">${arrow}${shortName}${info?' · '+info:''}</span>
        ${why?`<span class="sc-driver-why">→ ${why}</span>`:''}
      </div>`;
    }).filter(Boolean).join('');
    if(tags) driverHtml=`<div class="sc-drivers">${tags}</div>`;
  } else if(!cl.models?.[pid]?.data?.lat){
    driverHtml=`<div class="sc-no-markers">Sin datos de modelo para este clúster</div>`;
  }

  // Top 3 Leaderboard
  const topList = Object.entries(PILAR_RANKS[pid]||{})
    .sort((a,b)=>a[1]-b[1])
    .slice(0,3)
    .map(entry => {
       const cidTop = entry[0];
       const rankTop = entry[1];
       const clTop = OPT.clusters[cidTop]||RAW.clusters[cidTop]||{};
       const nameTop = clTop.label||cidTop;
       const rawScoreTop = OPT.clusters[cidTop]?.pillar_scores?.[key]??0;
       const normTop = normPilar(pid, rawScoreTop);
       const pctTop = Math.round(normTop*100);
       const isCurrent = (cidTop === cid) ? 'font-weight:700;color:#0f172a;' : '';
       return `<div style="${isCurrent}">${rankTop}. ${nameTop} <span style="float:right;color:${meta.color};font-weight:700">${pctTop}%</span></div>`;
    }).join('');

  const top3Html = topList ? `<div style="margin-top:8px;padding-top:6px;border-top:1px solid #e2e8f0">
    <div style="font-size:10px;color:#64748b;margin-bottom:4px;font-weight:700">🏆 TOP 3 NACIONAL</div>
    <div style="font-size:10px;color:#334155;line-height:1.5">${topList}</div>
  </div>` : '';

  // TM insight box (only for TM)
  let tmInsight = '';
  if(pid==='TM') {
    const growN=cl.cts_n_growing||0, decN=cl.cts_n_declining||0;
    const ctsLbl=cl.cts_label||'';
    if(growN>0||decN>0||ctsLbl){
      tmInsight = `<div class="sc-tm-insight" style="display:block">
        <b>Trayectoria 2026–32:</b> ${ctsLbl}<br>
        <span style="color:#22c55e;font-weight:600">▲ ${growN} mina${growN!==1?'s':''} en crecimiento</span>
        &nbsp; <span style="color:#f87171;font-weight:600">▼ ${decN} en declive</span>
      </div>`;
    }
  }

  detail.style.borderLeftColor = meta.color;
  detail.innerHTML = `
    ${statsHtml}
    <div class="sc-formula">${formula}</div>
    ${explain?`<div class="sc-explain">💡 ${explain}</div>`:''}
    ${driverHtml}
    ${top3Html}
    ${tmInsight}
  `;
}

function refreshAllInlineDetails() {
  if (!selectedCluster) return;
  activePilars.forEach(pid => {
    try { renderPilarInline(pid, selectedCluster); } catch(e) {}
  });
}

// Close scorecard when clicking map background
map.on('click',()=>closePilarScorecard());
</script>
<div id="pilar-panel">
  <h4>Pilares de Optimización</h4>
  <div class="pilar-row" onclick="togglePilar('TM')">
    <input type="checkbox" id="chk-TM"><div class="pilar-dot" style="background:#059669"></div>
    <span class="pilar-label"><b>TM</b> · Trayectoria</span>
  </div>
  <div id="pilar-detail-TM" class="pilar-inline-detail" style="display:none;"></div>

  <div class="pilar-row" onclick="togglePilar('LP')">
    <input type="checkbox" id="chk-LP"><div class="pilar-dot" style="background:#7c3aed"></div>
    <span class="pilar-label"><b>LP</b> · Potencial</span>
  </div>
  <div id="pilar-detail-LP" class="pilar-inline-detail" style="display:none;"></div>

  <div class="pilar-row" onclick="togglePilar('FM')">
    <input type="checkbox" id="chk-FM"><div class="pilar-dot" style="background:#dc2626"></div>
    <span class="pilar-label"><b>FM</b> · Fricción</span>
  </div>
  <div id="pilar-detail-FM" class="pilar-inline-detail" style="display:none;"></div>

  <div class="pilar-row" onclick="togglePilar('RE')">
    <input type="checkbox" id="chk-RE"><div class="pilar-dot" style="background:#2563eb"></div>
    <span class="pilar-label"><b>RE</b> · Recursos</span>
  </div>
  <div id="pilar-detail-RE" class="pilar-inline-detail" style="display:none;"></div>

  <div class="pilar-row" onclick="togglePilar('DH')">
    <input type="checkbox" id="chk-DH"><div class="pilar-dot" style="background:#0891b2"></div>
    <span class="pilar-label"><b>DH</b> · Densidad</span>
  </div>
  <div id="pilar-detail-DH" class="pilar-inline-detail" style="display:none;"></div>
</div>
<div id="pilar-scorecard">
  <div class="sc-header">
    <div>
      <div class="sc-title" id="sc-title">Cluster</div>
      <div class="sc-sub" id="sc-sub"></div>
    </div>
    <button class="sc-close" onclick="closePilarScorecard()">✕</button>
  </div>
  <div id="sc-table"></div>
  <div class="sc-tm-insight" id="sc-tm-insight" style="display:none"></div>
</div>
</body>
</html>"""

os.makedirs(OUTPUT_DIR, exist_ok=True)
with open(OUTPUT_HTML,"w",encoding="utf-8") as f:
    f.write(html)
with open(OUTPUT_IDX,"w",encoding="utf-8") as f:
    f.write(html)

# Write to ROOT index.html to synchronize the workspace
ROOT_IDX = os.path.abspath(os.path.join(BASE, "..", "index.html"))
try:
    with open(ROOT_IDX, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅  Root index.html → {ROOT_IDX}")
except Exception as e:
    print(f"⚠ Failed to write root index.html: {e}")

# Write to mining-map/index.html to synchronize the maps
MAP_IDX = os.path.abspath(os.path.join(BASE, "..", "mining-map", "index.html"))
try:
    MAP_DIR = os.path.dirname(MAP_IDX)
    os.makedirs(MAP_DIR, exist_ok=True)
    with open(MAP_IDX, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅  mining-map index.html → {MAP_IDX}")
except Exception as e:
    print(f"⚠ Failed to write mining-map index.html: {e}")

sz=os.path.getsize(OUTPUT_HTML)/1024/1024
print(f"\n✅  Dashboard → {OUTPUT_HTML}")
print(f"✅  index.html  → {OUTPUT_IDX}")
print(f"   Size: {sz:.2f} MB")
print(f"   Clusters: {len(clusters)} | Faenas: {len(all_faenas)}")
print(f"   Train lines: {len(train_lines)} | SIGEX: {len(sigex_projects)}")
print(f"   OPT clusters: {len(_opt_slim['clusters'])}")
print(f"\n   open \"{OUTPUT_IDX}\"")

