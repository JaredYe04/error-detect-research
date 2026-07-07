"""Lightweight intra-procedural CFG builder (stdlib only).

Builds a basic-block control flow graph for a single Python function extracted
from a source string.  Designed for use with PatternGuard checks (RF04, RF07,
RF13) without any third-party dependencies.
"""

from __future__ import annotations

import ast
import re


# ---------------------------------------------------------------------------
# CFG construction
# ---------------------------------------------------------------------------

def build_cfg(code: str) -> dict:
    """Build a basic-block CFG for the first function found in *code*.

    Returns a dict::

        {
            'nodes': [{'id': int, 'stmts': [ast.stmt], 'label': str}, ...],
            'edges': [(src_id, dst_id), ...],
            'entry': int,
            'exits': [int, ...],   # ids of blocks that contain a Return
        }

    The *entry* block is always node 0 and is an empty sentinel.  The *exits*
    list contains the ids of every block whose last statement is a ``return``.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {"nodes": [], "edges": [], "entry": 0, "exits": []}

    func: ast.FunctionDef | None = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func = node
            break
    if func is None:
        return {"nodes": [], "edges": [], "entry": 0, "exits": []}

    nodes: list[dict] = []
    edges: list[tuple[int, int]] = []
    exits: list[int] = []
    _seen_edges: set[tuple[int, int]] = set()

    def _new_block(stmts: list, label: str) -> int:
        idx = len(nodes)
        nodes.append({"id": idx, "stmts": list(stmts), "label": label})
        return idx

    def _add_edge(src: int, dst: int) -> None:
        if (src, dst) not in _seen_edges:
            _seen_edges.add((src, dst))
            edges.append((src, dst))

    def _process(stmts: list[ast.stmt], preds: list[int]) -> list[int]:
        """Walk *stmts*, wiring blocks to *preds*.  Returns live successor ids."""
        acc: list[ast.stmt] = []
        live = list(preds)

        for stmt in stmts:
            if isinstance(stmt, ast.Return):
                acc.append(stmt)
                blk = _new_block(acc, "return")
                for p in live:
                    _add_edge(p, blk)
                exits.append(blk)
                return []  # control does not flow past a return

            if isinstance(stmt, ast.If):
                # flush accumulated straight-line stmts
                if acc:
                    blk = _new_block(acc, "seq")
                    for p in live:
                        _add_edge(p, blk)
                    live = [blk]
                    acc = []

                cond = _new_block([stmt.test], "cond")
                for p in live:
                    _add_edge(p, cond)

                true_live = _process(stmt.body, [cond])
                false_live = _process(stmt.orelse, [cond]) if stmt.orelse else [cond]
                live = true_live + false_live

            elif isinstance(stmt, (ast.For, ast.While)):
                if acc:
                    blk = _new_block(acc, "seq")
                    for p in live:
                        _add_edge(p, blk)
                    live = [blk]
                    acc = []

                loop_hdr = _new_block([stmt], "loop")
                for p in live:
                    _add_edge(p, loop_hdr)

                body_live = _process(stmt.body, [loop_hdr])
                # back-edge from body to header (approximate)
                for p in body_live:
                    _add_edge(p, loop_hdr)
                live = [loop_hdr]

            elif isinstance(stmt, ast.Try):
                if acc:
                    blk = _new_block(acc, "seq")
                    for p in live:
                        _add_edge(p, blk)
                    live = [blk]
                    acc = []

                try_live = _process(stmt.body, live)
                handler_live: list[int] = []
                for h in stmt.handlers:
                    handler_live.extend(_process(h.body, live))
                else_live = _process(stmt.orelse, try_live) if stmt.orelse else try_live
                finally_live = _process(stmt.finalbody, else_live + handler_live) if stmt.finalbody else else_live + handler_live  # type: ignore[attr-defined]
                live = finally_live

            else:
                acc.append(stmt)

        if acc:
            blk = _new_block(acc, "seq")
            for p in live:
                _add_edge(p, blk)
            live = [blk]

        return live

    entry = _new_block([], "entry")
    _process(func.body, [entry])

    return {"nodes": nodes, "edges": edges, "entry": entry, "exits": exits}


# ---------------------------------------------------------------------------
# CFG analysis helpers
# ---------------------------------------------------------------------------

def has_unreachable_returns(cfg: dict) -> bool:
    """Return True if any return block is not reachable from the entry node."""
    nodes = cfg.get("nodes", [])
    edges = cfg.get("edges", [])
    entry = cfg.get("entry", 0)
    exits = cfg.get("exits", [])

    if not nodes or not exits:
        return False

    # BFS reachability from entry
    reachable: set[int] = set()
    queue = [entry]
    while queue:
        cur = queue.pop(0)
        if cur in reachable:
            continue
        reachable.add(cur)
        for src, dst in edges:
            if src == cur:
                queue.append(dst)

    return any(e not in reachable for e in exits)


def has_empty_branch_bodies(code: str) -> bool:
    """Return True if any else/elif block contains only ``pass`` (RF13).

    Checks both via AST (accurate) and a regex fallback for edge cases.
    """
    # Regex fast-path
    if re.search(r"else\s*:\s*\n\s+pass\b", code):
        return True

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False

    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        orelse = node.orelse
        if not orelse:
            continue
        # else branch with a single Pass statement
        if len(orelse) == 1 and isinstance(orelse[0], ast.Pass):
            return True
        # elif chain: orelse is a single ast.If — check its else recursively
        # (handled by ast.walk visiting the inner If)

    return False


def all_paths_define_outputs(code: str, output_keys: list[str]) -> bool:
    """Return True if every ``return`` in the function returns all *output_keys*.

    Checks return dict literals; non-dict returns are treated as suspicious
    (returns False) unless *output_keys* is empty.
    """
    if not output_keys:
        return True

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False

    found_any_return = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Return):
            continue
        found_any_return = True
        val = node.value
        if val is None:
            return False
        if isinstance(val, ast.Dict):
            ret_keys: set[str] = set()
            for k in val.keys:
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    ret_keys.add(k.value)
            if not all(k in ret_keys for k in output_keys):
                return False
        # Non-dict return: can't verify statically, treat as non-conformant
        # only when a dict is expected (output_keys non-empty)
        elif not isinstance(val, ast.Name):
            return False

    return found_any_return
