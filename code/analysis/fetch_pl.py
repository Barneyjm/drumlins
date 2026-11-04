"""Fetch the Polish national lidar DTM (GUGiK WCS) at 20 m over a lon/lat box, in EPSG:2180, plus a flat-water mask."""
import sys, subprocess, numpy as np, rasterio, os
from rasterio.merge import merge
from scipy import ndimage as ndi
from pyproj import Transformer
D, lo0, la0, lo1, la1 = sys.argv[1], *map(float, sys.argv[2:6])
t = Transformer.from_crs(4326, 2180, always_xy=True)
xs, ys = zip(*[t.transform(a, b) for a in (lo0, lo1) for b in (la0, la1)])
X0, X1, Y0, Y1 = min(xs), max(xs), min(ys), max(ys); S = 6000.0; tiles = []
os.makedirs(f"{D}/data/pl", exist_ok=True)
for x in np.arange(X0, X1, S):
    for y in np.arange(Y0, Y1, S):
        f = f"{D}/data/pl/t_{int(x)}_{int(y)}.tif"
        if not os.path.exists(f):
            u = ("https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WCS/DigitalTerrainModelFormatTIFF?SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCoverage"
                 f"&COVERAGEID=DTM_PL-KRON86-NH_TIFF&FORMAT=image/tiff&SUBSET=x({x:.0f},{x + S:.0f})&SUBSET=y({y:.0f},{y + S:.0f})&SCALESIZE=x(300),y(300)")
            for _ in range(3):
                r = subprocess.run(["curl", "-sS", "-m", "300", "-o", f, "-w", "%{http_code}", u], capture_output=True, text=True)
                if r.stdout == "200": break
            print(f, r.stdout, flush=True)
        tiles.append(f)
srcs = [rasterio.open(f) for f in tiles]
mos, tr = merge(srcs, nodata=-9999)
z = mos[0].astype(np.float32); z[(z <= 0.01) | (z < -100)] = np.nan
zf = np.nan_to_num(z, nan=-9999); rng = ndi.maximum_filter(zf, 5) - ndi.minimum_filter(zf, 5)
flat = rng < 0.05; lab, nl = ndi.label(flat); sz = ndi.sum(flat, lab, range(1, nl + 1))
water = ndi.binary_dilation(np.isin(lab, np.where(sz * 400 > 0.5e6)[0] + 1), iterations=3) | ~np.isfinite(z)
prof = dict(driver="GTiff", height=z.shape[0], width=z.shape[1], count=2, dtype="float32", crs="EPSG:2180", transform=tr, compress="deflate", nodata=np.nan)
with rasterio.open(f"{D}/data/ny_dem_20m.tif", "w", **prof) as o: o.write(z, 1); o.write(water.astype(np.float32), 2)
print("wrote", z.shape, "valid", np.isfinite(z).mean().round(3), "water", water.mean().round(3))
