# NL-RQ-ADAS-v1 — SOFL 形式化规格交付物（M2：LLM 生成 SOFL）

**文档名**：`MiniMax-M3.1-Flash-无禁令-1.md`（生成模型：MiniMax-M3.1-Flash；条件：无禁令；序号：1）
**唯一输入**：`NL-RQ-ADAS-v1_spec.md` v1.0（`C:/Users/zct11/WorkBuddy/2026-11-11-20-16-46/NL-RQ-ADAS-v1_spec.md`）
**交付范围**：模块 `ADAS_System`（Level 0）与 `AEB_Branch`（Level 1）、两张 CDFD、open-issues 列表、可追溯性矩阵
**建模原则**：只建模规格写明的内容；规格沉默之处不作发明，一律进入 §6 open-issues。

---

## 0. 记法约定（SOFL 子集）

本模型使用的 SOFL 子集严格限定为任务书给定的语法：

| 构件 | 形式 | 说明 |
|---|---|---|
| module head | `\| \| \|` 表；`( ... )` 为输入端口，其后为输出端口 | 端口内条目为 `名: 类型`；同端口多条流用 `,` 分隔，不同端口用 `\|` 分隔 |
| 类型 | `Name = composed of field1: real, field2: nat, field3: String end` | 可嵌套引用其它 composed 类型；本模型仅使用 `real / nat / String` 与 composed 类型 |
| 过程 | `process 名(入参) out: 出参` | 形参即 CDFD 中进入该过程的箭头 |
| 存储访问 | `ext rd 存储名` / `ext wr 存储名` | 与 CDFD 的读/写连线一一对应 |
| 条件 | `pre <谓词>`、`post <谓词>`、`post if <守卫> then <谓词>` | 无条件 post 用 `post`，条件 post 用守卫形式 |
| 算子 | `and`、`=`、`<>`、`>`、`>=`、`<=`、`<`、`.`（字段访问） | **未使用** `or`、`not`、`=>`、量词、`seq of` |

三条因算子受限而采用的表达约定（均不引入新语义）：

1. **存储内容绑定**：`ext rd <store>` 声明的读取内容，绑定到该过程签名中同类型的形参；CDFD 上体现为 `store → process` 的读连线。
2. **封闭值域用排除法表达**：因无 `or`，"取值为集合中任一成员"改写为"排除集合中其余成员"（见 `F3_3_Maneuver_Planning` 的 `no_risk` 分支）。
3. **非空守卫**：`pre` 中要求某数据的场合一律写 `<datum> <> null`；`post` 中读取输入数据字段处一律带守卫（满足 R-G-6）。

**记号映射**：规格元素 → 模型元素
`F1..F7` → `F1_Perception_Localisation / F2_Prediction / F3_Behaviour_Planning / F4_Route_Planning / F5_Motion_Planning / F6_Control / F7_Safety_Shield`；
`D1..D4` → 同名；`E1..E9` → 模块端口与 CDFD 外部终端同名。

---

## 1. 模块 `ADAS_System`（Level 0，整车级）

模块清单核对（R-L0-1）：**7 个过程**（F1–F7）、**4 个数据存储**（D1–D4）、**9 个外部接口**（E1–E9），无其它元素。

