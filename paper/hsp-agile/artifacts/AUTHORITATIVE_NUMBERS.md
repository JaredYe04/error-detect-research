# Authoritative Numbers Card

One-page map of which run ids to cite for E1 / E6 / E2 / E12 / E10.
**Cite fixed-oracle M-win runs for E1 / E12 / E10**; do not invent numbers.

Campaign script: `paper/hsp-agile/scripts/run_m_win_campaign.ps1`

---

## Pre-expansion snapshot (External Evidence Sprint Phase 0)

Frozen before `run_github_harvest_v2` / `run_ext_hardseed_e6_v2` / `run_prevention_external_v1` (2026-07-12). Do not overwrite; cite as baseline.

| Corpus / claim | n / figure | Run / note |
|----------------|------------|------------|
| GitHub harvest ranking | n=48; B1 85.8% / B2 89.9% / M_eq 89.9% | `run_github_harvest_v1` |
| HKCA09 SOFL→FSF ranking | n=35; B1 74.3% / B2 100% / M_eq 100% | `run_hkca09_b1b2m_v1` |
| Published-industrial desensitized | n=28; B1/B2/M_eq 100% | `run_desens_real_sofl_v1` |
| Ext hard-seed protocol (Conf.\<1) wrong_relop | n=76, Δ+20.7 pp | `run_ext_hardseed_e6_v1` |
| Ext pooled headroom (Conf.\<1) | n=183, Δ+18.3 pp | same protocol artifact |

Run-dir convention for this sprint: `artifacts/run_github_harvest_v2/`, `artifacts/run_ext_hardseed_e6_v2/`, `artifacts/run_prevention_external_v1/`.

---

## Corpus / protocol card (cite from papers)

Papers must distinguish three corpora. Do not mix numbers across rows.

| Role | Experiments | Authoritative run id(s) | Protocol notes | Cite as |
|------|-------------|-------------------------|----------------|---------|
| **Primary ranking** (fixed others-witness oracle) | E1, E10, E12, **A1–A3 ablation** | `run_e1_m_win_v2`, `run_e10_m_win_v1`, `run_e12_m_win_v1`, **`run_e1_ablation_fixed_v1`** | Strengthened M: $K{=}5$ bundle — **stress-test only** | B1/B2/M Conf / Strict; ablation Δ |
| **Equal-K Conf.** | B2 vs M_eq | **`run_e1_equal_k_v1`** | Both $K{=}3$; M_eq uses `semantic_ir` + advisory gate | **Primary equal-K Conf ranking** (+2.5 pp) |
| **Mechanism / prevention** | E6, E2 | `run_feedback_v2`, `prevention_full_v1` | E6: $K{=}3$ feedback isolation (**lead C2**); win profile: 13/14 zero test-only, others/arithmetic (not ordering-uniqueness); E2: PDR/FAR | +7.7 pp (CI excludes 0); PDR/FAR |
| **Hard-seed C2 support** | combo seeds @ gemini | **`run_ir_combo_seed_gemini_n40_v1` + `extra40_v1` (pooled n=80)**; **field ablation on n40** | $n{=}80$×3 seeds; freeze buggy code → one T=0 repair; field cells $n{=}120$ | Supporting: FULL vs test_only **+26.5 pp**; FULL vs **ir_nl_only +28.0 pp** (CI excl 0); single-field drops CI include 0 |
| **Historical pre-fix** | archive only | `run_e1_canonical_v1` / `run_hard_full_parallel_v1` | Buggy others-witness (~5% Strict) | Label historical; never primary |

**Causal clarity (P1):** Fixed-oracle E1 M vs B2 is a **bundle** ($K{=}5$, advisory gate, `execution_trace_matched`, argmax)—**not** single-factor C2. E14 scopes uniqueness (`semantic_ir` 75.1% ≠ `execution_trace_matched` 85.4%; paired mean Conf. 5/19/96). See `artifacts/P1_CAUSAL_NOTES.md`.

**CCF-B Accept revision protocol:** cite `tables/master_protocol.tex` as the single
protocol map. Do not mix $K$, feedback renderer, gate mode, or corpus across
claims.

**E6 headroom strata (`data/processed/e6_headroom_summary.*`):**
all tasks C--A $+7.7$ pp (14/4/102; CI $[2.3,13.6]$ in prose / paired table);
test-only Conf. $<1$ subset $n=114$, $+8.2$ pp (14/4/96; CI $[2.3,14.4]$);
collapsed test-only Conf. $=0$ subset $n=13$, $+90.7$ pp (13/0/0; CI
$[88.8,93.3]$; paired sign delta $1.0$).
Decisive (non-tie) tasks: $14/18$ wins ($77.8\%$; Wilson $[54.8,91.0]\%$).
Partial band $0<$Conf$<1$ ($n=101$): $-2.5$ pp — do not force SIFR.
The collapsed subset is the mechanism explanation, not an external-effect
headline.

