"""Rescore every field's candidates with the shape-light (sl) and shape-blind (sb) models."""
import pickle, pandas as pd, numpy as np
F = [("MEN","men","candidates_scored.csv",0.70),("CHP","chp","candidates_scored.csv",0.85),("PTB","ptb","candidates_scored.csv",0.70),
     ("TM","tm","candidates_scored.csv",0.70),("PZ","pz","candidates_scored.csv",0.50),("LEE","lee","candidates_scored.csv",0.70),
     ("MO","mo","candidates_scored.csv",0.50),("LG","lg","candidates_scored.csv",0.50),("AC","ac","candidates_scored.csv",0.70),
     ("PS","ps","candidates_scored.csv",0.50),("WSH","wsh","candidates_scored.csv",0.70),("GB","gb","candidates_scored.csv",0.50),
     ("NY","drumlins","candidates_scored3.csv",0.25),("EDEN","eden","candidates_scored.csv",0.70),("BR","br","candidates_scored.csv",0.50),
     ("IRL","irl","candidates_scored.csv",0.50)]
M = {k: pickle.load(open(f"{k}_classifier.pkl", "rb")) for k in ("sl", "sb")}
rows = []
for k, d, f, thr in F:
    c = pd.read_csv(f"/home/claude/{d}/{f}"); c = c[c.height_m < 60].copy()
    for nm, m in M.items(): c["p_" + nm] = m["model"].predict_proba(c[m["feats"]].values)[:, 1]
    c[["cid", "x", "y", "length_m", "width_m", "elong", "az", "height_m", "p_drumlin", "p_sl", "p_sb"]].to_csv(f"scored_{k}.csv", index=False)
    def med(s): return f"{len(s):5d} L{s.length_m.median():5.0f} W{s.width_m.median():4.0f} E{s.elong.median():.2f}"
    o, a, b = c[c.p_drumlin >= thr], c[c.p_sl >= 0.6], c[c.p_sb >= 0.6]
    rows.append(dict(field=k, old_n=len(o), old_L=o.length_m.median(), old_W=o.width_m.median(), old_E=o.elong.median(),
                     sl_n=len(a), sl_L=a.length_m.median(), sl_W=a.width_m.median(), sl_E=a.elong.median(),
                     sb_n=len(b), sb_E=b.elong.median(), overlap=len(set(o.cid) & set(a.cid)) / max(len(o), 1)))
    print(f"{k:5s} old@{thr}: {med(o)} | shape-light@0.6: {med(a)} | shape-blind@0.6: {med(b)}")
R = pd.DataFrame(rows); R.to_csv("field_medians_compare.csv", index=False)
for p in ("old", "sl"):
    lw, ll, le = np.log(R[p + "_W"]), np.log(R[p + "_L"]), np.log(R[p + "_E"])
    print(f"{p}: between-field SD of log median W {lw.std():.3f}, L {ll.std():.3f}; range W {R[p+'_W'].min():.0f}-{R[p+'_W'].max():.0f}, L {R[p+'_L'].min():.0f}-{R[p+'_L'].max():.0f}; corr(lnE, lnL) {np.corrcoef(le, ll)[0,1]:.2f}, corr(lnE, lnW) {np.corrcoef(le, lw)[0,1]:.2f}")
from scipy.stats import spearmanr
print("rank agreement of field median E, old vs shape-light:", spearmanr(R.old_E, R.sl_E))
