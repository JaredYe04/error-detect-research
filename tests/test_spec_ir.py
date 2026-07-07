"""Round-trip tests for SpecIR, FSFLowerer, and notation adapters.

Tests:
  1. SpecIR serialise → to_dict() / deserialise → from_dict() round-trip
  2. FSFLowerer.lower() produces a valid TaskSpec dict from SpecIR
  3. SOFLAdapter.from_task_spec() converts a hard_tasks.json entry to SpecIR
  4. MiniZAdapter.parse() returns SpecIR and FSFLowerer produces TaskSpec dict
  5. StateMachineAdapter.parse() returns SpecIR and FSFLowerer produces TaskSpec dict
  6. load_builtin_miniz_tasks() returns 18 dicts with required keys
  7. load_builtin_statemachine_tasks() returns 18 dicts with required keys
  8. get_adapter() registry works
"""
from __future__ import annotations
import json
from pathlib import Path
import pytest

from src.ir.spec_ir import GuardAtom, GuardedCase, Param, SpecIR
from src.ir.lowerers.fsf_lowerer import FSFLowerer
from src.adapters.sofl_adapter import SOFLAdapter
from src.adapters.miniz_adapter import MiniZAdapter, load_builtin_miniz_tasks
from src.adapters.statemachine_adapter import StateMachineAdapter, load_builtin_statemachine_tasks
from src.adapters import get_adapter

REPO_ROOT = Path(__file__).parent.parent


def _make_sample_specir() -> SpecIR:
    """Construct a minimal SpecIR for testing."""
    return SpecIR(
        task_id="TEST001",
        notation="mini_z",
        name="TestProc",
        inputs=[Param("x", "nat"), Param("y", "nat")],
        outputs=[Param("result", "nat")],
        cases=[
            GuardedCase(
                index=1,
                guard=[GuardAtom("x", "gt", 5)],
                postcondition={"result": 1},
                guard_text="x gt 5",
                post_text="result eq 1",
            ),
            GuardedCase(
                index=2,
                guard=[GuardAtom("", "others")],
                postcondition={"result": 0},
                guard_text="others",
                post_text="result eq 0",
            ),
        ],
        surface_prompt="Test spec",
        metadata={"module": "TestMod"},
    )


# ── Test 1: SpecIR round-trip ────────────────────────────────────────────────

def test_specir_to_dict_and_back():
    """SpecIR serialises to dict and deserialises back without data loss."""
    original = _make_sample_specir()
    d = original.to_dict()

    # Check dict structure
    assert d["task_id"] == "TEST001"
    assert d["notation"] == "mini_z"
    assert len(d["inputs"]) == 2
    assert len(d["cases"]) == 2
    assert d["cases"][0]["guard"][0]["var"] == "x"
    assert d["cases"][0]["guard"][0]["op"] == "gt"
    assert d["cases"][0]["guard"][0]["threshold"] == 5
    assert d["cases"][1]["guard"][0]["op"] == "others"

    # Round-trip
    restored = SpecIR.from_dict(d)
    assert restored.task_id == original.task_id
    assert restored.notation == original.notation
    assert restored.name == original.name
    assert len(restored.inputs) == len(original.inputs)
    assert restored.inputs[0].name == "x"
    assert len(restored.cases) == 2
    assert restored.cases[0].guard[0].var == "x"
    assert restored.cases[0].guard[0].threshold == 5
    assert restored.cases[1].guard[0].op == "others"
    assert restored.has_others_case
    assert restored.scenario_count == 2


# ── Test 2: FSFLowerer produces valid TaskSpec dict ──────────────────────────

def test_fsf_lowerer_produces_valid_task_spec():
    """FSFLowerer.lower() produces a dict with all required TaskSpec keys."""
    spec = _make_sample_specir()
    task = FSFLowerer.lower(spec)

    required_keys = {"taskId", "kind", "name", "signature", "fsfScenarios", "promptSpec"}
    assert required_keys.issubset(task.keys()), f"Missing keys: {required_keys - task.keys()}"

    assert task["taskId"] == "TEST001"
    assert task["kind"] == "process"
    assert isinstance(task["fsfScenarios"], list)
    assert len(task["fsfScenarios"]) == 2

    sc1 = task["fsfScenarios"][0]
    assert sc1["kind"] == "scenario"
    assert sc1["test"] == "x gt 5"
    assert sc1["def"] == "result eq 1"

    sc2 = task["fsfScenarios"][1]
    assert sc2["kind"] == "others"
    assert sc2["test"] == "others"

    # Embedded SpecIR for traceability
    assert "_spec_ir" in task
    assert task["_spec_ir"]["task_id"] == "TEST001"

    # signature
    assert task["signature"]["inputs"][0]["name"] == "x"
    assert task["signature"]["outputs"][0]["name"] == "result"


