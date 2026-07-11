# 独立审稿报告（盲审视角）

> 生成依据：仅阅读 `paper/hsp-agile-conference/main.tex` 及其 `\input` 引用的表格文件，以及
> `AUTHORITATIVE_NUMBERS.md` 中的数字核对。未参考任何 ACCEPT 清单、历史审稿报告或写作计划文档。

---

## 一、论文概述

论文题目：*Witness-Guided Repair and Dual-Gate Checks for LLM-Generated Guard Specifications*

该工作在 SOFL/FSF 有序卫式规范框架下提出三个贡献：
1. **PEWG**（Priority-Encoded Witness Generation）：用 Z3 为每个场景 $s_i$ 生成满足 $\Phi_i = \hat{g}_i \land \bigwedge_{j<i}\neg\hat{g}_j$ 的证人输入，覆盖 others 残差区域；
2. **SIFR**（Scenario-Indexed Feedback Rendering）：将场景标识、证人输入、期望/实际输出打包成结构化 JSON 作为 LLM 修复反馈；
3. **DGA**（Dual-Gate Acceptance）：$\mathrm{Accept} \Leftrightarrow \mathrm{Conf}=1 \land \mathrm{Screen}=\mathit{pass}$，用 PDR/FAR 评估防漏效果。

主要实验：E6（反馈消融）、E2（变异体防漏）、外部语料传递性。
核心评估基准：BENCH-120（合成 FSF，Z3 重叠过滤，120 个任务）；工业变异体集合（n=132 + n=720 HardSynthetic，共 n=852）。

---

## 二、数字一致性核查

逐项核对论文引用数字与表格/AUTHORITATIVE_NUMBERS.md 中的来源数据：

| 论文陈述 | 来源数据 | 一致？ |
|---------|---------|--------|
| E6 all-task C−A: +7.7 pp, CI [2.3, 13.6], W/L/T 14/4/102, Wilcoxon p=0.018 | `e6_headroom_summary.tex` 第一行；AUTHORITATIVE_NUMBERS §E6 | ✓ |
| headroom subset n=114, +8.2 pp, CI [2.3, 14.4] | `e6_headroom_summary.tex` 第二行 | ✓ |
| Conf=0 rescue n=13, +90.7 pp, 13/0/0 | `e6_headroom_summary.tex` 第三行 | ✓ |
| partial band n=101, −2.5 pp, CI [−5.8, 0.2] | `e6_headroom_summary.tex` 第四行 | ✓ |
| decisive 14/18, Wilson CI [54.8, 91.0]% | `e6_headroom_summary.tex` 第五行 | ✓ |
| Industrial FAR: B2 56.8% → M 32.6% (n=132), CI [−31.8, −17.4] pp | `e2_decomp_availability.tex`；AUTHORITATIVE_NUMBERS §E2 | ✓ |
| HardSynthetic n=720, PDR 100%, FAR 0% | `e2_decomp_availability.tex` | ✓ |
| pooled n=852: B2 FAR 8.8% → M 5.0% | `e2_decomp_availability.tex` | ✓ |
| wrong_relop external: n=79, +20.6 pp, CI [12.7, 28.6] | `e6_ext_multi_status.tex` 第三行；AUTHORITATIVE_NUMBERS §v2 | ✓ |
| HKCA09 gemini: n=17, +18.8 pp, CI [3.9, 37.5] | `e6_ext_multi_status.tex` 第五行 | ✓ |
| GitHub Screen: FAR 60.4% → 11.5% (94 B2-accept/M-reject cases) | AUTHORITATIVE_NUMBERS §External prevention | ✓（论文正文写"94 B2-accept/M-reject cases"，card 写"Screen-hits 94"，一致）|
| Gemini combo n=80: FULL vs test_only +26.5 pp, CI [21.0, 32.2] | `e6_ext_multi_status.tex`；AUTHORITATIVE_NUMBERS §Hard combo | ✓ |
| Field ablation: FULL − ir_nl_only +28.0 pp; single-field drops CI include 0 | Table `tab:field-conf`（内嵌） | ✓（ir_nl_only：+28.0 pp，excl 0；ir_no_scenario_id：−0.9 pp，incl 0；ir_no_expected：+5.0 pp，incl 0）|
| E1 M 100.0% / B2 98.3% / B1 84.2% | AUTHORITATIVE_NUMBERS §E1 authoritative | ✓ |
| M_eq +2.5 pp (3/0/117) | AUTHORITATIVE_NUMBERS §E1 equal-K | ✓ |
| E14: semantic_ir 75.1% vs execution_trace_matched 85.4% | AUTHORITATIVE_NUMBERS §E14 | ✓ |
| HTE tree precision 0.167, recall 0.786 | 论文正文，无对应表格来源（文内直接陈述） | 无法从公开表格独立核对 |

