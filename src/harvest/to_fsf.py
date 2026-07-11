"""Convert classified harvest payloads into FSF TaskSpec dicts."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from src.benchmarks.reference_gen import generate_reference_code, validate_reference
from src.formal.fsf_eval import generate_concrete_cases
from src.harvest.classify import classify_candidate


def _slug(s: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_.-]+", "_", s)
    return s.strip("_")[:80] or "anon"


def _norm_guard(g: str) -> str:
    g = g.strip()
    # light sugar: == -> eq, etc. if authors used python ops
    repl = [
        (r"\s*>=\s*", " ge "),
        (r"\s*<=\s*", " le "),
        (r"\s*!=\s*", " ne "),
        (r"\s*==\s*", " eq "),
        (r"\s*>\s*", " gt "),
        (r"\s*<\s*", " lt "),
        (r"\band\b", "&&"),
        (r"\bor\b", "||"),
    ]
    out = g
    for pat, rep in repl:
        out = re.sub(pat, rep, out, flags=re.I)
    return out.strip()


def decision_table_to_task(table: dict[str, Any], *, provenance: dict[str, Any]) -> dict[str, Any]:
    name = _slug(str(table.get("name") or provenance.get("path") or "table"))
    rules = table.get("rules") or table.get("rows") or []
    scenarios: list[dict[str, Any]] = []
    for i, rule in enumerate(rules, start=1):
        if not isinstance(rule, dict):
            continue
        guard = rule.get("guard") or rule.get("when") or rule.get("if") or rule.get("test")
        post = rule.get("post") or rule.get("then") or rule.get("def") or rule.get("output")
        if not guard or not post:
            continue
        if isinstance(post, dict):
            post = " && ".join(f"{k} eq {v}" for k, v in post.items())
        scenarios.append(
            {
                "index": i,
                "kind": "scenario",
                "test": _norm_guard(str(guard)),
                "def": _norm_guard(str(post)) if " eq " in str(post) or "&&" in str(post) else str(post),
            }
        )
    if not scenarios:
        raise ValueError("no convertible rules")

    default = table.get("default") or table.get("others")
    if isinstance(default, dict):
        dpost = default.get("post") or default.get("def") or "result eq 0"
    elif isinstance(default, str):
        dpost = default
    else:
        outs = table.get("outputs") or [{"name": "result"}]
        dpost = " && ".join(f"{o['name'] if isinstance(o, dict) else o} eq 0" for o in outs)

    scenarios.append({"index": len(scenarios) + 1, "kind": "others", "test": "others", "def": dpost})

    inputs = table.get("inputs") or _infer_vars(scenarios, side="test")
    outputs = table.get("outputs") or _infer_vars(scenarios, side="def")
    inputs = [_as_param(x) for x in inputs]
    outputs = [_as_param(x) for x in outputs]

    task: dict[str, Any] = {
        "taskId": f"GitHubHarvest.{name}",
        "kind": "process",
        "name": name.lower(),
        "signature": {"inputs": inputs, "outputs": outputs},
        "fsfScenarios": scenarios,
        "ext": [],
        "promptSpec": _prompt(name, inputs, outputs, scenarios),
        "sourceFile": f"github://{provenance.get('repo')}/{provenance.get('path')}",
        "sourceBasename": provenance.get("path"),
        "externalProvenance": {
            "source": "github_harvest",
            "generator": "src.harvest.to_fsf",
            "corpus": "github_harvest",
            "repo": provenance.get("repo"),
            "path": provenance.get("path"),
            "html_url": provenance.get("html_url"),
            "query_id": provenance.get("query_id"),
        },
        "realspec": {
            "source_type": "github_harvest",
            "provenance": provenance,
        },
    }
    task["referenceCode"] = generate_reference_code(task)
    return task


def fsm_to_task(fsm: dict[str, Any], *, provenance: dict[str, Any]) -> dict[str, Any]:
    name = _slug(str(fsm.get("name") or provenance.get("path") or "fsm"))
    scenarios: list[dict[str, Any]] = []
    for i, tr in enumerate(fsm.get("transitions") or [], start=1):
        if not isinstance(tr, dict):
            continue
        guard = tr.get("guard") or "true"
        src = tr.get("from") or tr.get("source")
        post = tr.get("post") or f"state eq {tr.get('to') or tr.get('target')}"
        test = f"(state eq {src}) && ({_norm_guard(str(guard))})" if src is not None else _norm_guard(str(guard))
        scenarios.append({"index": i, "kind": "scenario", "test": test, "def": str(post)})
    if not scenarios:
        raise ValueError("no transitions")
    scenarios.append(
        {
            "index": len(scenarios) + 1,
            "kind": "others",
            "test": "others",
            "def": fsm.get("default_post", "state eq state"),
        }
    )
    sig = fsm.get("signature") or {
        "inputs": [{"name": "state", "type": "int"}, {"name": "event", "type": "int"}],
        "outputs": [{"name": "state", "type": "int"}],
    }
    task: dict[str, Any] = {
        "taskId": f"GitHubHarvest.FSM_{name}",
        "kind": "process",
        "name": f"fsm_{name.lower()}",
        "signature": sig,
        "fsfScenarios": scenarios,
        "ext": [],
        "promptSpec": _prompt(name, sig["inputs"], sig["outputs"], scenarios),
        "sourceFile": f"github://{provenance.get('repo')}/{provenance.get('path')}",
        "sourceBasename": provenance.get("path"),
        "externalProvenance": {
            "source": "github_harvest",
            "generator": "src.harvest.to_fsf.fsm",
            "corpus": "github_harvest",
            "repo": provenance.get("repo"),
            "path": provenance.get("path"),
            "html_url": provenance.get("html_url"),
            "query_id": provenance.get("query_id"),
        },
        "realspec": {"source_type": "github_harvest", "provenance": provenance},
    }
    task["referenceCode"] = generate_reference_code(task)
    return task


def _as_param(x: Any) -> dict[str, str]:
    if isinstance(x, dict) and "name" in x:
        return {"name": str(x["name"]), "type": str(x.get("type", "int"))}
    return {"name": str(x), "type": "int"}


def _infer_vars(scenarios: list[dict[str, Any]], *, side: str) -> list[dict[str, str]]:
    names: list[str] = []
    seen: set[str] = set()
    for sc in scenarios:
        text = sc.get("test" if side == "test" else "def", "")
        for tok in re.findall(r"\b[a-zA-Z_]\w*\b", text):
            if tok.lower() in {"others", "true", "false", "and", "or", "eq", "ne", "gt", "ge", "lt", "le"}:
                continue
            if tok not in seen and not tok.isdigit():
                # skip numeric literals mistaken — already non-digit
                seen.add(tok)
                names.append(tok)
    if side == "def" and not names:
        names = ["result"]
    if side == "test" and not names:
        names = ["x"]
    return [{"name": n, "type": "int"} for n in names]


def _prompt(name: str, inputs: list, outputs: list, scenarios: list) -> str:
    in_names = ", ".join(p["name"] if isinstance(p, dict) else str(p) for p in inputs)
    out_names = ", ".join(p["name"] if isinstance(p, dict) else str(p) for p in outputs)
    lines = [f"Process {name}({in_names}) -> ({out_names})", "", "FSF specification:"]
    for sc in scenarios:
        if sc.get("kind") == "others":
            lines.append(f"others => {sc['def']}")
        else:
            lines.append(f"if ({sc['test']}) => {sc['def']}")
    return "\n".join(lines)


def validate_task(task: dict[str, Any]) -> dict[str, Any]:
    scenarios = task.get("fsfScenarios", [])
    signature = task.get("signature", {})
    non_others = [s for s in scenarios if s.get("kind") != "others"]
    dom = task.get("smtDomain") or {}
    int_lo = dom.get("lo") if isinstance(dom, dict) else None
    int_hi = dom.get("hi") if isinstance(dom, dict) else None
    try:
        cases = generate_concrete_cases(
            scenarios,
            signature,
            max_cases=max(12, 3 * max(1, len(non_others))),
            int_lo=int(int_lo) if int_lo is not None else None,
            int_hi=int(int_hi) if int_hi is not None else None,
        )
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"witness: {exc}", "n_cases": 0}
    covered = {c.scenario_index for c in cases if getattr(c, "kind", None) != "others"}
    missing = [s["index"] for s in non_others if s["index"] not in covered]
    try:
        ref_ok = validate_reference(task, task["referenceCode"])
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"ref: {exc}", "n_cases": len(cases), "missing": missing}
    ok = bool(ref_ok) and not missing and len(cases) >= 1
    return {"ok": ok, "n_cases": len(cases), "missing": missing, "ref_ok": ref_ok}


def convert_classified(rec: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Try convert; return (task_or_none, status)."""
    kind = rec.get("kind")
    prov = {
        "repo": rec.get("repo"),
        "path": rec.get("path"),
        "html_url": rec.get("html_url"),
        "query_id": rec.get("query_id"),
    }
    try:
        if kind == "decision_table" and isinstance(rec.get("payload"), dict):
            task = decision_table_to_task(rec["payload"], provenance=prov)
        elif kind == "fsm" and isinstance(rec.get("payload"), dict):
            task = fsm_to_task(rec["payload"], provenance=prov)
        elif kind == "fsf_task" and isinstance(rec.get("payload"), dict):
            task = dict(rec["payload"])
            task.setdefault("externalProvenance", {})
            task["externalProvenance"].update(
                {"source": "github_harvest", "corpus": "github_harvest", **prov}
            )
            if "referenceCode" not in task:
                task["referenceCode"] = generate_reference_code(task)
        elif kind == "rule_list" and isinstance(rec.get("payload"), dict):
            task = decision_table_to_task(rec["payload"], provenance=prov)
        else:
            return None, {"ok": False, "skipped": True, "reason": f"no converter for kind={kind}"}
        status = validate_task(task)
        if not status.get("ok"):
            return None, status
        # stable id
        h = hashlib.sha256(
            (task.get("promptSpec") or "").encode("utf-8")
        ).hexdigest()[:10]
        task["taskId"] = f"GitHubHarvest.{_slug(task.get('name', 't'))}_{h}"
        return task, status
    except Exception as exc:  # noqa: BLE001
        return None, {"ok": False, "error": str(exc)}


def classify_and_convert(
    *,
    path: str,
    text: str,
    repo: str,
    html_url: str = "",
    query_id: str = "",
) -> tuple[dict[str, Any], dict[str, Any] | None, dict[str, Any]]:
    rec = classify_candidate(path=path, text=text, repo=repo)
    rec["html_url"] = html_url
    rec["query_id"] = query_id
    task, status = convert_classified(rec)
    return rec, task, status
