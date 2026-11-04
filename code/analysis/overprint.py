"""Overprinting test: per-tile orientation spread and two-generation (bimodal) signal; does it explain shape?"""
import numpy as np, pandas as pd, statsmodels.formula.api as smf, sys
FIELDS = {"NY": ("drumlins/candidates_scored3.csv", 0.25, "drumlins/tile_morph_till.csv", "drumlins/tile_conv_20km.csv"),
          "GB": ("gb/candidates_scored.csv", 0.5, "gb/tile_morph_0.5.csv", "gb/tile_conv_0.5_20km.csv"),
          "PS": ("ps/candidates_scored.csv", 0.5, "ps/tile_morph_0.5_n12.csv", None)}
for a in sys.argv[1:]:
    k, c, thr, tm, tc = a.split(","); FIELDS[k] = (c, float(thr), tm, tc if tc != "-" else None)

def vm_fit(th, K=2, it=200, seed=0):
    """EM for a K-component von Mises mixture on doubled axial angles th (rad, in [0, 2pi))."""
    from scipy.special import i0e, i1e
    rng = np.random.default_rng(seed); n = len(th)
    mu = rng.uniform(0, 2 * np.pi, K) if K > 1 else np.array([np.angle(np.exp(1j * th).mean())])
    if K == 2: mu = np.array([np.angle(np.exp(1j * th).mean()) - 0.6, np.angle(np.exp(1j * th).mean()) + 0.6])
    kap = np.full(K, 2.0); w = np.full(K, 1 / K)
    for _ in range(it):
        lp = np.log(w) + kap * np.cos(th[:, None] - mu) - np.log(2 * np.pi * i0e(kap)) - kap
        m = lp.max(1, keepdims=True); r = np.exp(lp - m); r /= r.sum(1, keepdims=True)
        w = r.mean(0).clip(1e-6); C = (r * np.cos(th[:, None])).sum(0); S = (r * np.sin(th[:, None])).sum(0)
        mu = np.arctan2(S, C); Rb = np.hypot(C, S) / r.sum(0).clip(1e-9)
        kap = np.clip(np.where(Rb < 0.53, 2 * Rb + Rb ** 3 + 5 * Rb ** 5 / 6, np.where(Rb < 0.85, -0.4 + 1.39 * Rb + 0.43 / (1 - Rb), 1 / (Rb ** 3 - 4 * Rb ** 2 + 3 * Rb + 1e-9))), 0.01, 500)
    lp = np.log(w) + kap * np.cos(th[:, None] - mu) - np.log(2 * np.pi * i0e(kap)) - kap
    m = lp.max(1); ll = (m + np.log(np.exp(lp - m[:, None]).sum(1))).sum()
    return ll, mu, kap, w

import os; EMIN = float(os.environ.get("EMIN", 0))
rows = []
for f, (cf, thr, tm, tc) in FIELDS.items():
    s = pd.read_csv(cf); d = s[(s.p_drumlin >= thr) & (s.height_m < 60)].copy()
    d["tile"] = (d.row // 512).astype(int) * 100 + (d.col // 512).astype(int)
    t = pd.read_csv(tm)
    if tc: t = t.merge(pd.read_csv(tc)[["tile", "conv"]], on="tile", how="left")
    for _, q in t.iterrows():
        a = np.radians((d.loc[(d.tile == q.tile) & (d.elong >= EMIN), "az"].values % 180) * 2)
        if len(a) < 12: continue
        R = abs(np.exp(1j * a).mean()); spread = np.degrees(np.sqrt(-2 * np.log(max(R, 1e-6))) / 2)
        l1 = vm_fit(a, 1)[0]; l2, mu, kap, w = max((vm_fit(a, 2, seed=s_) for s_ in range(3)), key=lambda z: z[0])
        dbic = (l2 - l1) - 0.5 * 3 * np.log(len(a))                 # >0 favours two generations (BIC)
        sep = abs(np.degrees((mu[0] - mu[1] + np.pi) % (2 * np.pi) - np.pi) / 2)
        two = (dbic > 0) and (w.min() >= 0.2) and (sep >= 20)
        rows.append(dict(field=f, tile=q.tile, n=len(a), E=q.E, L=q.L, W=q.W, conv=q.get("conv", np.nan), spread=spread, dbic=dbic, sep=sep, minor=w.min(), two=two))
o = pd.DataFrame(rows); o.to_csv("overprint_tiles.csv", index=False)
print(o.groupby("field").agg(tiles=("tile", "size"), spread_med=("spread", "median"), two_gen_frac=("two", "mean"), sep_med=("sep", "median")).round(2))
print("\nWithin-field: does orientation spread / two generations predict shape?")
for f, g in o.groupby("field"):
    g = g.assign(lE=np.log(g.E), lL=np.log(g.L), lW=np.log(g.W))
    out = []
    for v in ("lE", "lL", "lW"):
        r = np.corrcoef(g.spread, g[v])[0, 1]; dt = g.loc[g.two, v].mean() - g.loc[~g.two, v].mean() if g.two.any() and (~g.two).any() else np.nan
        out.append(f"{v[1]}: r(spread)={r:+.2f}, two-gen minus one-gen {dt:+.2f}")
    print(f"  {f} ({len(g)} tiles): " + "; ".join(out))
    if g.conv.notna().sum() > 10:
        h = g.dropna(subset=["conv"]); a = smf.ols("lE ~ conv", h).fit(); b = smf.ols("lE ~ conv + spread + two", h).fit()
        print(f"     convergence slope on log E: {a.params.conv:+.2f} (p {a.pvalues.conv:.3f}) -> with overprinting controls {b.params.conv:+.2f} (p {b.pvalues.conv:.3f})")
