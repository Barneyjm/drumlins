"""Weighted precision of old and shape-light selections from the blind spot-check cards
(stratified: 36 cards from p_old>=0.5, 12 from p_old<0.5 & height>=3)."""
import pandas as pd, numpy as np, os
D = {"MEN":"men","CHP":"chp","PTB":"ptb","TM":"tm","PZ":"pz","LEE":"lee","MO":"mo","LG":"lg","AC":"ac","PS":"ps","WSH":"wsh","EDEN":"eden","BR":"br","IRL":"irl"}
THR = dict(MEN=.7,CHP=.85,PTB=.7,TM=.7,PZ=.5,LEE=.7,MO=.5,LG=.5,AC=.7,PS=.5,WSH=.7,EDEN=.7,BR=.5,IRL=.5)
out = []
for k, d in D.items():
    c = pd.read_csv(f"scored_{k}.csv")
    f = f"/home/claude/{d}/check/claude_labels.csv"; col = "me"
    if not os.path.exists(f): f, col = f"/home/claude/{d}/check/sonnet_labels.csv", "son"
    L = pd.read_csv(f).merge(c[["cid", "p_sl", "p_drumlin", "elong"]], on="cid", how="left")
    if L.p_sl.isna().any(): print(k, "missing", L.p_sl.isna().sum())
    L = L.dropna(subset=["p_sl"]); L["yes"] = L[col].str.lower().eq("yes")
    N = {"acc": (c.p_drumlin >= 0.5).sum(), "rej": ((c.p_drumlin < 0.5) & (c.height_m >= 3)).sum()}
    L["wt"] = L.grp.map(lambda g: N[g] / (L.grp == g).sum())
    def prec(sel):
        s = L[sel]; return (s.wt * s.yes).sum() / s.wt.sum() if len(s) else np.nan, len(s)
    po, no = prec(L.p >= THR[k]); ps_, ns = prec(L.p_sl >= 0.6)
    out.append(dict(field=k, labeller="Claude Opus" if col == "me" else "Claude Sonnet", old_prec=round(po, 2), old_cards=no, sl_prec=round(ps_, 2), sl_cards=ns,
                    sl_from_rej=int(((L.p_sl >= 0.6) & (L.grp == "rej")).sum())))
R = pd.DataFrame(out); print(R.to_string(index=False)); R.to_csv("precision_compare.csv", index=False)
T = pd.read_csv("train_cv.csv")
for f, g in T.groupby("field"):
    for nm, col, t in (("orig@0.5", "p_orig", 0.5), ("sl@0.6", "p_sl", 0.6)):
        s = g[g[col] >= t]; print(f"{f} {nm}: CV precision {s.label.mean():.2f} recall {(s.label.sum()/g.label.sum()):.2f} (n {len(s)})")