```sofl
-- =====================================================================
-- Module: ADAS_System  --  Level 0, vehicle-level ADAS onboard system
-- Input specification : NL-RQ-ADAS-v1 (v1.0)
-- Elements             : exactly F1..F7 (processes), D1..D4 (stores),
--                        E1..E9 (external interfaces)  -- R-L0-1
--
-- SOFL subset conventions used in this module
--   module head : | ... | table;  "( ... )" = input ports, then output ports
--   types       : Name = composed of <field> : <type>, ... end
--   process     : process <name>(<formal inputs>) out: <formal outputs>
--   store access: ext rd <store>   (read-only)
--                 ext wr <store>   (write)
--   conditions : pre  <predicate>
--                post <predicate>
--                post if <guard> then <predicate>
--   operators  : and  =  <>  >  >=  <=  <  . (field access)
--                [ no or / not / => / quantifiers / seq of ]
--   store bind : the content of a store declared by "ext rd" is bound to the
--                formal input of the same type in the process signature
--   null guard : "<datum> <> null" states non-nullness (R-G-6)
--   exclusion  : because "or" is not available, closed value sets are
--                specified by excluding the unwanted members
-- =====================================================================

module ADAS_System

|  |  |
| --- | --- | --- |
( raw_sensor_data: SensorFrame | gnss_imu: GnssImu | driver_intent: DriverIntent | destination: Destination | map_data: MapSegment | traffic_rules: TrafficRules | actuator_cmd: ActuatorCommand ) warning: WarningSignal | checked_cmd: ActuatorCommand
|  |  |
| --- | --- | --- |

-- ---------------------------------------------------------------------
-- TYPES
-- ---------------------------------------------------------------------

-- E1 : time-synchronised sensor frames, per-sensor validity flag + timestamp
--      (§3 E1)
SensorFrame = composed of
  sensor_id: nat,
  timestamp: real,
  valid: nat
end

-- E2 : GNSS fix and IMU samples with validity flags (§3 E2)
GnssImu = composed of
  gnss_valid: nat,
  imu_valid: nat,
  position_x: real,
  position_y: real,
  heading: real,
  angular_rate: real,
  acceleration: real
end

-- E3 : driver command / ODD status from the HMI (§3 E3)
DriverIntent = composed of
  requested_cruise_speed: real,
  override_accelerate: nat,
  override_brake: nat,
  override_steer: real,
  driver_attention: nat
end

-- E4 : navigation destination and route preferences (§3 E4)
Destination = composed of
  longitude: real,
  latitude: real,
  route_preferences: String
end

-- E5 / D1 : HD-map segment for the current road (§3 E5, §4 D1)
MapSegment = composed of
  road_id: String,
  lane_id: String,
  posted_speed_limit: real,
  curvature: real,
  lane_topology: String
end

-- E6 / D4 : currently applicable traffic rules (§3 E6, §4 D4)
TrafficRules = composed of
  posted_speed_limit: real,
  traffic_signal_state: nat
end

-- E7 : driver-facing warning signal, type + active flag (§3 E7)
--      warning_type domain : none | caution | imminent_collision
WarningSignal = composed of
  warning_type: String,
  active: nat
end

-- E8 / E9 : actuation command -- longitudinal acceleration, brake, steering
--           (§3 E8, E9)
ActuatorCommand = composed of
  accel_cmd: real,
  brake_cmd: real,
  steer_cmd: real
end

-- D3 : ego state store content (§4 D3)
EgoState = composed of
  x: real,
  y: real,
  yaw: real,
  speed: real,
  yaw_rate: real,
  acceleration: real,
  last_update: real
end

-- ego pose delivered by F1 to F4 (§5 F1, §5.1)
EgoPose = composed of
  x: real,
  y: real,
  yaw: real
end

-- D2 : fused object table content (§4 D2)
ObjectKinematics = composed of
  object_id: nat,
  x: real,
  y: real,
  vx: real,
  vy: real,
  object_class: nat
end

ObjectTable = composed of
  object_count: nat,
  lead_object_id: nat,
  lead_object: ObjectKinematics
end

-- F2 output : predicted trajectories and the derived minimum TTC (§5 F2)
PredictedTrajectory = composed of
  object_id: nat,
  horizon: real,
  predicted_x: real,
  predicted_y: real,
  predicted_speed: real
end

PredictionSet = composed of
  horizon: real,
  object_count: nat,
  min_ttc: real,
  lead_trajectory: PredictedTrajectory
end

-- F3 output : target manoeuvre (§5 F3)
--   manoeuvre_type domain : cruise | keep_lane | lane_change |
--                            lane_keep_deceleration | emergency_deceleration
Manoeuvre = composed of
  manoeuvre_type: String,
  target_speed: real,
  target_lane: String,
  required_decel: real
end

-- F4 output : route to the destination (§5 F4)
Route = composed of
  path_length: real,
  eta: real,
  lane_geometry: String
end

-- F5 output : kinematically feasible trajectory (§5 F5)
--   max_decel, min_gap_to_lead and rss_safe_distance extend the field list
--   stated in §5 F5 -- see OI-22 (open issues).
Trajectory = composed of
  max_speed: real,
  max_accel: real,
  max_decel: real,
  horizon_duration: real,
  min_gap_to_lead: real,
  rss_safe_distance: real
end

-- ---------------------------------------------------------------------
-- PROCESSES  (Level 0 -- exactly the seven functions of §5)
-- ---------------------------------------------------------------------

-- F1 -- Perception & Localisation (§5 F1)
--   reads D1; writes D2 and D3; does not read D2 or D3 (§5 F1)
process F1_Perception_Localisation(raw_sensor_data: SensorFrame, gnss_imu: GnssImu, map_segment: MapSegment) out: object_table: ObjectTable, ego_state: EgoState, ego_pose: EgoPose
ext rd D1
ext wr D2
ext wr D3
pre  raw_sensor_data.valid = 1 and gnss_imu.gnss_valid = 1 and gnss_imu.imu_valid = 1
post object_table.object_count >= 0
post object_table.lead_object.object_id = object_table.lead_object_id
post ego_state.speed >= 0
post ego_state.last_update >= 0
post ego_state.yaw_rate <= 3.5 and ego_state.yaw_rate >= -3.5
post ego_pose.x = ego_state.x and ego_pose.y = ego_state.y and ego_pose.yaw = ego_state.yaw

-- F2 -- Prediction (§5 F2)
--   reads D1; writes no store; is the only function that computes TTC
--   at Level 0 (§5 F2 -- see OI-01 for the §6 F3.1 conflict)
process F2_Prediction(object_table: ObjectTable, ego_state: EgoState, map_segment: MapSegment) out: prediction: PredictionSet
ext rd D1
pre  object_table <> null and ego_state <> null
post prediction.horizon >= 3.0
post prediction.object_count <= object_table.object_count
post if prediction.object_count > 0 then prediction.min_ttc >= 0

-- F3 -- Behaviour Planning (§5 F3), atomic at Level 0 (R-SCOPE-4)
--   reads D1 and D4; writes no store; the AEB branch of F3 is refined in
--   module AEB_Branch (Level 1)
process F3_Behaviour_Planning(ego_state: EgoState, prediction: PredictionSet, driver_intent: DriverIntent, route: Route, map_segment: MapSegment, traffic_rules: TrafficRules) out: manoeuvre: Manoeuvre, warning: WarningSignal
ext rd D1
ext rd D4
pre  ego_state <> null and prediction <> null and driver_intent <> null and route <> null
post manoeuvre.manoeuvre_type <> ""
post manoeuvre.target_lane <> ""
post warning.active >= 0 and warning.active <= 1
post if prediction.object_count > 0 and prediction.min_ttc > 3.0 then warning.active = 0
post if prediction.object_count > 0 and prediction.min_ttc > 1.5 and prediction.min_ttc <= 3.0 then warning.active = 1
post if prediction.object_count > 0 and prediction.min_ttc <= 1.5 then warning.active = 1
post if manoeuvre.manoeuvre_type = "emergency_deceleration" then manoeuvre.required_decel >= 6.0
post if manoeuvre.manoeuvre_type = "emergency_deceleration" and ego_state.speed <= 36.11 then manoeuvre.target_speed = 0

-- F4 -- Route Planning (§5 F4); reads D1; writes no store
process F4_Route_Planning(destination: Destination, ego_pose: EgoPose, map_segment: MapSegment) out: route: Route
ext rd D1
pre  destination <> null and ego_pose <> null
post route.path_length >= 0
post route.eta >= 0
post route.lane_geometry <> ""

-- F5 -- Motion Planning (§5 F5); reads D1 and D4; writes no store
process F5_Motion_Planning(manoeuvre: Manoeuvre, route: Route, ego_state: EgoState, prediction: PredictionSet, map_segment: MapSegment, traffic_rules: TrafficRules) out: trajectory: Trajectory
ext rd D1
ext rd D4
pre  manoeuvre <> null and route <> null and ego_state <> null and prediction <> null
post if traffic_rules <> null then trajectory.max_speed <= traffic_rules.posted_speed_limit
post trajectory.max_decel >= manoeuvre.required_decel
post if manoeuvre.manoeuvre_type = "emergency_deceleration" then trajectory.max_accel <= 2.0
post if manoeuvre.manoeuvre_type = "emergency_deceleration" then trajectory.max_decel >= 4.0
post if prediction.lead_trajectory <> null then trajectory.min_gap_to_lead >= trajectory.rss_safe_distance
post trajectory.rss_safe_distance >= 0
post trajectory.horizon_duration >= 0

-- F6 -- Control (§5 F6); reads D3; writes no store
process F6_Control(trajectory: Trajectory, ego_state: EgoState) out: actuator_cmd: ActuatorCommand
ext rd D3
pre  trajectory <> null and ego_state <> null
post actuator_cmd.accel_cmd <= 3.0
post actuator_cmd.steer_cmd <= 1.0 and actuator_cmd.steer_cmd >= -1.0
post if trajectory.max_accel > 0 then actuator_cmd.accel_cmd <= trajectory.max_accel
post if trajectory.max_decel > 0 then actuator_cmd.brake_cmd >= trajectory.max_decel

-- F7 -- Safety Shield, monitoring and arbitration (§5 F7, R-E-2)
--   reads D3 and D4; writes no store; the only producer of E8
process F7_Safety_Shield(actuator_cmd: ActuatorCommand, ego_state: EgoState, traffic_rules: TrafficRules) out: checked_cmd: ActuatorCommand
ext rd D3
ext rd D4
pre  actuator_cmd <> null and ego_state <> null and traffic_rules <> null
post checked_cmd.accel_cmd <= 3.0
post checked_cmd.steer_cmd <= 1.0 and checked_cmd.steer_cmd >= -1.0
post if actuator_cmd.steer_cmd > 1.0 then checked_cmd.steer_cmd <= 1.0
post if actuator_cmd.steer_cmd < -1.0 then checked_cmd.steer_cmd >= -1.0
post if actuator_cmd.steer_cmd <= 1.0 and actuator_cmd.steer_cmd >= -1.0 then checked_cmd.steer_cmd = actuator_cmd.steer_cmd
post if ego_state.speed > traffic_rules.posted_speed_limit then checked_cmd.accel_cmd <= 0

end_module
```

