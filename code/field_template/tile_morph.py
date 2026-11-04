import pandas as pd, numpy as np, rasterio, sys
f = sys.argv[1] if len(sys.argv) > 1 else "candidates_scored.csv"
s = pd.read_csv(f"/home/claude/lg/{f}")
b = rasterio.open("/home/claude/lg/data/ny_dem_20m.tif").bounds; T = 10240
for thr in (0.5, 0.7, 0.9):
    d = s[(s.p_drumlin >= thr) & (s.height_m < 60)].copy()
    d["c"] = ((d.x - b.left) // T).astype(int); d["r"] = ((b.top - d.y) // T).astype(int)
    g = d.groupby(["r", "c"]).agg(n=("cid", "size"), L=("length_m", "median"), W=("width_m", "median"), E=("elong", "median")).reset_index()
    g = g[g.n >= int(sys.argv[2]) if len(sys.argv) > 2 else g.n >= 20]; g["tile"] = g.r * 100 + g.c; g["x"] = b.left + (g.c + .5) * T; g["y"] = b.top - (g.r + .5) * T
    g[["tile", "n", "L", "W", "E", "x", "y", "r", "c"]].to_csv(f"/home/claude/lg/tile_morph_{thr}.csv", index=False); print(thr, len(g), "tiles")
