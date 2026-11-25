# 模型质量评分表 v2（GQM 框架）

**数据来源**：`scores_v2.json`（脚本 `score_models_v2.py` 可复现）
**执行日期**：2026-11-23
**基准**：44 条原子需求（`atomic_requirements_human.json`；双拆一致性 semantic Jaccard = 0.804）
**文献依据**：GQM [15]、SEQUAL [22]、需求质量属性 ISO 29148 [21]、Requirements Smells [24]、LLM-as-Judge [29]、自偏好偏差 [30]

> **方法声明**：跨符号体系的需求模型质量比较没有统一标准。本表的"原子需求清单 + 适配覆盖率"
> 是**本文自提的方法**，以 GQM [15] 与 SEQUAL [22] 为理论依据，不是对任何现成标准的执行。

---

## 1. 双拆一致性（原子需求清单构建）

| 指标 | 值 |
|---|---:|
| 人工拆分条数 | 44 |
| LLM 独立拆分条数 | 46 |
| 语义匹配条数 | 37 |
| **Semantic Jaccard（报告值）** | **0.804** |
| ID Jaccard（仅参考，两侧编号独立） | 0.915 |
| LLM 独有条目（未纳入共同基准） | 9 |

> LLM 拆分者类别命名不同（`ext/func/th` vs `external/function/threshold`），
> 语义匹配已按类别对齐。受作者人数限制，第二拆分者为 LLM 而非人类，这是局限。

---

## 2. 五核心指标（论文 Table II）

### Level 0（M1 / M3 / M4）

| 指标 | M1 人工 SOFL | M3 AI DFD | M4 AI UML |
|---|---:|---:|---:|
| M1 需求覆盖率 | **1.000** | **1.000** | **1.000** |
| ├ 安全相关覆盖 | **1.000** | **1.000** | **1.000** |
| M2 精确率 | **1.000** | **1.000** | **1.000** |
| M3 一致性 | **0.749** | 0.624 | 0.596 |
| M4 形式化精确度 | **0.914** | 0.871 | 0.957 |
| **四项均值** | **0.916** | 0.874 | 0.888 |

### Level 1（M1 / M3 / M4 / M5）

| 指标 | M1 人工 SOFL | M3 AI DFD | M4 AI UML | M5 AI 状态机 |
|---|---:|---:|---:|---:|
| M1 需求覆盖率 | 0.615 | **1.000** | **1.000** | 0.615 |
| ├ 安全相关覆盖 | 0.583 | **1.000** | **1.000** | 0.583 |
| M2 精确率 | **1.000** | **1.000** | **1.000** | **1.000** |
| M3 一致性 | 0.737 | 0.458 | 0.571 | **0.748** |
| M4 形式化精确度 | 0.800 | **1.000** | 0.600 | 0.771 |
| **四项均值** | 0.788 | **0.865** | 0.793 | 0.783 |

**关键发现**：M1 人工版在 Level 1 覆盖率只有 0.615——它**漏写了 5 条规范阈值**
（N-1 130 km/h、N-3 30 km/h 降速、N-4 CCRm/CCRb 场景、N-5 RSS 距离、N-6 RSS 制动轮廓）。
这是人工模型的真实缺陷，不是提取器偏差。AI 模型因提示词要求"阈值只用 §7/§8"，反而全部覆盖。

> **关于覆盖率打标**：初版自动脚本用 MES 文本匹配算覆盖率，M1 得 0.387 而 AI 得 0.968。
> 诊断发现 M1 的 MES 由工具产物提取、文本量只有 AI 版的 1/2～1/3，自动匹配系统性偏向文本详细者。
> 因此改为**逐条人工打标**（44 条 × 各模型，证据记录在 `coverage_manual.json`），上表为人工打标结果。

---

## 3. 缺陷注入实验（论文 Table III）

**设计**：每个模型植入 6 个缺陷（遗漏 / 矛盾 / 条件错误 / 流缺失 / 歧义），共 24 个；
隔离 LLM 评审者按固定 rubric 评审 3 轮，不知道植入了什么；人工逐条复核判真检出/误报。

