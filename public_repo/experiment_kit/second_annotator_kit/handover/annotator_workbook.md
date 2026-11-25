# 需求覆盖度第二标注工作手册

> 这份手册要你做的事只有一件：**判断若干条需求，在某个模型里有没有被写到**。
> 全程约 30–45 分钟。判断依据全部写在下面的候选条款里，你不需要通读模型全文。

## 一、你要做什么

每个任务是一对「需求 + 模型」。你打开模型里与该需求相关的条款（手册已经替你摘出来了），
然后判断它算不算覆盖了这条需求，给出三个分数之一：

| 分数 | 含义 | 判断标准 |
|---|---|---|
| **1** | 覆盖 | 这条需求的**每一个要素**都被模型条款明确写出 |
| **0.5** | 部分覆盖 | 模型触及了这条需求，但**至少有一个要素没写出来** |
| **0** | 未覆盖 | 模型里找不到对应语义 |

**关键判断规则（重要）**：一条需求如果是由另一条需求推导出来的，
那么当模型只写出了那个推导结果、没写推导依据时，
**算「1」（覆盖）**，只要这个推导关系在该模型里有说明（追溯表、注释、文档里写过"由 X 推导"即可）。
如果没有说明，就按「0.5」或「0」处理。

> 这条规则是本次标注的核心分歧点，也是我们最想知道你判断的地方。
> 遇到拿不准的，按你第一反应的读法填，并在 evidence 里写明你的理由。

**第二条规则（同样重要）**：每条需求都给了它在规格里的**来源条款编号**（如 `N-4`、`F3.1`、`R-SCOPE-1`）。
候选条款里凡是带这个编号的行 —— 追溯表里的 `[N-4] …`、文档表格里的 `| N-4 | … |` —— 都是**模型自己声明"我实现了这条需求"**。
看到这类行时，请把它当作强证据；但也要核对它下面的载体条款是否真的写出了该需求的语义。

**第三条规则：1 与 0.5 的界线 —— 要素分解测试**

「明确写出」与「部分写出」的分界不是语气强弱，而是**这条需求的要素有没有被写全**。
每条需求下面都列出了它的要素（要素划分来自规格原文，与任何标注结果无关）。
把要素逐个对到模型条款上：

| 情形 | 分数 |
|---|---|
| 每个要素都在条款里被写出 | **1** |
| 模型触及了这条需求，但至少有一个要素没写出来 | **0.5** |
| 一个要素都没写出来 | **0** |

「被写出」包含两种情形，**都算写出**：
1. 数值/条件直接出现在契约里；
2. 数值/条件出现在追溯表或文档里，且追溯说明写清了它与本需求的对应关系。

「没写出来」有三种典型形态，**都要判 0.5、不判 1**：
- **只有信号名、没有约束** —— 提到了这个量，但没把它写成契约（例如只写"保持最小间距"却无 d_min 表达式）；
- **只覆盖一半职责** —— 复合需求里只写了一部分（例如写了制动下限、没写响应时间上限）；
- **要素落在别处** —— 本分支的条款里没有，由父模块或相邻元素实现。

> **规则一优先于规则三**：若某个要素可由推导覆盖、且推导关系有说明，
> 该要素即视为"已写出"；规则三只用来判断**要素是否齐全**。

**适用条件与排除条件不计入要素。** 需求里"在……情形下""（……除外）"这类措辞，
是对要求**适用范围的限定**，不是模型需要另行编码的断言 —— 限定越窄，要求越弱。
模型把这些限定也编码进去反而是过度约束。个别需求的具体说明列在该需求下方。

## 二、评分怎么写

- `label`：填 `1`、`0.5` 或 `0`
- `evidence`：一句话，指出你依据哪个元素、哪条条款，以及是怎么对应的。
  例如：`C-F3-4 postcondition 写了 decel_req>=6.0，与 N-3 的 30 km/h 经 A-1 推导对应`
- 拿不准的照实填，不必迎合任何"标准答案"——我们要的是你的独立判断。

## 三、纪律要求

- **不要**去查论文正文、结论表或任何标注结果文件。
- 提问请在开始前一次性问完（规格里的缩写、术语含义等），标注过程中不要再逐条问。
- 材料里如果出现你觉得矛盾或说不通的地方，照实记下来，这本身也是有用的信息。

## 四、模型材料对照表

每张判定卡下面都附了候选条款。如果候选明显不相关、而你怀疑模型里其实有相关内容，
可以翻看原始产物：

| 模型 | 是什么 | 原始产物 |
|---|---|---|
| `M1` | M1 人工 SOFL（原始版） | `models/M1_manual_human/BehaviorPlanning.fModule` |
| `M1.1` | M1.1 人工 SOFL（补入阈值表） | `models/M1_1_manual_plus_thresholds/BehaviorPlanning.fModule` |
| `M2` | M2 LLM 生成 SOFL | `models/M2_AI_SOFL_single/AEB_Branch.fModule` |
| `M3` | M3 LLM 生成 DFD | `models/M3_AI_DFD/M3_process_dictionary.md` |
| `M4` | M4 LLM 生成 UML 类图/顺序图 | `models/M4_AI_UML/M4_L1.puml + M4_constraints.md` |
| `M5` | M5 LLM 生成 UML 状态机 | `models/M5_AI_StateMachine/M5_AEB_statechart.puml` |

## 五、判定卡

共 54 张卡：**必做 30 张**（第一部分，承载全部有争议的判断）；**可选 24 张**（第二部分，对照集，用于检查你是不是对某类模型一律给"已覆盖"）。
时间紧就只做必做部分。

### 需求 TH-1 —— AEB 工作车速上限至少 130 km/h（静止目标除外）

来源条款：N-1

规格来源条款编号：`N-1`（模型若在追溯表或文档表格里标注了这个编号，说明它自称实现了该条款 —— 请一并考虑）

**本需求的要素分解**（1 个要素，来自规格原文；请把每个要素逐个对到模型条款上）：

- 要素 a：AEB 能力的适用车速上限 **≥ 130 km/h**（即：模型写 `speed<=130.0` 即满足；写 `speed<=100.0` 则不满足）

> 「静止目标除外」是适用范围排除（规格原文：operational up to ... 130 km/h, stationary targets excluded），不计入要素。模型未另行编码该排除，**不影响覆盖**，仍按 1 个要素判定。
> ⚠️ **不等号方向**：本需求写的是「上限**至少** 130 km/h」，约束的是**上限本身**（要求上限 V ≥ 130）；而模型写 `ego_state.speed<=130.0`，是把上限**取成 130**。130 ≥ 130 成立，**因此模型写法正确，不要判 0.5**。
> 只有两种情况算没写出来：模型写出的上限**小于** 130（如 `<=100.0`）——那会在 100–130 km/h 之间留下 AEB 不生效的空档；或模型写的是**严格**不等式 `<130.0`——那样恰好在 130 km/h 时能力不可用，不满足「至少 130」。

→ 1 个要素全部写出 = `1`；写出一部分 = `0.5`；一个都没写出 = `0`

#### 卡 TH-1 × M1 — M1 人工 SOFL（原始版）

*Level-0（整车）+ Level-1（AEB 分支：ComputeTTC → ClassifyRisk → PlanManeuver）*

候选条款（按相关度排序，请逐条看）：

- `Motion_Planning@L0` [postcondition] traffic_rules.speed_limit>0 -> trajectory.max_speed<=traffic_rules.speed_limit

→ **label** = `___`    **evidence** = ________________________

#### 卡 TH-1 × M1.1 — M1.1 人工 SOFL（补入阈值表）

*Level-0 + Level-1，AEB 分支已补入阈值表*

候选条款（按相关度排序，请逐条看）：

- `traceability@L0` [traceability] [N-1] AEB capability operational up to a vehicle speed of 130 km/h (N-1). | 载体: precondition ego_state.speed<=130.0 | 元素: PlanManeuver
- `traceability@L1` [traceability] [N-1] AEB capability operational up to a vehicle speed of 130 km/h (N-1). | 载体: precondition ego_state.speed<=130.0 | 元素: PlanManeuver
- `Motion_Planning@L0` [postcondition] traffic_rules.speed_limit>0 -> trajectory.max_speed<=traffic_rules.speed_limit
- `traceability@L0` [traceability] [N-3] The >30 km/h impact-speed reduction is realised through the 6.0 m/s2 emergency deceleration of A-1; the derived intermediate figures of section 7 are not used as constraint values. | 载体: via A-1 (decel_req>=6.0) | 元素: PlanManeuver
- `traceability@L1` [traceability] [N-3] The >30 km/h impact-speed reduction is realised through the 6.0 m/s2 emergency deceleration of A-1; the derived intermediate figures of section 7 are not used as constraint values. | 载体: via A-1 (decel_req>=6.0) | 元素: PlanManeuver
- `traceability@L0` [traceability] [N-4] The CCRm envelope (VUT 60-130 km/h, target 20 km/h, target decelerating at -4 m/s2) is the sizing basis of A-1 and is not written as a constraint value. | 载体: via A-1 (decel_req>=6.0) | 元素: PlanManeuver
- `traceability@L1` [traceability] [N-4] The CCRm envelope (VUT 60-130 km/h, target 20 km/h, target decelerating at -4 m/s2) is the sizing basis of A-1 and is not written as a constraint value. | 载体: via A-1 (decel_req>=6.0) | 元素: PlanManeuver

→ **label** = `___`    **evidence** = ________________________

#### 卡 TH-1 × M2 — M2 LLM 生成 SOFL

*Level-0（ADAS_System）+ Level-1（AEB_Branch）*

候选条款（按相关度排序，请逐条看）：

- `traceability@L0` [traceability] [N-1] AEB branch guaranteed for ego_state.speed <= 130.0 km/h (realised in child module AEB_Branch). | 载体: postcondition of the Level-1 TTC_Computation | 元素: F3
- `traceability@L1` [traceability] [N-1] The AEB branch is guaranteed up to 130 km/h. | 载体: postcondition ego_state.speed <= 130.0 | 元素: F3.1
- `F3.1@L1` [invariant] The AEB capability is guaranteed for ego_state.speed <= 130.0 km/h (N-1).
- `F3.1@L1` [postcondition] ego_state.speed <= 130.0 -> ttc_set <> null
- `F5@L0` [postcondition] trajectory.max_speed <= Traffic_Rules_DB.posted_speed_limit
- `traceability@L0` [traceability] [N-3] Emergency deceleration sized from N-3/N-4 as A-1 = 6.0 m/s^2; the > 30 km/h impact-speed reduction is the sizing yardstick, not a runtime threshold. | 载体: postcondition manoeuvre.required_decel >= 6.0 | 元素: F3, F7
- `traceability@L1` [traceability] [N-4] Sizing basis only; the 60-130 km/h VUT window and the 20 km/h target speed are assessment parameters without a runtime element (see OI-14). | 载体: postcondition manoeuvre.required_decel >= 6.0 | 元素: F3.3
- `traceability@L0` [traceability] [N-4] The CCRb -4 m/s^2 target deceleration is realised as the RSS braking capability 4.0 m/s^2; the 60-130 km/h VUT window and the 20 km/h target speed are assessment-scenario parameters with no runtime element (see OI-14). | 载体: postcondition trajectory.decel_limit >= 4.0 | 元素: F5, F3

→ **label** = `___`    **evidence** = ________________________

#### 卡 TH-1 × M3 — M3 LLM 生成 DFD

*Level-0 + Level-1（F3.1/F3.2/F3.3 细化）；部分语义写在过程字典与 README 追溯表里*

候选条款（按相关度排序，请逐条看）：

- `traceability@L1` [traceability] [N-1] AEB operational up to 130 km/h (sizing context for A-1). | 载体: postcondition | 元素: F3.3
- `traceability@L0` [traceability] [N-1] AEB operational up to 130 km/h; realised in child F3.3 sizing. | 载体: postcondition | 元素: F3.3, F1
- `README.md` [文档 L102] | N-1 | F3.3, F1 | AEB up to 130 km/h (sizing context) |
- `M3_process_dictionary.md` [文档 L18] * Numeric constants are taken **only** from specification §7 (N-1..N-7) and §8
- `README.md` [文档 L29] 4. **Threshold discipline:** every numeric value comes from §7 (N-1..N-7) and
- `F5@L0` [postcondition] trajectory.max_speed <= traffic_rules.speed_limit and trajectory.max_accel <= 3.0 and trajectory.required_decel >= manoeuvre.required_decel
- `M3_process_dictionary.md` [文档 L92] - guard `true` → `trajectory.max_speed <= traffic_rules.speed_limit and trajectory.max_accel <= 3.0 and trajectory.required_decel >= manoeuvre.required_decel`
- `README.md` [文档 L104] | N-3 | F3.3 | >30 km/h impact-speed reduction |

→ **label** = `___`    **evidence** = ________________________

#### 卡 TH-1 × M4 — M4 LLM 生成 UML 类图/顺序图

*Level-0 + Level-1（三个类细化）；阈值追溯表在 M4_constraints.md*

候选条款（按相关度排序，请逐条看）：

- `traceability@L0` [traceability] [N-1] AEB capability operational up to a vehicle speed of 130 km/h. | 载体: invariant C-F3-5 | 元素: F3
- `traceability@L1` [traceability] [N-1] The emergency manoeuvre is limited to a vehicle speed of 130 km/h. | 载体: invariant C-L1-10 | 元素: F3.3
- `M4_constraints.md` [文档 L11] | 阈值来源 | 仅规格 §7（N-1…N-7）与 §8（A-1…A-7）；未自造任何数值 |
- `M4_constraints.md` [文档 L159] | C-L1-10 | post（guard `risk_level = 'critical'`） | `ego_speed_kmh <= 130.0` | **N-1** |
- `F7@L0` [invariant] checked_speed_cmd_kmh <= speed_limit_kmh
- `F3.3@L1` [invariant] driver_accel_request = 'true' and risk_level = 'critical' | required_decel_ms2 >= 6.0 and target_speed_kmh = 0.0
- `F5@L0` [invariant] max_permitted_speed_kmh <= speed_limit_kmh
- `F3@L0` [invariant] risk_level = 'critical' | ego_speed_kmh <= 130.0
- `F3.3@L1` [invariant] risk_level = 'critical' | ego_speed_kmh <= 130.0
- `F3@L0` [invariant] risk_level = 'critical' | required_decel_ms2 >= 6.0 and target_speed_kmh = 0.0
- `F7@L0` [postcondition] checked_speed_cmd_kmh <= speed_limit_kmh
- `F5@L0` [postcondition] max_permitted_speed_kmh <= speed_limit_kmh
- `traceability@L0` [traceability] [N-3] The > 30 km/h impact-speed reduction is realised through the 6.0 m/s2 emergency deceleration of A-1; the derived intermediate figures of section 7 are not used as constraint values. | 载体: invariant C-F3-4 (via A-1) | 元素: F3, F5, F6, F7
- `traceability@L0` [traceability] [N-4] The CCRm envelope (VUT 60-130 km/h, target 20 km/h, target decelerating at -4 m/s2) is the sizing basis of A-1 and is realised by C-F3-4 and C-F5-5. | 载体: derivation of A-1 | 元素: F3, F5
- `M4_constraints.md` [文档 L169] | N-1 | 130 km/h | C-F3-5, C-L1-10 |
- `M4_constraints.md` [文档 L50] | C-F3-5 | post（guard `risk_level = 'critical'`） | `ego_speed_kmh <= 130.0` | **N-1** |

