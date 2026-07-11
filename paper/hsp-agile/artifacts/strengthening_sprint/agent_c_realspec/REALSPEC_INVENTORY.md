# RealSpec Inventory

**Total tasks:** 103 (deduped; skipped 22 duplicates)

## By source_type

| source_type | n |
|-------------|--:|
| real_derived | 40 |
| industrial_pattern | 31 |
| textbook | 22 |
| published_case | 10 |

## Sources merged

- `benchmarks/external_sofl.json` ???`textbook`
- `benchmarks/manual_heldout.json` ???`textbook`
- `benchmarks/industrial_sofl.json` ???`industrial_pattern`
- `benchmarks/published_industrial_pilot.json` ???`published_case`
- `benchmarks/real_derived/humaneval_fsf.json` ???`real_derived`
- `benchmarks/real_derived/mbpp_fsf.json` ???`real_derived`

## Gaps

- GitHub live harvest still thin (see `harvest_github_specs.py`)
- FSM / decision-table converters are stubs for expansion
- No proprietary vendor dumps claimed

Output: `benchmarks/realspec/realspec_v1.json`
