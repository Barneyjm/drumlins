"""Null test for the convergence result (reviewer point 4): can noisy azimuths of stubby drumlins alone
create an elongation-convergence correlation? Keep every drumlin's position and elongation, give the ice a
uniform flow direction (no real convergence), add azimuth noise whose spread depends on each drumlin's
elongation (measured from the real data), rebuild the flow field exactly as before and refit log E ~ conv."""
import numpy as np, pandas as pd, statsmodels.formula.api as smf
from scipy import ndimage as ndi
rng = np.random.default_rng(0)
FF = {"NY": "/home/claude/drumlins/flowfield_4km.npz", "GB": "/home/claude/gb/flowfield_4km_0.5.npz", "PS": "/home/claude/ps/flowfield_4km_0.5.npz"}
a = pd.read_csv("perdrumlin.csv")
def axdiff(a1, a2): d = (a1 - a2) % 180; return np.minimum(d, 180 - d)
def conv_from(fx, fy, dens, G, x0, y1, xs, ys, PATH=10000.0):
    ny, nx = fx.shape; mask = dens >= 8; div = np.gradient(fx, G, axis=1) - np.gradient(fy, G, axis=0); out = []
    for x, y in zip(xs, ys):
        yy, xx = (y1 - y) / G, (x - x0) / G; acc = 0; st = 0; ok = True
        while st < PATH:
            i, j = int(round(yy)), int(round(xx))
            if not (0 <= i < ny and 0 <= j < nx) or not mask[i, j]: ok = False; break
            acc += div[i, j] * 500; xx -= fx[i, j] * 500 / G; yy += fy[i, j] * 500 / G; st += 500
        out.append(-acc if ok else np.nan)
    return np.array(out)
for k, path in FF.items():
    f = np.load(path); G = float(f["G"]); x0, y1 = float(f["x0"]), float(f["y1"]); ny, nx = f["fx"].shape
    d = a[a.field == k].copy(); ci = ((d.x - x0) / G).astype(int).clip(0, nx - 1).values; ri = ((y1 - d.y) / G).astype(int).clip(0, ny - 1).values
    loc_az = np.degrees(np.arctan2(f["fx"][ri, ci], f["fy"][ri, ci])) % 180
    d["dev"] = axdiff(d.az.values, loc_az); d["Eb"] = pd.qcut(d.elong, 8)
    sd = d.groupby("Eb", observed=True).dev.apply(lambda v: np.sqrt(np.mean(np.radians(v) ** 2)))   # rms deviation (rad) per E bin
    sig = d.Eb.map(sd).astype(float).values
    obs = smf.ols("lE ~ conv", d.assign(lE=np.log(d.elong)).dropna(subset=["conv"])).fit().params.conv
    fxm, fym = np.nanmean(f["fx"][f["dens"] >= 8]), np.nanmean(f["fy"][f["dens"] >= 8]); th0 = np.degrees(np.arctan2(fxm, fym)) % 360
    slopes = []
    for rep in range(30):
        az = (th0 + np.degrees(rng.normal(0, sig))) % 180
        a2 = np.radians(2 * az); C = np.zeros((ny, nx)); S = np.zeros((ny, nx)); N = np.zeros((ny, nx))
        np.add.at(C, (ri, ci), np.cos(a2)); np.add.at(S, (ri, ci), np.sin(a2)); np.add.at(N, (ri, ci), 1)
        sg = 4.0; Cs, Ss, Ns = (ndi.gaussian_filter(v, sg) for v in (C, S, N))
        faz = (np.degrees(np.arctan2(Ss, Cs)) / 2) % 180; dd = np.abs(((faz - th0) + 180) % 360 - 180); faz = np.where(dd <= 90, faz, (faz + 180) % 360)
        fx, fy = np.sin(np.radians(faz)), np.cos(np.radians(faz)); dens = Ns * (2 * np.pi * sg ** 2)
        cv = conv_from(fx, fy, dens, G, x0, y1, d.x.values, d.y.values)
        t = pd.DataFrame(dict(lE=np.log(d.elong.values), conv=cv)).dropna(); slopes.append(smf.ols("lE ~ conv", t).fit().params.conv)
    slopes = np.array(slopes)
    print(f"{k}: azimuth rms deviation by E bin (deg) {np.round(np.degrees(sd.values), 0).tolist()} | observed slope {obs:+.2f} | "
          f"null slopes mean {slopes.mean():+.2f}, 95% range {np.percentile(slopes, 2.5):+.2f} to {np.percentile(slopes, 97.5):+.2f}")
