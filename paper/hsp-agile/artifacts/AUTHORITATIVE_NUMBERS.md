# Authoritative Numbers Card

One-page map of which run ids to cite for E1 / E6 / E2 / E12 / E10.
**Cite fixed-oracle M-win runs for E1 / E12 / E10**; do not invent numbers.

Campaign script: `paper/hsp-agile/scripts/run_m_win_campaign.ps1`

---

## Corpus / protocol card (cite from papers)

Papers must distinguish three corpora. Do not mix numbers across rows.

| Role | Experiments | Authoritative run id(s) | Protocol notes | Cite as |
|------|-------------|-------------------------|----------------|---------|
| **Primary ranking** (fixed others-witness oracle) | E1, E10, E12, **A1–A3 ablation** | `run_e1_m_win_v2`, `run_e10_m_win_v1`, `run_e12_m_win_v1`, **`run_e1_ablation_fixed_v1`** | Strengthened M: $K{=}5$ bundle — **stress-test only** | B1/B2/M Conf / Strict; ablation Δ |
| **Equal-K Conf.** | B2 vs M_eq | **`run_e1_equal_k_v1`** | Both $K{=}3$; M_eq uses `semantic_ir` + advisory gate | **Primary equal-K Conf ranking** (+2.5 pp) |
| **Mechanism / prevention** | E6, E2 | `run_feedback_v2`, `prevention_full_v1` | E6: $K{=}3$ feedback isolation (**lead C2**); E2: PDR/FAR | +7.7 pp (CI excludes 0); PDR/FAR |
| **Historical pre-fix** | archive only | `run_e1_canonical_v1` / `run_hard_full_parallel_v1` | Buggy others-witness (~5% Strict) | Label historical; never primary |

**Causal clarity (P1):** Fixed-oracle E1 M vs B2 is a **bundle** ($K{=}5$, advisory gate, `execution_trace_matched`, argmax)—**not** single-factor C2. E14 scopes uniqueness (`semantic_ir` 75.1% ≠ `execution_trace_matched` 85.4%; paired mean Conf. 5/19/96). See `artifacts/P1_CAUSAL_NOTES.md`.

**Quick primary numbers (fixed oracle):** E1 B1 84.2% / B2 98.3% / M 100.0%; E10 B1 81% / B2 99% / M 100%; E12 B1 88.6% / B2 100% / M 99.7% (B2 first every seed).  
**Published-industrial pilot (`run_pubind_pilot_v1`, n=10):** B1 80.0% / B2 100.0% / M_eq 100.0% (equal K=3). Supports C4 default B2. Corpus: `benchmarks/published_industrial_pilot.json` (reconstructed from published railway/ATM/banking SOFL cases; not proprietary dumps). Vendor `.asfl` import: `vendor/README.md`.

---

## Authoritative run ids

| Exp | Role | Current (pre–M-win) | M-win target | Status |
|-----|------|---------------------|--------------|--------|
| **E1** | Main table (B1/B2/M), stress-test | `run_e1_canonical_v1` (840 jobs; **superseded for B1/B2/M**) | `run_e1_m_win_v2` | **filled** (fixed others-witness oracle) |
| **E6** | Feedback variants (test-only / test+expected / semantic_ir) | `run_feedback_v2` (`dedicated_e6`, n=120) | — (unchanged; E14 is length-matched companion) | canonical |
| **E2** | Prevention PDR/FAR (impl-screening n=852; pooled n=1704) | `prevention_eval/prevention_full_v1` | — (prevention eval separate from M-win Conf campaign) | canonical |
| **E12** | Multi-seed stability (B1/B2/M × 3 seeds) | `run_e12_canonical_v1` (1080 jobs; historical) | `run_e12_m_win_v1` | **filled** (fixed others-witness oracle) |
| **E10** | Unfiltered random benchmark (B1/B2/M) | `run_e10_random_v2` (300 jobs; historical) | `run_e10_m_win_v1` | **filled** (fixed others-witness oracle) |

Related (not in M-win campaign): E14 `run_e14_sweep_v1`; E16 `run_e16_canonical_v1`; E17 `run_e17_advisory_v1`; **equal-K** `run_e1_equal_k_v1` (B2 vs M_eq, K=3).

Benchmark fingerprint (E1/E12 canonical): `322157816b37c34e`.