# ── Test 3: SOFLAdapter.from_task_spec() from hard_tasks.json ────────────────

def test_sofl_adapter_from_task_spec():
    """SOFLAdapter converts a real hard_tasks.json entry to SpecIR."""
    hard_tasks_path = REPO_ROOT / "benchmarks" / "hard_tasks.json"
    if not hard_tasks_path.exists():
        pytest.skip("hard_tasks.json not found")

    with open(hard_tasks_path, encoding="utf-8") as f:
        tasks = json.load(f)
    task = tasks[0]

    spec = SOFLAdapter.from_task_spec(task)

    assert isinstance(spec, SpecIR)
    assert spec.notation == "sofl"
    assert spec.task_id == task["taskId"]
    assert len(spec.inputs) == len(task["signature"]["inputs"])
    assert len(spec.outputs) == len(task["signature"]["outputs"])
    assert len(spec.cases) == len(task["fsfScenarios"])
    assert spec.has_others_case  # hard tasks always have an 'others' case

    # Round-trip through dict
    restored = SpecIR.from_dict(spec.to_dict())
    assert restored.task_id == spec.task_id
    assert len(restored.cases) == len(spec.cases)


# ── Test 4: MiniZAdapter.parse() → SpecIR → FSFLowerer ──────────────────────

_MINI_Z_SPEC = """\
SCHEMA SimpleCalc
INPUTS: x: int, y: int
OUTPUTS: result: int

CASE x gt 5 => result eq 1
CASE x eq 0 => result eq 2
DEFAULT result eq 0
"""

def test_miniz_adapter_parse_returns_specir():
    """MiniZAdapter.parse() returns a SpecIR with correct structure."""
    adapter = MiniZAdapter()
    spec = adapter.parse(_MINI_Z_SPEC, "MZ_TEST")

    assert isinstance(spec, SpecIR)
    assert spec.notation == "mini_z"
    assert spec.task_id == "MZ_TEST"
    assert len(spec.inputs) == 2
    assert spec.inputs[0].name == "x"
    assert len(spec.outputs) == 1
    assert spec.outputs[0].name == "result"
    assert len(spec.cases) == 3  # 2 CASEs + 1 DEFAULT
    assert spec.has_others_case
    assert spec.cases[0].guard[0].var == "x"
    assert spec.cases[0].guard[0].op == "gt"
    assert spec.cases[0].guard[0].threshold == 5
    assert spec.cases[2].guard[0].op == "others"


def test_miniz_adapter_lowered_task_spec():
    """MiniZAdapter.parse() + FSFLowerer produces correct TaskSpec dict."""
    adapter = MiniZAdapter()
    spec = adapter.parse(_MINI_Z_SPEC, "MZ_TEST")
    task = FSFLowerer.lower(spec)

    assert task["taskId"] == "MZ_TEST"
    assert len(task["fsfScenarios"]) == 3
    assert task["fsfScenarios"][-1]["kind"] == "others"
    assert task["fsfScenarios"][0]["test"] == "x gt 5"


def test_miniz_to_task_spec_via_base():
    """SpecAdapter.to_task_spec() produces TaskSpec compatible dict."""
    adapter = MiniZAdapter()
    spec = adapter.parse(_MINI_Z_SPEC, "MZ_TEST")
    task = adapter.to_task_spec(spec)
    assert "taskId" in task
    assert "fsfScenarios" in task


# ── Test 5: StateMachineAdapter.parse() → SpecIR → FSFLowerer ───────────────

_SM_SPEC = """\
INPUTS: level: int, threshold: int
OUTPUTS: status: int, action: int
STATES: normal, warning, critical
INITIAL: normal

normal → critical  IF level gt 10 && threshold gt 5   DO status eq 3 && action eq 2
normal → warning   IF level gt 5                       DO status eq 2 && action eq 1
others                                                  DO status eq 1 && action eq 0
"""

