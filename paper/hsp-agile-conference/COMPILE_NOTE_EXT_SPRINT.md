# Conference compile note (External Evidence Sprint Phase 6)

Local MiKTeX cannot fetch packages (`IEEEtran` installed manually as
`paper/hsp-agile-conference/IEEEtran.cls`; remote repo offline / SSL issues).
Docker Desktop engine not running. Prior `main.pdf` was ~9 pages before this
sprint; added content is one compact Screen table + ~1 paragraph of prose.
**Expected page count: ≤10** (monitor on a full TeX Live / Overleaf build).

Restore path when online:
```
latexmk -pdf -interaction=nonstopmode main.tex
```
