# M4 — OCL 约束清单（AI 生成的面向对象模型 / UML）

| 项 | 值 |
|---|---|
| 模型 | M4 — LLM-generated object-oriented model (UML) |
| 唯一需求来源 | `NL-RQ-ADAS-v1_需求规格.md` |
| provenance | producer = llm, passes = **1**, self_review_performed = **false** |
| 约束语法 | OCL 子集：`=` `<>` `>` `>=` `<` `<=` `and`（**不使用 `or` / `not`**） |
| 属性类型 | 仅 `real` / `nat` / `String` |
| 守卫式约束写法 | `<guard> | <effect>`：若 `<guard>` 成立，则 `<effect>` 必须成立 |
| 阈值来源 | 仅规格 §7（N-1…N-7）与 §8（A-1…A-7）；未自造任何数值 |

> **守卫与析取的处理**：布尔算子集不含 `or`，因此任何析取（如“no risk 时为 cruise *或* keep-lane”）
> 一律拆成 **多条同守卫的约束**（每条分别蕴含该析取项），或用 MES 的 `guard` / `effect` 字段表达。
> 枚举型取值域（`warning_type`、`manoeuvre_type`、`risk_level`）以 note 形式给出，不进入可执行约束。

---

## 1. F1 — Perception & Localisation

| ID | 类别 | 约束表达式 | 对应需求条款 |
|---|---|---|---|
| C-F1-1 | pre | `raw_sensor_data <> null and gnss_imu <> null` | R-G-1, R-G-6, F1 |
| C-F1-2 | pre | `hd_map_segment <> null` | R-G-6, R-D-2, F1 |
| C-F1-3 | post | `object_count >= 0 and lead_object_id <> ''` | F1, R-G-1 |
| C-F1-4 | post | `ego_speed_ms >= 0.0` | F1, R-G-1 |
| C-F1-5 | invariant | `ego_yaw_rate_rad_s <= 3.5 and ego_yaw_rate_rad_s >= -3.5` | **A-4** |
| C-F1-6 | invariant | `ego_state_ts >= 0` | F1, R-G-1 |

补充（非 OCL，结构性）：F1 **写** D2、D3，**不读** D2、D3；F1 是 `ego_state` 与 `object_table` 的唯一生产者。

## 2. F2 — Prediction

| ID | 类别 | 约束表达式 | 对应需求条款 |
|---|---|---|---|
| C-F2-1 | pre | `object_table <> null and ego_state <> null` | R-G-1, R-G-6, F2 |
| C-F2-2 | pre | `hd_map_segment <> null` | R-G-6, R-D-2, F2 |
| C-F2-3 | post | `prediction_horizon_s >= 3.0` | **A-7**, F2（“at least 3 s”） |
| C-F2-4 | post | `min_ttc_s >= 0.0` | F2, R-G-1 |
| C-F2-5 | invariant（结构性） | TTC 只在 F2 内计算；F2 不得写任何 store | F2 |

## 3. F3 — Behaviour Planning

| ID | 类别 | 约束表达式 | 对应需求条款 |
|---|---|---|---|
| C-F3-1 | pre | `ego_state <> null and predicted_trajectories <> null and min_ttc_s >= 0.0` | R-G-1, R-G-6, F3 |
| C-F3-2 | pre | `driver_intent <> null and route <> null and traffic_rules <> null and hd_map_segment <> null` | R-G-6, R-D-2, F3 |
| C-F3-3 | post | `manoeuvre_type <> '' and target_speed_kmh >= 0.0 and target_lane_id <> ''` | F3, R-G-1 |
| C-F3-4 | post（guard `risk_level = 'critical'`） | `required_decel_ms2 >= 6.0 and target_speed_kmh = 0.0` | **A-1**（由 N-3/N-4 推导） |
| C-F3-5 | post（guard `risk_level = 'critical'`） | `ego_speed_kmh <= 130.0` | **N-1** |
| C-F3-6 | post（guard `ttc_min_s <= 2.0`） | `warning_type <> 'none'` | **N-2** |
| C-F3-7 | post（guard `risk_level = 'critical'`） | `warning_type = 'imminent collision' and warning_active = 'true'` | F3, §6 F3.2 |
| C-F3-8 | post（guard `risk_level = 'no_risk'`） | `warning_type = 'none' and warning_active = 'false'` | §6 F3.2 |
| C-F3-9 | post | `target_speed_kmh <= speed_limit_kmh` | F3（遵守 D4 交通规则） |
| C-F3-10 | post（guard `risk_level = 'caution'`） | `required_decel_ms2 > 0.0` | §6 F3.3（非零减速需求） |
| C-F3-11 | post | `gap_to_lead_m >= d_min_rss_m` | **N-5**（`d_min_rss_m` 按 N-5 / A-2 参数集计算；强制方未指定，见 OI-13） |