---

## 2. 模块 `AEB_Branch`（Level 1，F3 的 AEB 分支细化）

模块清单核对（R-L1-1）：**恰好三个子过程** F3.1 → F3.2 → F3.3；D1、D4 以只读方式被引用（`ext rd`）。

```sofl
-- =====================================================================
-- Module: AEB_Branch  --  Level 1 refinement of the AEB branch of F3
-- Input specification : NL-RQ-ADAS-v1 (v1.0)
-- Refines             : F3 Behaviour Planning of module ADAS_System
-- Elements             : exactly three sub-functions F3.1, F3.2, F3.3
--                        (R-L1-1, §6)
-- Stores referenced    : D1 (read only, by F3.3), D4 (read only, by F3.2)
--
-- SOFL subset conventions: identical to module ADAS_System
--   module head : | ... | table;  "( ... )" = input ports, then output ports
--   types       : Name = composed of <field> : <type>, ... end
--   process     : process <name>(<formal inputs>) out: <formal outputs>
--   store access: ext rd <store>   (read-only)
--   conditions : pre  <predicate>
--                post <predicate>
--                post if <guard> then <predicate>
--   operators  : and  =  <>  >  >=  <=  <  . (field access)
--                [ no or / not / => / quantifiers / seq of ]
--   store bind : the content of a store declared by "ext rd" is bound to the
--                formal input of the same type in the process signature
--   null guard : "<datum> <> null" states non-nullness (R-G-6)
--   exclusion  : closed value sets are specified by excluding unwanted
--                members, because "or" is not available
--
-- Threshold provenance
--   3.0   s  = T_risk_high   (§8 A-5)
--   1.5   s  = T_fcw         (§8 A-5, §7 N-2)
--   2.0   s  = latest TTC at which the warning shall be present (§7 N-2)
--   6.0   m/s^2 = A_emergency (§8 A-1, sized from N-3/N-4)
--   4.0   m/s^2 = a_min,brake (§8 A-2, §7 N-6)
--   36.11 m/s  = 130 km/h (§7 N-1)
-- =====================================================================

module AEB_Branch

|  |  |
| --- | --- | --- |
( predicted_trajectories: PredictionSet | ego_state: EgoState | driver_intent: DriverIntent | route: Route ) warning: WarningSignal | manoeuvre: Manoeuvre
|  |  |
| --- | --- | --- |

-- ---------------------------------------------------------------------
-- TYPES
-- ---------------------------------------------------------------------

-- D1 : HD-map segment for the current road (§4 D1) -- read by F3.3
MapSegment = composed of
  road_id: String,
  lane_id: String,
  posted_speed_limit: real,
  curvature: real,
  lane_topology: String
end

-- D4 : currently applicable traffic rules (§4 D4) -- read by F3.2
TrafficRules = composed of
  posted_speed_limit: real,
  traffic_signal_state: nat
end

-- ego state produced by F1 (§5 F1, §4 D3)
EgoState = composed of
  x: real,
  y: real,
  yaw: real,
  speed: real,
  yaw_rate: real,
  acceleration: real,
  last_update: real
end

-- predicted trajectories produced by F2 (§5 F2)
PredictedTrajectory = composed of
  object_id: nat,
  horizon: real,
  predicted_x: real,
  predicted_y: real,
  predicted_speed: real
end

PredictionSet = composed of
  horizon: real,
  object_count: nat,
  min_ttc: real,
  lead_trajectory: PredictedTrajectory
end

-- E3 : driver command / ODD status from the HMI (§3 E3)
DriverIntent = composed of
  requested_cruise_speed: real,
  override_accelerate: nat,
  override_brake: nat,
  override_steer: real,
  driver_attention: nat
end

-- route produced by F4 (§5 F4)
Route = composed of
  path_length: real,
  eta: real,
  lane_geometry: String
end

-- E7 : driver-facing warning signal (§3 E7)
--   warning_type domain : none | caution | imminent_collision
WarningSignal = composed of
  warning_type: String,
  active: nat
end

-- F3.3 output : target manoeuvre (§5 F3, §6 F3.3)
--   manoeuvre_type domain : cruise | keep_lane | lane_change |
--                            lane_keep_deceleration | emergency_deceleration
Manoeuvre = composed of
  manoeuvre_type: String,
  target_speed: real,
  target_lane: String,
  required_decel: real
end

-- F3.1 output : TTC set -- minimum TTC and number of objects considered
--               (§6 F3.1)
TtcSet = composed of
  object_count: nat,
  min_ttc: real
end

-- ---------------------------------------------------------------------
-- PROCESSES  (Level 1 -- exactly three sub-functions, §6 / R-L1-1)
-- ---------------------------------------------------------------------

-- F3.1 -- TTC Computation (§6 F3.1)
--   inputs : predicted trajectories (F2), ego state (F1)
--   output : TTC set
--   Note : §5 F2 declares F2 the only function that computes TTC, while
--         §6 F3.1 requires F3.1 to compute the TTC -- unresolved
--         contradiction, see OI-01.
process F3_1_TTC_Computation(prediction: PredictionSet, ego_state: EgoState) out: ttc_set: TtcSet
pre  prediction <> null and ego_state <> null
post if prediction.object_count = 0 then ttc_set.object_count = 0
post if prediction.object_count > 0 then ttc_set.object_count <= prediction.object_count
post if prediction.object_count > 0 then ttc_set.min_ttc >= 0

-- F3.2 -- Risk Classification (§6 F3.2)
--   inputs : TTC set (F3.1), traffic rules (D4)
--   outputs: risk level, warning (E7)
--   Note : D4 is an input of F3.2 but no rule relating traffic rules to the
--         risk level is stated -- see OI-15.
process F3_2_Risk_Classification(ttc_set: TtcSet, traffic_rules: TrafficRules) out: risk_level: String, warning: WarningSignal
ext rd D4
pre  ttc_set <> null and traffic_rules <> null
post if ttc_set.min_ttc > 3.0 then risk_level = "no_risk" and warning.active = 0 and warning.warning_type = "none"
post if ttc_set.min_ttc > 1.5 and ttc_set.min_ttc <= 3.0 then risk_level = "caution" and warning.active = 1 and warning.warning_type = "caution"
post if ttc_set.min_ttc <= 1.5 then risk_level = "critical" and warning.active = 1 and warning.warning_type = "imminent_collision"
post if ttc_set.min_ttc <= 2.0 then warning.active = 1

-- F3.3 -- Maneuver Planning (§6 F3.3)
--   inputs : risk level (F3.2), ego state (F1), driver intent (E3),
--            route (F4), D1
--   output : manoeuvre
process F3_3_Maneuver_Planning(risk_level: String, ego_state: EgoState, driver_intent: DriverIntent, route: Route, map_segment: MapSegment) out: manoeuvre: Manoeuvre
ext rd D1
pre  risk_level <> null and ego_state <> null and driver_intent <> null and route <> null
post manoeuvre.manoeuvre_type <> ""
post manoeuvre.target_lane <> ""
post if risk_level = "no_risk" then manoeuvre.manoeuvre_type <> "emergency_deceleration"
post if risk_level = "no_risk" then manoeuvre.manoeuvre_type <> "lane_change"
post if risk_level = "no_risk" then manoeuvre.required_decel = 0
post if risk_level = "caution" then manoeuvre.manoeuvre_type = "lane_keep_deceleration" and manoeuvre.required_decel > 0
post if risk_level = "critical" then manoeuvre.manoeuvre_type = "emergency_deceleration" and manoeuvre.required_decel >= 4.0 and manoeuvre.target_speed = 0
post if risk_level = "critical" then manoeuvre.required_decel >= 6.0
post if risk_level = "critical" and ego_state.speed <= 36.11 then manoeuvre.manoeuvre_type = "emergency_deceleration" and manoeuvre.required_decel >= 6.0 and manoeuvre.target_speed = 0
post if risk_level = "critical" and driver_intent.override_accelerate = 1 then manoeuvre.required_decel >= 6.0 and manoeuvre.target_speed = 0
post if risk_level = "no_risk" and driver_intent.override_accelerate = 1 then manoeuvre.required_decel = 0

end_module
```

