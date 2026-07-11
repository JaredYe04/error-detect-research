# Legacy short sections (deprecated)

The canonical paper source is **`chapters/`** (thesis-style 9-chapter report).

The files in `sections/` (`01_introduction.tex` through `07_conclusion.tex`) are
retained as reference from the original acmart 12-page draft. They are **not**
included in `main.tex` and should not be edited for publication updates.

**Deprecation notice:** this directory is legacy. Many values remain as
`\texttt{TBD}` placeholders from the short draft; all publication-ready numbers,
figures, and narrative live under `chapters/`. Do not copy TBD placeholders into
the canonical report.

To build the paper:

```powershell
powershell -File paper/hsp-agile/scripts/build.ps1 -Which all
```

Data and figures are refreshed automatically via `scripts/refresh_paper_assets.py`.
