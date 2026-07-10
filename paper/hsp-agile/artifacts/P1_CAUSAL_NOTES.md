# P1 Causal Clarity Notes (C2 / E6 / E14 / E1)

Purpose: keep C2 claims single-factor-honest. Do not cite fixed-oracle E1 M vs B2 as proof that Semantic Feedback IR alone causes the gain.

---

## Evidence roles

| Claim | Experiment | What is isolated | What is *not* isolated |
|-------|------------|------------------|------------------------|
| **Primary C2** | **E6** (`run_feedback_v2`, dedicated_e6, $n{=}120$) | Feedback *content* under full M, $K{=}3$: test_only / test_expected / semantic_ir | Length-matched structured traces; deployment budget/gate |
| **C2 uniqueness scope** | **E14** (`run_e14_sweep_v1`, $n{=}120$ per variant) | Length-matched feedback surfaces under mode M | Does **not** replace E6 as the lead causal lever vs unstructured feedback |
| **Deployment ranking** | Fixed-oracle **E1** (`run_e1_m_win_v2`) | Aggregate B1/B2/M under strengthened M | **Bundle**, not single-factor C2 |

### E6 (primary C2)

- Isolates feedback content under full M with $K{=}3$.
- Headline: semantic_ir 86.9% vs test_only 79.1% (**+7.7 pp**).
- Cite as: typed Semantic Feedback IR vs *unstructured test-only*, not vs every structured trace.

### E14 (scope uniqueness; paired analysis)

- Aggregate means (authoritative table): test_only 73.8%, test_expected 74.4%, semantic_ir 75.1%, execution_trace_matched **85.4%**.
- Paired per-task mean Conf. (`e14_paired_summary`, from `results.jsonl`):

  | Comparison | Wins | Losses | Ties | Δ mean Conf. |
  |------------|------|--------|------|--------------|
  | semantic_ir vs execution_trace_matched | 5 | 19 | 96 | **−10.3 pp** |
  | semantic_ir vs test_only | 18 | 16 | 86 | **+1.3 pp** |

- Strict-success pairing is near-floor (~5% strict under this run; mostly ties) and should not drive C2 claims—prefer mean Conf.
- Script: `paper/hsp-agile/scripts/e14_paired_analysis.py`
- Outputs: `paper/hsp-agile/data/processed/e14_paired_summary.{json,csv}`

### Fixed-oracle E1 M vs B2 = **bundle** (NOT single-factor C2)

Strengthened M in `run_e1_m_win_v2` differs from B2 in multiple factors at once:

- $K{=}5$ (vs typical B2 / historical $K{=}3$)
- Advisory critical-only pattern gate
- E14-informed `execution_trace_matched` feedback (not bare `semantic_ir`)
- Best-effort $\arg\max$ Conf. over attempts
- `formal_max_cases=32`, stronger field-diff repair hints

Therefore: **do not** write “E1 proves Semantic Feedback IR.” E1 is a near-ceiling deployment stress-test under a multi-knob M.

### Ideal future single-factor experiment

Hold fixed-oracle protocol and all other knobs equal; vary **only** the feedback surface:

- **B2** (test-feedback baseline) vs **M′** that differs solely by rendering Semantic Feedback IR  
  (same $K$, same gate policy, same argmax/best-effort policy, same formal case budget).

Until that run exists, keep C2 anchored on E6 and use E14 only to scope uniqueness.

---

## Optional re-run commands (do not burn API budget casually)

Dry-check / small smoke only unless explicitly approved:

```powershell
# Schema / smoke (cheap): 2 tasks × 4 variants
python experiments/run_e14_sweep.py --run-name run_e14_sweep_smoke --task-limit 2

# Full E14 (expensive; 120 × 4 LLM jobs) — only if regenerating artifacts
# python experiments/run_e14_sweep.py --run-name run_e14_sweep_v2

# Recompute paired W/L/T from existing artifacts (no LLM)
python paper/hsp-agile/scripts/e14_paired_analysis.py --run-dir artifacts/run_e14_sweep_v1
```

Ideal single-factor B2 vs M′ (Semantic IR only) is **not** wired as a one-liner today; would need a dedicated mode or `feedback_variant` sweep with B2-matched $K$/gate. Prefer analysis of existing artifacts over new full-matrix spends.

---

## Paper wording checklist

- [x] C2 in ch01: E6 primary; E14 scopes uniqueness; E1 = bundle
- [x] ch04 FeedbackRenderer / C2 caption: not uniquely best among structured traces
- [x] ch07 E14 + RQ1 answer: paired 5/19/96; single-factor vs bundle
- [x] abstract: E6 lead; E14 numbers; E1 bundle clause
- [x] AUTHORITATIVE_NUMBERS.md cross-ref (below)