---

## 3. CDFD — `ADAS_System`（Level 0）

### 3.1 元素清单（20 个，无增删）

> 配套示意图：Level 0 CDFD 图（见对话中的 `ADAS_System_Level0_CDFD`）。图中外部接口名采用缩写（raw_sensor→raw_sensor_data 等），完整名称以本表与 §3.2 为准；多读者的存储（D1/D3/D4）在图上以「读：…」标注。

**外部终端（9）**

| ID | 终端（数据流名） | 方向 | 类型 | 规格 |
|---|---|---|---|---|
| E1 | `raw_sensor_data` | in | SensorFrame | §3 E1 |
| E2 | `gnss_imu` | in | GnssImu | §3 E2 |
| E3 | `driver_intent` | in | DriverIntent | §3 E3 |
| E4 | `destination` | in | Destination | §3 E4 |
| E5 | `map_data` | in | MapSegment | §3 E5 |
| E6 | `traffic_rules` | in | TrafficRules | §3 E6 |
| E7 | `warning` | out | WarningSignal | §3 E7 |
| E8 | `checked_cmd` | out | ActuatorCommand | §3 E8 |
| E9 | `actuator_cmd` | in | ActuatorCommand | §3 E9 |

**过程（7）**：`F1_Perception_Localisation`、`F2_Prediction`、`F3_Behaviour_Planning`、`F4_Route_Planning`、`F5_Motion_Planning`、`F6_Control`、`F7_Safety_Shield`

**数据存储（4）**：`D1` HD Map Store、`D2` Object Track Store、`D3` Ego State Store、`D4` Traffic Rules Store

### 3.2 数据流连线清单（33 条）

| # | 流名 | 源 | 汇 | 模式 | 类型 | 规格依据 |
|---|---|---|---|---|---|---|
| 1 | `raw_sensor_data` | E1 | F1 | in | SensorFrame | §3 E1, §5 F1 |
| 2 | `gnss_imu` | E2 | F1 | in | GnssImu | §3 E2, §5 F1 |
| 3 | `driver_intent` | E3 | F3 | in | DriverIntent | §3 E3, §5 F3 |
| 4 | `destination` | E4 | F4 | in | Destination | §3 E4, §5 F4 |
| 5 | `map_data` | E5 | D1 | **写**（外部刷新） | MapSegment | §3 E5, §4 D1 lifetime, OI-02 |
| 6 | `traffic_rules` | E6 | D4 | **写**（外部刷新） | TrafficRules | §3 E6, §4 D4 lifetime, OI-02 |
| 7 | `actuator_cmd` | E9 | F7 | in | ActuatorCommand | §3 E9, R-E-2, OI-06 |
| 8 | `map_segment` | D1 | F1 | **读** | MapSegment | §5.1 store reads |
| 9 | `map_segment` | D1 | F2 | **读** | MapSegment | §5.1 store reads |
| 10 | `map_segment` | D1 | F3 | **读** | MapSegment | §5.1 store reads |
| 11 | `map_segment` | D1 | F4 | **读** | MapSegment | §5.1 store reads |
| 12 | `map_segment` | D1 | F5 | **读** | MapSegment | §5.1 store reads |
| 13 | `traffic_rules` | D4 | F3 | **读** | TrafficRules | §5.1 store reads |
| 14 | `traffic_rules` | D4 | F5 | **读** | TrafficRules | §5.1 store reads |
| 15 | `traffic_rules` | D4 | F7 | **读** | TrafficRules | §5.1 store reads |
| 16 | `ego_state` | D3 | F6 | **读** | EgoState | §5.1 store reads |
| 17 | `ego_state` | D3 | F7 | **读** | EgoState | §5.1 store reads |
| 18 | `object_table` | F1 | D2 | **写** | ObjectTable | §5.1 store writes, §5 F1 |
| 19 | `ego_state` | F1 | D3 | **写** | EgoState | §5.1 store writes, §5 F1 |
| 20 | `ego_state` | F1 | F2 | in | EgoState | §5 F2 输入, §5.1（含 pose 字段）, OI-03 |
| 21 | `object_table` | F1 | F2 | in | ObjectTable | §5.1 F1→F2 |
| 22 | `ego_state` | F1 | F3 | in | EgoState | §5 F3 输入, OI-03 |
| 23 | `ego_state` | F1 | F5 | in | EgoState | §5 F5 输入, OI-03 |
| 24 | `ego_pose` | F1 | F4 | in | EgoPose | §5.1 F1→F4 |
| 25 | `prediction` | F2 | F3 | in | PredictionSet | §5.1 F2→F3 |
| 26 | `prediction` | F2 | F5 | in | PredictionSet | §5.1 F2→F5 |
| 27 | `manoeuvre` | F3 | F5 | in | Manoeuvre | §5.1 F3→F5 |
| 28 | `route` | F4 | F3 | in | Route | §5.1 F4→F3 |
| 29 | `route` | F4 | F5 | in | Route | §5.1 F4→F5 |
| 30 | `trajectory` | F5 | F6 | in | Trajectory | §5.1 F5→F6 |
| 31 | `actuator_cmd` | F6 | F7 | in | ActuatorCommand | §5.1 F6→F7 |
| 32 | `warning` | F3 | E7 | out | WarningSignal | §5.1 F3→outside, R-E-1 |
| 33 | `checked_cmd` | F7 | E8 | out | ActuatorCommand | §5.1 F7→outside, R-E-1, R-E-2 |