def test_statemachine_adapter_parse_returns_specir():
    """StateMachineAdapter.parse() returns a SpecIR with correct structure."""
    adapter = StateMachineAdapter()
    spec = adapter.parse(_SM_SPEC, "SM_TEST")

    assert isinstance(spec, SpecIR)
    assert spec.notation == "mini_statemachine"
    assert spec.task_id == "SM_TEST"
    assert len(spec.inputs) == 2
    assert len(spec.outputs) == 2
    assert spec.has_others_case
    assert len(spec.cases) == 3  # 2 transitions + 1 others
    assert spec.cases[0].guard[0].var == "level"
    assert spec.cases[0].guard[0].op == "gt"


def test_statemachine_lowered_task_spec():
    """StateMachineAdapter + FSFLowerer produces a correct TaskSpec dict."""
    adapter = StateMachineAdapter()
    spec = adapter.parse(_SM_SPEC, "SM_TEST")
    task = FSFLowerer.lower(spec)

    assert task["taskId"] == "SM_TEST"
    assert len(task["fsfScenarios"]) == 3
    assert task["fsfScenarios"][-1]["kind"] == "others"


# ── Test 6: load_builtin_miniz_tasks() ───────────────────────────────────────

def test_load_builtin_miniz_tasks_count_and_schema():
    """load_builtin_miniz_tasks() returns 18 TaskSpec dicts with required keys."""
    tasks = load_builtin_miniz_tasks()
    assert len(tasks) == 18, f"Expected 18, got {len(tasks)}"
    required_keys = {"taskId", "name", "signature", "fsfScenarios", "promptSpec"}
    for t in tasks:
        assert required_keys.issubset(t.keys()), f"Task missing keys: {required_keys - t.keys()}"
        assert t["taskId"].startswith("MZ")
        assert len(t["fsfScenarios"]) >= 2
        # Last scenario should be 'others'
        assert t["fsfScenarios"][-1]["kind"] == "others"
        # SpecIR embedded
        assert "_spec_ir" in t
        assert t["_spec_ir"]["notation"] == "mini_z"


# ── Test 7: load_builtin_statemachine_tasks() ────────────────────────────────

def test_load_builtin_statemachine_tasks_count_and_schema():
    """load_builtin_statemachine_tasks() returns 18 TaskSpec dicts with required keys."""
    tasks = load_builtin_statemachine_tasks()
    assert len(tasks) == 18, f"Expected 18, got {len(tasks)}"
    required_keys = {"taskId", "name", "signature", "fsfScenarios", "promptSpec"}
    for t in tasks:
        assert required_keys.issubset(t.keys()), f"Task missing keys: {required_keys - t.keys()}"
        assert t["taskId"].startswith("SM")
        assert len(t["fsfScenarios"]) >= 2
        assert t["fsfScenarios"][-1]["kind"] == "others"
        assert "_spec_ir" in t
        assert t["_spec_ir"]["notation"] == "mini_statemachine"


# ── Test 8: Adapter registry ─────────────────────────────────────────────────

def test_get_adapter_registry():
    """get_adapter() returns correct adapter instances."""
    mz = get_adapter("mini_z")
    assert isinstance(mz, MiniZAdapter)
    assert mz.notation_name == "mini_z"

    sm = get_adapter("mini_statemachine")
    assert isinstance(sm, StateMachineAdapter)
    assert sm.notation_name == "mini_statemachine"

    sofl = get_adapter("sofl")
    assert isinstance(sofl, SOFLAdapter)
    assert sofl.notation_name == "sofl"

    with pytest.raises(ValueError, match="No adapter registered"):
        get_adapter("nonexistent_notation")


def test_pipeline_accepts_specir():
    """Pipeline normalizes SpecIR inputs via FSFLowerer before execution."""
    from src.pipeline.task_input import normalize_task

    spec = _make_sample_specir()
    task = normalize_task(spec)
    assert task["taskId"] == "TEST001"
    assert "fsfScenarios" in task
    assert "_spec_ir" in task


def test_normalize_task_embeds_spec_ir_for_legacy_dict():
    """Legacy TaskSpec dicts gain embedded _spec_ir via SOFLAdapter."""
    from src.pipeline.task_input import normalize_task

    hard_tasks_path = REPO_ROOT / "benchmarks" / "hard_tasks.json"
    if not hard_tasks_path.exists():
        pytest.skip("hard_tasks.json not found")

    with open(hard_tasks_path, encoding="utf-8") as f:
        task = json.load(f)[0]

    normalized = normalize_task(task)
    assert "_spec_ir" in normalized
    assert normalized["_spec_ir"]["notation"] == "sofl"
