# HSP-Agile / SgDP — 10-Page Conference Submission Outline

**Source document:** 108-page report (`paper/hsp-agile/`, chapters ch01–ch09 + `front/abstract.tex`)  
**Target length:** ~10 pages (IEEE/ACM two-column, including references)  
**Scope:** Condensed *submission plan* — not a page-compressed version of the report.

---

## 1. Target Venue Recommendation

### Primary: **ICSME 2027** (IEEE International Conference on Software Maintenance and Evolution)

| Criterion | Fit |
|-----------|-----|
| **Topic alignment** | LLM-assisted synthesis, specification conformance, repair loops, empirical SE evaluation — core ICSME themes (evolution, quality, automated repair). |
| **Contribution type** | Framework + tool instantiation + 120-task benchmark + ablation study matches ICSME’s empirical/tool-track expectations. |
| **Audience** | Practitioners and researchers in spec-driven agile workflows (Agile-SOFL lineage) and LLM code generation. |
| **Artifact policy** | ICSME encourages/rewards reproducibility packages; the report already ships tasks, logs, and scripts (`run_hard_full_parallel_v1`). |

**Rationale:** The paper’s centre of gravity is *software maintenance quality* — preventing specification-conformance defects before merge — not pure formal verification. ICSME reviewers expect mechanism + measurement; the three-insight structure (C1–C3) maps cleanly to a 10-page empirical paper.

### Backup: **SANER 2027** (IEEE International Conference on Software Analysis, Evolution and Revalidation)

| Criterion | Fit |
|-----------|-----|
| **Analysis angle** | SMT witnesses, pattern guard, mutation-based PDR/FAR — analysis-driven defect prevention. |
| **Repair narrative** | CEGIS-style counterexample-guided repair with typed Semantic Feedback IR fits SANER’s analysis/repair focus. |
| **Risk** | Slightly narrower readership for SOFL/Agile-SOFL; mitigate with `classify_signal` running example and HumanEval/MBPP transfer rows (E8c). |

**Why not QRS / ICFEM as primary:** QRS is broader quality/reliability (viable third choice); ICFEM favours deductive proofs and rich logics — this work explicitly positions *below* full verification (bounded witnesses, not theorem proving).

---

## 2. Page Budget Table

Assumes IEEE two-column, 10 pt, ~0.5 page for abstract (often excluded from limit but budgeted here for planning).

| Section | Est. pages | Notes |
|---------|------------|-------|
| **Abstract** | 0.25 | ≤250 words; standalone |
| **1. Introduction** | 1.00 | Problem, `classify_signal`, acceptance eq., contributions |
| **2. Background & Related Work** | 0.75 | SOFL/FSF first-match + 1 comparison table; no survey depth |
| **3. Approach** | 2.25 | Merge formal essentials + SgDP loop + worked trace |
| **4. Experimental Setup** | 1.00 | Benchmark, modes, metrics, threats preview |
| **5. Results** | 2.50 | Mechanism-first: E3/E6 → E1 → E2 → E5/E8 |
| **6. Discussion & Threats** | 0.75 | Paradox, failure taxonomy, generalisation limits |
| **7. Conclusion** | 0.25 | Three insights + one limitation sentence |
| **References** | 0.75 | ~35–45 citations (trim from report bib) |
| **Total** | **~9.50** | Headroom for one extra figure or table |

*Optional squeeze:* Background 0.5 + Approach 2.0 → free 0.5 for a second results figure.

---

## 3. What to KEEP (Core Claims, Figures, Tables)

### Tier-1 claims (must survive condensation)

| ID | Claim (report wording) | Primary evidence |
|----|------------------------|------------------|
| **C1** | Prevention depends on **semantic regions** (first-match partitions), not surface syntax; **SpecIR** is the hinge. | E3 overlap scaling; E8 adapter transfer |
| **C2** | Repair needs a **typed scenario failure** (Semantic Feedback IR), not raw pass/fail. | E6 (+7.7 pp A→C); E5 convergence; A3 ablation (−6.3 pp) |
| **C3** | Release is **conjunctive**: full witness conformance **and** clear high-severity pattern screen. | E1 strict paradox; E2 PDR/FAR; `Accept` decision tree |

