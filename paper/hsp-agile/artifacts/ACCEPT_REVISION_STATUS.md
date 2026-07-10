# CCF-B Accept Revision Status

Status for the HSP-Agile CCF-B Accept push as of 2026-07-10.

## P0 — complete

- Protocol card and fixed-oracle evidence roles are synchronized.
- The abstract leads with E6 typed-feedback evidence, E2 prevention results,
  and C4 deployment framing.

Authoritative run IDs, protocol boundaries, and headline values are recorded in
[AUTHORITATIVE_NUMBERS.md](AUTHORITATIVE_NUMBERS.md).

## P1 — complete

- A1–A3 ablations are explicitly scoped as historical pre-fix evidence.
- Conference and report claims are synchronized.
- E14 paired analysis is recorded and used to bound the uniqueness claim.
- C2 causal wording distinguishes the E6 single-factor result from the bundled
  fixed-oracle E1 deployment comparison.

The causal interpretation and the E14 paired results are documented in
[P1_CAUSAL_NOTES.md](P1_CAUSAL_NOTES.md).

## P2 — complete

- Related-work positioning covers Clover, DafnyBench, Self-Debug/Reflexion,
  and the B6 verifier-loop comparator.
- The conference text states that SgDP complements B2 and does not establish a
  universal M \(>\) B2 ranking.
- The report briefly positions solver-directed witnesses relative to
  QuickCheck/property-based testing.

## Remaining

- **Single-factor B2 vs M′:** optional. Hold budget, gate, selection policy, and
  formal-case budget fixed while varying only the Semantic Feedback IR surface.
  See [P1_CAUSAL_NOTES.md](P1_CAUSAL_NOTES.md).

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
