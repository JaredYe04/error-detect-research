# Wave-1 hard-seed results (experiment only)

**Narrative frozen.** Do not edit Abstract/C2 from these numbers alone.

## Completion

| Run | Tasks | Rows | Status |
|-----|------:|-----:|--------|
| H1 ecnu E6-win14 | 14 | 378 | done |
| H2 gemini E6-win14 | 14 | 378 | done |
| H6 gpt-4o-mini E6-win14 | 14 | 378 | done (**saturated**) |
| H4 ecnu hard_all 0–60 | 60 | 1620 | done |
| H5 RealSpec gemini | 38 | 864 | done |
| H5 RealSpec ecnu | 18 | 378 | done |
| H6 RealSpec gpt-4o-mini | 13 | 270 | done (**saturated**) |

## What worked (CI excludes 0)

| Setting | Contrast | Δ pp | Note |
|---------|----------|-----:|------|
| H1 ecnu | swap_bodies FULL−A | +4.5 | small but clean |
| H1 ecnu | wrong_relop FULL−NO_EXP | +13.1 | field signal |
| H2 gemini | invert_order FULL−A | +31.3 | large; fields saturate with FULL |
| H4 ecnu n=60 | swap_bodies FULL−NO_EXP | +1.5 | diluted vs H1 |
| H5 RealSpec gemini | wrong_relop FULL−A | +16.8 | **best non-synthetic** |

## What failed / under-powered

1. **gpt-4o-mini is not a weak model here** — all variants → Conf 1.0 (synthetic + RealSpec). Need harder seeds or a truly weaker endpoint.
2. **Expanding to hard_all 60 diluted E6-win14 gaps** — many ties; wrong_relop FULL even slightly below A.
3. **RealSpec invert/swap @ gemini** — fully saturated (no separation).
4. **RealSpec @ ecnu** — no CI-excl-0 contrast; wrong_relop FULL < A (−6.9 pp).
5. On RealSpec gemini `wrong_relop`, `test_expected` ≈ FULL (0.46 vs 0.45) — gain over unstructured A is real; **typed uniqueness vs expected-output still weak**.

## Wave-2 plan (continue)

1. **Harder combo seeds** (`combo_swap_relop`, `combo_invert_relop`, `drop_first_guard`) on E6-win14 @ gpt-4o-mini + gemini — break saturation.
2. **RealSpec wrong_relop full corpus** @ gemini (best signal so far) + field ablations.
3. **Try alternate weak model** (e.g. deepseek / qwen-turbo) if combo still saturates gpt-4o-mini.
4. Keep paper narrative frozen until Wave-2 has ≥1 clean multi-model + RealSpec field result.
