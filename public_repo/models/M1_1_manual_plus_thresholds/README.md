# M1.1：人工模型补入阈值表后的对照实验

**目的**：论文 Finding 2 曾把 Level-1 覆盖度差距（人工 0.615 vs 生成 1.000）归因于"输入版本差"——
但那只是推断。M1.1 直接检验它：**把规范阈值表补入同一个人工模型，看差距是否消失**。

## 结论（已写入论文）

| 指标 | M1 (L1) | M1.1 (L1) | 变化 |
|---|---:|---:|---|
| I1 需求覆盖度 | 0.615 | **1.000** | +0.385 |
| I2 精确率 | 1.000 | 1.000 | — |
| I3 一致性 | 0.737 | 0.737 | — |
| I4 形式化精确度 | 0.800 | 0.800 | — |
| I4（严格内容判据） | 0.533 | 0.533 | — |

**Level-1 缺口是输入版本效应，不是建模能力差异。** 给定阈值表后，同一模型、同一记法、同一架构
的 I1 达到 1.000，与生成的 DFD/UML 模型完全持平；其余指标一律不动。

**修订代价**：34 次编辑操作（契约 21 + 类型字段 5 + 追溯 8），触及 46.7% 的契约子句。

## 做了什么改动

架构零改动——`System.cdfd` 与 `BehaviorPlanning.cdfd` 与 M1 **逐字节相同**。
全部改动在两个 `.fModule` 里：

| 阈值 | 落点 | 契约 |
|---|---|---|
| N-1 (130 km/h) | PlanManeuver（Level-1） | pre 加 `ego_state.speed<=130.0` |
| N-2 (FCW@1.5s) | ClassifyRisk | 已有，无需改动 |
| N-3 / N-4 | — | **不写进契约**（§7 中是 A-1 的推导依据，与 M3/M4 同口径，只在追溯表记录） |
| N-5 (RSS d_min) | Prediction / Motion_Planning | 新增字段 `lead_gap`、`lead_speed`；契约 `min_gap<=predicted_trajectories.lead_gap` |
| N-6 (RSS 制动轮廓) | Motion_Planning / Control / Safety_Shield | 新增字段 `decel_limit`；契约 `decel_limit>=4.0`、`brake_cmd>=decel_limit`、`accel_cmd<=2.0` |
| N-7 (横向包络) | Motion_Planning | 新增字段 `lateral_accel`；契约 `lateral_accel>=0` |

新字段（共 5 个）：`TrajectorySet.min_gap` / `.decel_limit` / `.lateral_accel`，
`PredictedTrajectory.lead_gap` / `.lead_speed`。

## 文件

```
models/M1_1_manual_plus_thresholds/
  System.cdfd              ← 与 M1 逐字节相同
  BehaviorPlanning.cdfd    ← 与 M1 逐字节相同
  System.fModule           ← 补入阈值契约
  BehaviorPlanning.fModule ← 补入 N-1
  MES_M1.1_L0.json         ← 自动生成
  MES_M1.1_L1.json         ← 自动生成
add_m1_1_coverage.py         ← M1.1 的人工覆盖标注（13 条 L1 + 沿用 M1 的 31 条 L0）
measure_revision_cost.py     ← 修订代价测算
revision_cost_m1_to_m1_1.json← 测算结果
```

## 复现

```bash
PY="C:/Users/zct11/.workbuddy/binaries/python/envs/default/Scripts/python"

# 1. 校验（M1.1 与 M1 用同一套三部分检查器）
mkdir -p /tmp/m11 && cp models/M1_1_manual_plus_thresholds/*.fModule \
                        models/M1_1_manual_plus_thresholds/*.cdfd /tmp/m11/
SOFL_BASE=/tmp/m11 $PY validate_sofl_model.py System
SOFL_BASE=/tmp/m11 $PY validate_sofl_model.py BehaviorPlanning System

# 2. 重建 MES
SOFL_BASE=".../models/M1_1_manual_plus_thresholds" \
MES_OUT=".../models/M1_1_manual_plus_thresholds" \
MES_MODEL_ID="M1.1" MES_GEN_DATE="2026-11-24" $PY build_mes_m1.py

# 3. 写覆盖标注（只新增 M1.1 条目，不动 M1–M5）
$PY add_m1_1_coverage.py

# 4. 评分
$PY score_models_v2.py            # → scores_v2.json
$PY formal_criterion_checker.py   # → formal_criterion_results.json
$PY measure_revision_cost.py      # → revision_cost_m1_to_m1_1.json
```

## ⬜ 需要你做的一件事（**已完成 2026-11-24 18:39**）

**作者已在 SOFL 工具中打开 M1.1，确认 GUI 正常加载。**

- 工具位置：`D:\EdgeDownload\Release\Release\SOFLTool.exe`（ClickOnce 部署的 WinForms 应用，
  2013 年版；同目录有 `knowledgeBase.xml`，内容为场景组合语义库，非 CDFD 模块文法）。
- M1.1 的四个文件已装入工具工程目录 `C:\Users\zct11\Desktop\Autonomous-driving\`：
  两个 `.fModule` 为 M1.1 版本，两个 `.cdfd` 与 M1 原版逐字节相同（架构未变，工具里无需重画图）。

**这使 M1.1 与 M1 具有同等地位**——两者都是 SOFL 工具的实际产物，都通过了同一套三部分检查器。

> ⚠️ **由此产生的一个坑，已修复**：工具工程目录会随人工建模进度被覆盖，现在装的是 M1.1。
> 因此 `build_mes_m1.py` 与 `validate_sofl_model.py` 的**默认数据源已从工具工程目录改为本仓库的
> `models/M1_manual_human/`**。否则直接重跑这两个脚本会把 M1 的 MES 悄悄覆盖成 M1.1 的，
> 使论文中 M1 的 I1 由 0.615 变成 1.000。要重建 M1.1 的 MES 必须显式指定：
>
> ```bash
> SOFL_BASE=".../models/M1_1_manual_plus_thresholds" \
> MES_OUT=".../models/M1_1_manual_plus_thresholds" \
> MES_MODEL_ID="M1.1" MES_GEN_DATE="2026-11-24" $PY build_mes_m1.py
> ```

**若将来要把工具工程目录恢复为 M1 原版**：把 `models/M1_manual_human/` 里的
`System.fModule` 与 `BehaviorPlanning.fModule` 复制回去即可（`.cdfd` 无需改动）。

## 论文中的位置

- 摘要 (1)
- §IV-C 模型集（新增一句：M1.1 通过同一套三部分检查器）
- §V-A2（新增小节，表 IV-A / 表 IV-B）
- §V-A 第二点、§VI-A、§VI-B
- Finding 2（重写）
- 威胁 4（补 M1.1 的边界：作者自修订 ⇒ 代价是下界）
- 结论首段
- 附录 A（产物清单 2 行）
