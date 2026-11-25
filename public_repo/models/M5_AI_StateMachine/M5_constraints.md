# M5 — 状态机约束规格（AEB 分支）

唯一需求来源：`NL-RQ-ADAS-v1`。所有数值只取 §7 / §8；禁止自造。
布尔算子仅限 `=` `<>` `>` `>=` `<` `<=` `and`；禁止析取与取反算子；所有值默认非空，故不写空值检查表达式。

## 0. 常量与变量字典

| 符号 | 取值 | 来源 |
|---|---|---|
| `T_risk_high` | 3.0 s | §8 A-5 |
| `T_fcw` | 1.5 s | §8 A-5（与 §7 N-2 一致） |
| `A_emergency` | 6.0 m/s² | §8 A-1（由 §7 N-3/N-4 推导） |
| `warning_latest` | TTC = 2.0 s | §7 N-2 |
| `min_ttc` | F3.1 上报的最小 TTC | §6 F3.1 |
| `obj_count` | F3.1 上报的被考虑目标数，`obj_count = 0` 时无最小 TTC | §6 F3.1 |
| `driver_accel_request` | E3 中的 manual override(accelerate) | §3 E3, §6 F3.3 |
| `sensor_validity` | E1/E2 的 validity flags 合并 | §3 E1, §3 E2 |
| `odd_active` | E3 中的 ODD status | §3 E3 |
| `risk_level` | `no_risk` / `caution` / `critical` | §6 F3.2 |
| `maneuver.deceleration` | 机动要求的减速度 | §6 F3.3 |
| `maneuver.target_speed` | 机动目标速度 | §6 F3.3 |
| `checked_cmd` | F7 仲裁后的 E8 | §3 E8, §5 F7, R-E-2 |

---

## 1. 状态不变式（invariant）

### S1 `Normal`
- INV-N1 `risk_level = no_risk` — §6 F3.2
- INV-N2 `warning = none` — §6 F3.2, §3 E7, R-E-1
- INV-N3 `maneuver = cruise` — §6 F3.3
- INV-N4（仅 `obj_count > 0` 时成立）`min_ttc > 3.0` — §8 A-5, §6 F3.2
- INV-N5 `odd_active = true and sensor_validity = true` — §3 E3, E1, E2（活动态前提）

### S2 `Caution`
- INV-C1 `risk_level = caution` — §6 F3.2
- INV-C2 `min_ttc <= 3.0 and min_ttc > 1.5` — §8 A-5（caution 波段定义）
- INV-C3 `warning = caution` — §6 F3.2, §7 N-2
- INV-C4 `maneuver = deceleration and maneuver.deceleration > 0` — §6 F3.3（非零减速度）
- INV-C5 `odd_active = true and sensor_validity = true` — §3 E3, E1, E2

### S3 `EmergencyBrake`（组合状态）
- INV-E1 `risk_level = critical` — §6 F3.2
- INV-E2 `min_ttc <= 1.5` — §8 A-5, §7 N-2
- INV-E3 `warning = imminent_collision` — §6 F3.2, §3 E7
- INV-E4 `maneuver = emergency_deceleration and maneuver.deceleration >= 6.0 and maneuver.target_speed = 0` — §6 F3.3, §8 A-1
- INV-E5 `checked_cmd.deceleration >= 6.0` — §8 A-1, §3 E8, R-E-2
- INV-E6 `odd_active = true and sensor_validity = true` — §3 E3, E1, E2

子状态（层次化）：
- S3.a `BrakeRamp`: `maneuver.deceleration >= 6.0 and ego_speed > 0` — §8 A-1, §4 D3
- S3.b `Standstill`: `ego_speed = 0 and checked_cmd.target_speed = 0` — §6 F3.3, §3 E8