**总体数字一致性：良好。**论文与支撑材料之间无明显矛盾。others-witness 测量修正已在论文中主动披露（§A1 最后一段），且历史数据被标记为不再引用。HTE 精确率/召回率缺乏可查的独立数据文件，但论文已将其定位为"清单策略，非预测器"，该数字的核对优先级低。

---

## 三、评审意见

### 3.1 优点

**优点一：测量诚信度高，实验条件控制清晰。**
论文主动披露了 others-witness 生成 bug（历史版本因未取反高优先级卫式导致 Conf. 虚高约 5% Strict），并以修正后的 fixed-oracle 结果作为一次性数据。master protocol 表明确区分了 $K$、反馈渲染器、门控、语料库之间的边界，避免跨条件混淆数字。32 个 B2 接受/M 拒绝的工业变异体均经过 Conf.=1 二次验证（仅 Screen 门生效），因果归因链路清晰。这种在会议论文中主动报告测量修正的做法值得肯定。

**优点二：主动报告四条失败边界，避免过度拉伸结论。**
论文在 §4 及 Table `tab:deploy` 中明确报告：(1) partial-failure band（0 < Conf < 1，n=101）SIFR 反而 −2.5 pp；(2) GPT-4o/Claude 在工业任务上 B2 已经 Accept=1，escalate 到 M 反降至 95.5%；(3) E14 显示 execution_trace_matched（85.4%）优于 semantic_ir（75.1%），SIFR 并非最优结构化渠道；(4) HTE 精度仅 0.167。这些负面结果的主动披露使论文整体可信度高于同类工具类论文的平均水平。

**优点三：证人生成的形式化设计有清晰的接口语义。**
$\Phi_i = \hat{g}_i \land \bigwedge_{j<i}\neg\hat{g}_j$ 的 first-match 编码在形式上正确，others 证人通过 $\bigwedge_i\neg\hat{g}_i$ 显式构造。这一接口设计在关联 LLM 修复与 SMT 规范验证方面有明确的形式化根据，与 CEGIS/counterexample-guided 修复传统能够建立清晰对比（相关工作 §2 做了合理的差异化）。

---

### 3.2 主要弱点与风险

**弱点一：主要实证基础高度集中于合成语料，工业规模不足。**

E6 的核心机制证据来自 BENCH-120——一个合成、经 Z3 重叠过滤、仅涵盖 integer/boolean 片段的 120 任务集合。实际决定性差异集中在 13 个 Conf=0 任务（全任务的 10.8%）。工业 FAR 证据来自 n=132 个工业变异体，衍生自 n=31 个实践者风格任务；变异体由作者根据 SOFL 故障模式选定——与 Screen 的 14 个 AST 模式来自同一故障分类体系。外部语料（GitHub n=48、HKCA09 n=35）均为重建/爬取，而非生产环境的 `.asfl` dump；去标识化已发表工业案例（n=28）三种模式全部达到 100%，不能提供有效区分度。Screen 在 HKCA09 上 FAR 几乎不变（50.0% → 48.6%），在已发表工业语料上 FAR 完全不变（0 个 Screen 命中），表明 Screen 的防漏效果可能与特定 SOFL 故障模式高度相关，而非跨语料的通用改进。

对于 CCF-B 级 SE 实证论文，这一规模和多样性难以令 PC 信服该方法在真实工业场景中的部署价值。

**弱点二：实验体系复杂，核心贡献的因果链路对一般读者不透明。**

论文同时维护 E1/E2/E6/E10/E12/E14 六个主要实验，B1/B2/A2/B6/M\_eq/M 六种模式，以及 BENCH-120/工业/GitHub/HKCA09/去标识化 等五个语料。abstract 中密集列举约 12 个独立量化声明，包含至少 6 个括号内 CI 范围。master protocol 表虽然提供了映射，但实际阅读体验下，一个不熟悉 SOFL 生态的 PC 成员需要大量努力才能追踪"E6 primary endpoint 是 n=114 headroom subset，而非 14/120 wins"这一核心逻辑转换。此外，论文承认 E14 表明执行轨迹反馈优于 SIFR，而 M 模式同时绑定了 $K=5$、advisory gate、execution\_trace\_matched 等多个因子——这使 E6 与 M 之间的贡献归因存在模糊性（E6 隔离了反馈内容，但 M 的最终性能并不单独依赖 semantic\_ir）。