### Headline numbers (repeat in abstract, intro, conclusion)

- **90.4%** mean strict formal conformance (M) on 120-task hard benchmark  
- **+6.2 pp** vs one-shot B1; **+2.4 pp** vs test-feedback B2  
- **+7.7 pp** full Semantic Feedback IR vs test-only (E6)  
- **25.0%** strict success under conjunctive gate (vs 26.7% B1/B2) — frame as *selectivity*, not weakness  
- **4.6×** latency vs B2; **A2** as near-Pareto alternative (90.9% Conf., 12.1 s)

### Figures to KEEP (with file paths)

| Fig | Path | Role |
|-----|------|------|
| Motivation: tests vs SMT witness | `diagrams/tikz/defect_vs_test.tex` → render for submission | Why unit tests miss ordering defects |
| SgDP overview | `diagrams/tikz/sgdp_framework_overview.tex` | Single architecture figure |
| Worked example trace | `diagrams/tikz/worked_example_trace.tex` | End-to-end `classify_signal` (C1–C3 in one panel) |
| Acceptance decision tree | `diagrams/tikz/accept_decision_tree.tex` | C3 conjunctive gate |
| Complexity / overlap (E3) | `figures/complexity_heatmap.pdf` | C1 scaling claim |
| Feedback variants (E6) | `figures/feedback_variant_bar.pdf` | C2 isolation (+7.7 pp) |
| Main conformance distribution | `figures/formal_conformance_cdf.pdf` *or* `figures/mode_distribution_strict_conformance.pdf` | Pick **one** — CDF preferred for space |
| Ablation | `figures/ablation_contribution_ci.pdf` | Component attribution |
| Repair convergence (E5) | `figures/repair_convergence.pdf` | Justifies K=3 |
| Prevention heatmap (E2) | `figures/prevention_heatmap_by_mode_eval.pdf` | Complementarity M vs B2 |
| Pareto quality–latency | `figures/pareto_quality_vs_latency.pdf` | RQ5 trade-off |
| Generalisation (E8) | `figures/generalisation_bar.pdf` | SpecIR transfer |
| Failure taxonomy (E9) | `figures/failure_taxonomy_pie.pdf` | Residual failure honesty |

### Tables to KEEP

| Table | Source | Role |
|-------|--------|------|
| Main results (7 modes) | `ch07_results.tex` → `tab:main-results`; data: `data/processed/summary_by_mode.csv` | E1 headline |
| Compared modes | `ch06_experimental_setup.tex` → `tab:modes` | Compact mode legend |
| E6 feedback variants | `ch07_results.tex` → `tab:feedback-e6` | C2 numbers |
| Prevention PDR/FAR | `ch07_results.tex` → `tab:prevention` | C3 mutant screening |
| Generalisation summary | `ch07_results.tex` → `tab:generalisation`; data: `data/processed/generalisation_summary.csv` | E8 one glance |
| Claim–experiment map | `ch06_experimental_setup.tex` → `tab:claim-map` | Optional inline box in Setup |

### Running example & listings (inline, not appendix)

- `listings/classify_signal.fsf` — FSF spec  
- `listings/classify_signal_bug.py` — buggy LLM candidate  
- Abbreviated Semantic Feedback IR JSON (from `ch08_discussion.tex`, `lst:classify-signal-ir`)

---

## 4. What to CUT or Move to Appendix / Supplementary

### Chapters → disposition

| Report chapter | Conference disposition |
|----------------|------------------------|
| ch02 Background | **Cut to 0.75 pp** — SOFL/FSF semantics + one related-work table; drop extended surveys (DafnyBench, Reflexion, etc.) to citations only |
| ch03 Formalization | **Merge into §3** — keep Def. task, SpecIR, conformance, Accept, Φᵢ formulas; drop theorems (FAR bound), full proof sketches |
| ch04 Method | **Core of §3** — walkthrough + 4 SgDP components; drop prompt-design cards, extended pattern catalogue |
| ch05 Implementation | **Cut** — 2–3 sentences + optional 1-line architecture; move `diagrams/puml/rendered/component_arch.pdf` to supplementary |
| ch06 Experiments | **Condense to §4** — drop mutant operator encyclopedia, statistical protocol details |
| ch07 Results | **§5 subset** — see experiment table below |
| ch08 Discussion | **§6 subset** — paradox + E9 + 1-page threats; cut sprint CI/CD essay, failure trace listings |
| ch09 Conclusion | **§7** — 3 bullets + future work one sentence |
| Appendices A–C | **Supplementary / artifact** — reproducibility, benchmark construction, RF01–RF14 catalogue |

