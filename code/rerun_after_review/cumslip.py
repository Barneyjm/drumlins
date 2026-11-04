"""Zoet-style cumulative slip per drumlin from the NADI-1 margin chronology.
At each 0.5-ka slice the lobe is treated as a perfectly plastic ice profile H = sqrt(2 tau0 x / (rho g)) fed by uniform
ablation a over the ablation zone, so flux q = a x and slip speed u = q/H ~ sqrt(x) (x = distance up-ice from the margin).
Cumulative slip S = sum over covered slices of u dt.  Field-specific constants (tau0, a) drop into field fixed effects in log space."""
import glob, re, numpy as np, pandas as pd, geopandas as gpd, shapely, statsmodels.formula.api as smf, warnings
from shapely.ops import unary_union
from pyproj import Transformer
warnings.filterwarnings("ignore")
EPSG = {"NY": 32618, "GB": 32616, "PS": 32610, "AC": 32616, "BR": 32616, "LG": 32616, "PZ": 32615, "TM": 32615}
a = pd.read_csv("perdrumlin.csv"); a = a[a.field.isin(EPSG)].reset_index(drop=True)
X = np.zeros(len(a)); Y = np.zeros(len(a))
to_alb = Transformer.from_crs(4326, 5070, always_xy=True)
for f, e in EPSG.items():
    m = (a.field == f).values; lo, la = Transformer.from_crs(e, 4326, always_xy=True).transform(a.x.values[m], a.y.values[m]); X[m], Y[m] = to_alb.transform(lo, la)
pts = shapely.points(X, Y)
files = sorted(glob.glob("/home/claude/ext/nadi/NADI-1*/*OPTIMAL*.shp"), key=lambda f: -float(re.search(r"/([\d.]+)ka", f).group(1)))
D = []; ages = []
for f in files:
    g = gpd.read_file(f, on_invalid="fix"); g = g[g.geometry.notna()].to_crs(5070)
    P = unary_union(shapely.make_valid(g.geometry.values)); inside = shapely.contains(P, pts)
    dist = shapely.distance(pts, P.boundary) / 1000.0
    D.append(np.where(inside, dist, np.nan)); ages.append(float(re.search(r"/([\d.]+)ka", f).group(1)))
D = np.array(D); dt = 0.5
a["dur_ka"] = np.isfinite(D).sum(0) * dt
for p, nm in ((0.0, "S0"), (0.5, "S05"), (1.0, "S1")):
    a[nm] = np.nansum(np.where(np.isfinite(D), np.clip(D, 0.5, None) ** p, 0), 0) * dt
a["xmean"] = np.nanmean(D, 0)
a.to_csv("cumslip.csv", index=False)
