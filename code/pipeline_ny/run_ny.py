"""Run windowed spectral analysis over the NY DEM; write CSV + maps."""
import sys, csv, numpy as np, rasterio
from scipy import ndimage as ndi
sys.path.insert(0, "/home/claude/drumlins")
from spectral import analyze_window, iter_windows, synthetic_field

WIN, STEP, DX, LMAX = 768, 192, 20.0, 5000.0
D = "/home/claude/drumlins"


def null_threshold(n=60):
    """95th pct of q_lat for random (Poisson) placement of similar-size drumlins."""
    qs, pks = [], []
    for i in range(n):
        rng = np.random.default_rng(5000 + i)
        lat = rng.uniform(250, 800)
        z = synthetic_field(WIN, DX, lat_spacing=lat, long_spacing=3 * lat,
                            flow_az=rng.uniform(0, 180), width=0.5 * lat, elong=rng.uniform(2, 4),
                            height=12, placement="poisson", noise_amp=rng.uniform(2, 8),
                            seed=6000 + i)
        r = analyze_window(z, DX, lam_max=LMAX)
        qs.append(np.nan_to_num(r["q_lat"])); pks.append(r["pk_lat"])
    return float(np.percentile(qs, 95)), float(np.percentile(pks, 95))


def main():
    with rasterio.open(f"{D}/data/ny_dem_20m.tif") as s:
        z = s.read(1); water = s.read(2) > 0.5; tr = s.transform
    valid = np.isfinite(z) & ~water
    # fill invalid with normalized-convolution smooth surface (no sharp edges in FFT)
    zz = np.where(valid, z, 0.0)
    num = ndi.gaussian_filter(zz, 25); den = ndi.gaussian_filter(valid.astype(float), 25)
    zfill = np.where(valid, z, num / np.maximum(den, 1e-6))
    qthr, pkthr = null_threshold()
    print(f"null (Poisson) 95th pct: q_lat {qthr:.2f}  pk_lat {pkthr:.2f}")
    rows = []
    for r, c in iter_windows(zfill, WIN, STEP, valid, min_valid=0.85):
        res = analyze_window(zfill[r:r + WIN, c:c + WIN], DX, lam_max=LMAX)
        cx, cy = tr * (c + WIN / 2, r + WIN / 2)
        res.update(row=r, col=c, x=cx, y=cy, valid=float(valid[r:r + WIN, c:c + WIN].mean()))
        rows.append(res)
    keys = list(rows[0].keys())
    with open(f"{D}/ny_windows.csv", "w", newline="") as f:
        w = csv.DictWriter(f, keys); w.writeheader(); w.writerows(rows)
    np.save(f"{D}/data/null_thr.npy", np.array([qthr, pkthr]))
    print(len(rows), "windows")


if __name__ == "__main__":
    main()
