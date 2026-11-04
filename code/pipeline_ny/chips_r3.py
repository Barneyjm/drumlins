"""Round-2 label cards from the 10 m DEM, with the (road-filled, 20 m) candidate outline."""
import sys, json, io, base64, os, numpy as np, pandas as pd, rasterio
from scipy import ndimage as ndi
from PIL import Image
sys.path.insert(0, "/home/claude/drumlins")
from candidates import load
from detect import detect

D = "/home/claude/drumlins"; OUT = 440; R10 = 200   # 200 px * 10 m = 2 km half-width (4 km card)
S = pd.read_csv(f"{D}/label_sample_r3.csv")
z20, v20, tr20 = load()
src = rasterio.open(f"{D}/data/ny_dem_10m.tif")
inv = ~src.transform


def hillshade(z, dx):
    z = ndi.gaussian_filter(z, 0.8)
    gy, gx = np.gradient(z, dx)
    sl = np.arctan(np.hypot(gx, gy) * 6.0); asp = np.arctan2(-gx, gy); alt = np.radians(40)
    h = np.zeros_like(z)
    for az, w in ((315, .5), (45, .25), (225, .25)):
        a = np.radians(az); h += w * (np.sin(alt) * np.cos(sl) + np.cos(alt) * np.sin(sl) * np.cos(a - asp))
    lo, hi = np.percentile(h, [1, 99]); return np.clip((h - lo) / (hi - lo + 1e-9), 0, 1)


items, chips = [], {}
for _, p in S.iterrows():
    c10, r10 = inv * (p.x, p.y); c10, r10 = int(c10), int(r10)
    win = rasterio.windows.Window(c10 - R10, r10 - R10, 2 * R10, 2 * R10)
    z = src.read(1, window=win, boundless=True, fill_value=np.nan)
    w = src.read(2, window=win, boundless=True, fill_value=1) > 0.5
    zf = np.where(np.isfinite(z), z, np.nanmean(z))
    g = (hillshade(zf, 10.0) * 255).astype(np.uint8)
    rgb = np.stack([g] * 3, -1); wat = w | ~np.isfinite(z)
    rgb[wat] = (rgb[wat] * .35 + np.array([70, 120, 190]) * .65).astype(np.uint8)
    clean = Image.fromarray(rgb).resize((OUT, OUT), Image.LANCZOS)
    a = np.array(clean); a[OUT - 22:OUT - 16, 12:12 + OUT // 4] = 255     # 1 km bar (card = 4 km)
    clean = Image.fromarray(a)
    # outline: re-detect on the 20 m grid (road-filled) around the candidate, pick nearest footprint
    r0, c0 = int(p.row), int(p.col); R = 100
    ra, ca = r0 - R, c0 - R
    zz = z20[max(ra, 0):r0 + R, max(ca, 0):c0 + R]; vv = v20[max(ra, 0):r0 + R, max(ca, 0):c0 + R]
    lab, P = detect(zz, 20.0, valid=vv, flow_az=None, h_thresh=1.5, h_split=1.5, h_peak=3.0,
                    min_area=0.005e6, max_area=5e6, min_elong=0.0, pre_close_px=3)
    best = min(P, key=lambda q: (q["row"] + max(ra, 0) - p.row) ** 2 + (q["col"] + max(ca, 0) - p.col) ** 2, default=None)
    outl = clean.copy()
    if best is not None:
        m = np.zeros((2 * R, 2 * R), bool)
        sub = lab == best["label"]
        m[max(ra, 0) - ra:max(ra, 0) - ra + sub.shape[0], max(ca, 0) - ca:max(ca, 0) - ca + sub.shape[1]] = sub
        mb = np.array(Image.fromarray(m.astype(np.uint8) * 255).resize((OUT, OUT), Image.NEAREST)) > 0
        e = mb & ~ndi.binary_erosion(mb, iterations=2)
        b = np.array(outl); b[e] = (255, 150, 0); outl = Image.fromarray(b)
    for key, im in ((f"{p.rid}_c", clean), (f"{p.rid}_o", outl)):
        buf = io.BytesIO(); im.save(buf, "JPEG", quality=78)
        chips[key] = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    items.append(dict(cid=p.rid, h=round(float(p.height_m), 1), L=int(p.length_m), W=int(p.width_m)))
json.dump(items, open(f"{D}/label_app/items_r3.json", "w"))
os.makedirs(f"{D}/label_app/pub3", exist_ok=True)
K = 3; per = (len(items) + K - 1) // K
for k in range(K):
    part = {kk: v for it in items[k * per:(k + 1) * per] for kk, v in chips.items() if kk.startswith(it["cid"] + "_")}
    open(f"{D}/label_app/pub3/chips{k}.js", "w").write(
        "window.CHIPS=Object.assign(window.CHIPS||{}," + json.dumps(part) + ');window.dispatchEvent(new Event("chips"));')
print(len(items), "items; per chunk", per)
