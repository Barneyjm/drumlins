import sys, pandas as pd
rows = [l.split() for l in open(sys.argv[1]) if l.strip()]
for f in dict.fromkeys(r[0] for r in rows):
    L = {int(r[1]): r[2:] for r in rows if r[0] == f}
    k = pd.read_csv(f"/home/claude/{f}/check/.key.csv"); k["son"] = [L[r.sheet][r.pos - 1] for r in k.itertuples()]
    k.to_csv(f"/home/claude/{f}/check/sonnet_labels.csv", index=False)
    out = [f"{t}: prec {(k[k.p >= t].son == 'yes').mean():.2f} (n {len(k[k.p >= t])})" for t in (0.5, 0.7, 0.85)]
    print(f, "| yes among rejected", (k[k.grp == "rej"].son == "yes").mean().round(2), "|", "; ".join(out))