**弱点三：Static Screen 的有效性边界未经独立验证，循环风险明显。**

14 条 AST 级别安全模式（inverted priority、missing preemption、unconditional success 等）直接来源于 SOFL 故障预防模式，而 E2 的变异算子（DRO、MBO、WRO 等）也建模于"递归式卫式生成错误"。Screen 之所以在工业-132 上命中率高（32/132 命中，即 24.2%），而在 HKCA09（2 命中）和已发表工业（0 命中）上近乎失效，有理由怀疑测试集与模式集之间存在构造意义上的循环。Screen 的 false positive 表格（Table `tab:screen-fp`）显示 120/120 参考实现均触发 advisory 匹配，但 0/120 触发 high/critical 拒绝——该数字实际上揭示了 screen 在实践中将几乎所有代码标为 advisory，这是一个严重的精度问题（advisory 匹配的 precision 未报告），削弱了 Screen 作为"有效第二门"的声明。

---

## 四、各投稿目标场馆评估

### 4.1 CCF-B 软件工程研究轨道（ICSME / SANER 风格）

**概率分布（须合计 100%）：**

| 评审结论 | 概率 |
|---------|------|
| Accept | 8% |
| Weak Accept | 18% |
| Borderline | 28% |
| Weak Reject | 28% |
| Reject | 18% |

**P(Accept+) = P(Accept) + P(Weak Accept) ≈ 26%**

**评估理由：**
ICSME/SANER 的实证 SE 论文通常要求工业规模的验证、或显著的工具可用性、或对核心 SE 从业者的直接影响。BENCH-120 的合成性质、13 任务的核心机制证据、以及对 SOFL/FSF 专属生态的依赖，使该论文对非 SOFL 社区的推广价值有限。论文写作诚实、方法论有理论根据，但 PC 成员面对这一规模的实验体量（120 合成任务，132 工业变异体），加上复杂的多实验结构，大概率会给出 borderline 或 weak reject 评分。Screen 循环构造的隐患若被挑剔的审稿人识别，则可能滑入 reject。接受的关键障碍：生态依赖（SOFL/FSF）+ 合成语料 + Screen 评估的循环性。

---

### 4.2 ICFEM（CCF-C，形式化工程 / 形式化方法）

**概率分布（须合计 100%）：**

| 评审结论 | 概率 |
|---------|------|
| Accept | 20% |
| Weak Accept | 30% |
| Borderline | 28% |
| Weak Reject | 15% |
| Reject | 7% |

**P(Accept+) = P(Accept) + P(Weak Accept) ≈ 50%**

**评估理由：**
ICFEM 以形式化工程方法为核心，SOFL/FSF、Z3 证人生成、以及有序卫式规范的形式化处理均在该社区的核心兴趣范围内。$\Phi_i$ 的 first-match 编码与 dual-gate acceptance predicate 的有界操作语义定位（"非定理证明，非完备性断言"）符合 ICFEM 论文的形式化诚信标准。工业案例（railway/ATM/banking SOFL 重建）与 ICFEM 历史受众相吻合。然而，实验规模仍然有限；ICFEM 审稿人可能对 SMT 可扩展性（论文引用了 ~29–31 ms 的见证生成延迟，仅限 LIA 片段）和 Screen 模式完备性有疑问。主要风险：Screen 未做完备性论证，工业验证规模偏小。若作者能在 camera-ready 或修订中补充更大规模的 SOFL 工业案例或 real `.asfl` dump，接受概率可显著提高。

---

## 五、给作者的建议

论文的形式化设计和测量诚信值得肯定，但以下三点是修订的优先方向：第一，应在 Screen 评估中独立报告 14 条模式对变异算子的覆盖矩阵，明确哪些 Screen 命中来自非 SOFL 故障模式家族的变异体，以消除循环构造的疑虑；第二，E6 的叙述应在摘要和引言中将"13 任务 Conf=0 rescue"与"all-task +7.7 pp aggregate"在位置上反转——先介绍后者作为支持性聚合，再深入机制解释，避免读者误以为论文的整体贡献依赖于 13 个极端任务；第三，若 vendor NDA pilot 可在投稿前获得哪怕 n≥20 的真实 `.asfl` 任务上的 DGA 运行结果，将显著强化工业相关性声明，否则论文应在引言中主动缩减对"工业部署"的定语范围，改为"SOFL/FSF 规范合成环境"。

---

*报告生成时间：2026-07-12（UTC+8）*
*审稿人注：本报告仅依据论文文本和数字支撑文件形成判断，未参考任何历史版本审稿报告、写作目标文档或接受策略文件。*
