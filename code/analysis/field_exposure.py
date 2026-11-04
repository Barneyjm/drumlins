import sys, glob, re, numpy as np, pandas as pd, geopandas as gpd, shapely, warnings
from shapely.ops import unary_union
from pyproj import Transformer
warnings.filterwarnings("ignore")
files = sorted(glob.glob("/home/claude/ext/nadi/NADI-1*/*OPTIMAL*.shp"), key=lambda f: -float(re.search(r"/([\d.]+)ka", f).group(1)))
polys = []
for f in files:
    g = gpd.read_file(f, on_invalid="fix"); g = g[g.geometry.notna()].to_crs(5070); polys.append(unary_union(shapely.make_valid(g.geometry.values)))
ext = unary_union([p for f, p in zip(files, polys) if float(re.search(r"/([\d.]+)ka", f).group(1)) >= 14]).boundary
rows = []; alb = Transformer.from_crs(4326, 5070, always_xy=True)
for arg in sys.argv[1:]:
    K, v = arg.split("="); D, E, thr = v.split(","); fn = "candidates_scored3.csv" if D == "drumlins" else "candidates_scored.csv"
    s = pd.read_csv(f"/home/claude/{D}/{fn}"); d = s[(s.p_drumlin >= float(thr)) & (s.height_m < 60)].sample(frac=1, random_state=1).head(400)
    lo, la = Transformer.from_crs(int(E), 4326, always_xy=True).transform(d.x.values, d.y.values); X, Y = alb.transform(lo, la); pts = shapely.points(X, Y)
    Dm = np.array([np.where(shapely.contains(P, pts), shapely.distance(pts, P.boundary) / 1000, np.nan) for P in polys])
    dur = np.isfinite(Dm).sum(0) * 0.5; S = np.nansum(np.where(np.isfinite(Dm), np.clip(Dm, .5, None) ** .5, 0), 0) * .5
    rows.append(dict(field=K, dist=float(np.median(shapely.distance(pts, ext) / 1000)), dur=float(np.median(dur)), S05=float(np.median(S)), covered=float((dur > 0).mean())))
    print(rows[-1], flush=True)
pd.DataFrame(rows).to_csv("/home/claude/fieldprops_exp.csv", index=False)
