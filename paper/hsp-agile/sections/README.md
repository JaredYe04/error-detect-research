# Legacy short sections (deprecated)

The canonical paper source is **`chapters/`** (thesis-style 9-chapter report).

The files in `sections/` (`01_introduction.tex` through `07_conclusion.tex`) are
retained as reference from the original acmart 12-page draft. They are **not**
included in `main.tex` and should not be edited for publication updates.

To build the paper:

```powershell
powershell -File paper/hsp-agile/scripts/build.ps1 -Clean
```

Data and figures are refreshed automatically via `scripts/refresh_paper_assets.py`.
