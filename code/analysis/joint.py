"""Puget texture test + joint 3-field fit: shape ~ model speed + model thickness + till texture, field fixed effects."""
import numpy as np, pandas as pd, statsmodels.formula.api as smf
F = {"NY": ("drumlins/tile_morph_till.csv", None, "drumlins/icemodel/run_g6.npz"),
     "GB": ("gb/tile_morph_0.5.csv", "gb/tile_till.csv", "gb/icemodel/run_gbG.npz"),
     "PS": ("ps/tile_morph_0.5_n12.csv", "ps/tile_till.csv", "ps/icemodel/run_pF.npz")}
rows = []
for f, (tm, tt, run) in F.items():
    t = pd.read_csv(tm)
    if tt: t = t.merge(pd.read_csv(tt), on="tile")
    r = np.load(run); x, y, H, sp = r["x"], r["y"], r["H"], r["sp"]; dx = x[1] - x[0]
    for _, q in t.iterrows():
        j = int(round((q.x - x[0]) / dx)); i = int(round((y[0] - q.y) / dx))
        if not (3 <= i < len(y) - 3 and 3 <= j < len(x) - 3): continue
        Hs = H[:, i, j]; full = Hs > 50; late = full & (Hs < 700)
        if late.sum() == 0: continue
        rows.append(dict(field=f, tile=q.tile, L=q.L, W=q.W, E=q.E, n=q.n, sand=q.sand, frag=q.frag, till=q.till_frac,
                         u=sp[full, i, j].mean(), ul=sp[late, i, j].mean(), Hm=Hs[full].mean(), x=q.x, y=q.y))
d = pd.DataFrame(rows).dropna()
for v in "LWE": d["l" + v] = np.log(d[v])
d["lu"], d["lul"], d["lH"] = np.log(d.u), np.log(d.ul), np.log(d.Hm)
d["ssand"], d["sfrag"] = (d.sand - 45) / 10, (d.frag - 25) / 10
print(d.groupby("field").agg(n=("tile", "size"), L=("L", "median"), W=("W", "median"), E=("E", "median"), u=("u", "median"),
                             H=("Hm", "median"), sand=("sand", "median"), stones=("frag", "median")).round(1))
print("\nPuget texture test (within field):")
p = d[d.field == "PS"]
for v in ("lL", "lW", "lE"):
    m = smf.ols(f"{v} ~ sfrag + ssand", p).fit(); print(f"  {v[1]}: stones {m.params.sfrag:+.3f} (p={m.pvalues.sfrag:.2f})  sand {m.params.ssand:+.3f} (p={m.pvalues.ssand:.2f})  R2 {m.rsquared:.2f}  n={len(p)}")
print("\nJoint fit, field fixed effects, common slopes  [cluster-robust by field-block]:")
d["blk"] = d.field + ((d.x // 20480).astype(int) * 1000 + (d.y // 20480).astype(int)).astype(str)
for v in ("lL", "lW", "lE"):
    m = smf.ols(f"{v} ~ C(field) + lu + lH + sfrag + ssand", d).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d.blk)[0]})
    print(f"  {v[1]}: speed {m.params.lu:+.2f}±{m.bse.lu:.2f}  thickness {m.params.lH:+.2f}±{m.bse.lH:.2f}  "
          f"stones {m.params.sfrag:+.3f}±{m.bse.sfrag:.3f}  sand {m.params.ssand:+.3f}±{m.bse.ssand:.3f}  R2 {m.rsquared:.2f}")
print("\nDo the speed slopes differ by field? (field x speed interaction)")
for v in ("lL", "lW", "lE"):
    a = smf.ols(f"{v} ~ C(field) + lu + lH + sfrag + ssand", d).fit(); b = smf.ols(f"{v} ~ C(field)*lu + lH + sfrag + ssand", d).fit()
    fs = b.compare_f_test(a); sl = {f: b.params.lu + b.params.get(f"C(field)[T.{f}]:lu", 0) for f in ("GB", "NY", "PS")}
    print(f"  {v[1]}: per-field speed slopes " + ", ".join(f"{k} {s:+.2f}" for k, s in sl.items()) + f"   F-test p={fs[1]:.3f}")
print("\nThickness-only per field (log shape vs log H):")
for f, g in d.groupby("field"):
    print("  ", f, {v[1]: round(np.polyfit(g.lH, g[v], 1)[0], 2) for v in ("lL", "lW", "lE")}, "r_E", round(np.corrcoef(g.lH, g.lE)[0, 1], 2))
d.to_csv("joint_tiles.csv", index=False)
