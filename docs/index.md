# How Drumlins Form: Evidence from 16 Fields

*James · November 2026*

!!! warning "Read this first: an amateur study"
    I'm not a geologist. This is an independent project done with an AI model (Anthropic's Claude Opus) doing most of the analysis, and it has not been peer-reviewed. Treat it as a careful exploration with open data and code, not as an established result. See [Caveats](#caveats) below for the specific limits, and please [open an issue](https://github.com/Barneyjm/drumlins/issues) if you spot a mistake.

## What drumlins are and why they matter

A drumlin is a streamlined hill shaped by an ice sheet flowing over its bed: blunt and steep on the end that faced the oncoming ice, tapering toward the end the ice flowed off. Typical drumlins are a few hundred metres to a kilometre or so long, a few hundred metres wide and tens of metres high. They rarely occur alone; they come in fields of hundreds to thousands, often described as a "basket of eggs" landscape. The name comes from the Irish *droimnín*, "little ridge". Large fields cover parts of New York, Wisconsin, Minnesota, Michigan, Canada, Ireland and Britain, all left by ice sheets that melted away at the end of the last ice age.

<figure markdown="span">
  ![Hillshade of drumlins in the Central New York field](assets/ny_hillshade.jpg)
  <figcaption>About 7 × 5 km of the Central New York drumlin field, near the north end of Canandaigua Lake (USGS 3DEP 10 m elevation, lit from the northwest). Ice flowed roughly north-northeast to south-southwest, along the long axes of the hills; each hill is a drumlin.</figcaption>
</figure>

**Why they matter.**

- **They record how ice sheets moved.** Drumlins line up with the flow, so geologists use them to map where vanished ice sheets went and how their flow changed as they retreated.
- **They are a window on the ice-sheet bed.** How fast an ice sheet slides depends on what happens where ice meets soft, wet sediment, and that is one of the least certain parts of forecasting how fast Antarctica and Greenland lose ice to the sea. The bed of a living ice sheet is almost impossible to observe; old drumlin fields are its exposed floor, with tens of thousands of examples.
- **How they form is still unsolved.** Geologists have argued about it since the 1800s. Drumlins can be made of till, gravel or bedrock, so their contents alone do not settle it. Theories range from ice moulding soft sediment to meltwater floods to a bed instability, like ripples in sand, that grows bumps of a preferred size.

This study tests that last idea, and what happens after the bumps form, against drumlin shapes measured across 16 fields on three continents.

## What's new here

As far as we can tell from the literature we read, these parts are new. Our reading was not exhaustive, so some of them may already exist.

- **One method across many fields.** Large drumlin inventories are usually mapped region by region by hand, for example the roughly 59,000 drumlins of Britain and Ireland in [Clark et al. (2009)](https://www.sciencedirect.com/science/article/abs/pii/S0277379108002540). Here a single automated detector and classifier, checked blind in each field, was run over 16 fields in North America, Britain, Ireland and Patagonia. That lets shape be compared between fields without differences in mapping style.
- **A within-field margin gradient across several ice sheets.** Drumlins get stubbier toward the maximum ice limit, out to about 60 km. It shows up in every cold-margin field near a dated ice limit (Green Bay, Langlade, Pierz in the Laurentide; Magellan–Otway in Patagonia), and again at a modern Icelandic surge glacier.
- **A direct test of the instability theory's speed prediction.** The theory predicts how drumlin shape should change with ice speed. We measured that change in the field and found it goes the other way.
- **Cumulative slip tested beyond one field.** [Zoet et al. (2021)](https://onlinelibrary.wiley.com/doi/10.1002/esp.5192) linked elongation to cumulative slip under the Green Bay Lobe. We reproduce their result there, and find it holds pooled across fields but with a different strength in each.
- **Width is nearly fixed; length does the varying.** Across fields, median width changes by a factor of 1.8 and median length by 2.2, and elongation follows length.

## Where this meets existing theory

| Existing idea | What we found |
| --- | --- |
| **Bed instability sets drumlin size** ([Fowler & Chapwanya, 2014](https://royalsocietypublishing.org/doi/10.1098/rspa.2014.0185)) | **Supported for size.** Observed drumlins imply a natural length scale of about 400–450 m, a physically sensible value. |
| **The same theory: faster ice makes stubbier drumlins** | **Contradicted.** Where flow converges and speeds up, drumlins get *longer*, in New York, Green Bay and Puget. |
| **Elongation tracks ice speed**, with fast ice-stream beds grading into mega-scale lineations (a common textbook view) | **Only partly.** No single speed law fits across fields. Within a field, how long and how far ice slid over a spot predicts elongation better than speed alone. |
| **Elongation grows with cumulative slip** ([Zoet et al., 2021](https://onlinelibrary.wiley.com/doi/10.1002/esp.5192)) | **Replicated** in Green Bay (+0.26) and pooled across fields (+0.21), but the coefficient is not shared between fields. |
| **Stubby drumlins near the edge need a frozen ice margin** (an idea we tested) | **Not required.** The same inward gradient appears under warm-based ice at Múlajökull, and cumulative slip accounts for it. |
| **Drumlin sizes from large hand-mapped samples** ([Clark et al., 2009](https://www.sciencedirect.com/science/article/abs/pii/S0277379108002540): mean 629 m long, 209 m wide, elongation 2.9) | **Consistent.** Our field medians are similar, for example Green Bay at 628 × 210 m and 2.93, which is a check on the detector. |
| **Meltwater-flood and other formation ideas** | **Not tested.** Our data are shapes and positions, which cannot separate these mechanisms on their own. |


## Summary

Drumlins form in two stages. A bed instability under sliding ice sets their starting size; afterwards, they keep lengthening for as long as ice flows over them. Across 16 drumlin fields and one modern glacier, that picture fits better than any law tying drumlin shape to ice speed.

- **Stage 1, size.** The Fowler & Chapwanya (2014) instability gives a natural length scale l<sub>D</sub> = √(η·u / (Δρ·g)), with fastest-growing bumps 1–2 l<sub>D</sub> long and 0.3–1 l<sub>D</sub> wide. Observed sizes imply l<sub>D</sub> ≈ 400–450 m. Median drumlin width is nearly constant across fields, at 184–327 m.

- **Stage 2, lengthening.** Within a field, elongation rises with time under ice, cumulative slip and converging flow; length carries the change, not width. Near ice-sheet margins this gives stubbier drumlins. The same gradient appears under warm-based ice in Iceland, so a frozen bed is not required.

- **What the data reject.** No single ice-speed law fits; the theory's prediction that faster ice makes stubbier drumlins fails. Between-field differences in elongation are not explained by exposure, margin distance, relief, latitude or till texture.

- **How much it explains.** Glaciological controls shift field averages by tens of percent. Each explains about 1% of the variation between individual drumlins; most of that variation is local.

| Claim                                                                  | Confidence | Main evidence                                                                              |
|------------------------------------------------------------------------|------------|--------------------------------------------------------------------------------------------|
| Stubbier drumlins within about 60 km of the ice limit                  | High       | 4 cold-margin fields + Múlajökull; none beyond 60 km                                       |
| Elongation grows with cumulative slip or time under ice, within fields | Moderate   | Pooled slope +0.21; explains the margin effect; replicates Zoet et al. (2021) in Green Bay |
| Converging flow lengthens drumlins                                     | Moderate   | New York +0.9, Puget +0.4, Green Bay +0.4                                                  |
| One shared coefficient across fields                                   | Rejected   | Per-field slopes range −2.6 to +0.45                                                       |
| Width set by the instability scale, length by growth                   | Suggestive | Width varies 1.8× across fields, length 2.2×                                               |
| Sandier till gives slightly bigger drumlins                            | Moderate   | +2–5% per 10% sand, within 20 km blocks                                                    |

<figure markdown="span">
  [![The drumlin field simulator](assets/simulator.png){ width="520" }](simulator.md)
  <figcaption>Try the <a href="simulator/">interactive simulator</a>: drag the ice and bed sliders and watch a drumlin field grow.</figcaption>
</figure>

## Caveats

- **Who did this.** I'm not a geologist and have no training in glacial geomorphology. The analysis was done with Claude Opus, and drumlin labels came from me and from Claude Opus, Claude Sonnet and Claude Haiku, not from trained mappers.
- **Not peer-reviewed.** No geologist has checked the methods or the conclusions. The claims of novelty rest on a limited literature search.
- **Detection errors.** Blind checks put precision at 67–85% per field, so 15–33% of accepted "drumlins" may be something else (a moraine hummock, a kame, a hill cut by roads).
- **Coarse inputs.** Ice-margin reconstructions are generalised and come in time slices of half a thousand years or more. Cumulative slip comes from a simple ice-profile model, not a calibrated reconstruction. Soil data come from map units, not boreholes.
- **Correlation, not mechanism.** The results describe how drumlin shape varies; they do not show what physically causes it. Each control explains only about 1% of the variation between individual drumlins.
- **Field choice.** The 16 fields are the ones where public elevation data and our detector worked well, not a designed sample.