> 相对 §5.1 强制清单的**增量**共 5 条（#5、#6、#7、#22、#23），逐条理由见 §6 的 OI-02、OI-03、OI-06；§5.1 中的每一条强制流均已原样保留。

### 3.3 存储访问矩阵（与 CDFD 读写连线一致）

| 过程 | D1 | D2 | D3 | D4 | `ext` 声明 |
|---|---|---|---|---|---|
| F1 | 读 | 写 | 写 | — | `ext rd D1` / `ext wr D2` / `ext wr D3` |
| F2 | 读 | — | — | — | `ext rd D1` |
| F3 | 读 | — | — | 读 | `ext rd D1` / `ext rd D4` |
| F4 | 读 | — | — | — | `ext rd D1` |
| F5 | 读 | — | — | 读 | `ext rd D1` / `ext rd D4` |
| F6 | — | — | 读 | — | `ext rd D3` |
| F7 | — | — | 读 | 读 | `ext rd D3` / `ext rd D4` |

（§5 F1「shall not read D2 or D3」、F2/F3/F4/F5/F6/F7「shall not write any store」均已满足；R-D-1、R-D-2 见 §7。）

### 3.4 生产者/消费者审计（R-G-4、R-G-5）

| 数据 | 唯一生产者 | 消费者 | 说明 |
|---|---|---|---|
| `object_table` | F1 | F2（并写 D2） | §5.1 未指定其它消费者，模型未新增 |
| `ego_state` / `ego_pose` | F1 | F2、F3、F4、F5（并写 D3） | 按 §5 输入清单分配，每条流单消费者 |
| `prediction` | F2 | F3、F5 | §5.1 显式双消费者 |
| `route` | F4 | F3、F5 | §5.1 显式双消费者 |
| `manoeuvre` | F3 | F5 | §5.1 |
| `trajectory` | F5 | F6 | §5.1 |
| `actuator_cmd` | F6（另见 E9 外部输入） | F7 | OI-06：同一数据出现两个来源，与 R-G-4「单生产者」冲突 |
| `warning` | F3 | E7 | R-E-1 |
| `checked_cmd` | F7 | E8 | R-E-1、R-E-2 |
| D1 内容 | 外部 E5 刷新 | F1、F2、F3、F4、F5 | §5.1 显式多消费者读；写者归属见 OI-02 |
| D2 内容 | F1 | 无（仅被写） | §5 F1 禁止读 D2 |
| D3 内容 | F1（写） | F6、F7（读） | §5.1、§11 问题 2（OI-21） |
| D4 内容 | 外部 E6 刷新 | F3、F5、F7 | §5.1；写者归属见 OI-02 |

---

## 4. CDFD — `AEB_Branch`（Level 1）

### 4.1 元素清单

> 配套示意图：Level 1 CDFD 图（见对话中的 `AEB_Branch_Level1_CDFD`）。

**过程（3，恰好）**：`F3_1_TTC_Computation`、`F3_2_Risk_Classification`、`F3_3_Maneuver_Planning`

**数据存储（2，只读引用）**：`D1`（HD Map Store，被 F3.3 读）、`D4`（Traffic Rules Store，被 F3.2 读）——与 Level 0 中 D1/D4 为同一实例，仅在细化模块中以只读方式出现。

**外部终端（模块边界，取自 Level 0 的既定元素，未新增语义）**：

| 终端 | 来源/去向 | 类型 | 规格 |
|---|---|---|---|
| X-PRED | F2 → 本模块 | PredictionSet | §5.1 F2→F3 |
| X-EGO | F1 → 本模块 | EgoState | §5 F3 输入 |
| X-INT | E3 → 本模块 | DriverIntent | §3 E3 |
| X-ROUTE | F4 → 本模块 | Route | §5.1 F4→F3 |
| E7 | 本模块 → 外部 | WarningSignal | §3 E7 |
| X-MAN | 本模块 → F5 | Manoeuvre | §5.1 F3→F5 |

### 4.2 数据流连线清单（11 条）

| # | 流名 | 源 | 汇 | 模式 | 规格依据 |
|---|---|---|---|---|---|
| 1 | `prediction` | X-PRED (F2) | F3.1 | in | §6 F3.1 输入 |
| 2 | `ego_state` | X-EGO (F1) | F3.1 | in | §6 F3.1 输入 |
| 3 | `ego_state` | X-EGO (F1) | F3.3 | in | §6 F3.3 输入 |
| 4 | `traffic_rules` | D4 | F3.2 | **读** | §6 F3.2 输入（D4） |
| 5 | `map_segment` | D1 | F3.3 | **读** | §6 F3.3 输入（D1） |
| 6 | `ttc_set` | F3.1 | F3.2 | in | §6 F3.1 输出 → F3.2 输入 |
| 7 | `risk_level` | F3.2 | F3.3 | in | §6 F3.2 输出 → F3.3 输入 |
| 8 | `warning` | F3.2 | E7 | out | §6 F3.2 输出 (E7) |
| 9 | `driver_intent` | X-INT (E3) | F3.3 | in | §6 F3.3 输入 (E3) |
| 10 | `route` | X-ROUTE (F4) | F3.3 | in | §6 F3.3 输入 |
| 11 | `manoeuvre` | F3.3 | X-MAN (F5) | out | §6 F3.3 输出 → §5.1 F3→F5 |

三条子过程之间只有两条内部流（#6 ttc_set、#7 risk_level），无旁路；无任何 `ext wr`（§6 未授权写存储）。

### 4.3 细化覆盖核对

| Level 0 的 F3 责任（§5 F3） | Level 1 归属 |
|---|---|
| 决定目标机动（含 emergency deceleration） | F3.3 |
| 决定是否发出驾驶员警告 E7 及警告类型 | F3.2 |
| 尊重适用交通规则 D4 与驾驶员意图 E3 | F3.3（E3）；D4 在 F3.2 声明但无用规则（OI-15） |
| 不写任何存储 | 三过程均无 `ext wr` |
| 使用预测轨迹与自车状态 | F3.1 |

---

## 5. 契约一览（R-G-1）

