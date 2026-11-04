"""Per-tile till texture from SSURGO (Soil Data Access). Deepest horizon of major components whose
parent material mentions till; weighted by map-unit area in tile x component percent."""
import time, requests, numpy as np, pandas as pd, rasterio
from pyproj import Transformer

U = "https://sdmdataaccess.sc.egov.usda.gov/tabular/post.rest"
D = "/home/claude/lg"


def q(sql, tries=3):
    for k in range(tries):
        try:
            r = requests.post(U, json={"query": sql, "format": "JSON+COLUMNNAME"}, timeout=180)
            r.raise_for_status(); t = r.json().get("Table", [])
            return pd.DataFrame(t[1:], columns=t[0]) if t else pd.DataFrame()
        except Exception as e:
            time.sleep(3 * (k + 1)); err = e
    raise err


with rasterio.open(f"{D}/data/ny_dem_20m.tif") as s:
    tr = s.transform
to_ll = Transformer.from_crs("EPSG:32616", "EPSG:4326", always_xy=True)
tiles = pd.read_csv(f"{D}/tile_morph_0.5.csv")
rows = []
for _, t in tiles.iterrows():
    r0, c0 = (int(t.tile) // 100) * 512, (int(t.tile) % 100) * 512
    corners = [tr * (c0, r0), tr * (c0 + 512, r0), tr * (c0 + 512, r0 + 512), tr * (c0, r0 + 512)]
    ll = [to_ll.transform(x, y) for x, y in corners]
    wkt = "POLYGON((" + ",".join(f"{lo:.5f} {la:.5f}" for lo, la in ll + [ll[0]]) + "))"
    mu = q(f"""SELECT P.mukey, SUM(P.mupolygongeo.STIntersection(geometry::STGeomFromText('{wkt}',4326)).STArea()) AS a
        FROM mupolygon P WHERE P.mupolygongeo.STIntersects(geometry::STGeomFromText('{wkt}',4326))=1 GROUP BY P.mukey""")
    if mu.empty:
        continue
    mu["a"] = mu.a.astype(float)
    mk = ",".join(mu.mukey)
    hz = q(f"""SELECT c.mukey, c.cokey, c.comppct_r, pm.pmgroupname, h.hzdept_r, h.claytotal_r, h.sandtotal_r,
        (SELECT SUM(f.fragvol_r) FROM chfrags f WHERE f.chkey=h.chkey) AS frag
        FROM component c LEFT JOIN copmgrp pm ON pm.cokey=c.cokey AND pm.rvindicator='Yes'
        JOIN chorizon h ON h.cokey=c.cokey WHERE c.mukey IN ({mk}) AND c.majcompflag='Yes'""")
    for col in ("comppct_r", "hzdept_r", "claytotal_r", "sandtotal_r", "frag"):
        hz[col] = pd.to_numeric(hz[col], errors="coerce")
    hz["till"] = hz.pmgroupname.fillna("").str.lower().str.contains("till")
    deep = hz.sort_values("hzdept_r").groupby("cokey").tail(1)
    deep = deep.merge(mu, on="mukey")
    deep["w"] = deep.a * deep.comppct_r / 100
    tot = deep.groupby("cokey").w.first().sum()
    T = deep[deep.till & deep.claytotal_r.notna()]
    if T.empty:
        continue
    def wavg(col):
        m = T[col].notna(); return float(np.average(T[col][m], weights=T.w[m])) if m.any() else np.nan
    T = T.assign(frag=T.frag.fillna(0))
    rows.append(dict(tile=int(t.tile), till_frac=float(T.w.sum() / tot), clay=wavg("claytotal_r"),
                     sand=wavg("sandtotal_r"), frag=wavg("frag"), n_comp=len(T)))
    print(rows[-1], flush=True)
pd.DataFrame(rows).to_csv(f"{D}/tile_till.csv", index=False)
print("tiles with till data:", len(rows))
