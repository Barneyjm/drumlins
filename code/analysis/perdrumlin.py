"""Drumlin-level test in every field: log elongation (and L, W) vs upstream flow convergence and distance from the ice limit.
Cluster-robust errors by 5 km blocks."""
import sys, numpy as np, pandas as pd, statsmodels.formula.api as smf, warnings, glob, re
warnings.filterwarnings("ignore")
import geopandas as gpd, shapely
from shapely.ops import unary_union
from shapely.geometry import Point
from pyproj import Transformer
F = {"NY": ("drumlins", "candidates_scored3.csv", 0.25, "flowfield_4km.npz", 32618),
     "GB": ("gb", "candidates_scored.csv", 0.5, "flowfield_4km_0.5.npz", 32616),
     "PS": ("ps", "candidates_scored.csv", 0.5, "flowfield_4km_0.5.npz", 32610),
     "WAD": ("wad", "candidates_scored.csv", 0.7, "flowfield_4km_0.7.npz", 32615),
     "AC": ("ac", "candidates_scored.csv", 0.7, "flowfield_4km_0.7.npz", 32616),
     "BR": ("br", "candidates_scored.csv", 0.7, "flowfield_4km_0.7.npz", 32616),
     "LG": ("lg", "candidates_scored.csv", 0.7, "flowfield_4km_0.7.npz", 32616),
     "PZ": ("pz", "candidates_scored.csv", 0.7, "flowfield_4km_0.7.npz", 32615),
     "TM": ("tm", "candidates_scored.csv", 0.7, "flowfield_4km_0.7.npz", 32615),
     "BI": ("bi", "candidates_scored.csv", 0.7, "flowfield_4km_0.7.npz", 32719),
     "MO": ("mo", "candidates_scored.csv", 0.7, "flowfield_4km_0.7.npz", 32719),
     "STG": ("stg", "candidates_scored.csv", 0.7, "flowfield_4km_0.7.npz", 32633),
     "ZBO": ("zbo", "candidates_scored.csv", 0.7, "flowfield_4km_0.7.npz", 32634),
     "IRL": ("irl", "candidates_scored.csv", 0.7, "flowfield_4km_0.7.npz", 32629),
     "EDEN": ("eden", "candidates_scored.csv", 0.7, "flowfield_4km_0.7.npz", 27700)}
import os
THRS = dict(a.split("=") for a in os.environ.get("THRS", "").split(",") if a)
for k, v in THRS.items(): F[k] = F[k][:2] + (float(v), f"flowfield_4km_{v}.npz") + F[k][4:]
only = sys.argv[1:] or list(F)
PATH = 10000.0
shp = sorted(glob.glob("/home/claude/ext/nadi/NADI-1*/*OPTIMAL*.shp"), key=lambda f: -float(re.search(r"/([\d.]+)ka", f).group(1)))
def ld(f):
    g = gpd.read_file(f, on_invalid="fix"); g = g[g.geometry.notna()]; return unary_union(shapely.make_valid(g.geometry.values))
ext_na = unary_union([ld(f) for f in shp if float(re.search(r"/([\d.]+)ka", f).group(1)) >= 14])
EU = {"STG", "ZBO", "IRL", "EDEN"}
dshp = sorted(glob.glob("/home/claude/ext/dated/DATED1*/TS*_mc.shp")) + glob.glob("/home/claude/ext/dated/DATED1*/TS_27_poly.shp")
def dage(f): m = re.search(r"TS_?(\d+)", f); return int(m.group(1))
ext_eu = None
SA = {"BI", "MO"}; ext_sa = None
if any(k in SA for k in only):
    ps = glob.glob("/home/claude/ext/patice/Supplementary data/Shapefiles/Reconstruction/[Ii]cesheet*ka.shp")
    ps = [f for f in ps if float(re.search(r"heet([\d.]+)ka", f).group(1)) >= 15]
    ext_sa = unary_union([shapely.make_valid(g) for f in ps for g in gpd.read_file(f).to_crs(4326).geometry.values if g is not None])
