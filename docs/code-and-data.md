# Code and data

Everything needed to check the numbers in this write-up is in the [repository](https://github.com/Barneyjm/drumlins), apart from the elevation models themselves (tens of gigabytes; the scripts fetch them from the public sources listed under [Sources](sources.md)).

## Data

| File | What it holds |
| --- | --- |
| `data/accepted_drumlins.csv` | All 17,593 accepted drumlins in the 16 fields: field, lon/lat (WGS84), length, width, elongation, azimuth, height and classifier score |
| `data/results/perdrumlin.csv` | 15,955 drumlins with ice-limit distance, flow convergence and 5 km block ID (input to the margin-gradient tests) |
| `data/results/cumslip.csv` | Per-drumlin cumulative slip and time under ice from the NADI-1 margin slices |
| `data/results/fieldprops_*.csv`, `baseline_fields.csv` | Field-level properties (relief, latitude, exposure, till texture) used in the between-field tests |
| `data/results/margin_tiles.csv`, `overprint_tiles.csv`, `joint_tiles.csv` | Tile-level results for the margin, overprinting and joint-fit tests |
| `data/soils/soil_*.csv` | SSURGO till clay, sand and rock-fragment content sampled at each drumlin (US fields) |
| `data/mulajokull/` | Múlajökull drumlins (4 m ArcticDEM) and their surge-moraine zones |
| `data/labels/` | Human labels for the New York training rounds, plus Claude Opus, Claude Sonnet and Claude Haiku labels used for agreement checks |
| `models/pooled_classifier.pkl` | The pooled gradient-boosted drumlin classifier (scikit-learn), trained on 1,385 labels |

Coordinates in the result tables other than `accepted_drumlins.csv` are in each field's UTM zone (British National Grid for the Vale of Eden).

## Code

| Folder | What it does |
| --- | --- |
| `code/pipeline_ny/` | The original Central New York pipeline: DEM fetch, candidate detection, labelling chips, classifier training, validation, flow field and spacing tests |
| `code/field_template/` | The per-field copy of the pipeline used for every other field (fetch, detect, score, spot-check sheets, tile morphology, flow field) |
| `code/analysis/` | Cross-field analysis: per-drumlin margin tests, cumulative slip, saturation fits, soils, field baselines, the clay test and the field setup scripts |
| `code/mulajokull/` | Drumlin detection on the Múlajökull forefield |

The scripts were written as a working research pipeline, not a package. They use absolute paths under `/home/claude/` and expect the elevation data and ice-margin shapefiles (NADI-1, DATED-1, PATICE) in an `ext/` folder; adjust the paths before rerunning. Main dependencies: Python 3, numpy, scipy, pandas, scikit-image, scikit-learn, statsmodels, rasterio/GDAL, geopandas, shapely and pyproj.
