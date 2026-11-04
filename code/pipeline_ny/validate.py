"""Validation gates for the spectral drumlin pipeline on synthetic fields."""
import itertools, json, sys
import numpy as np
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from spectral import synthetic_field, analyze_window, fractal_noise

DX, N = 20.0, 512


def angdiff(a, b):
    d = abs(a - b) % 180
    return min(d, 180 - d)


def recovery():
    rows = []
    seed = 0
    for lat, az, noise, jit in itertools.product([300, 500, 800], [0, 35, 80, 125, 160],
                                                 [2, 6, 12], [0.1, 0.25]):
        seed += 1
        z = synthetic_field(N, DX, lat_spacing=lat, long_spacing=3 * lat, flow_az=az,
                            width=0.5 * lat, elong=3, height=12, jitter=jit,
                            noise_amp=noise, seed=seed)
        r = analyze_window(z, DX)
        rows.append(dict(lat=lat, az=az, noise=noise, jit=jit,
                         az_err=angdiff(r["flow_az"], az),
                         lat_err=abs(r["lam_lat"] - lat) / lat,
                         long_err=abs(r["lam_long"] - 3 * lat) / (3 * lat),
                         reg_lat=r["reg_lat"], reg_long=r["reg_long"]))
    return rows


def discrimination(n_each=40):
    out = {"lattice": [], "poisson": [], "noise_only": []}
    for i in range(n_each):
        rng = np.random.default_rng(1000 + i)
        lat = rng.uniform(300, 800); az = rng.uniform(0, 180)
        kw = dict(lat_spacing=lat, long_spacing=3 * lat, flow_az=az, width=0.5 * lat,
                  elong=3, height=12, noise_amp=rng.uniform(2, 8), seed=2000 + i)
        for pl in ("lattice", "poisson"):
            r = analyze_window(synthetic_field(N, DX, placement=pl, jitter=0.18, **kw), DX)
            out[pl].append(r)
        zn = fractal_noise(N, DX, rng.uniform(2, 3), 10, rng)
        out["noise_only"].append(analyze_window(zn, DX))
    return out


def auc(pos, neg):
    pos, neg = np.asarray(pos), np.asarray(neg)
    return float(((pos[:, None] > neg[None, :]).mean() + 0.5 * (pos[:, None] == neg[None, :]).mean()))


if __name__ == "__main__":
    rec = recovery()
    az = np.array([r["az_err"] for r in rec]); le = np.array([r["lat_err"] for r in rec])
    lo = np.array([r["long_err"] for r in rec])
    print(f"RECOVERY n={len(rec)}  az_err median {np.median(az):.1f} deg  p90 {np.percentile(az,90):.1f}")
    print(f"  lat_err median {np.median(le)*100:.1f}%  p90 {np.percentile(le,90)*100:.1f}%")
    print(f"  long_err median {np.median(lo)*100:.1f}%  p90 {np.percentile(lo,90)*100:.1f}%")
    for key in ("noise", "lat", "jit"):
        for v in sorted(set(r[key] for r in rec)):
            sub = [r for r in rec if r[key] == v]
            print(f"   {key}={v}: az {np.median([s['az_err'] for s in sub]):.1f}  "
                  f"lat {np.median([s['lat_err'] for s in sub])*100:.1f}%  "
                  f"long {np.median([s['long_err'] for s in sub])*100:.1f}%")
    d = discrimination()
    for k in ("reg_lat", "reg_long", "pk_lat", "pk_long"):
        L = [r[k] for r in d["lattice"]]; P = [r[k] for r in d["poisson"]]; Nn = [r[k] for r in d["noise_only"]]
        print(f"{k:9s} lattice med {np.median(L):.3f} | poisson {np.median(P):.3f} | noise {np.median(Nn):.3f}"
              f" | AUC lat-vs-poisson {auc(L,P):.2f}  lat-vs-noise {auc(L,Nn):.2f}")
    json.dump(dict(recovery=rec), open("/home/claude/drumlins/validation_recovery.json", "w"))
