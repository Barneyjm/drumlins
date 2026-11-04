import numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyBboxPatch, FancyArrowPatch
from pyproj import Transformer
OUT = "/home/claude/drumlin-site/docs/assets/"
ICE = "#1f66a3"; TILL = "#b07a2e"; INK = "#22262a"; MUTE = "#5b636b"; RED = "#b8323f"; GRN = "#1f7a50"; GREY = "#9aa1a8"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "text.color": INK, "axes.edgecolor": MUTE, "axes.labelcolor": INK,
                     "xtick.color": MUTE, "ytick.color": MUTE, "svg.fonttype": "none"})
def save(fig, name): fig.savefig(OUT + name, format="svg", facecolor="white", bbox_inches="tight", pad_inches=0.12); plt.close(fig)
def drum(ax, x, y, L, W, ang=0, fc=TILL, alpha=1): ax.add_patch(Ellipse((x, y), L, W, angle=ang, fc=fc, ec="#7a531c", lw=0.8, alpha=alpha))
def arrow(ax, x0, y0, x1, y1, c=ICE, lw=2, ms=14): ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=ms, color=c, lw=lw))

# ---------- data file
EPSG = dict(MEN=32616, PTB=32617, TM=32615, PZ=32615, LEE=32616, MO=32719, LG=32616, AC=32616, PS=32610, WSH=32618, GB=32616, NY=32618, EDEN=27700, BR=32616, IRL=32629)
NAME = dict(MEN="Menominee, MI", PTB="Peterborough, ON", TM="Toimi, MN", PZ="Pierz, MN", LEE="Leelanau, MI", MO="Magellan–Otway, Chile", LG="Langlade, WI",
            AC="Antrim–Charlevoix, MI", PS="Puget Lowland, WA", WSH="Washington County, NY", GB="Green Bay lobe, WI", NY="Central New York",
            EDEN="Vale of Eden, England", BR="Branch County, MI", IRL="Cavan–Monaghan, Ireland")
out = []
for k, e in EPSG.items():
    s = pd.read_csv(f"scored_{k}.csv"); s = s[s.p_sl >= 0.6]
    lon, lat = Transformer.from_crs(e, 4326, always_xy=True).transform(s.x.values, s.y.values)
    out.append(pd.DataFrame(dict(field=NAME[k], lon=lon.round(6), lat=lat.round(6), length_m=s.length_m.round(1), width_m=s.width_m.round(1),
                                 elongation=s.elong.round(3), azimuth_deg=s.az.round(1), height_m=s.height_m.round(2), p_shape_light=s.p_sl.round(3), p_original=s.p_drumlin.round(3))))
A = pd.concat(out); A.to_csv("/home/claude/drumlin-site/data/accepted_drumlins.csv", index=False); print("accepted", len(A))
F = A.groupby("field").agg(n=("length_m", "size"), L=("length_m", "median"), W=("width_m", "median"), E=("elongation", "median"), H=("height_m", "median")).round(2)
F.to_csv("field_table_new.csv"); print(F.sort_values("E", ascending=False).to_string())

# ---------- margin chart (bins of elongation relative to field mean), shape-light selection
a = pd.read_csv("perdrumlin.csv"); a["lE"] = np.log(a.elong); a["rel"] = a.lE - a.groupby("field").lE.transform("mean")
bins = [0, 10, 20, 30, 45, 60, 100, 150, 250, 400]; labs = ["0–10", "10–20", "20–30", "30–45", "45–60", "60–100", "100–150", "150–250", "250–400"]
a["bin"] = pd.cut(a.dist_km, bins, labels=labs)
rows = []
for b, g in a.groupby("bin", observed=True):
    bm = g.groupby("blk").rel.mean(); se = bm.std(ddof=1) / np.sqrt(len(bm)) if len(bm) > 1 else np.nan
    rows.append((b, (np.exp(g.rel.mean()) - 1) * 100, 100 * 2 * se, len(g), g.field.nunique()))
B = pd.DataFrame(rows, columns=["bin", "pct", "e2", "n", "nf"]); print(B.round(1).to_string()); B.to_csv("margin_bins.csv", index=False)
fig, ax = plt.subplots(figsize=(6.2, 3.3)); x = np.arange(len(B))
for i, r in B.iterrows():
    c = ICE if i < 5 else GREY; ax.errorbar(i, r.pct, yerr=r.e2, fmt="o", color=c, ms=7, lw=1.8, capsize=0)
    ax.text(i, r.pct + (r.e2 + 1.5) * (1 if r.pct >= 0 else -1), f"{r.pct:+.0f}%", ha="center", va="bottom" if r.pct >= 0 else "top", fontsize=9.5, color=c)
ax.axhline(0, color="#ccc", lw=1); ax.axvline(4.5, color=MUTE, ls="--", lw=0.9); ax.set_ylim(-42, 20); ax.text(4.6, -39, "60 km", fontsize=9.5, color=MUTE)
ax.set_xticks(x); ax.set_xticklabels(B.bin, rotation=40, ha="right", fontsize=9.5); ax.set_xlabel("distance inside the maximum ice limit (km)")
ax.set_ylabel("elongation vs field mean"); ax.yaxis.set_major_formatter(lambda v, p: f"{v:+.0f}%"); ax.spines[["top", "right"]].set_visible(False)
ax.set_title("Drumlins near the old ice edge are stubbier\nthan their field average", fontsize=11, loc="left", pad=10)
save(fig, "margin_gradient.svg")

