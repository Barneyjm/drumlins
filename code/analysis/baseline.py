import numpy as np, pandas as pd, statsmodels.formula.api as smf
from scipy.stats import spearmanr
d = pd.read_csv("fieldprops_dem.csv"); d = d[d.field != "BRD"]
d = d.merge(pd.read_csv("fieldprops_exp.csv"), on="field", how="left")
soil = pd.read_csv("fieldprops_soil.csv").drop_duplicates("field", keep="last"); d = d.merge(soil.drop(columns="n_pts"), on="field", how="left")
LITH = dict(NY="sed", GB="carb", PS="unconsol", AC="sed", BR="sed", LG="cryst", PZ="cryst", TM="cryst", MO="sed", IRL="sed", EDEN="sed",
            MEN="carb", LEE="sed", CHP="cryst", WSH="sed", PTB="carb")
SHEET = dict(PS="Cordilleran", MO="Patagonian", IRL="BIIS", EDEN="BIIS")
d["lith"] = d.field.map(LITH); d["sheet"] = d.field.map(SHEET).fillna("Laurentide")
d["lE"] = np.log(d.E); d["lL"] = np.log(d.L); d["lW"] = np.log(d.W)
d.to_csv("baseline_fields.csv", index=False)
print(d[["field", "n", "E", "L", "W", "H", "relief", "slope_along", "density", "dist", "S05", "sand", "stones", "clay", "lith", "sheet"]].round(2).sort_values("E").to_string(index=False))
print(f"\n{len(d)} fields; Spearman rank correlation of median elongation with each property:")
res = []
for p in ("H", "L", "W", "relief", "slope_along", "density", "elev", "lat", "dist", "S05", "dur", "sand", "stones", "clay", "till_frac"):
    g = d.dropna(subset=[p]); r, pv = spearmanr(g[p], g.E); res.append((p, len(g), r, pv))
for p, n, r, pv in sorted(res, key=lambda x: x[3]): print(f"  {p:12s} n={n:2d}  rho={r:+.2f}  p={pv:.3f}")
print("\nby bedrock class (median E):", d.groupby("lith").E.agg(["size", "median"]).round(2).to_dict("index"))
print("by ice sheet:", d.groupby("sheet").E.agg(["size", "median"]).round(2).to_dict("index"))
m = smf.ols("lE ~ C(lith)", d).fit(); print(f"lithology ANOVA p={m.f_pvalue:.3f}, R2={m.rsquared:.2f}")