| 模型 | 第1轮 | 第2轮 | 第3轮 | **均值检出率** | 三轮并集 | 方差 | 误报率 |
|---|---:|---:|---:|---:|---:|---:|---:|
| M1 人工 SOFL | 0.833 | 0.667 | 0.833 | **0.778** | 0.833 | 0.009 | **0.095** |
| M3 AI DFD | 0.667 | 0.500 | 0.667 | 0.611 | 0.667 | 0.009 | 0.218 |
| M4 AI UML | 0.500 | 0.500 | 0.833 | 0.611 | 0.833 | 0.037 | 0.167 |
| M5 AI 状态机 | 0.667 | 0.667 | 0.500 | 0.611 | 0.667 | 0.009 | **0.476** |
| **总体** | | | | **0.653** | | | 0.260 |

**Cohen's κ = 0.389**（pooled：TP=47, FN=25, FP=19, TN=53）——按 Landis & Koch [31] 属
"fair agreement"，说明 LLM 评审与人工真值只是中等一致，**不能替代人工核验**。

### 解读（不预设结论）

1. **M1 人工 SOFL 的缺陷最容易被检出**（0.778），且误报率最低（0.095）。
   可能原因：形式化契约把矛盾/条件错误显式化（`2.0 vs A-1 的 6.0`、`>=` 变 `==` 都很容易对照规格发现）。
2. **M5 状态机误报率最高**（0.476）——评审者把合法的合成状态
   （FaultDegraded / Deactivated）当成"臆造元素"，反映 LLM 对"哪些元素算幻觉"判断不稳定。
3. **方差都很小**（≤0.037），三轮评审结果稳定；但 M4 方差相对最大（0.037）。
4. 这些是**观察结果，不是证明**——样本是单次植入的 6 缺陷 × 4 模型，外推需谨慎。

---

## 4. 与 v1 评分的关系

| v1 维度 | v2 对应 | 变化 |
|---|---|---|
| D1 结构完整性 | M1 覆盖率 | 从"元素计数"改为"原子需求逐条打标" |
| D2 接口一致性 | M3 一致性 | 保留算法，扩展为含工具语法 |
| D3 语义正确性 | 并入 M2/M3 | 不再单列（阈值已由覆盖率承载） |
| D4 形式化强度 | M4 形式化精确度 | 加歧义词占比（依据 Requirements Smells [24]） |
| D5 可追溯性 | 并入 M3 | 作为一致性的一部分 |
| D6 幻觉率 | M2 精确率 | 反向计分改为正向 |
| — | **M5 缺陷检出率** | **全新，补上"AI 反馈评估"这一作业要求** |

v1 的 `<>null` 提示词对照（57/37 → 0）仍作为独立发现保留，不属于五指标。

---

## 5. 局限性（论文必须写）

1. **结构代理 ≠ 语义正确**：五指标测的是"需求是否被表达、接口是否对得上"，
   不证明需求语义正确。M1 覆盖率 1.000 但实际漏了 5 条阈值——因为 L0 打标不含阈值类需求。
2. **覆盖率按层级分别打标**：L0 只判整车级需求（31 条），L1 只判 AEB+阈值+范围（13 条），
   因此 M1-L0=1.000 与 M1-L1=0.615 不可直接比较，M5 也没有 L0 分数。
3. **第二拆分者是 LLM 不是人**，Jaccard 0.804 是"人-LLM 一致性"而非"人-人一致性"。
4. **缺陷注入是单次设计**：每模型 6 个缺陷，未覆盖所有缺陷类型组合；检出率是点估计。
5. **κ 为 pooled 简化口径**，未区分模型/轮次的分层效应。
6. **评审者可能对 SOFL 小众语言不熟**——这本身是影响因素分析的素材（M1 低误报率可能部分源于此）。

---

## 6. 论文可直接用的英文结论

> Using a 44-item atomic requirements baseline derived independently by a human and an LLM
> (semantic Jaccard = 0.804), all four models achieve full coverage at the vehicle level; differences
> appear at Level 1, where the manually constructed SOFL model covers only 0.615 of the safety-related
> atomic requirements, having omitted five normative thresholds, whereas both LLM-generated DFD and
> UML models cover all of them because their prompts required thresholds to be drawn exclusively from
> the specification. In the defect-injection experiment, LLM reviewers detected 0.653 of planted
> defects on average with a 0.260 false-positive rate and only fair agreement with human adjudication
> (κ = 0.389), indicating that AI feedback must be corroborated by manual or tool-based verification.
> Contrary to the expectation that formal models are harder to review, the SOFL baseline yielded the
> highest detection rate (0.778) and the lowest false-positive rate (0.095), suggesting that explicit
> contracts make certain defect classes more visible to LLM reviewers.
