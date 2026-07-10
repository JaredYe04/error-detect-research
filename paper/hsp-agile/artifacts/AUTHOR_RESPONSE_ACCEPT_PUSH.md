# Accept Push — n1n Multi-Model + Industrial SOFL

**日期：** 2026-07-10  
**目标：** 稳定 Accept（跨商业模型族 + 工业模式语料）

---

## 环境兼容

| 变量 | 用途 |
|------|------|
| `ECNU_API_KEY` / `ECNU_BASE_URL` | 校内网关 |
| `N1N_API_KEY` / `N1N_BASE_URL` | [n1n.ai](https://api.n1n.ai/pricing) 商业聚合 |

实现：`src/llm/providers.py` + 更新后的 `ECNUClient`（按 model id 自动路由）。  
`.env.example` 已同步。冒烟：`gpt-4o` / `claude-sonnet-4-6` / `deepseek-v3.2` OK；`gpt-5.6` 503 不可用。

---

## 新实验（全部高并发 + progress.json）

| Run | 模型 | 规模 | 并行 | 要点 |
|-----|------|------|------|------|
| `run_e6_n1n_gpt4o_s30` | gpt-4o | 29×3 | 12 | Δ(C−A)=**0.0**（饱和） |
| `run_e6_n1n_claude46_s30` | claude-sonnet-4-6 | 29×3 | 12 | Δ=**+1.0 pp** |
| `run_e6_n1n_deepseek_s30` | deepseek-v3.2 | 29×3 | 12 | Δ=**−3.9 pp**（结构化反馈可伤弱模型） |
| `run_e16_n1n_gpt4o_s30` | gpt-4o | 29×3 | 10 | B1=B2 **100%**, M **88.9%** |
| `run_industrial_gpt4o_v1` | gpt-4o | 31×3 | 12 | B2 **100%**, B1/M 95.5%, Strict 67.7% |
| `run_industrial_claude46_v1` | claude-sonnet-4-6 | 31×3 | 10 | 同上模式 |
| `run_industrial_deepseek_v1` | deepseek-v3.2 | 31×3 | 12 | 见聚合 CSV |

工业语料：`benchmarks/industrial_sofl.json`（**31** 任务，Z3 全通过）。

---

## 对 Accept 的论证增量

1. **多模型族**：OpenAI + Anthropic + DeepSeek（商业）+ 校内 Qwen/DeepSeek  
2. **机制边界诚实**：+7.7 非普适；Claude +1.0；饱和/回归均披露  
3. **工业模式语料**：B2 100% Conf → 部署表最强外部证据  
4. **E2 bootstrap CI 不含 0**（此前已完成）

仍非“生产 vendor 日志”，但已远超纯合成 hard set。

---

## 复现

```powershell
python paper/hsp-agile/scripts/aggregate_n1n_campaigns.py
python scripts/poll_n1n_campaigns.py   # 进度
```

估计档位：**Accept 边缘 ~68–75%**（诚实跨模型 + 工业语料；若审稿人硬要真实企业 SOFL 源码仍可能卡）。