| 过程 | precondition 所需数据 | postcondition 产出数据 | 量化约束（含阈值出处） |
|---|---|---|---|
| F1 | E1 有效标志、E2 有效标志 | object_table(D2)、ego_state(D3)、ego_pose | `yaw_rate ≤ 3.5 / ≥ -3.5`（A-4）；`speed ≥ 0`、`last_update ≥ 0`（定性） |
| F2 | object_table、ego_state | prediction（预测轨迹 + 最小 TTC） | `horizon ≥ 3.0`（A-7）；`min_ttc ≥ 0`（定性域约束） |
| F3 | ego_state、prediction、driver_intent、route | manoeuvre、warning(E7) | `required_decel ≥ 6.0`（A-1）；`speed ≤ 36.11 → target_speed = 0`（N-1）；`min_ttc` 3.0 / 1.5 分档（A-5） |
| F4 | destination、ego_pose | route | 无 §7/§8 阈值 → 定性：`path_length ≥ 0`、`eta ≥ 0`、`lane_geometry ≠ ""` |
| F5 | manoeuvre、route、ego_state、prediction | trajectory | `max_speed ≤ D4.posted_speed_limit`（§5 F5）；`max_decel ≥ manoeuvre.required_decel`（§5 F5）；紧急时 `max_accel ≤ 2.0`、`max_decel ≥ 4.0`（A-2 / N-6）；`min_gap_to_lead ≥ rss_safe_distance`（N-5） |
| F6 | trajectory、ego_state | actuator_cmd(E9) | `accel_cmd ≤ 3.0`（A-3）；`steer_cmd ≤ 1.0 / ≥ -1.0`（A-6）；`accel_cmd ≤ trajectory.max_accel`、`brake_cmd ≥ trajectory.max_decel`（转换一致性） |
| F7 | actuator_cmd、ego_state、traffic_rules | checked_cmd(E8) | `accel_cmd ≤ 3.0`（A-3）；`steer_cmd ≤ 1.0 / ≥ -1.0`（A-6）；越界时削转角、未越界时保留转角（§5 F7）；超速时 `accel_cmd ≤ 0`（D4 执法） |
| F3.1 | prediction、ego_state | ttc_set | `object_count = 0`（§6 F3.1）；`object_count ≤ prediction.object_count`；`min_ttc ≥ 0` |
| F3.2 | ttc_set、traffic_rules | risk_level、warning(E7) | `min_ttc > 3.0 → no_risk`；`1.5 < min_ttc ≤ 3.0 → caution`；`min_ttc ≤ 1.5 → critical`（A-5）；`min_ttc ≤ 2.0 → warning.active = 1`（N-2） |
| F3.3 | risk_level、ego_state、driver_intent、route、map_segment | manoeuvre | `critical → required_decel ≥ 6.0 ∧ target_speed = 0`（A-1、N-3/N-4）；`critical → required_decel ≥ 4.0`（N-6 / A-2）；`caution → required_decel > 0`；`no_risk → required_decel = 0`；`speed ≤ 36.11 → emergency`（N-1）；`critical ∧ 驾驶员加速 → 紧急机动不被覆盖`（§6 F3.3） |

---

## 6. open-issues（规格未写明 / 规格内部矛盾 / 建模决定）