### S4 `DriverOverride`
- INV-D1 `driver_accel_request = true` — §3 E3, §6 F3.3
- INV-D2 `risk_level <> critical` — §6 F3.3（critical 时驾驶员加速请求不得劫持）
- INV-D3 `maneuver = driver_accelerate` — §6 F3.3
- INV-D4 `odd_active = true and sensor_validity = true` — §3 E3, E1, E2

### S5 `FaultDegraded`（合成状态，见 OI-5）
- INV-F1 `sensor_validity = false` — §3 E1, E2
- INV-F2 `warning = retained and maneuver = retained` — OI-5（`retained` = 进入前源状态的输出值，保守保持）

### S6 `Deactivated`（合成状态，见 OI-5）
- INV-X1 `odd_active = false` — §3 E3
- INV-X2 `warning = none and maneuver = cruise` — OI-5（AEB 退出后安全降级假设）

---

## 2. 迁移前置/后置约束

每条迁移都给出 `guard` / `pre` / `post`，并标注条款；`quantified=true` 表示含 §7/§8 数值比较。

### T1 `Normal -> Caution`
- guard `min_ttc <= 3.0 and min_ttc > 1.5` — §8 A-5, §6 F3.2
- pre `sensor_validity = true and odd_active = true and obj_count > 0` — §3 E1/E2/E3, §6 F3.1
- post `warning = caution and maneuver = deceleration and maneuver.deceleration > 0` — §6 F3.2, F3.3
- quantified: true（3.0, 1.5）

### T2 `Caution -> Normal`
- guard `min_ttc > 3.0` — §8 A-5
- pre `warning = caution and obj_count > 0` — §6 F3.2, F3.1
- post `warning = none and maneuver = cruise` — §6 F3.2, F3.3
- quantified: true（3.0）

### T3 `Caution -> EmergencyBrake`
- guard `min_ttc <= 1.5` — §8 A-5, §7 N-2
- pre `warning = caution and sensor_validity = true and odd_active = true` — §6 F3.2, §3 E1/E2/E3
- post `warning = imminent_collision and maneuver = emergency_deceleration and maneuver.deceleration >= 6.0 and maneuver.target_speed = 0 and checked_cmd.deceleration >= 6.0` — §6 F3.2/F3.3, §8 A-1, §3 E8, R-E-2
- quantified: true（1.5, 6.0）
- 说明：`warning` 在 TTC = 1.5 s 已发出，早于 §7 N-2 的 2.0 s 上限，满足 N-2。

### T4 `EmergencyBrake -> Caution`
- guard `min_ttc > 1.5 and min_ttc <= 3.0` — §8 A-5
- pre `warning = imminent_collision and maneuver.deceleration >= 6.0` — §6 F3.2, §8 A-1
- post `warning = caution and maneuver = deceleration and maneuver.deceleration > 0` — §6 F3.2/F3.3
- quantified: true（1.5, 3.0）

### T5 `EmergencyBrake -> Normal`
- guard `min_ttc > 3.0` — §8 A-5
- pre `warning = imminent_collision and obj_count > 0` — §6 F3.2/F3.1
- post `warning = none and maneuver = cruise` — §6 F3.2/F3.3
- quantified: true（3.0）

### T6 `Caution -> Normal`（空目标集）
- guard `obj_count = 0` — §6 F3.1
- pre `warning = caution and obj_count = 0` — §6 F3.1/F3.2
- post `warning = none and maneuver = cruise` — §6 F3.2/F3.3（按 no risk 处理；见 OI-7）
- quantified: false

### T7 `EmergencyBrake -> Normal`（空目标集）
- guard `obj_count = 0` — §6 F3.1
- pre `warning = imminent_collision and obj_count = 0` — §6 F3.1/F3.2
- post `warning = none and maneuver = cruise` — §6 F3.2/F3.3, OI-7
- quantified: false

### T8 `DriverOverride -> Normal`（空目标集）
- guard `obj_count = 0` — §6 F3.1
- pre `driver_accel_request = true and obj_count = 0` — §3 E3, §6 F3.1
- post `warning = none and maneuver = cruise` — §6 F3.2/F3.3, OI-7
- quantified: false

