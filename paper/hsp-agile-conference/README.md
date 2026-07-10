# HSP-Agile Conference Cut (strict ≤10 pages)

IEEE `IEEEtran` conference class. Self-contained `main.tex`.

## Build

```powershell
cd paper/hsp-agile-conference
C:\Users\tange\tectonic.exe -X compile main.tex
```

Bibliography: `../hsp-agile/bib/references.bib`.

## Page budget (target 9–10, never >10)

| Section | Est. |
|---------|------|
| Abstract + keywords | 0.3 |
| Intro | 1.0 |
| Related | 0.8 |
| Approach (+ alg) | 1.5 |
| Setup | 0.8 |
| Results (tables/figs) | 3.5 |
| Discussion + Conclusion | 1.0 |
| References | ~1.0 |
| **Total** | **~9–10** |

After compile: `python -c "from pypdf import PdfReader; print(len(PdfReader('main.pdf').pages))"`.

## Claims (must match AUTHORITATIVE_NUMBERS)

- E6 +7.7 pp; 14/4/102; CI [2.3,13.6]; p=0.018
- E2 PDR/FAR; C4 B2 default
- Equal-K M_eq +2.5 pp
- Published-industrial pilot + industrial-pattern for external validity
- Vendor `.asfl`: see `vendor/README.md` / `REQUEST_TEMPLATE.md`
