# Published Industrial SOFL Pilot

**File:** `benchmarks/published_industrial_pilot.json`  
**Generator:** `src/benchmarks/published_industrial_pilot.py`  
**Export:** `python scripts/export_published_industrial_pilot.py`  
**Validate:** `python scripts/validate_published_industrial_pilot.py`  
**Full honesty + provenance:** `benchmarks/DESENSITIZED_REAL_SOFL_PILOT.md`

## Honesty

| Claim | OK? |
|-------|-----|
| Reconstructed from **published** industrial SOFL case studies | Yes |
| Railway crossing (Liu/Mitsubishi), interlocking (Luo/Casco SOFL’17), ATM/hotel/banking (Liu / Agile-SOFL) | Yes |
| Desensitized compact integers; no proprietary IDs | Yes |
| Proprietary Casco / Mitsubishi / Nippon Signal production dumps | **No** |
| Drop-in for vendor `.asfl` when `vendor/agile-sofl-toolchain/examples` exists | Yes |

## Scale

Wave-2 expansion targets **~28** desensitized published-case tasks (was 10).
See provenance catalog in `DESENSITIZED_REAL_SOFL_PILOT.md`.

## Run

```bash
python experiments/run_all.py --modes B1 B2 M_eq --repeats 1 \
  --benchmark-path benchmarks/published_industrial_pilot.json \
  --run-name run_desens_real_sofl_v1 --parallelism 4 --force-max-attempts 3 \
  --model ecnu-plus
```
