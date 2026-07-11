# RealSpec Inventory

**Total tasks:** 203 (deduped; skipped 23 duplicates)

## By source_type

| source_type | n |
|-------------|--:|
| github_harvest | 47 |
| real_derived | 40 |
| github_sofl | 35 |
| industrial_pattern | 31 |
| published_case | 28 |
| textbook | 22 |

## Sources merged

- `benchmarks/external_sofl.json` ???`textbook`
- `benchmarks/manual_heldout.json` ???`textbook`
- `benchmarks/industrial_sofl.json` ???`industrial_pattern`
- `benchmarks/published_industrial_pilot.json` ???`published_case`
- `benchmarks/github_harvest_v1.json` ???`github_harvest`
- `benchmarks/hkca09_sofl_fsf.json` ???`github_sofl`
- `benchmarks/real_derived/humaneval_fsf.json` ???`real_derived`
- `benchmarks/real_derived/mbpp_fsf.json` ???`real_derived`

## Gaps

- GitHub live harvest still thin (see `harvest_github_specs.py`)
- FSM / decision-table converters are stubs for expansion
- No proprietary vendor dumps claimed

## External Evidence Sprint Phase 1 (2026-07-12)

Targeted harvest `wave3_targeted_v2` (`--max-files-per-repo 120`) did **not**
grow validated GitHub tasks past **n=48** (FCoTFL classical `.sofl` has no
auto-converter; see `artifacts/github_harvest/wave3_targeted_v2/EXPANSION_NOTE.md`).
RealSpec total remains **203**. Narrative: public reconstruction / harvest only.

Output: `benchmarks/realspec/realspec_v1.json`
