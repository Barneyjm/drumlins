# Data and methods

Of 26 fields attempted, 16 passed quality checks; they hold 17,593 accepted drumlins, picked from over 300,000 candidate hills.

1.  **Elevation.** USGS 3DEP 1/3 arc-second data in the US, Copernicus 30 m in Canada, Ireland and Patagonia, England Environment Agency lidar for the Vale of Eden, Polish national lidar, and 2 m ArcticDEM for Múlajökull. Everything was resampled to 20 m (4 m in Iceland) in UTM.

2.  **Detection.** Hills come from top-hat relief and an h-maxima watershed, with road cuts filled by grey closing and outlines trimmed at half height. Length, width and azimuth come from each footprint's second moments.

3.  **Classification.** A gradient-boosted classifier with neighbourhood features (how many aligned hills sit nearby) was trained on 722 New York labels from James and Anthropic’s Claude 5.5 family models. It was retrained with relabelled Green Bay and Puget cards, then pooled across all three (1,385 labels).

<figure markdown="span">
  ![Detected hills on two New York hillshade windows. Green outlines were accepted by the classifier as drumlins; red outlines were rejected.](assets/model_zoom.jpg)
  <figcaption>Detected hills on two New York hillshade windows. Green outlines were accepted by the classifier as drumlins; red outlines were rejected.</figcaption>
</figure>


4.  **Quality control.** Each field got 48 blind cards (36 accepted, 12 rejected). The cutoff was set where precision reached about 70% or better: 0.25–0.85 depending on the field. Labeller agreement with James: Claude Opus κ = 0.83, Claude Sonnet 0.69, Claude Haiku 0.33.

5.  **Ice history.** Ice margins and timing come from NADI-1 for North America (0.5 ka slices), DATED-1 for Britain and Ireland, and PATICE for Patagonia. Múlajökull surge limits come from Sigurkarlsson's thesis.

6.  **Flow.** Convergence was measured from the drumlins' own orientations: an upstream-integrated flux-tube width over 10–20 km. A shallow-ice model on ETOPO beds was calibrated to drumlin directions for New York (median error 11°), Green Bay (21°) and Puget (19–21°).

7.  **Exposure.** Cumulative slip was estimated from a plastic-lobe ice profile at each margin slice, where slip speed scales with the square root of distance from the margin. Summing over cover time gives each drumlin's total.

8.  **Soils.** Till clay, sand and stone content at each drumlin come from USDA SSURGO, using till-parent map units.

Statistics use field fixed effects and errors clustered by 5 km blocks. Tile tests use Dutilleul effective sample size and block bootstraps.


<figure markdown="span">
  ![Median drumlin elongation per 10 km tile across the Central New York field, weighted by classifier probability.](assets/elongation_map.jpg)
  <figcaption>Median drumlin elongation per 10 km tile across the Central New York field, weighted by classifier probability.</figcaption>
</figure>