| ID | 问题 | 规格依据 | 本模型的处理 | 需要确认 |
|---|---|---|---|---|
| OI-01 | TTC 归属矛盾：§5 F2 称 F2 是「唯一计算 TTC 的功能」，§6 又要求 F3.1 计算 TTC | §5 F2 vs §6 F3.1 | Level 0 由 F2 计算最小 TTC；Level 1 按 §6 由 F3.1 计算 TTC。同一量在两级各有生产者，与 R-G-4「单生产者」张力 | 是否改写 §5 F2，或将 F3.1 改名为「TTC 提取/选择」并复用 F2 的 TTC |
| OI-02 | 存储写者缺位：§4 记 D1 owner 为「F5 / F1」、D4 owner 为「F5」，且由 E5/E6 刷新；但 §5 规定 F5 不得写存储，§5.1 只列 F1 写 D2/D3；R-D-1 要求「仅 owner 函数写」 | §4 表、§5 F5、§5.1、R-D-1 | 模型把刷新画成外部写连线（E5→D1、E6→D4），函数侧仅 F1 写 D2/D3 | D1/D4 是否应各设一个拥有者函数，或由 F5 之外的缓存功能刷新 |
| OI-03 | §5.1 强制清单缺少 F1→F3、F1→F5 的 ego_state 流，但 §5 明列 F3、F5 的输入含 ego state | §5 F3/F5 输入 vs §5.1 | 模型补两条流（#22、#23），并把 F1→F2 的流写作 ego_state（§5.1 记为 ego pose，pose 字段已含于其中） | 确认 §5.1 清单为非穷举，或补齐这两条 |
| OI-04 | N-7 要求横向加速度在车辆能力内，但 §7/§8 未给横向加速度数值 | §7 N-7 | F5/F7 以定性 postcondition 表述；定量部分只能落在 A-6（±1.0 归一化转角） | 是否补一个横向加速度能力值（如 A-7 之外新增） |
| OI-05 | 记法禁用 `seq of`，多元素集合无法直接表达（传感器帧集、逐目标表、逐目标轨迹、TTC 集） | 任务书语法约束 | 集合以「计数 + 前导/相关元素」建模：`object_count`、`lead_object`、`lead_trajectory` | 若允许列表类型，上述类型需拓宽为 list |
| OI-06 | E9 双重身份：E 表中 E9 是外部**输入**，§5/§5.1 却是 F6 的内部输出到 F7 | §3 E9 vs §5 F6、§5.1、R-E-2 | 模块头保留 `actuator_cmd` 输入端口（按 E 表），CDFD 同时保留 F6→F7 内部流与 E9→F7 输入流 | E9 是外部冗余通道还是 F6→F7 流的外部面？建议二选一以满足 R-G-4 |
| OI-07 | A-1 紧急减速 6.0 m/s² 与 A-3「纵向执行包络上界 3.0 m/s²（F6/F7）」冲突 | §8 A-1 vs A-3 | A-3 解释为**正向加速度指令**上界；制动指令按轨迹要求减速度（≥ 紧急机动要求）给出下界，二者相容 | 明确 A-3 是否约束制动幅值；若是，6.0 m/s² 无法经 F6→F7 传达 |
| OI-08 | 风险等级到 E7 警告类型的映射未写明（§6 只说「发不发、发哪种」的抽象层级） | §6 F3.2 vs §3 E7 | 映射 no_risk→none、caution→caution、critical→imminent_collision | 确认映射 |
| OI-09 | N-6 的「dangerous situation」未与 caution 档对齐；反应时间 ρ=0.1 s 及所有周期时序在本记法中不可表达 | §7 N-6、§8 A-2、§11 问题 3 | `a_min,brake=4.0` 仅挂在 critical 档；时序不入模型 | 「危险状态」是否覆盖 caution 档；是否需要引入时序属性 |
| OI-10 | §6 F3.3「其它风险档驾驶员加速请求优先」与「caution 必须产生非零减速」冲突 | §6 F3.3 | caution 档保留强制减速（非零 required_decel），驾驶员请求仅在 no_risk 档生效（required_decel = 0）；critical 档明确不被加速请求覆盖 | 明确 caution 档的优先级规则 |
| OI-11 | A-5 的 `T_risk_high = 3.0 s` 恰等于 A-7 的预测视界 3.0 s：若 TTC 被视界截断，则「no risk（TTC > 3.0）」不可达，每周期都是 caution | §8 A-5 vs A-7、§5 F2 | 模型按 §5「视界至少 3 s」建模，TTC 允许超出视界（视界内无碰撞按「无碰撞」上报） | 确认「视界内无碰撞」的 TTC 上报方式（无穷大 / > 视界 / 截断值） |
| OI-12 | N-3 要求冲击速度降低「**超过** 30 km/h」，但 §7 推导为 8.33 m/s（= 30.0 km/h）恰好 30 km/h | §7 N-3 vs §7 推导、A-1 | 按 A-1 = 6.0 m/s² 原样建模，不额外加余量 | 是否需要略大于 6.0 m/s² 的余量 |
| OI-13 | N-1 为「至少 130 km/h」，超过 130 km/h 的 AEB 行为未规定（N-4 CCRm 上限亦为 130 km/h） | §7 N-1、N-4 | 紧急减速机动不附加速度门限（保守），另设 ≤ 36.11 m/s 的显式 postcondition 以承载 N-1 | 规定 130 km/h 以上的降级策略 |
| OI-14 | §5 F3 的机动类型含 lane-change，但 §6 的三子过程只覆盖 no_risk/caution/critical，lane-change 在 Level 1 无归属 | §5 F3 vs §6 | 模型不越权补充：no_risk 档用排除法限定为 cruise/keep_lane，lane_change 无生产者 | 确认 lane-change 决策归属（仍在 F3 原子部分？是否需第四子过程——但会被 R-L1-1 禁止） |
| OI-15 | D4 含交通信号状态；§6 F3.2 把 D4 列为输入却无任何规则使用它 | §3 E6、§4 D4、§6 F3.2 | D4 仍按 §6 声明为 F3.2 的读输入，规则留空 | 补充规则（如红灯/限速对风险分类的影响） |
| OI-16 | 若干字段规格未给结构：车道几何、车道拓扑、路径偏好、目标类别 | §5 F4、§3 E4/E5、§4 D2 | 一律以 `String`（车道几何/拓扑/偏好）与 `nat`（类别码）承载，不臆造枚举 | 给出字段级结构或接受不透明承载 |
| OI-17 | `brake_cmd` 无单位/标定 | §3 E8/E9 | 按与 `accel_cmd` 同一纵向减速度标度建模，并写入 OI-07 说明 | 明确制动指令标度 |
| OI-18 | F1/F2/F4 对 D1 的读取目的未写明 | §5.1 | D1 读作为建图上下文（车道/路段匹配与预测）建模，无附加规则 | 说明各处 D1 读的具体用途 |
| OI-19 | Level 0 的原子 F3 使用了 §6/§8 的 A-5 风险阈值（§5 未复述） | §5 F3 vs §6 F3.2、§8 A-5 | Level 0 F3 以同一阈值给出警告 postcondition，保证 Level 0 与 Level 1 一致 | 确认 Level 0 是否允许展开该阈值 |
| OI-20 | R-SCOPE-1 要求 SAE L2（驾驶员监督/接管），但七功能划分中没有驾驶员监控（DMS）或接管仲裁元素 | §1 R-SCOPE-1、§11 问题 1 | 模型不新增功能；L2 监督责任只体现在 F3/F3.3 读取 E3 的驾驶员意图与注意力字段 | 是否增设驾驶员监控功能（会突破 R-L0-1 的「恰好七个」） |
| OI-21 | D3 由 F1 写、F6/F7 读，跨函数所有权（规格自问） | §4 D3、§11 问题 2 | 按 §5.1 建模（F1 写、F6/F7 读），不做所有权再分配 | 确认 D3 所有权安排 |
| OI-22 | §5 F5 的 trajectory 字段只列「最大许可速度/最大许可加速度/视界时长」，无法表达「满足机动要求的减速量」与 N-5 的最小间距 | §5 F5、§7 N-5 | 扩展 `Trajectory`：`max_decel`、`min_gap_to_lead`、`rss_safe_distance`（并入 OI-05 声明） | 确认字段扩展；并补充 RSS Eq.(1) 的闭式或明确其外部引用性质 |

**建模决定一览（供四个模型对比时区分「规格要求」与「建模选择」）**：D1/D4 由外部接口刷新（OI-02）；F1→F3/F5 的 ego_state 流（OI-03）；A-3 仅约束正向加速度（OI-07）；风险→警告类型映射（OI-08）；`Trajectory` 字段扩展（OI-22）；集合以计数+前导元素承载（OI-05）；no_risk 档用排除法表达（OI-10/OI-14）。

---

## 7. 可追溯性矩阵（R-G-2）

### 7.1 R-xx 条款 → 模型元素

| 要求 | 模型元素 | 落实方式 |
|---|---|---|
| R-SCOPE-1 | 模块 `ADAS_System`（整体）、`F3_Behaviour_Planning`、`F3_3_Maneuver_Planning`、`F7_Safety_Shield` | L2 语义落在 E3 `driver_intent`（含 attention/override）进入 F3/F3.3，以及 F7 的仲裁职责；无独立驾驶员监控元素 → OI-20 |
| R-SCOPE-2 | 模块头 9 个外部端口 + CDFD §3.1 的 E1–E9 终端 | 全部外部对象只作为端口/终端出现；D1–D4、F1–F7 全在边界内 |
| R-SCOPE-3 | §3.1 过程清单（7 个原子过程） | Level 0 无任何 F 以下的分解，无检测/跟踪/规划器内部元素 |
| R-SCOPE-4 | `ADAS_System`（Level 0）+ `AEB_Branch`（Level 1，仅细化 F3 为 F3.1–F3.3） | 其余 F1/F2/F4–F7 在 Level 0 保持原子 |
| R-E-1 | 模块头输出端口仅 `warning`(E7)、`checked_cmd`(E8)；生产者为 F3、F7 | §3.4 审计表：不存在其它输出流 |
| R-E-2 | `F7_Safety_Shield`（pre 含 actuator_cmd，post 产出 checked_cmd）；CDFD #7、#31、#33 | E8 的唯一生产者是 F7；无 F6→E8 直连 |
| R-D-1 | `ext wr` 仅出现于 `F1_Perception_Localisation`（D2、D3）；§3.3 矩阵 | D1/D4 的刷新为外部连线 → OI-02 |
| R-D-2 | §3.3 存储访问矩阵 | F1 只读 D1；无函数读未被 §5.1 指派的存储；F1 不读 D2/D3 |
| R-L0-1 | §3.1 元素清单：7 过程 / 4 存储 / 9 外部终端 | 逐项核对无增删 |
| R-L1-1 | `AEB_Branch`：`F3_1_TTC_Computation`、`F3_2_Risk_Classification`、`F3_3_Maneuver_Planning` | 恰好三个子过程，链式数据流 F3.1→F3.2→F3.3 |
| R-G-1 | 每个过程的 `pre`/`post`（§5 契约一览） | 全部 10 个过程均给出所需数据、产出数据与至少一条量化/定性约束 |
| R-G-2 | 本矩阵 | — |
| R-G-3 | §3.1、§4.1 元素清单 + §6 声明 | 每个元素均有 R-xx 归属；扩展项（Trajectory 字段、不透明字段等）已在 OI-05/OI-16/OI-22 声明 |
| R-G-4 | §3.4 生产者/消费者审计 | 除 §5.1 显式允许的 D1/D4 多读者外，每条流单生产者单消费者；`actuator_cmd` 双来源 → OI-06 |
| R-G-5 | §3.4 审计表「消费者」列 | 每个产出数据均有且仅有规格指定的消费者 |
| R-G-6 | 各过程 `pre` 中的 `<datum> <> null`；`post` 中对输入字段的读取均带守卫 | 例：F5 中 `if traffic_rules <> null then …`、`if prediction.lead_trajectory <> null then …` |

