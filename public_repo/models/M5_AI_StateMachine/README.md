# M5 — 整车级 ADAS / AEB 分支 UML 状态机需求模型

## 1. 产出物清单

| 文件 | 内容 |
|---|---|
| `M5_AEB_statechart.puml` | PlantUML 状态机图，8 个状态、27 条迁移，含组合状态与层次子状态 |
| `M5_constraints.md` | 每状态 invariant、每迁移 pre/post、结构性约束，逐条标注规格条款 |
| `MES_M5_L1.json` | MES v1 交换格式，状态/迁移映射为 element，flows 表达守卫依赖 |
| `README.md` | 本文件：可追溯性矩阵、§11 四问回答、表达力对比、kind 扩展说明 |

生成方式：单次生成，`passes = 1`，`self_review_performed = false`。数值只取规格 §7/§8；
布尔表达式只用 `= <> > >= < <= and`；不写空值检查表达式。

## 2. 需求条款 → 状态机元素可追溯性矩阵

| 条款 | 规格要点 | 状态机元素 | 实现方式 |
|---|---|---|---|
| R-SCOPE-1 | SAE L2，驾驶员监督 | `DriverOverride`, T9–T13 | 状态/迁移 |
| R-SCOPE-2 | 系统边界为整车 | `E1`,`E2`,`E3`,`E7`,`E8`,`E9` | 外部接口 |
| R-SCOPE-4 | L1 仅细化 F3 的 AEB 分支 | `Normal`,`Caution`,`EmergencyBrake`,`DriverOverride` | 状态集合 |
| R-E-1 | 输出仅 E7/E8 | `Caution`,`EmergencyBrake`,`T3`,`T13`,`T20`,`T27` | 动作 |
| R-E-2 | E8 由监控/仲裁得到 | `T3`,`T13`,`T20`,`T27`,`E9` | 后置条件 |
| R-L1-1 | F3 拆为三个子功能 | `Normal`,`Caution`,`EmergencyBrake`,`DriverOverride` | 守卫/警告/机动 |
| F3.1 | TTC 集合；`obj_count = 0` | `T6`,`T7`,`T8` | 守卫 |
| F3.2 | 风险分级与警告 | `Normal`,`Caution`,`EmergencyBrake`,`T1`–`T5` | 不变式/守卫 |
| F3.3 | 机动选择与驾驶员加速优先级 | `DriverOverride`,`T9`–`T13`,`T27` | 后置条件 |
| N-2 | FCW 不晚于 TTC = 2.0 s | `T3`,`T10`,`T13`,`T20` | 守卫（1.5 s 触发） |
| N-3 | 碰撞速度削减 > 30 km/h | `EmergencyBrake` | 经 A-1 体现 |
| N-4 | CCRm 最坏闭合速度 | `EmergencyBrake` | 经 A-1 体现 |
| A-1 | 紧急减速度 6.0 m/s² | `EmergencyBrake`,`BrakeRamp`,`T3`,`T13`,`T20`,`T27` | 后置条件 |
| A-5 | `T_risk_high = 3.0 s`，`T_fcw = 1.5 s` | `Normal`,`Caution`,`EmergencyBrake`,`T1`–`T5`,`T9`–`T13`,`T18`–`T20` | 守卫 |
| R-G-1 | 前置/后置/量化约束 | `T1`–`T5`,`T9`–`T13`,`T18`–`T20` | 量化后置条件 |
| R-G-2 | 可追溯性 | 本矩阵 | 文档 |
| R-G-3 | 无孤儿元素 | `FaultDegraded`,`Deactivated` | OI-5 声明 |
| R-G-4 | 显式命名有向依赖 | `T1`–`T27` | flow |
| R-G-5 | 接口纪律 | `E7`,`E8` | boundary_out flow |
| R-G-6 | 前置条件显式、空值安全 | 四个活动状态 | 前置条件 |

## 3. 规格 §11 四个 open issues 的回答

**OI-1（七功能划分是否足够，是否需要独立驾驶员监控功能）**
就本 L1 行为模型而言，驾驶员注意力与手动接管由 `E3 driver_intent` 承载，并映射为
`DriverOverride` 状态，无需在 L1 新增功能；R-L0-1 也禁止在 Level 0 增加第八个功能。
独立的驾驶员监控功能仍属 Level 0 的开放问题，本模型不擅自引入。

**OI-2（D3 由 F1 写、F6/F7 读的归属是否可接受）**
可接受。R-D-1 / R-D-2 要求写入唯一、读取被显式指派；状态机只通过 T27 读取 D3 的
`ego_speed`，从不写 D3，没有扩大读取方集合，因此未引入归属冲突。

**OI-3（是否需要周期时间要求）**
需要。本状态机是事件驱动的，隐含假设 `min_ttc` 每个规划周期刷新一次；若没有周期时间
上界，TTC 波段切换就无法保证 §7 N-2 的 2.0 s 警告上限。规格未给周期数值，本模型遵守
"不自造数值"约束，仅把该缺口登记为高风险开放问题，不填具体毫秒数。

