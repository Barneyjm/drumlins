import numpy as np, pandas as pd, statsmodels.formula.api as smf, warnings
warnings.filterwarnings("ignore")
a = pd.read_csv("cumslip.csv"); a = a[(a.S05 > 0)].copy()
a["lE"], a["lL"], a["lW"] = np.log(a.elong), np.log(a.length_m), np.log(a.width_m)
for c in ("S0", "S05", "S1"): a["l" + c] = np.log(a[c])
a["ld"] = np.log(a.dist_km.clip(1)); a["ld60"] = np.minimum(a.ld, np.log(60))
cl = lambda d: dict(cov_type="cluster", cov_kwds={"groups": pd.factorize(d.blk)[0]})
m0 = smf.ols("lE ~ C(field)", a).fit()
print(f"n={len(a)} drumlins, {a.field.nunique()} fields\n")
print("single predictors (field fixed effects; within-field dR2; per-field slopes; shared-slope F test):")
for p in ("lS0", "lS05", "lS1", "ld", "ld60"):
    m = smf.ols(f"lE ~ C(field) + {p}", a).fit(**cl(a)); full = smf.ols(f"lE ~ C(field)*{p}", a).fit()
    F = full.compare_f_test(smf.ols(f"lE ~ C(field) + {p}", a).fit())
    per = {f: round(smf.ols(f"lE ~ {p}", g).fit().params[p], 2) for f, g in a.groupby("field")}
    print(f"  {p:5s} slope {m.params[p]:+.3f} ± {m.bse[p]:.3f} (p {m.pvalues[p]:.4f}) dR2 {m.rsquared - m0.rsquared:.4f} | {per} | shared p={F[1]:.2g}")
print("\nhead-to-head:")
for fm in ("lE ~ C(field) + lS05 + ld60", "lE ~ C(field) + lS05 + lS0", "lE ~ C(field) + lS05 + ld60 + lS0"):
    m = smf.ols(fm, a).fit(**cl(a)); print(f"  {fm:34s}", {k: f"{m.params[k]:+.3f} (p {m.pvalues[k]:.3f})" for k in m.params.index if not k.startswith("C(") and k != "Intercept"}, f"AIC {m.aic:.0f}")
print("\nlength and width vs cumulative slip:")
for y in ("lL", "lW"):
    m = smf.ols(f"{y} ~ C(field) + lS05", a).fit(**cl(a)); print(f"  {y}: {m.params.lS05:+.3f} (p {m.pvalues.lS05:.4f})")
print("\nleave-one-field-out: slope fitted on other fields, r(predicted, observed within-field log E):")
for p in ("lS05", "ld60", "lS0"):
    out = []
    for f in sorted(a.field.unique()):
        tr, te = a[a.field != f], a[a.field == f]; b = smf.ols(f"lE ~ C(field) + {p}", tr).fit().params[p]
        out.append(f"{f} {np.corrcoef(b * te[p], te.lE)[0, 1] * np.sign(b):+.2f}")
    print(f"  {p:5s} (slope {smf.ols(f'lE ~ C(field) + {p}', a).fit().params[p]:+.3f}): " + ", ".join(out))
print("\nmargin effect explained? slope of log E on log distance near (<60 km) and far, before and after controlling for cumulative slip:")
for lab, d in (("near <60 km", a[a.dist_km < 60]), ("far >=60 km", a[a.dist_km >= 60])):
    m1 = smf.ols("lE ~ C(field) + ld", d).fit(**cl(d)); m2 = smf.ols("lE ~ C(field) + ld + lS05", d).fit(**cl(d))
    print(f"  {lab}: dist {m1.params.ld:+.3f} (p {m1.pvalues.ld:.3f}) -> with slip: dist {m2.params.ld:+.3f} (p {m2.pvalues.ld:.3f}), slip {m2.params.lS05:+.3f} (p {m2.pvalues.lS05:.3f})")
