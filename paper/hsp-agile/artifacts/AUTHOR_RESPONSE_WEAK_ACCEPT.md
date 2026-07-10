# Author Response — Weak Accept Push (P0–P2)

**目标：** 将 CCF-B / 会议审稿从 Borderline 推到 Weak Accept。  
**范围：** 本轮文稿与数据一致性抛光（P1/P2）；**未**新跑多模型族 LLM；工业案例仍属 future work。  
**日期：** 2026-07-10

---

## 审稿意见 → 本轮处理映射

| 主题 | 审稿关切 | 本轮如何回应 | 证据位置 |
|------|----------|--------------|----------|
| **Number audit** | 主表 / 消融 / E2 数字与 CSV 不一致；旧 −6.3 / +0.5 / A2 near-Pareto | 以 `summary_by_mode.csv` 为 E1 真源；消融 Conf Δ：A2 −6.0、A3 −3.9、A1 −0.8（\|\Δ\|：A2 > A3 > A1）；同步 `sections/05_results.tex` 与 `CONFERENCE_10PAGE_OUTLINE.md`；E2 表明确为 impl-screening $n{=}852$（非 pooled $n{=}1704$） | `ch07`；`sections/05_results.tex`；`data/processed/summary_by_mode.csv`；`prevention_summary.json` |
| **E2 统计披露** | PDR/FAR 95.0/5.0 vs 91.2/8.8 是否过度推断 | 报告描述性差值（+3.8 pp PDR，−3.8 pp FAR）；诚实声明未预注册配对检验；`prevention_summary` 无 M–B2 bootstrap CI；推断留给 future work | `ch07` Table `tab:prevention` 后段落 |
| **E6 / E14 scope** | B4≈B2 是否削弱 E6；长度混淆 | C2 主证据仍为 E6（typed IR vs test-only +7.7 pp）；E14 长度匹配（`execution_trace_matched`）界定“结构 vs 长度”；不把 E14 写成替代 E6 的主 claim | `run_feedback_v2`；`run_e14_sweep_v1`；`AUTHOR_RESPONSE.md` Q6 |
| **Deployment framing** | 不以 “M 全面优于 B2” 为 headline | 部署边界表：B2 = 默认 mean Conf/延迟；M = Accept / PDR–FAR / typed repair 场景；E10/E12 支持非全域优势 | `ch08` `tab:deployment-boundary`；E10/E12 |
| **Hybrid B6 / M_lite** | 相关工作 VerifierLoop；能否用轻量混合替代 M | B6 全量对齐（`run_b6_full_v2`）；E18：M_lite 不优于 B6/B2——混合非捷径；完整 M 仅在 IR+gate 一体时部署 | `ch07` E18；`ch08` deployment / B6 段 |
| **Conference cut** | 10 页装不下全量实验 | `paper/hsp-agile-conference/` + `CONFERENCE_10PAGE_OUTLINE.md`：保留 C1–C3、E6→部署→E2；消融数字已与 canonical 对齐；A2 不再写成 near-Pareto | outline §3/§8；conference stubs |
| **Reproducibility** | 审稿人无法复现主表 | Appendix A 新增 “Reproducing canonical tables”：prepare / plot / `build.ps1` / tectonic；列出 canonical run IDs | `appendices/app_a_reproducibility.tex` |

---

## P0–P2 完成度（相对修订计划）

| 优先级 | 项 | 状态 | 备注 |
|--------|----|------|------|
| **P0** | 数字一致性 + 叙事（E6/部署边界居前，非 E1 全域胜出） | Done（本轮加固） | E1 真源 CSV；legacy `05_results` 消融已修 |
| **P0** | E12 / E10 边界证据 | Done（既有） | 不以 M>B2 为 publishable core |
| **P1** | E14 长度匹配、B6 对齐、E17 advisory、M_lite | Done（既有实验 + 文稿） | 本轮未重跑 |
| **P1** | E2 统计诚实披露 | Done（本轮） | 无虚构 p-value |
| **P2** | 会议版裁剪 / outline 数字同步 | Done（本轮部分） | −6.3 / +0.5 / A2 Pareto 已清 |
| **P2** | 工业试点 / vendor E11 扩展 | **未做** | 仍属 future work |
| **P2** | 新增多模型族 LLM 全量 | **未做** | E16 仍为既有 `ecnu-max` 试点；本轮无新 multi-family run |

---

## 仍保留的 Limitations（主动披露）

1. **无本轮新 multi-family LLM run** — 主结果仍以单一主模型管线 + 既有 E16 试点为界。  
2. **工业 / 真实项目案例** — 仍为 future work；外部泛化依赖 E8/E10/E11 等已有证据。  
3. **E2 PDR/FAR** — 仅描述性差值；无预注册推断检验。  
4. **合成 hard benchmark** — overlap 过滤偏向 SMT 友好任务；部署表与 E10 随机样本用于界定适用范围。

---

## Canonical run IDs（与附录一致）

| Run ID | 角色 |
|--------|------|
| `run_e1_canonical_v1` | E1 主表、消融、E3 |
| `run_e12_canonical_v1` | 多种子稳定性 |
| `run_feedback_v2` | E6 feedback variants |
| `run_e14_sweep_v1` | E14 长度匹配 |
| `run_b6_full_v2` | B6 VerifierLoop-FSF |

刷新：`python paper/hsp-agile/scripts/refresh_paper_assets.py --run-dir artifacts/run_e1_canonical_v1`  
或：`powershell -File paper/hsp-agile/scripts/build.ps1 -Clean`

---

## 一句话给审稿人

本轮将消融与 E2 披露与 processed 真源对齐，明确部署边界与 E6/E14/B6 证据范围，并补强附录复现命令；**不**声称新的多模型或工业验证——这些仍诚实列为 limitations。
