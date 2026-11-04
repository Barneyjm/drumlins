import numpy as np, pandas as pd, statsmodels.formula.api as smf, warnings
from scipy.optimize import curve_fit
from scipy.stats import spearmanr
warnings.filterwarnings("ignore")
a = pd.read_csv("cumslip.csv"); a = a[a.S05 > 0].copy(); a["lE"] = np.log(a.elong)
cl = lambda d: dict(cov_type="cluster", cov_kwds={"groups": pd.factorize(d.blk)[0]})
for X, unit in (("S05", "sqrt(km)·ka"), ("dur_ka", "ka")):
    print(f"\n===== exposure = {X} [{unit}] =====")
    g = a.groupby("field").agg(n=("lE", "size"), X=(X, "median"), Xiqr=(X, lambda s: s.quantile(.75) - s.quantile(.25)), E=("elong", "median"))
    g["slope"] = [smf.ols(f"lE ~ np.log({X})", d).fit(**cl(d)).params[f"np.log({X})"] if d[X].std() > 0 else np.nan for _, d in a.groupby("field")]
    print(g.sort_values("X").round(2).to_string())
    ok = g.dropna(); r, p = spearmanr(ok.X, ok.slope); print(f"  1) do low-exposure fields have steeper slopes? Spearman(median exposure, per-field slope) = {r:+.2f} (p {p:.2f}); saturation predicts negative")
    r, p = spearmanr(g.X, g.E); print(f"  2) do high-exposure fields have higher median elongation? Spearman(median exposure, median E) = {r:+.2f} (p {p:.2f}); one curve predicts positive")
    # 3) pooled saturating fit on individual drumlins, field offsets allowed in log space
    f_ids = {f: i for i, f in enumerate(sorted(a.field.unique()))}; fi = a.field.map(f_ids).values; x = a[X].values; y = a.lE.values
    def sat(xx, lnEmax, lnEmin, Ss, *off):
        o = np.r_[0.0, off][fi]; return o + np.log(np.exp(lnEmin) + (np.exp(lnEmax) - np.exp(lnEmin)) * (1 - np.exp(-xx / Ss)))
    nf = len(f_ids)
    for lab, model, p0 in (("saturating + field offsets", lambda xx, *p: sat(xx, *p), [np.log(3.5), np.log(1.8), np.median(x), *np.zeros(nf - 1)]),
                           ("log-linear + field offsets", lambda xx, b, c, *off: np.r_[0.0, off][fi] + c + b * np.log(xx), [0.2, 1.0, *np.zeros(nf - 1)])):
        try:
            p, _ = curve_fit(model, x, y, p0=p0, maxfev=20000); res = y - model(x, *p); k = len(p); aic = len(y) * np.log((res ** 2).mean()) + 2 * k
            extra = f"E_max {np.exp(p[0]):.2f}, E_min {np.exp(p[1]):.2f}, S* {p[2]:.1f}" if lab.startswith("sat") else f"slope {p[0]:+.3f}"
            print(f"  3) {lab:28s}: AIC {aic:.0f}  {extra}")
        except Exception as e: print("  fit failed", lab, e)
    # 4) one curve with NO field offsets
    def sat0(xx, lnEmax, lnEmin, Ss): return np.log(np.exp(lnEmin) + (np.exp(lnEmax) - np.exp(lnEmin)) * (1 - np.exp(-xx / Ss)))
    p, _ = curve_fit(sat0, x, y, p0=[np.log(3.5), np.log(2), np.median(x)], maxfev=20000)
    res = y - sat0(x, *p); null = y - y.mean()
    print(f"  4) single curve, no field offsets: E_max {np.exp(p[0]):.2f}, E_min {np.exp(p[1]):.2f}, S* {p[2]:.1f}; R2 {1 - (res**2).sum() / (null**2).sum():.3f}; field-only R2 {smf.ols('lE ~ C(field)', a).fit().rsquared:.3f}")