### 7.2 阈值锚点 N-x / A-x → 模型元素

| 锚点 | 取值 | 模型元素与位置 |
|---|---|---|
| N-1 | 130 km/h = 36.11 m/s | `F3_3_Maneuver_Planning`：`critical and ego_state.speed <= 36.11 → emergency_deceleration ∧ required_decel ≥ 6.0 ∧ target_speed = 0`；`F3_Behaviour_Planning` 同义 postcondition |
| N-2 | FCW ≤ 1.5 s；警告须在 TTC = 2.0 s 前存在 | `F3_2_Risk_Classification`：`min_ttc <= 2.0 → warning.active = 1`；`min_ttc <= 1.5 → critical`（T_fcw = A-5 = 1.5 s）；Level 0 F3 同构 |
| N-3 | 冲击速度降低 > 30 km/h | `F3_3`/`F3` 的 `required_decel >= 6.0`（A-1 即按 N-3/N-4 推得）；余量问题见 OI-12 |
| N-4 | CCRm 60–130 km/h，目标 20 km/h；CCRb −4 m/s² | `F3_3` 的 36.11 m/s 速度上限（= 130 km/h）；F5 的 `max_decel >= 4.0`（对 CCRb 减速目标的保守包络）；OI-13 |
| N-5 | RSS 纵向最小安全间距 d_min | `F5_Motion_Planning`：`min_gap_to_lead >= rss_safe_distance`（A-2 参数集 ρ=0.1 / a_max,accel=2.0 / a_max,brake=4.0 / a_min,brake=4.0 在类型注释与 OI-22 中标注） |
| N-6 | 制动 ≥ a_min,brake；ρ 内纵向加速度 ≤ a_max,accel | `F5`：`emergency → max_decel >= 4.0 ∧ max_accel <= 2.0`；`F3_3`：`critical → required_decel >= 4.0` |
| N-7 | 横向加速度须在车辆能力内 | `F5`（轨迹运动学可行，定性）、`F6`/`F7`（A-6 转角包络）；无数值 → OI-04 |
| A-1 | 6.0 m/s² | `F3_3`：`critical → required_decel >= 6.0`；`F3`：`emergency_deceleration → required_decel >= 6.0` |
| A-2 | ρ=0.1 s, a_max,accel=2.0, a_max,brake=4.0, a_min,brake=4.0 | `F5`：`max_accel <= 2.0`、`max_decel >= 4.0`；`F3_3`：`required_decel >= 4.0`；ρ/视界相关 → OI-09、OI-22 |
| A-3 | 3.0 m/s² | `F6`：`accel_cmd <= 3.0`；`F7`：`checked_cmd.accel_cmd <= 3.0` |
| A-4 | 3.5 rad/s | `F1`：`ego_state.yaw_rate <= 3.5 ∧ >= -3.5` |
| A-5 | T_risk_high=3.0 s, T_fcw=1.5 s | `F3_2`：`> 3.0 → no_risk`、`1.5 < x ≤ 3.0 → caution`、`≤ 1.5 → critical`；`F3` 同构 |
| A-6 | ±1.0 | `F6`：`steer_cmd <= 1.0 ∧ >= -1.0`；`F7`：同样的上界 + 越界削角 + 未越界保留 |
| A-7 | 3.0 s | `F2`：`prediction.horizon >= 3.0` |

### 7.3 §5 功能责任 / §4 存储 / §3 接口 → 模型元素

| 条款 | 模型元素 |
|---|---|
| §5 F1（对象表、自车状态、写 D2/D3、不读 D2/D3） | `F1_Perception_Localisation`；CDFD #1、#2、#8、#18、#19、#20、#21、#24 |
| §5 F2（≥3 s 视界、最小 TTC、唯一算 TTC、不写存储） | `F2_Prediction`；CDFD #9、#20、#21、#25、#26 |
| §5 F3（机动、警告 E7、尊重 D4/E3、不写存储） | `F3_Behaviour_Planning`；CDFD #3、#10、#13、#22、#25、#27、#28、#32 |
| §5 F4（路径长度、ETA、车道几何、不写存储） | `F4_Route_Planning`；CDFD #4、#11、#24、#28、#29 |
| §5 F5（运动学可行轨迹、不超限速、满足减速要求、不写存储） | `F5_Motion_Planning`；CDFD #12、#14、#23、#26、#27、#29、#30 |
| §5 F6（执行指令、包络 A-3/A-6、不写存储） | `F6_Control`；CDFD #16、#30、#31 |
| §5 F7（监控仲裁、保转角、执行 D4、不写存储） | `F7_Safety_Shield`；CDFD #7、#15、#17、#31、#33 |
| §4 D1–D4 | 存储 D1–D4；写者/读者见 §3.3；D1→F1–F5、D4→F3/F5/F7、D3→F6/F7、D2 无读者 |
| §3 E1–E9 | §3.1 外部终端表 + §3.2 连线 #1–#7、#32、#33 |
| §6 F3.1 / F3.2 / F3.3 | `F3_1_TTC_Computation` / `F3_2_Risk_Classification` / `F3_3_Maneuver_Planning`；§4.2 连线清单 |

---

## 8. 交付物清单

| 文件 | 内容 |
|---|---|
| `MiniMax-M3.1-Flash-无禁令-1.md` | 本文档：模块文本 + 两张 CDFD 元素/连线清单 + 契约一览 + open-issues + 追溯矩阵 |
| `ADAS_System.sofl` | 模块 `ADAS_System` 的完整 SOFL 文本（§1 同源） |
| `AEB_Branch.sofl` | 模块 `AEB_Branch` 的完整 SOFL 文本（§2 同源） |
