# HSP-Agile / SgDP — CCF-B Research Report

> **Title:** *A Specification-Guided Defect Prevention Framework for Reliable LLM-Assisted Formal Development*  
> **Format:** A4 report (`report` class + `thesis.sty`), ~120 pages  
> **Target:** CCF-B venues (SANER / ICSME / QRS / ICFEM; stretch ASE/TOSEM)

This directory contains the **expanded CCF-B research report**, upgraded from the short acmart conference draft. It reuses the thesis typography, diagrams, listings, and experimental figures while preserving the **SgDP framework narrative** (RQ1–RQ5, C1–C5, Theorems 1–3, E1–E9).

## Document Structure

| Chapter | File | Content |
|---------|------|---------|
| Front | `front/cover.tex`, `front/abstract.tex` | Title page + abstract |
| Ch 1 | `chapters/ch01_introduction.tex` | SgDP framing, C1–C5, RQ1–5, motivating example |
| Ch 2 | `chapters/ch02_background.tex` | SOFL/FSF, CEGIS, SMT, mutation + positioning table |
| Ch 3 | `chapters/ch03_formalization.tex` | Formal task model, BAP, benchmark formalization |
| Ch 4 | `chapters/ch04_method.tex` | SgDP framework, theorems, pipeline stages |
| Ch 5 | `chapters/ch05_implementation.tex` | System architecture, modules, orchestration |
| Ch 6 | `chapters/ch06_experimental_setup.tex` | RQ1–5, E1–9 protocol, benchmark, modes |
| Ch 7 | `chapters/ch07_results.tex` | Mechanism-first results + all figures |
| Ch 8 | `chapters/ch08_discussion.tex` | Failure analysis, paradox, threats, implications |
| Ch 9 | `chapters/ch09_conclusion.tex` | Findings + future work |
| App A–C | `appendices/app_*.tex` | Reproducibility, benchmark, pattern catalogue |

Legacy short conference sections remain in `sections/` for reference; the **canonical source** is `chapters/`.

## Build

```powershell
# Full pipeline: refresh data → generate figures → compile PDF
powershell -File scripts/build.ps1 -Clean

# Output
# build/main.pdf
```

Requirements: Python 3.12+, matplotlib, pandas, tectonic (`tools/tectonic/tectonic.exe`).

## Figures

| Type | Location | Generator |
|------|----------|-----------|
| Matplotlib (12+6) | `figures/*.pdf` | `figures/scripts/plot_mpl_figures.py` |
| TikZ diagrams | `diagrams/tikz/*.tex` | inline via `\tikzinput{}` |
| PlantUML | `diagrams/puml/rendered/*.pdf` | `scripts/render_puml.py` (Kroki) |

CCF-B mechanism figures (E3–E9) use proxy data until full experiment runs complete; replace with real CSVs when available.

## Related Artifacts

- `artifacts/UPGRADE_ROADMAP.md` — 12-week milestone plan
- `artifacts/EXPERIMENT_MATRIX.md` — E1–E9 specifications
- `artifacts/CONTRIBUTION_REFRAME.md` — old vs new C1–C5 mapping
- `artifacts/PAPER_ASSETS.md` — figure/table checklist

## Typography

Formatting matches `paper/thesis/` via shared `thesis.sty`:

- A4, 12pt, 1.5 line spacing, fancy headers
- `\widefig{}`, `\tikzinput{}`, `\pumlfig{}` for figures
- `\inputfsf{}`, `\inputpython{}` for code listings
- `plainnat` numbered citations
