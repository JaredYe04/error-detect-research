#!/usr/bin/env bash
# Offline reproducibility smoke test for SgDP / HSP-Agile artifact.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> [1/3] Unit tests (SpecIR, Feedback IR, schema validation)"
python -m pytest tests/test_spec_ir.py tests/test_feedback_ir.py tests/test_schema_validate.py -q

echo "==> [2/3] Paper metrics (uses bundled artifacts when available)"
FEEDBACK_DIR="artifacts/run_feedback_v2/feedback_variants"
if [[ -d "$FEEDBACK_DIR" ]]; then
  python paper/hsp-agile/scripts/prepare_mechanism_data.py --feedback-dir "$FEEDBACK_DIR"
else
  echo "    (skip prepare_mechanism_data: $FEEDBACK_DIR not found)"
fi

echo "==> [3/3] Regenerate matplotlib figures"
python paper/hsp-agile/figures/scripts/plot_mpl_figures.py

echo "==> Reproduce smoke complete."
echo "    Full LLM experiments: python experiments/run_all.py --quick"
echo "    E6 feedback variants: python experiments/run_sweep.py --experiment feedback_variants --task-limit 3"
