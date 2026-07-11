"""Unit tests for parameterized SMT integer domains."""

from __future__ import annotations

from src.formal.fsf_eval import DEFAULT_INT_HI, DEFAULT_INT_LO, generate_concrete_cases


def _firewall_task_like():
    scenarios = [
        {"index": 1, "kind": "scenario", "test": "src_trust lt 0", "def": "action eq 0"},
        {
            "index": 2,
            "kind": "scenario",
            "test": "src_trust ge 5 && dst_port gt 1024",
            "def": "action eq 1",
        },
        {"index": 3, "kind": "others", "test": "others", "def": "action eq 0"},
    ]
    signature = {
        "inputs": [{"name": "src_trust", "type": "int"}, {"name": "dst_port", "type": "int"}],
        "outputs": [{"name": "action", "type": "int"}],
    }
    return scenarios, signature


def test_default_domain_constants():
    assert DEFAULT_INT_LO == -5
    assert DEFAULT_INT_HI == 20


def test_wide_domain_needed_for_high_ports():
    scenarios, signature = _firewall_task_like()
    narrow = generate_concrete_cases(scenarios, signature, int_lo=-5, int_hi=20)
    wide = generate_concrete_cases(scenarios, signature, int_lo=-5, int_hi=2048)
    # Scenario 2 needs dst_port > 1024; only the wide box can witness it.
    narrow_idx = {c.scenario_index for c in narrow}
    wide_idx = {c.scenario_index for c in wide}
    assert 2 in wide_idx
    assert 2 not in narrow_idx or all(
        c.inputs.get("dst_port", 0) <= 20 for c in narrow if c.scenario_index == 2
    )
    assert any(c.inputs.get("dst_port", 0) > 1024 for c in wide if c.scenario_index == 2)
