# Phase 3 — PC Review Response (Target: Weak Accept / ~55%)

**Input:** Subagent PC review (Borderline 38%, 2026-07-10)  
**Goal:** Raise acceptance probability by aligning evidence order with claims

## P0 (implemented this sprint)

| ID | Action | Status |
|----|--------|--------|
| P0-1 | Demote E1 90.4% headline; lead with E6 + deployment table | In progress |
| P0-2 | Conference Results order: E6→E3/E10→E2→deploy→E12→E1 footnote | In progress |
| P0-3 | Fix E3 tier numbers (was inconsistent with `complexity_by_mode.csv`) | In progress |
| P0-4 | Narrow E6/C2: gain vs test-only, not vs trace-matched | In progress |
| P0-5 | B6 table sourced from same 120-task corpus; no cross-run mixing in prose | In progress |

## P1 (implemented / running)

| ID | Action | Status |
|----|--------|--------|
| P1-1 | `M_lite` mode (B6 witnesses + Semantic IR, no pattern guard) + `run_m_lite_v1` | Running |
| P1-2 | Related-work repair-loop comparison table (B2/B3–B5/B6/M/M_lite) | In progress |
| P1-3 | E16 documented as `ecnu-max` pilot (29 tasks) | Done |

## Iteration loop

1. Implement P0/P1 → `refresh_paper_assets.py`
2. Subagent review (strict CCF-B)
3. Address blocking issues → repeat until Borderline ≥ Weak Accept
