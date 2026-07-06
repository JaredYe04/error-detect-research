"""Reference implementations for benchmark tasks (B0 ground truth)."""

from __future__ import annotations

from typing import Any

from src.benchmarks.reference_gen import generate_reference_code, validate_reference

# Hand-tuned references override auto-generated when available
HANDCRAFTED: dict[str, str] = {}


def borrow(member_id: int, book_id: int) -> dict[str, int]:
    if member_id > 0:
        return {"success": 1}
    if book_id == 0:
        return {"success": 0}
    return {"success": 0}


def return_book(member_id: int, book_id: int) -> dict[str, int]:
    if member_id > 0:
        return {"success": 1}
    return {"success": 0}


def reserve(member_id: int, book_id: int) -> dict[str, int]:
    if book_id > 0:
        return {"queued": 1}
    return {"queued": 0}


def list_catalog(count: int) -> dict[str, int]:
    if count > 0:
        return {"count": 1}
    return {"count": 0}


REFERENCE_MAP = {
    "SYSTEM_Library.Borrow": borrow,
    "SYSTEM_Library.Return": return_book,
    "SYSTEM_Library.Reserve": reserve,
    "SYSTEM_Library.ListCatalog": list_catalog,
}


def get_reference_code(task_id: str, task: dict[str, Any] | None = None) -> str | None:
    if task_id in HANDCRAFTED:
        return HANDCRAFTED[task_id]
    fn = REFERENCE_MAP.get(task_id)
    if fn is not None:
        import inspect
        return inspect.getsource(fn)
    if task is not None:
        code = generate_reference_code(task)
        if validate_reference(task, code):
            return code
    return None


def get_reference_callable(task_id: str):
    return REFERENCE_MAP.get(task_id)