### T9 `Normal -> DriverOverride`
- guard `driver_accel_request = true and min_ttc > 3.0` — §3 E3, §6 F3.3, §8 A-5
- pre `risk_level = no_risk and odd_active = true` — §6 F3.2, §3 E3
- post `maneuver = driver_accelerate and warning = none` — §6 F3.3, F3.2
- quantified: true（3.0）

### T10 `Caution -> DriverOverride`
- guard `driver_accel_request = true and min_ttc <= 3.0 and min_ttc > 1.5` — §3 E3, §8 A-5, §6 F3.3
- pre `risk_level = caution and warning = caution` — §6 F3.2
- post `maneuver = driver_accelerate and warning = caution` — §6 F3.3（caution 下警告仍按 F3.2 保留）
- quantified: true（3.0, 1.5）

### T11 `DriverOverride -> Normal`
- guard `driver_accel_request = false and min_ttc > 3.0` — §3 E3, §8 A-5
- pre `driver_accel_request = true and risk_level = no_risk` — §3 E3, §6 F3.2
- post `maneuver = cruise and warning = none` — §6 F3.3/F3.2
- quantified: true（3.0）

### T12 `DriverOverride -> Caution`
- guard `driver_accel_request = false and min_ttc <= 3.0 and min_ttc > 1.5` — §3 E3, §8 A-5
- pre `driver_accel_request = true and risk_level = caution` — §3 E3, §6 F3.2
- post `maneuver = deceleration and warning = caution and maneuver.deceleration > 0` — §6 F3.3/F3.2
- quantified: true（3.0, 1.5）

### T13 `DriverOverride -> EmergencyBrake`
- guard `min_ttc <= 1.5` — §8 A-5, §7 N-2
- pre `driver_accel_request = true and min_ttc <= 1.5` — §3 E3, §8 A-5
- post `warning = imminent_collision and maneuver = emergency_deceleration and maneuver.deceleration >= 6.0 and maneuver.target_speed = 0 and checked_cmd.deceleration >= 6.0` — §6 F3.3（紧急机动不得被驾驶员加速请求覆盖）, §8 A-1
- quantified: true（1.5, 6.0）

### T14 `Normal -> FaultDegraded`
- guard `sensor_validity = false` — §3 E1, E2
- pre `risk_level = no_risk` — §6 F3.2
- post `warning = none and maneuver = cruise` — OI-5（保持源输出）
- quantified: false

### T15 `Caution -> FaultDegraded`
- guard `sensor_validity = false` — §3 E1, E2
- pre `warning = caution` — §6 F3.2
- post `warning = caution and maneuver = deceleration` — OI-5
- quantified: false

### T16 `EmergencyBrake -> FaultDegraded`
- guard `sensor_validity = false` — §3 E1, E2
- pre `warning = imminent_collision and maneuver.deceleration >= 6.0` — §6 F3.2, §8 A-1
- post `warning = imminent_collision and maneuver = emergency_deceleration` — OI-5
- quantified: false

### T17 `DriverOverride -> FaultDegraded`
- guard `sensor_validity = false` — §3 E1, E2
- pre `driver_accel_request = true` — §3 E3
- post `warning = none and maneuver = driver_accelerate` — OI-5
- quantified: false

### T18 `FaultDegraded -> Normal`
- guard `sensor_validity = true and min_ttc > 3.0` — §3 E1/E2, §8 A-5
- pre `sensor_validity = false and odd_active = true` — §3 E1/E2/E3
- post `warning = none and maneuver = cruise` — §6 F3.2/F3.3
- quantified: true（3.0）

### T19 `FaultDegraded -> Caution`
- guard `sensor_validity = true and min_ttc <= 3.0 and min_ttc > 1.5` — §3 E1/E2, §8 A-5
- pre `sensor_validity = false and odd_active = true` — §3 E1/E2/E3
- post `warning = caution and maneuver = deceleration and maneuver.deceleration > 0` — §6 F3.2/F3.3
- quantified: true（3.0, 1.5）