if any(k in EU for k in only):
    gs = [gpd.read_file(f).to_crs(4326) for f in dshp if dage(f) >= 17]
    ext_eu = unary_union([shapely.make_valid(g) for gg in gs for g in gg.geometry.values if g is not None])
rows = []
for k in only:
    D, cf, thr, ff, epsg = F[k]
    try: f = np.load(f"/home/claude/{D}/{ff}")
    except FileNotFoundError: print(k, "no flow field yet"); continue
    fx, fy, dens = f["fx"], f["fy"], f["dens"]; G = float(f["G"]) if "G" in f else 1000.0; x0, y1 = float(f["x0"]), float(f["y1"]); ny, nx = fx.shape
    mask = dens >= 8; div = np.gradient(fx, G, axis=1) - np.gradient(fy, G, axis=0)
    s = pd.read_csv(f"/home/claude/{D}/{cf}"); d = s[(s.p_drumlin >= thr) & (s.height_m < 60)].copy()
    ext = ext_eu if k in EU else (ext_sa if k in SA else ext_na)
    bnd = gpd.GeoSeries([ext.boundary], crs=4326).to_crs(epsg).iloc[0]; inside = gpd.GeoSeries([ext], crs=4326).to_crs(epsg).iloc[0]
    conv = []
    for x, y in zip(d.x.values, d.y.values):
        yy, xx = (y1 - y) / G, (x - x0) / G; acc = 0; st = 0; ok = True
        while st < PATH:
            i, j = int(round(yy)), int(round(xx))
            if not (0 <= i < ny and 0 <= j < nx) or not mask[i, j]: ok = False; break
            acc += div[i, j] * 500; xx -= fx[i, j] * 500 / G; yy += fy[i, j] * 500 / G; st += 500
        conv.append(-acc if ok else np.nan)
    d["conv"] = conv
    d["dist_km"] = [bnd.distance(Point(x, y)) / 1000 for x, y in zip(d.x, d.y)]
    d["field"] = k; d["blk"] = k + (d.x // 5000).astype(int).astype(str) + "_" + (d.y // 5000).astype(int).astype(str)
    rows.append(d[["field", "x", "y", "length_m", "width_m", "elong", "az", "conv", "dist_km", "blk"]])
a = pd.concat(rows); a.to_csv("perdrumlin.csv", index=False)
a["lE"], a["lL"], a["lW"], a["ldist"] = np.log(a.elong), np.log(a.length_m), np.log(a.width_m), np.log(a.dist_km.clip(1))
print(f"{'field':5s} {'n':>5s} {'medL':>6s} {'medW':>5s} {'medE':>5s} {'dist km':>9s} | {'E~conv':>14s} {'E~ldist':>14s} | {'L~conv':>14s} {'W~conv':>14s}")
for k, g in a.groupby("field", sort=False):
    h = g.dropna(subset=["conv"])
    def fit(fm, data, term):
        m = smf.ols(fm, data).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(data.blk)[0]}); return f"{m.params[term]:+.2f}{'*' if m.pvalues[term] < 0.05 else ' '}({m.pvalues[term]:.2f})"
    print(f"{k:5s} {len(h):5d} {g.length_m.median():6.0f} {g.width_m.median():5.0f} {g.elong.median():5.2f} {g.dist_km.min():4.0f}-{g.dist_km.max():<4.0f} | "
          f"{fit('lE ~ conv', h, 'conv'):>14s} {fit('lE ~ ldist', g, 'ldist'):>14s} | {fit('lL ~ conv', h, 'conv'):>14s} {fit('lW ~ conv', h, 'conv'):>14s}  joint: {fit('lE ~ conv + ldist', h, 'conv')} / {fit('lE ~ conv + ldist', h, 'ldist')}")