### Experiments to CUT or supplementary

| Exp | Disposition |
|-----|-------------|
| **E4** Boundary density | **Supplementary** (`figures/boundary_coverage_by_density.pdf`) — cite one sentence in E3 discussion |
| **E7** Pattern guard P/R/F1 | **Supplementary** (`figures/pattern_guard_f1_bar.pdf`) — one sentence: “F1 > 0.6 on Ordering/GuardInversion” |
| **Sensitivity** | **Cut** (`figures/sensitivity_heatmap.pdf`) — footnote K=2 extrapolation |
| **E8c** real-derived detail | **Keep one row each** in generalisation table; full `tab:benchmark-by-source` → supplementary |
| **B3–B5** baselines | **Keep compact row** in main table (E1-ext); cite M > B3/B5 on Conf |
| **Significance appendix** | **Cut** — report Holm p and Cliff’s δ inline for M vs B1 only |

### Figures to CUT (redundant with main table)

- `figures/summary_metrics_by_mode.pdf`
- `figures/llm_calls_distribution.pdf`
- `figures/radar_metrics.pdf`
- `figures/mode_distribution_latency.pdf` (Pareto subsumes)
- `figures/prevention_bar.pdf` (if heatmap kept)
- `figures/residual_error_distribution.pdf`
- `diagrams/tikz/contribution_map.tex` (replace with contribution bullet list)
- `diagrams/tikz/benchmark_pipeline.tex` → one sentence in setup
- All PlantUML class/sequence diagrams (`diagrams/puml/rendered/*.pdf`)

---

## 5. Restructured Section Headings (Conference Format)

```
Title: Specification-Guided Defect Prevention for LLM Synthesis
       over Ordered Guard Specifications

Authors, affiliations

Abstract

1  Introduction
   1.1  Motivation: specification-conformance defects and the test-sampling gap
   1.2  Running example: classify_signal
   1.3  Research questions and contributions

2  Background and Related Work
   2.1  Ordered FSF / first-match semantics
   2.2  LLM synthesis and test-feedback repair
   2.3  Positioning: SgDP vs verification and vs test-only loops

3  The SgDP Framework and HSP-Agile
   3.1  Formal model (task, SpecIR, conformance, Accept)
   3.2  Four components: oracle, witnesses, Semantic Feedback IR, conjunctive gate
   3.3  Worked example trace (classify_signal end-to-end)
   3.4  Instantiation interface (SOFL/FSF; adapters sketched)

4  Experimental Setup
   4.1  Hard benchmark (120 tasks, overlap filter)
   4.2  Compared modes and ablations
   4.3  Metrics: Conf, Strict, PDR/FAR, latency
   4.4  Implementation notes and reproducibility (brief)

5  Results
   5.1  RQ4/C1: advantage grows with guard overlap (E3)
   5.2  RQ3/C2: typed feedback and repair dynamics (E6, E5, ablation)
   5.3  RQ1: overall effectiveness (E1)
   5.4  RQ2/C3: prevention and mutant screening (E2)
   5.5  RQ5: quality–overhead trade-off (E1 Pareto)
   5.6  External validity: adapter transfer (E8)

6  Discussion
   6.1  The strict-success paradox (conjunctive selectivity)
   6.2  Residual failures (E9 taxonomy)
   6.3  Threats to validity (construct, internal, external, conclusion)
   6.4  Practical deployment sketch (3–4 sentences)

7  Conclusion

References

--- Supplementary / Artifact (not in page count) ---
  S1  Benchmark construction protocol
  S2  E4 boundary-coverage curves
  S3  E7 pattern-guard F1 by category
  S4  Full statistical tables (significance_tests.json)
  S5  RF01–RF14 pattern catalogue
  S6  Reproduction commands (from appendices/app_a_reproducibility.tex)
```

