#!/usr/bin/env python3
"""Targeted harvest from known high-value SOFL / formal-spec GitHub repos.

Complements broad code search (often noisy) by walking recursive trees of
curated repositories and converting convertible artefacts.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.harvest.auth import require_auth
from src.harvest.github_api import GitHubClient
from src.harvest.to_fsf import classify_and_convert
from src.benchmarks.complexity import annotate_tasks_complexity
from src.benchmarks.reference_gen import generate_reference_code
from src.asfl_bridge import extract_spec

TARGET_REPOS = [
    {
        "full_name": "HKCA09/SOFL-Maintainability-Experiment-Dataset",
        "notes": "SOFL maintainability experiment dataset",
    },
    {
        "full_name": "ICARUSxyz/FCoTFL",
        "notes": "FCoTFL with SOFL formal specs",
    },
    {
        "full_name": "JaredYe04/agile-sofl-toolchain",
        "notes": "Agile-SOFL toolchain examples (.asfl)",
    },
]

INTERESTING_SUFFIXES = (
    ".asfl",
    ".sofl",
    ".json",
    ".yml",
    ".yaml",
    ".dmn",
    ".md",
    ".txt",
    ".fsf",
)


def list_blobs(client: GitHubClient, full_name: str) -> list[str]:
    data = client.get_json(f"/repos/{full_name}/git/trees/HEAD", {"recursive": "1"})
    out = []
    for t in data.get("tree") or []:
        if t.get("type") != "blob":
            continue
        path = t.get("path") or ""
        low = path.lower()
        if any(low.endswith(sfx) for sfx in INTERESTING_SUFFIXES):
            # skip huge / binary-ish
            if t.get("size", 0) and int(t["size"]) > 400_000:
                continue
            out.append(path)
    return out


def try_asfl_tasks(text: str, *, repo: str, path: str, tmp: Path) -> list[dict]:
    """Write temp .asfl and parse via node bridge if available."""
    if not path.lower().endswith((".asfl", ".sofl")):
        return []
    tmp.mkdir(parents=True, exist_ok=True)
    f = tmp / Path(path).name
    f.write_text(text, encoding="utf-8")
    try:
        data = extract_spec(f, tasks=True)
    except Exception as exc:  # noqa: BLE001
        return []
    if not data.get("ok"):
        return []
    tasks = []
    for i, task in enumerate(data.get("tasks") or []):
        task = dict(task)
        task.setdefault("taskId", f"GitHubHarvest.ASFL_{repo.replace('/', '_')}_{i}")
        task["sourceFile"] = f"github://{repo}/{path}"
        task["externalProvenance"] = {
            "source": "github_targeted",
            "corpus": "github_harvest",
            "repo": repo,
            "path": path,
        }
        task["realspec"] = {"source_type": "github_harvest", "provenance": {"repo": repo, "path": path}}
        if "referenceCode" not in task and task.get("fsfScenarios"):
            try:
                task["referenceCode"] = generate_reference_code(task)
            except Exception:  # noqa: BLE001
                continue
        tasks.append(task)
    return tasks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-files-per-repo", type=int, default=80)
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "benchmarks" / "github_harvest_v1.json",
    )
    ap.add_argument(
        "--run-dir",
        type=Path,
        default=ROOT / "artifacts" / "github_harvest" / "wave3_targeted_v1",
    )
    ap.add_argument("--extra-repo", action="append", default=[], help="owner/name")
    args = ap.parse_args()

    status, token = require_auth()
    client = GitHubClient(token)
    args.run_dir.mkdir(parents=True, exist_ok=True)
    dl = args.run_dir / "downloaded"
    dl.mkdir(exist_ok=True)

    repos = list(TARGET_REPOS)
    for r in args.extra_repo:
        repos.append({"full_name": r, "notes": "extra"})

    all_tasks: list[dict] = []
    log = []

    for repo_meta in repos:
        full = repo_meta["full_name"]
        print(f"[repo] {full}")
        try:
            blobs = list_blobs(client, full)
        except Exception as exc:  # noqa: BLE001
            print(f"  tree failed: {exc}")
            log.append({"repo": full, "error": str(exc)})
            continue
        # Prefer asfl/sofl/json with decision-ish names
        def score(p: str) -> int:
            low = p.lower()
            s = 0
            if low.endswith((".asfl", ".sofl")):
                s += 100
            if any(k in low for k in ("decision", "fsf", "scenario", "spec", "example", "process")):
                s += 20
            if low.endswith((".json", ".yml", ".yaml")):
                s += 5
            if "readme" in low:
                s -= 50
            return -s

        blobs = sorted(blobs, key=score)[: args.max_files_per_repo]
        print(f"  candidates={len(blobs)}")
        for path in blobs:
            try:
                text = client.get_raw_file(full, path)
            except Exception as exc:  # noqa: BLE001
                log.append({"repo": full, "path": path, "error": str(exc)})
                continue
            safe = f"{full.replace('/', '_')}__{path.replace('/', '_')}"[:200]
            (dl / safe).write_text(text, encoding="utf-8", errors="replace")

            # ASFL bridge first
            asfl_tasks = try_asfl_tasks(text, repo=full, path=path, tmp=args.run_dir / "tmp_asfl")
            for t in asfl_tasks:
                from src.harvest.to_fsf import validate_task

                st = validate_task(t)
                if st.get("ok"):
                    all_tasks.append(t)
                    print(f"  + asfl {t['taskId']}")
                else:
                    log.append({"repo": full, "path": path, "asfl_status": st})

            rec, task, st = classify_and_convert(
                path=path, text=text, repo=full, query_id="targeted"
            )
            if task is not None and st.get("ok"):
                all_tasks.append(task)
                print(f"  + {task['taskId']} kind={rec.get('kind')}")
            else:
                log.append(
                    {
                        "repo": full,
                        "path": path,
                        "kind": rec.get("kind"),
                        "status": st,
                    }
                )

    # dedupe by taskId / promptSpec
    by_id = {}
    for t in all_tasks:
        by_id[t.get("taskId")] = t
    tasks = list(by_id.values())
    annotate_tasks_complexity(tasks)

    # merge with existing harvest if any
    if args.out.exists():
        try:
            prev = json.loads(args.out.read_text(encoding="utf-8"))
            for t in prev:
                by_id.setdefault(t.get("taskId"), t)
            tasks = list(by_id.values())
            annotate_tasks_complexity(tasks)
        except Exception:  # noqa: BLE001
            pass

    args.out.write_text(json.dumps(tasks, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (args.run_dir / "log.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
    (args.run_dir / "SUMMARY.json").write_text(
        json.dumps({"n_tasks": len(tasks), "repos": [r["full_name"] for r in repos]}, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {args.out} n={len(tasks)}")
    return 0 if tasks else 1


if __name__ == "__main__":
    raise SystemExit(main())
