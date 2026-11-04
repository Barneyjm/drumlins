"""Margin gradient within 60 km: original selection vs shape-light selection.
Field fixed effects with 5 km block-clustered SEs, plus a mixed model with a random slope per field."""
import numpy as np, pandas as pd, statsmodels.formula.api as smf, warnings; warnings.filterwarnings("ignore")
sets = {"original": pd.read_csv("/home/claude/perdrumlin.csv"), "shape-light": pd.read_csv("perdrumlin.csv")}
bins = [0, 10, 20, 30, 45, 60, 100, 150, 250, 400]
for nm, a in sets.items():
    a = a.copy(); a["lE"], a["lL"], a["lW"], a["ld"] = np.log(a.elong), np.log(a.length_m), np.log(a.width_m), np.log(a.dist_km.clip(1))
    a["rel"] = a.lE - a.groupby("field").lE.transform("mean")
    a["bin"] = pd.cut(a.dist_km, bins); t = a.groupby("bin", observed=True).agg(n=("rel", "size"), fields=("field", "nunique"), rel=("rel", "mean"))
    t["pct"] = (np.exp(t.rel) - 1) * 100
    print(f"\n=== {nm}: n={len(a)}\n" + t[["n", "fields", "pct"]].round(1).to_string())
    near = a[a.dist_km < 60]
    for lab, sub in (("all <60 km", near), ("cold-margin (GB LG PZ MO)", near[near.field.isin(["GB", "LG", "PZ", "MO"])])):
        cl = dict(cov_type="cluster", cov_kwds={"groups": pd.factorize(sub.blk)[0]})
        out = []
        for y in ("lE", "lL", "lW"):
            m = smf.ols(f"{y} ~ C(field) + ld", sub).fit(**cl); out.append(f"{y[1]} {m.params.ld:+.3f}±{m.bse.ld:.3f}")
        try:
            mm = smf.mixedlm("lE ~ ld", sub, groups=sub.field, re_formula="~ld").fit(reml=True)
            mix = f"mixed-model slope {mm.params.ld:+.3f}±{mm.bse.ld:.3f} (p {mm.pvalues.ld:.3f})"
        except Exception as e: mix = f"mixed failed {e}"
        per = {f: round(smf.ols("lE ~ ld", g).fit().params.ld, 2) for f, g in sub.groupby("field") if len(g) > 30}
        print(f"  {lab}: n={len(sub)} fields={sub.field.nunique()} | " + ", ".join(out) + f" | {mix} | per field {per}")
    far = a[a.dist_km >= 60]; m = smf.ols("lE ~ C(field) + ld", far).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(far.blk)[0]})
    print(f"  beyond 60 km: {m.params.ld:+.3f}±{m.bse.ld:.3f}")
