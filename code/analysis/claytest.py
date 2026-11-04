import glob, numpy as np, pandas as pd, statsmodels.formula.api as smf, warnings
warnings.filterwarnings("ignore")
fs = [pd.read_csv(f) for f in sorted(glob.glob("soil_*.csv"))]
ny = pd.read_csv("drumlins/drumlin_soils_till.csv").assign(field="NY")
d = pd.concat(fs + [ny], ignore_index=True)
d = d[(d.till_share >= 0.5) & d.clay.notna()].copy()
d["lL"], d["lW"], d["lE"] = np.log(d.length_m), np.log(d.width_m), np.log(d.elong)
d["c10"] = d.clay / 10; d["s10"] = d.sand / 10; d["f10"] = d.frag.fillna(0) / 10
d["blk20"] = d.field + "_" + (d.x // 20000).astype(int).astype(str) + "_" + (d.y // 20000).astype(int).astype(str)
d["blk5"] = d.field + "_" + (d.x // 5000).astype(int).astype(str) + "_" + (d.y // 5000).astype(int).astype(str)
cl = lambda q: dict(cov_type="cluster", cov_kwds={"groups": pd.factorize(q.blk5)[0]})
print(d.groupby("field").agg(n=("lL", "size"), clay=("clay", "median"), clay_iqr=("clay", lambda s: s.quantile(.75) - s.quantile(.25)), L=("length_m", "median")).round(1).to_string())
print("\nper 10% clay  (log units; -0.10 ~ 10% smaller)")
for spec, fe in (("within field", "C(field)"), ("within 20-km blocks", "C(blk20)")):
    for y in ("lL", "lW", "lE"):
        m = smf.ols(f"{y} ~ {fe} + c10", d).fit(**cl(d)); m2 = smf.ols(f"{y} ~ {fe} + c10 + s10 + f10", d).fit(**cl(d))
        print(f"  {spec:20s} {y}: clay {m.params.c10:+.3f} ± {m.bse.c10:.3f} (p {m.pvalues.c10:.3f}) | with sand+stones: clay {m2.params.c10:+.3f} (p {m2.pvalues.c10:.3f}), sand {m2.params.s10:+.3f} (p {m2.pvalues.s10:.3f}), stones {m2.params.f10:+.3f} (p {m2.pvalues.f10:.3f})")
print("\nper field, log L and log W on clay (within field):")
for f, g in d.groupby("field"):
    if g.clay.std() < 1 or len(g) < 60: print(f"  {f}: too little clay variation / n"); continue
    a = smf.ols("lL ~ c10", g).fit(**cl(g)); b = smf.ols("lW ~ c10", g).fit(**cl(g))
    print(f"  {f:4s} n={len(g):4d}  L {a.params.c10:+.3f} (p {a.pvalues.c10:.3f})  W {b.params.c10:+.3f} (p {b.pvalues.c10:.3f})")
fp = d.groupby("field").agg(c=("clay", "median"), L=("length_m", "median"), W=("width_m", "median")).reset_index()
bl = np.polyfit(fp.c / 10, np.log(fp.L), 1)[0]; bw = np.polyfit(fp.c / 10, np.log(fp.W), 1)[0]
print(f"\nbetween-field slope (field medians, n={len(fp)}): L {bl:+.3f}, W {bw:+.3f} per 10% clay")
