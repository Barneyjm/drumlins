# How Drumlins Form: Evidence from 16 Fields

A study of drumlin shape across 16 drumlin fields in North America, Britain, Ireland and Patagonia, plus the active drumlin field at Múlajökull, Iceland.

**Read it:** https://barneyjm.github.io/drumlins/

The short version: drumlins form in two stages. A bed instability under sliding ice sets their starting size, and they keep lengthening for as long as ice flows over them. Within a field, elongation rises with time under ice, cumulative slip and converging flow; between fields, nothing tested explains the differences.

## What's here

- `docs/` – the write-up (MkDocs Material), the margin-gradient chart and the interactive drumlin-field simulator
- `data/` – the 17,593 accepted drumlins, per-drumlin and field-level results, SSURGO soils, Múlajökull data and the training labels
- `models/` – the pooled drumlin classifier
- `code/` – the detection, classification and analysis scripts (see [Code and data](docs/code-and-data.md) for the layout and caveats)

## Building the site locally

```bash
pip install "mkdocs<2" "mkdocs-material<10"
mkdocs serve
```

Every push to `main` rebuilds the site through GitHub Actions (`.github/workflows/pages.yml`).

## Credits

Research by James, with Anthropic's Claude Opus doing the analysis. Claude Opus, Claude Sonnet and Claude Haiku were used alongside James as drumlin labellers.