→ **label** = `___`    **evidence** = ________________________

#### 卡 TH-1 × M5 — M5 LLM 生成 UML 状态机

*Level-1（AEB 状态机），约束写在状态迁移标签上*

> **候选条款：无。** 该模型中未检索到与本需求相关的条款。
> 若你认为漏检，请翻看原始产物 `models/M5_AI_StateMachine/M5_AEB_statechart.puml`。

→ **label** = `___`    **evidence** = ________________________

### 需求 TH-3 —— 部分介入需将碰撞速度降低超过 30 km/h

来源条款：N-3

规格来源条款编号：`N-3`（模型若在追溯表或文档表格里标注了这个编号，说明它自称实现了该条款 —— 请一并考虑）

**本需求的要素分解**（1 个要素，来自规格原文；请把每个要素逐个对到模型条款上）：

- 要素 a：碰撞速度降低量 > 30 km/h

> 「部分介入（type 3）」是适用情形，**不计入要素**。模型若用风险等级或机动类型来表达「部分介入」即可，不要求出现字面 type 3。

→ 1 个要素全部写出 = `1`；写出一部分 = `0.5`；一个都没写出 = `0`

#### 卡 TH-3 × M1 — M1 人工 SOFL（原始版）

*Level-0（整车）+ Level-1（AEB 分支：ComputeTTC → ClassifyRisk → PlanManeuver）*

> **候选条款：无。** 该模型中未检索到与本需求相关的条款。
> 若你认为漏检，请翻看原始产物 `models/M1_manual_human/BehaviorPlanning.fModule`。

→ **label** = `___`    **evidence** = ________________________

#### 卡 TH-3 × M1.1 — M1.1 人工 SOFL（补入阈值表）

*Level-0 + Level-1，AEB 分支已补入阈值表*

候选条款（按相关度排序，请逐条看）：

- `traceability@L0` [traceability] [N-3] The >30 km/h impact-speed reduction is realised through the 6.0 m/s2 emergency deceleration of A-1; the derived intermediate figures of section 7 are not used as constraint values. | 载体: via A-1 (decel_req>=6.0) | 元素: PlanManeuver
- `traceability@L1` [traceability] [N-3] The >30 km/h impact-speed reduction is realised through the 6.0 m/s2 emergency deceleration of A-1; the derived intermediate figures of section 7 are not used as constraint values. | 载体: via A-1 (decel_req>=6.0) | 元素: PlanManeuver
- `traceability@L0` [traceability] [N-1] AEB capability operational up to a vehicle speed of 130 km/h (N-1). | 载体: precondition ego_state.speed<=130.0 | 元素: PlanManeuver
- `traceability@L1` [traceability] [N-1] AEB capability operational up to a vehicle speed of 130 km/h (N-1). | 载体: precondition ego_state.speed<=130.0 | 元素: PlanManeuver
- `traceability@L0` [traceability] [N-4] The CCRm envelope (VUT 60-130 km/h, target 20 km/h, target decelerating at -4 m/s2) is the sizing basis of A-1 and is not written as a constraint value. | 载体: via A-1 (decel_req>=6.0) | 元素: PlanManeuver
- `traceability@L1` [traceability] [N-4] The CCRm envelope (VUT 60-130 km/h, target 20 km/h, target decelerating at -4 m/s2) is the sizing basis of A-1 and is not written as a constraint value. | 载体: via A-1 (decel_req>=6.0) | 元素: PlanManeuver

→ **label** = `___`    **evidence** = ________________________

#### 卡 TH-3 × M2 — M2 LLM 生成 SOFL

*Level-0（ADAS_System）+ Level-1（AEB_Branch）*

候选条款（按相关度排序，请逐条看）：

- `traceability@L0` [traceability] [N-3] Emergency deceleration sized from N-3/N-4 as A-1 = 6.0 m/s^2; the > 30 km/h impact-speed reduction is the sizing yardstick, not a runtime threshold. | 载体: postcondition manoeuvre.required_decel >= 6.0 | 元素: F3, F7
- `traceability@L1` [traceability] [N-3] The 6.0 m/s^2 emergency deceleration is sized from the N-3 impact-speed yardstick. | 载体: postcondition manoeuvre.required_decel >= 6.0 | 元素: F3.3
- `F3.1@L1` [invariant] The AEB capability is guaranteed for ego_state.speed <= 130.0 km/h (N-1).
- `traceability@L0` [traceability] [N-1] AEB branch guaranteed for ego_state.speed <= 130.0 km/h (realised in child module AEB_Branch). | 载体: postcondition of the Level-1 TTC_Computation | 元素: F3
- `traceability@L1` [traceability] [N-1] The AEB branch is guaranteed up to 130 km/h. | 载体: postcondition ego_state.speed <= 130.0 | 元素: F3.1
- `traceability@L1` [traceability] [N-4] Sizing basis only; the 60-130 km/h VUT window and the 20 km/h target speed are assessment parameters without a runtime element (see OI-14). | 载体: postcondition manoeuvre.required_decel >= 6.0 | 元素: F3.3
- `traceability@L0` [traceability] [N-4] The CCRb -4 m/s^2 target deceleration is realised as the RSS braking capability 4.0 m/s^2; the 60-130 km/h VUT window and the 20 km/h target speed are assessment-scenario parameters with no runtime element (see OI-14). | 载体: postcondition trajectory.decel_limit >= 4.0 | 元素: F5, F3

→ **label** = `___`    **evidence** = ________________________

#### 卡 TH-3 × M3 — M3 LLM 生成 DFD

*Level-0 + Level-1（F3.1/F3.2/F3.3 细化）；部分语义写在过程字典与 README 追溯表里*

候选条款（按相关度排序，请逐条看）：

- `traceability@L1` [traceability] [N-3] Impact-speed reduction sizing A-1. | 载体: postcondition | 元素: F3.3
- `traceability@L0` [traceability] [N-3] Impact-speed reduction; sizes emergency deceleration A-1. | 载体: postcondition | 元素: F3.3
- `README.md` [文档 L104] | N-3 | F3.3 | >30 km/h impact-speed reduction |
- `M3_process_dictionary.md` [文档 L190] deceleration at least `$A_emergency = 6.0` m/s² (A-1, sized from N-3/N-4) and
- `traceability@L1` [traceability] [N-1] AEB operational up to 130 km/h (sizing context for A-1). | 载体: postcondition | 元素: F3.3
- `traceability@L0` [traceability] [N-1] AEB operational up to 130 km/h; realised in child F3.3 sizing. | 载体: postcondition | 元素: F3.3, F1
- `README.md` [文档 L102] | N-1 | F3.3, F1 | AEB up to 130 km/h (sizing context) |
- `README.md` [文档 L127] active handover management is in scope. Impact: medium. Recorded as OI-1.
- `README.md` [文档 L136] model leaves it open. Impact: medium. Recorded as OI-2.
- `README.md` [文档 L143] flags this as the highest-impact gap. Impact: high. Recorded as OI-3.
- `README.md` [文档 L152] here. Impact: medium. Recorded as OI-4.

→ **label** = `___`    **evidence** = ________________________

#### 卡 TH-3 × M4 — M4 LLM 生成 UML 类图/顺序图

*Level-0 + Level-1（三个类细化）；阈值追溯表在 M4_constraints.md*

候选条款（按相关度排序，请逐条看）：

- `traceability@L0` [traceability] [N-3] The > 30 km/h impact-speed reduction is realised through the 6.0 m/s2 emergency deceleration of A-1; the derived intermediate figures of section 7 are not used as constraint values. | 载体: invariant C-F3-4 (via A-1) | 元素: F3, F5, F6, F7
- `M4_constraints.md` [文档 L171] | N-3 | 冲击速度降低 > 30 km/h | C-F3-4（经 A-1 = 6.0 m/s² 体现），C-F5-5, C-F6-4, C-F7-2, C-F7-3 |
- `M4_constraints.md` [文档 L49] | C-F3-4 | post（guard `risk_level = 'critical'`） | `required_decel_ms2 >= 6.0 and target_speed_kmh = 0.0` | **A-1**（由 N-3/N-4 推导） |
- `traceability@L0` [traceability] [N-1] AEB capability operational up to a vehicle speed of 130 km/h. | 载体: invariant C-F3-5 | 元素: F3
- `traceability@L1` [traceability] [N-1] The emergency manoeuvre is limited to a vehicle speed of 130 km/h. | 载体: invariant C-L1-10 | 元素: F3.3
- `traceability@L0` [traceability] [N-4] The CCRm envelope (VUT 60-130 km/h, target 20 km/h, target decelerating at -4 m/s2) is the sizing basis of A-1 and is realised by C-F3-4 and C-F5-5. | 载体: derivation of A-1 | 元素: F3, F5
- `M4_constraints.md` [文档 L169] | N-1 | 130 km/h | C-F3-5, C-L1-10 |
- `M4_constraints.md` [文档 L172] | N-4 | CCRm：VUT 60–130 km/h，目标 20 km/h，目标 −4 m/s² | C-F3-4 / C-F5-5（A-1 的推导前提，追溯于 F3.3、F6） |
- `M4_constraints.md` [文档 L184] > 规格 §7 “Derived threshold” 中的 30 km/h、110 km/h、30.6 m/s、8.33 m/s、1.39 s、≈37 m、0.61 g

→ **label** = `___`    **evidence** = ________________________

#### 卡 TH-3 × M5 — M5 LLM 生成 UML 状态机

*Level-1（AEB 状态机），约束写在状态迁移标签上*

候选条款（按相关度排序，请逐条看）：

- `traceability@L1` [traceability] [N-3] Sized through A-1. | 载体: invariant | 元素: EmergencyBrake

→ **label** = `___`    **evidence** = ________________________

### 需求 TH-4 —— CCRm 测试包络 VUT 60–130 km/h、目标 20 km/h；CCRb 目标减速度 −4 m/s²

来源条款：N-4

规格来源条款编号：`N-4`（模型若在追溯表或文档表格里标注了这个编号，说明它自称实现了该条款 —— 请一并考虑）

**本需求的要素分解**（3 个要素，来自规格原文；请把每个要素逐个对到模型条款上）：

- 要素 a：CCRm 试验场景的 VUT 车速窗口 60–130 km/h
- 要素 b：CCRm 试验场景的目标初速 20 km/h
- 要素 c：CCRb 试验场景的目标减速度 −4 m/s²

→ 3 个要素全部写出 = `1`；写出一部分 = `0.5`；一个都没写出 = `0`

#### 卡 TH-4 × M1 — M1 人工 SOFL（原始版）

*Level-0（整车）+ Level-1（AEB 分支：ComputeTTC → ClassifyRisk → PlanManeuver）*

候选条款（按相关度排序，请逐条看）：

- `PlanManeuver@L1` [postcondition] risk_level.risk_type=0 -> maneuver.maneuver_type=1 and maneuver.target_speed<=map_data.speed_limit
- `PlanManeuver@L1` [postcondition] risk_level.risk_type=2 -> maneuver.maneuver_type=3 and maneuver.decel_req>=6.0 and maneuver.target_speed=0
- `Behavior_Planning@L0` [postcondition] traffic_rules.speed_limit>0 -> maneuver.target_speed<=traffic_rules.speed_limit

→ **label** = `___`    **evidence** = ________________________

#### 卡 TH-4 × M1.1 — M1.1 人工 SOFL（补入阈值表）

*Level-0 + Level-1，AEB 分支已补入阈值表*

候选条款（按相关度排序，请逐条看）：

- `traceability@L0` [traceability] [N-4] The CCRm envelope (VUT 60-130 km/h, target 20 km/h, target decelerating at -4 m/s2) is the sizing basis of A-1 and is not written as a constraint value. | 载体: via A-1 (decel_req>=6.0) | 元素: PlanManeuver
- `traceability@L1` [traceability] [N-4] The CCRm envelope (VUT 60-130 km/h, target 20 km/h, target decelerating at -4 m/s2) is the sizing basis of A-1 and is not written as a constraint value. | 载体: via A-1 (decel_req>=6.0) | 元素: PlanManeuver
- `PlanManeuver@L1` [postcondition] risk_level.risk_type=0 -> maneuver.maneuver_type=1 and maneuver.target_speed<=map_data.speed_limit
- `PlanManeuver@L1` [postcondition] risk_level.risk_type=2 -> maneuver.maneuver_type=3 and maneuver.decel_req>=6.0 and maneuver.target_speed=0
- `Behavior_Planning@L0` [postcondition] traffic_rules.speed_limit>0 -> maneuver.target_speed<=traffic_rules.speed_limit
- `traceability@L0` [traceability] [A-4] Yaw-rate envelope 3.5 rad/s. | 载体: postcondition yaw_rate in (-3.5, 3.5) | 元素: Perception_Localization
- `traceability@L1` [traceability] [A-4] Yaw-rate envelope 3.5 rad/s. | 载体: postcondition yaw_rate in (-3.5, 3.5) | 元素: Perception_Localization
- `traceability@L0` [traceability] [A-6] Normalised steering command envelope +/-1.0. | 载体: steer_cmd in (-1.0, 1.0) | 元素: Control, Safety_Shield
- `traceability@L1` [traceability] [A-6] Normalised steering command envelope +/-1.0. | 载体: steer_cmd in (-1.0, 1.0) | 元素: Control, Safety_Shield
- `traceability@L0` [traceability] [N-7] Euclidean manoeuvring envelope; the specification fixes no numeric value, so the constraint is qualitative. | 载体: trajectory.lateral_accel>=0 | 元素: Motion_Planning
- `traceability@L1` [traceability] [N-7] Euclidean manoeuvring envelope; the specification fixes no numeric value, so the constraint is qualitative. | 载体: trajectory.lateral_accel>=0 | 元素: Motion_Planning

→ **label** = `___`    **evidence** = ________________________

#### 卡 TH-4 × M2 — M2 LLM 生成 SOFL

*Level-0（ADAS_System）+ Level-1（AEB_Branch）*

候选条款（按相关度排序，请逐条看）：

