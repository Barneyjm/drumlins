"""High-recall candidate generation + features + stratified labelling sample + chips."""
import sys, json, os, numpy as np, pandas as pd, rasterio
from scipy import ndimage as ndi
sys.path.insert(0, "/home/claude/drumlins")
from detect import detect, tophat_relief
from PIL import Image, ImageDraw

D = "/home/claude/drumlins"; DX = 20.0; T = 512; HALO = 64
PRE = int(os.environ.get("PRE_CLOSE", "0")); SUF = os.environ.get("SUF", "")


def load():
    with rasterio.open(f"{D}/data/ny_dem_20m.tif") as s:
        z = s.read(1); water = s.read(2) > 0.5; tr = s.transform
    valid = np.isfinite(z) & ~water
    zz = np.where(valid, z, 0.0)
    num = ndi.gaussian_filter(zz, 25); den = ndi.gaussian_filter(valid.astype(float), 25)
    zf = np.where(valid, z, num / np.maximum(den, 1e-6))
    return zf, valid, tr


def flow_lookup():
    W = pd.read_csv(f"{D}/ny_windows.csv")
    rr = (W.row + 384).values; cc = (W.col + 384).values; az = W.flow_az.values
    def f(r, c):
        return float(az[np.argmin((rr - r) ** 2 + (cc - c) ** 2)])
    return f


