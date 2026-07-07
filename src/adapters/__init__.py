"""SgDP Specification Adapter registry."""
from src.adapters.base import SpecAdapter
from src.adapters.miniz_adapter import MiniZAdapter
from src.adapters.statemachine_adapter import StateMachineAdapter
from src.adapters.sofl_adapter import SOFLAdapter

ADAPTERS: dict[str, type[SpecAdapter]] = {
    "mini_z": MiniZAdapter,
    "mini_statemachine": StateMachineAdapter,
    "sofl": SOFLAdapter,
}


def get_adapter(notation: str) -> SpecAdapter:
    """Get an instantiated adapter for the given notation name."""
    cls = ADAPTERS.get(notation)
    if cls is None:
        raise ValueError(
            f"No adapter registered for notation {notation!r}. "
            f"Available: {list(ADAPTERS.keys())}"
        )
    return cls()