**Measurement correction (critical):** a bug in others-witness generation (others encoded as `True` without ¬prior guards) previously inflated false failures (~5% Strict / ~86–89% Conf on canonical E1). Fixed first-match others witnesses in `src/formal/fsf_eval.py` and `first_match_oracle` in `checker.py`. Frame as enabling fair evaluation—do not hide.

Pipeline strengthenings in `run_e1_m_win_v2` / E10 / E12 M-win: best-effort argmax Conf over attempts; `execution_trace_matched` feedback (E14-informed); advisory pattern gate (critical-only hard block) for default M; $K{=}5$ for M; `formal_max_cases=32`; stronger field-diff repair hints.

Refresh after M-win E1:
```
python paper/hsp-agile/scripts/refresh_paper_assets.py --run-dir artifacts/run_e1_m_win_v2
```

---

## E1 equal-K (`run_e1_equal_k_v1`, n=120, B2 vs M_eq, both K=3)

| Mode | Mean Conf. | Paired vs B2 |
|------|------------|--------------|
| B2 | 97.5% | — |
| M_eq | **100.0%** | **+2.5 pp; wins 3 / losses 0 / ties 117** |

- Protocol: `--modes B2 M_eq --force-max-attempts 3 --repeats 1`
- M_eq = formal + semantic_ir + advisory gate at K=3 (not the K=5 bundle)
- Cite as **primary equal-K Conf ranking**; lead mechanism remains E6
- Source: `artifacts/run_e1_equal_k_v1` via `summarize_equal_k.py`

---

## E1 authoritative (`run_e1_m_win_v2`, n=120, fixed others-witness oracle)

| Mode | Mean Conf. | Strict success | Mean llm_calls |
|------|------------|----------------|----------------|
| B1 | 84.2% | 84.2% | 1.00 |
| B2 | 98.3% | 98.3% | ~1.18 |
| M | **100.0%** | **100.0%** | ~1.16 |

- **M vs B2:** +1.7 pp; wins 2/120, losses 0, ties 118 (report win rate / means; no Holm claim unless computed).
- Latency (mean ms): B1 17{,}193; B2 9{,}576; M 10{,}457.
- Source: `artifacts/run_e1_m_win_v2/results.jsonl` via `summarize_m_win.py`.

### Historical pre-fix E1 (`run_e1_canonical_v1`, seed 0, n=120) — do not cite as primary

| Mode | Mean Conf. | Strict success |
|------|------------|----------------|
| B0 / B1 | 89.2% | 5.0% |
| B2 | 87.7% | 5.0% |
| M | 86.3% | 5.0% |
| A1 | 85.5% | 5.0% |
| A2 | 80.3% | 5.0% |
| A3 | 82.4% | 3.3% |

Inflated false failures from the others-witness bug; pre-fix A1–A3 Conf.
deltas (−0.8 / −6.0 / −3.9 pp vs. M 86.3%) are **historical only**.

### Fixed-oracle ablation (`run_e1_ablation_fixed_v1`, n=120; vs M on `run_e1_m_win_v2`)

Matched to strengthened M ($K{=}5$ where repair applies, `formal_max_cases=32`,
`execution_trace_matched`, advisory gate):

| Mode | Removed | Mean Conf. | Δ vs M |
|------|---------|------------|--------|
| M | — | 100.0% | — |
| A1 | formal checker | 82.5% | **−17.5 pp** |
| A2 | pattern guard | 100.0% | **0.0 pp** |
| A3 | repair loop | 74.2% | **−25.8 pp** |

**Primary Conf. ranking:** A3 > A1 > A2 (by |Δ|). A2's zero Conf. delta under
advisory gate + ceiling is expected—cite E2 PDR/FAR for the guard. Script:
`paper/hsp-agile/scripts/summarize_ablation_fixed.py`.

---

## Unchanged mechanism / prevention numbers

