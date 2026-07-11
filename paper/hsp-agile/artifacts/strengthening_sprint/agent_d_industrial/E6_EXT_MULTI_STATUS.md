# Exp-External E6-Ext / E6-Multi Status

Generated from existing local artifacts on 2026-07-11. No paper plan file was edited.

## Evidence Table

| Evidence slice | Run / artifact | n | Key numbers | Status | Paper use |
|---|---|---:|---|---|---|
| BENCH-120 feedback isolation anchor | `run_feedback_v2`; `data/processed/e6_paired_summary.json` | 120 paired tasks | `semantic_ir` 86.9% vs `test_only` 79.1%; delta +7.7 pp; W/L/T 14/4/102; 95% CI [2.3, 13.6]; Wilcoxon p=0.018 | Significant support | Lead C2 mechanism result, not external evidence. |
| E6-Multi hard combo seeds | `run_ir_combo_seed_gemini_n40_v1` + `run_ir_combo_seed_gemini_extra40_v1`; `data/processed/gemini_combo_n80_summary.json` | 80 tasks x 3 seeds = 240 paired cells | FULL=`semantic_ir` vs `test_only`: +26.5 pp, W/L/T 78/27/135, 95% CI [21.0, 32.2]. FULL vs `test_expected`: +26.7 pp, W/L/T 79/18/143, 95% CI [21.0, 32.3]. FULL vs `ir_no_expected`: +5.0 pp, 95% CI [-3.3, 13.6]. | Significant support vs unstructured/expected-string feedback; saturation/null vs one structured ablation | Supporting C2 under harder injected bugs and weaker model. Do not claim uniqueness over every structured field ablation. |
| Real/headroom one-shot E6 | `run_real_e6_headroom_v1`; `REAL_E6_HEADROOM_PAIRED.json` | 57 paired tasks | All variants 100.0% Conf/Strict; `semantic_ir` vs `test_only` delta +0.0 pp; W/L/T 0/0/57; CI [0.0, 0.0] | Saturated | External C4/headroom diagnostic only. Not evidence against C2 because there is no repair headroom. |
| RealSpec B1-fail feedback slice | `run_realspec_e6_b1fail_v1`; `realspec_e6_b1fail_summary.json` | 30 tasks | `test_only`=`test_expected`=`semantic_ir`=100.0%; note says saturated under `ecnu-plus` | Saturated | Same interpretation as Real/headroom: useful as a saturation warning, not a null C2 claim. |
| HKCA09 SOFL->FSF ranking | `run_hkca09_b1b2m_v1`; `realspec_b1b2m_summary.json` | 35 tasks x 3 modes | B1 74.3%; B2 100.0%; `M_eq` 100.0% | B2/M saturation with B1 headroom | Supports external validity of B2/M pipeline on public SOFL reconstructions; not typed-IR feedback evidence. |
| HKCA09 hard-seed feedback | `run_hkca09_hard_seed_e6_v1` + `v2`; `HKCA09_HARD_SEED_PAIRED.json` | 26-30 paired tasks per seed family | `wrong_relop`: +12.7 pp, W/L/T 9/5/12, CI [-3.5, 29.6]. `invert_order`: -2.3 pp, CI [-5.4, 0.6]. `swap_bodies`: -0.8 pp, CI [-4.6, 3.1]. `combo_invert_relop`: -21.5 pp, CI [-35.3, -9.1]. `drop_first_guard`: -25.7 pp, CI [-37.3, -14.6]. | Mixed; only wrong_relop is positive and it is not significant; two families significantly favor `test_only` | Cite only as scoped external stress evidence. It does not replace BENCH-120 E6 and should not be summarized as uniformly positive. |
| GitHub live harvest ranking | `run_github_harvest_v1`; `GITHUB_HARVEST_EVAL_SUMMARY.json` | 48 tasks x 3 modes | B1 85.8%; B2 89.9%; `M_eq` 89.9%; `M_eq` vs B2 W/L/T 1/1/46 | Tie / near-saturation | Supports C4 external validity and default B2; not C2 typed-IR feedback evidence. |
| Published-industrial desensitized pilot | `run_desens_real_sofl_v1`; `DESENS_REAL_SOFL_PILOT_SUMMARY.json` | 28 tasks x 3 modes | B1=B2=`M_eq`=100.0% Conf/Strict; `M_eq` vs B2 W/L/T 0/0/28 | Saturated | External corpus coverage only. Do not use for M-over-B2 or C2 effect claims. |
| Legacy external summary | `data/processed/e11_external_summary.csv` | 22 tasks x 3 modes | B1/B2 success 63.6%, strict 89.8%; M success 59.1%, strict 81.9% | Historical / incompatible endpoint | Keep out of current E6-Ext unless the protocol is reconciled with current fixed-oracle/confidence reporting. |

## Bottom Line

E6-Multi can be supported from existing artifacts: the pooled Gemini combo-seed run shows a large, CI-excluding advantage for `semantic_ir` over `test_only` and `test_expected` across 240 paired cells. The same artifact also shows a non-significant result against `ir_no_expected`, so the safe claim is support against unstructured and expected-string feedback under hard injected bugs, not uniqueness over every structured IR field.

E6-Ext is not uniformly positive. RealSpec/headroom, RealSpec B1-fail, GitHub, HKCA09 ranking, and desensitized industrial corpora mostly saturate or tie under the current model/protocol. HKCA09 hard-seed stress is mixed: `wrong_relop` is directionally positive but underpowered, while two seed families significantly favor `test_only`. Use these as external validity and boundary-condition evidence, not as a replacement for the BENCH-120 E6 mechanism result.

## Blockers / No-API Decision

- No live model API jobs were launched in this pass; the requested evidence could be regenerated from completed local artifacts.
- Fresh E6-Ext API runs would require new protocol choices because the current external corpora mostly saturate under `ecnu-plus`.
- New GitHub harvest expansion is blocked on the handoff/auth path in `GITHUB_AUTH_HANDOFF.md` and would change corpus provenance.
- A stronger external C2 claim likely needs pre-registered hard external seeds with enough repair headroom, plus model selection that avoids 100% ceiling effects.
