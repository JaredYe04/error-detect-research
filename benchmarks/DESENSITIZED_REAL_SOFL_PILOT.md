# Desensitized Real SOFL Pilot

**Corpus:** `benchmarks/published_industrial_pilot.json`  
**Generator:** `src/benchmarks/published_industrial_pilot.py`  
**Validation:** `python scripts/validate_published_industrial_pilot.py`  
**Export:** `python scripts/export_published_industrial_pilot.py`

## Honesty contract

| Claim | Status |
|-------|--------|
| Reconstructed from **publicly described** industrial / teaching SOFL cases | Yes |
| Desensitized (compact ints, no station IDs, no vendor dumps) | Yes |
| Proprietary Casco / Mitsubishi / Nippon Signal / bank production `.asfl` | **No** |
| Suitable for C4 external-validity pilot | Yes |

## Provenance catalog (Wave-2 expansion)

| Domain | Task IDs (prefix `PubIndPilot.`) | Public source |
|--------|----------------------------------|---------------|
| Railway crossing | CrossingApproach, CrossingClear, ApproachLock | Liu et al. WIFT'98 railway crossing (Mitsubishi trial) |
| Railway interlocking | RouteLock, SignalAspect, PointMove, RouteConflict, FlankProtect, SignalClear | Luo et al. SOFL'17 Casco interlocking + public interlocking-table patterns |
| ATM / Agile-SOFL | AtmAuth, AtmWithdraw, AtmDeposit, AtmTransfer, AtmInquire, DailyWithdrawCap | Liu SOFL book; Agile-SOFL ATM example (Waseda PDF / QRS companion) |
| Hotel | HotelBook, HotelCheckout | Liu SOFL hotel application list |
| Banking | TransferGuard, FraudHold | Liu online-banking SOFL modelling |
| Library / process | LibraryBorrow, LibraryReturn, WaterTank, InventoryReorder, TrafficPriority | Liu 2004 SOFL book teaching/industrial examples |
| IET fault-prevention style | AccessBadge, MedDose, PowerTrip, InsuranceClaim | Li & Liu IET Software 2023 / QRS-C 2022 modelling style |

## Desensitization rules

1. Replace real thresholds (e.g. 200,000 JPY) with small integers in Z3 witness bounds.
2. Strip organization, station, and account identifiers.
3. Keep **first-match ordering** and overlap structure that industrial decision tables exhibit.
4. Tag every task with `externalProvenance.source` bibliographic key.

## Run evaluation

```powershell
python scripts/export_published_industrial_pilot.py
python scripts/validate_published_industrial_pilot.py
python experiments/run_all.py --modes B1 B2 M_eq --repeats 1 `
  --benchmark-path benchmarks/published_industrial_pilot.json `
  --run-name run_desens_real_sofl_v1 --parallelism 4 --force-max-attempts 3 `
  --model ecnu-plus
```

Then rebuild RealSpec merge:

```powershell
python paper/hsp-agile/scripts/strengthening/build_realspec_corpus.py
```
