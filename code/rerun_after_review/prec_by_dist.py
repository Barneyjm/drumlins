"""Precision of the shape-light selection (p_sl >= 0.6) by distance inside the ice limit, using labelled cards
(GB, PS: blocked-CV predictions on training labels; LG, PZ, MO: blind spot-check cards labelled by Claude Opus).
Distance is taken from the nearest drumlin in perdrumlin.csv (it varies slowly in space)."""
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
pdm = pd.read_csv("perdrumlin.csv")
def dist_for(field, x, y):
    g = pdm[pdm.field == field]; d, i = cKDTree(g[["x", "y"]].values).query(np.c_[x, y]); return np.where(d < 3000, g.dist_km.values[i], np.nan)
rows = []
T = pd.read_csv("train_cv.csv")
for f in ("GB", "PS"):
    g = T[T.field == f]; rows.append(pd.DataFrame(dict(field=f, dist=dist_for(f, g.x, g.y), acc=g.p_sl >= 0.6, yes=g.label == 1, elong=g.elong)))
for f, d in (("LG", "lg"), ("PZ", "pz"), ("MO", "mo")):
    c = pd.read_csv(f"scored_{f}.csv"); L = pd.read_csv(f"/home/claude/{d}/check/claude_labels.csv").merge(c[["cid", "x", "y", "p_sl", "elong"]], on="cid")
    L = L[L.grp == "acc"]   # unweighted: accepted-stratum cards only
    rows.append(pd.DataFrame(dict(field=f, dist=dist_for(f, L.x, L.y), acc=L.p_sl >= 0.6, yes=L.me.str.lower() == "yes", elong=L.elong)))
R = pd.concat(rows).dropna(subset=["dist"]); R = R[R.acc]
R["band"] = pd.cut(R.dist, [0, 20, 60, 400], labels=["0–20 km", "20–60 km", ">60 km"])
t = R.groupby("band", observed=True).agg(cards=("yes", "size"), precision=("yes", "mean"), fields=("field", "nunique"))
t["±95%"] = 1.96 * np.sqrt(t.precision * (1 - t.precision) / t.cards); print(t.round(2).to_string())
print("\nby field and band:\n", R.groupby(["field", "band"], observed=True).yes.agg(["size", "mean"]).round(2).to_string())
fp = R[~R.yes]; tp = R[R.yes]
print("\nmedian elongation of false positives vs true drumlins among accepted cards:", round(fp.elong.median(), 2), round(tp.elong.median(), 2))

# --- Is the gradient there among labelled TRUE drumlins only (all labelled cards, not just accepted)?
import statsmodels.formula.api as smf
rows = []
for f in ("GB", "PS"):
    g = T[(T.field == f) & (T.label == 1)]; rows.append(pd.DataFrame(dict(field=f, dist=dist_for(f, g.x, g.y), elong=g.elong.values)))
for f, d in (("LG", "lg"), ("PZ", "pz"), ("MO", "mo")):
    c = pd.read_csv(f"scored_{f}.csv"); L = pd.read_csv(f"/home/claude/{d}/check/claude_labels.csv").merge(c[["cid", "x", "y", "elong"]], on="cid")
    L = L[L.me.str.lower() == "yes"]; rows.append(pd.DataFrame(dict(field=f, dist=dist_for(f, L.x, L.y), elong=L.elong.values)))
Y = pd.concat(rows).dropna(); Y = Y[Y.dist < 60]; Y["lE"], Y["ld"] = np.log(Y.elong), np.log(Y.dist.clip(1))
m = smf.ols("lE ~ C(field) + ld", Y).fit(cov_type="HC1")
print(f"\nlabelled true drumlins only, <60 km: n={len(Y)} ({Y.field.value_counts().to_dict()}), slope {m.params.ld:+.3f}±{m.bse.ld:.3f} (p {m.pvalues.ld:.3f})")
Yg = Y[Y.field == "GB"]; mg = smf.ols("lE ~ ld", Yg).fit(cov_type="HC1"); print(f"  Green Bay alone: n={len(Yg)} slope {mg.params.ld:+.3f}±{mg.bse.ld:.3f}")
# --- stricter cutoffs on the full selection
a = pd.read_csv("perdrumlin.csv"); sc = pd.concat([pd.read_csv(f"scored_{f}.csv").assign(field=f) for f in a.field.unique()])
a = a.merge(sc[["field", "x", "y", "p_sl"]], on=["field", "x", "y"], how="left")
a["lE"], a["ld"] = np.log(a.elong), np.log(a.dist_km.clip(1))
for t in (0.6, 0.7, 0.8, 0.9):
    s = a[(a.p_sl >= t) & (a.dist_km < 60)]; mm = smf.ols("lE ~ C(field) + ld", s).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(s.blk)[0]})
    print(f"  p_sl>={t}: n={len(s)} margin slope {mm.params.ld:+.3f}±{mm.bse.ld:.3f}")
