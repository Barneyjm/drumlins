"""Train a drumlin classifier on James's labels (from the labelling artifact's db export).
Usage: python3 train.py labels.json   (labels.json = {cid: "yes"|"no"|"unsure"})"""
import sys, json, numpy as np, pandas as pd
from scipy.spatial import cKDTree
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import roc_auc_score, average_precision_score, precision_recall_fscore_support

D = "/home/claude/lg"
BASE = ["area_m2", "length_m", "width_m", "elong", "az_dev", "height_m", "th2_max",
        "slope_mean", "slope_max", "fill_ratio"]


def add_context(df, r=1500.0):
    xy = df[["x", "y"]].values
    tree = cKDTree(xy)
    nb = tree.query_ball_point(xy, r)
    a2 = np.radians(2 * df.az.values)
    cnt, coh, align, hmed, strictf = [], [], [], [], []
    for i, js in enumerate(nb):
        js = [j for j in js if j != i]
        cnt.append(len(js))
        if len(js) >= 3:
            c, s = np.cos(a2[js]).mean(), np.sin(a2[js]).mean()
            coh.append(np.hypot(c, s))
            mean = np.arctan2(s, c) / 2
            d = abs(np.degrees(np.radians(df.az.values[i]) - mean)) % 180
            align.append(min(d, 180 - d))
            hmed.append(np.median(df.height_m.values[js]))
            strictf.append(df.strict.values[js].mean())
        else:
            coh.append(0); align.append(90); hmed.append(0); strictf.append(0)
    df = df.copy()
    df["nb_count"] = cnt; df["nb_coherence"] = coh; df["nb_align_dev"] = align
    df["nb_height_med"] = hmed; df["nb_strict_frac"] = strictf
    df["h_rel"] = df.height_m / (df.nb_height_med + 1)
    return df


FEATS = BASE + ["nb_count", "nb_coherence", "nb_align_dev", "nb_height_med", "nb_strict_frac", "h_rel"]


def main(path):
    lab = json.load(open(path))
    allc = add_context(pd.read_csv(f"{D}/candidates_all.csv"))
    allc.to_csv(f"{D}/candidates_ctx.csv", index=False)
    L = pd.DataFrame([(int(k), v) for k, v in lab.items()], columns=["cid", "label"])
    print(L.label.value_counts().to_dict())
    tr = allc.merge(L[L.label.isin(["yes", "no"])], on="cid")
    # drop lake-fill artifacts (filled water surfaces masquerading as tall hills)
    tr = tr[tr.height_m < 60]
    y = (tr.label == "yes").astype(int).values
    X = tr[FEATS].values
    clf = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.06, max_iter=300,
                                         l2_regularization=1.0, min_samples_leaf=8)
    cv = StratifiedKFold(5, shuffle=True, random_state=0)
    p = cross_val_predict(clf, X, y, cv=cv, method="predict_proba")[:, 1]
    print(f"n={len(y)} yes={y.sum()}  CV ROC-AUC {roc_auc_score(y, p):.3f}  PR-AUC {average_precision_score(y, p):.3f}")
    for name, pred in (("model@0.5", p >= 0.5), ("old strict rule", tr.strict.values == 1)):
        pr, rc, f1, _ = precision_recall_fscore_support(y, pred, average="binary", zero_division=0)
        print(f"  {name:16s} precision {pr:.2f} recall {rc:.2f} F1 {f1:.2f}")
    clf.fit(X, y)
    allc["p_drumlin"] = clf.predict_proba(allc[FEATS].values)[:, 1]
    allc.to_csv(f"{D}/candidates_scored.csv", index=False)
    print("field-wide: p>=0.5:", int((allc.p_drumlin >= 0.5).sum()), "of", len(allc),
          "| old strict:", int(allc.strict.sum()))
    # active-learning queue: most uncertain unlabelled candidates for a second round
    un = allc[~allc.cid.isin(L.cid)].copy()
    un["unc"] = -abs(un.p_drumlin - 0.5)
    un.sort_values("unc", ascending=False).head(150).to_csv(f"{D}/next_round.csv", index=False)


if __name__ == "__main__":
    main(sys.argv[1])
