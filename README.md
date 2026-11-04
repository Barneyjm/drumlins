# How Drumlins Form: Evidence from 15 Fields

An amateur, not peer-reviewed study of drumlin shape across 15 drumlin fields in North America, Britain, Ireland and Patagonia, plus the active drumlin field at Múlajökull, Iceland.

**Read it:** https://barneyjm.github.io/drumlins/

The short version: within a drumlin field, drumlins are stubbier near the old ice edge and longer where ice flow converged, which fits drumlins lengthening the more (or faster) ice slid over them. Differences between fields remain unexplained. The write-up was revised on Nov 4, 2026 after a review found a shape bias in the original classifier; see the site's "What changed after review" section.

## What's here

- `docs/` – the write-up (MkDocs Material), the margin-gradient chart and the interactive drumlin-field simulator
- `data/` – the 13,607 accepted drumlins (plus the first version's 17,593 for comparison), per-drumlin and field-level results, SSURGO soils, Múlajökull data and the training labels
- `models/` – the pooled drumlin classifier
- `code/` – the detection, classification and analysis scripts (see [Code and data](docs/code-and-data.md) for the layout and caveats)

## Building the site locally

```bash
pip install "mkdocs<2" "mkdocs-material<10" mkdocs-glightbox
mkdocs serve
```

Every push to `main` rebuilds the site through GitHub Actions (`.github/workflows/pages.yml`).

## Credits

Research by James, with Anthropic's Claude Opus doing the analysis. Claude Opus, Claude Sonnet and Claude Haiku were used alongside James as drumlin labellers.

## License

MIT (see `LICENSE`). Third-party data sources keep their own terms; see the Sources page.
