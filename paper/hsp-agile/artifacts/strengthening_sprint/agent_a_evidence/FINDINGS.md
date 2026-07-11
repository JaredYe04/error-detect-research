# FINDINGS — Why does E6 (`semantic_ir`) win?

**Scope:** Existing E6 run only (`run_feedback_v2`, n=120 tasks × 3 variants). No new LLM experiments. Numbers computed by `mine_task_features.py`.

## Headline outcome

Paired C−A (`semantic_ir` − `test_only`): **14 M-wins / 4 A-wins / 102 ties** (ties dominate: 102/120 = 85.0%). The mean Conf. advantage of typed IR is concentrated in a small non-tie slice.

Three-way argmax winner (`E6_winner`) is almost always `tie` (118/120): when C beats A, `test_expected` often matches C, so unique `semantic_ir` argmax is rare (2/120). All primary claims below use the **paired C−A** definition (matches paper W/L/T = 14/4/102).

## Primary regime: rescue from collapsed test-only Conf.

M-win tasks have near-floor **Conf under `test_only`** (mean=0.0446, median=0.0000) versus B2-like (mean=0.8900; Cohen d=-12.858). Under `semantic_ir` they recover to mean Conf=0.9107.

**13/14 of the E6 wins have `conf_test_only == 0`** (suite-wide zero-A tasks: 13/120).
- Rule `conf_test_only==0`: **13/13** M-wins (win_rate=1.000, covers 13/14 = 0.929 of E6 wins, lift=8.571).
- Rule `conf_test_only<0.25`: **13/13** M-wins (win_rate=1.000, covers 0.929 of E6 wins, lift=8.571).

A-wins (n=4) are the mirror image: high `test_only` (mean=0.8958) collapsing under `semantic_ir` (mean=0.1875).

## Static spec features: weak / homogeneous on this suite

The annotated HardSynthetic suite is nearly homogeneous on several axes used in the deployment story: **all 120 tasks** have `n_scenarios=7`, `guard_complexity=Nested`, `n_inputs=5`, `n_outputs=3`. Therefore scenario-count and guard-complexity thresholds cannot separate winners here.

Overlap does **not** favor M-wins on E6: mean overlap_rate M-win=1.196 vs B2-like=1.245 (Cohen d=-0.292). boundary_density similarly flat (M=2.541 vs B2-like=2.547; d=-0.065).

Among the 14 wins, overlap tiers are: high=4, low=7, medium=3; guard complexity: Nested=14.

`overlap_tier==low` has mild positive lift (7/48, covers 7/14 wins, lift=1.250) — opposite of a pure high-overlap necessity claim on this run.
Story-aligned `overlap_tier==high` ∧ `n_scenarios≥7`: 4/38 (covers 4/14 wins, lift=0.902).
Numeric cut `overlap_rate≥1.3` ∧ `n_scenarios≥7`: 4/38 (covers 4/14 wins, lift=0.902).

### Concrete thresholds (data-driven, non-vacuous)

Base M-win rate = 14/120 = 0.117.

- **`conf_test_only==0`**: 13/13 M-wins (win_rate=1.000, covers 13/14 = 0.929 of all E6 wins, lift=8.571).
- **`conf_test_only<0.25`**: 13/13 M-wins (win_rate=1.000, covers 13/14 = 0.929 of all E6 wins, lift=8.571).
- **`conf_test_only<0.5`**: 13/13 M-wins (win_rate=1.000, covers 13/14 = 0.929 of all E6 wins, lift=8.571).

**How many of the 14 E6 wins share the strongest covering regime (`conf_test_only==0`)?** **13 / 14** (92.9%).

## Interpretation (honest)

On E6, typed Semantic Feedback IR is **not universally better**: most tasks are exact C=A ties (102/120). Where it wins, the dominant pattern is **repair rescue**: `test_only` fails almost completely (often Conf=0), while typed IR recovers to high Conf (~0.875–0.958). Static overlap/scenario features are too homogeneous here to support an ex-ante high-overlap deployment rule from E6 alone.

Implication for the sprint story: use E6 to argue **IR irreplaceability on hard repair failures** (field-rich feedback when the baseline loop collapses). Defer **when-to-enable / high-overlap predictor** claims to Agent F using features that actually vary, or to stratified runs with more complexity diversity.

## Caveats

1. **Ties dominate** (102/120). Feature contrasts rest on a small decisive set (14+4=18 non-ties); Cohen d vs B2-like is diluted by 102 ties.
2. **Homogeneous generator:** scenario_count / Nested / I/O arity do not vary — null results on those axes are expected, not evidence against the mechanism elsewhere.
3. **Overlap story not supported by E6 alone:** M-wins are not enriched for high overlap_tier; do not invent a high-overlap necessity claim from this table.
4. **Confounding with difficulty:** zero-A tasks may be harder for reasons correlated with (unmeasured) bug patterns; rescue ≠ proof that overlap causes IR value.
5. **Secondary labels** (E1 M-win, equal-K, E14) are attached in `task_feature_db` for cross-checks but do not redefine the E6 C−A winner used here.
6. **boundary_density** = (# relational ops in non-others guards) / n_scenarios — proxy only.

## Artifacts

- `task_feature_db.csv` / `task_feature_db.json`
- `winner_feature_summary.json`
- `winner_feature_tables.md`
- optional `overlap_vs_delta.png`, `scenario_count_vs_delta.png`