---

## 6. Abstract Rewrite Bullets (≤250 words structure)

Use this skeleton; target **200–230 words**.

1. **Hook (2 sentences):** Ordered guard specifications (e.g., SOFL/FSF) require first-match precedence; LLMs synthesise plausible code that fails on thin guard-overlap regions unit tests rarely sample.

2. **Gap (1 sentence):** Test-feedback repair lacks specification-level structure—it cannot name which scenario was violated or force witnesses into precedence partitions.

3. **Approach (3 sentences — one per insight):**
   - **C1:** Introduce SgDP with SpecIR so prevention depends on semantic regions, not surface syntax.
   - **C2:** Counterexample-guided repair via Semantic Feedback IR—a typed record naming violated scenario, witness, and expected output before prompt rendering.
   - **C3:** Conjunctive acceptance: every specification-derived witness must match and no high-severity structural pattern may remain.

4. **Instantiation (1 sentence):** HSP-Agile realises SgDP for SOFL/FSF with Z3 witnesses and a pattern screen.

5. **Evaluation setup (1 sentence):** 120-task precedence-sensitive benchmark, seven modes (one-shot, test-feedback, full pipeline, ablations), Qwen-27B, budget K=3.

6. **Headline results (2–3 sentences):** E6 +7.7\,pp typed feedback (lead); overlap-scoped E3/E10; E1 stress-test 90.4\% (+6.2\,pp vs B1); M--B2 aggregate **not** Holm-significant ($p{=}0.811$); PDR 95.0\% / FAR 5.0\%.

7. **Transfer & artifact (1 sentence):** Adapter-level transfer to Mini-StateMachine and real-derived HumanEval/MBPP subsets; tasks, logs, and scripts released.

8. **Limitation (1 sentence):** Conjunctive gate yields 25% strict acceptance; residual failures are ordering/boundary/arithmetic; latency ≈4.6× test-feedback.

9. **Keywords:** specification-guided defect prevention; LLM code synthesis; SOFL/FSF; counterexample-guided repair; SMT witnesses.

---

## 7. Contribution Bullets (Conference Style, 3–4 Items)

- **SgDP framework** — A notation-agnostic prevention loop combining SpecIR semantic regions, SMT-guided witnesses, Semantic Feedback IR, and a conjunctive acceptance gate for ordered guard specifications.

- **Semantic Feedback IR** — A typed failure record that names the violated scenario and witness before natural-language repair rendering; empirically +7.7 pp over test-only feedback under identical repair budget.

- **Precedence-sensitive benchmark and evaluation** — A 120-task hard corpus with overlap filter and mutation-based PDR/FAR protocol showing 90.4% mean conformance (+6.2 pp over one-shot LLM) and growing advantage under dense guard overlap.

- **HSP-Agile instantiation and transfer** — Open-source SOFL/FSF pipeline with adapter-level generalisation to Mini-StateMachine and real-derived specs without redesigning the core loop.

*(If venue limits to 3 contributions, merge bullets 3–4: “benchmark + HSP-Agile artifact with adapter transfer.”)*

---

## 8. Experiment Table — Minimum Viable Set

### Modes (7 primary → **5 in paper**, 2 ablations)

| Mode | In 10-page paper? | Rationale |
|------|-------------------|-----------|
| **B1** One-shot LLM | **Yes** | Primary baseline |
| **B2** Test-feedback | **Yes** | Strongest practical baseline |
| **M** Full SgDP/HSP-Agile | **Yes** | Proposed method |
| **A1** No formal checker | **Yes** | Isolates Z3 witnesses (−3.9 pp) |
| **A3** No repair | **Yes** | Isolates CEGIS loop (−6.3 pp) |
| **A2** No pattern guard | **Mention** | Near-Pareto (90.9%, 12 s); C3 gate not Conf booster |
| **B0** Template reference | **Footnote** | Difficulty calibration (27.5%) only |
| B3–B5 | **Supplementary** | Evaluated; 5\% Strict without formal witnesses; B4≈B2 |

### Experiments E1–E9

