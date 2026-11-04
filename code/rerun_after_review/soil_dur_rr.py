"""Till texture and time-under-ice on the shape-light selection (soil data exist only for drumlins in the old
selection, so the texture test uses the overlap)."""
import glob, numpy as np, pandas as pd, statsmodels.formula.api as smf, warnings; warnings.filterwarnings("ignore")
fs = [pd.read_csv(f) for f in sorted(glob.glob("/home/claude/soil_*.csv"))] + [pd.read_csv("/home/claude/drumlins/drumlin_soils_till.csv").assign(field="NY")]
d = pd.concat(fs, ignore_index=True); d = d[(d.till_share >= 0.5) & d.clay.notna()]
keep = []
for f, g in d.groupby("field"):
    try: s = pd.read_csv(f"scored_{f}.csv")
    except FileNotFoundError: continue
    keep.append(g.merge(s[s.p_sl >= 0.6][["cid"]], on="cid"))
d = pd.concat(keep); d = d[d.field != "CHP"]; print("drumlins with soils in new selection:", len(d), d.field.value_counts().to_dict())
d["lL"], d["lW"], d["lE"] = np.log(d.length_m), np.log(d.width_m), np.log(d.elong)
d["c10"], d["s10"], d["f10"] = d.clay / 10, d.sand / 10, d.frag.fillna(0) / 10
d["blk20"] = d.field + "_" + (d.x // 20000).astype(int).astype(str) + "_" + (d.y // 20000).astype(int).astype(str)
d["blk5"] = d.field + "_" + (d.x // 5000).astype(int).astype(str) + "_" + (d.y // 5000).astype(int).astype(str)
cl = dict(cov_type="cluster", cov_kwds={"groups": pd.factorize(d.blk5)[0]})
for fe in ("C(field)", "C(blk20)"):
    for y in ("lL", "lW", "lE"):
        m = smf.ols(f"{y} ~ {fe} + c10 + s10 + f10", d).fit(**cl)
        print(f"{fe:9s} {y}: clay {m.params.c10:+.3f}±{m.bse.c10:.3f}  sand {m.params.s10:+.3f}±{m.bse.s10:.3f}  stones {m.params.f10:+.3f}±{m.bse.f10:.3f}")
c = pd.read_csv("cumslip.csv"); c = c[(c.dist_km < 60)].dropna(subset=["dur_ka"]); c["lE"], c["ld"] = np.log(c.elong), np.log(c.dist_km.clip(1))
clc = dict(cov_type="cluster", cov_kwds={"groups": pd.factorize(c.blk)[0]})
for fm in ("lE ~ C(field) + dur_ka", "lE ~ C(field) + ld", "lE ~ C(field) + ld + dur_ka"):
    m = smf.ols(fm, c).fit(**clc); print(fm, {k: f"{m.params[k]:+.3f}±{m.bse[k]:.3f}" for k in m.params.index if not k.startswith("C(") and k != "Intercept"}, f"n={len(c)}")
print("corr(ld, dur) near:", round(np.corrcoef(c.ld, c.dur_ka)[0, 1], 2))
