import sys, pandas as pd
D = sys.argv[1]; L = {i + 1: s.split() for i, s in enumerate(sys.argv[2:])}
k = pd.read_csv(f"{D}/check/.key.csv"); k["me"] = [L[r.sheet][r.pos - 1] for r in k.itertuples()]
k.to_csv(f"{D}/check/claude_labels.csv", index=False)
print(pd.crosstab(k.grp, k.me))
for t in (0.5, 0.7, 0.85):
    s = k[k.p >= t]; print(f"thr {t}: accepted {len(s)}, precision {(s.me == 'yes').mean():.2f}; recall {(s.me == 'yes').sum() / max((k.me == 'yes').sum(), 1):.2f}")