## 4. F4 — Route Planning

| ID | 类别 | 约束表达式 | 对应需求条款 |
|---|---|---|---|
| C-F4-1 | pre | `destination <> null and ego_pose <> null and hd_map_segment <> null` | R-G-6, R-D-2, F4 |
| C-F4-2 | post | `route_length_m >= 0.0 and eta_s >= 0.0` | F4, R-G-1 |
| C-F4-3 | post | `route_lane_geometry <> ''` | F4（供 F3/F5 使用的车道几何） |

## 5. F5 — Motion Planning

| ID | 类别 | 约束表达式 | 对应需求条款 |
|---|---|---|---|
| C-F5-1 | pre | `manoeuvre <> null and route <> null and ego_state <> null` | R-G-6, F5 |
| C-F5-2 | post | `max_permitted_speed_kmh <= speed_limit_kmh` | F5（F5 不得超速） |
| C-F5-3 | post | `horizon_duration_s >= 0.0 and max_permitted_accel_ms2 >= 0.0` | F5, R-G-1 |
| C-F5-4 | post | `trajectory_decel_capability_ms2 >= manoeuvre.required_decel_ms2` | F5（兑现减速需求） |
| C-F5-5 | post（guard `manoeuvre.risk_level = 'critical'`） | `trajectory_decel_capability_ms2 >= 6.0` | **A-1** |
| C-F5-6 | post | `commanded_lateral_accel_ms2 <= a_lat_max_ms2` | **N-7**（规格未给数值 → 定性约束，见 OI-8） |

## 6. F6 — Control

| ID | 类别 | 约束表达式 | 对应需求条款 |
|---|---|---|---|
| C-F6-1 | pre | `trajectory <> null and ego_state <> null` | R-G-6, F6 |
| C-F6-2 | post | `accel_cmd_ms2 <= 3.0 and accel_cmd_ms2 >= -6.0` | **A-3**（加速侧）/ **A-1**（制动侧） |
| C-F6-3 | post | `steering_cmd <= 1.0 and steering_cmd >= -1.0` | **A-6** |
| C-F6-4 | post | `brake_cmd_ms2 >= 0.0 and brake_cmd_ms2 <= 6.0` | **A-1**（执行器包络上界；见 OI-7） |

## 7. F7 — Safety Shield (monitoring & arbitration)

| ID | 类别 | 约束表达式 | 对应需求条款 |
|---|---|---|---|
| C-F7-1 | pre | `actuator_cmd <> null and ego_state <> null and traffic_rules <> null` | R-G-6, F7 |
| C-F7-2 | post | `checked_accel_cmd_ms2 <= 3.0 and checked_accel_cmd_ms2 >= -6.0` | **A-3** / **A-1** |
| C-F7-3 | post | `checked_brake_cmd_ms2 >= 0.0 and checked_brake_cmd_ms2 <= 6.0` | **A-1** |
| C-F7-4 | post | `checked_steering_cmd <= 1.0 and checked_steering_cmd >= -1.0` | **A-6** |
| C-F7-5 | post | `checked_speed_cmd_kmh <= speed_limit_kmh` | F7（在最终指令上强制 D4） |
| C-F7-6 | post（guard `dangerous_situation = 'true'`） | `checked_brake_cmd_ms2 >= 4.0` | **N-6**（`a_min,brake`）, **A-2** |
| C-F7-7 | post（guard `response_time_s <= 0.1`） | `checked_accel_cmd_ms2 <= 2.0` | **N-6**（`ρ`、`a_max,accel`）, **A-2** |
| C-F7-8 | post（guard `actuator_cmd.accel_cmd_ms2 < -6.0`） | `checked_accel_cmd_ms2 >= -6.0` | F7（即使 F6 违规也须输出合规指令）, R-E-2 |
| C-F7-9 | post（guard `steering_within_envelope = 'true'`） | `checked_steering_cmd = actuator_cmd.steering_cmd` | F7（保留 F6 的转向指令） |
| C-F7-10 | invariant（结构性） | F7 的输出是到达 E8 的唯一通路；原始指令 E9 不得直达执行器 | R-E-1, R-E-2 |

