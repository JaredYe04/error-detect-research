# B3--B5 extended baseline protocol (E1-ext)

## Status (2026-07-10, post REV-0)

| Item | State |
|------|--------|
| `config_for_mode` B3/B4/B5 branches | **Validated** (`tests/test_config_modes.py`, 3/3 pass) |
| Smoke `run_b345_smoke_v3` | **Complete** (9/9 jobs; distinct `feedback_variant`: self_critique / execution_trace / reflexion) |
| Run `artifacts/run_ccf_b_extended_v1` | **Complete** (1080/1080 jobs) |
| Modes | B3 (Self-Refine), B4 (Self-Debug), B5 (Reflexion-lite) |
| Benchmark | 120-task hard set (`load_benchmark()`) |
| Repeats | 3 per mode (360 rows each); paper merges **repeat 0** |
| LLM | ECNU `ecnu-plus` via `ECNUClient` |

**Re-run only** if you change B3--B5 `config_for_mode` semantics or need fresh LLM samples.

### Recorded artefact metrics (repeat 0, n=120; merged into paper `results_raw.csv`)

| Mode | Strict | Conf. | Kill | Lat. (ms) | Fail. |
|------|--------|-------|------|-----------|-------|
| B3 | 5.0% | 81.9% | 51.0% | 13,210 | 2.33 |
| B4 | 5.0% | 87.1% | 49.3% | 10,758 | 2.49 |
| B5 | 5.0% | 81.1% | 50.6% | 6,212 | 2.33 |
| M (E1 ref.) | 25.0% | 90.4% | 60.6% | 43,659 | 1.98 |

Full 3-repeat means: B3 Conf. 81.8%, B4 87.5%, B5 81.7% (`meta.json` reports 1065 LLM calls for the campaign).

---

## Prerequisites

```powershell
cd d:\repos\error-detect-research
# Set ECNU_API_KEY in .env or environment
```

---

## Smoke test (3 tasks, 1 repeat) — post REV-0 validation

```powershell
python -u experiments/run_all.py `
  --modes B3 B4 B5 `
  --repeats 1 `
  --task-limit 3 `
  --run-name run_b345_smoke_v3 `
  --parallelism 3
```

Expected: `artifacts/run_b345_smoke_v3/results.jsonl` (9 lines), distinct feedback variants per mode.

---

## Full E1-ext campaign (120 tasks, 3 repeats)

Matches completed run `run_ccf_b_extended_v1`:

```powershell
python -u experiments/run_all.py `
  --modes B3 B4 B5 `
  --repeats 3 `
  --run-name run_ccf_b_extended_v1 `
  --parallelism 8
```

---

## Merge into paper pipeline

```powershell
python paper/hsp-agile/scripts/prepare_paper_data.py `
  --extended-run-dir artifacts/run_ccf_b_extended_v1 `
  --extended-repeat 0
```

Then `paper/hsp-agile/scripts/build_pdf.ps1`.
