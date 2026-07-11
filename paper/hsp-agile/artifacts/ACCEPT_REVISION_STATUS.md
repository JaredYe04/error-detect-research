# CCF-B Accept Revision Status

Status for the HSP-Agile CCF-B Accept push as of 2026-07-10.

## P0 — complete

- Protocol card and fixed-oracle evidence roles are synchronized.
- The abstract leads with E6 typed-feedback evidence, E2 prevention results,
  and C4 deployment framing.

Authoritative run IDs, protocol boundaries, and headline values are recorded in
[AUTHORITATIVE_NUMBERS.md](AUTHORITATIVE_NUMBERS.md).

## P1 — complete (updated 2026-07-11)

- Fixed-oracle A1–A3 promoted: A3 −25.8 / A1 −17.5 / A2 0.0 (advisory+ceiling).
- Equal-K `M_eq` +2.5 pp cited in abstract / Ch7 / conference.
- E14 paired analysis scopes C2 uniqueness.
- Strengthening-sprint IR uniqueness: **partial** — see
  `strengthening_sprint/DATA_VERDICT.md`; gemini combo n=40 expand running.

## Remaining

- **Gemini combo n=40** (`run_ir_combo_seed_gemini_n40_v1`): expand only non-saturated
  endpoint; promote to paper **only if** CI-stable FULL−A / FULL−B across seeds.
- **Single-factor B2 vs M′ (semantic_ir only):** optional; equal-K M_eq already
  closer than K=5 bundle.

## Paper sync checklist

| Artifact | Status |
|----------|--------|
| Long-paper Ch6 protocol card | Done |
| Abstract / Ch1 / Ch9 lead = E6+E2+C4 | Done |
| Ch7 ablation **fixed-oracle primary** (A3 −25.8 / A1 −17.5 / A2 0.0) | Done |
| Conference stubs + README | Done |
| E14 paired W/L/T | Done (`e14_paired_summary`) |
| Ch2 repair-loop table caption | Done |
| `stats_summary.tex` pre-fix note | Done |
| `run_e1_ablation_fixed_v1` (360 jobs) | Done |
