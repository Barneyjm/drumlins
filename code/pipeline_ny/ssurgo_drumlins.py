"""Soil map unit under each model drumlin (centroid point-in-polygon), then till texture per map unit."""
import time, requests, numpy as np, pandas as pd
from pyproj import Transformer

U = "https://sdmdataaccess.sc.egov.usda.gov/tabular/post.rest"
D = "/home/claude/drumlins"


def q(sql, tries=4):
    for k in range(tries):
        try:
            r = requests.post(U, json={"query": sql, "format": "JSON+COLUMNNAME"}, timeout=240)
            r.raise_for_status(); t = r.json().get("Table", [])
            return pd.DataFrame(t[1:], columns=t[0]) if t else pd.DataFrame()
        except Exception as e:
            err = e; time.sleep(4 * (k + 1))
    raise err


s = pd.read_csv(f"{D}/candidates_scored3.csv")
d = s[(s.p_drumlin >= 0.25) & (s.height_m < 60)].copy().reset_index(drop=True)
lon, lat = Transformer.from_crs("EPSG:32618", "EPSG:4326", always_xy=True).transform(d.x.values, d.y.values)
d["lon"], d["lat"] = lon, lat
out = []
B = 150
for i in range(0, len(d), B):
    chunk = d.iloc[i:i + B]
    vals = ",".join(f"({int(r.cid)},geometry::STGeomFromText('POINT({r.lon:.6f} {r.lat:.6f})',4326))" for r in chunk.itertuples())
    res = q(f"SELECT pts.id, P.mukey FROM (VALUES {vals}) AS pts(id,g) JOIN mupolygon P ON P.mupolygongeo.STIntersects(pts.g)=1")
    out.append(res)
    if (i // B) % 6 == 0:
        print(f"{i + len(chunk)}/{len(d)}", flush=True)
mk = pd.concat(out).drop_duplicates("id").rename(columns={"id": "cid"}); mk["cid"] = mk.cid.astype(int)
d = d.merge(mk, on="cid", how="left")
ukeys = d.mukey.dropna().unique().tolist()
print("drumlins matched:", d.mukey.notna().sum(), "of", len(d), "| map units:", len(ukeys))
hz = []
for j in range(0, len(ukeys), 200):
    keys = ",".join(ukeys[j:j + 200])
    hz.append(q(f"""SELECT c.mukey, c.cokey, c.compname, c.comppct_r, pm.pmgroupname, h.hzdept_r, h.claytotal_r, h.sandtotal_r,
        (SELECT SUM(f.fragvol_r) FROM chfrags f WHERE f.chkey=h.chkey) AS frag
        FROM component c LEFT JOIN copmgrp pm ON pm.cokey=c.cokey AND pm.rvindicator='Yes'
        JOIN chorizon h ON h.cokey=c.cokey WHERE c.mukey IN ({keys}) AND c.majcompflag='Yes'"""))
hz = pd.concat(hz)
for col in ("comppct_r", "hzdept_r", "claytotal_r", "sandtotal_r", "frag"):
    hz[col] = pd.to_numeric(hz[col], errors="coerce")
hz["till"] = hz.pmgroupname.fillna("").str.lower().str.contains("till")
deep = hz.sort_values("hzdept_r").groupby("cokey").tail(1).copy()
deep["frag"] = deep.frag.fillna(0)
rows = []
for mkey, g in deep.groupby("mukey"):
    t = g[g.till & g.claytotal_r.notna()]
    tot = g.comppct_r.sum()
    if t.empty or t.comppct_r.sum() == 0:
        rows.append(dict(mukey=mkey, till_share=0.0)); continue
    w = t.comppct_r
    rows.append(dict(mukey=mkey, till_share=float(w.sum() / tot), clay=float(np.average(t.claytotal_r, weights=w)),
                     sand=float(np.average(t.sandtotal_r.fillna(t.sandtotal_r.mean()), weights=w)),
                     frag=float(np.average(t.frag, weights=w)), series=t.sort_values("comppct_r").compname.iloc[-1]))
mt = pd.DataFrame(rows)
d = d.merge(mt, on="mukey", how="left")
d.to_csv(f"{D}/drumlin_soils.csv", index=False)
print("drumlins on till-dominated units (till share >= 0.5):", int((d.till_share >= 0.5).sum()))
print(d[d.till_share >= 0.5].series.value_counts().head(10).to_string())