- `traceability@L1` [traceability] [N-4] Sizing basis only; the 60-130 km/h VUT window and the 20 km/h target speed are assessment parameters without a runtime element (see OI-14). | 载体: postcondition manoeuvre.required_decel >= 6.0 | 元素: F3.3
- `traceability@L0` [traceability] [N-4] The CCRb -4 m/s^2 target deceleration is realised as the RSS braking capability 4.0 m/s^2; the 60-130 km/h VUT window and the 20 km/h target speed are assessment-scenario parameters with no runtime element (see OI-14). | 载体: postcondition trajectory.decel_limit >= 4.0 | 元素: F5, F3
- `F1@L0` [invariant] ego_state.yaw_rate <= 3.5 and ego_state.yaw_rate >= -3.5 (A-4 sanity envelope on the localisation output)
- `F3@L0` [invariant] manoeuvre.target_speed <= Traffic_Rules_DB.posted_speed_limit (traffic rules respected)
- `F3@L0` [postcondition] manoeuvre.target_speed <= Traffic_Rules_DB.posted_speed_limit
- `F3.3@L1` [postcondition] risk_level.risk_code = 2 -> manoeuvre.manoeuvre_type = 4 and manoeuvre.required_decel >= 6.0 and manoeuvre.target_speed = 0
- `traceability@L0` [traceability] [A-3] Longitudinal actuation envelope 3.0 m/s^2 in F6 and F7. | 载体: postconditions on long_accel_cmd and checked_cmd | 元素: F6, F7
- `traceability@L0` [traceability] [A-4] Yaw-rate sanity envelope on the localisation output. | 载体: postcondition ego_state.yaw_rate <= 3.5 and ego_state.yaw_rate >= -3.5 | 元素: F1
- `traceability@L0` [traceability] [A-6] Normalised steering envelope +/- 1.0, with steering preservation inside the envelope. | 载体: postconditions on steer_cmd and checked_cmd.steer_cmd | 元素: F6, F7
- `traceability@L0` [traceability] [F6] Actuation command inside the actuator envelope A-3 / A-6. | 载体: process + postcondition | 元素: F6
- `traceability@L0` [traceability] [F7] Shield output satisfying the envelope even for a violating input; steering preserved unless out of envelope; D4 enforced. | 载体: process + postcondition | 元素: F7
- `traceability@L0` [traceability] [N-7] Partial: no numeric lateral-acceleration capability exists in section 7/8 (see OI-10). | 载体: trajectory.lateral_accel and the A-6 steering envelope | 元素: F5, F6, F7

→ **label** = `___`    **evidence** = ________________________

#### 卡 TH-4 × M3 — M3 LLM 生成 DFD

*Level-0 + Level-1（F3.1/F3.2/F3.3 细化）；部分语义写在过程字典与 README 追溯表里*

候选条款（按相关度排序，请逐条看）：