# ---------- What's new 1: method (two rows, phone friendly)
fig, ax = plt.subplots(figsize=(5.2, 3.3)); ax.set_xlim(0, 6); ax.set_ylim(0, 4.1); ax.axis("off")
steps = [("15 fields", "3 continents"), ("Elevation", "lidar or 30 m"), ("Detector", "same settings"),
         ("Classifier", "no shape inputs"), ("Blind check", "48 cards a field"), ("Shapes", "one cutoff: 0.6")]
pos = [(1, 3.1), (3, 3.1), (5, 3.1), (5, 1.35), (3, 1.35), (1, 1.35)]
for i, ((t, s), (x, y)) in enumerate(zip(steps, pos)):
    c = ICE if i in (2, 3, 4) else MUTE
    ax.add_patch(FancyBboxPatch((x - 0.85, y - 0.55), 1.7, 1.1, boxstyle="round,pad=0.02,rounding_size=0.12", fc="white", ec=c, lw=1.6))
    ax.text(x, y + 0.15, t, ha="center", va="center", fontsize=11.5, weight="bold"); ax.text(x, y - 0.25, s, ha="center", va="center", fontsize=9.5, color=MUTE)
for (x0, y0), (x1, y1) in zip(pos[:-1], pos[1:]):
    if y0 == y1: arrow(ax, x0 + (0.88 if x1 > x0 else -0.88), y0, x1 - (0.88 if x1 > x0 else -0.88), y1, c=MUTE, lw=1.3, ms=11)
    else: arrow(ax, x0, y0 - 0.58, x1, y1 + 0.58, c=MUTE, lw=1.3, ms=11)
ax.text(3, 0.25, "identical in every field", ha="center", fontsize=10.5, color=ICE)
save(fig, "new_method.svg")

# ---------- What's new 2: margin (fewer bins, larger type)
show = B.iloc[:6].copy()
fig, ax = plt.subplots(figsize=(5.2, 3.0)); ax.set_xlim(-0.9, 5.7); ax.set_ylim(-1.35, 2.25); ax.axis("off")
ax.add_patch(plt.Rectangle((-0.9, -0.55), 0.4, 2.1, fc="#dbe9f6", ec="none")); ax.plot([-0.5, -0.5], [-0.55, 1.55], color=ICE, lw=2.5)
ax.text(-0.7, -0.68, "ice\nlimit", ha="center", va="top", fontsize=9.5, color=ICE)
E0, Wd, EX = 2.4, 0.36, 2
for i, r in show.iterrows():
    xx = i * 0.98 + 0.05; L = Wd * E0 * (1 + EX * r.pct / 100); al = 1 if i < 5 else 0.45
    for y in (0.0, 0.95): drum(ax, xx, y, L, Wd, alpha=al)
    col = RED if (r.pct < 0 and i < 5) else (GRN if i < 5 else MUTE)
    ax.text(xx, 1.62, f"{r.pct:+.0f}%", ha="center", fontsize=11, weight="bold", color=col)
    ax.text(xx, -0.68, r.bin, ha="center", va="top", fontsize=9.5, color=MUTE)
ax.text(2.4, -1.3, "km inside the ice limit", ha="center", fontsize=10, color=MUTE)
ax.text(-0.9, 2.2, "Elongation vs field average (shape differences ×2)", fontsize=10, va="top")
save(fig, "new_margin.svg")

# ---------- What's new 3: convergence
fig, ax = plt.subplots(figsize=(5.2, 3.2)); ax.set_xlim(0, 6); ax.set_ylim(0, 4); ax.axis("off")
for cx, title, spread, L in ((1.5, "spreading flow", 1, 0.95), (4.5, "converging flow", -1, 1.5)):
    for dx in (-0.7, 0, 0.7):
        x0 = cx + dx * (0.55 if spread == 1 else 1.0); x1 = cx + dx * (1.0 if spread == 1 else 0.55)
        arrow(ax, x0, 3.45, x1, 2.55, lw=1.6, ms=11)
    drum(ax, cx, 1.75, 0.42, L * 0.85, ang=0); ax.text(cx, 3.75, title, ha="center", fontsize=11, weight="bold")
    ax.text(cx, 0.6, "shorter" if spread == 1 else "longer", ha="center", fontsize=10.5)
ax.text(3, 0.2, "New York +1.20, Puget +0.65, Green Bay +0.54", ha="center", fontsize=9.5, color=MUTE)
save(fig, "new_convergence.svg")

# ---------- What's new 4: classifier bias
th = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]; orig = [8.9, 16.7, 20.7, 24.5, 30.6, 49.2]; sl = [4.1, 7.1, 7.4, 11.1, 11.3, 24.8]
fig, ax = plt.subplots(figsize=(5.2, 3.1)); w = 0.36; xx = np.arange(len(th))
ax.bar(xx - w / 2, orig, w, color=RED, label="original classifier"); ax.bar(xx + w / 2, sl, w, color=ICE, label="no shape inputs")
ax.set_xticks(xx); ax.set_xticklabels([f"{t:.1f}" for t in th]); ax.set_xlabel("classifier cutoff")
ax.set_ylabel("elongation inflation"); ax.yaxis.set_major_formatter(lambda v, p: f"+{v:.0f}%"); ax.spines[["top", "right"]].set_visible(False)
ax.legend(frameon=False, fontsize=10, loc="upper left"); ax.set_title("How much more elongated the kept drumlins are\nthan all confirmed drumlins", fontsize=10.5, loc="left")
save(fig, "new_bias.svg")
