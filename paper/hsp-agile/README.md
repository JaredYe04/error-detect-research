# HSP-Agile Paper Workspace

This folder contains a modular LaTeX manuscript draft and full data/figure provenance pipeline.

## Structure

- `main.tex`: manuscript entrypoint (`acmart` format)
- `sections/`: section-wise modular text
- `tables/`: reusable table modules (notation, stats)
- `bib/references.bib`: bibliography database
- `data/raw/` and `data/processed/`: paper data sources
- `figures/scripts/`: figure generation code
- `figures/FIGURE_MANIFEST.json`: figure-to-data-and-command provenance map
- `scripts/prepare_paper_data.py`: artifact-to-paper ETL
- `scripts/refresh_paper_assets.py`: one-shot data refresh + figure regeneration

## Commands

```bash
python paper/hsp-agile/scripts/prepare_paper_data.py
python paper/hsp-agile/figures/scripts/plot_paper_figures.py
python paper/hsp-agile/scripts/refresh_paper_assets.py
```

Install plotting/export dependencies:

```bash
pip install plotly kaleido
```

If Kaleido cannot start Chrome in your environment, install a compatible bundled browser:

```bash
choreo_get_chrome
```

Regenerate publication-ready figures (interactive HTML + static PNG/PDF) with deterministic settings:

```bash
python paper/hsp-agile/figures/scripts/plot_paper_figures.py --static-formats png pdf --dpi 300 --seed 7
```

Run one-shot data refresh + figure regeneration:

```bash
python paper/hsp-agile/scripts/refresh_paper_assets.py --static-formats png pdf --dpi 300 --seed 7
```

If LaTeX is installed:

```bash
cd paper/hsp-agile
latexmk -pdf main.tex
```

## Template Basis

The manuscript follows ACM-style (`acmart`) layout conventions and references the local template source under:

- `paper/template-acmart/`

## Notes

- All figures in the manuscript should be generated from scripts, not manually edited.
- Statistical values in `tables/stats_summary.tex` should be refreshed after final experiment runs.
