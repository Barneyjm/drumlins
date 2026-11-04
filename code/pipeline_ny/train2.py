"""Combined training on road-filled candidates (rounds 1+2), honest evaluation, field scoring."""
import json, numpy as np, pandas as pd
from scipy.spatial import cKDTree
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.metrics import roc_auc_score, average_precision_score, precision_recall_fscore_support
from train import FEATS

def model():
    return HistGradientBoostingClassifier(max_depth=3, learning_rate=0.06, max_iter=300,
                                          l2_regularization=1.0, min_samples_leaf=8)

new = pd.read_csv("candidates_ctx_closed3.csv")
# ---- round 1 labels, transferred to road-filled candidates
lab1 = json.load(open("labels_round1.json"))
orig = pd.read_csv("candidates_ctx.csv")
L1 = orig[orig.cid.astype(str).isin(lab1)].copy(); L1["label"] = L1.cid.astype(str).map(lab1)
d, i = cKDTree(new[["x", "y"]].values).query(L1[["x", "y"]].values)
L1 = L1[d < 150].assign(nidx=i[d < 150])[["nidx", "label"]].assign(rnd=1)
# ---- round 2 labels, native
lab2 = json.load(open("labels_round2.json"))
S2 = pd.read_csv("label_sample_r2.csv"); S2["label"] = S2.rid.map(lab2)
cid2idx = {c: k for k, c in enumerate(new.cid.values)}
L2 = pd.DataFrame(dict(nidx=[cid2idx[c] for c in S2.cid], label=S2.label, rnd=2, why=S2.why.values, p_r1=S2.p.values))
A = pd.concat([L1, L2], ignore_index=True)
A = A[A.label.isin(["yes", "no"])].drop_duplicates("nidx", keep="last")
A = A[new.height_m.values[A.nidx] < 60]
X = new.iloc[A.nidx.values][FEATS].values; y = (A.label == "yes").astype(int).values
print(f"training set: {len(y)} ({y.sum()} drumlins) — round1 {int((A.rnd==1).sum())}, round2 {int((A.rnd==2).sum())}")

# ---- 1) out-of-sample: round-1-only model scored on round-2 labels
r1 = A.rnd == 1
m1 = model().fit(X[r1], y[r1]); p12 = m1.predict_proba(X[~r1])[:, 1]
pr, rc, f1, _ = precision_recall_fscore_support(y[~r1], p12 >= .5, average="binary", zero_division=0)
print(f"round-1 model on round-2 cards (hard cases by design): ROC-AUC {roc_auc_score(y[~r1], p12):.2f}  P {pr:.2f} R {rc:.2f}")
R2 = A[~r1].assign(y=y[~r1], p=p12)
rd = R2[R2.why == "rounded"]
print(f"  rounded herd hills you called drumlins: {int(rd.y.sum())}/{len(rd)}; round-1 model accepted {int(((rd.p>=.5)&(rd.y==1)).sum())} of those")

# ---- 2) spatial-block CV on everything (10 km blocks so neighbours can't leak)
blocks = (new.x.values[A.nidx] // 10000).astype(int) * 1000 + (new.y.values[A.nidx] // 10000).astype(int)
p = cross_val_predict(model(), X, y, cv=GroupKFold(5), groups=blocks, method="predict_proba")[:, 1]
pr, rc, f1, _ = precision_recall_fscore_support(y, p >= .5, average="binary", zero_division=0)
print(f"combined, spatial-block CV: ROC-AUC {roc_auc_score(y, p):.3f}  PR-AUC {average_precision_score(y, p):.3f}  P {pr:.2f} R {rc:.2f} F1 {f1:.2f}")
el = new.elong.values[A.nidx]
for nm, m in (("elongation < 1.7", el < 1.7), ("elongation >= 1.7", el >= 1.7)):
    if (y[m] == 1).sum():
        print(f"  recall on drumlins with {nm}: {((p[m] >= .5) & (y[m] == 1)).sum() / (y[m] == 1).sum():.2f} (n={int((y[m]==1).sum())})")

# ---- 3) final model, field-wide
mf = model().fit(X, y)
new["p_drumlin"] = mf.predict_proba(new[FEATS].values)[:, 1]
new.loc[new.height_m >= 60, "p_drumlin"] = 0.0
new.to_csv("candidates_scored2.csv", index=False)
herd = (new.nb_coherence > 0.6) & (new.nb_count >= 8)
rnd_ = herd & (new.elong < 1.7) & new.height_m.between(5, 30)
p_old = m1.predict_proba(new[FEATS].values)[:, 1]
print(f"field-wide drumlins (p>=0.5): {int((new.p_drumlin>=.5).sum())} of {len(new)}")
print(f"rounded herd hills accepted: round-1 model {np.mean(p_old[rnd_]>=.5):.2f} -> combined {np.mean(new.p_drumlin[rnd_]>=.5):.2f}; all herd members {np.mean(p_old[herd]>=.5):.2f} -> {np.mean(new.p_drumlin[herd]>=.5):.2f}")
