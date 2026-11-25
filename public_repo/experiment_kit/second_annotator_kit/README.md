# 第二标注者工具包

## 先看这里

**要做什么、怎么做、要多久** → 看 [`HOWTO_通俗版.md`](HOWTO_通俗版.md)
**要不要做、为什么** → 看 [`DECISION.md`](DECISION.md)

## 当前状态

**2026-11-25 决定：执行第二人标注。**

材料已备妥，待发出：

```bash
python build_handover.py     # 生成 handover/ —— 这是唯一可以发给标注者的目录
```

`handover/` 里只有 5 个文件（手册、填答表、给标注者的说明、填写示例、清单），
**不含任何答案**。⚠️ **不要把 `second_annotator_kit/` 整个目录发给标注者** ——
其中的 `labelling_template_discriminating.json` 含 `primary_label`（即答案），
上一级目录的 `coverage_manual.json` 更是全部主标注。

材料收回后：

```bash
python experiment_kit/second_annotator_kit/finish_second_rater.py <填好的表>          # 演练
python experiment_kit/second_annotator_kit/finish_second_rater.py <填好的表> --apply  # 写入论文
```

该命令串起三步：算 κ → 中英两版六处回填 → 引用完整性复核。

## 文件清单

| 文件 | 给谁 | 说明 |
|---|---|---|
| `HOWTO_通俗版.md` | 作者 | 操作指南，含给标注者的话术 |
| `build_handover.py` | 作者 | 生成 `handover/` 交付目录 + 泄题扫描 |
| `handover/` | **标注者** | 交付目录（整个目录一起发） |
| `annotator_workbook.md` | **标注者** | 54 张判定卡，每张附候选条款（必做 30 + 可选 24） |
| `annotator_form.json` | **标注者** | 填答表（无 `primary_label` 字段） |
| `build_annotator_workbook.py` | 作者 | 生成手册与填答表 |
| `finish_second_rater.py` | 作者 | 收回后的完整流程入口（κ → 回填 → 复核） |
| `finalize_second_rater.py` | 作者 | 算 κ、列分歧、生成回填句 |
| `candidate_clauses.json` | 作者 | 候选条款（机器可读，备查/复核） |
| `labelling_template_discriminating.json` | 作者 | **不要发给标注者**（含 `primary_label`，即答案） |
| `make_discriminating_sample.py` | 作者 | 抽样与模板生成（`build_annotator_workbook.py` 已覆盖其功能） |
| `compute_kappa_discriminating.py` | 作者 | κ 计算（`finalize` 已内置，此为独立版本） |
| `DECISION.md` | 作者 | 决策依据 |
| `legacy/` | — | 旧版随机抽样工具包，已被新方案取代，保留备查 |

## 注意事项

- **`labelling_template_discriminating.json` 不可发给标注者** —— 含 `primary_label` 字段。
  `annotator_form.json` 已剥离该字段，可安全转发。
- 手册的候选条款按 **L0 + L1 合并**取材，与主标注口径一致。
  原因：N-5（RSS 安全距离）、TH-3/TH-4（场景包络）落在 L0 的
  Motion_Planning / Safety_Shield 上，不在 L1 的 AEB 分支里；
  只抽 L1 会漏掉这些，导致标注者误判"未覆盖"。
- 文档型载体也纳入候选：M3 的 `M3_process_dictionary.md` / `README.md`、
  M4 的 `M4_constraints.md`。M3/M4 覆盖 TH-3/4/5/6 正是靠这些文档性表述。

## 候选条款的排序规则（2026-11-25 修订）

候选条款不是"按关键字命中强度取前 N 条"，而是按**来源可信度**分层：

| 优先级 | 含义 | 例子 |
|---|---|---|
| 3 | 模型**自己声明**实现了该来源条款 | 追溯表里 `[N-4] …` 那一行；文档表格里 `\| N-4 \| … \|` 那一行 |
| 2 | 关键字强命中（数值/字段名直接对上） | `ego_state.speed<=130.0` |
| 1 | 关键字弱命中（语义相关但无具体数值） | `traffic_rules.speed_limit>0` |

每条需求都标注了它在规格里的**来源条款编号**（如 `N-4`、`F3.1`、`R-SCOPE-1`）。
凡是在模型追溯表或文档表格里带这个编号的行，就是模型对该需求的自我声明 ——
既最可靠，又不含任何答案（编号来自规格，不是来自标注结果）。

**为什么不能简单取"命中最强的前 N 条"**：早期版本按关键字强度排序后取前 8 条，
但 `"文档 L102"` 的排序在 ASCII 之后，导致文档型条款被系统性地挤出名额。
结果是 12 张卡（TH-1/3/4/5/6 × M3/M4）**看不到承载其覆盖的那一行**，
标注者会据此误判"未覆盖"，产生**假分歧**、把 κ 算低。
现已改为：按优先级排序 + 每个来源（元素 id / 追溯标签 / 文档文件）最多取 2 条。

`build_annotator_workbook.py` 每次运行会自检三件事，全绿才可发给标注者：

1. 主标注为"覆盖"的卡片是否都给出了候选（当前 40/40）；
2. 这些卡片里是否存在优先级 3 的候选（当前 34/40；缺的 6 张全在 M1，
   因为 M1 用自己的元素命名、不按规格编号打追溯标签，靠关键字命中足够）；
3. 承载覆盖的**文档型**条款有没有被截断挤掉（当前 0 张）。

## 1 / 0.5 / 0 的界线：要素分解测试（2026-11-25 加）

原手册对 0.5 的判据是"模型提到了相关的东西，但缺了关键部分" —— 不可机械执行，
标注者只能凭语感判断，必然引入与被测判据无关的方差。现改为**要素分解测试**：

- 每条判别力需求（TH-1/3/4/5/6）都在手册里列出它的**要素**（来自规格原文，含答案）；
- 要素全部写出 = 1；写出一部分 = 0.5；一个都没写 = 0；
- 「被写出」= 契约条款 **或** 把它与该需求挂钩的追溯说明；
- 「没写出」= 只有信号名无约束 / 只覆盖一半职责 / 要素落在别处；
- **适用条件与排除条件不计入要素**（如 TH-1 的"静止目标除外"、TH-3 的"部分介入"）——
  它们限定要求的适用范围，编码它们反而是过度约束。

要素划分经核对与主标注完全自洽：单要素需求（TH-1、TH-3）只出现 0 / 1，
多要素需求（TH-4 三要素、TH-5/TH-6 两要素）才出现 0.5；
主标注全部 3 个 0.5 恰好都落在多要素需求上。

要素划分写在 `build_annotator_workbook.py` 的 `ELEMENTS`，
不计入要素的措辞写在 `NOT_ELEMENTS`。⚠️ **勿把适用条件误列为要素** ——
若把 TH-3 的"部分介入"算作要素，M3/M4 会从 1 掉到 0.5，Finding 2 的
"M1.1 = M3 = M4" 就不再成立。

