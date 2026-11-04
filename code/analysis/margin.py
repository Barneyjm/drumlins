"""Distance to the maximum (LGM) ice limit and deglaciation age from NADI-1 (Dalton et al. 2023) per tile."""
import glob, re, sys, numpy as np, pandas as pd, geopandas as gpd
from shapely.ops import unary_union
from shapely.geometry import Point
from pyproj import Transformer
FILES = sorted(glob.glob("/home/claude/ext/nadi/NADI-1*/*OPTIMAL*.shp"), key=lambda f: -float(re.search(r"/([\d.]+)ka", f).group(1)))
AGE = [float(re.search(r"/([\d.]+)ka", f).group(1)) for f in FILES]
FIELDS = {"NY": ("drumlins/tile_morph_till.csv", 32618), "GB": ("gb/tile_morph_0.5.csv", 32616), "PS": ("ps/tile_morph_0.5_n12.csv", 32610)}
for a in sys.argv[1:]:
    k, f, e = a.split(","); FIELDS[k] = (f, int(e))
def load(f):
    import shapely
    g = gpd.read_file(f, on_invalid="fix"); g = g[g.geometry.notna()]
    return unary_union(shapely.make_valid(g.geometry.values))
polys = None
rows = []
for k, (tf, epsg) in FIELDS.items():
    t = pd.read_csv(tf); to_ll = Transformer.from_crs(f"EPSG:{epsg}", "EPSG:4326", always_xy=True)
    lon, lat = to_ll.transform(t.x.values, t.y.values)
    lo0, la0 = lon.mean(), lat.mean()
    if polys is None: polys = [load(f) for f in FILES]
    ext = unary_union([p for a, p in zip(AGE, polys) if a >= 14])          # maximum extent over 25-14 ka
    bnd = gpd.GeoSeries([ext.boundary], crs=4326).to_crs(epsg).iloc[0]
    for i, q in t.iterrows():
        P = Point(lon[i], lat[i]); inside = [a for a, p in zip(AGE, polys) if p.contains(P)]
        rows.append(dict(field=k, tile=q.tile, dist_margin_km=bnd.distance(Point(q.x, q.y)) / 1000, deglac_ka=min(inside) if inside else np.nan,
                         covered_from_ka=max(inside) if inside else np.nan))
    print(k, "done")
o = pd.DataFrame(rows); o.to_csv("margin_tiles.csv", index=False)
print(o.groupby("field")[["dist_margin_km", "deglac_ka", "covered_from_ka"]].describe().round(1).T.to_string())
