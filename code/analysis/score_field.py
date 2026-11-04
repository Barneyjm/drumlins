import sys, pickle, runpy, warnings, pandas as pd; warnings.filterwarnings("ignore")
D = sys.argv[1]; sys.argv = ["x"]
add_context = runpy.run_path("/home/claude/gb/train.py", run_name="lib")["add_context"]
m = pickle.load(open("/home/claude/pooled_classifier.pkl", "rb"))
c = add_context(pd.read_csv(f"{D}/candidates_all_closed3.csv"))
c["p_drumlin"] = m["model"].predict_proba(c[m["feats"]].values)[:, 1]; c.loc[c.height_m >= 60, "p_drumlin"] = 0
c.to_csv(f"{D}/candidates_scored.csv", index=False)
k = c[c.p_drumlin >= 0.5]
print(D, "accepted p>=0.5:", len(k), "p>=0.8:", (c.p_drumlin >= 0.8).sum(), k[["length_m", "width_m", "elong", "height_m"]].median().round(1).to_dict())
