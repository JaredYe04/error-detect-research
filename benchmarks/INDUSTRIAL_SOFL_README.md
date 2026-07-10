# Industrial SOFL / FSF Benchmark Corpus

Practitioner-style ordered-guard FSF tasks for HSP-Agile **E11-style** external
evaluation (`benchmarks/industrial_sofl.json`).

## What this is / is not

| Claim | Status |
|-------|--------|
| Hand-authored FSF with industrial *domain names* and decision-table structure | Yes |
| Validated Z3 witnesses + formal check vs. generated `referenceCode` | Yes (`industrial_sofl_validation.json`) |
| Vendor production specs, proprietary sprint dumps, or scraped enterprise repos | **No** |
| Output of `HardTaskGenerator` / `HardSynthetic.*` | **No** |
| Fabricated bibliographic citations for `industrial_pattern:*` rows | **No** — those tags are pattern labels only |

Paper wording should say **practitioner-style / industrial-pattern corpus**, not
“real industrial case study,” unless a vendor submodule is added later.

## Purpose

Complement the curated textbook/IET set in `external_sofl.json` with additional
**domain-looking** decision processes (banking, telecom, SCADA, healthcare,
warehouse, airline, insurance, traffic, cache/rate-limit, library, process
control, fraud, enrollment, payroll).

## Construction method

1. **Schema** matches `external_sofl.json` / `src/benchmarks/external_sofl_corpus.py`:
   `taskId`, `kind`, `signature`, `fsfScenarios`, `referenceCode`,
   `promptSpec`, `externalProvenance`.
2. **Guards** are ordered first-match scenarios plus an `others` clause.
   Several tasks intentionally use **overlapping** guards so scenario order
   matters (same evaluation pressure as dense HardSynthetic overlap tiers).
3. **Reference code** is compiled from FSF via `generate_reference_code`
   (elif chain = first-match).
4. **Numeric scales** use compact integers (typically within Z3 witness bounds
   used by `generate_concrete_cases`) while names and structure follow industrial
   decision tables. E.g. credit bands `0–10` instead of raw FICO scores.
5. **Provenance** (`externalProvenance.source`) is one of:
   - `liu2004soflbook` — classic SOFL / Agile-SOFL patterns (ATM, library, tank)
   - `li2023iet_faultprevention` — IET fault-prevention RF-style patterns
   - `industrial_pattern:<domain>` — practitioner decision-table pattern for
     that domain (**not** a fabricated paper citation)

Authoritative task definitions live in
`src/benchmarks/industrial_sofl_corpus.py` (`generator: manual_industrial_curation`,
`corpus: industrial_sofl`). The JSON export is a derived artifact.

## Build / validate

```bash
python scripts/export_industrial_sofl.py
```

This writes `benchmarks/industrial_sofl.json` (with complexity annotations) and
`benchmarks/industrial_sofl_validation.json` (per-task witness coverage +
formal-check vs. `referenceCode`).

Loader: `src.benchmarks.industrial_sofl_corpus.load_industrial_sofl_tasks`.

## Relation to E11 / n1n industrial runs

- **E11** typically uses `external_sofl.json` (textbook/IET).
- **Industrial campaigns** (e.g. `artifacts/run_industrial_gpt4o_v1`,
  `run_industrial_claude46_v1`) point `benchmark_path` at
  `benchmarks/industrial_sofl.json` and evaluate B1/B2/M for external-validity
  tables in the HSP-Agile paper.
- Aggregate with:
  `python paper/hsp-agile/scripts/aggregate_n1n_campaigns.py`

Keep HardSynthetic tasks out of this file.
