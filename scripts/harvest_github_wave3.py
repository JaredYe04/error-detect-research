#!/usr/bin/env python3
"""Wave-3 GitHub live harvest for RealSpec expansion.

Requires auth (one of):
  - env GH_TOKEN / GITHUB_TOKEN  (classic PAT: public_repo or fine-grained Contents:Read)
  - `gh auth login` then this script uses `gh auth token`

Stages written under artifacts/github_harvest/<run>/:
  01_auth.json
  02_search_hits.jsonl
  03_downloaded/…
  04_classified.jsonl
  05_converted_tasks.json
  06_skipped.jsonl
  SUMMARY.md

Usage:
  python scripts/harvest_github_wave3.py --dry-run-auth
  python scripts/harvest_github_wave3.py --live --max-downloads 80
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.harvest.auth import resolve_github_auth
from src.harvest.github_api import GitHubClient
from src.harvest.queries import CODE_QUERIES, REPO_QUERIES
from src.harvest.to_fsf import classify_and_convert


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def dry_run_auth() -> int:
    status, _tok = resolve_github_auth()
    print(json.dumps({
        "ok": status.ok,
        "method": status.method,
        "login": status.login,
        "message": status.message,
        "token_redacted": True,
    }, indent=2))
    return 0 if status.ok else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run-auth", action="store_true", help="Only check auth; exit 0/2")
    ap.add_argument("--live", action="store_true", help="Run live GitHub search + download")
    ap.add_argument("--max-downloads", type=int, default=60)
    ap.add_argument("--per-query", type=int, default=15)
    ap.add_argument("--run-name", type=str, default=None)
    ap.add_argument(
        "--out-root",
        type=Path,
        default=ROOT / "artifacts" / "github_harvest",
    )
    args = ap.parse_args()

    if args.dry_run_auth and not args.live:
        return dry_run_auth()

    status, token = resolve_github_auth()
    if not status.ok or not token:
        print(status.message, file=sys.stderr)
        return 2

    run_name = args.run_name or f"wave3_{_now()}"
    run_dir = args.out_root / run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    dl_dir = run_dir / "03_downloaded"
    dl_dir.mkdir(exist_ok=True)

    _write_json(
        run_dir / "01_auth.json",
        {
            "ok": True,
            "method": status.method,
            "login": status.login,
            "message": status.message,
            "started_utc": _now(),
        },
    )

    client = GitHubClient(token)
    hits_path = run_dir / "02_search_hits.jsonl"
    classified_path = run_dir / "04_classified.jsonl"
    skipped_path = run_dir / "06_skipped.jsonl"

    # Clear previous partials for this run name
    for p in (hits_path, classified_path, skipped_path):
        if p.exists():
            p.unlink()

    seen_keys: set[str] = set()
    download_budget = args.max_downloads
    tasks: list[dict] = []
    n_hits = 0
    n_dl = 0
    n_converted = 0
    n_skipped = 0

    # Prefer gh search code when available; else REST
    for q in sorted(CODE_QUERIES, key=lambda x: x.get("priority", 9)):
        if download_budget <= 0:
            break
        qid = q["id"]
        query = q["query"]
        print(f"[search] {qid}: {query}")
        items: list[dict] = []
        gh_items = client.try_gh_search_code(query, limit=args.per_query)
        if gh_items:
            for it in gh_items:
                repo = (it.get("repository") or {}).get("nameWithOwner") or ""
                path = it.get("path") or ""
                items.append(
                    {
                        "repo": repo,
                        "path": path,
                        "html_url": it.get("url"),
                        "query_id": qid,
                        "via": "gh_search_code",
                    }
                )
        else:
            try:
                data = client.search_code(query, per_page=min(30, args.per_query))
            except Exception as exc:  # noqa: BLE001
                print(f"  REST search failed: {exc}")
                data = {"items": []}
            for it in data.get("items") or []:
                repo = (it.get("repository") or {}).get("full_name") or ""
                path = it.get("path") or ""
                items.append(
                    {
                        "repo": repo,
                        "path": path,
                        "html_url": it.get("html_url"),
                        "query_id": qid,
                        "via": "rest_search_code",
                    }
                )

        with hits_path.open("a", encoding="utf-8") as hf:
            for it in items:
                n_hits += 1
                hf.write(json.dumps(it, ensure_ascii=False) + "\n")

        for it in items:
            if download_budget <= 0:
                break
            repo, path = it["repo"], it["path"]
            if not repo or not path:
                continue
            key = f"{repo}::{path}"
            if key in seen_keys:
                continue
            seen_keys.add(key)
            try:
                text = client.get_raw_file(repo, path)
            except Exception as exc:  # noqa: BLE001
                with skipped_path.open("a", encoding="utf-8") as sf:
                    sf.write(json.dumps({"repo": repo, "path": path, "error": str(exc)}) + "\n")
                n_skipped += 1
                continue

            safe = key.replace("/", "_").replace("::", "__")
            (dl_dir / f"{safe[:180]}").write_text(text, encoding="utf-8", errors="replace")
            n_dl += 1
            download_budget -= 1

            rec, task, st = classify_and_convert(
                path=path,
                text=text,
                repo=repo,
                html_url=it.get("html_url") or "",
                query_id=qid,
            )
            with classified_path.open("a", encoding="utf-8") as cf:
                slim = {k: v for k, v in rec.items() if k != "payload"}
                slim["convert_status"] = {k: v for k, v in st.items() if k != "error" or True}
                if st.get("error"):
                    slim["convert_error"] = st.get("error")
                cf.write(json.dumps(slim, ensure_ascii=False) + "\n")

            if task is not None and st.get("ok"):
                tasks.append(task)
                n_converted += 1
                print(f"  + converted {task['taskId']} from {repo}/{path}")
            else:
                n_skipped += 1
                with skipped_path.open("a", encoding="utf-8") as sf:
                    sf.write(
                        json.dumps(
                            {
                                "repo": repo,
                                "path": path,
                                "kind": rec.get("kind"),
                                "status": st,
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )

    # Optional repo discovery log (no download storm)
    repo_hits = []
    for rq in REPO_QUERIES:
        try:
            data = client.search_repos(rq["query"], per_page=min(20, rq.get("limit", 10)))
            for it in data.get("items") or []:
                repo_hits.append(
                    {
                        "query_id": rq["id"],
                        "full_name": it.get("full_name"),
                        "html_url": it.get("html_url"),
                        "description": it.get("description"),
                        "stars": it.get("stargazers_count"),
                    }
                )
        except Exception as exc:  # noqa: BLE001
            repo_hits.append({"query_id": rq["id"], "error": str(exc)})
    _write_json(run_dir / "02b_repo_hits.json", repo_hits)

    out_tasks = run_dir / "05_converted_tasks.json"
    _write_json(out_tasks, tasks)

    # Also export to benchmarks/ for eval convenience
    bench = ROOT / "benchmarks" / "github_harvest_v1.json"
    bench.write_text(json.dumps(tasks, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    summary = {
        "run": run_name,
        "auth_method": status.method,
        "login": status.login,
        "n_hits": n_hits,
        "n_downloaded": n_dl,
        "n_converted_ok": n_converted,
        "n_skipped": n_skipped,
        "benchmark_path": str(bench.relative_to(ROOT)).replace("\\", "/"),
        "run_dir": str(run_dir.relative_to(ROOT)).replace("\\", "/"),
    }
    _write_json(run_dir / "SUMMARY.json", summary)
    (run_dir / "SUMMARY.md").write_text(
        "# GitHub Harvest Wave-3 Summary\n\n"
        + "\n".join(f"- **{k}:** `{v}`" for k, v in summary.items())
        + "\n\nNext:\n\n```powershell\n"
        + "python scripts/build_github_harvest_corpus.py --from-run "
        + run_name
        + "\n"
        + "python experiments/run_all.py --modes B1 B2 M_eq --repeats 1 `\n"
        + "  --benchmark-path benchmarks/github_harvest_v1.json `\n"
        + "  --run-name run_github_harvest_v1 --parallelism 4 --force-max-attempts 3 `\n"
        + "  --model ecnu-plus\n```\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    if n_converted == 0:
        print(
            "WARNING: 0 tasks converted. Check 06_skipped.jsonl / 04_classified.jsonl; "
            "many GitHub hits need schema-shaped decision tables. "
            "Repo hits are in 02b_repo_hits.json for manual follow-up.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
