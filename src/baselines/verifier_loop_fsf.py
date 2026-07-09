"""VerifierLoop-FSF baseline (mode B6, REV-7).

Adapts verifier-in-the-loop repair to FSF ordered-guard tasks:
  - SMT witness checking during the repair loop (same case budget as M)
  - Structured counterexample feedback (scenario guard + inputs + expected)
  - No Semantic Feedback IR projection (no violation_type / reason / fix hints)
  - No pattern guard

Brackets B2 (test-only, no formal loop) and M (full semantic IR + patterns).
"""

from __future__ import annotations

from src.pipeline.runner import PipelineConfig, config_for_mode

MODE = "B6"
DESCRIPTION = "VerifierLoop-FSF: SMT witnesses + structured test cex, no SpecIR repair IR"


def pipeline_config() -> PipelineConfig:
    """Return the canonical B6 pipeline configuration."""
    return config_for_mode(MODE)