| Exp | In paper? | Footprint | Supports |
|-----|-----------|-----------|----------|
| **E1** Overall effectiveness | **Yes** | Main table + 1 distribution figure + Pareto | RQ1, RQ5, C1–C3 |
| **E2** Prevention PDR/FAR | **Yes (partial)** | Heatmap *or* aggregate table; skip per-operator prose | RQ2, C3 |
| **E3** Complexity / overlap | **Yes** | `complexity_heatmap.pdf` | RQ4, **C1** |
| **E4** Boundary density | **Supplementary** | 1 cross-reference sentence | C1 supporting |
| **E5** Repair dynamics | **Yes** | `repair_convergence.pdf` | RQ3, K=3 |
| **E6** Feedback variants | **Yes** | Bar + small table | RQ3, **C2** |
| **E7** Pattern guard F1 | **Supplementary** | One aggregated sentence | C3 |
| **E8** Generalisation | **Yes (compact)** | Table + bar; n=30 adapter notations (E8b) | C1 transfer (partial on adapters) |
| **E9** Failure taxonomy | **Yes** | Pie chart + 3-sentence interpretation | Honesty / limits |

**Minimum experiment core if space-critical:** E1 + E3 + E6 + E2 (table only) + E8 (table only) = five result subsubsections.

---

## 9. Risks for Reviewers and Mitigation (Condensed Version)

| Risk | Reviewer concern | Mitigation in 10-page version |
|------|------------------|-------------------------------|
| **Synthetic benchmark** | 120 hard synthetic tasks ≠ real SOFL repos | Lead with `classify_signal`; report E8c HumanEval/MBPP M-only rows (93.8%/95.0%); release construction scripts; acknowledge Z3 overlap filter favours SMT |
| **Single LLM, single run** | Qwen-27B, no multi-seed repeats | State T_repair=0.0, bootstrap CIs over tasks; ablations isolate components; footnote B3–B5 planned; sensitivity to model discussed in threats |
| **Strict success paradox** | M has *lower* strict rate (25% vs 26.7%) | Dedicated §6.1: conjunctive gate ≠ weaker code; FAR 5.0% vs 8.8%; conformance is primary metric; cite Wilcoxon non-sig |
| **Small effect vs B2** | +2.4 pp conformance may seem modest | Pair with E3 (+8 pp in dense tier) and E6 (+7.7 pp); emphasise *mechanism* and fault-class complementarity (heatmap), not aggregate pp alone |
| **Latency cost** | 4.6× B2, ~44 s/task | Pareto figure; position as CI pre-merge gate; offer **A2** operating point (90.9%, 12 s) when pattern screen optional |
| **SOFL niche** | FSF unfamiliar to general SE audience | Frame as **ordered guard specs** (general); SpecIR as notation-agnostic; Mini-StateMachine transfer |
| **Not full verification** | Finite witnesses, no proof | Up-front positioning: bounded prevention between tests and Dafny; FAR bound theorem → supplementary |
| **Pattern guard ad hoc** | 14 RF rules | Report E7 F1 in supp; A2 ablation shows +0.5 pp Conf — guard is diagnostic/prevention gate, not accuracy driver |
| **E8c incomplete baselines** | No B1/B2 on HumanEval/MBPP | Label clearly; do not over-claim; use as external sanity check for M only |
| **Author-constructed benchmark** | Tuning bias | Ablation + independent E8 subsets; release 180→120 filter protocol in artifact |

---

## Appendix: Key Data File Index (for figure regeneration)

| Artifact | Path |
|----------|------|
| Raw runs | `data/raw/results_raw.csv` |
| Summary by mode | `data/processed/summary_by_mode.csv` |
| Ablation | `data/processed/ablation_contribution.csv` |
| Generalisation | `data/processed/generalisation_summary.csv` |
| Prevention | `data/processed/prevention_summary.json`, `prevention_heatmap.csv` |
| Failure taxonomy | `data/processed/failure_taxonomy.json` |
| Significance | `data/processed/significance_tests.json` |
| Plot script | `figures/scripts/plot_mpl_figures.py` |
| Stats table | `tables/stats_summary.tex` |

---

*Generated from report canonical sources: `front/abstract.tex`, `chapters/ch01_introduction.tex`–`ch09_conclusion.tex`.*
