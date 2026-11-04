"""Download BRITICE v2 subglacial-lineation polygons/polylines (and moraine polygons) over the Eden and Cavan-Monaghan fields."""
import json, sys, time, urllib.request, urllib.parse, pandas as pd
from pyproj import Transformer
BASE = "https://services2.arcgis.com/Dn40vzt2R38VJsSS/arcgis/rest/services/"
LAY = {"lin_poly": "Filtered_BRITICE_v2_test/FeatureServer/20", "lin_line": "Filtered_BRITICE_v2_test/FeatureServer/9",
       "moraine_poly": "Filtered_BRITICE_v2_test/FeatureServer/19", "ribs_poly": "Filtered_BRITICE_v2_test/FeatureServer/21",
       "irl_lin": "Subglacial_Lineations_Ireland/FeatureServer/0"}
F = {"EDEN": 27700, "IRL": 32629}
for k, e in F.items():
    s = pd.read_csv(f"/home/claude/rerun/scored_{k}.csv")
    lon, lat = Transformer.from_crs(e, 4326, always_xy=True).transform([s.x.min(), s.x.max()], [s.y.min(), s.y.max()])
    env = f"{min(lon)},{min(lat)},{max(lon)},{max(lat)}"; print(k, env)
    for nm, path in LAY.items():
        feats, off = [], 0
        while True:
            q = urllib.parse.urlencode(dict(where="1=1", geometry=env, geometryType="esriGeometryEnvelope", inSR=4326, spatialRel="esriSpatialRelIntersects",
                                            outFields="*", outSR=4326, f="geojson", resultOffset=off, resultRecordCount=2000))
            d = json.load(urllib.request.urlopen(BASE + path + "/query?" + q, timeout=120)); fs = d.get("features", [])
            feats += fs; off += len(fs)
            if len(fs) < 2000 and not d.get("properties", {}).get("exceededTransferLimit"): break
        json.dump(dict(type="FeatureCollection", features=feats), open(f"britice_{k}_{nm}.geojson", "w")); print(" ", nm, len(feats))
