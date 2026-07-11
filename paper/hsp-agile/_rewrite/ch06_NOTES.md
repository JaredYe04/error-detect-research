# Ch.6 Rewrite Notes

## Compression
- Original ≈4713 words / 845 lines → rewrite ≈2183 words / 486 lines (**≈54% shorter** by word count; target was ~40%).
- Encyclopedia + FAQ tone removed; protocol stated once.

## Removed (meta)
- “Each RQ answers a reviewer concern” and all “to answer the reviewer” framing.
- Repeated pre-fix vs fixed-oracle disclaimers (now **once** under corpora / measurement correction).
- Duplicated corpus-card prose after Table `tab:corpus-card` (run-id lists, pipeline script names, incremental `progress.json` ETA notes).
- Long per-mode paragraphs for B0–B6/A1–A3 → two short summary paragraphs after `tab:modes`.
- Eight-scenario illustrative enumerate list → one-paragraph skeleton pointing at `compute_tax`.
- Four-paragraph threats preview → **one** short paragraph (full threats remain Ch.8).
- Verbose E1–E17 paragraphs → compact Table `tab:eval-protocol`.
- Long post-hoc power paragraph → two sentences + pointer to `power_analysis.json`.
- Separate E10/E11/real-priority/SMT/E8 subsections → single auxiliary table `tab:aux-benchmarks`.

## Restructured
- RQs kept, mechanism-first, claim-linked, no FAQ language.
- LLM protocol: config + one corpus card + one measurement-correction paragraph + brief reproducibility pointer.
- Eval protocol and auxiliary benchmarks are table-first.
- Modes: keep `tab:modes`; prose is role-grouped (baselines / M+ablations).

## Numbers (AUTHORITATIVE_NUMBERS)
- No invented numbers. Cite via `\input{tables/authoritative_numbers}` and existing run ids.
- Fixed-oracle E1 B1 **84.2%** retained in prose once.
- Equal-$K$ **+2.5 pp** retained in corpus card.
- E12 honesty line kept: B2 100% every seed; M 99.7% mean; do not claim M dominates all seeds.
- Pre-fix ~5% Strict / buggy others-witness stated once.

## Labels preserved
- `ch:experiments`, `tab:claim-map`, `sec:exp:rq`, `sec:exp:environment`, `sec:exp:protocol`, `tab:corpus-card`, `sec:exp:benchmark`, `fig:benchmark-pipeline`, `tab:benchmark-stats`, `sec:exp:e10`, `sec:exp:e11`, `sec:exp:real-priority`, `sec:exp:smt-scalability`, `sec:exp:methods`, `tab:modes`, `sec:exp:mutants`, `sec:exp:metrics`, `sec:exp:eval-protocol`, `sec:exp:stats`, `sec:exp:e12`, `sec:exp:threats-preview`.
- **New labels:** `tab:aux-benchmarks`, `tab:eval-protocol` (compact tables).
- `sec:exp:e11` / `sec:exp:real-priority` / `sec:exp:smt-scalability` co-located after the aux table (no longer separate subsections); cross-refs still resolve.

## Inputs / floats preserved
- `\input{tables/authoritative_numbers}`
- `\tikzinput{diagrams/tikz/benchmark_pipeline}` + `fig:benchmark-pipeline`
- `tab:benchmark-stats`, `tab:modes`, `tab:corpus-card`, `tab:claim-map`