- `traceability@L1` [traceability] [N-4] CCRm envelope sizing A-1. | 载体: postcondition | 元素: F3.3
- `traceability@L0` [traceability] [N-4] CCRm envelope; sizes A-1. | 载体: postcondition | 元素: F3.3
- `README.md` [文档 L105] | N-4 | F3.3 | CCRm envelope |
- `M3_process_dictionary.md` [文档 L190] deceleration at least `$A_emergency = 6.0` m/s² (A-1, sized from N-3/N-4) and
- `F3.3@L1` [postcondition] risk_level = 0 and driver_intent.accelerate = 1 -> manoeuvre.target_speed >= driver_intent.requested_speed
- `F3.3@L1` [postcondition] risk_level = 1 and driver_intent.accelerate = 1 -> manoeuvre.target_speed >= driver_intent.requested_speed
- `traceability@L0` [traceability] [A-4] Lateral / yaw-rate envelope 3.5 rad/s. | 载体: invariant | 元素: F1, F6
- `traceability@L0` [traceability] [A-6] Steering envelope +/-1.0. | 载体: postcondition | 元素: F6, F7
- `traceability@L0` [traceability] [N-7] Euclidean lateral envelope. | 载体: invariant | 元素: F5, F7, F1
- `README.md` [文档 L108] | N-7 | F5, F7, F1 | Euclidean lateral envelope |
- `M3_process_dictionary.md` [文档 L111] envelope: comfort longitudinal limit 3.0 m/s² (A-3), steering ±1.0 (A-6),
- `F3.3@L1` [postcondition] risk_level = 2 -> manoeuvre.type = 2 and manoeuvre.required_decel >= 6.0 and manoeuvre.target_speed = 0
- `README.md` [文档 L112] | A-4 | F1, F6 | 3.5 rad/s yaw-rate envelope |
- `README.md` [文档 L114] | A-6 | F6, F7 | +/-1.0 steering envelope |
- `M3_process_dictionary.md` [文档 L129] safety envelope even when F6's command violates it; preserve F6's steering
- `M3_process_dictionary.md` [文档 L130] unless it violates the envelope (the four guards above encode "preserve unless

→ **label** = `___`    **evidence** = ________________________

#### 卡 TH-4 × M4 — M4 LLM 生成 UML 类图/顺序图

*Level-0 + Level-1（三个类细化）；阈值追溯表在 M4_constraints.md*

候选条款（按相关度排序，请逐条看）：

- `traceability@L0` [traceability] [N-4] The CCRm envelope (VUT 60-130 km/h, target 20 km/h, target decelerating at -4 m/s2) is the sizing basis of A-1 and is realised by C-F3-4 and C-F5-5. | 载体: derivation of A-1 | 元素: F3, F5
- `M4_constraints.md` [文档 L172] | N-4 | CCRm：VUT 60–130 km/h，目标 20 km/h，目标 −4 m/s² | C-F3-4 / C-F5-5（A-1 的推导前提，追溯于 F3.3、F6） |
- `M4_constraints.md` [文档 L49] | C-F3-4 | post（guard `risk_level = 'critical'`） | `required_decel_ms2 >= 6.0 and target_speed_kmh = 0.0` | **A-1**（由 N-3/N-4 推导） |
- `F3.3@L1` [invariant] driver_accel_request = 'true' and risk_level = 'critical' | required_decel_ms2 >= 6.0 and target_speed_kmh = 0.0
- `F3@L0` [invariant] risk_level = 'critical' | required_decel_ms2 >= 6.0 and target_speed_kmh = 0.0
- `F3.3@L1` [invariant] risk_level = 'critical' | required_decel_ms2 >= 6.0 and target_speed_kmh = 0.0
- `F3@L0` [invariant] target_speed_kmh <= speed_limit_kmh
- `traceability@L0` [traceability] [A-3] Comfortable longitudinal acceleration limit of 3.0 m/s2, applied to the acceleration side of the envelope (OI-7). | 载体: invariants C-F6-2, C-F7-2, C-E9-1 | 元素: F6, F7, E9
- `traceability@L0` [traceability] [A-4] Yaw-rate envelope of 3.5 rad/s as a sanity envelope on the localisation output. | 载体: invariants C-F1-5 and C-D3-2 | 元素: F1, D3
- `traceability@L0` [traceability] [A-6] Steering command envelope of +/- 1.0 (normalised). | 载体: invariants C-F6-3, C-F7-4, C-E8-1, C-E9-2 | 元素: F6, F7, E8, E9
- `traceability@L0` [traceability] [F6] Actuation command inside the actuator envelope (A-3, A-6, A-1). | 载体: class + constraints C-F6-1 .. C-F6-4 | 元素: F6
- `traceability@L0` [traceability] [F7] Arbitration to the safety envelope, steering preservation, traffic-rule enforcement. | 载体: class + constraints C-F7-1 .. C-F7-10 | 元素: F7
- `traceability@L0` [traceability] [N-7] Lateral-acceleration envelope of the trajectory; no numeric value is given in sections 7/8 (OI-8). | 载体: invariant C-F5-6 | 元素: F5
- `F3.3@L1` [postcondition] driver_accel_request = 'true' and risk_level = 'critical' -> required_decel_ms2 >= 6.0 and target_speed_kmh = 0.0
- `F3@L0` [postcondition] manoeuvre_type <> '' and target_speed_kmh >= 0.0 and target_lane_id <> ''
- `F3@L0` [postcondition] risk_level = 'critical' -> required_decel_ms2 >= 6.0 and target_speed_kmh = 0.0

→ **label** = `___`    **evidence** = ________________________

#### 卡 TH-4 × M5 — M5 LLM 生成 UML 状态机

*Level-1（AEB 状态机），约束写在状态迁移标签上*

候选条款（按相关度排序，请逐条看）：

- `traceability@L1` [traceability] [N-4] Worst-case CCRm basis for A-1. | 载体: invariant | 元素: EmergencyBrake
- `Standstill@L1` [invariant] checked_cmd.target_speed = 0
- `EmergencyBrake@L1` [invariant] maneuver = emergency_deceleration and maneuver.deceleration >= 6.0 and maneuver.target_speed = 0
- `T27@L1` [postcondition] checked_cmd.target_speed = 0 and checked_cmd.brake = active
- `T20@L1` [postcondition] warning = imminent_collision and maneuver = emergency_deceleration and maneuver.deceleration >= 6.0 and maneuver.target_speed = 0
- `T3@L1` [postcondition] warning = imminent_collision and maneuver = emergency_deceleration and maneuver.deceleration >= 6.0 and maneuver.target_speed = 0 and checked_cmd.deceleration >= 6.0
- `T13@L1` [postcondition] warning = imminent_collision and maneuver = emergency_deceleration and maneuver.deceleration >= 6.0 and maneuver.target_speed = 0 and checked_cmd.deceleration >= 6.0

→ **label** = `___`    **evidence** = ________________________

### 需求 TH-5 —— 保持 RSS 纵向安全距离 d_min，采用集成方定义参数集

来源条款：N-5 / A-2

规格来源条款编号：`N-5 / A-2`（模型若在追溯表或文档表格里标注了这个编号，说明它自称实现了该条款 —— 请一并考虑）

**本需求的要素分解**（2 个要素，来自规格原文；请把每个要素逐个对到模型条款上）：

- 要素 a：保持 RSS 纵向安全距离 d_min（作为可判定的约束写出，而非仅定性提及）
- 要素 b：采用集成方定义的 RSS 参数集（ρ = 0.1 s、a_max,accel = 2.0、a_max,brake = 4.0、a_min,brake = 4.0）

→ 2 个要素全部写出 = `1`；写出一部分 = `0.5`；一个都没写出 = `0`

#### 卡 TH-5 × M1 — M1 人工 SOFL（原始版）

*Level-0（整车）+ Level-1（AEB 分支：ComputeTTC → ClassifyRisk → PlanManeuver）*

> **候选条款：无。** 该模型中未检索到与本需求相关的条款。
> 若你认为漏检，请翻看原始产物 `models/M1_manual_human/BehaviorPlanning.fModule`。

→ **label** = `___`    **evidence** = ________________________

#### 卡 TH-5 × M1.1 — M1.1 人工 SOFL（补入阈值表）

*Level-0 + Level-1，AEB 分支已补入阈值表*

候选条款（按相关度排序，请逐条看）：

- `traceability@L0` [traceability] [A-2] RSS parameter set rho = 0.1 s, a_max,accel = 2.0, a_max,brake = 4.0, a_min,brake = 4.0. | 载体: A-2 parameter values 4.0 / 2.0 in the braking profile | 元素: Motion_Planning, Control, Safety_Shield
- `traceability@L1` [traceability] [A-2] RSS parameter set rho = 0.1 s, a_max,accel = 2.0, a_max,brake = 4.0, a_min,brake = 4.0. | 载体: A-2 parameter values 4.0 / 2.0 in the braking profile | 元素: Motion_Planning, Control, Safety_Shield
- `traceability@L0` [traceability] [N-5] RSS longitudinal safe distance d_min, with A-2 parameters; realised as a maintained minimum gap on the predicted lead. | 载体: trajectory.min_gap<=predicted_trajectories.lead_gap | 元素: Prediction, Motion_Planning
- `traceability@L1` [traceability] [N-5] RSS longitudinal safe distance d_min, with A-2 parameters; realised as a maintained minimum gap on the predicted lead. | 载体: trajectory.min_gap<=predicted_trajectories.lead_gap | 元素: Prediction, Motion_Planning
- `Motion_Planning@L0` [postcondition] predicted_trajectories.lead_gap>=0 -> trajectory.min_gap<=predicted_trajectories.lead_gap
- `Motion_Planning@L0` [postcondition] trajectory.min_gap>=0
- `traceability@L0` [traceability] [A-3] Comfortable longitudinal acceleration limit 3.0 m/s2. | 载体: accel_cmd<=3.0 | 元素: Control, Safety_Shield
- `traceability@L1` [traceability] [A-3] Comfortable longitudinal acceleration limit 3.0 m/s2. | 载体: accel_cmd<=3.0 | 元素: Control, Safety_Shield
- `traceability@L0` [traceability] [N-6] RSS braking profile: at least a_min,brake = 4.0, and no longitudinal acceleration above a_max,accel = 2.0. | 载体: trajectory.decel_limit>=4.0 / brake_cmd>=decel_limit / accel_cmd<=2.0 | 元素: Motion_Planning, Control, Safety_Shield
- `traceability@L1` [traceability] [N-6] RSS braking profile: at least a_min,brake = 4.0, and no longitudinal acceleration above a_max,accel = 2.0. | 载体: trajectory.decel_limit>=4.0 / brake_cmd>=decel_limit / accel_cmd<=2.0 | 元素: Motion_Planning, Control, Safety_Shield

→ **label** = `___`    **evidence** = ________________________

#### 卡 TH-5 × M2 — M2 LLM 生成 SOFL

*Level-0（ADAS_System）+ Level-1（AEB_Branch）*

候选条款（按相关度排序，请逐条看）：

- `traceability@L0` [traceability] [A-2] a_max,accel = 2.0 and a_min,brake = a_max,brake = 4.0; rho = 0.1 s not formalised (see OI-13). | 载体: postconditions trajectory.max_accel <= 2.0 and trajectory.decel_limit >= 4.0 | 元素: F5
- `traceability@L0` [traceability] [N-5] Partial: the RSS parameter set (A-2) is applied, but the spec does not restate the d_min closed form (see OI-9). | 载体: postcondition trajectory.min_gap >= 0 and trajectory.decel_limit >= 4.0 | 元素: F5
- `traceability@L1` [traceability] [N-5] The RSS safe distance has no closed form in the spec; the emergency deceleration covers the dangerous case, the formal distance bound remains open (see OI-9). | 载体: qualitative postcondition on the manoeuvre | 元素: F3.3
- `F2@L0` [postcondition] predicted_trajectories.lead_gap >= 0
- `F5@L0` [postcondition] trajectory.min_gap >= 0
- `traceability@L0` [traceability] [A-3] Longitudinal actuation envelope 3.0 m/s^2 in F6 and F7. | 载体: postconditions on long_accel_cmd and checked_cmd | 元素: F6, F7
- `traceability@L0` [traceability] [N-4] The CCRb -4 m/s^2 target deceleration is realised as the RSS braking capability 4.0 m/s^2; the 60-130 km/h VUT window and the 20 km/h target speed are assessment-scenario parameters with no runtime element (see OI-14). | 载体: postcondition trajectory.decel_limit >= 4.0 | 元素: F5, F3

→ **label** = `___`    **evidence** = ________________________

#### 卡 TH-5 × M3 — M3 LLM 生成 DFD

*Level-0 + Level-1（F3.1/F3.2/F3.3 细化）；部分语义写在过程字典与 README 追溯表里*

候选条款（按相关度排序，请逐条看）：

- `traceability@L0` [traceability] [A-2] RSS parameter set. | 载体: postcondition | 元素: F5, F7
- `traceability@L0` [traceability] [N-5] RSS minimum safe distance. | 载体: postcondition | 元素: F5
- `README.md` [文档 L106] | N-5 | F5 | RSS minimum safe distance |
- `README.md` [文档 L110] | A-2 | F5, F7 | RSS parameter set |
- `M3_process_dictionary.md` [文档 L135] * **quantified:** true (3.0 from A-3, 1.0 from A-6, 4.0/2.0/0.1 from A-2/N-6)
- `M3_process_dictionary.md` [文档 L96] deceleration requirement; respect the RSS longitudinal safe distance (N-5) with
- `F6@L0` [postcondition] actuator_cmd.longitudinal_accel <= 3.0 and actuator_cmd.steering <= 1.0 and actuator_cmd.steering >= -1.0
- `F7@L0` [postcondition] checked_cmd.longitudinal_accel <= 3.0 and checked_cmd.brake >= 0
- `traceability@L0` [traceability] [A-3] Comfort longitudinal limit 3.0. | 载体: postcondition | 元素: F6, F7
- `traceability@L0` [traceability] [N-6] RSS braking profile. | 载体: postcondition | 元素: F6, F7
- `M3_process_dictionary.md` [文档 L97] A-2 parameters (`rho = 0.1`, `a_max_accel = 2.0`, `a_max_brake = 4.0`,
- `M3_process_dictionary.md` [文档 L108] - guard `true` → `actuator_cmd.longitudinal_accel <= 3.0 and actuator_cmd.steering <= 1.0 and actuator_cmd.steering >= -1.0`
- `M3_process_dictionary.md` [文档 L110] (longitudinal acceleration, brake, steering). Keep commands inside the actuator
- `M3_process_dictionary.md` [文档 L111] envelope: comfort longitudinal limit 3.0 m/s² (A-3), steering ±1.0 (A-6),
- `README.md` [文档 L111] | A-3 | F6, F7 | 3.0 m/s2 longitudinal limit |
- `M3_process_dictionary.md` [文档 L124] - guard `true` → `checked_cmd.longitudinal_accel <= 3.0 and checked_cmd.brake >= 0`

→ **label** = `___`    **evidence** = ________________________

#### 卡 TH-5 × M4 — M4 LLM 生成 UML 类图/顺序图

*Level-0 + Level-1（三个类细化）；阈值追溯表在 M4_constraints.md*

候选条款（按相关度排序，请逐条看）：

- `traceability@L0` [traceability] [A-2] RSS parameter set: rho = 0.1 s, a_max,accel = 2.0, a_max,brake = 4.0, a_min,brake = 4.0. | 载体: invariants C-F7-6, C-F7-7, C-F3-11 | 元素: F7, F3
- `traceability@L0` [traceability] [N-5] d_min is computed with the A-2 parameter set; the spec names no enforcing function (OI-13). | 载体: invariant C-F3-11 | 元素: F3
- `M4_constraints.md` [文档 L173] | N-5 | RSS 纵向安全距离 `d_min` | C-F3-11（强制方未指定 → OI-9） |
- `M4_constraints.md` [文档 L177] | A-2 | ρ=0.1, a_max,accel=2.0, a_max,brake=4.0, a_min,brake=4.0 | C-F7-6, C-F7-7, C-F3-11 |
- `F3@L0` [invariant] gap_to_lead_m >= d_min_rss_m
- `F3@L0` [postcondition] gap_to_lead_m >= d_min_rss_m
- `traceability@L0` [traceability] [A-3] Comfortable longitudinal acceleration limit of 3.0 m/s2, applied to the acceleration side of the envelope (OI-7). | 载体: invariants C-F6-2, C-F7-2, C-E9-1 | 元素: F6, F7, E9
- `traceability@L0` [traceability] [N-6] Braking with at least a_min,brake during a dangerous situation and no longitudinal acceleration above a_max,accel during the response time rho. | 载体: invariants C-F7-6 and C-F7-7 | 元素: F7
- `M4_constraints.md` [文档 L56] | C-F3-11 | post | `gap_to_lead_m >= d_min_rss_m` | **N-5**（`d_min_rss_m` 按 N-5 / A-2 参数集计算；强制方未指定，见 OI-13） |
- `M4_constraints.md` [文档 L95] | C-F7-6 | post（guard `dangerous_situation = 'true'`） | `checked_brake_cmd_ms2 >= 4.0` | **N-6**（`a_min,brake`）, **A-2** |
- `M4_constraints.md` [文档 L96] | C-F7-7 | post（guard `response_time_s <= 0.1`） | `checked_accel_cmd_ms2 <= 2.0` | **N-6**（`ρ`、`a_max,accel`）, **A-2** |
- `M4_constraints.md` [文档 L174] | N-6 | RSS 制动曲线（`a_min,brake`，`a_max,accel`，`ρ`） | C-F7-6, C-F7-7 |

→ **label** = `___`    **evidence** = ________________________

#### 卡 TH-5 × M5 — M5 LLM 生成 UML 状态机

*Level-1（AEB 状态机），约束写在状态迁移标签上*

> **候选条款：无。** 该模型中未检索到与本需求相关的条款。
> 若你认为漏检，请翻看原始产物 `models/M5_AI_StateMachine/M5_AEB_statechart.puml`。

→ **label** = `___`    **evidence** = ________________________

### 需求 TH-6 —— 危险持续期间至少以 a_min,brake 制动，响应时间内不超过 a_max,accel

来源条款：N-6

规格来源条款编号：`N-6`（模型若在追溯表或文档表格里标注了这个编号，说明它自称实现了该条款 —— 请一并考虑）

**本需求的要素分解**（2 个要素，来自规格原文；请把每个要素逐个对到模型条款上）：

- 要素 a：危险持续期间的制动减速度下限 ≥ a_min,brake（= 4.0 m/s²）
- 要素 b：响应时间内的加速度上限 ≤ a_max,accel（= 2.0 m/s²）

→ 2 个要素全部写出 = `1`；写出一部分 = `0.5`；一个都没写出 = `0`

#### 卡 TH-6 × M1 — M1 人工 SOFL（原始版）

*Level-0（整车）+ Level-1（AEB 分支：ComputeTTC → ClassifyRisk → PlanManeuver）*

候选条款（按相关度排序，请逐条看）：

- `traceability@L0` [traceability] [N-6] threshold 0.5 appears in the validated fModule | 载体: threshold in postconditions | 元素: 
- `Control@L0` [postcondition] actuator_cmd.accel_cmd<=3.0 and actuator_cmd.brake_cmd>=0 and actuator_cmd.steer_cmd>-1.0 and actuator_cmd.steer_cmd<1.0
- `Safety_Shield@L0` [postcondition] actuator_cmd.accel_cmd>3.0 -> checked_cmd.accel_cmd<=3.0
- `Safety_Shield@L0` [postcondition] checked_cmd.steer_cmd=actuator_cmd.steer_cmd and checked_cmd.accel_cmd<=3.0 and checked_cmd.brake_cmd>=0 and checked_cmd.steer_cmd>-1.0 and checked_cmd.steer_cmd<1.0
- `Motion_Planning@L0` [postcondition] maneuver.maneuver_type=3 -> trajectory.max_accel<=-6.0
- `Behavior_Planning@L0` [postcondition] predicted_trajectories.min_ttc<1.5 -> maneuver.maneuver_type=3 and maneuver.decel_req>=6.0 and warning.warn_active=1
- `PlanManeuver@L1` [postcondition] risk_level.risk_type=1 -> maneuver.maneuver_type=2 and maneuver.decel_req>0
- `PlanManeuver@L1` [postcondition] risk_level.risk_type=2 -> maneuver.maneuver_type=3 and maneuver.decel_req>=6.0 and maneuver.target_speed=0
- `Safety_Shield@L0` [postcondition] traffic_rules.red_light=1 -> checked_cmd.brake_cmd>=0.5

→ **label** = `___`    **evidence** = ________________________

#### 卡 TH-6 × M1.1 — M1.1 人工 SOFL（补入阈值表）

*Level-0 + Level-1，AEB 分支已补入阈值表*

候选条款（按相关度排序，请逐条看）：

- `traceability@L0` [traceability] [N-6] RSS braking profile: at least a_min,brake = 4.0, and no longitudinal acceleration above a_max,accel = 2.0. | 载体: trajectory.decel_limit>=4.0 / brake_cmd>=decel_limit / accel_cmd<=2.0 | 元素: Motion_Planning, Control, Safety_Shield
- `traceability@L1` [traceability] [N-6] RSS braking profile: at least a_min,brake = 4.0, and no longitudinal acceleration above a_max,accel = 2.0. | 载体: trajectory.decel_limit>=4.0 / brake_cmd>=decel_limit / accel_cmd<=2.0 | 元素: Motion_Planning, Control, Safety_Shield
- `Control@L0` [postcondition] actuator_cmd.accel_cmd>0 -> actuator_cmd.accel_cmd<=2.0
- `Safety_Shield@L0` [postcondition] actuator_cmd.accel_cmd>0 -> checked_cmd.accel_cmd<=2.0
- `Safety_Shield@L0` [postcondition] actuator_cmd.brake_cmd>0 -> checked_cmd.brake_cmd>=4.0
- `Motion_Planning@L0` [postcondition] trajectory.decel_limit>=4.0
- `traceability@L0` [traceability] [A-2] RSS parameter set rho = 0.1 s, a_max,accel = 2.0, a_max,brake = 4.0, a_min,brake = 4.0. | 载体: A-2 parameter values 4.0 / 2.0 in the braking profile | 元素: Motion_Planning, Control, Safety_Shield
- `traceability@L1` [traceability] [A-2] RSS parameter set rho = 0.1 s, a_max,accel = 2.0, a_max,brake = 4.0, a_min,brake = 4.0. | 载体: A-2 parameter values 4.0 / 2.0 in the braking profile | 元素: Motion_Planning, Control, Safety_Shield
- `traceability@L0` [traceability] [N-2] Forward-collision warning present no later than TTC = 2.0 s (N-2). | 载体: postcondition min_ttc<=1.5 -> warning.warn_active=1 | 元素: ClassifyRisk
- `traceability@L1` [traceability] [N-2] Forward-collision warning present no later than TTC = 2.0 s (N-2). | 载体: postcondition min_ttc<=1.5 -> warning.warn_active=1 | 元素: ClassifyRisk
- `Control@L0` [postcondition] actuator_cmd.accel_cmd<=3.0 and actuator_cmd.brake_cmd>=0 and actuator_cmd.steer_cmd>-1.0 and actuator_cmd.steer_cmd<1.0
- `Motion_Planning@L0` [postcondition] maneuver.maneuver_type=3 -> trajectory.max_accel<=-6.0
- `Behavior_Planning@L0` [postcondition] predicted_trajectories.min_ttc<1.5 -> maneuver.maneuver_type=3 and maneuver.decel_req>=6.0 and warning.warn_active=1
- `PlanManeuver@L1` [postcondition] risk_level.risk_type=1 -> maneuver.maneuver_type=2 and maneuver.decel_req>0
- `PlanManeuver@L1` [postcondition] risk_level.risk_type=2 -> maneuver.maneuver_type=3 and maneuver.decel_req>=6.0 and maneuver.target_speed=0
- `traceability@L0` [traceability] [A-1] Emergency deceleration 6.0 m/s2, target speed 0, not overridable by a driver acceleration request. | 载体: postcondition decel_req>=6.0 | 元素: PlanManeuver

→ **label** = `___`    **evidence** = ________________________

#### 卡 TH-6 × M2 — M2 LLM 生成 SOFL

*Level-0（ADAS_System）+ Level-1（AEB_Branch）*

候选条款（按相关度排序，请逐条看）：

- `traceability@L1` [traceability] [N-6] The braking profile is covered by A-1 >= a_min,brake = 4.0; the response time rho = 0.1 s is not formalised (see OI-13). | 载体: postcondition manoeuvre.required_decel >= 6.0 | 元素: F3.3
- `traceability@L0` [traceability] [N-6] a_max,accel and a_min,brake from A-2; the response time rho = 0.1 s cannot be expressed (no timing construct, see OI-13). | 载体: postconditions trajectory.max_accel <= 2.0 and trajectory.decel_limit >= 4.0 | 元素: F5
- `F5@L0` [invariant] trajectory.decel_limit >= 4.0 (A-2 a_min,brake = a_max,brake / N-6)
- `F5@L0` [invariant] trajectory.max_accel <= 2.0 (A-2 a_max,accel / N-6)
- `F3.2@L1` [invariant] warning.active = 1 whenever ttc_set.min_ttc <= 2.0 s (N-2 warning present no later than the 2.0 s staging point)
- `F3.2@L1` [postcondition] ttc_set.obj_count > 0 and ttc_set.min_ttc <= 2.0 -> warning.active = 1
- `traceability@L0` [traceability] [A-2] a_max,accel = 2.0 and a_min,brake = a_max,brake = 4.0; rho = 0.1 s not formalised (see OI-13). | 载体: postconditions trajectory.max_accel <= 2.0 and trajectory.decel_limit >= 4.0 | 元素: F5
- `traceability@L1` [traceability] [N-2] Warning raised at TTC <= 2.0 s and at latest at the 2.0 s staging point; T_fcw = 1.5 s. | 载体: postconditions on warning.active | 元素: F3.2
- `traceability@L0` [traceability] [N-2] Warning raised at TTC <= 3.0 s and in particular at TTC <= 2.0 s, i.e. no later than the 2.0 s cut-out staging point; T_fcw = 1.5 s (A-5). | 载体: postcondition of the Level-1 Risk_Classification | 元素: F3
- `traceability@L0` [traceability] [N-4] The CCRb -4 m/s^2 target deceleration is realised as the RSS braking capability 4.0 m/s^2; the 60-130 km/h VUT window and the 20 km/h target speed are assessment-scenario parameters with no runtime element (see OI-14). | 载体: postcondition trajectory.decel_limit >= 4.0 | 元素: F5, F3
- `traceability@L0` [traceability] [N-5] Partial: the RSS parameter set (A-2) is applied, but the spec does not restate the d_min closed form (see OI-9). | 载体: postcondition trajectory.min_gap >= 0 and trajectory.decel_limit >= 4.0 | 元素: F5
- `F3.3@L1` [invariant] For the critical risk level the required deceleration is at least 6.0 m/s^2 and the target speed is 0 (A-1).
- `F6@L0` [invariant] actuator_cmd.long_accel_cmd <= 3.0 and actuator_cmd.long_accel_cmd >= -3.0 (A-3)
- `F7@L0` [invariant] checked_cmd.long_accel_cmd <= 3.0 and checked_cmd.long_accel_cmd >= -3.0 (A-3)
- `F7@L0` [postcondition] Ego_State_DB.speed >= Traffic_Rules_DB.posted_speed_limit and actuator_cmd.long_accel_cmd > 0 -> checked_cmd.long_accel_cmd <= 0
- `F6@L0` [postcondition] actuator_cmd.brake_cmd >= 0

→ **label** = `___`    **evidence** = ________________________

#### 卡 TH-6 × M3 — M3 LLM 生成 DFD

*Level-0 + Level-1（F3.1/F3.2/F3.3 细化）；部分语义写在过程字典与 README 追溯表里*

候选条款（按相关度排序，请逐条看）：

- `traceability@L0` [traceability] [N-6] RSS braking profile. | 载体: postcondition | 元素: F6, F7
- `README.md` [文档 L107] | N-6 | F6, F7 | RSS braking profile |
- `M3_process_dictionary.md` [文档 L132] enforce RSS braking profile (N-6: at least `a_min_brake = 4.0`, no acceleration
- `M3_process_dictionary.md` [文档 L135] * **quantified:** true (3.0 from A-3, 1.0 from A-6, 4.0/2.0/0.1 from A-2/N-6)
- `README.md` [文档 L151] envelope (A-3/A-6, N-6/N-7), which is equally safety-critical yet left unmandated
- `traceability@L1` [traceability] [N-2] Warning no later than TTC = 2.0 s. | 载体: postcondition | 元素: F3.2
- `traceability@L0` [traceability] [N-2] Warning no later than TTC = 2.0 s; child F3.2. | 载体: postcondition | 元素: F3.2
- `F6@L0` [postcondition] actuator_cmd.longitudinal_accel <= 3.0 and actuator_cmd.steering <= 1.0 and actuator_cmd.steering >= -1.0
- `F7@L0` [postcondition] checked_cmd.longitudinal_accel <= 3.0 and checked_cmd.brake >= 0
- `F3.3@L1` [postcondition] risk_level = 0 and driver_intent.accelerate = 1 -> manoeuvre.target_speed >= driver_intent.requested_speed
- `F3.3@L1` [postcondition] risk_level = 1 -> manoeuvre.type = 1 and manoeuvre.required_decel > 0
- `F5@L0` [postcondition] trajectory.max_speed <= traffic_rules.speed_limit and trajectory.max_accel <= 3.0 and trajectory.required_decel >= manoeuvre.required_decel
- `F6@L0` [precondition] trajectory.max_accel <= 3.0
- `traceability@L0` [traceability] [A-1] Emergency deceleration 6.0 m/s2. | 载体: postcondition | 元素: F3.3
- `traceability@L1` [traceability] [A-1] Emergency deceleration 6.0 m/s2. | 载体: postcondition | 元素: F3.3
- `traceability@L0` [traceability] [N-3] Impact-speed reduction; sizes emergency deceleration A-1. | 载体: postcondition | 元素: F3.3

→ **label** = `___`    **evidence** = ________________________

#### 卡 TH-6 × M4 — M4 LLM 生成 UML 类图/顺序图

*Level-0 + Level-1（三个类细化）；阈值追溯表在 M4_constraints.md*

候选条款（按相关度排序，请逐条看）：

- `traceability@L0` [traceability] [N-6] Braking with at least a_min,brake during a dangerous situation and no longitudinal acceleration above a_max,accel during the response time rho. | 载体: invariants C-F7-6 and C-F7-7 | 元素: F7
- `M4_constraints.md` [文档 L174] | N-6 | RSS 制动曲线（`a_min,brake`，`a_max,accel`，`ρ`） | C-F7-6, C-F7-7 |
- `M4_constraints.md` [文档 L95] | C-F7-6 | post（guard `dangerous_situation = 'true'`） | `checked_brake_cmd_ms2 >= 4.0` | **N-6**（`a_min,brake`）, **A-2** |
- `F7@L0` [invariant] dangerous_situation = 'true' | checked_brake_cmd_ms2 >= 4.0
- `F7@L0` [invariant] response_time_s <= 0.1 | checked_accel_cmd_ms2 <= 2.0
- `F3@L0` [invariant] ttc_min_s <= 2.0 | warning_type <> 'none'
- `F3.2@L1` [invariant] ttc_min_s <= 2.0 | warning_type <> 'none'
- `F3@L0` [postcondition] ttc_min_s <= 2.0 -> warning_type <> 'none'
- `F3.2@L1` [postcondition] ttc_min_s <= 2.0 -> warning_type <> 'none'
- `traceability@L0` [traceability] [A-2] RSS parameter set: rho = 0.1 s, a_max,accel = 2.0, a_max,brake = 4.0, a_min,brake = 4.0. | 载体: invariants C-F7-6, C-F7-7, C-F3-11 | 元素: F7, F3
- `traceability@L0` [traceability] [N-2] A warning must be present no later than TTC = 2.0 s. | 载体: invariant C-F3-6 | 元素: F3
- `traceability@L1` [traceability] [N-2] A warning must be present no later than TTC = 2.0 s. | 载体: invariant C-L1-6 | 元素: F3.2
- `F6@L0` [invariant] accel_cmd_ms2 <= 3.0 and accel_cmd_ms2 >= -6.0
- `F6@L0` [invariant] brake_cmd_ms2 >= 0.0 and brake_cmd_ms2 <= 6.0
- `F5@L0` [invariant] commanded_lateral_accel_ms2 <= a_lat_max_ms2
- `F3.3@L1` [invariant] driver_accel_request = 'true' and risk_level <> 'critical' | manoeuvre_type <> 'emergency_deceleration' and required_decel_ms2 >= 0.0

→ **label** = `___`    **evidence** = ________________________

#### 卡 TH-6 × M5 — M5 LLM 生成 UML 状态机

*Level-1（AEB 状态机），约束写在状态迁移标签上*

候选条款（按相关度排序，请逐条看）：

- `traceability@L1` [traceability] [N-2] Warning issued at TTC 1.5 s, no later than 2.0 s. | 载体: guard | 元素: T3, T10, T13, T20
- `EmergencyBrake@L1` [invariant] checked_cmd.deceleration >= 6.0
- `DriverOverride@L1` [invariant] driver_accel_request = true
- `Caution@L1` [invariant] maneuver = deceleration and maneuver.deceleration > 0
- `DriverOverride@L1` [invariant] maneuver = driver_accelerate
- `EmergencyBrake@L1` [invariant] maneuver = emergency_deceleration and maneuver.deceleration >= 6.0 and maneuver.target_speed = 0
- `BrakeRamp@L1` [invariant] maneuver.deceleration >= 6.0
- `T27@L1` [postcondition] checked_cmd.target_speed = 0 and checked_cmd.brake = active
- `T12@L1` [postcondition] maneuver = deceleration and warning = caution and maneuver.deceleration > 0
- `T10@L1` [postcondition] maneuver = driver_accelerate and warning = caution
- `T9@L1` [postcondition] maneuver = driver_accelerate and warning = none
- `T15@L1` [postcondition] warning = caution and maneuver = deceleration
- `T1@L1` [postcondition] warning = caution and maneuver = deceleration and maneuver.deceleration > 0
- `T4@L1` [postcondition] warning = caution and maneuver = deceleration and maneuver.deceleration > 0
- `T19@L1` [postcondition] warning = caution and maneuver = deceleration and maneuver.deceleration > 0
- `T16@L1` [postcondition] warning = imminent_collision and maneuver = emergency_deceleration

→ **label** = `___`    **evidence** = ________________________

### 需求 AEB-1 —— F3.1 对每个预测目标计算 TTC，报告最小 TTC 与考虑的目标数量

来源条款：F3.1

规格来源条款编号：`F3.1`（模型若在追溯表或文档表格里标注了这个编号，说明它自称实现了该条款 —— 请一并考虑）

（对照集条目）该需求按**整体**判定：模型里有条款表达其语义 → `1`；完全没有 → `0`。

#### 卡 AEB-1 × M1 — M1 人工 SOFL（原始版）（可选）

*Level-0（整车）+ Level-1（AEB 分支：ComputeTTC → ClassifyRisk → PlanManeuver）*

候选条款（按相关度排序，请逐条看）：

- `ComputeTTC@L1` [postcondition] predicted_trajectories.count=0 -> ttc_values.count=0
- `ComputeTTC@L1` [postcondition] predicted_trajectories.count>0 -> ttc_values.count=predicted_trajectories.count and ttc_values.min_ttc<=predicted_trajectories.min_ttc
- `Behavior_Planning@L0` [postcondition] predicted_trajectories.min_ttc<1.5 -> maneuver.maneuver_type=3 and maneuver.decel_req>=6.0 and warning.warn_active=1
- `Behavior_Planning@L0` [postcondition] predicted_trajectories.min_ttc>=1.5 -> maneuver.maneuver_type<>3
- `ClassifyRisk@L1` [postcondition] ttc_values.min_ttc<=1.5 -> risk_level.risk_type=2 and warning.warn_active=1
- `ClassifyRisk@L1` [postcondition] ttc_values.min_ttc<=3.0 and ttc_values.min_ttc>1.5 -> risk_level.risk_type=1 and warning.warn_active=1
- `traceability@L1` [traceability] [F-ComputeTTC] pre/post in fModule; clause realisation verified by validate_sofl_model.py | 载体: process contract | 元素: ComputeTTC
- `ClassifyRisk@L1` [postcondition] ttc_values.min_ttc>3.0 -> risk_level.risk_type=0 and warning.warn_active=0

→ **label** = `___`    **evidence** = ________________________

#### 卡 AEB-1 × M3 — M3 LLM 生成 DFD（可选）

*Level-0 + Level-1（F3.1/F3.2/F3.3 细化）；部分语义写在过程字典与 README 追溯表里*

候选条款（按相关度排序，请逐条看）：

- `traceability@L1` [traceability] [F3.1]  | 载体: process | 元素: F3.1
- `README.md` [文档 L115] | A-7 | F2, F3.1 | 3.0 s prediction horizon |
- `README.md` [文档 L12] | `M3_L1.dot` | Level 1 DFD (F3 refined into F3.1/F3.2/F3.3) |
- `M3_process_dictionary.md` [文档 L141] ### 3.1 / F3.1 — TTC Computation
- `M3_process_dictionary.md` [文档 L156] * **Inputs:** `ttc_set` (F3.1), `traffic_rules` (D4 read).
- `F3.1@L1` [postcondition] ttc_set.count = 0 -> ttc_set.min_ttc = 0
- `F3.2@L1` [postcondition] ttc_set.min_ttc <= 1.5 -> risk_level = 2 and warning.active = 1 and warning.type = 2
- `F3.2@L1` [postcondition] ttc_set.min_ttc <= 3.0 and ttc_set.min_ttc > 1.5 -> risk_level = 1 and warning.active = 1 and warning.type = 1
- `traceability@L1` [traceability] [N-2] Warning no later than TTC = 2.0 s. | 载体: postcondition | 元素: F3.2
- `traceability@L0` [traceability] [N-2] Warning no later than TTC = 2.0 s; child F3.2. | 载体: postcondition | 元素: F3.2
- `README.md` [文档 L140] period. Without a bound on the F2->F3.1->F3.2->F3.3->F5->F6->F7 latency, the
- `README.md` [文档 L41] 8. **F3 ego_state:** modelled as `F1 -> F3` (and split to F3.1/F3.3 at Level 1)
- `README.md` [文档 L48] | IN `predicted_trajectories` (F2) | -> F3.1 |
- `README.md` [文档 L49] | IN `ego_state` (F1) | -> F3.1 and -> F3.3 |
- `README.md` [文档 L66] | R-SCOPE-4 | F3, F3.1, F3.2, F3.3 | two-level split |
- `README.md` [文档 L72] | R-L1-1 | F3.1, F3.2, F3.3 | three sub-processes |

→ **label** = `___`    **evidence** = ________________________

#### 卡 AEB-1 × M4 — M4 LLM 生成 UML 类图/顺序图（可选）

*Level-0 + Level-1（三个类细化）；阈值追溯表在 M4_constraints.md*

候选条款（按相关度排序，请逐条看）：

- `traceability@L1` [traceability] [F3.1] Minimum TTC over the object set plus the number of objects considered; count 0 for the empty set. | 载体: class + constraints C-L1-1, C-L1-2, C-L1-16, C-L1-19 | 元素: F3.1
- `M4_constraints.md` [文档 L126] ## 10. Level 1 细化（F3.1 / F3.2 / F3.3）
- `M4_constraints.md` [文档 L128] ### F3.1 — TTC Computation
- `F2@L0` [invariant] TTC is computed in F2 only (spec F2); see OI-6 for the conflict with the Level-1 clause F3.1
- `F2@L0` [invariant] min_ttc_s >= 0.0
- `F3.2@L1` [invariant] risk_level = 'caution' | ttc_min_s <= 3.0 and ttc_min_s > 1.5
- `F3.2@L1` [invariant] risk_level = 'critical' | ttc_min_s <= 1.5
- `F3@L0` [invariant] ttc_min_s <= 2.0 | warning_type <> 'none'
- `F3@L0` [postcondition] ttc_min_s <= 2.0 -> warning_type <> 'none'
- `traceability@L1` [traceability] [A-7] The TTC is evaluated over the 3.0 s prediction horizon of F2. | 载体: invariant C-L1-19 | 元素: F3.1
- `traceability@L0` [traceability] [F2] Prediction over at least 3 s, derivation of the minimum TTC, sole TTC owner, no store write. | 载体: class + constraints C-F2-1 .. C-F2-5 | 元素: F2
- `traceability@L1` [traceability] [F3.2] Risk level as a function of the minimum TTC; warning raised for caution and critical only. | 载体: class + constraints C-L1-3 .. C-L1-6, C-L1-13 .. C-L1-17 | 元素: F3.2
- `traceability@L0` [traceability] [N-2] A warning must be present no later than TTC = 2.0 s. | 载体: invariant C-F3-6 | 元素: F3
- `traceability@L1` [traceability] [N-2] A warning must be present no later than TTC = 2.0 s. | 载体: invariant C-L1-6 | 元素: F3.2
- `M4_constraints.md` [文档 L132] | C-L1-16 | pre | `predicted_trajectories <> null and ego_state <> null` | F3.1, R-G-6 |
- `M4_constraints.md` [文档 L133] | C-L1-1 | post | `considered_object_count >= 0 and ttc_min_s >= 0.0` | F3.1, R-G-1 |

→ **label** = `___`    **evidence** = ________________________

### 需求 AEB-3 —— F3.2 按最小 TTC 分三级：TTC>3.0s 无风险、1.5–3.0s 注意、≤1.5s 临界

来源条款：F3.2 / A-5

规格来源条款编号：`F3.2 / A-5`（模型若在追溯表或文档表格里标注了这个编号，说明它自称实现了该条款 —— 请一并考虑）

（对照集条目）该需求按**整体**判定：模型里有条款表达其语义 → `1`；完全没有 → `0`。

#### 卡 AEB-3 × M1 — M1 人工 SOFL（原始版）（可选）

*Level-0（整车）+ Level-1（AEB 分支：ComputeTTC → ClassifyRisk → PlanManeuver）*

候选条款（按相关度排序，请逐条看）：

- `traceability@L0` [traceability] [A-5] threshold 3.0 appears in the validated fModule | 载体: threshold in postconditions | 元素: 
- `traceability@L1` [traceability] [A-5] threshold 3.0 appears in the validated fModule | 载体: threshold in postconditions | 元素: 
- `Control@L0` [postcondition] actuator_cmd.accel_cmd<=3.0 and actuator_cmd.brake_cmd>=0 and actuator_cmd.steer_cmd>-1.0 and actuator_cmd.steer_cmd<1.0
- `Safety_Shield@L0` [postcondition] actuator_cmd.accel_cmd>3.0 -> checked_cmd.accel_cmd<=3.0
- `Safety_Shield@L0` [postcondition] checked_cmd.steer_cmd=actuator_cmd.steer_cmd and checked_cmd.accel_cmd<=3.0 and checked_cmd.brake_cmd>=0 and checked_cmd.steer_cmd>-1.0 and checked_cmd.steer_cmd<1.0
- `PlanManeuver@L1` [postcondition] driver_intent.intent_type=2 and risk_level.risk_type<2 -> maneuver.maneuver_type=1
- `ComputeTTC@L1` [postcondition] predicted_trajectories.count=0 -> ttc_values.count=0
- `ComputeTTC@L1` [postcondition] predicted_trajectories.count>0 -> ttc_values.count=predicted_trajectories.count and ttc_values.min_ttc<=predicted_trajectories.min_ttc
- `Behavior_Planning@L0` [postcondition] predicted_trajectories.min_ttc<1.5 -> maneuver.maneuver_type=3 and maneuver.decel_req>=6.0 and warning.warn_active=1
- `Behavior_Planning@L0` [postcondition] predicted_trajectories.min_ttc>=1.5 -> maneuver.maneuver_type<>3
- `PlanManeuver@L1` [postcondition] risk_level.risk_type=0 -> maneuver.maneuver_type=1 and maneuver.target_speed<=map_data.speed_limit
- `ClassifyRisk@L1` [postcondition] risk_level.risk_value>=0
- `ClassifyRisk@L1` [postcondition] ttc_values.min_ttc<=1.5 -> risk_level.risk_type=2 and warning.warn_active=1
- `traceability@L0` [traceability] [A-3] threshold 3.0 appears in the validated fModule | 载体: threshold in postconditions | 元素: 
- `traceability@L1` [traceability] [A-3] threshold 3.0 appears in the validated fModule | 载体: threshold in postconditions | 元素: 
- `traceability@L1` [traceability] [F-ClassifyRisk] pre/post in fModule; clause realisation verified by validate_sofl_model.py | 载体: process contract | 元素: ClassifyRisk

→ **label** = `___`    **evidence** = ________________________

#### 卡 AEB-3 × M3 — M3 LLM 生成 DFD（可选）

*Level-0 + Level-1（F3.1/F3.2/F3.3 细化）；部分语义写在过程字典与 README 追溯表里*

候选条款（按相关度排序，请逐条看）：

- `traceability@L0` [traceability] [A-5] Risk thresholds 3.0 / 1.5 s. | 载体: postcondition | 元素: F3.2
- `traceability@L1` [traceability] [A-5] Risk thresholds 3.0 / 1.5 s. | 载体: postcondition | 元素: F3.2
- `traceability@L1` [traceability] [F3.2]  | 载体: process | 元素: F3.2
- `README.md` [文档 L100] | F3.2 | 3.2 | Risk Classification |
- `README.md` [文档 L103] | N-2 | F3.2 | warning by TTC = 2.0 s |
- `M3_process_dictionary.md` [文档 L143] * **Outputs:** `ttc_set` → F3.2.
- `M3_process_dictionary.md` [文档 L155] ### 3.2 / F3.2 — Risk Classification
- `F6@L0` [postcondition] actuator_cmd.longitudinal_accel <= 3.0 and actuator_cmd.steering <= 1.0 and actuator_cmd.steering >= -1.0
- `F7@L0` [postcondition] checked_cmd.longitudinal_accel <= 3.0 and checked_cmd.brake >= 0
- `F3.3@L1` [postcondition] risk_level = 0 and driver_intent.accelerate = 1 -> manoeuvre.target_speed >= driver_intent.requested_speed
- `F3.3@L1` [postcondition] risk_level = 1 -> manoeuvre.type = 1 and manoeuvre.required_decel > 0
- `F5@L0` [postcondition] trajectory.max_speed <= traffic_rules.speed_limit and trajectory.max_accel <= 3.0 and trajectory.required_decel >= manoeuvre.required_decel
- `F3.1@L1` [postcondition] ttc_set.count = 0 -> ttc_set.min_ttc = 0
- `F3.2@L1` [postcondition] ttc_set.min_ttc <= 1.5 -> risk_level = 2 and warning.active = 1 and warning.type = 2
- `F3.2@L1` [postcondition] ttc_set.min_ttc <= 3.0 and ttc_set.min_ttc > 1.5 -> risk_level = 1 and warning.active = 1 and warning.type = 1
- `F3.1@L1` [precondition] predicted_trajectories.horizon >= 3.0

→ **label** = `___`    **evidence** = ________________________

#### 卡 AEB-3 × M4 — M4 LLM 生成 UML 类图/顺序图（可选）

*Level-0 + Level-1（三个类细化）；阈值追溯表在 M4_constraints.md*

候选条款（按相关度排序，请逐条看）：

- `traceability@L0` [traceability] [A-5] T_risk_high = 3.0 and T_fcw = 1.5 are applied in the Level-1 refinement of F3. | 载体: risk band thresholds applied in F3.2 (C-L1-3 .. C-L1-5) | 元素: F3
- `traceability@L1` [traceability] [A-5] T_risk_high = 3.0 s and T_fcw = 1.5 s. | 载体: invariants C-L1-3, C-L1-4, C-L1-5 | 元素: F3.2
- `traceability@L1` [traceability] [F3.2] Risk level as a function of the minimum TTC; warning raised for caution and critical only. | 载体: class + constraints C-L1-3 .. C-L1-6, C-L1-13 .. C-L1-17 | 元素: F3.2
- `M4_constraints.md` [文档 L126] ## 10. Level 1 细化（F3.1 / F3.2 / F3.3）
- `M4_constraints.md` [文档 L137] ### F3.2 — Risk Classification
- `F2@L0` [invariant] TTC is computed in F2 only (spec F2); see OI-6 for the conflict with the Level-1 clause F3.1
- `F6@L0` [invariant] accel_cmd_ms2 <= 3.0 and accel_cmd_ms2 >= -6.0
- `F7@L0` [invariant] checked_accel_cmd_ms2 <= 3.0 and checked_accel_cmd_ms2 >= -6.0
- `F3.3@L1` [invariant] driver_accel_request = 'true' and risk_level <> 'critical' | manoeuvre_type <> 'emergency_deceleration' and required_decel_ms2 >= 0.0
- `F3.3@L1` [invariant] driver_accel_request = 'true' and risk_level = 'critical' | required_decel_ms2 >= 6.0 and target_speed_kmh = 0.0
- `F3.1@L1` [invariant] horizon_s >= 3.0
- `F5@L0` [invariant] manoeuvre.risk_level = 'critical' | trajectory_decel_capability_ms2 >= 6.0
- `F2@L0` [invariant] min_ttc_s >= 0.0
- `F7@L0` [invariant] response_time_s <= 0.1 | checked_accel_cmd_ms2 <= 2.0
- `F3.2@L1` [invariant] risk_level = 'caution' | ttc_min_s <= 3.0 and ttc_min_s > 1.5
- `F3@L0` [invariant] risk_level = 'critical' | ego_speed_kmh <= 130.0

→ **label** = `___`    **evidence** = ________________________

### 需求 EXT-3 —— E3 driver_intent：驾驶员指令与 ODD 状态、注意力状态输入

来源条款：E3

规格来源条款编号：`E3`（模型若在追溯表或文档表格里标注了这个编号，说明它自称实现了该条款 —— 请一并考虑）

（对照集条目）该需求按**整体**判定：模型里有条款表达其语义 → `1`；完全没有 → `0`。

#### 卡 EXT-3 × M1 — M1 人工 SOFL（原始版）（可选）

*Level-0（整车）+ Level-1（AEB 分支：ComputeTTC → ClassifyRisk → PlanManeuver）*

候选条款（按相关度排序，请逐条看）：

- `PlanManeuver@L1` [postcondition] driver_intent.intent_type=2 and risk_level.risk_type<2 -> maneuver.maneuver_type=1

→ **label** = `___`    **evidence** = ________________________

#### 卡 EXT-3 × M3 — M3 LLM 生成 DFD（可选）

*Level-0 + Level-1（F3.1/F3.2/F3.3 细化）；部分语义写在过程字典与 README 追溯表里*

候选条款（按相关度排序，请逐条看）：

- `traceability@L1` [traceability] [E3] parent-owned | 载体: external entity | 元素: E3
- `README.md` [文档 L122] arrives as a field of E3 `driver_intent` and is consumed by F3 (and F3.3 for
- `M3_process_dictionary.md` [文档 L174] * **Inputs:** `risk_level` (F3.2), `ego_state` (F1), `driver_intent` (E3), `route`
- `README.md` [文档 L51] | IN `driver_intent` (E3) | -> F3.3 |
- `M3_process_dictionary.md` [文档 L55] (F2), `driver_intent` (E3), `route` (F4), `hd_map_segment` (D1 read).
- `F3.3@L1` [postcondition] risk_level = 0 and driver_intent.accelerate = 1 -> manoeuvre.target_speed >= driver_intent.requested_speed
- `F3.3@L1` [postcondition] risk_level = 1 and driver_intent.accelerate = 1 -> manoeuvre.target_speed >= driver_intent.requested_speed
- `M3_process_dictionary.md` [文档 L66] deceleration; decide the driver warning; respect D4 and E3. Writes no store.
- `README.md` [文档 L92] | E3 | box E3 | driver_intent in -> F3/F3.3 |
- `F3.3@L1` [postcondition] risk_level = 2 and driver_intent.accelerate = 1 -> manoeuvre.required_decel >= 6.0
- `README.md` [文档 L120] (L2 handover) function needed?**
- `README.md` [文档 L121] The model keeps the mandated seven (R-L0-1, F1..F7). Driver attention already
- `README.md` [文档 L123] accelerate-request arbitration), so handover *state* is represented without a new
- `README.md` [文档 L124] element. However R-SCOPE-1 fixes SAE L2 (driver supervises); active handover
- `README.md` [文档 L127] active handover management is in scope. Impact: medium. Recorded as OI-1.
- `M3_process_dictionary.md` [文档 L179] - `driver_intent.requested_speed >= 0`

→ **label** = `___`    **evidence** = ________________________

#### 卡 EXT-3 × M4 — M4 LLM 生成 UML 类图/顺序图（可选）

*Level-0 + Level-1（三个类细化）；阈值追溯表在 M4_constraints.md*

候选条款（按相关度排序，请逐条看）：

- `M4_constraints.md` [文档 L117] | C-E3-1 | E3 | `driver_intent <> null` | E3, R-G-6 |
- `F3.3@L1` [invariant] driver_accel_request = 'true' and risk_level <> 'critical' | manoeuvre_type <> 'emergency_deceleration' and required_decel_ms2 >= 0.0
- `F3.3@L1` [invariant] driver_accel_request = 'true' and risk_level = 'critical' | required_decel_ms2 >= 6.0 and target_speed_kmh = 0.0
- `F3@L0` [precondition] driver_intent <> null and route <> null and traffic_rules <> null and hd_map_segment <> null
- `traceability@L0` [traceability] [F3] Manoeuvre type / target speed / target lane / required deceleration, warning decision, traffic rules and driver intent respected, no store write. | 载体: class + constraints C-F3-1 .. C-F3-11 | 元素: F3
- `traceability@L1` [traceability] [F3] The manoeuvre decision, the warning decision, the traffic-rule and driver-intent handling of F3 are distributed over the three sub-functions. | 载体: refinement | 元素: F3.1, F3.2, F3.3
- `M4_constraints.md` [文档 L154] | C-L1-18 | pre | `risk_level <> '' and ego_state <> null and driver_intent <> null and route <> null and hd_map_segment <> null` | F3.3, R-G-6 |
- `F3.3@L1` [postcondition] driver_accel_request = 'true' and risk_level <> 'critical' -> manoeuvre_type <> 'emergency_deceleration' and required_decel_ms2 >= 0.0
- `F3.3@L1` [postcondition] driver_accel_request = 'true' and risk_level = 'critical' -> required_decel_ms2 >= 6.0 and target_speed_kmh = 0.0
- `F3.3@L1` [precondition] risk_level <> '' and ego_state <> null and driver_intent <> null and route <> null and hd_map_segment <> null
- `M4_constraints.md` [文档 L160] | C-L1-11 | post（guard `driver_accel_request = 'true' and risk_level = 'critical'`） | `required_decel_ms2 >= 6.0 and target_speed_kmh = 0.0` | F3.3（紧急动作不被加速请求覆盖） |
- `M4_constraints.md` [文档 L161] | C-L1-12 | post（guard `driver_accel_request = 'true' and risk_level <> 'critical'`） | `manoeuvre_type <> 'emergency_deceleration' and required_decel_ms2 >= 0.0` | F3.3（其余风险等级下加速请求优先） |
- `M4_constraints.md` [文档 L47] | C-F3-2 | pre | `driver_intent <> null and route <> null and traffic_rules <> null and hd_map_segment <> null` | R-G-6, R-D-2, F3 |

→ **label** = `___`    **evidence** = ________________________

### 需求 EXT-5 —— E5 map_data：当前位置高精地图路段（道路/车道/限速/曲率）输入

来源条款：E5

规格来源条款编号：`E5`（模型若在追溯表或文档表格里标注了这个编号，说明它自称实现了该条款 —— 请一并考虑）

（对照集条目）该需求按**整体**判定：模型里有条款表达其语义 → `1`；完全没有 → `0`。

#### 卡 EXT-5 × M1 — M1 人工 SOFL（原始版）（可选）

*Level-0（整车）+ Level-1（AEB 分支：ComputeTTC → ClassifyRisk → PlanManeuver）*

候选条款（按相关度排序，请逐条看）：

- `PlanManeuver@L1` [postcondition] risk_level.risk_type=0 -> maneuver.maneuver_type=1 and maneuver.target_speed<=map_data.speed_limit

→ **label** = `___`    **evidence** = ________________________

#### 卡 EXT-5 × M3 — M3 LLM 生成 DFD（可选）

*Level-0 + Level-1（F3.1/F3.2/F3.3 细化）；部分语义写在过程字典与 README 追溯表里*

候选条款（按相关度排序，请逐条看）：

- `M3_process_dictionary.md` [文档 L202] | D1 HD Map Store | F5 / F1 | E5 refresh | F1, F2, F3, F4, F5 |
- `M3_process_dictionary.md` [文档 L207] Note: D1/D4 refresh flows from E5/E6 and the E9 interface routing are recorded as
- `README.md` [文档 L38] 7. **D1/D4 refresh:** E5->D1 and E6->D4 are modelled as store writes because §4
- `README.md` [文档 L39] says "refreshed by E5/E6", even though §5.1 assigns no in-function writer —
- `F4@L0` [precondition] hd_map_segment.road_id > 0
- `README.md` [文档 L86] | D1 | cylinder D1 | store (read by F1,F2,F3,F4,F5; refreshed by E5) |
- `README.md` [文档 L94] | E5 | box E5 | map_data in -> D1 |
- `M3_process_dictionary.md` [文档 L175] (F4), `hd_map_segment` (D1 read).
- `M3_process_dictionary.md` [文档 L188] * **Processing rules:** Produce cruise/keep-lane for no risk; deceleration with
- `README.md` [文档 L22] 2. **Notation mapping:** process = `box`; external entity = `box` with
- `M3_process_dictionary.md` [文档 L26] * **Inputs:** `raw_sensor_data` (E1), `gnss_imu` (E2), `hd_map_segment` (D1 read).
- `M3_process_dictionary.md` [文档 L41] * **Inputs:** `object_table` (F1), `ego_state` (F1), `hd_map_segment` (D1 read).
- `README.md` [文档 L53] | IN `hd_map_segment` (D1, read) | -> F3.3 |
- `M3_process_dictionary.md` [文档 L55] (F2), `driver_intent` (E3), `route` (F4), `hd_map_segment` (D1 read).
- `M3_process_dictionary.md` [文档 L64] (cruise / keep-lane / lane-change / lane-keeping-with-deceleration / emergency
- `M3_process_dictionary.md` [文档 L65] deceleration) as a type plus target speed, target lane and required

→ **label** = `___`    **evidence** = ________________________

#### 卡 EXT-5 × M4 — M4 LLM 生成 UML 类图/顺序图（可选）

*Level-0 + Level-1（三个类细化）；阈值追溯表在 M4_constraints.md*

候选条款（按相关度排序，请逐条看）：

- `M4_constraints.md` [文档 L119] | C-E5-1 | E5 | `map_data <> null` | E5, R-G-6 |
- `F4@L0` [invariant] route_lane_geometry <> ''
- `F3@L0` [postcondition] manoeuvre_type <> '' and target_speed_kmh >= 0.0 and target_lane_id <> ''
- `F3.3@L1` [postcondition] risk_level = 'no_risk' -> manoeuvre_type = 'keep_lane'
- `F4@L0` [postcondition] route_lane_geometry <> ''
- `F3@L0` [precondition] driver_intent <> null and route <> null and traffic_rules <> null and hd_map_segment <> null
- `F1@L0` [precondition] hd_map_segment <> null
- `F2@L0` [precondition] hd_map_segment <> null
- `F3.3@L1` [precondition] risk_level <> '' and ego_state <> null and driver_intent <> null and route <> null and hd_map_segment <> null
- `traceability@L0` [traceability] [F3] Manoeuvre type / target speed / target lane / required deceleration, warning decision, traffic rules and driver intent respected, no store write. | 载体: class + constraints C-F3-1 .. C-F3-11 | 元素: F3
- `traceability@L0` [traceability] [F4] Path length, ETA and the lane geometry needed by F3 and F5. | 载体: class + constraints C-F4-1 .. C-F4-3 | 元素: F4
- `M4_constraints.md` [文档 L105] | C-D1-1 | D1 | `posted_speed_limit_kmh > 0.0` | D1, F5, R-G-1 |
- `F4@L0` [precondition] destination <> null and ego_state <> null and hd_map_segment <> null
- `M4_constraints.md` [文档 L109] | C-D4-1 | D4 | `posted_speed_limit_kmh > 0.0` | D4, R-G-1 |
- `M4_constraints.md` [文档 L13] > **守卫与析取的处理**：布尔算子集不含 `or`，因此任何析取（如“no risk 时为 cruise *或* keep-lane”）
- `M4_constraints.md` [文档 L154] | C-L1-18 | pre | `risk_level <> '' and ego_state <> null and driver_intent <> null and route <> null and hd_map_segment <> null` | F3.3, R-G-6 |

→ **label** = `___`    **evidence** = ________________________

### 需求 EXT-6 —— E6 traffic_rules：当前适用交通规则（限速与信号灯状态）输入

来源条款：E6

规格来源条款编号：`E6`（模型若在追溯表或文档表格里标注了这个编号，说明它自称实现了该条款 —— 请一并考虑）

（对照集条目）该需求按**整体**判定：模型里有条款表达其语义 → `1`；完全没有 → `0`。

#### 卡 EXT-6 × M1 — M1 人工 SOFL（原始版）（可选）

*Level-0（整车）+ Level-1（AEB 分支：ComputeTTC → ClassifyRisk → PlanManeuver）*

候选条款（按相关度排序，请逐条看）：

- `PlanManeuver@L1` [postcondition] risk_level.risk_type=0 -> maneuver.maneuver_type=1 and maneuver.target_speed<=map_data.speed_limit
- `Safety_Shield@L0` [postcondition] traffic_rules.red_light=1 -> checked_cmd.brake_cmd>=0.5
- `Behavior_Planning@L0` [postcondition] traffic_rules.speed_limit>0 -> maneuver.target_speed<=traffic_rules.speed_limit
- `Motion_Planning@L0` [postcondition] traffic_rules.speed_limit>0 -> trajectory.max_speed<=traffic_rules.speed_limit

→ **label** = `___`    **evidence** = ________________________

#### 卡 EXT-6 × M3 — M3 LLM 生成 DFD（可选）

*Level-0 + Level-1（F3.1/F3.2/F3.3 细化）；部分语义写在过程字典与 README 追溯表里*

候选条款（按相关度排序，请逐条看）：

- `M3_process_dictionary.md` [文档 L205] | D4 Traffic Rules Store | F5 | E6 refresh | F3, F5, F7 |
- `M3_process_dictionary.md` [文档 L207] Note: D1/D4 refresh flows from E5/E6 and the E9 interface routing are recorded as
- `README.md` [文档 L38] 7. **D1/D4 refresh:** E5->D1 and E6->D4 are modelled as store writes because §4
- `README.md` [文档 L39] says "refreshed by E5/E6", even though §5.1 assigns no in-function writer —
- `F5@L0` [postcondition] trajectory.max_speed <= traffic_rules.speed_limit and trajectory.max_accel <= 3.0 and trajectory.required_decel >= manoeuvre.required_decel
- `README.md` [文档 L89] | D4 | cylinder D4 | store (read by F3,F5,F7; refreshed by E6) |
- `README.md` [文档 L95] | E6 | box E6 | traffic_rules in -> D4 |
- `M3_process_dictionary.md` [文档 L116] * **Inputs:** `actuator_cmd` = E9 (F6), `ego_state` (D3 read), `traffic_rules`
- `M3_process_dictionary.md` [文档 L120] - `traffic_rules.speed_limit >= 0`
- `M3_process_dictionary.md` [文档 L14] constraints are used instead (e.g. `valid = 1`, `speed_limit >= 0`). The
- `M3_process_dictionary.md` [文档 L156] * **Inputs:** `ttc_set` (F3.1), `traffic_rules` (D4 read).
- `M3_process_dictionary.md` [文档 L160] - `traffic_rules.speed_limit >= 0`
- `README.md` [文档 L33] (`valid = 1`, `speed_limit >= 0`) are used, and `>= 0` is never applied to a
- `M3_process_dictionary.md` [文档 L35] vehicle motion signals to obtain ego pose, speed, yaw rate, acceleration. Write
- `README.md` [文档 L50] | IN `traffic_rules` (D4, read) | -> F3.2 |
- `M3_process_dictionary.md` [文档 L54] * **Inputs:** `ego_state` (F1), `traffic_rules` (D4 read), `predicted_trajectories`

→ **label** = `___`    **evidence** = ________________________

#### 卡 EXT-6 × M4 — M4 LLM 生成 UML 类图/顺序图（可选）

*Level-0 + Level-1（三个类细化）；阈值追溯表在 M4_constraints.md*

候选条款（按相关度排序，请逐条看）：

- `M4_constraints.md` [文档 L120] | C-E6-1 | E6 | `traffic_rules <> null` | E6, R-G-6 |
- `F7@L0` [invariant] checked_speed_cmd_kmh <= speed_limit_kmh
- `F5@L0` [invariant] max_permitted_speed_kmh <= speed_limit_kmh
- `F3@L0` [invariant] target_speed_kmh <= speed_limit_kmh
- `F7@L0` [postcondition] checked_speed_cmd_kmh <= speed_limit_kmh
- `F5@L0` [postcondition] max_permitted_speed_kmh <= speed_limit_kmh
- `F3@L0` [postcondition] target_speed_kmh <= speed_limit_kmh
- `F3.2@L1` [precondition] ttc_set <> null and traffic_rules <> null
- `M4_constraints.md` [文档 L105] | C-D1-1 | D1 | `posted_speed_limit_kmh > 0.0` | D1, F5, R-G-1 |
- `F7@L0` [precondition] actuator_cmd <> null and ego_state <> null and traffic_rules <> null
- `F3@L0` [precondition] driver_intent <> null and route <> null and traffic_rules <> null and hd_map_segment <> null
- `M4_constraints.md` [文档 L109] | C-D4-1 | D4 | `posted_speed_limit_kmh > 0.0` | D4, R-G-1 |
- `M4_constraints.md` [文档 L141] | C-L1-17 | pre | `ttc_set <> null and traffic_rules <> null` | F3.2, R-G-6 |
- `M4_constraints.md` [文档 L47] | C-F3-2 | pre | `driver_intent <> null and route <> null and traffic_rules <> null and hd_map_segment <> null` | R-G-6, R-D-2, F3 |
- `M4_constraints.md` [文档 L54] | C-F3-9 | post | `target_speed_kmh <= speed_limit_kmh` | F3（遵守 D4 交通规则） |
- `M4_constraints.md` [文档 L71] | C-F5-2 | post | `max_permitted_speed_kmh <= speed_limit_kmh` | F5（F5 不得超速） |

→ **label** = `___`    **evidence** = ________________________

### 需求 SCOPE-1 —— 系统为 SAE L2 级整车级 ADAS 车载系统，驾驶员持续监督

来源条款：R-SCOPE-1

规格来源条款编号：`R-SCOPE-1`（模型若在追溯表或文档表格里标注了这个编号，说明它自称实现了该条款 —— 请一并考虑）

（对照集条目）该需求按**整体**判定：模型里有条款表达其语义 → `1`；完全没有 → `0`。

#### 卡 SCOPE-1 × M1 — M1 人工 SOFL（原始版）（可选）

*Level-0（整车）+ Level-1（AEB 分支：ComputeTTC → ClassifyRisk → PlanManeuver）*

候选条款（按相关度排序，请逐条看）：

- `PlanManeuver@L1` [postcondition] driver_intent.intent_type=2 and risk_level.risk_type<2 -> maneuver.maneuver_type=1

→ **label** = `___`    **evidence** = ________________________

#### 卡 SCOPE-1 × M3 — M3 LLM 生成 DFD（可选）

*Level-0 + Level-1（F3.1/F3.2/F3.3 细化）；部分语义写在过程字典与 README 追溯表里*

候选条款（按相关度排序，请逐条看）：

- `traceability@L0` [traceability] [R-SCOPE-1] Onboard ADAS at SAE L2 within the vehicle boundary. | 载体: whole model | 元素: F1, F2, F3, F4, F5, F6, F7
- `README.md` [文档 L124] element. However R-SCOPE-1 fixes SAE L2 (driver supervises); active handover
- `README.md` [文档 L63] | R-SCOPE-1 | F1..F7 | whole system model |
- `F3.3@L1` [postcondition] risk_level = 0 and driver_intent.accelerate = 1 -> manoeuvre.target_speed >= driver_intent.requested_speed
- `F3.3@L1` [postcondition] risk_level = 1 and driver_intent.accelerate = 1 -> manoeuvre.target_speed >= driver_intent.requested_speed
- `M3_process_dictionary.md` [文档 L128] * **Processing rules:** Supervise F6's command and output one satisfying the
- `M3_process_dictionary.md` [文档 L167] critical (`<= 1.5`). Raise the driver warning for caution and critical;
- `F3.3@L1` [postcondition] risk_level = 2 and driver_intent.accelerate = 1 -> manoeuvre.required_decel >= 6.0
- `README.md` [文档 L119] **OI-1 — Is the seven-function split sufficient; is a separate driver-monitoring
- `README.md` [文档 L120] (L2 handover) function needed?**
- `README.md` [文档 L121] The model keeps the mandated seven (R-L0-1, F1..F7). Driver attention already
- `README.md` [文档 L122] arrives as a field of E3 `driver_intent` and is consumed by F3 (and F3.3 for
- `M3_process_dictionary.md` [文档 L174] * **Inputs:** `risk_level` (F3.2), `ego_state` (F1), `driver_intent` (E3), `route`
- `M3_process_dictionary.md` [文档 L179] - `driver_intent.requested_speed >= 0`
- `M3_process_dictionary.md` [文档 L185] - guard `risk_level = 2 and driver_intent.accelerate = 1` → `manoeuvre.required_decel >= 6.0`
- `M3_process_dictionary.md` [文档 L186] - guard `risk_level = 0 and driver_intent.accelerate = 1` → `manoeuvre.target_speed >= driver_intent.requested_speed`

→ **label** = `___`    **evidence** = ________________________

#### 卡 SCOPE-1 × M4 — M4 LLM 生成 UML 类图/顺序图（可选）

*Level-0 + Level-1（三个类细化）；阈值追溯表在 M4_constraints.md*

候选条款（按相关度排序，请逐条看）：

- `traceability@L0` [traceability] [R-SCOPE-1] Onboard ADAS of a passenger car at SAE level 2; the seven classes are the vehicle-side functions. | 载体: class | 元素: F1, F2, F3, F4, F5, F6, F7
- `F3.3@L1` [invariant] driver_accel_request = 'true' and risk_level <> 'critical' | manoeuvre_type <> 'emergency_deceleration' and required_decel_ms2 >= 0.0
- `F3.3@L1` [invariant] driver_accel_request = 'true' and risk_level = 'critical' | required_decel_ms2 >= 6.0 and target_speed_kmh = 0.0
- `F3@L0` [precondition] driver_intent <> null and route <> null and traffic_rules <> null and hd_map_segment <> null
- `traceability@L1` [traceability] [F3.3] Manoeuvre per risk level; the emergency manoeuvre is not overridden by a driver acceleration request. | 载体: class + constraints C-L1-7 .. C-L1-12, C-L1-18 | 元素: F3.3
- `traceability@L0` [traceability] [F3] Manoeuvre type / target speed / target lane / required deceleration, warning decision, traffic rules and driver intent respected, no store write. | 载体: class + constraints C-F3-1 .. C-F3-11 | 元素: F3
- `traceability@L1` [traceability] [F3] The manoeuvre decision, the warning decision, the traffic-rule and driver-intent handling of F3 are distributed over the three sub-functions. | 载体: refinement | 元素: F3.1, F3.2, F3.3
- `M4_constraints.md` [文档 L117] | C-E3-1 | E3 | `driver_intent <> null` | E3, R-G-6 |
- `M4_constraints.md` [文档 L154] | C-L1-18 | pre | `risk_level <> '' and ego_state <> null and driver_intent <> null and route <> null and hd_map_segment <> null` | F3.3, R-G-6 |
- `F3.3@L1` [postcondition] driver_accel_request = 'true' and risk_level <> 'critical' -> manoeuvre_type <> 'emergency_deceleration' and required_decel_ms2 >= 0.0
- `F3.3@L1` [postcondition] driver_accel_request = 'true' and risk_level = 'critical' -> required_decel_ms2 >= 6.0 and target_speed_kmh = 0.0
- `F3.3@L1` [precondition] risk_level <> '' and ego_state <> null and driver_intent <> null and route <> null and hd_map_segment <> null
- `M4_constraints.md` [文档 L160] | C-L1-11 | post（guard `driver_accel_request = 'true' and risk_level = 'critical'`） | `required_decel_ms2 >= 6.0 and target_speed_kmh = 0.0` | F3.3（紧急动作不被加速请求覆盖） |
- `M4_constraints.md` [文档 L161] | C-L1-12 | post（guard `driver_accel_request = 'true' and risk_level <> 'critical'`） | `manoeuvre_type <> 'emergency_deceleration' and required_decel_ms2 >= 0.0` | F3.3（其余风险等级下加速请求优先） |
- `M4_constraints.md` [文档 L47] | C-F3-2 | pre | `driver_intent <> null and route <> null and traffic_rules <> null and hd_map_segment <> null` | R-G-6, R-D-2, F3 |

→ **label** = `___`    **evidence** = ________________________

### 需求 SCOPE-3 —— 规格约束功能分配与数据依赖，不约束功能内部算法

来源条款：R-SCOPE-3

规格来源条款编号：`R-SCOPE-3`（模型若在追溯表或文档表格里标注了这个编号，说明它自称实现了该条款 —— 请一并考虑）

（对照集条目）该需求按**整体**判定：模型里有条款表达其语义 → `1`；完全没有 → `0`。

#### 卡 SCOPE-3 × M1 — M1 人工 SOFL（原始版）（可选）

*Level-0（整车）+ Level-1（AEB 分支：ComputeTTC → ClassifyRisk → PlanManeuver）*

候选条款（按相关度排序，请逐条看）：

- `Perception_Localization@L0` [decomposition] raw_sensor_data.valid=1 and gnss_imu.valid=1 and map_data.speed_limit>=0
- `Prediction@L0` [decomposition] objects.lead_speed>=0 and ego_pose.speed>=0 and map_data.speed_limit>=0
- `Behavior_Planning@L0` [decomposition] ego_state.speed>=0 and driver_intent.cruise_speed>=0 and route.path_length>0 and traffic_rules.speed_limit>0
- `Safety_Shield@L0` [decomposition] ego_state.speed>=0 and actuator_cmd.brake_cmd>=0
- `Motion_Planning@L0` [decomposition] maneuver.target_speed>=0 and ego_state.speed>=0 and map_data.speed_limit>=0
- `Control@L0` [decomposition] trajectory.horizon>0 and ego_state.speed>=0
- `Route_Planning@L0` [decomposition] ego_pose.speed>=0 and map_data.speed_limit>=0 and destination.lon>=0

→ **label** = `___`    **evidence** = ________________________

#### 卡 SCOPE-3 × M3 — M3 LLM 生成 DFD（可选）

*Level-0 + Level-1（F3.1/F3.2/F3.3 细化）；部分语义写在过程字典与 README 追溯表里*

候选条款（按相关度排序，请逐条看）：

- `traceability@L0` [traceability] [R-SCOPE-3] Only functional allocation and data dependencies are modelled. | 载体: functional allocation | 元素: F1, F2, F3, F4, F5, F6, F7
- `README.md` [文档 L65] | R-SCOPE-3 | F1..F7 | functional allocation only |
- `traceability@L0` [traceability] [R-G-4] Every dependency is an explicit named directed flow; shared flows declared twice. | 载体: flows | 元素: F1, F2, F3, F4, F5, F6, F7
- `traceability@L0` [traceability] [R-SCOPE-1] Onboard ADAS at SAE L2 within the vehicle boundary. | 载体: whole model | 元素: F1, F2, F3, F4, F5, F6, F7
- `traceability@L0` [traceability] [R-SCOPE-2] Everything outside the vehicle is an external interface. | 载体: external entities | 元素: E1, E2, E3, E4, E5, E6, E7, E8, E9
- `traceability@L1` [traceability] [R-SCOPE-4] Exactly one Level-0 function refined. | 载体: level split | 元素: F3.1, F3.2, F3.3
- `traceability@L0` [traceability] [R-SCOPE-4] Two levels; only F3 refined. | 载体: level split | 元素: F3, F3.1, F3.2, F3.3
- `README.md` [文档 L124] element. However R-SCOPE-1 fixes SAE L2 (driver supervises); active handover
- `README.md` [文档 L126] Conclusion: sufficient for the stated *functional* allocation; insufficient if
- `README.md` [文档 L127] active handover management is in scope. Impact: medium. Recorded as OI-1.
- `README.md` [文档 L147] The model follows R-SCOPE-4 and R-L1-1, which explicitly name the F3 emergency
- `README.md` [文档 L63] | R-SCOPE-1 | F1..F7 | whole system model |
- `README.md` [文档 L64] | R-SCOPE-2 | E1..E9 | external entities |
- `README.md` [文档 L66] | R-SCOPE-4 | F3, F3.1, F3.2, F3.3 | two-level split |

→ **label** = `___`    **evidence** = ________________________

#### 卡 SCOPE-3 × M4 — M4 LLM 生成 UML 类图/顺序图（可选）

*Level-0 + Level-1（三个类细化）；阈值追溯表在 M4_constraints.md*

候选条款（按相关度排序，请逐条看）：

- `traceability@L0` [traceability] [R-SCOPE-3] No detector, tracker, planner or controller internals are decomposed at Level 0. | 载体: structure | 元素: F1, F2, F3, F4, F5, F6, F7
- `traceability@L0` [traceability] [R-G-4] Every dependency is a named directed flow with a single producer and a single consumer; a flow is shared only where spec section 5.1 says so (ego_state to F2/F4, predicted_trajectories to F3/F5, route to F3/F5). | 载体: flows | 元素: 
- `traceability@L0` [traceability] [R-SCOPE-1] Onboard ADAS of a passenger car at SAE level 2; the seven classes are the vehicle-side functions. | 载体: class | 元素: F1, F2, F3, F4, F5, F6, F7
- `traceability@L0` [traceability] [R-SCOPE-2] Everything outside the vehicle is an actor or a port, never an internal element. | 载体: actor / port | 元素: E1, E2, E3, E4, E5, E6, E7, E8, E9
- `traceability@L0` [traceability] [R-SCOPE-4] Exactly one Level-0 function is refined; all others stay atomic. | 载体: package in M4_L1.puml | 元素: F3
- `traceability@L1` [traceability] [R-SCOPE-4] Exactly one Level-0 function is refined; the remaining Level-0 elements are carried over unchanged. | 载体: package in M4_L1.puml | 元素: F3.1, F3.2, F3.3

→ **label** = `___`    **evidence** = ________________________

### 需求 TH-2 —— 前向碰撞预警须在 TTC=2.0 s 前发出

来源条款：N-2

规格来源条款编号：`N-2`（模型若在追溯表或文档表格里标注了这个编号，说明它自称实现了该条款 —— 请一并考虑）

（对照集条目）该需求按**整体**判定：模型里有条款表达其语义 → `1`；完全没有 → `0`。

#### 卡 TH-2 × M1 — M1 人工 SOFL（原始版）（可选）

*Level-0（整车）+ Level-1（AEB 分支：ComputeTTC → ClassifyRisk → PlanManeuver）*

候选条款（按相关度排序，请逐条看）：

- `traceability@L0` [traceability] [N-2] threshold 1.5 appears in the validated fModule | 载体: threshold in postconditions | 元素: 
- `traceability@L1` [traceability] [N-2] threshold 1.5 appears in the validated fModule | 载体: threshold in postconditions | 元素: 
- `ComputeTTC@L1` [postcondition] predicted_trajectories.count=0 -> ttc_values.count=0
- `ComputeTTC@L1` [postcondition] predicted_trajectories.count>0 -> ttc_values.count=predicted_trajectories.count and ttc_values.min_ttc<=predicted_trajectories.min_ttc
- `Behavior_Planning@L0` [postcondition] predicted_trajectories.min_ttc<1.5 -> maneuver.maneuver_type=3 and maneuver.decel_req>=6.0 and warning.warn_active=1
- `Behavior_Planning@L0` [postcondition] predicted_trajectories.min_ttc>=1.5 -> maneuver.maneuver_type<>3
- `ClassifyRisk@L1` [postcondition] ttc_values.min_ttc<=1.5 -> risk_level.risk_type=2 and warning.warn_active=1
- `ClassifyRisk@L1` [postcondition] ttc_values.min_ttc<=3.0 and ttc_values.min_ttc>1.5 -> risk_level.risk_type=1 and warning.warn_active=1
- `traceability@L1` [traceability] [F-ComputeTTC] pre/post in fModule; clause realisation verified by validate_sofl_model.py | 载体: process contract | 元素: ComputeTTC
- `ClassifyRisk@L1` [postcondition] ttc_values.min_ttc>3.0 -> risk_level.risk_type=0 and warning.warn_active=0

→ **label** = `___`    **evidence** = ________________________

#### 卡 TH-2 × M3 — M3 LLM 生成 DFD（可选）

*Level-0 + Level-1（F3.1/F3.2/F3.3 细化）；部分语义写在过程字典与 README 追溯表里*

候选条款（按相关度排序，请逐条看）：

- `traceability@L1` [traceability] [N-2] Warning no later than TTC = 2.0 s. | 载体: postcondition | 元素: F3.2
- `traceability@L0` [traceability] [N-2] Warning no later than TTC = 2.0 s; child F3.2. | 载体: postcondition | 元素: F3.2
- `README.md` [文档 L103] | N-2 | F3.2 | warning by TTC = 2.0 s |
- `README.md` [文档 L141] "no later than TTC = 2.0 s" warning (N-2) and the emergency intervention cannot be
- `M3_process_dictionary.md` [文档 L169] `2 = imminent collision`. FCW timing follows N-2 (no later than TTC = 2.0 s).
- `F3.1@L1` [postcondition] ttc_set.count = 0 -> ttc_set.min_ttc = 0
- `F3.2@L1` [postcondition] ttc_set.min_ttc <= 1.5 -> risk_level = 2 and warning.active = 1 and warning.type = 2
- `F3.2@L1` [postcondition] ttc_set.min_ttc <= 3.0 and ttc_set.min_ttc > 1.5 -> risk_level = 1 and warning.active = 1 and warning.type = 1
- `traceability@L1` [traceability] [R-E-1] Warning is one of the two system outputs. | 载体: boundary_out flow | 元素: E7, F3.2
- `M3_process_dictionary.md` [文档 L133] above `a_max_accel = 2.0` during `rho = 0.1`) and lateral envelope (N-7).
- `F3.2@L1` [postcondition] ttc_set.min_ttc > 3.0 -> risk_level = 0 and warning.active = 0 and warning.type = 0
- `M3_process_dictionary.md` [文档 L135] * **quantified:** true (3.0 from A-3, 1.0 from A-6, 4.0/2.0/0.1 from A-2/N-6)
- `M3_process_dictionary.md` [文档 L141] ### 3.1 / F3.1 — TTC Computation
- `M3_process_dictionary.md` [文档 L143] * **Outputs:** `ttc_set` → F3.2.
- `M3_process_dictionary.md` [文档 L148] - guard `true` → `ttc_set.min_ttc >= 0 and ttc_set.min_ttc <= 3.0`
- `M3_process_dictionary.md` [文档 L149] - guard `ttc_set.count = 0` → `ttc_set.min_ttc = 0`

→ **label** = `___`    **evidence** = ________________________

#### 卡 TH-2 × M4 — M4 LLM 生成 UML 类图/顺序图（可选）

*Level-0 + Level-1（三个类细化）；阈值追溯表在 M4_constraints.md*

候选条款（按相关度排序，请逐条看）：

- `traceability@L0` [traceability] [N-2] A warning must be present no later than TTC = 2.0 s. | 载体: invariant C-F3-6 | 元素: F3
- `traceability@L1` [traceability] [N-2] A warning must be present no later than TTC = 2.0 s. | 载体: invariant C-L1-6 | 元素: F3.2
- `M4_constraints.md` [文档 L148] | C-L1-6 | post（guard `ttc_min_s <= 2.0`） | `warning_type <> 'none'` | **N-2** |
- `M4_constraints.md` [文档 L170] | N-2 | 2.0 s | C-F3-6, C-L1-6 |
- `F2@L0` [invariant] TTC is computed in F2 only (spec F2); see OI-6 for the conflict with the Level-1 clause F3.1
- `F2@L0` [invariant] min_ttc_s >= 0.0
- `F7@L0` [invariant] response_time_s <= 0.1 | checked_accel_cmd_ms2 <= 2.0
- `F3.2@L1` [invariant] risk_level = 'caution' | ttc_min_s <= 3.0 and ttc_min_s > 1.5
- `F3.2@L1` [invariant] risk_level = 'critical' | ttc_min_s <= 1.5
- `F3@L0` [invariant] ttc_min_s <= 2.0 | warning_type <> 'none'
- `F7@L0` [postcondition] response_time_s <= 0.1 -> checked_accel_cmd_ms2 <= 2.0
- `F3@L0` [postcondition] risk_level = 'critical' -> warning_type = 'imminent collision' and warning_active = 'true'
- `traceability@L0` [traceability] [A-2] RSS parameter set: rho = 0.1 s, a_max,accel = 2.0, a_max,brake = 4.0, a_min,brake = 4.0. | 载体: invariants C-F7-6, C-F7-7, C-F3-11 | 元素: F7, F3
- `traceability@L0` [traceability] [A-5] T_risk_high = 3.0 and T_fcw = 1.5 are applied in the Level-1 refinement of F3. | 载体: risk band thresholds applied in F3.2 (C-L1-3 .. C-L1-5) | 元素: F3
- `traceability@L1` [traceability] [A-5] T_risk_high = 3.0 s and T_fcw = 1.5 s. | 载体: invariants C-L1-3, C-L1-4, C-L1-5 | 元素: F3.2
- `traceability@L1` [traceability] [A-7] The TTC is evaluated over the 3.0 s prediction horizon of F2. | 载体: invariant C-L1-19 | 元素: F3.1

→ **label** = `___`    **evidence** = ________________________
