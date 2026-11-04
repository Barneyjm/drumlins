"""Per-field properties for the baseline-elongation question. Usage: python3 fieldprops.py FIELD=dir,epsg,thr ..."""
import sys, numpy as np, pandas as pd, rasterio
from scipy import ndimage as ndi
from pyproj import Transformer
rows = []
for arg in sys.argv[1:]:
    k, v = arg.split("="); D, e, thr = v.split(","); thr = float(thr)
    f = "candidates_scored3.csv" if D == "drumlins" else "candidates_scored.csv"
    s = pd.read_csv(f"/home/claude/{D}/{f}"); d = s[(s.p_drumlin >= thr) & (s.height_m < 60)].copy()
    with rasterio.open(f"/home/claude/{D}/data/ny_dem_20m.tif") as src:
        z = src.read(1, out_shape=(src.height // 10, src.width // 10)).astype(float); tr = src.transform * src.transform.scale(10, 10)
    ok = np.isfinite(z); zf = np.where(ok, z, np.nanmean(z))
    num = ndi.gaussian_filter(np.where(ok, z, 0), 12.5); den = ndi.gaussian_filter(ok.astype(float), 12.5); Z5 = num / np.maximum(den, 1e-6)   # ~5 km smooth (200 m px)
    gy, gx = np.gradient(Z5, 200.0); gy = -gy                                                     # north-positive
    z1 = ndi.gaussian_filter(zf, 2.5); rel = ndi.generic_filter(z1, np.std, size=25)              # relief of 1-km-smoothed surface in 5 km windows
    col, row = (~tr) * (d.x.values, d.y.values); r_, c_ = np.clip(row.astype(int), 0, z.shape[0] - 1), np.clip(col.astype(int), 0, z.shape[1] - 1)
    az = np.radians(d.az.values)                                                                  # axial; sign fixed by mean flow later
    sx, sy = gx[r_, c_], gy[r_, c_]
    along = np.abs(sx * np.sin(az) + sy * np.cos(az))                                             # |regional slope along drumlin axis|
    lon, lat = Transformer.from_crs(int(e), 4326, always_xy=True).transform(d.x.median(), d.y.median())
    rows.append(dict(field=k, n=len(d), thr=thr, E=d.elong.median(), L=d.length_m.median(), W=d.width_m.median(), H=d.height_m.median(),
                     relief=float(np.median(rel[r_, c_])), slope_along=float(np.median(along) * 1000), lat=lat, lon=lon,
                     elev=float(np.nanmedian(z[r_, c_])), density=len(d) / (ok.sum() * 0.04)))
    print(k, "ok", flush=True)
pd.DataFrame(rows).to_csv("/home/claude/fieldprops_dem.csv", index=False); print(pd.DataFrame(rows).round(2).to_string())
