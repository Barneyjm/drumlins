"""Ice-flow direction field from drumlin long-axis azimuths; flowline divergence and an upstream-integrated
flux-tube width (speed proxy). Uses orientations only (never elongation) so the later test is not circular."""
import sys, numpy as np, pandas as pd, rasterio
from scipy import ndimage as ndi

D = "/home/claude/lg"
SIG_KM = float(sys.argv[1]) if len(sys.argv) > 1 else 4.0
THR = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
G = 1000.0                                                      # grid spacing (m)
s = pd.read_csv(f"{D}/candidates_scored.csv")
d = s[(s.p_drumlin >= THR) & (s.height_m < 60)]
with rasterio.open(f"{D}/data/ny_dem_20m.tif") as f:
    tr = f.transform; H, W = f.height, f.width
x0, y1 = tr.c, tr.f; nx, ny = int(W * 20 / G) + 1, int(H * 20 / G) + 1
ci = ((d.x - x0) / G).astype(int).clip(0, nx - 1); ri = ((y1 - d.y) / G).astype(int).clip(0, ny - 1)
a2 = np.radians(2 * d.az.values)
C = np.zeros((ny, nx)); S = np.zeros((ny, nx)); N = np.zeros((ny, nx))
np.add.at(C, (ri, ci), np.cos(a2)); np.add.at(S, (ri, ci), np.sin(a2)); np.add.at(N, (ri, ci), 1)
sg = SIG_KM * 1000 / G
Cs, Ss, Ns = (ndi.gaussian_filter(v, sg) for v in (C, S, N))
coh = np.hypot(Cs, Ss) / np.maximum(Ns, 1e-9)                  # orientation coherence 0..1
az = (np.degrees(np.arctan2(Ss, Cs)) / 2) % 180                 # axial azimuth
from pyproj import Transformer
_sx, _sy = Transformer.from_crs("EPSG:4326", "EPSG:32616", always_xy=True).transform(-88.0, 47.0)
_gx = x0 + (np.arange(nx) + 0.5) * G; _gy = y1 - (np.arange(ny) + 0.5) * G
_X, _Y = np.meshgrid(_gx, _gy); _away = np.degrees(np.arctan2(_X - _sx, _Y - _sy)) % 360
_d = np.abs(((az - _away) + 180) % 360 - 180)
flow_az = np.where(_d <= 90, az, (az + 180) % 360)              # sense pointing away from the lobe source
fx, fy = np.sin(np.radians(flow_az)), np.cos(np.radians(flow_az))   # east, north components
dens = Ns * (2 * np.pi * sg ** 2)                               # ~drumlins within the kernel
mask = (dens >= 8) & (coh >= 0.5)
div = np.gradient(fx, G, axis=1) - np.gradient(fy, G, axis=0)  # rows run north->south, so d/dy = -d/drow
div = np.where(mask, div, np.nan)


def upstream_log_width(r, c, step=500.0, smax=60000.0):
    """Integrate divergence upstream along the flowline; returns log(w_here/w_entry) and path length."""
    yy, xx, acc, sdone = float(r), float(c), 0.0, 0.0
    while sdone < smax:
        i, j = int(round(yy)), int(round(xx))
        if not (0 <= i < ny and 0 <= j < nx) or not mask[i, j]:
            break
        acc += div[i, j] * step
        xx -= fx[i, j] * step / G; yy += fy[i, j] * step / G     # go upstream: x back along fx, north = row decreasing
        sdone += step
    return acc, sdone


np.savez(f"{D}/flowfield_{SIG_KM:g}km_{THR}.npz", fx=fx, fy=fy, div=div, coh=coh, mask=mask, dens=dens,
         x0=x0, y1=y1, G=G)
t = pd.read_csv(f"{D}/tile_morph_{THR}.csv")
rows = []
for _, r in t.iterrows():
    rr, cc = (y1 - r.y) / G, (r.x - x0) / G
    i, j = int(rr), int(cc)
    if not (0 <= i < ny and 0 <= j < nx) or not mask[i, j]:
        continue
    lw, L = upstream_log_width(rr, cc)
    win = div[max(i - 5, 0):i + 6, max(j - 5, 0):j + 6]
    rows.append(dict(tile=int(r.tile), div_local=float(np.nanmean(win)), logw=lw, path_km=L / 1000,
                     speed_proxy=float(np.exp(-lw)), coh=float(coh[i, j]), E=r.E, L=r.L, W=r.W, n=r.n))
out = pd.DataFrame(rows); out.to_csv(f"{D}/tile_flow_{SIG_KM:g}km_{THR}.csv", index=False)
print(f"sigma {SIG_KM} km: tiles {len(out)}; median upstream path {out.path_km.median():.0f} km; "
      f"speed proxy range {out.speed_proxy.min():.2f}-{out.speed_proxy.max():.2f}")
