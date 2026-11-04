"""Pooled classifier: NY (James+machine) + Green Bay relabel + Puget relabel. Saved for scoring new fields."""
import glob, runpy, sys, io, os, contextlib, pickle, numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
sys.path.insert(0, "/home/claude/drumlins"); cwd = os.getcwd(); os.chdir("/home/claude/drumlins"); sys.argv = ["train3.py"]
with contextlib.redirect_stdout(io.StringIO()): g = runpy.run_path("/home/claude/drumlins/train3.py")
os.chdir(cwd); FEATS = g["FEATS"]; X, y, w = [g["X"]], [g["y"]], [g["w"]]
for D, rev in (("gb", "relabel/claude_review.csv"), ("ps", None)):
    c = pd.read_csv(f"/home/claude/{D}/candidates_scored_ny.csv" if D == "ps" else f"/home/claude/{D}/v1/candidates_scored.csv")
    key = pd.read_csv(f"/home/claude/{D}/relabel/.key.csv")
    so = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"/home/claude/{D}/relabel/sonnet_part*.csv"))]); so["label"] = so.label.str.strip().str.lower()
    L = key[["sheet", "pos", "cid"]].merge(so[["sheet", "pos", "label"]], on=["sheet", "pos"]); L["w"] = 0.5
    if rev:
        cr = pd.read_csv(f"/home/claude/{D}/{rev}"); cr["lc"] = cr.label.str.strip().str.lower()
        L = L.merge(cr[["sheet", "pos", "lc"]], on=["sheet", "pos"], how="left"); mm = L.lc.notna(); L.loc[mm, "label"] = L.loc[mm, "lc"]; L.loc[mm, "w"] = 0.75
    L = L[L.label.isin(["yes", "no"])].merge(c[["cid"] + FEATS], on="cid")
    X.append(L[FEATS].values); y.append((L.label == "yes").astype(int).values); w.append(L.w.values * 2.0); print(D, L.label.value_counts().to_dict())
m = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.06, max_iter=300, l2_regularization=1.0, min_samples_leaf=8)
m.fit(np.concatenate(X), np.concatenate(y), sample_weight=np.concatenate(w))
pickle.dump(dict(model=m, feats=FEATS), open("/home/claude/pooled_classifier.pkl", "wb")); print("saved; total labels", sum(len(a) for a in y))
