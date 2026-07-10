# M-Win Campaign Status (2026-07-10)

## Root cause fixed
`src/formal/fsf_eval.py`: others witnesses were `BoolVal(True)` without
`¬(g1∨…∨g_{n-1})`, creating false failures (~5% Strict). Fixed +
`first_match_oracle` in `checker.py`.

## Pipeline strengthenings
- Best-effort `argmax Conf` over attempts
- Default M: `execution_trace_matched`, advisory pattern gate, K=5, formal_max_cases=32
- Stronger field-diff / others repair hints
- `run_all.py` preserves mode-native K (no longer forces K=3)

## Authoritative results (fixed oracle)

| Exp | Run | B1 | B2 | M | M−B2 |
|-----|-----|----|----|---|------|
| E1 | `run_e1_m_win_v2` | 84.2% | 98.3% | **100.0%** | **+1.7 pp** (2/120 wins) |
| E10 | `run_e10_m_win_v1` | 81.0% | 99.0% | **100.0%** | **+1.0 pp** (1/100 wins) |
| E12 | `run_e12_m_win_v1` | 88.6% | **100.0%** | 99.7% | −0.3 pp (B2 more seed-stable) |

Ablations (`run_e1_m_win_ablation_v1`): B0 100%, A1 81.7%, A2 98.3%, A3 83.3%.

## Paper
Abstract, Ch1/7/8/9, conference stubs, and `AUTHORITATIVE_NUMBERS.md` updated.
E6 +7.7 pp mechanism claim retained; oracle fix disclosed as measurement correction.
