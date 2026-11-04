"""Compare our detections with expert hand-mapped BRITICE v2 drumlins/lineations.
EDEN: lineation polygons (outlines). IRL: lineation crest lines (+ ribbed-moraine polygons)."""
import json, numpy as np, pandas as pd, geopandas as gpd, shapely
from shapely.ops import unary_union
pd.set_option("display.width", 200)
F = {"EDEN": 27700, "IRL": 32629}
def load(k, nm, e):
    g = gpd.read_file(f"britice_{k}_{nm}.geojson")
    return g.set_crs(4326, allow_override=True).to_crs(e) if len(g) else g
rows = []
for k, e in F.items():
    c = pd.read_csv(f"/home/claude/rerun/scored_{k}.csv")
    P = gpd.GeoDataFrame(c, geometry=gpd.points_from_xy(c.x, c.y), crs=e)
    sel = {"original": c.p_drumlin >= {"EDEN": 0.7, "IRL": 0.5}[k], "shape-light": c.p_sl >= 0.6}
    if k == "EDEN":
        H = load(k, "lin_poly", e); H = H[H.geometry.notna()]
        Hm = gpd.GeoDataFrame(geometry=list(unary_union(shapely.make_valid(H.geometry.values)).geoms), crs=e)   # merge duplicate mappings
        hit = gpd.sjoin(P, Hm, predicate="within", how="left").groupby(level=0).index_right.first()
    else:
        L1 = pd.concat([load(k, "irl_lin", e), load(k, "lin_line", e)]); L1 = L1[L1.geometry.notna()]
        Hm = gpd.GeoDataFrame(geometry=list(unary_union(L1.geometry.values).geoms) if L1.geom_type.iloc[0] != "Polygon" else [], crs=e)
        Hm = gpd.GeoDataFrame(geometry=[g for g in shapely.line_merge(unary_union(L1.geometry.values)).geoms], crs=e) if hasattr(shapely.line_merge(unary_union(L1.geometry.values)), "geoms") else Hm
        tol = np.maximum(100, c.width_m.values / 2)
        d, idx = shapely.STRtree(Hm.geometry.values).query_nearest(P.geometry.values, return_distance=True, all_matches=False)
        nd = np.full(len(P), np.inf); ni = np.full(len(P), -1); nd[d[0]] = idx; ni[d[0]] = d[1]
        hit = pd.Series(np.where(nd <= tol, ni, np.nan), index=P.index)
    ribs = load(k, "ribs_poly", e); mor = load(k, "moraine_poly", e)
    in_rib = gpd.sjoin(P, ribs[["geometry"]], predicate="within", how="left").groupby(level=0).index_right.first().notna() if len(ribs) else pd.Series(False, index=P.index)
    # evaluation area: 2 km cells that contain mapped lineations (where mappers looked)
    cell = lambda x, y: (np.floor(x / 2000).astype(int) * 100000 + np.floor(y / 2000).astype(int))
    hb = Hm.geometry.representative_point(); hcells = set(cell(hb.x.values, hb.y.values))
    P["incell"] = np.isin(cell(c.x.values, c.y.values), list(hcells)); P["hit"] = hit.notna().values; P["rib"] = in_rib.values
    for nm, m in sel.items():
        s = P[m & P.incell]
        matched_h = set(hit[m & P.incell].dropna().astype(int))
        hin = Hm[np.isin(cell(hb.x.values, hb.y.values), list(hcells))]
        rows.append(dict(field=k, selection=nm, accepted=len(s), precision_vs_map=s.hit.mean(), in_mapped_ribs=s.rib.mean(),
                         mapped_features=len(hin), recall=len(matched_h) / len(hin)))
    # candidates: does the classifier score track the map?
    from sklearn.metrics import roc_auc_score
    cc = P[P.incell & (P.height_m >= 3)]
    print(k, "candidates in mapped cells", len(cc), "| AUC vs map: original", round(roc_auc_score(cc.hit, cc.p_drumlin), 3), "shape-light", round(roc_auc_score(cc.hit, cc.p_sl), 3))
    if k == "EDEN":   # shape comparison with hand outlines
        def lw(g):
            r = g.minimum_rotated_rectangle; xy = np.array(r.exterior.coords); a = np.hypot(*(xy[1] - xy[0])); b = np.hypot(*(xy[2] - xy[1])); return max(a, b), min(a, b)
        Hm["hL"], Hm["hW"] = zip(*[lw(g) for g in Hm.geometry]); Hm["hE"] = Hm.hL / Hm.hW
        s = P[sel["shape-light"] & P.hit].copy(); s = s.join(Hm[["hL", "hW", "hE"]], on=hit[s.index].astype(int).rename("h")) if False else s
        s["h"] = hit[s.index].astype(int).values; s = s.merge(Hm[["hL", "hW", "hE"]], left_on="h", right_index=True)
        s = s.sort_values("p_sl", ascending=False).drop_duplicates("h")
        print(f"EDEN matched pairs {len(s)}: ours L {s.length_m.median():.0f} W {s.width_m.median():.0f} E {s.elong.median():.2f} | hand L {s.hL.median():.0f} W {s.hW.median():.0f} E {s.hE.median():.2f} | "
              f"Spearman E {s[['elong','hE']].corr(method='spearman').iloc[0,1]:.2f}, L {s[['length_m','hL']].corr(method='spearman').iloc[0,1]:.2f}, W {s[['width_m','hW']].corr(method='spearman').iloc[0,1]:.2f}")
        hin = Hm[np.isin(cell(hb.x.values, hb.y.values), list(hcells))]
        print(f"EDEN all mapped drumlins in area: n {len(hin)} L {hin.hL.median():.0f} W {hin.hW.median():.0f} E {hin.hE.median():.2f}")
        Hm.to_file("eden_hand_merged.gpkg"); P.drop(columns="geometry").assign(hid=hit.values).to_csv("eden_match.csv", index=False)
    else:
        P.drop(columns="geometry").assign(hid=hit.values).to_csv("irl_match.csv", index=False)
print(pd.DataFrame(rows).round(3).to_string(index=False))