**B6 prevention:** formal-only ⇒ equals B2/A2 when Screen is off.
HardSynthetic slice of `prevention_full_v1`: B2/A2/M (and B6 by design) at
PDR $100\%$ / FAR $0\%$ ($n=720$). Industrial B6 rows absent from
`prevention_full_v1` (disclose n/a). See `tables/e2_decomp_availability.tex`.

**Screen-hit industrial vignettes (`e2_screen_hit_vignettes.py`):**
32 mutants with B2 accept and M reject; all industrial; Conf.=1 under B2/A2/M
in every case (DRO 15, MBO 15, WRO 2). Table `e2_screen_vignette.tex`.

**Industrial FAR bootstrap (`e2_pdr_far_bootstrap.json`):**
industrial $n{=}132$, $\Delta$FAR M−B2 ${-}24.2$ pp, CI $[-31.8,\,-17.4]$ pp
(excludes 0). Pooled $\Delta$FAR CI also excludes 0 but is not the release claim.
on 120 clean reference implementations, any advisory pattern match occurs on
120/120, but high-or-critical rejection is 0/120 and critical rejection is
0/120. Cite as clean-reference reject rate, not as proof of complete screen
precision.

**E2 decomposition (`prevention_full_v1` slice analysis; table
`tables/e2_decomp_availability.tex`):**
- Pooled impl-screening $n{=}852$: B2=A2 PDR/FAR 91.2/8.8; M 95.0/5.0
  ($\Delta_{\mathrm{screen}}{=}{-}3.8$\,pp FAR).
- HardSynthetic slice $n{=}720$: B2=A2=M all PDR 100\% / FAR 0\% (no screen
  headroom).
- Industrial slice $n{=}132$: B2=A2 PDR/FAR 43.2/56.8; M 67.4/32.6
  ($\Delta_{\mathrm{screen}}{=}{-}24.2$\,pp FAR; 32 B2-accept/M-reject cases,
  all industrial).
- B6/M_lite: no rows in `prevention_full_v1`. Because both are formal-only /
  no-Screen modes (like A2), expected prevention equals B2/A2; do not invent
  B6 FAR. BENCH-120 Conf. artifacts remain B6 81.1\% / M_lite 79.0\%.
- Offline HardSynthetic-180 regenerates the hard IDs but does not restore the
  missing 33 industrial task definitions; cite archived `prevention_full_v1`
  for prevention claims.

**Quick primary numbers (fixed oracle):** E1 B1 84.2% / B2 98.3% / M 100.0%; E10 B1 81% / B2 99% / M 100%; E12 B1 88.6% / B2 100% / M 99.7% (B2 first every seed).  
**Real-priority micro (`run_real_priority_micro_v1`, n=30):** B1 **95.6%** / B2 **100%** / M_eq **100%** (0/0/30). Includes firewall/role/tax/billing adaptations + industrial/GitHub/HKCA09. Supports C4 + external validity. See `benchmarks/REAL_PRIORITY_MICRO_README.md`.

**SMT scalability (`artifacts/smt_scalability_v1`):** LIA mean witness ~29–31 ms from `[-5,20]` through `[-1000,1000]`; Real `[-100,100]` ~19 ms. No latency cliff on this fragment; hybrid fuzzing fallback discussed in ch08.

**GitHub live harvest (`run_github_harvest_v2`, n=48; v1 frozen in Phase 0):** B1 **83.7%** / B2 **92.0%** / M_eq **92.0%** (equal K=3, ecnu-plus; M_eq vs B2 0/0/48; Accept B1 72.9% / B2=M_eq 81.2%). Public `.asfl` FSF auto-extract. Phase-1 targeted expansion did **not** grow validated $n$ past 48. Supports C4; Accept≠mean-Conf.

**E6 external hard-seed protocol v2 (`artifacts/run_ext_hardseed_e6_v2/`):**
pre-registered filter keeps pairs with test-only Conf. $<1$.
Primary family `wrong_relop`: $n{=}79$, $\Delta{+}20.6$ pp, W/L/T 22/1/56,
CI $[12.7,28.6]$ (excludes 0); decisive 22/23.
Pooled headroom across seed families: $n{=}186$, $\Delta{+}18.3$ pp,
CI $[13.2,23.8]$.
New slices: GitHub harvest wrong_relop gemini $n{=}3$ (CI includes 0; rare
injectable relops); HKCA09 wrong_relop gemini v2 headroom $n{=}17$,
$\Delta{+}18.8$ pp, CI $[3.9,37.5]$ (excludes 0).
Script: `paper/hsp-agile/scripts/run_ext_hardseed_protocol.py`.
Cite as external transfer under headroom, not a replacement for BENCH-120 E6.
(v1 snapshot frozen above in Phase 0: wrong_relop $n{=}76$, ${+}20.7$.)

