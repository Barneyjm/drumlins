# Open questions and next tests

## Validate against expert maps

About 14,000 drumlins in the southern Green Bay Lobe have been hand-mapped from lidar (Barrette et al., 2017, described in [WGNHS 2019](https://data.wgnhs.wisc.edu/pubshare/WOFR2019-02.pdf)). Comparing our detections with that map would give real precision and recall by distance from the margin. That is the most important missing check: the BRITICE comparison (see [Data and methods](methods.md#validation-against-expert-maps)) confirmed our precision far from margins but cannot test near them. The Green Bay inventory does not appear to be public, so it would have to be requested from the authors. A Patagonian map ([Darvill et al., 2014](https://durham-repository.worktribe.com/output/1468686/a-glacial-geomorphological-map-of-the-southernmost-ice-lobes-of-patagonia-the-bahia-inutil-san-sebastian-magellan-otway-skyring-and-bella-vista-lobes)) covers the Magellan–Otway field.

## Find smaller drumlins

We recover only 7–10% of hand-mapped drumlins, mostly the large ones. Running the detector on 1–2 m lidar without resampling to 20 m would test whether the within-field patterns hold for the whole population.

## Separate time from speed

Near margins, time under ice, distance and ice speed all change together. The cleanest separation is a readvance zone where drumlins survived on both sides of the readvance limit. Fox Valley, Killard Point and Loch Lomond did not qualify.

## Proper slip estimates

Repeat the flowline slip reconstruction of Zoet et al. (2021) in New York, Puget and Pierz. Then test whether slip predicts elongation beyond distance.

## Flow from independent indicators

Use striations, eskers or NADI-1 flowlines instead of drumlin orientations. That would remove any remaining circularity from the convergence test.

## Field baselines

Nothing tested explains why some fields have more elongated drumlins than others. Candidates our data cannot see include:

- till thickness;
- the rock under the till;
- subglacial drainage;
- ice thickness and stiffness.

## Pre-registered tests

The 60 km break and the cold-margin grouping were chosen after looking. Future fields should be tested with those choices fixed in advance.

## Rerun the older tests

The spacing, till-texture tiles and shallow-ice model figures still use the first classifier. They need rerunning on the corrected selection.

## Múlajökull with dated limits

Digitise the thesis surge limits (1954–2008), then compare each drumlin's quiet-flow exposure with its shape.
