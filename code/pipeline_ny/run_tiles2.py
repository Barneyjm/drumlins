"""Spacing (object-shuffle) test + per-tile morphometry using model-accepted drumlins."""
import sys, numpy as np, pandas as pd, rasterio
from multiprocessing import Pool
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
sys.path.insert(0, "/home/claude/drumlins")
from detect import detect, tophat_relief
from pointtest import object_shuffle_test
from candidates import load

T, DX, THR = 512, 20.0, 0.5
ZF, VALID, TR = load()
SC = pd.read_csv("/home/claude/drumlins/candidates_scored2.csv")
TREE = cKDTree(SC[["row", "col"]].values)


def job(rc):
    r, c = rc
    v = VALID[r:r + T, c:c + T]
    if v.mean() < 0.6:
        return None
    z = ZF[r:r + T, c:c + T]
    lab, P = detect(z, DX, valid=v, flow_az=None, h_thresh=1.5, h_split=1.5, h_peak=3.0,
                    min_area=0.005e6, max_area=5e6, min_elong=0.0, pre_close_px=3)
    keep = np.zeros(lab.max() + 1, bool); ps, el, ln, wd, hts = [], [], [], [], []
    for p in P:
        d, i = TREE.query([p["row"] + r, p["col"] + c])
        if d > 3:
            continue
        pr = SC.p_drumlin.values[i]
        ps.append(pr); el.append(SC.elong.values[i]); ln.append(SC.length_m.values[i])
        wd.append(SC.width_m.values[i]); hts.append(SC.height_m.values[i])
        if pr >= THR:
            keep[p["label"]] = True
    labk = np.where(keep[lab], lab, 0)
    ps, el, ln, wd = map(np.array, (ps, el, ln, wd))
    out = dict(row=r, col=c, valid=float(v.mean()))
    x, y = TR * (c + T / 2, r + T / 2); out.update(x=x, y=y)
    for t in (0.3, 0.5, 0.7):
        m = ps >= t
        out[f"n_{t}"] = int(m.sum())
        out[f"elong_med_{t}"] = float(np.median(el[m])) if m.sum() >= 5 else np.nan
    if len(ps) >= 5 and ps.sum() > 0:
        o = np.argsort(el); cw = np.cumsum(ps[o]) / ps.sum()
        out["elong_wmed"] = float(el[o][np.searchsorted(cw, 0.5)])
        out["len_wmed"] = float(np.average(ln, weights=ps)); out["wid_wmed"] = float(np.average(wd, weights=ps))
    zc = ndi.grey_closing(z, size=(3, 3))
    res = object_shuffle_test(tophat_relief(zc, DX), labk, v, DX, nsim=39, seed=r * 7 + c)
    if res:
        out.update({k: res[k] for k in ("n", "p_pk", "p_q", "pk_obs", "pk_null_med", "q_obs", "lam_lat", "flow_az")})
    return out


if __name__ == "__main__":
    H, W = ZF.shape
    tiles = [(r, c) for r in range(0, H - T + 1, T) for c in range(0, W - T + 1, T)]
    with Pool(2) as p:
        out = [o for o in p.map(job, tiles) if o]
    df = pd.DataFrame(out); df.to_csv("/home/claude/drumlins/ny_tiles_r2.csv", index=False)
    t = df.dropna(subset=["p_pk"])
    from scipy.stats import binom
    k = int((t.p_pk < 0.05).sum())
    print(f"spacing test: {len(t)} tiles, {int(t.n.sum())} model drumlins; p_pk<0.05 in {k} "
          f"(chance ~8%: P(>= {k}) = {1 - binom.cdf(k - 1, len(t), 0.08):.3f}); p_q<0.05 in {int((t.p_q < 0.05).sum())}")
    print(f"median pk_obs/pk_null {np.median(t.pk_obs / t.pk_null_med):.2f}")