**External prevention / Screen (`artifacts/run_prevention_external_v1/`,
`--impl-screening-only` on reference mutants):**
GitHub harvest: Screen-hits **94**; FAR B2/A2 60.4% → M **11.5%**.
HKCA09: Screen-hits 2; FAR 50.0% → 48.6% (near-null).
Published-industrial: Screen-hits 0; FAR 50% all modes (saturation boundary).
Industrial-132 remains primary Screen evidence; GitHub is reproducible extension.
Tables: `e2_ext_screen.tex`, `e2_screen_vignette_external.tex`.

**HKCA09 SOFL→FSF (`run_hkca09_b1b2m_v1`, n=35):** B1 **74.3%** / B2 **100%** / M_eq 100% (0/0/35). Overlap-rich reconstructions from public maintainability-experiment SOFL modules. Supports C4 (B1 headroom; B2 enough). RealSpec total **203** (`github_sofl=35`).

**HKCA09 hard-seed C2 (`run_hkca09_hard_seed_e6_v1`):** one-shot E6 on real/headroom saturates (all variants Conf=1). Freeze seed → T=0 repair: **wrong_relop** semantic_ir 82.0% vs test_only 69.3% (**+12.7 pp**; W/L/T 9/5/12; CI includes 0). invert_order mixed. Prefer filtered gemini v2 headroom row above for CI-excludes-0 external transfer. See `HKCA09_FSF_EXPANSION.md`.

**Published-industrial desensitized pilot (`run_desens_real_sofl_v1`, n=28):** B1/B2/M_eq all **100.0%** Conf./Strict (equal K=3, ecnu-plus; paired M_eq vs B2 0/0/28). Supports C4 default B2. Corpus: `benchmarks/published_industrial_pilot.json`. Vendor `.asfl` import: `vendor/README.md` / `artifacts/VENDOR_INTAKE_CHECKLIST.md` (NDA pending; interim = published reconstruction). Provenance: `benchmarks/DESENSITIZED_REAL_SOFL_PILOT.md`.

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

### E6 (
un_feedback_v2)

| Variant | Mean Conf. |
|---------|------------|
| A test_only | 79.1% |
| B test_expected | 78.9% |
| C semantic_ir | 86.9% |

C-A = **+7.7 pp** (primary typed-IR / single-factor C2 claim). Source: eedback_variant_summary.csv.

**Paired stats** (e6_paired_summary.json; scripts/e6_paired_analysis.py):

| Contrast | W/L/T | Delta (pp) | 95% CI (pp) | Wilcoxon p |
|----------|-------|------------|-------------|------------|
| C-A | 14/4/102 | +7.7 | [2.3, 13.6] | 0.018 |
| C-B | 14/4/102 | +8.0 | [2.2, 14.0] | 0.027 |

Both CIs exclude 0. Paper table: 	ables/e6_paired_stats.tex.

### E14 (
un_e14_sweep_v1) --- uniqueness scope, not primary C2

| Variant | Mean strict Conf. |
|---------|-------------------|
| test_only | 73.8% |
| test_expected | 74.4% |
| semantic_ir | 75.1% |
| execution_trace_matched | **85.4%** |

Paired mean Conf. (e14_paired_summary): semantic_ir vs execution_trace_matched **5 / 19 / 96** (W/L/T, -10.3 pp); vs test_only 18 / 16 / 86 (+1.3 pp). Script: paper/hsp-agile/scripts/e14_paired_analysis.py. Details: P1_CAUSAL_NOTES.md.

### Hard combo-seed support (pooled n40 + extra40 → n=80)

Primary supporting run: `run_ir_combo_seed_gemini_n40_v1` + `run_ir_combo_seed_gemini_extra40_v1`
(model gemini-2.5-flash; freeze injected buggy code → one T=0 repair).

**Pooled** (n=240 task × seed cells), FULL=semantic_ir:

| Contrast | Delta (pp) | W/L/T | 95% CI (pp) | Excl. 0 |
|----------|------------|-------|-------------|---------|
| vs test_only | **+26.5** | 78/27/135 | [21.0, 32.2] | **Yes** |
| vs test_expected | **+26.7** | 79/18/143 | [21.0, 32.3] | **Yes** |
| vs ir_no_expected | +5.0 | 29/17/74 | [-3.3, 13.6] | No (n40 field slice) |

Per-seed FULL vs test_only also CI-excl-0 (+23.4 / +26.7 / +29.2 pp).
Archive n40-only slice: +33.2 / +32.6 pp (Table `gemini_combo_n40.tex`).
Cite pooled n80 as supporting C2 under harder bugs; not uniqueness vs every structured ablation.
Table: `tables/gemini_combo_n80.tex`. JSON: `data/processed/gemini_combo_n80_summary.json`.
gpt-4o-mini / deepseek combo saturate (~100%) — do not cite as weak-model evidence.

### E2 (prevention_full_v1, impl-screening n=852)

| Mode | PDR | FAR |
|------|-----|-----|
| B2 | 91.2% | 8.8% |
| M | 95.0% | 5.0% |

Abstract cites M PDR 95.0% / FAR 5.0% vs B2. Source: prevention_summary.json -> y_eval_type.*.impl_screening.

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
