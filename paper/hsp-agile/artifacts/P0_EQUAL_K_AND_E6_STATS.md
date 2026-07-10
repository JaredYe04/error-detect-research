# P0: Equal-K + E6 Stats Status
## E6 paired stats
- Source: `D:\repos\error-detect-research\artifacts\run_feedback_v2\feedback_variants\results.jsonl`
- vs `test_only`: W/L/T=14/4/102, Δ=+7.7 pp, 95% CI [2.256944444444444, 13.645833333333332], wilcoxon_p=0.0182342529296875
- vs `test_expected`: W/L/T=14/4/102, Δ=+8.0 pp, 95% CI [2.1527777777777777, 13.958333333333334], wilcoxon_p=0.02684783935546875

## Equal-K Conf ranking
- Fixed-oracle E1 (`run_e1_m_win_v2`): M K=5 vs B2 K=3 — **bundle**, not equal-K.
- Archive equal-K=3 (`run_hard_full_parallel_v1`): B2 88.0% / M 90.4% (pre-fix / different oracle regime — not primary).
- Proxy truncate: `{"run": "run_e1_m_win_v2", "protocol": "truncate_M_attempt_history_at_K=3 vs final B2", "used_history_rows": 120, "n_paired": 120, "M_mean": 1.0, "B2_mean": 0.9833333333333333, "wins": 2, "losses": 0, "ties": 118, "note": "Proxy equal-K only if attempt_history present; otherwise falls back to final M Conf (NOT equal-K)."}`
- Dedicated equal-K run: `run_e1_equal_k_v1`
- **Primary:** M_eq 100.0% vs B2 97.5% (Δ +2.5 pp; W/L/T 3/0/117)

## Paper policy
1. Lead Conf claim = E6 (+7.7 pp) at K=3 with paired CI.
2. Equal-K Conf ranking = run_e1_equal_k_v1 (B2 vs M_eq).
3. Fixed-oracle E1 M-win (K=5) reported as stress-test bundle only.
4. Deploy claim = C4 (B2 default; M for Accept/FAR≤5%).