## 8. 实体类（store）上的约束

| ID | 元素 | 约束表达式 | 对应需求条款 |
|---|---|---|---|
| C-D1-1 | D1 | `posted_speed_limit_kmh > 0.0` | D1, F5, R-G-1 |
| C-D2-1 | D2 | `object_count >= 0` | D2, R-G-1 |
| C-D3-1 | D3 | `ego_speed_ms >= 0.0` | D3, R-G-1 |
| C-D3-2 | D3 | `ego_yaw_rate_rad_s <= 3.5 and ego_yaw_rate_rad_s >= -3.5` | **A-4** |
| C-D4-1 | D4 | `posted_speed_limit_kmh > 0.0` | D4, R-G-1 |

## 9. 外部接口（actor / port）上的约束

| ID | 元素 | 约束表达式 | 对应需求条款 |
|---|---|---|---|
| C-E1-1 | E1 | `raw_sensor_data <> null` | E1, R-G-6 |
| C-E2-1 | E2 | `gnss_imu <> null` | E2, R-G-6 |
| C-E3-1 | E3 | `driver_intent <> null` | E3, R-G-6 |
| C-E4-1 | E4 | `destination <> null` | E4, R-G-6 |
| C-E5-1 | E5 | `map_data <> null` | E5, R-G-6 |
| C-E6-1 | E6 | `traffic_rules <> null` | E6, R-G-6 |
| C-E7-1 | E7 | `warning_type <> '' and warning_active <> ''` | E7, R-E-1 |
| C-E8-1 | E8 | `checked_steering_cmd <= 1.0 and checked_steering_cmd >= -1.0` | E8, **A-6** |
| C-E9-1 | E9 | `accel_cmd_ms2 <= 3.0 and accel_cmd_ms2 >= -6.0` | E9, **A-3** / **A-1** |
| C-E9-2 | E9 | `steering_cmd <= 1.0 and steering_cmd >= -1.0` | E9, **A-6** |

## 10. Level 1 细化（F3.1 / F3.2 / F3.3）

### F3.1 — TTC Computation

| ID | 类别 | 约束表达式 | 对应需求条款 |
|---|---|---|---|
| C-L1-16 | pre | `predicted_trajectories <> null and ego_state <> null` | F3.1, R-G-6 |
| C-L1-1 | post | `considered_object_count >= 0 and ttc_min_s >= 0.0` | F3.1, R-G-1 |
| C-L1-2 | post（guard `considered_object_count = 0`） | `considered_object_count = 0` | F3.1（空集合报告计数 0） |
| C-L1-19 | post | `horizon_s >= 3.0` | **A-7**（在 F2 的预测视界上求 TTC） |

### F3.2 — Risk Classification

| ID | 类别 | 约束表达式 | 对应需求条款 |
|---|---|---|---|
| C-L1-17 | pre | `ttc_set <> null and traffic_rules <> null` | F3.2, R-G-6 |
| C-L1-3 | post（guard `risk_level = 'no_risk'`） | `ttc_min_s > 3.0` | **A-5**（`T_risk_high`） |
| C-L1-4 | post（guard `risk_level = 'caution'`） | `ttc_min_s <= 3.0 and ttc_min_s > 1.5` | **A-5** |
| C-L1-5 | post（guard `risk_level = 'critical'`） | `ttc_min_s <= 1.5` | **A-5**（`T_fcw`） |
| C-L1-13 | post（guard `risk_level = 'caution'`） | `warning_type = 'caution' and warning_active = 'true'` | F3.2 |
| C-L1-14 | post（guard `risk_level = 'critical'`） | `warning_type = 'imminent collision' and warning_active = 'true'` | F3.2 |
| C-L1-15 | post（guard `risk_level = 'no_risk'`） | `warning_type = 'none' and warning_active = 'false'` | F3.2 |
| C-L1-6 | post（guard `ttc_min_s <= 2.0`） | `warning_type <> 'none'` | **N-2** |

