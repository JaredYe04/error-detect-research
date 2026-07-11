"""Lightweight ASFL/SOFL FSF extractor (no Node parser required).

Parses process blocks that contain an ``FSF :`` section of the form::

    FSF :
    customer > 0 && ok = 1 ||
    product = 0 && ok = 0 ||
    others && ok = 0
"""

from __future__ import annotations

import re
from typing import Any

from src.benchmarks.reference_gen import generate_reference_code


_PROCESS_RE = re.compile(
    r"process\s+([A-Za-z_][\w]*)\s*\((.*?)\)\s*"
    r"(?:([A-Za-z_][\w\s,:]*)?)?\s*"
    r"(?:ext[\s\S]*?)?"
    r"FSF\s*:\s*"
    r"([\s\S]*?)"
    r"(?=decom:|comment:|end_process|process\s+|end_module|module\s+)",
    re.IGNORECASE,
)

_PARAM_RE = re.compile(r"([A-Za-z_][\w]*)\s*:\s*[A-Za-z_][\w]*")


def _norm_ops(expr: str) -> str:
    e = expr.strip()
    e = re.sub(r"\s*>=\s*", " ge ", e)
    e = re.sub(r"\s*<=\s*", " le ", e)
    e = re.sub(r"\s*!=\s*", " ne ", e)
    e = re.sub(r"\s*<>\s*", " ne ", e)
    e = re.sub(r"\s*==\s*", " eq ", e)
    e = re.sub(r"(?<![<>=!])=(?!=)", " eq ", e)
    e = re.sub(r"\s*>\s*", " gt ", e)
    e = re.sub(r"\s*<\s*", " lt ", e)
    e = re.sub(r"\band\b", "&&", e, flags=re.I)
    e = re.sub(r"\bor\b", "||", e, flags=re.I)
    e = re.sub(r"\s+", " ", e).strip()
    return e


def _split_fsf_clauses(body: str) -> list[str]:
    # join continued lines; split on ||
    flat = " ".join(line.strip() for line in body.splitlines() if line.strip())
    parts = [p.strip().rstrip(";").strip() for p in re.split(r"\|\|", flat) if p.strip()]
    return parts


def _parse_clause(clause: str) -> tuple[str, str] | None:
    """Return (guard_or_others, post_assignments)."""
    c = clause.strip()
    if not c:
        return None
    # others && post
    m = re.match(r"^others\s*(?:&&|,)?\s*(.+)$", c, flags=re.I)
    if m:
        return "others", _norm_ops(m.group(1))
    # guard && post  (split on last && that separates guard from assignment-like post)
    if "&&" in c:
        left, right = c.rsplit("&&", 1)
        left, right = left.strip(), right.strip()
        # heuristic: post side contains '=' / eq
        if re.search(r"=|\beq\b", right, flags=re.I):
            return _norm_ops(left), _norm_ops(right)
        # maybe multiple && in guard — take first assignment chunk from the right
        bits = [b.strip() for b in c.split("&&")]
        for i in range(len(bits) - 1, 0, -1):
            if re.search(r"=|\beq\b", bits[i], flags=re.I):
                guard = " && ".join(_norm_ops(b) for b in bits[:i])
                post = " && ".join(_norm_ops(b) for b in bits[i:])
                return guard, post
    return None


def _params_from_sig(sig: str) -> list[dict[str, str]]:
    return [{"name": m.group(1), "type": "int"} for m in _PARAM_RE.finditer(sig or "")]


def _outputs_from_header(header: str | None) -> list[dict[str, str]]:
    if not header:
        return [{"name": "result", "type": "int"}]
    outs = []
    for m in _PARAM_RE.finditer(header):
        outs.append({"name": m.group(1), "type": "int"})
    return outs or [{"name": "result", "type": "int"}]