def main():
    zf, valid, tr = load()
    H, Wd = zf.shape
    flow = flow_lookup()
    th_full = tophat_relief(zf, DX)
    th2 = tophat_relief(zf, DX, 2000.0)
    gy, gx = np.gradient(ndi.gaussian_filter(zf, 1), DX)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    rows = []
    cid = 0
    for r in range(0, H, T):
        for c in range(0, Wd, T):
            ra, rb = max(r - HALO, 0), min(r + T + HALO, H)
            ca, cb = max(c - HALO, 0), min(c + T + HALO, Wd)
            v = valid[ra:rb, ca:cb]
            if v.mean() < 0.3:
                continue
            fa = flow(r + T / 2, c + T / 2)
            lab, P = detect(zf[ra:rb, ca:cb], DX, valid=v, flow_az=None, h_thresh=1.5, h_split=1.5,
                            h_peak=3.0, min_area=0.005e6, max_area=5e6, min_elong=0.0,
                            pre_close_px=PRE)
            for p in P:
                gr, gc = p["row"] + ra, p["col"] + ca
                if not (r <= gr < r + T and c <= gc < c + T):
                    continue                      # keep only core-tile centroids (no duplicates)
                m = lab == p["label"]
                rr_, cc_ = np.nonzero(m)
                d = abs(p["az"] - fa) % 180; d = min(d, 180 - d)
                x, y = tr * (gc, gr)
                rows.append(dict(cid=cid, row=gr, col=gc, x=x, y=y, area_m2=p["area_m2"],
                                 length_m=p["length_m"], width_m=p["width_m"],
                                 elong=p["length_m"] / max(p["width_m"], 1), az=p["az"], flow_az=fa,
                                 az_dev=d, height_m=p["height_m"],
                                 th2_max=float(th2[rr_ + ra, cc_ + ca].max()),
                                 slope_mean=float(slope[rr_ + ra, cc_ + ca].mean()),
                                 slope_max=float(slope[rr_ + ra, cc_ + ca].max()),
                                 fill_ratio=float(m.sum() * DX * DX / (np.pi / 4 * p["length_m"] * p["width_m"])),
                                 strict=int(p["height_m"] >= 6 and p["length_m"] / max(p["width_m"], 1) >= 1.3 and d <= 30)))
                cid += 1
    df = pd.DataFrame(rows)
    df.to_csv(f"{D}/candidates_all{SUF}.csv", index=False)
    print(len(df), "candidates;", int(df.strict.sum()), "pass the old strict filter")
    if SUF: return
    # ---- stratified labelling sample (~260)
    rng = np.random.default_rng(42)
    df["hbin"] = pd.cut(df.height_m, [0, 4.5, 7, 12, 1e9], labels=["low", "mid", "tall", "vtall"])
    df["region"] = pd.qcut(df.x, 4, labels=False) * 3 + pd.qcut(df.y, 3, labels=False)
    picks = []
    for (s, h), g in df.groupby(["strict", "hbin"], observed=True):
        k = {0: 22, 1: 40}[s]
        if h == "low" and s == 1:
            k = 0
        picks.append(g.sample(min(k, len(g)), random_state=int(rng.integers(1e6)), weights=None))
    samp = pd.concat(picks)
    # top up for geographic coverage
    for reg, g in df.groupby("region"):
        if (samp.region == reg).sum() < 12:
            picks2 = g[~g.cid.isin(samp.cid)].sample(min(12, len(g)), random_state=reg)
            samp = pd.concat([samp, picks2])
    samp = samp.sample(frac=1, random_state=7).reset_index(drop=True)
    samp.to_csv(f"{D}/label_sample.csv", index=False)
    print("sample", len(samp), samp.groupby(["strict", "hbin"], observed=True).size().to_dict())
    # ---- chips: multi-directional hillshade, 3.2 km, outline of candidate
    os.makedirs(f"{D}/label_app/chips", exist_ok=True)
    zs = ndi.gaussian_filter(zf, 0.7)
    gy, gx = np.gradient(zs, DX)
    hs = np.zeros_like(zs)
    for az_l, w in ((315, 0.4), (45, 0.2), (225, 0.2), (135, 0.2)):
        a = np.radians(az_l); alt = np.radians(35)
        sl = np.arctan(np.hypot(gx, gy) * 2.0); asp = np.arctan2(-gx, gy)
        hs += w * (np.sin(alt) * np.cos(sl) + np.cos(alt) * np.sin(sl) * np.cos(a - asp))
    hs = np.clip(hs, 0, 1)
    R = 80
    for _, p in samp.iterrows():
        r0, c0 = int(p.row), int(p.col)
        ra, rb = max(r0 - R, 0), min(r0 + R, H); ca, cb = max(c0 - R, 0), min(c0 + R, Wd)
        chip = (hs[ra:rb, ca:cb] * 255).astype(np.uint8)
        wat = ~valid[ra:rb, ca:cb]
        rgb = np.stack([chip] * 3, -1)
        rgb[wat] = (rgb[wat] * 0.5 + np.array([60, 110, 170]) * 0.5).astype(np.uint8)
        # outline of the candidate: re-detect locally and take the component at centroid
        lab, P = detect(zf[ra:rb, ca:cb], DX, valid=valid[ra:rb, ca:cb], flow_az=None, h_thresh=1.5,
                        h_split=1.5, h_peak=3.0, min_area=0.005e6, max_area=5e6, min_elong=0.0)
        best = None
        for q in P:
            dd = (q["row"] + ra - p.row) ** 2 + (q["col"] + ca - p.col) ** 2
            if best is None or dd < best[0]:
                best = (dd, q["label"])
        img = Image.fromarray(rgb).resize(((cb - ca) * 3, (rb - ra) * 3), Image.BILINEAR)
        if best is not None and best[0] < 9:
            m = (lab == best[1])
            edge = m & ~ndi.binary_erosion(m)
            er, ec = np.nonzero(edge)
            dr = ImageDraw.Draw(img)
            for a_, b_ in zip(er, ec):
                dr.rectangle([b_ * 3, a_ * 3, b_ * 3 + 2, a_ * 3 + 2], fill=(255, 140, 0))
        # 1 km scale bar
        dr = ImageDraw.Draw(img)
        dr.rectangle([10, img.height - 16, 10 + 150, img.height - 11], fill=(255, 255, 255))
        img.save(f"{D}/label_app/chips/{int(p.cid)}.jpg", quality=80)
    json.dump([dict(cid=int(p.cid), h=round(float(p.height_m), 1), L=int(p.length_m), W=int(p.width_m))
               for _, p in samp.iterrows()], open(f"{D}/label_app/items.json", "w"))


if __name__ == "__main__":
    main()