### F3.3 — Maneuver Planning

| ID | 类别 | 约束表达式 | 对应需求条款 |
|---|---|---|---|
| C-L1-18 | pre | `risk_level <> '' and ego_state <> null and driver_intent <> null and route <> null and hd_map_segment <> null` | F3.3, R-G-6 |
| C-L1-7 | post（guard `risk_level = 'no_risk'`） | `manoeuvre_type = 'cruise'` | F3.3 |
| C-L1-7b | post（guard `risk_level = 'no_risk'`） | `manoeuvre_type = 'keep_lane'` | F3.3（与 C-L1-7 共同表达析取） |
| C-L1-8 | post（guard `risk_level = 'caution'`） | `required_decel_ms2 > 0.0` | F3.3 |
| C-L1-9 | post（guard `risk_level = 'critical'`） | `required_decel_ms2 >= 6.0 and target_speed_kmh = 0.0` | **A-1**, F3.3 |
| C-L1-10 | post（guard `risk_level = 'critical'`） | `ego_speed_kmh <= 130.0` | **N-1** |
| C-L1-11 | post（guard `driver_accel_request = 'true' and risk_level = 'critical'`） | `required_decel_ms2 >= 6.0 and target_speed_kmh = 0.0` | F3.3（紧急动作不被加速请求覆盖） |
| C-L1-12 | post（guard `driver_accel_request = 'true' and risk_level <> 'critical'`） | `manoeuvre_type <> 'emergency_deceleration' and required_decel_ms2 >= 0.0` | F3.3（其余风险等级下加速请求优先） |

---

## 11. 阈值 → 约束 的完整覆盖表

| 阈值 ID | 取值 | 出现在约束 |
|---|---|---|
| N-1 | 130 km/h | C-F3-5, C-L1-10 |
| N-2 | 2.0 s | C-F3-6, C-L1-6 |
| N-3 | 冲击速度降低 > 30 km/h | C-F3-4（经 A-1 = 6.0 m/s² 体现），C-F5-5, C-F6-4, C-F7-2, C-F7-3 |
| N-4 | CCRm：VUT 60–130 km/h，目标 20 km/h，目标 −4 m/s² | C-F3-4 / C-F5-5（A-1 的推导前提，追溯于 F3.3、F6） |
| N-5 | RSS 纵向安全距离 `d_min` | C-F3-11（强制方未指定 → OI-9） |
| N-6 | RSS 制动曲线（`a_min,brake`，`a_max,accel`，`ρ`） | C-F7-6, C-F7-7 |
| N-7 | 横向加速度包络（无数值） | C-F5-6（定性 → OI-4） |
| A-1 | 6.0 m/s² | C-F3-4, C-F5-5, C-F6-2, C-F6-4, C-F7-2, C-F7-3, C-L1-9, C-L1-11 |
| A-2 | ρ=0.1, a_max,accel=2.0, a_max,brake=4.0, a_min,brake=4.0 | C-F7-6, C-F7-7, C-F3-11 |
| A-3 | 3.0 m/s² | C-F6-2, C-F7-2, C-E9-1 |
| A-4 | 3.5 rad/s | C-F1-5, C-D3-2 |
| A-5 | 3.0 s / 1.5 s | C-L1-3, C-L1-4, C-L1-5 |
| A-6 | ±1.0 | C-F6-3, C-F7-4, C-E8-1, C-E9-2 |
| A-7 | 3.0 s | C-F2-3, C-L1-19 |

> 规格 §7 “Derived threshold” 中的 30 km/h、110 km/h、30.6 m/s、8.33 m/s、1.39 s、≈37 m、0.61 g
> 属**推导中间量**，未作为约束值写入模型；模型只使用 §8 正式列出的 A-1 = 6.0 m/s²。
> 模型中出现的所有数值仅限：0、0.1、1.0、1.5、2.0、3.0、3.5、4.0、6.0、130.0 及规格 §7/§8 中的其余取值。
