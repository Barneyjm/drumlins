"""Cumulative basal sliding / converging strain per drumlin from the calibrated ice-model runs; test vs elongation."""
import numpy as np, pandas as pd, json, statsmodels.formula.api as smf, warnings
from scipy.interpolate import RegularGridInterpolator
warnings.filterwarnings("ignore")
RUNS = {"NY": "drumlins/icemodel/run_g6", "GB": "gb/icemodel/run_gbG", "PS": "ps/icemodel/run_pF"}
a = pd.read_csv("perdrumlin.csv"); out = []
for f, run in RUNS.items():
    r = np.load(run + ".npz"); cfg = json.load(open(run + ".json")); x, y = r["x"], r["y"][::-1]
    H, ub, ux, uy = (r[k][:, ::-1, :] for k in ("H", "ub", "ux", "uy")); dt = 100.0; dx = x[1] - x[0]
    div = np.gradient(ux, dx, axis=2) + np.gradient(uy, dx, axis=1)          # 1/a  (y now ascending)
    cov = H > 50
    T = cov.sum(0) * dt                                                      # retreat-phase years covered
    S = (np.where(cov, ub, 0)).sum(0) * dt                                   # m of basal slip during retreat
    S0 = S + ub[0] * cfg["t_spin"]                                           # incl. build-up/maximum phase
    Cv = (np.where(cov, -div, 0)).sum(0) * dt                                # cumulative convergent strain
    Um = np.nanmean(np.where(cov, r["sp"][:, ::-1, :], np.nan), 0)
    d = a[a.field == f].copy()
    pts = np.c_[d.y.values, d.x.values]
    for name, F in (("Tc", T), ("S", S), ("S0", S0), ("Cv", Cv), ("Um", Um)):
        d[name] = RegularGridInterpolator((y, x), F, bounds_error=False, fill_value=np.nan, method="linear")(pts)
    out.append(d)
d = pd.concat(out); d = d[(d.Tc > 0) & (d.S > 0) & np.isfinite(d.Um)].copy()
d["lE"], d["lL"], d["lW"] = np.log(d.elong), np.log(d.length_m), np.log(d.width_m)
d["lS"], d["lS0"], d["lU"], d["ld"] = np.log(d.S), np.log(d.S0), np.log(d.Um), np.log(d.dist_km.clip(1))
d["Tk"] = d["Tc"] / 1000
d.to_csv("cumflow.csv", index=False)
print(d.groupby("field")[["Tc", "S", "S0", "Cv", "Um", "dist_km"]].median().round(2)); print(d.groupby("field").size())
cl = lambda q: dict(cov_type="cluster", cov_kwds={"groups": pd.factorize(q.blk)[0]})
# demeaned R2 (within-field) for each single predictor
print("\nwithin-field R2 and slope, pooled with field FE:")
for p in ("lS", "lS0", "Cv", "Tk", "lU", "ld"):
    m = smf.ols(f"lE ~ C(field) + {p}", d).fit(**cl(d)); m0 = smf.ols("lE ~ C(field)", d).fit()
    ia = smf.ols(f"lE ~ C(field)*{p}", d).fit(); fs = ia.compare_f_test(smf.ols(f"lE ~ C(field) + {p}", d).fit())
    per = {f: round(smf.ols(f"lE ~ {p}", g).fit().params[p], 3) for f, g in d.groupby("field")}
    print(f"  {p:4s}: slope {m.params[p]:+.3f} (p {m.pvalues[p]:.3f})  dR2 {m.rsquared - m0.rsquared:.4f}  per-field {per}  shared-slope F p={fs[1]:.3g}")
print("\njoint:")
for fm in ("lE ~ C(field) + lS + Cv", "lE ~ C(field) + lS + Cv + ld", "lE ~ C(field) + lS + Cv + lU + ld"):
    m = smf.ols(fm, d).fit(**cl(d)); print(f"  {fm:36s}", {k: f"{m.params[k]:+.3f} (p {m.pvalues[k]:.3f})" for k in m.params.index if not k.startswith("C(") and k != "Intercept"})
print("\nleave-one-field-out prediction of within-field elongation (r between predicted and observed demeaned log E):")
for p in ("lS + Cv", "lS", "Cv", "ld"):
    rs = []
    for f in RUNS:
        tr, te = d[d.field != f], d[d.field == f].copy()
        m = smf.ols(f"lE ~ C(field) + {p}", tr).fit(); terms = [t.strip() for t in p.split("+")]
        pred = sum(m.params[t] * te[t] for t in terms); obs = te.lE - te.lE.mean()
        rs.append(f"{f} {np.corrcoef(pred, obs)[0, 1]:+.2f}")
    print(f"  {p:8s}: " + ", ".join(rs))
