import json
from pathlib import Path

runs = [
    ("E6-gpt4o", "artifacts/run_e6_n1n_gpt4o_s30/feedback_variants/progress.json"),
    ("E6-claude", "artifacts/run_e6_n1n_claude46_s30/feedback_variants/progress.json"),
    ("E6-ds", "artifacts/run_e6_n1n_deepseek_s30/feedback_variants/progress.json"),
    ("Ind-gpt4o", "artifacts/run_industrial_gpt4o_v1/progress.json"),
    ("Ind-claude", "artifacts/run_industrial_claude46_v1/progress.json"),
    ("E16-gpt4o", "artifacts/run_e16_n1n_gpt4o_s30/progress.json"),
]
for name, p in runs:
    path = Path(p)
    if not path.exists():
        print(name, "NO PROGRESS YET")
        continue
    d = json.loads(path.read_text(encoding="utf-8"))
    pct = d.get("percent", 0)
    last = str(d.get("last_message", ""))[:70]
    print(
        f"{name}: {d.get('completed')}/{d.get('total')} "
        f"({pct:.1f}%) eta={d.get('eta_sec')} status={d.get('status')} | {last}"
    )
