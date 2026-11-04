"""Combine James's labels (weight 1) with machine labels (Sonnet 0.5, Claude review 0.75).
Evaluate ONLY on James's labels in held-out 10 km blocks; compare with a James-only model."""
import json, glob, sys, numpy as np, pandas as pd
from scipy.spatial import cKDTree
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score, average_precision_score, precision_recall_fscore_support
from train import FEATS

W_SONNET, W_CLAUDE = 0.5, 0.75
new = pd.read_csv("candidates_ctx_closed3.csv")
cid2idx = {c: k for k, c in enumerate(new.cid.values)}


def model():
    return HistGradientBoostingClassifier(max_depth=3, learning_rate=0.06, max_iter=300,
                                          l2_regularization=1.0, min_samples_leaf=8)


# --- James (rounds 1 + 2)
lab1 = json.load(open("labels_round1.json")); orig = pd.read_csv("candidates_ctx.csv")
L1 = orig[orig.cid.astype(str).isin(lab1)].copy(); L1["label"] = L1.cid.astype(str).map(lab1)
d, i = cKDTree(new[["x", "y"]].values).query(L1[["x", "y"]].values)
L1 = L1[d < 150].assign(nidx=i[d < 150])[["nidx", "label"]]
lab2 = json.load(open("labels_round2.json")); S2 = pd.read_csv("label_sample_r2.csv")
L2 = pd.DataFrame(dict(nidx=[cid2idx[c] for c in S2.cid], label=S2.rid.map(lab2)))
J = pd.concat([L1, L2]).query("label in ['yes','no']").drop_duplicates("nidx", keep="last").assign(w=1.0, src="james")
# --- machine labels for round 3
key = pd.read_csv("ai_label/.key_r3.csv")
so = pd.concat([pd.read_csv(f) for f in sorted(glob.glob("ai_label/sonnet_r3_part*.csv"))])
so["label"] = so.label.str.strip().str.lower()
M = key.merge(so[["sheet", "pos", "label"]], on=["sheet", "pos"])
M["src"] = "sonnet"; M["w"] = W_SONNET
rev = sorted(glob.glob("ai_label/claude_r3_review*.csv"))
if rev:
    cr = pd.concat([pd.read_csv(f) for f in rev]); cr["label_c"] = cr.label.str.strip().str.lower()
    M = M.merge(cr[["sheet", "pos", "label_c"]], on=["sheet", "pos"], how="left")
    m = M.label_c.notna()
    M.loc[m, "label"] = M.loc[m, "label_c"]; M.loc[m, "src"] = "claude"; M.loc[m, "w"] = W_CLAUDE
M["nidx"] = [cid2idx[int(r[3:])] for r in M.rid]
print("round-3 machine labels:", M.groupby(["src", "label"]).size().to_dict())
Mk = M.query("label in ['yes','no']")[["nidx", "label", "w", "src"]]
A = pd.concat([J, Mk]).drop_duplicates("nidx", keep="first")
A = A[new.height_m.values[A.nidx] < 60].reset_index(drop=True)
X = new.iloc[A.nidx.values][FEATS].values; y = (A.label == "yes").astype(int).values; w = A.w.values
isJ = (A.src == "james").values
blocks = (new.x.values[A.nidx] // 10000).astype(int) * 1000 + (new.y.values[A.nidx] // 10000).astype(int)
el = new.elong.values[A.nidx]


def evaluate(use_machine):
    p = np.full(len(y), np.nan)
    for tr, te in GroupKFold(5).split(X, y, blocks):
        trm = tr if use_machine else tr[isJ[tr]]
        mdl = model().fit(X[trm], y[trm], sample_weight=w[trm])
        te = te[isJ[te]]
        p[te] = mdl.predict_proba(X[te])[:, 1]
    k = isJ
    pr, rc, f1, _ = precision_recall_fscore_support(y[k], p[k] >= .5, average="binary", zero_division=0)
    short = k & (el < 1.7) & (y == 1); long_ = k & (el >= 1.7) & (y == 1)
    return dict(auc=roc_auc_score(y[k], p[k]), prauc=average_precision_score(y[k], p[k]), P=pr, R=rc, F1=f1,
                R_short=(p[short] >= .5).mean(), R_long=(p[long_] >= .5).mean())


for nm, um in (("James labels only", False), ("James + machine labels", True)):
    r = evaluate(um)
    print(f"{nm:24s} AUC {r['auc']:.3f} PR-AUC {r['prauc']:.3f} P {r['P']:.2f} R {r['R']:.2f} F1 {r['F1']:.2f} | recall short {r['R_short']:.2f} long {r['R_long']:.2f}")
print(f"training rows: James {int(isJ.sum())}, machine {int((~isJ).sum())}")
if "--fit" in sys.argv:
    mf = model().fit(X, y, sample_weight=w)
    new["p_drumlin"] = mf.predict_proba(new[FEATS].values)[:, 1]
    new.loc[new.height_m >= 60, "p_drumlin"] = 0.0
    new.to_csv("candidates_scored3.csv", index=False)
    print("field-wide drumlins (p>=0.5):", int((new.p_drumlin >= .5).sum()))


def sweep():
    out = {}
    for um in (False, True):
        p = np.full(len(y), np.nan)
        for tr, te in GroupKFold(5).split(X, y, blocks):
            trm = tr if um else tr[isJ[tr]]
            mdl = model().fit(X[trm], y[trm], sample_weight=w[trm]); te = te[isJ[te]]
            p[te] = mdl.predict_proba(X[te])[:, 1]
        out[um] = p
    for t in (0.5, 0.4, 0.35, 0.3, 0.25):
        line = f"thr {t:.2f} |"
        for um, nm in ((False, "James-only"), (True, "combined")):
            p = out[um]; k = isJ
            pr, rc, f1, _ = precision_recall_fscore_support(y[k], p[k] >= t, average="binary", zero_division=0)
            sh = k & (el < 1.7) & (y == 1)
            line += f" {nm}: P {pr:.2f} R {rc:.2f} F1 {f1:.2f} Rshort {(p[sh] >= t).mean():.2f} |"
        print(line)


if "--sweep" in sys.argv:
    sweep()
