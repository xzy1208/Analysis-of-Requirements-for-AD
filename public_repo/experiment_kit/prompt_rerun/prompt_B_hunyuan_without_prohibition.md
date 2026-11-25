# Prompt B — Tencent Hunyuan 4 Flash，SOFL 无禁令（M3n）

**使用方法**：新开干净会话（模型选 Tencent Hunyuan 4 Flash），先附上
`NL-RQ-ADAS-v1_spec.md` 全文，然后粘贴下面的文本（含指南全文）。
**注意**：本 prompt 故意**不含** `x <> null` 禁令——这是它与 M3/M5 历史 prompt
的唯一关键差异；也**不要**给模型看 M1/M2/M4 或任何论文结论。

---

下面是 SOFL 建模指南，请严格遵守：

[粘贴 notation_guide_SOFL.md 全文]

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
- 与 M3（Hunyuan DFD，有禁令）相比的其它显著差异：
