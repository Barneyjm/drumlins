"""Shape-blind pooled classifier: same labels as pooled_train.py, but without features that encode
length, width, elongation or orientation. Blocked CV compares it with the original feature set."""
import glob, runpy, sys, io, os, contextlib, pickle, numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score, average_precision_score
sys.path.insert(0, "/home/claude/drumlins"); cwd = os.getcwd(); os.chdir("/home/claude/drumlins"); sys.argv = ["train3.py"]
with contextlib.redirect_stdout(io.StringIO()): g = runpy.run_path("/home/claude/drumlins/train3.py")
os.chdir(cwd); FEATS = list(g["FEATS"])
A, new = g["A"], g["new"]
ny = new.iloc[A.nidx.values][FEATS + ["x", "y"]].reset_index(drop=True)
parts = [ny.assign(label=g["y"], w=g["w"], field="NY")]
for D, rev in (("gb", "relabel/claude_review.csv"), ("ps", None)):
    c = pd.read_csv(f"/home/claude/{D}/candidates_scored_ny.csv" if D == "ps" else f"/home/claude/{D}/v1/candidates_scored.csv")
    key = pd.read_csv(f"/home/claude/{D}/relabel/.key.csv")
    so = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"/home/claude/{D}/relabel/sonnet_part*.csv"))]); so["label"] = so.label.str.strip().str.lower()
    L = key[["sheet", "pos", "cid"]].merge(so[["sheet", "pos", "label"]], on=["sheet", "pos"]); L["w"] = 0.5
    if rev:
        cr = pd.read_csv(f"/home/claude/{D}/{rev}"); cr["lc"] = cr.label.str.strip().str.lower()
        L = L.merge(cr[["sheet", "pos", "lc"]], on=["sheet", "pos"], how="left"); mm = L.lc.notna(); L.loc[mm, "label"] = L.loc[mm, "lc"]; L.loc[mm, "w"] = 0.75
    L = L[L.label.isin(["yes", "no"])].merge(c[["cid"] + FEATS + ["x", "y"]], on="cid")
    parts.append(L[FEATS + ["x", "y"]].assign(label=(L.label == "yes").astype(int).values, w=L.w.values * 2.0, field=D.upper()))
T = pd.concat(parts, ignore_index=True)
SHAPE = {"length_m", "width_m", "elong", "az_dev", "nb_coherence", "nb_align_dev", "nb_strict_frac"}
SB = [f for f in FEATS if f not in SHAPE]
print("labels", len(T), T.groupby("field").label.agg(["size", "sum"]).to_dict("index"))
print("shape-blind features:", SB)
blocks = T.field + "_" + (T.x // 10000).astype(int).astype(str) + "_" + (T.y // 10000).astype(int).astype(str)
mk = lambda: HistGradientBoostingClassifier(max_depth=3, learning_rate=0.06, max_iter=300, l2_regularization=1.0, min_samples_leaf=8)
SL = [f for f in FEATS if f not in {"length_m", "width_m", "elong"}]
print("shape-light features:", SL)
res = {}
for name, F in (("original", FEATS), ("shape-light", SL), ("shape-blind", SB)):
    p = np.zeros(len(T))
    for tr, te in GroupKFold(5).split(T, T.label, blocks):
        p[te] = mk().fit(T[F].values[tr], T.label.values[tr], sample_weight=T.w.values[tr]).predict_proba(T[F].values[te])[:, 1]
    res[name] = p; y = T.label.values
    print(f"\n{name}: ROC-AUC {roc_auc_score(y, p):.3f}  PR-AUC {average_precision_score(y, p):.3f}")
    for t in (0.3, 0.4, 0.5, 0.6, 0.7):
        k = p >= t; print(f"  t={t}: precision {y[k].mean():.2f} recall {k[y == 1].mean():.2f} | median E of accepted {np.median(T.elong[k]):.2f} vs all true {np.median(T.elong[y == 1]):.2f}")
    print("  Spearman(p, E) among true drumlins:", round(pd.Series(p[y == 1]).corr(T.elong[y == 1].reset_index(drop=True), method="spearman"), 2))
for nm, F in (("sb", SB), ("sl", SL)):
    m = mk().fit(T[F].values, T.label.values, sample_weight=T.w.values)
    pickle.dump(dict(model=m, feats=F), open(f"/home/claude/rerun/{nm}_classifier.pkl", "wb"))
T.assign(p_orig=res["original"], p_sl=res["shape-light"], p_sb=res["shape-blind"]).to_csv("/home/claude/rerun/train_cv.csv", index=False)
