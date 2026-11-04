# Code and data

Everything needed to check the numbers is in the [repository](https://github.com/Barneyjm/drumlins), apart from the elevation models (tens of gigabytes; the scripts fetch them from the public sources listed under [Sources](sources.md)).

## Data (current version)

| File | What it holds |
| --- | --- |
| `data/accepted_drumlins.csv` | 13,607 accepted drumlins in 15 fields, from the corrected classifier at cutoff 0.6. Columns: field, lon/lat (WGS84), length, width, elongation, azimuth, height, and both classifier scores. |
| `data/results_v2/perdrumlin_v2.csv` | 11,844 drumlins with ice-limit distance, flow convergence and 5 km block ID (input to the margin and convergence tests) |
| `data/results_v2/cumslip_v2.csv` | The same drumlins with time under ice and the cumulative-slip estimate (US fields) |
| `data/results_v2/precision_compare.csv` | Per-field precision of the old and new selections, from the blind cards |
| `data/results_v2/field_medians_compare.csv` | Field medians under the old and new selections |
| `data/results_v2/training_labels_cv.csv` | The 1,385 training labels with cross-validated scores from the original, shape-light and shape-blind classifiers |
| `data/results_v2/margin_bins.csv` | The margin chart values |
| `data/soils/soil_*.csv` | SSURGO till clay, sand and rock-fragment content at each drumlin (US fields) |
| `data/mulajokull/` | Múlajökull drumlins (4 m ArcticDEM) and their surge-moraine zones |
| `data/labels/` | Human labels for the New York training rounds, plus Claude Opus, Claude Sonnet and Claude Haiku labels |
| `models/shape_light_classifier.pkl` | The current classifier (scikit-learn; no length, width or elongation inputs) |

The first version's data are kept for comparison: `data/accepted_drumlins_v1.csv`, `data/results_v1/` and `models/pooled_classifier_v1.pkl`.

Coordinates in the result tables other than `accepted_drumlins.csv` are in each field's UTM zone (British National Grid for the Vale of Eden).

## Code

| Folder | What it does |
| --- | --- |
| `code/pipeline_ny/` | The original Central New York pipeline: DEM fetch, candidate detection, labelling chips, classifier training, validation, flow field and spacing tests |
| `code/field_template/` | The per-field copy of the pipeline used for every other field |
| `code/analysis/` | First-version cross-field analysis, field setup scripts and the diagram script |
| `code/rerun_after_review/` | The post-review rerun: shape-light classifier, rescoring, precision estimates, margin and convergence tests, the convergence null test, the soil and time tests, and the figures. `RESULTS.md` summarises the numbers. |
| `code/mulajokull/` | Drumlin detection on the Múlajökull forefield |

The scripts were written as a working research pipeline, not a package. They use absolute paths under `/home/claude/` and expect the elevation data and ice-margin shapefiles (NADI-1, DATED-1, PATICE) in an `ext/` folder; adjust the paths before rerunning. Main dependencies: Python 3, numpy, scipy, pandas, scikit-image, scikit-learn, statsmodels, rasterio/GDAL, geopandas, shapely and pyproj.
