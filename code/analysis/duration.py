"""Ice-cover duration per drumlin from NADI-1 (N. America): rival explanation to the frozen margin."""
import glob, re, numpy as np, pandas as pd, geopandas as gpd, shapely, statsmodels.formula.api as smf, warnings
from shapely.ops import unary_union
from pyproj import Transformer
warnings.filterwarnings("ignore")
EPSG = {"NY": 32618, "GB": 32616, "PS": 32610, "WAD": 32615, "AC": 32616, "BR": 32616, "LG": 32616, "PZ": 32615, "TM": 32615}
a = pd.read_csv("perdrumlin.csv"); a = a[a.field.isin(EPSG)].copy()
lon = np.zeros(len(a)); lat = np.zeros(len(a))
for f, e in EPSG.items():
    m = (a.field == f).values; t = Transformer.from_crs(e, 4326, always_xy=True); lon[m], lat[m] = t.transform(a.x.values[m], a.y.values[m])
files = glob.glob("/home/claude/ext/nadi/NADI-1*/*OPTIMAL*.shp"); ages = [float(re.search(r"/([\d.]+)ka", f).group(1)) for f in files]
cov = np.zeros((len(files), len(a)), bool)
for k, f in enumerate(files):
    g = gpd.read_file(f, on_invalid="fix"); g = g[g.geometry.notna()]
    poly = unary_union(shapely.make_valid(g.geometry.values)); cov[k] = shapely.contains_xy(poly, lon, lat)
ages = np.array(ages); A = np.where(cov, ages[:, None], np.nan)
a["deglac_ka"] = np.nanmin(A, 0); a["start_ka"] = np.nanmax(A, 0); a["dur_ka"] = a.start_ka - a.deglac_ka
a["lE"] = np.log(a.elong); a["ld"] = np.log(a.dist_km.clip(1)); a.to_csv("perdrumlin_dur.csv", index=False)
print(a.groupby("field")[["dist_km", "dur_ka", "deglac_ka"]].median().round(1))
near = a[a.dist_km < 60].dropna(subset=["dur_ka"])
print("within 60 km: corr(log dist, duration) =", round(np.corrcoef(near.ld, near.dur_ka)[0, 1], 2))
for fm in ("lE ~ C(field) + ld", "lE ~ C(field) + dur_ka", "lE ~ C(field) + ld + dur_ka"):
    m = smf.ols(fm, near).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(near.blk)[0]})
    print(f"  {fm:30s}", {k: f"{m.params[k]:+.3f} (p {m.pvalues[k]:.3f})" for k in m.params.index if not k.startswith("C(") and k != "Intercept"})
for f, g in near.groupby("field"):
    if g.dur_ka.std() > 0.1 and len(g) > 50:
        m = smf.ols("lE ~ ld + dur_ka", g).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(g.blk)[0]})
        print(f"  {f}: dist {m.params.ld:+.2f} (p {m.pvalues.ld:.3f}), duration {m.params.dur_ka:+.3f}/ka (p {m.pvalues.dur_ka:.3f}), dur range {g.dur_ka.min():.1f}-{g.dur_ka.max():.1f} ka")
