# Published Industrial SOFL Pilot

**File:** `benchmarks/published_industrial_pilot.json` ($n{=}10$)  
**Generator:** `src/benchmarks/published_industrial_pilot.py`  
**Export:** `python scripts/export_published_industrial_pilot.py`

## Honesty

| Claim | OK? |
|-------|-----|
| Reconstructed from **published** industrial SOFL case studies | Yes |
| Railway crossing (Liu/Mitsubishi), interlocking (Luo/Casco SOFL’17), ATM/hotel/banking (Liu applications) | Yes |
| Proprietary Casco / Mitsubishi / Nippon Signal production dumps | **No** |
| Drop-in for vendor `.asfl` when `vendor/agile-sofl-toolchain/examples` exists | Yes |

See `vendor/README.md` for how to obtain real toolchain examples.

## Tasks

| ID | Domain | Provenance key |
|----|--------|----------------|
| CrossingApproach / CrossingClear | Railway crossing | `liu1998railwaycrossing` |
| RouteLock / SignalAspect / PointMove | Interlocking | `luo2017railway` |
| AtmAuth / AtmWithdraw | ATM | `liu2004soflbook` |
| HotelBook | Hotel | `liu_sofl_hotel` |
| TransferGuard / FraudHold | Online banking | `liu_sofl_online_banking` |

## Run

```bash
python experiments/run_all.py --modes B1 B2 M_eq --repeats 1 \
  --benchmark-path benchmarks/published_industrial_pilot.json \
  --run-name run_pubind_pilot_v1 --parallelism 4 --force-max-attempts 3
```