**OI-4（L1 应细化 F3 还是 F6/F7）**
按 R-SCOPE-4 的强制规定，本模型细化 F3 的 AEB 分支。状态机尤其适合这个选择：风险等级
切换是有状态的模式行为，而 F6/F7 执行链更适合用数据流/仲裁刻画。T13 体现了状态机相对
顺序图的优势——"critical 时驾驶员加速请求被禁止"这一条在顺序图里要枚举多个 alt 片段，
在状态机里只需省略一条 `EmergencyBrake -> DriverOverride` 迁移并配 SC-1 约束。

## 4. 状态划分的关键决策

1. **主模式按 F3.2 风险等级划分**：`Normal`（no risk）、`Caution`（caution）、
   `EmergencyBrake`（critical），保证每个状态的不变式都可直接对应规格分级。
2. **`DriverOverride` 独立建模**：F3.3 的优先级规则是非对称的——no risk / caution 允许
   驾驶员加速优先，critical 禁止。把它做成独立状态并显式省略 critical 到它的迁移，
   使"禁止劫持"成为可见的结构事实，而非隐藏在算法注释里。
3. **`EmergencyBrake` 用组合状态表达层次**：内含 `BrakeRamp` 与 `Standstill` 两个子状态，
   用 T27 在 `ego_speed = 0` 时切换，体现状态机对层次化的支持；子状态迁移同样带守卫/动作。
4. **空目标集单独处理**：F3.1 规定 `obj_count = 0` 时上报 count 0，故用 T6/T7/T8 显式
   回到 `Normal`，避免为 `min_ttc` 编造数值（OI-7）。
5. **退出/失效状态声明为合成元素**：`FaultDegraded` 守卫只取 E1/E2 validity flags，
   `Deactivated` 守卫只取 E3 ODD status；其动作是保守假设，依 R-G-3 在 OI-5 登记。
6. **守卫互斥与优先级**：同一源状态按 `odd_active = false` > `sensor_validity = false` >
   TTC 波段 排序（SC-2），使状态机可检验、无二义迁移。
7. **阈值全部引用 §7/§8**：`3.0` / `1.5` / `6.0` / `2.0`，无自造数值；A-1 与 A-3 的张力
   登记为 OI-6。

## 5. 为什么状态机图能表达 CDFD / DFD / 类图 / 顺序图表达不了的东西

- **CDFD / DFD**：核心是数据流、加工与存储，没有"系统当前处于哪种模式"这一维度。
  因此无法表达同一 `min_ttc` 在不同模式下触发不同迁移（例如 `min_ttc = 1.4 s` 在
  `Caution` 触发 T3，在 `DriverOverride` 触发 T13，在 `FaultDegraded` 触发 T20），
  也无法表达状态不变式、层次化子状态和守卫优先级这类"与历史/当前模式相关"的语义。
- **类图**：能声明 `risk_level`、`warning`、`maneuver` 等属性及其类型关系，但属于静态
  结构。它无法规定"警告必须在 TTC ≤ 1.5 s 由 caution 切换为 imminent_collision"、
  "紧急状态下 `maneuver.deceleration >= 6.0` 且驾驶员加速请求失效"这类带时序与守卫的
  行为约束；类图里"有一个属性"和"该属性何时、在何种条件下取何值"是两回事。
- **顺序图**：擅长给出单条消息交互轨迹，其 `alt` 组合片段只覆盖被显式画出的场景。
  对于持续驻留的状态（如 `Standstill` 需长期保持 `checked_cmd.target_speed = 0`）、
  状态不变式、循环、以及"禁止某条迁移"（SC-1）这类负向约束，顺序图要么遗漏，要么
  场景数爆炸。状态机用有限状态 + 守卫 + 动作 + 层次 + 不变式一次性覆盖全部可达行为，
  并支持 pre/post 形式化检验。
- **本实验的关键对照点**：F3.3 的非对称覆盖规则（critical 禁止驾驶员劫持、其余级别允许）
  是典型的模式相关行为。状态机用"有无某条迁移 + 不变式 `risk_level <> critical`"即可
  精确表达；DFD/CDFD 无法表达模式，类图无法表达时序守卫，顺序图需枚举多个场景且难以
  保证"所有场景下都不存在该迁移"这一全局性质。

## 6. MES `kind` 扩展说明

MES_schema.md 的 `elements[].kind` 示例为 `"function"`，本模型按任务要求扩展为
`"state"`（8 个）与 `"transition"`（27 个），属 schema 允许的扩展字段取值。
`level` 统一为 `"L1"`，`parent_module` 为 `"System"`（本模型是 F3 行为的细化）。
`flows` 中每条迁移对应一条 `kind = "active"` 的具名有向流，携带守卫变量，并在
`transition` / `guard` / `action` 扩展字段中记录事件守卫依赖；父级拥有的 F3.1/F3.2/F3.3、
D3、E9 仅在条款引用与 notes 中出现，不作为 L1 element，以保持元素 kind 的纯粹性。

## 7. 校验结论

- `M5_AEB_statechart.puml`：`@startuml` / `@enduml` 各 1 次，状态与迁移语法配对完整。
- `MES_M5_L1.json`：`json.load` 解析通过；35 个 element（8 state + 27 transition）、
  34 条 flow，producer/consumer 全部可解析，无重复 id。
- 全部守卫与约束仅使用允许算子，阈值仅取规格 §7/§8。
