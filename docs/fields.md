# Fields

Fifteen fields passed quality control with the corrected classifier (one cutoff, 0.6, everywhere). Rows are sorted by median elongation. Between-field differences are not explained by anything we tested, so treat the ordering as descriptive.

| Field | Median L (m) | Median W (m) | Median E | Drumlins | Precision | Ice sheet | Dist. inside limit (km) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Menominee, MI | 660 | 197 | 3.22 | 1,122 | 0.70* | Laurentide | 125 |
| Central New York | 712 | 217 | 3.17 | 3,329 | 0.75† | Laurentide | 157 |
| Green Bay lobe, WI | 658 | 220 | 2.89 | 3,345 | 0.77† | Laurentide | 52 |
| Magellan–Otway, Chile | 643 | 216 | 2.87 | 382 | 0.80 | Patagonian | 28 |
| Langlade, WI | 780 | 261 | 2.82 | 566 | 0.59 | Laurentide | 42 |
| Antrim–Charlevoix, MI | 736 | 248 | 2.79 | 759 | 0.81 | Laurentide | 296 |
| Puget Lowland, WA | 834 | 289 | 2.78 | 1,180 | 0.54† | Cordilleran | 26 |
| Peterborough, ON | 684 | 242 | 2.74 | 181 | 0.82* | Laurentide | 231 |
| Pierz, MN | 722 | 258 | 2.66 | 211 | 0.81 | Laurentide | 50 |
| Leelanau, MI | 601 | 224 | 2.66 | 139 | 0.74* | Laurentide | 262 |
| Toimi, MN | 865 | 322 | 2.55 | 300 | 0.71 | Laurentide | 218 |
| Vale of Eden, England | 632 | 263 | 2.29 | 485 | 0.79 | British–Irish | 99 |
| Branch County, MI | 629 | 285 | 2.27 | 158 | 0.79 | Laurentide | 262 |
| Washington County, NY | 546 | 232 | 2.27 | 321 | 0.55* | Laurentide | 272 |
| Cavan–Monaghan, Ireland | 515 | 253 | 1.97 | 1,129 | 0.81 | British–Irish | 219 |

- **Precision** is the estimated share of accepted hills that are drumlins, from the 48 blind cards per field, weighted by how common each card group is.
    - Unmarked values are from cards labelled by Claude Opus.
    - An asterisk (\*) marks cards labelled by Claude Sonnet.
    - A dagger (†) marks cross-validation on the training labels.
    - All labels come from non-experts (James and Claude models).
- **Distance** is the field's median distance inside the maximum ice limit.
- **Múlajökull** (88 drumlins, 4 m ArcticDEM) was analysed separately.

## Excluded

- **Chippewa lobe, WI:** precision about 0.1 with the corrected classifier. It passed the first version only at a very high cutoff on the shape-based classifier.
- **Wadena, MN:** formed before the last glacial maximum, so it falls outside the ice-margin reconstruction.
- **Eastern Massachusetts, Bahía Inútil (Tierra del Fuego), Iron County MI, Alpena MI:** precision 0.22–0.47 in the first version.
- **Stargard and Zbójno, Poland:** too few drumlins, even with lidar.
- **Fox Valley, WI:** precision 0.62 in the first version.
- **Polk County WI, Guelph ON, Brainerd MN:** too few accepted drumlins.

The first version's table, with 16 fields and per-field cutoffs, is kept as `data/accepted_drumlins_v1.csv` in the repository.
