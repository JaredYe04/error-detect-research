# Author Response — Experiment Push (E6-max / E11-max / E2 bootstrap)

**日期：** 2026-07-10  
**目标：** 补齐审稿人可能卡住的跨模型与预防统计证据。

---

## 本轮新跑实验

| 实验 | Run ID | 规模 | 并行 | 结果要点 |
|------|--------|------|------|----------|
| **E6 × ecnu-max** | `run_e6_ecnu_max_v1` | 120×3=360 | 14 | A/B/C ≈ 89.2/89.0/89.2%；C−A = **+0.03 pp**；仅 1/120 任务 C>A |
| **E11 × ecnu-max** | `run_e11_ecnu_max_v1` | 22×3=66 | 10 | B1/B2/M 全平：Conf **89.8%**，Strict **63.6%**（主模型上 M 曾落后至 81.9%） |
| **E2 bootstrap** | `e2_pdr_far_bootstrap.json` | B=5000 | — | ΔPDR(M−B2) 95% CI **[2.5, 5.0] pp**；ΔFAR **[−5.0, −2.5] pp**；**均不含 0** |

冒烟：`run_e6_ecnu_max_smoke`（2 任务）验证 `--model` 通路后全量启动。

工程：`experiments/run_sweep.py` 新增 `--model`，反馈 job 写入 `model` 字段。

---

## 对审稿关切的回答

### Q: 单模型？跨模型族？
- 主结果：`ecnu-plus`（Qwen 族）
- 复现：`ecnu-max`（DeepSeek 族，平台文档 DeepSeek-V4-Flash）
- **E16**（已有）：B1/B2/M 全 89.2%
- **新 E6-max**：机制增益在强模型上因天花板消失，而非反转
- **新 E11-max**：外部集上 M 差距闭合为平局
- 诚实结论：+7.7 pp 是 **有修复 headroom 的主端点** 证据；更强端点饱和时部署仍默认 B2

### Q: E2 +3.8 pp 是否噪声？
- 配对 bootstrap（mutant_id，$n{=}852$）CI 不含 0 → 预防差距稳健

### Q: 工业案例？
- 仍无 vendor submodule；E11 外部教材/IET 语料 + ecnu-max 复现是本轮能做的最大外部加强
- 真正工业 sprint 仍列 future work

---

## 文稿已更新位置

- `front/abstract.tex` — E6-max 饱和 + E2 bootstrap
- `ch07` — E6-max 表；E11-max 段；E16 与 E6 交叉解读；E2 CI
- `ch08` — “Two LLM endpoints” 替代 “Single LLM family”
- `ch09` — limitation 对齐
- 会议版 `main.tex` + `results_stub.tex`
- CSV：`e6_ecnu_max_summary.csv`, `e11_ecnu_max_summary.csv`, `e2_pdr_far_bootstrap.json`

---

## 估计档位变化

| 之前 | 之后（本轮实验后） |
|------|-------------------|
| Weak Accept 边缘 ~52–58% | **Weak Accept ~58–65%**（跨端点诚实饱和 + E2 CI 加分；工业案例仍缺） |

若再补：vendor 工业案例或 GPT/Claude 商业 API 上 E6 子集，可冲 Accept。
