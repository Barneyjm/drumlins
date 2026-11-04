# Rerun after peer review (Nov 4, 2026)

Scripts in this folder: train_sb.py, rescore.py, precision.py, perdrumlin_rr.py, margin_rr.py, prec_by_dist.py, cumslip.py/cumslip_test.py (copies run on the new selection), conv_null.py.

## Classifier selection bias (confirmed)
- Original pooled model: blocked-CV ROC-AUC 0.859. Among labelled true drumlins, Spearman(score, E) = 0.61. At cutoff 0.7 the accepted median E is 3.25 against 2.63 for all true drumlins (+24%).
- Shape-light model (length, width, elongation removed; orientation-alignment kept): AUC 0.842, Spearman(score, E | true) = 0.30, accepted median E at 0.7 = 2.67.
- Shape-blind model (all shape and orientation removed): AUC 0.711, too weak to use.
- New selection: shape-light, one cutoff of 0.6 everywhere; 13,825 drumlins. Spot-check precision is 0.70–0.82 in most fields, Langlade 0.59, Washington Co. 0.55, Chippewa 0.08 (drop Chippewa).

## Between-field
- Field median elongation falls in most fields (Chippewa 3.52 to 2.49, Toimi 3.32 to 2.55). Central New York rises (2.84 to 3.17); it had the lowest old cutoff, 0.25.
- Rank agreement of field median E, old vs new: Spearman 0.32.
- Width vs length spread (excluding Chippewa): SD of log median W 0.130, L 0.143. Ranges: W 196–321 m, L 515–865 m. "Width nearly fixed, length varies" does not survive.

## Margin gradient (survives, stronger)
- Within 60 km: +0.237 ± 0.026 (5 km block-clustered SE); mixed model with a random slope per field +0.282 ± 0.109 (p 0.010).
- Cold-margin fields (GB, LG, PZ, MO): +0.323 ± 0.031; mixed model +0.373 ± 0.124 (p 0.003). Puget is still 0.00.
- 0–10 km bin: −25.8% (old −15.5%).
- Precision by distance (shape-light, labelled cards): 0–20 km 0.38 (29 cards), 20–60 km 0.72 (192), beyond 60 km 0.88 (50). False positives are stubbier (median E 2.1 vs 3.26).
- Labelled true drumlins only (no classifier; n = 234 within 60 km, 5 fields): slope +0.267 ± 0.086 (p 0.002); Green Bay alone +0.56 ± 0.17.
- Stricter cutoffs strengthen the slope: 0.7 gives +0.27, 0.8 gives +0.32, 0.9 gives +0.41.

## Convergence (survives, stronger)
- New York +1.20 (old +0.92), Puget +0.65 (old +0.38), Green Bay +0.54 jointly with distance (old +0.41).
- Null test: uniform flow plus elongation-dependent azimuth noise (rms deviation 13° at low E to 4° at high E) gives a mean null slope of about 0 in all three fields, so orientation noise does not create the correlation.

## Cumulative slip (does not add beyond distance)
- Pooled +0.265 ± 0.046, but with distance capped at 60 km in the same model: slip −0.10 (p 0.37), distance +0.33. Leave-one-field-out prediction fails. Per-field slopes range from −2.75 to +1.16.
- This confirms the reviewer's point: in this model, slip is a re-expression of distance and time.
