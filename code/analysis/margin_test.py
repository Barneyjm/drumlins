import numpy as np, pandas as pd, statsmodels.formula.api as smf, sys
m = pd.read_csv("margin_tiles.csv"); o = pd.read_csv("overprint_tiles.csv")
d = o.merge(m, on=["field", "tile"])
d["lE"], d["lL"], d["lW"], d["ld"] = np.log(d.E), np.log(d.L), np.log(d.W), np.log(d.dist_margin_km)
for f, g in d.groupby("field"):
    out = []
    for v in ("lE", "lL", "lW"):
        r = np.corrcoef(g.ld, g[v])[0, 1]; s = np.polyfit(g.ld, g[v], 1)[0]; out.append(f"{v[1]} r={r:+.2f} slope={s:+.2f}")
    near = g[g.dist_margin_km < 40]; far = g[g.dist_margin_km >= 40]
    print(f"{f} ({len(g)} tiles, {g.dist_margin_km.min():.0f}-{g.dist_margin_km.max():.0f} km): " + "; ".join(out),
          f"| E within 40 km {near.E.median() if len(near) else float('nan'):.2f} (n={len(near)}) vs beyond {far.E.median() if len(far) else float('nan'):.2f} (n={len(far)})")
    if g.conv.notna().sum() > 10:
        h = g.dropna(subset=["conv"]); b = smf.ols("lE ~ conv + ld", h).fit()
        print(f"    log E ~ conv + log dist: conv {b.params.conv:+.2f} (p {b.pvalues.conv:.3f}), dist {b.params.ld:+.2f} (p {b.pvalues.ld:.3f})")