\subsection{E6 (`run_feedback_v2`)

| Variant | Mean Conf. |
|---------|------------|
| A test_only | 79.1% |
| B test_expected | 78.9% |
| C semantic_ir | 86.9% |

C−A = **+7.7 pp** (primary typed-IR / single-factor C2 claim). Source: `feedback_variant_summary.csv`.

**Paired stats** (`e6_paired_summary.json`; `scripts/e6_paired_analysis.py`):

| Contrast | W/L/T | Δ (pp) | 95% CI (pp) | Wilcoxon p |
|----------|-------|--------|-------------|------------|
| C−A | 14/4/102 | +7.7 | [2.3, 13.6] | 0.018 |
| C−B | 14/4/102 | +8.0 | [2.2, 14.0] | 0.027 |

Both CIs exclude 0. Paper table: `tables/e6_paired_stats.tex`.

**Paired stats** (`e6_paired_summary.json`, script `e6_paired_analysis.py`):

| Contrast | W/L/T | Δ (pp) | 95% CI (pp) | Wilcoxon p |
|----------|-------|--------|-------------|------------|
| C−A | 14/4/102 | +7.7 | [2.3, 13.6] | 0.018 |
| C−B | 14/4/102 | +8.0 | [2.2, 14.0] | 0.027 |

Both CIs exclude zero. Cite Table `tab:e6-paired` in papers.

### E14 (`run_e14_sweep_v1`) — uniqueness scope, not primary C2

| Variant | Mean strict Conf. |
|---------|-------------------|
| test_only | 73.8% |
| test_expected | 74.4% |
| semantic_ir | 75.1% |
| execution_trace_matched | **85.4%** |

Paired mean Conf. (`e14_paired_summary`): semantic_ir vs execution_trace_matched **5 / 19 / 96** (W/L/T, −10.3 pp); vs test_only 18 / 16 / 86 (+1.3 pp). Script: `paper/hsp-agile/scripts/e14_paired_analysis.py`. Details: `P1_CAUSAL_NOTES.md`.

### E2 (`prevention_full_v1`, impl-screening n=852)

| Mode | PDR | FAR |
|------|-----|-----|
| B2 | 91.2% | 8.8% |
| M | 95.0% | 5.0% |

Abstract cites M PDR 95.0% / FAR 5.0% vs B2. Source: `prevention_summary.json` → `by_eval_type.*.impl_screening`.

---

## E12 authoritative (`run_e12_m_win_v1`, 120 × 3 seeds × B1/B2/M = 1080, fixed oracle)

| Mode | Mean Conf. (across seeds) | Seed 0 | Seed 1 | Seed 2 |
|------|---------------------------|--------|--------|--------|
| B1 | 88.6% | 95.0% | 75.8% | 95.0% |
| B2 | **100.0%** | 100.0% | 100.0% | 100.0% |
| M | 99.7% | 100.0% | 99.2% | 100.0% |

- **Ranking:** B2 first every seed (ties with M at 100% on seeds 0 and 2).
- **Mean-across-seeds pairing M vs B2:** wins 0, losses 1, ties 119.
- **One M failure:** seed1 HardCase069 (Conf 0).
- **Honest framing:** both near ceiling; E1/E10 show M≥B2 on aggregate; E12 shows B2 slightly more seed-stable (100.0% vs 99.7%). **Do not claim M dominates all seeds.**
- Source: `artifacts/run_e12_m_win_v1` via `summarize_m_win.py`.

### Historical pre-fix E12 (`run_e12_canonical_v1`) — do not cite as primary

| Mode | Mean Conf. (across seeds) |
|------|---------------------------|
| B1 | 86.1% |
| B2 | 88.0% |
| M | 86.0% |

B2 led all seeds; M wins 4/120; Friedman p=0.077. Superseded by fixed-oracle E12.

---

## E10 authoritative (`run_e10_m_win_v1`, n=100 unfiltered random, fixed oracle)

| Mode | Mean Conf. |
|------|------------|
| B1 | 81.0% |
| B2 | 99.0% |
| M | **100.0%** |

- **M vs B2:** +1.0 pp; wins 1/100, losses 0, ties 99.
- Source: `artifacts/run_e10_m_win_v1` via `summarize_m_win.py`.

### Historical pre-fix E10 (`run_e10_random_v2`, n=100) — do not cite as primary

| Mode | Mean Conf. |
|------|------------|
| B1 | 83.9% |
| B2 | 89.1% |
| M | 83.1% |

Buggy others-witness oracle; superseded by `run_e10_m_win_v1`.

---

## M-win fill-in checklist

- [x] `TODO_M_WIN` E1: Conf / strict from `artifacts/run_e1_m_win_v2`
- [x] `TODO_M_WIN` E12: seed means from `run_e12_m_win_v1` (under fixed oracle)
- [x] `TODO_M_WIN` E10: B1/B2/M Conf from `run_e10_m_win_v1` (under fixed oracle)
- [x] Update abstract / chapters / conference stubs for E1 / E10 / E12
- [x] Point prose citations at `run_e1_m_win_v2`, `run_e10_m_win_v1`, `run_e12_m_win_v1`
