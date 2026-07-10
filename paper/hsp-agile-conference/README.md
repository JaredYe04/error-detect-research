# HSP-Agile — ICSME/SANER 10-page submission cut

Condensed from the full report in `paper/hsp-agile/`.
Target: ~8–10 pages two-column (Weak-Accept draft quality). Mechanism-first;
honest that **B2 ≥ M on aggregate Conf.**

## Claim scope (do not overclaim)

| Claim | Scope | Not claimed |
|-------|--------|-------------|
| E6 +7.7 pp | Full Semantic IR vs **unstructured test-only** under M ($n{=}120$, $K{=}3$) | Uniqueness vs any structured trace |
| E14 | `semantic_ir` 75.1% vs `execution_trace_matched` 85.4% | Contradicts “IR always best feedback” |
| E2 | M PDR 95.0 / FAR 5.0 vs B2 91.2 / 8.8 | M wins mean Conf. |
| E1 / E12 | B1 89.2, B2 87.7, M 86.3; E12 B2 all seeds (88.0 vs 86.0) | M beats B2 on Conf. |
| Deploy | **B2 default**; M when Accept / PDR–FAR needed | Universal mode ranking |

Canonical numbers also used: E10 B2 89.1 vs M 83.1; E3 non-monotone tertiles;
ablation Conf Δ A1 −0.8, A2 −6.0, A3 −3.9; B6 full $n{=}120$: B2 88.2, B6 81.1, M 82.0.

## Build

From this directory (paths resolve relative to `main.tex`):

```bash
cd paper/hsp-agile-conference
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Requires `../hsp-agile/bib/references.bib` and
`../hsp-agile/figures/performance_vs_overlap.pdf`.
Stubs live in `../hsp-agile/sections/conference/*.tex`.

## Structure

| Section | Stub | Content focus |
|---------|------|----------------|
| Intro | `intro_stub.tex` | `classify_signal` motivation; C2 lead + E14 caveat; C3; C4 |
| Related | `related_stub.tex` | Clover, DafnyBench, Self-Refine/Debug, Reflexion, B6 |
| Approach | `approach_stub.tex` | SpecIR, Semantic IR, Accept eq., $K{=}3$ |
| Setup | `setup_stub.tex` | BENCH-120, E10/E11/E8c, B1/B2/M/A1/A3, Qwen2.5-27B |
| Results | `results_stub.tex` | E6→E14→main table→E12/B6→E3/E10→deploy→E2 |
| Discussion | `discussion_stub.tex` | Deploy + threats (merged) |
| Conclusion | `conclusion_stub.tex` | C1–C4; B2 default |

Main-text modes: **B1, B2, M, A1, A3**. B3–B5 / A2 / B6 detail in supplementary
(full report / appendix).

See `paper/hsp-agile/artifacts/CONFERENCE_10PAGE_OUTLINE.md` for the figure list.
