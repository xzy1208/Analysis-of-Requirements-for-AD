# Prompt A — MiniMax-M3.1-Flash，SOFL 复刻 + 空洞守卫禁令（M2b）

**使用方法**：新开干净会话（模型选 MiniMax-M3.1-Flash），先附上
`NL-RQ-ADAS-v1_spec.md` 全文，然后粘贴下面的文本（含指南全文）。
**不要**给模型看 M1/M2/M4 或任何论文结论。

---

下面是 SOFL 建模指南，请严格遵守：

[粘贴 notation_guide_SOFL.md 全文]

## 附加约束（本次重跑唯一新增的句子）

**不要写形如 `x <> null` 的前置条件：SOFL 中值按类型声明默认非空，
这类检查是同义反复；precondition 必须陈述真实约束（如阈值、有效性标志、
范围条件），而不是类型层面的空检查。**

---

完成后输出：
1. `ADAS_System` 与 `AEB_Branch` 两个 module 的完整文本；
2. 每个 module 对应 CDFD 的元素与连线清单（可用列表描述）；
3. open-issues 列表；
4. 可追溯性说明（每条 R-xx 对应的元素）。

## 结果登记（模型答完后人填写，不进 prompt）
- 生成日期：
- 会话是否完全干净（未见任何先前模型/论文）：
- `<> null` 出现次数（module+cdfd 全文统计）：____
- `<> ''` 出现次数：____
- 与 M2 相比的其它显著差异：
