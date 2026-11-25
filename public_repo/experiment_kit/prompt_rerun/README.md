# 同生成器禁令重跑包（关闭 Table VII 观察性对比的混杂）

## 背景
论文 V-C 的 `x <> null` 空洞守卫对比是观察性的：禁令与生成器族捆绑
（M3/M5 = Hunyuan 且有禁令；M2/M4 = MiniMax 且无禁令）。
本包用**同生成器、只增删一句禁令**的重跑把 2×2 设计补全：

| | 有禁令 | 无禁令 |
|---|---|---|
| MiniMax-M3.1-Flash | ✅ 已有？**← 本次跑 Prompt A** | ✅ 已有（M2，57 处） |
| Tencent Hunyuan 4 Flash | ✅ 已有（M3 DFD、M5 状态机，0 处） | **← 本次跑 Prompt B** |

- **Prompt A**（MiniMax + SOFL 指南 + 禁令）：若产物空洞守卫从 57 → ≈0，
  说明禁令在同生成器内有效 → 观察性对比升级为受控结论。
- **Prompt B**（Hunyuan + SOFL 指南，无禁令）：若产物出现空洞守卫，
  说明 Hunyuan 家族不写该 idiom 不是家族习惯而是禁令所致。

两格都拿到后，2×2 完整，V-C 的措辞可从 "observational" 升级为
"controlled (single run per cell)"。

## 铁律（与主实验一致）
1. 新开会话（干净上下文），不得给模型看 M1/M2/M4 或论文任何结论。
2. 只给：`NL-RQ-ADAS-v1_spec.md`（工程根目录）+ 对应 prompt 文件全文。
3. 生成后在 MES 里数 `<> null` / `<> ''` 出现次数（可用
   `python -c "..."` 正则计数，或直接数 fModule/cdfd 源文件里的 `<> null`）。
4. 结果记为 M2b（MiniMax+禁令）与 M3n（Hunyuan 无禁令），写入
   Table VII 备注行，不参与 I1–I4 主表。

## 文件
| 文件 | 内容 |
|---|---|
| `notation_guide_SOFL.md` | 两个 prompt 共用的 SOFL 建模指南（按主实验 prompt 结构重构） |
| `prompt_A_minimax_with_prohibition.md` | MiniMax-M3.1-Flash，含禁令句 |
| `prompt_B_hunyuan_without_prohibition.md` | Tencent Hunyuan 4 Flash，不含禁令句 |

## 已知差异声明
重跑 prompt 的措辞与主实验的历史 prompt 不可能逐字一致（历史 prompt 未存档，
这是论文遗留缺口）。因此单格结果要与原格对比时，须在论文中注明
"prompt rewritten, notation guide equivalent"。理想做法是**每个格子跑 2–3 次**
报告方差；至少 Prompt A/B 各跑两次。