### T20 `FaultDegraded -> EmergencyBrake`
- guard `sensor_validity = true and min_ttc <= 1.5` — §3 E1/E2, §8 A-5
- pre `sensor_validity = false and odd_active = true` — §3 E1/E2/E3
- post `warning = imminent_collision and maneuver = emergency_deceleration and maneuver.deceleration >= 6.0 and maneuver.target_speed = 0` — §6 F3.3, §8 A-1
- quantified: true（1.5, 6.0）

### T21 `Normal -> Deactivated`
- guard `odd_active = false` — §3 E3
- pre `risk_level = no_risk` — §6 F3.2
- post `warning = none and maneuver = cruise` — OI-5
- quantified: false

### T22 `Caution -> Deactivated`
- guard `odd_active = false` — §3 E3
- pre `warning = caution` — §6 F3.2
- post `warning = none and maneuver = cruise` — OI-5
- quantified: false

### T23 `EmergencyBrake -> Deactivated`
- guard `odd_active = false` — §3 E3
- pre `warning = imminent_collision` — §6 F3.2
- post `warning = none and maneuver = cruise` — OI-5
- quantified: false

### T24 `DriverOverride -> Deactivated`
- guard `odd_active = false` — §3 E3
- pre `driver_accel_request = true` — §3 E3
- post `warning = none and maneuver = cruise` — OI-5
- quantified: false

### T25 `FaultDegraded -> Deactivated`
- guard `odd_active = false` — §3 E3
- pre `sensor_validity = false` — §3 E1/E2
- post `warning = none and maneuver = cruise` — OI-5
- quantified: false

### T26 `Deactivated -> Normal`
- guard `odd_active = true` — §3 E3
- pre `odd_active = false` — §3 E3
- post `warning = none and maneuver = cruise` — §6 F3.2/F3.3（重入后下一个规划周期重新分类）
- quantified: false

### T27 `BrakeRamp -> Standstill`（EmergencyBrake 内部）
- guard `ego_speed = 0` — §6 F3.3（target speed = 0）, §4 D3
- pre `maneuver.deceleration >= 6.0` — §8 A-1
- post `checked_cmd.target_speed = 0 and checked_cmd.brake = active` — §3 E8, §5 F7, R-E-2
- quantified: false

---

## 3. 结构性约束（可检验）

- SC-1 不存在 `EmergencyBrake -> DriverOverride` 的迁移：critical 时驾驶员加速请求不得覆盖紧急机动 — §6 F3.3。
- SC-2 同一源状态的迁移优先级为 `odd_active = false` > `sensor_validity = false` > TTC 波段守卫；保证守卫互斥、无二义迁移 — §3 E3, E1, E2；OI-5。
- SC-3 状态机只产生两类输出：`warning`（E7）与 `checked_cmd`（E8） — §3 R-E-1, §5 F7。
- SC-4 `checked_cmd` 必须由对 `actuator_cmd`（E9）的监控/仲裁得到，E9 不得直达执行器 — §3 R-E-2, §5 F7。
- SC-5 所有数值比较只引用 §7/§8 常量：`3.0` / `1.5` / `6.0` / `2.0` — §7, §8, R-G-1。
- SC-6 不写空值检查表达式：所有值默认非空 — 任务约束 / §9 R-G-6。
- SC-7 `maneuver` 由 F3.3 决定，`warning` 由 F3.2 决定，`min_ttc` 由 F3.1 上报；状态机不引入第四个 Level-1 功能 — §6 R-L1-1。
- SC-8 A-1（6.0 m/s²）超出 A-3（3.0 m/s²）舒适纵向加速度上限，紧急分支作为安全例外由 F7 仲裁放行 — §8 A-1/A-3, §5 F7；见 OI-6。
