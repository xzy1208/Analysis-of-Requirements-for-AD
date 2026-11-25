- # hy4 — SOFL 形式化规格（含 CDFD）

  > 输入基线：`NL-RQ-ADAS-v1_spec.md` v1.0。本文件只建模规格中写明的功能、存储、接口与阈值；未写明之处记入 open-issues。 模型名：**NL-RQ-ADAS-v1D**；包含两个 module：`ADAS_System`（Level 0）、`AEB_Branch`（Level 1）。

  ------

  ## 0. 表示约定（仅为类型编码，不是新元素）

  以下编码用于把规格中的枚举语义写成 `nat` 字段，取值含义在 open-issues OI-9 中声明，不引入新信号或阈值：

  | 字段                        | 编码                                                         |
  | --------------------------- | ------------------------------------------------------------ |
  | `Warning.warning_type`      | 0 = none；1 = caution；2 = imminent collision                |
  | `Warning.active`            | 0 = inactive；1 = active                                     |
  | `Manoeuvre.manoeuvre_type`  | 0 = cruise/keep-lane；1 = lane-change；2 = lane-keeping-with-deceleration；3 = deceleration；4 = emergency deceleration |
  | `RiskLevel.level`           | 0 = no risk；1 = caution；2 = critical                       |
  | `TrafficRules.signal_state` | 由 E6 提供的枚举值，本模型不解释其分项语义                   |

  单位约定：`EgoState.speed`、`closing_speed` 用 m/s；N-1 的 130 km/h 换算为 **36.1 m/s**（见 OI-12）。

  ------

  ## 1. 类型声明（两个 module 共享）

  ```
  
  ```

  ------

  ## 2. Module `ADAS_System`（Level 0）

  ### 2.1 Module head

  ```
  
  ```

  端口对应：E1 `raw_sensor_data`、E2 `gnss_imu`、E3 `driver_intent`、E4 `destination`、E5 `map_data`、E6 `traffic_rules`、E9 `e9_actuator_cmd` 为入；E7 `warning`、E8 `checked_cmd` 为出。

  ### 2.2 Process 契约

  ```
  
  ```

  ### 2.3 Level 0 CDFD — 元素清单

  **过程（恰好 7 个，R-L0-1）**

  | ID   | 名称               | 对应规格 |
  | ---- | ------------------ | -------- |
  | F1   | `f1_perception`    | §5 F1    |
  | F2   | `f2_prediction`    | §5 F2    |
  | F3   | `f3_behaviour`     | §5 F3    |
  | F4   | `f4_route`         | §5 F4    |
  | F5   | `f5_motion`        | §5 F5    |
  | F6   | `f6_control`       | §5 F6    |
  | F7   | `f7_safety_shield` | §5 F7    |

  **数据存储（恰好 4 个，R-L0-1）**

  | ID   | 名称                | 类型           | 写者               | 读者                        |
  | ---- | ------------------- | -------------- | ------------------ | --------------------------- |
  | D1   | HD Map Store        | `MapSegment`   | E5（外部刷新，§4） | F1、F2、F3、F4、F5          |
  | D2   | Object Track Store  | `ObjectTable`  | F1                 | F2（经 F1→F2 显式流，§5.1） |
  | D3   | Ego State Store     | `EgoState`     | F1                 | F6、F7                      |
  | D4   | Traffic Rules Store | `TrafficRules` | E6（外部刷新，§4） | F3、F5、F7                  |

  **外部终端（恰好 E1–E9，R-L0-1）**

  | ID   | 名称              | 方向 | 连接                                            |
  | ---- | ----------------- | ---- | ----------------------------------------------- |
  | E1   | `raw_sensor_data` | in   | → F1                                            |
  | E2   | `gnss_imu`        | in   | → F1                                            |
  | E3   | `driver_intent`   | in   | → F3                                            |
  | E4   | `destination`     | in   | → F4                                            |
  | E5   | `map_data`        | in   | → D1（写/刷新）                                 |
  | E6   | `traffic_rules`   | in   | → D4（写/刷新）                                 |
  | E7   | `warning`         | out  | F3 →                                            |
  | E8   | `checked_cmd`     | out  | F7 →                                            |
  | E9   | `actuator_cmd`    | in   | → F7（§3 的方向；与 F6→F7 内部流并存，见 OI-5） |

  ### 2.4 Level 0 CDFD — 数据流连线清单

  | #    | 起点 | 终点 | 流名                           | 类型 / 访问           | 依据                                      |
  | ---- | ---- | ---- | ------------------------------ | --------------------- | ----------------------------------------- |
  | 1    | E1   | F1   | `raw_sensor_data`              | `TimestampedFrameSet` | §3 E1                                     |
  | 2    | E2   | F1   | `gnss_imu`                     | `GnssImuSample`       | §3 E2                                     |
  | 3    | E5   | D1   | `map_data`                     | 写                    | §4 D1 “refreshed by E5”                   |
  | 4    | E6   | D4   | `traffic_rules`                | 写                    | §4 D4 “refreshed by E6”                   |
  | 5    | E4   | F4   | `destination`                  | `Destination`         | §5 F4                                     |
  | 6    | E3   | F3   | `driver_intent`                | `DriverIntent`        | §5 F3                                     |
  | 7    | E9   | F7   | `e9_actuator_cmd`              | `ActuatorCmd`         | §3 E9 / R-E-2                             |
  | 8    | D1   | F1   | `hd_map_1`                     | rd `MapSegment`       | §5.1 store reads                          |
  | 9    | F1   | D2   | `object_table`                 | wr `ObjectTable`      | §5.1 store writes                         |
  | 10   | F1   | D3   | `ego_state_to_store`           | wr `EgoState`         | §5.1 store writes                         |
  | 11   | F1   | F2   | `object_table_to_f2`           | `ObjectTable`         | §5.1 “F1 → F2: ego pose and object table” |
  | 12   | F1   | F2   | `ego_pose_to_f2`               | `EgoState`            | 同上                                      |
  | 13   | F1   | F4   | `ego_pose_to_f4`               | `EgoState`            | §5.1 “F1 → F4: ego pose”                  |
  | 14   | D1   | F2   | `hd_map_2`                     | rd `MapSegment`       | §5.1 store reads                          |
  | 15   | F2   | F3   | `predicted_trajectories_to_f3` | `PredictionSet`       | §5.1 “F2 → F3”                            |
  | 16   | F2   | F5   | `predicted_trajectories_to_f5` | `PredictionSet`       | §5.1 “F2 → F5”                            |
  | 17   | D1   | F3   | `hd_map_3`                     | rd `MapSegment`       | §5.1 store reads                          |
  | 18   | D4   | F3   | `rules_to_f3`                  | rd `TrafficRules`     | §5.1 store reads                          |
  | 19   | F4   | F3   | `route_to_f3`                  | `Route`               | §5.1 “F4 → F3”                            |
  | 20   | F4   | F5   | `route_to_f5`                  | `Route`               | §5.1 “F4 → F5”                            |
  | 21   | D1   | F4   | `hd_map_4`                     | rd `MapSegment`       | §5.1 store reads                          |
  | 22   | F3   | F5   | `manoeuvre`                    | `Manoeuvre`           | §5.1 “F3 → F5”                            |
  | 23   | D1   | F5   | `hd_map_5`                     | rd `MapSegment`       | §5.1 store reads                          |
  | 24   | D4   | F5   | `rules_to_f5`                  | rd `TrafficRules`     | §5.1 store reads                          |
  | 25   | F5   | F6   | `trajectory`                   | `Trajectory`          | §5.1 “F5 → F6”                            |
  | 26   | D3   | F6   | `ego_state_to_f6`              | rd `EgoState`         | §5.1 store reads                          |
  | 27   | F6   | F7   | `actuator_cmd`                 | `ActuatorCmd`         | §5.1 “F6 → F7”；§3 E9                     |
  | 28   | D3   | F7   | `ego_state_to_f7`              | rd `EgoState`         | §5.1 store reads                          |
  | 29   | D4   | F7   | `rules_to_f7`                  | rd `TrafficRules`     | §5.1 store reads                          |
  | 30   | F3   | E7   | `warning`                      | `Warning`             | §5.1 “F3 → outside: E7”                   |
  | 31   | F7   | E8   | `checked_cmd`                  | `ActuatorCmd`         | §5.1 “F7 → outside: E8”                   |

  > 每条流均为命名、有向、单生产者→单消费者；`route` 同时供给 F3 与 F5 是规格 §5.1 明确允许的共享（R-G-4）。

  ------

  ## 3. Module `AEB_Branch`（Level 1，F3 的 AEB 分支）

  ### 3.1 Module head

  ```
  
  ```

  > 入端口为 F3 边界上来自 F2/F1/D4/E3/F4/D1 的输入；出端口为 E7 `warning` 与回送 Level 0 F5 的 `manoeuvre`。这些是 F3 已声明的接口，不是新 E 接口。

  ### 3.2 Process 契约

  ```
  
  ```

  ### 3.3 Level 1 CDFD — 元素清单

  **过程（恰好 F3.1 → F3.2 → F3.3，R-L1-1）**

  | ID   | 名称             | 对应规格 |
  | ---- | ---------------- | -------- |
  | F3.1 | `f3_1_ttc`       | §6 F3.1  |
  | F3.2 | `f3_2_risk`      | §6 F3.2  |
  | F3.3 | `f3_3_manoeuvre` | §6 F3.3  |

  **数据存储（本层出现 2 个）**

  | ID   | 名称                | 类型           | 访问者        |
  | ---- | ------------------- | -------------- | ------------- |
  | D1   | HD Map Store        | `MapSegment`   | F3.3 `ext rd` |
  | D4   | Traffic Rules Store | `TrafficRules` | F3.2 `ext rd` |

  > D2/D3 不属于 F3 的输入（§6 未列出），故本层不出现，符合“不增删”。

  **外部终端（F3 的边界接口，非新 E 接口）**

  | ID   | 名称              | 方向 | 说明                                         |
  | ---- | ----------------- | ---- | -------------------------------------------- |
  | B1   | `pred_from_F2`    | in   | §6 F3.1 “predicted trajectories (from F2)”   |
  | B2   | `ego_from_F1`     | in   | §6 F3.1/F3.3 “ego state”                     |
  | E3   | `driver_intent`   | in   | §6 F3.3，规格明确的 E3                       |
  | B3   | `route_from_F4`   | in   | §6 F3.3 “route (from F4)”                    |
  | E7   | `warning`         | out  | §6 F3.2 “warning (E7)”                       |
  | B4   | `manoeuvre_to_F5` | out  | §6 F3.3 “Output: manoeuvre”；回送 Level 0 F5 |

  ### 3.4 Level 1 CDFD — 数据流连线清单

  | #    | 起点 | 终点 | 流名                     | 类型 / 访问       | 依据                             |
  | ---- | ---- | ---- | ------------------------ | ----------------- | -------------------------------- |
  | 1    | B1   | F3.1 | `predicted_trajectories` | `PredictionSet`   | §6 F3.1                          |
  | 2    | B2   | F3.1 | `ego_state_a`            | `EgoState`        | §6 F3.1                          |
  | 3    | F3.1 | F3.2 | `ttc_set`                | `TTCSet`          | §6 F3.2 “TTC set (from F3.1)”    |
  | 4    | D4   | F3.2 | `rules_to_f3_2`          | rd `TrafficRules` | §6 F3.2 “traffic rules (D4)”     |
  | 5    | F3.2 | F3.3 | `risk_level`             | `RiskLevel`       | §6 F3.3 “risk level (from F3.2)” |
  | 6    | F3.2 | E7   | `warning`                | `Warning`         | §6 F3.2 “warning (E7)”           |
  | 7    | B2   | F3.3 | `ego_state_b`            | `EgoState`        | §6 F3.3                          |
  | 8    | E3   | F3.3 | `driver_intent`          | `DriverIntent`    | §6 F3.3                          |
  | 9    | B3   | F3.3 | `route`                  | `Route`           | §6 F3.3                          |
  | 10   | D1   | F3.3 | `map_data`               | rd `MapSegment`   | §6 F3.3 “D1”                     |
  | 11   | F3.3 | B4   | `manoeuvre`              | `Manoeuvre`       | §6 F3.3                          |

  ------

  ## 4. Open issues

  规格 §11 要求报告的 4 项：

  - **OI-1**（§11.1）七函数划分对所述 ODD 是否足够；L2 驾驶员监控/接管是否需要独立功能。本模型严格保留 F1–F7，未新增功能。

  - **OI-2**（§11.2）D3 由 F1 写、F6/F7 读的归属是否合适。模型按 §5.1 原样保留。

  - **OI-3**（§11.3）规格固定阈值但未规定周期时间；紧急分支是否需要时序需求。模型未引入时间谓词。

  - **OI-4**（§11.4）Level 1 选择 F3 的 AEB 分支而不是 F6/F7 执行链是否最佳。模型按 §6 实现。

  建模决定 / 规格不一致（均不新增功能、存储、信号或阈值）：

  - **OI-5** §3 将 E9 列为方向 `in` 的外部接口，§5/F6 又把 `actuator_cmd` 作为 F6 的输出、F7 的输入。模型同时保留 E9→F7（按 §3）与 F6→F7（按 §5.1）两条命名流，F7 契约分别以 `e9_raw` 与 `cmd` 给出。二者语义同一性问题留待确认。

  - **OI-6** A-5 的说明引用了 **R-F2-1**（“prediction horizon of F2”），但该条款未在 §5 正文中定义。模型将 H2 的 3.0 s 下界按 A-7/R-F2-1 处理，条款正文待补。

  - **OI-7** §4 表中 D1 的 owner 写为 “F5 / F1”，而 §5.1 的写权限只列 “F1 writes D2 and D3”。模型按 §4 的 “refreshed by E5” 将 E5→D1 建模为外部刷新，未给 F5 写权限。

  - **OI-8** 本子集禁用 `seq of`，D2 的“逐目标表”以 `ObjectTable.count` + `lead_object` 表示；逐目标数组不可枚举，保留为抽象。

  - **OI-9** 枚举编码（Warning/Manoeuvre/RiskLevel/signal_state，见 §0）是表示约定，不是新阈值或新信号。

  - **OI-10** §6 规定 F3.2 输入 D4，但未给出交通规则如何改变风险分类。模型中 F3.2 `ext rd D4` 且 `pre rules.speed_limit > 0`，post 未使用规则字段；规则对分类的影响留空。

  - **OI-11** N-5 要求 RSS `d_min`（[S4] Eq.1）。该公式不在规格正文中，模型以 `Trajectory.rss_d_min` 抽象该量，仅使用 A-2 的参数集（ρ=0.1、a_max,accel=2.0、a_min,brake=4.0）做可表达约束，不展开外部公式。

  - **OI-12** N-1 的 130 km/h 在契约中写为 `<= 36.1`（m/s，四舍五入）；若采用其它单位换算需重算。

  - **OI-13** §6 F3.1 规定 count=0 时报告 0；模型以 `min_ttc = 0` 作为哨兵，由 `count = 0` 区分“无目标”，该哨兵不是阈值。

  - **OI-14** §6 同时要求 caution 产生非零减速、且“其他风险级别的驾驶员加速请求优先”。模型将 `risk.level = 1 and driver_intent.req_accel = 1` 的结果写为 cruise/零减速；与 caution 减速要求的优先级冲突需确认。

  - **OI-15** N-7 未给出横向加速度能力的数值。模型以 A-6 的归一化转向包络 `steer <= 1.0 and steer >= -1.0` 作为可表达代理，不发明横向加速度阈值。

  - **OI-16** §5 F2 “shall be the only function that computes TTC” 与 §6 F3.1 “shall compute TTC” 冲突。Level 0 保留 F2 计算 `min_ttc`，Level 1 按 §6 保留 F3.1，冲突留待确认。

  - **OI-17** F1→F2 的“ego pose and object table”在连线清单中拆为两条命名流（#11、#12），仅为满足单生产者-单消费者显式化（R-G-4），不是新信号。

  > 本模型**没有省略任何 pre 子句**：每个 process 都能从 §7/§8 阈值、§3/§4 的有效性标志或 §5/§6 的计数/路径字段中写出真实前置条件，因此未使用“无实质前置条件”的省略项。

  ------

  ## 5. 可追溯性说明（R-G-2 / R-G-3）

  ### 5.1 需求条款 → 模型元素

  | 条款               | 模型元素                                                     |
  | ------------------ | ------------------------------------------------------------ |
  | R-SCOPE-1          | 两个 module 的整体边界；`ADAS_System` 仅含 Level 0 七功能    |
  | R-SCOPE-2          | E1–E9 全部为外部终端；传感器/HMI/执行器等不出现在过程集合    |
  | R-SCOPE-3          | 所有 process 只写功能级契约，不涉及任何算法内部              |
  | R-SCOPE-4          | `ADAS_System`（L0）与 `AEB_Branch`（L1，仅细化 F3）          |
  | R-E-1              | 输出端口仅 `warning`(E7) 与 `checked_cmd`(E8)；连线 #30、#31 |
  | R-E-2              | E9 终端→F7（#7）、F6→F7（#27）、F7 post `e9_raw.accel > 3.0` 与 `checked.accel = cmd.accel` |
  | R-D-1              | D2/D3 仅 F1 写（#9、#10）；D1 由 E5 刷新、D4 由 E6 刷新（#3、#4） |
  | R-D-2              | 读权限严格按 §5.1：连线 #8、#14、#17–#21、#23、#24、#26、#28、#29；L1 的 #4、#10 |
  | R-L0-1             | Level 0 元素表：7 过程 + 4 存储 + E1–E9，无其它元素          |
  | R-L1-1             | Level 1 元素表：F3.1、F3.2、F3.3 三过程，链 F3.1→F3.2→F3.3   |
  | R-F2-1（A-5 引用） | F2 post `horizon >= 3.0`；F3/F5 pre `pred.horizon >= 3.0`（正文缺失见 OI-6） |
  | R-G-1              | 全部 10 个 process 均有 pre/post；§7/§8 有阈值处定量、其余定性（见第 6 节） |
  | R-G-2              | 本节矩阵                                                     |
  | R-G-3              | 所有元素均在上表或第 2.3/3.3 节元素表中有来源；建模约定见 OI-5–OI-17 |
  | R-G-4              | 2.4 / 3.4 连线清单均为命名有向流；`route` 共享由 §5.1 明定   |
  | R-G-5              | 每个输出流只有规格指定消费者（如 F3→F5、F5→F6、F6→F7、F7→E8） |
  | R-G-6              | 读字段的 post 均由输入情形守卫，如 `obj.count > 0`、`pred.object_count > 0`、`cmd.accel > 3.0` 等；无 null 检查（类型非空） |

  ### 5.2 阈值 → 模型子句

  | 阈值 | 值                                                       | 模型中的出现位置                                             |
  | ---- | -------------------------------------------------------- | ------------------------------------------------------------ |
  | N-1  | 130 km/h                                                 | F3.3 post：`ego.speed <= 36.1`                               |
  | N-2  | 警示不晚于 TTC=2.0 s                                     | F3 post `pred.min_ttc <= 2.0 → warn.active = 1`；F3.2 同名 post |
  | N-3  | 碰撞速度降低 > 30 km/h                                   | 经派生量 A-1=6.0 m/s² 落到 F3/F3.3/F5/F6 的 `6.0` 约束       |
  | N-4  | CCRm 60–130 km/h / 目标 20 km/h；CCRb −4 m/s²            | 与 N-3 一起派生 A-1（§7 派生段）；F6 post `cmd.accel <= -4.0` 对应 CCRb 减速度量级 |
  | N-5  | RSS 最小安全距离                                         | F5 post `traj.min_gap >= traj.rss_d_min`（抽象，见 OI-11）   |
  | N-6  | RSS 制动与 ρ 内加速上限                                  | F5 post `max_decel >= 4.0`；F7 post `checked.accel <= 2.0`（A-2 参数） |
  | N-7  | 横向操纵包络                                             | F6/F7 post 的 `steer <= 1.0 and steer >= -1.0`（以 A-6 代理，见 OI-15） |
  | A-1  | 6.0 m/s²                                                 | F3/F3.3 `req_decel >= 6.0`；F5 `max_decel >= 6.0`；F6 `cmd.accel <= -6.0` |
  | A-2  | ρ=0.1、a_max,accel=2.0、a_max,brake=4.0、a_min,brake=4.0 | F5 `max_accel <= 2.0`、`max_decel >= 4.0`；F6 `cmd.accel <= -4.0`；F7 `checked.accel <= 2.0` |
  | A-3  | 3.0 m/s²                                                 | F6 `cmd.accel <= 3.0`；F7 `checked.accel <= 3.0`             |
  | A-4  | 3.5 rad/s                                                | F1 post `ego.yaw_rate <= 3.5`                                |
  | A-5  | 3.0 s / 1.5 s                                            | F3、F3.2 的 3.0/1.5 风险带；F3.2 `min_ttc <= 2.0` 强化 N-2   |
  | A-6  | ±1.0                                                     | F6/F7 转向包络；F7 转向保持等式                              |
  | A-7  | 3.0 s 预测时域                                           | F2 post `horizon >= 3.0`；F3/F5 pre `pred.horizon >= 3.0`；F3.1 pre `pred.horizon > 0` |

  ------

  ## 6. 自查表：每个 process 的 pre 是否为真实约束

  | Process               | pre 子句                                                     | 真实约束依据                                               | 为何不是恒真                                         |
  | --------------------- | ------------------------------------------------------------ | ---------------------------------------------------------- | ---------------------------------------------------- |
  | F1 `f1_perception`    | `raw.frame_count > 0 and gnss.valid = 1`                     | §3 E1 帧/有效性语义、E2 validity；R-G-6                    | `frame_count: nat` 可为 0；`valid: nat` 可为 0       |
  | F2 `f2_prediction`    | `obj.count > 0`                                              | §4 D2 “object count”；§5 F2 需相关目标                     | `count: nat` 可为 0                                  |
  | F3 `f3_behaviour`     | `rules.speed_limit > 0 and route.path_length > 0 and pred.horizon >= 3.0` | §4 D4、§5 F4、A-7/R-F2-1                                   | 三项均为 `real`，非类型下界保证；`>= 3.0` 为规格阈值 |
  | F4 `f4_route`         | `ego.speed >= 0 and map.topology.lane_count > 0`             | §3 E2/D1 的速度与车道拓扑；§5 F4                           | `speed: real` 可为负；`lane_count: nat` 可为 0       |
  | F5 `f5_motion`        | `route.path_length > 0 and pred.horizon >= 3.0 and rules.speed_limit > 0` | §5 F4/F2/D4；A-7                                           | 均为 `real` 上的数值/阈值约束                        |
  | F6 `f6_control`       | `traj.horizon > 0 and ego.timestamp > 0`                     | §5 F5 “horizon duration”、§4 D3 “timestamp of last update” | `real` 字段可 <= 0                                   |
  | F7 `f7_safety_shield` | `ego.timestamp > 0 and rules.speed_limit > 0`                | §4 D3/D4；R-E-2                                            | `real` 字段可 <= 0                                   |
  | F3.1 `f3_1_ttc`       | `pred.horizon > 0`                                           | §6 F3.1 输入来自 F2；A-7                                   | `horizon: real` 可为 0；count=0 情形由 post 分支处理 |
  | F3.2 `f3_2_risk`      | `rules.speed_limit > 0`                                      | §6 F3.2 输入 D4；R-G-6                                     | `speed_limit: real` 可为 0；规则影响留 OI-10         |
  | F3.3 `f3_3_manoeuvre` | `route.path_length > 0 and ego.speed >= 0`                   | §6 F3.3 输入 route/ego state                               | `real` 字段可 <= 0 / 为负                            |

  **恒真条件排查结果**：契约中未出现 `x <> null`、`x <> ""`、`x = x`、`x >= x`、对 `nat` 的 `>= 0`、`if true then`。所有 post 守卫均为输入情形（TTC 带、计数、速度是否超限、转向/加速度是否超出包络、命令是否需保持），并在第 5.2 节对应到 N/A 条款；无阈值的功能（F1 的融合写回、F4 的路线生成、F3.1 的计数报告）使用定性 postcondition。

  **省略 pre 的 process**：无。
