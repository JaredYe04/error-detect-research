# Vendor Agile-SOFL toolchain (optional)

This directory is the **preferred** source of *real* SOFL/FSF artefacts for
HSP-Agile external validity.

## Why it is empty in the public repo

The historical `agile-sofl-toolchain` (SpecTool / `.asfl` examples) is **not**
published as an open GitHub repository. Industrial partners cited in SOFL
papers include:

| Partner / project | Role | Public dump? |
|-------------------|------|--------------|
| **Casco Signal Ltd.** (Luo et al., SOFL 2017 interlocking) | Railway interlocking SOFL case | No (proprietary) |
| **Mitsubishi Research Institute / Mitsubishi Electric** (Liu et al., railway crossing) | Crossing controller industrial trial | No |
| **Nippon Signal Co. Ltd.** (funded SOFL application research) | Signalling applications | No |
| Hosei / Hiroshima City Univ. teaching cases | ATM, hotel, banking, university IS | Partial descriptions only |

## How to obtain vendor data (recommended order)

1. **ECNU / Hosei collaboration** — email SpecTool / course `.asfl` packs
   (template: [`REQUEST_TEMPLATE.md`](REQUEST_TEMPLATE.md)). Contact starting
   point: `sliu@hosei.ac.jp` / http://cis.k.hosei.ac.jp/~sliu/  
   Place files under `vendor/agile-sofl-toolchain/examples/*.asfl`.
2. **Casco / signalling partner NDA** — export process-level FSF only
   (ordered scenarios; strip proprietary CDFD graphics) into the same folder.
3. **Published-industrial pilot (always available)** — until vendor files land:
   ```bash
   python scripts/export_published_industrial_pilot.py
   ```
   Output: `benchmarks/published_industrial_pilot.json`  
   Provenance: reconstructed FSF from *published* industrial SOFL case studies
   (railway crossing / interlocking, ATM, hotel, banking) — **not** a claim of
   proprietary production dumps.

## Import once `.asfl` files exist

```bash
python scripts/import_vendor_asfl.py \
  --vendor-dir vendor/agile-sofl-toolchain/examples \
  --out benchmarks/vendor_asfl_pilot.json
```

Optional merge with reconstructions: add `--merge-published`.  
Requires Node.js + `scripts/asfl_extract.mjs` (see `src/asfl_bridge.py`).

## Evaluation

```bash
# Published-industrial (default, no NDA)
python experiments/run_all.py --modes B1 B2 M_eq --repeats 1 \
  --benchmark-path benchmarks/published_industrial_pilot.json \
  --run-name run_pubind_pilot_v1 --parallelism 6 --force-max-attempts 3

# Vendor .asfl (after import)
python experiments/run_all.py --modes B1 B2 M_eq --repeats 1 \
  --benchmark-path benchmarks/vendor_asfl_pilot.json \
  --run-name run_vendor_asfl_v1 --parallelism 6 --force-max-attempts 3
```

Paper wording: call this a **published-industrial pilot** (or **vendor-asfl**
when `.asfl` imports succeed). Do **not** say “Casco production dump” unless
NDA artefacts are actually present.
