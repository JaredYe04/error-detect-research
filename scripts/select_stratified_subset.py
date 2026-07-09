import json, random, argparse, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.benchmarks.complexity import annotate_tasks_complexity
DEFAULT_IN = ROOT / "benchmarks" / "hard_tasks_annotated.json"
DEFAULT_OUT = ROOT / "benchmarks" / "e12_stratified_30.json"

def difficulty(task):
    gc = task.get("complexity", {}).get("guard_complexity", "Simple")
    if gc in ("Simple", "AND"):
        return "easy"
    if gc == "Nested":
        return "medium"
    return "hard"

def select_stratified(tasks, n=30, seed=42):
    tasks = [t for t in tasks if t.get("complexity")]
    strata = {}
    for t in tasks:
        tier = t.get("complexity", {}).get("overlap_density_tier") or "medium"
        strata.setdefault((difficulty(t), tier), []).append(t)
    rng = random.Random(seed)
    for bucket in strata.values():
        rng.shuffle(bucket)
    keys = sorted(strata)
    per = max(1, n // max(len(keys), 1))
    selected = []
    for key in keys:
        selected.extend(strata[key][:per])
    if len(selected) < n:
        pool = [t for t in tasks if t not in selected]
        rng.shuffle(pool)
        selected.extend(pool[: n - len(selected)])
    return selected[:n]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, default=DEFAULT_IN)
    p.add_argument("--output", type=Path, default=DEFAULT_OUT)
    p.add_argument("--n", type=int, default=30)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    if not args.input.exists():
        raise FileNotFoundError(args.input)
    tasks = json.loads(args.input.read_text(encoding="utf-8"))
    if not tasks[0].get("complexity"):
        tasks = annotate_tasks_complexity(tasks)
    picked = select_stratified(tasks, n=args.n, seed=args.seed)
    args.output.write_text(json.dumps(picked, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(picked)} tasks -> {args.output}")

if __name__ == "__main__":
    main()