def _infer_names(scenarios: list[dict[str, Any]], side: str) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    stop = {
        "others", "true", "false", "and", "or", "eq", "ne", "gt", "ge", "lt", "le",
    }
    for sc in scenarios:
        text = sc.get("test" if side == "test" else "def", "")
        for tok in re.findall(r"\b[A-Za-z_][\w]*\b", text):
            if tok.lower() in stop or tok in seen:
                continue
            seen.add(tok)
            names.append(tok)
    return names


def extract_fsf_tasks_from_asfl(
    text: str,
    *,
    provenance: dict[str, Any],
) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for m in _PROCESS_RE.finditer(text):
        name, sig, out_header, fsf_body = m.group(1), m.group(2), m.group(3), m.group(4)
        clauses = _split_fsf_clauses(fsf_body)
        scenarios: list[dict[str, Any]] = []
        idx = 1
        has_others = False
        for cl in clauses:
            parsed = _parse_clause(cl)
            if not parsed:
                continue
            guard, post = parsed
            if guard == "others":
                scenarios.append({"index": 0, "kind": "others", "test": "others", "def": post})
                has_others = True
            else:
                scenarios.append({"index": idx, "kind": "scenario", "test": guard, "def": post})
                idx += 1
        if not scenarios:
            continue
        # reindex others last
        regs = [s for s in scenarios if s["kind"] != "others"]
        others = [s for s in scenarios if s["kind"] == "others"]
        scenarios = []
        for i, s in enumerate(regs, start=1):
            s = dict(s)
            s["index"] = i
            scenarios.append(s)
        if others:
            o = dict(others[0])
            o["index"] = len(scenarios) + 1
            scenarios.append(o)
        elif not has_others:
            # synthesize others
            outs = _outputs_from_header(out_header)
            dpost = " && ".join(f"{o['name']} eq 0" for o in outs)
            scenarios.append(
                {"index": len(scenarios) + 1, "kind": "others", "test": "others", "def": dpost}
            )

        inputs = _params_from_sig(sig)
        outputs = _outputs_from_header(out_header)
        # fill missing vars referenced in scenarios
        for n in _infer_names(scenarios, "test"):
            if n not in {p["name"] for p in inputs}:
                inputs.append({"name": n, "type": "int"})
        for n in _infer_names(scenarios, "def"):
            if n not in {p["name"] for p in outputs} and n not in {p["name"] for p in inputs}:
                outputs.append({"name": n, "type": "int"})

        in_names = ", ".join(p["name"] for p in inputs)
        out_names = ", ".join(p["name"] for p in outputs)
        prompt = [f"Process {name}({in_names}) -> ({out_names})", "", "FSF specification:"]
        for sc in scenarios:
            if sc["kind"] == "others":
                prompt.append(f"others => {sc['def']}")
            else:
                prompt.append(f"if ({sc['test']}) => {sc['def']}")

        repo = provenance.get("repo", "github")
        path = provenance.get("path", "unknown")
        task: dict[str, Any] = {
            "taskId": f"GitHubHarvest.ASFL_{name}",
            "kind": "process",
            "name": name,
            "signature": {"inputs": inputs, "outputs": outputs},
            "fsfScenarios": scenarios,
            "ext": [],
            "promptSpec": "\n".join(prompt),
            "sourceFile": f"github://{repo}/{path}",
            "sourceBasename": path,
            "module": "GitHubASFL",
            "externalProvenance": {
                "source": "github_asfl_lite",
                "corpus": "github_harvest",
                "repo": repo,
                "path": path,
                "html_url": provenance.get("html_url"),
            },
            "realspec": {
                "source_type": "github_harvest",
                "provenance": provenance,
            },
        }
        try:
            task["referenceCode"] = generate_reference_code(task)
        except Exception:  # noqa: BLE001
            continue
        tasks.append(task)
    # uniquify taskIds within file
    seen: dict[str, int] = {}
    for t in tasks:
        base = t["taskId"]
        n = seen.get(base, 0)
        seen[base] = n + 1
        if n:
            t["taskId"] = f"{base}_{n}"
            t["name"] = f"{t['name']}_{n}"
    return tasks
