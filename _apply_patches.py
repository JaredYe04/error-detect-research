from pathlib import Path

ROOT = Path(r"d:/repos/error-detect-research")

run_all = (ROOT / "experiments" / "run_all.py").read_text(encoding="utf-8")
if "benchmark_path" not in run_all:
    run_all = run_all.replace(
        "    mutation_eval: bool = True,\n    seed: int = 42,\n",
        "    mutation_eval: bool = True,\n    seed: int = 42,\n    benchmark_path: Path | None = None,\n    task_subset_path: Path | None = None,\n",
    )
    run_all = run_all.replace(
        "    tasks = load_benchmark()\n    if task_limit:\n        tasks = tasks[:task_limit]\n",
        """    tasks = load_benchmark(benchmark_path, include_hard=False) if benchmark_path else load_benchmark()
    if task_subset_path:
        subset_raw = json.loads(task_subset_path.read_text(encoding=\"utf-8\"))
        if isinstance(subset_raw, list) and subset_raw and isinstance(subset_raw[0], dict):
            subset_ids = {t.get(\"taskId\") for t in subset_raw}
        elif isinstance(subset_raw, dict) and \"taskIds\" in subset_raw:
            subset_ids = set(subset_raw[\"taskIds\"])
        else:
            subset_ids = set(subset_raw)
        tasks = [t for t in tasks if t.get(\"taskId\") in subset_ids]
        order = {tid: i for i, tid in enumerate(subset_ids)}
        tasks.sort(key=lambda t: order.get(t.get(\"taskId\"), 10**9))
    if task_limit:
        tasks = tasks[:task_limit]\n""",
    )
    run_all = run_all.replace(
        '        "parallelism": parallelism,\n        "completed": len(done_keys),\n',
        '        "parallelism": parallelism,\n        "benchmark_path": str(benchmark_path) if benchmark_path else None,\n        "task_subset_path": str(task_subset_path) if task_subset_path else None,\n        "completed": len(done_keys),\n',
    )
    run_all = run_all.replace(
        '    parser.add_argument("--task-limit", type=int, default=None)\n',
        '    parser.add_argument("--task-limit", type=int, default=None)\n'
        '    parser.add_argument("--benchmark-path", type=Path, default=None, help="Benchmark JSON (default: benchmarks/tasks.json)")\n'
        '    parser.add_argument("--task-subset", type=Path, default=None, help="JSON list of taskIds or task objects for stratified runs")\n',
    )
    run_all = run_all.replace(
        "        task_limit=args.task_limit,\n        sensitivity=args.sensitivity,\n",
        "        task_limit=args.task_limit,\n        benchmark_path=args.benchmark_path,\n        task_subset_path=args.task_subset,\n        sensitivity=args.sensitivity,\n",
    )
    (ROOT / "experiments" / "run_all.py").write_text(run_all, encoding="utf-8")
    print("patched run_all.py")

runner = (ROOT / "src" / "pipeline" / "runner.py").read_text(encoding="utf-8")
if 'elif mode == "B3"' not in runner:
    insert = '''    elif mode == "B3":
        cfg.enable_formal = False
        cfg.enable_patterns = False
        cfg.enable_repair = True
        cfg.max_attempts = 3
        cfg.formal_max_cases = 8
        cfg.feedback_variant = "test_expected"
    elif mode == "B4":
        cfg.enable_formal = False
        cfg.enable_patterns = False
        cfg.enable_repair = True
        cfg.max_attempts = 3
        cfg.formal_max_cases = 8
        cfg.feedback_variant = "test_only"
    elif mode == "B5":
        cfg.enable_formal = False
        cfg.enable_patterns = False
        cfg.enable_repair = True
        cfg.max_attempts = 3
        cfg.formal_max_cases = 8
        cfg.feedback_variant = "test_only"
'''
    runner = runner.replace('    elif mode == "M":', insert + '    elif mode == "M":')
    runner = runner.replace(
        '            if cfg.mode == "B2":\n                formal_ok = test_result.passed\n',
        '            if cfg.mode in {"B2", "B3", "B4", "B5"}:\n                formal_ok = test_result.passed\n',
    )
    runner = runner.replace(
        '            if not cfg.enable_repair and cfg.mode != "B2":\n',
        '            if not cfg.enable_repair and cfg.mode not in {"B2", "B3", "B4", "B5"}:\n',
    )
    runner = runner.replace(
        '            if cfg.mode == "B2" and attempt >= cfg.max_attempts:\n',
        '            if cfg.mode in {"B2", "B3", "B4", "B5"} and attempt >= cfg.max_attempts:\n',
    )
    if "reflexion_memory" not in runner:
        runner = runner.replace(
            '        feedback: str | None = None\n        code = ""\n',
            '        feedback: str | None = None\n        reflexion_memory: list[str] = []\n        code = ""\n',
        )
        runner = runner.replace(
            '            if test_result.counterexamples:\n                feedback, last_feedback_json = build_repair_feedback(\n',
            '''            if cfg.mode == "B3" and test_result.counterexamples:
                feedback, last_feedback_json = build_repair_feedback(
                    task,
                    test_result.counterexamples,
                    variant=feedback_variant,
                    pattern_matches=last_patterns,
                )
                feedback = (
                    "Self-critique: identify logical errors in your previous implementation before revising.\\n"
                    + feedback
                )
                attempt_entry["semantic_feedback"] = last_feedback_json
            elif test_result.counterexamples:\n                feedback, last_feedback_json = build_repair_feedback(\n''',
        )
        runner = runner.replace(
            '            else:\n                feedback = "Implementation incorrect. Retry."\n                last_feedback_json = []\n            attempt_history.append(attempt_entry)\n',
            '''            else:
                feedback = "Implementation incorrect. Retry."
                last_feedback_json = []
            if cfg.mode == "B5" and feedback:
                reflexion_memory.append(feedback[:500])
                if len(reflexion_memory) > 1:
                    feedback = "Prior reflections:\\n" + "\\n".join(
                        f"- {m}" for m in reflexion_memory[:-1]
                    ) + "\\n\\n" + feedback
            attempt_history.append(attempt_entry)\n''',
        )
    runner = runner.replace(
        '        if cfg.mode == "B2":\n            formal_result = run_formal_check(code, task, max_cases=cfg.formal_max_cases)\n',
        '        if cfg.mode in {"B2", "B3", "B4", "B5"}:\n            formal_result = run_formal_check(code, task, max_cases=cfg.formal_max_cases)\n',
    )
    runner = runner.replace(
        '        if cfg.mode == "B2":\n            success = formal_result.passed\n',
        '        if cfg.mode in {"B2", "B3", "B4", "B5"}:\n            success = formal_result.passed\n',
    )
    (ROOT / "src" / "pipeline" / "runner.py").write_text(runner, encoding="utf-8")
    print("patched runner.py")

sel_path = ROOT / "scripts" / "select_stratified_subset.py"
if not sel_path.exists():
    sel_path.write_text((ROOT / "_patch_sel.py").read_text() if False else "", encoding="utf-8")
