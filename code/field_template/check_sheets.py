"""Blind spot-check sheets for Puget: 36 accepted (p>=0.5) + 12 rejected candidates, shuffled."""
import sys, numpy as np, pandas as pd
from scipy import ndimage as ndi
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, "/home/claude/lg")
from candidates import load
from detect import detect
D = "/home/claude/lg"; CW = 340; R = 100
c = pd.read_csv(f"{D}/candidates_scored.csv")
rng = np.random.default_rng(7)
acc = c[c.p_drumlin >= 0.5].sample(36, random_state=1).assign(grp="acc")
rej = c[(c.p_drumlin < 0.5) & (c.height_m >= 3)].sample(12, random_state=2).assign(grp="rej")
S = pd.concat([acc, rej]).sample(frac=1, random_state=3).reset_index(drop=True)
z, v, tr = load()
def hs(z, dx):
    z = ndi.gaussian_filter(z, 0.6); gy, gx = np.gradient(z, dx)
    sl = np.arctan(np.hypot(gx, gy) * 5.0); asp = np.arctan2(-gx, gy); alt = np.radians(40); h = 0
    for az, w in ((315, .5), (45, .25), (225, .25)):
        a = np.radians(az); h = h + w * (np.sin(alt) * np.cos(sl) + np.cos(alt) * np.sin(sl) * np.cos(a - asp))
    lo, hi = np.percentile(h, [1, 99]); return np.clip((h - lo) / (hi - lo + 1e-9), 0, 1)
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 30)
rows = []
for s0 in range(0, len(S), 12):
    sheet = Image.new('RGB', (4 * CW + 24, 3 * CW + 16), (20, 20, 20)); dr = ImageDraw.Draw(sheet)
    for j, (_, p) in enumerate(S.iloc[s0:s0 + 12].iterrows()):
        r0, c0 = int(p.row), int(p.col)
        ra, ca = max(r0 - R, 0), max(c0 - R, 0)
        zz = z[ra:r0 + R, ca:c0 + R]; vv = v[ra:r0 + R, ca:c0 + R]
        pad = ((ra - (r0 - R), (r0 + R) - ra - zz.shape[0] - (ra - (r0 - R))), (ca - (c0 - R), 0))
        g = (hs(zz, 20.0) * 255).astype(np.uint8); rgb = np.stack([g] * 3, -1)
        rgb[~vv] = (rgb[~vv] * .35 + np.array([70, 120, 190]) * .65).astype(np.uint8)
        lab, P = detect(zz, 20.0, valid=vv, flow_az=None, h_thresh=1.5, h_split=1.5, h_peak=3.0,
                        min_area=0.005e6, max_area=5e6, min_elong=0.0, pre_close_px=3)
        best = min(P, key=lambda q: (q["row"] + ra - p.row) ** 2 + (q["col"] + ca - p.col) ** 2, default=None)
        if best is not None:
            m = lab == best["label"]; e = m & ~ndi.binary_erosion(m, iterations=1)
            rgb[e] = (255, 150, 0)
        full = np.full((2 * R, 2 * R, 3), 20, np.uint8)
        full[ra - (r0 - R):ra - (r0 - R) + rgb.shape[0], ca - (c0 - R):ca - (c0 - R) + rgb.shape[1]] = rgb
        im = Image.fromarray(full).resize((CW, CW), Image.LANCZOS)
        a = np.array(im); a[CW - 20:CW - 14, 10:10 + CW // 4] = 255; im = Image.fromarray(a)
        x = (j % 4) * (CW + 8); y = (j // 4) * (CW + 8); sheet.paste(im, (x, y))
        dr.rectangle([x, y, x + 46, y + 40], fill=(0, 0, 0)); dr.text((x + 8, y + 3), str(j + 1), fill=(0, 230, 255), font=font)
        rows.append(dict(sheet=s0 // 12 + 1, pos=j + 1, cid=int(p.cid), grp=p.grp, p=round(p.p_drumlin, 3)))
    sheet.save(f"{D}/check/sheet_{s0 // 12 + 1}.jpg", quality=85)
pd.DataFrame(rows).to_csv(f"{D}/check/.key.csv", index=False); print(len(rows))
