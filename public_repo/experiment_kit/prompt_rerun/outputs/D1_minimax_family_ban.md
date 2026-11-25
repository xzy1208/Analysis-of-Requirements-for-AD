# NL-RQ-ADAS-v1 → SOFL 形式化规格 (M2: LLM-generated SOFL)

**模型**：MiniMax-M3.1-Flash ｜ **变体**：D ｜ **文件名**：`MiniMax-M3.1-Flash+D.md`
**输入规格**：`C:/Users/zct11/WorkBuddy/2026-11-11-20-16-46/NL-RQ-ADAS-v1_spec.md`
**交付物**：Level 0 模块 `ADAS_System`、Level 1 模块 `AEB_Branch`、两张 CDFD（元素+连线清单）、open-issues、可追溯性矩阵、自查表。

**建模纪律（全文适用）**
1. 只建模规格写明的内容；未写明者一律进 open-issues，不发明函数/存储/信号/阈值。
2. 阈值只取自 §7（N-1…N-7）与 §8（A-1…A-7）。
3. pre/post 中**不得出现恒真条件**：无 `x <> null`、无 `x = x`、无对 `nat` 的 `>= 0`、无 `if true`。守卫只能是「真实情形」（生产者写入的有效性标志、取自 §7/§8 的数值阈值、量纲/范围条件、状态前置条件）。
4. 可用算子限定为 `and` / `=` / `<>` / `>` / `>=` / `<=` / `<` 与点号字段访问；**不使用** `or` / `not` / `=>` / 量词 / `seq of`。
5. 量纲约定（见 MD-07）：速度 km/h；加速度 m/s²；时间 s；角速度 rad/s；**减速量带符号（负 = 制动）**。

---

## 1. 类型声明（两个 module 共用）

```
/* ---------------- boundary / store content types (E1..E6, D1..D4) ---------------- */

SensorValidity = composed of
    camera_valid: nat,
    radar_valid: nat,
    lidar_valid: nat
end

RawSensorData = composed of
    frame_count: nat,
    timestamp: real,
    validity: SensorValidity,
    valid: nat
end

GnssImu = composed of
    position_x: real,
    position_y: real,
    heading: real,
    angular_rate: real,
    acceleration: real,
    gnss_valid: nat,
    imu_valid: nat,
    valid: nat
end

DriverIntent = composed of
    requested_cruise_speed: real,
    override_accelerate: nat,
    override_brake: nat,
    override_steer: nat,
    attention_state: nat,
    valid: nat
end

Destination = composed of
    longitude: real,
    latitude: real,
    route_preference: nat,
    valid: nat
end

LaneTopology = composed of
    lane_link_count: nat
end

MapData = composed of
    road_id: nat,
    lane_id: nat,
    posted_speed_limit: real,
    curvature: real,
    topology: LaneTopology,
    valid: nat
end

TrafficRules = composed of
    posted_speed_limit: real,
    signal_state: nat,
    valid: nat
end

/* ---------------- internal flow types (F1..F7, F3.1..F3.3) ---------------- */

EgoPose = composed of
    pose_x: real,
    pose_y: real,
    valid: nat
end

EgoState = composed of
    pose: EgoPose,
    speed: real,
    yaw_rate: real,
    acceleration: real,
    timestamp: real,
    valid: nat
end

LeadObject = composed of
    object_id: nat,
    position_x: real,
    position_y: real,
    velocity_x: real,
    velocity_y: real,
    object_class: nat
end

ObjectTable = composed of
    object_count: nat,
    lead: LeadObject,
    valid: nat
end

Route = composed of
    path_length: real,
    eta: real,
    lane_count: nat,
    lane_width: real,
    valid: nat
end

PredictedTrajectories = composed of
    object_count: nat,
    horizon: real,
    min_ttc: real,
    min_ttc_valid: nat,
    valid: nat
end

Manoeuvre = composed of
    manoeuvre_type: String,
    target_speed: real,
    target_lane: nat,
    required_deceleration: real,
    valid: nat
end

Trajectory = composed of
    max_permitted_speed: real,
    max_permitted_acceleration: real,
    horizon_duration: real,
    valid: nat
end

ActuationCommand = composed of
    accel_command: real,
    brake_command: real,
    steer_command: real,
    valid: nat
end

Warning = composed of
    warning_type: String,
    active: nat
end

TTCSet = composed of
    object_count: nat,
    min_ttc: real,
    min_ttc_valid: nat,
    valid: nat
end
```

**字符串取值域（规格原词，无自造编号）**
`manoeuvre_type ∈ {cruise, keep_lane, lane_change, lane_keeping_with_deceleration, emergency_deceleration}`；
`risk_level ∈ {no_risk, caution, critical}`；
`warning_type ∈ {none, caution, imminent_collision}`。
其余离散量（`signal_state`、`route_preference`、`object_class`、`attention_state`、`override_*`、各 `valid`）用整数码，编码方式规格未给出 → **MD-08**。

---

## 2. Module `ADAS_System`（Level 0，整车级）

```
/* ============================================================================
 * Module ADAS_System  —  Level 0 vehicle-level ADAS architecture
 * Source: NL-RQ-ADAS-v1_spec.md  §3 (E), §4 (D), §5 (F), §5.1, §9
 * Element inventory is exactly: 7 processes (F1..F7) + 4 stores (D1..D4)
 *                             + 9 external interfaces (E1..E9)   [R-L0-1]
 * ========================================================================== */

/* E9 note (MD-01): §3 lists E9 as an interface with direction "in", but both its
   producer (F6) and its consumer (F7) are inside the vehicle.  It is therefore
   rendered as a boundary terminal carrying the raw command F6 -> F7, so that the
   E1..E9 inventory required by R-L0-1 stays complete and R-E-2 stays visible. */

module ADAS_System (
    E1_raw_sensor_data : RawSensorData |
    E2_gnss_imu : GnssImu |
    E3_driver_intent : DriverIntent |
    E4_destination : Destination |
    E5_map_data : MapData |
    E6_traffic_rules : TrafficRules |
    E9_actuator_cmd : ActuationCommand
  ) E7_warning : Warning | E8_checked_cmd : ActuationCommand

/* ------------------------------------------------------------------ F1 ---- */
/* §5 F1: E1, E2, D1(read) -> object table (D2), ego state (D3), ego pose/table
   to other functions.  F1 writes D2 and D3, reads neither.                  */

process F1_Perception_Localisation (raw: RawSensorData, imu: GnssImu, map: MapData) out: table: ObjectTable, ego: EgoState
ext rd D1
ext wr D2
ext wr D3
pre  raw.frame_count > 0
pre  raw.validity.camera_valid = 1 and raw.validity.radar_valid = 1 and raw.validity.lidar_valid = 1
pre  imu.gnss_valid = 1 and imu.imu_valid = 1
pre  map.valid = 1
post table.valid = 1 and ego.valid = 1
post if imu.imu_valid = 1 then ego.yaw_rate <= 3.5 and ego.yaw_rate >= -3.5
post if raw.frame_count > 0 then ego.timestamp >= raw.timestamp
end_process

/* ------------------------------------------------------------------ F2 ---- */
/* §5 F2: object table, ego state, D1(read) -> predicted trajectories.
   F2 is the only function that computes TTC at Level 0 (§5 F2).             */

process F2_Prediction (table: ObjectTable, ego: EgoState, map: MapData) out: trajectories: PredictedTrajectories
ext rd D1
pre  table.valid = 1 and ego.valid = 1 and map.valid = 1
post trajectories.valid = 1
post trajectories.horizon >= 3.0
post if trajectories.object_count = 0 then trajectories.min_ttc_valid = 0
post if trajectories.min_ttc_valid = 1 then trajectories.object_count > 0
end_process

/* ------------------------------------------------------------------ F3 ---- */
/* §5 F3: ego state, D4(read), predicted trajectories, E3, route(F4), D1(read)
   -> manoeuvre (F5), warning (E7).  F3 writes no store.
   The contract below is the atomic Level-0 projection of the Level-1 AEB
   branch (risk bands A-5, emergency deceleration A-1) onto the single F3.   */

process F3_Behaviour_Planning (ego: EgoState, rules: TrafficRules, trajectories: PredictedTrajectories, intent: DriverIntent, route: Route, map: MapData) out: manoeuvre: Manoeuvre, warning: Warning
ext rd D1
ext rd D4
pre  ego.valid = 1 and trajectories.valid = 1 and route.valid = 1
pre  rules.valid = 1 and map.valid = 1
post manoeuvre.valid = 1
/* warning decision — A-5 bands (T_risk_high = 3.0 s, T_fcw = 1.5 s) */
post if trajectories.min_ttc_valid = 0 then warning.active = 0 and warning.warning_type = "none"
post if trajectories.min_ttc_valid = 1 and trajectories.min_ttc > 3.0 then warning.active = 0 and warning.warning_type = "none"
post if trajectories.min_ttc_valid = 1 and trajectories.min_ttc <= 3.0 and trajectories.min_ttc > 1.5 then warning.active = 1 and warning.warning_type = "caution"
post if trajectories.min_ttc_valid = 1 and trajectories.min_ttc <= 1.5 then warning.active = 1 and warning.warning_type = "imminent_collision"
/* manoeuvre decision — A-1 emergency deceleration, §6 F3.3 driver-intent rule */
post if trajectories.min_ttc_valid = 0 then manoeuvre.required_deceleration >= 0.0
post if trajectories.min_ttc_valid = 1 and trajectories.min_ttc > 3.0 then manoeuvre.required_deceleration >= 0.0
post if trajectories.min_ttc_valid = 1 and trajectories.min_ttc <= 3.0 and trajectories.min_ttc > 1.5 and intent.override_accelerate = 0 then manoeuvre.required_deceleration < 0.0
post if trajectories.min_ttc_valid = 1 and trajectories.min_ttc <= 3.0 and trajectories.min_ttc > 1.5 and intent.override_accelerate = 1 then manoeuvre.required_deceleration >= 0.0
post if trajectories.min_ttc_valid = 1 and trajectories.min_ttc <= 1.5 then manoeuvre.maneouvre_type = "emergency_deceleration" and manoeuvre.required_deceleration <= -6.0 and manoeuvre.target_speed = 0.0
end_process

/* ------------------------------------------------------------------ F4 ---- */
/* §5 F4: E4, ego pose, D1(read) -> route.  F4 writes no store.              */

process F4_Route_Planning (destination: Destination, pose: EgoPose, map: MapData) out: route: Route
ext rd D1
pre  destination.longitude >= -180.0 and destination.longitude <= 180.0
pre  destination.latitude >= -90.0 and destination.latitude <= 90.0
pre  pose.valid = 1 and map.valid = 1
post route.valid = 1
post route.path_length >= 0.0
post route.eta >= 0.0
post route.lane_width > 0.0
end_process

/* ------------------------------------------------------------------ F5 ---- */
/* §5 F5: manoeuvre(F3), route(F4), ego state, D1(read), D4(read) -> trajectory.
   F5 writes no store.                                                        */

process F5_Motion_Planning (manoeuvre: Manoeuvre, route: Route, ego: EgoState, map: MapData, rules: TrafficRules) out: trajectory: Trajectory
ext rd D1
ext rd D4
pre  manoeuvre.valid = 1 and route.valid = 1 and ego.valid = 1
pre  map.valid = 1 and rules.valid = 1
post trajectory.valid = 1
post trajectory.horizon_duration > 0.0
post trajectory.max_permitted_speed >= 0.0
post if rules.posted_speed_limit > 0.0 then trajectory.max_permitted_speed <= rules.posted_speed_limit
post if manoeuvre.required_deceleration < 0.0 then trajectory.max_permitted_acceleration <= manoeuvre.required_deceleration
post trajectory.max_permitted_acceleration <= 3.0
end_process

/* ------------------------------------------------------------------ F6 ---- */
/* §5 F6: trajectory(F5), ego state(D3 read) -> actuator_cmd (E9).
   Actuator envelope: §5 F6 -> A-3 / A-6.                                   */

process F6_Control (trajectory: Trajectory, ego: EgoState) out: actuator: ActuationCommand
ext rd D3
pre  trajectory.valid = 1 and ego.valid = 1
post actuator.valid = 1
post actuator.accel_command <= 3.0
post actuator.steer_command <= 1.0 and actuator.steer_command >= -1.0
post actuator.brake_command >= 0.0
post if trajectory.max_permitted_acceleration < 3.0 then actuator.accel_command <= trajectory.max_permitted_acceleration
end_process

/* ------------------------------------------------------------------ F7 ---- */
/* §5 F7: actuator_cmd (E9), ego state(D3 read), D4(read) -> checked_cmd (E8).
   R-E-2: E9 never reaches the actuators directly.                         */

process F7_Safety_Shield (actuator: ActuationCommand, ego: EgoState, rules: TrafficRules) out: checked: ActuationCommand
ext rd D3
ext rd D4
pre  actuator.valid = 1 and ego.valid = 1 and rules.valid = 1
post checked.valid = 1
post checked.accel_command <= 3.0
post checked.steer_command <= 1.0 and checked.steer_command >= -1.0
post checked.brake_command >= 0.0
post if ego.speed >= rules.posted_speed_limit then checked.accel_command <= 0.0
post if actuator.steer_command <= 1.0 and actuator.steer_command >= -1.0 then checked.steer_command = actuator.steer_command
post if actuator.steer_command > 1.0 then checked.steer_command <= 1.0
post if actuator.steer_command < -1.0 then checked.steer_command >= -1.0
post if actuator.brake_command >= 0.0 then checked.brake_command = actuator.brake_command
end_process

end_module
```

---

## 3. Module `AEB_Branch`（Level 1，F3 的 AEB 分支细化）

```
/* ============================================================================
 * Module AEB_Branch  —  Level 1 refinement of F3 (AEB branch only)
 * §6 / R-L1-1: F3 is decomposed into exactly three sub-functions:
 *   F3.1 TTC Computation -> F3.2 Risk Classification -> F3.3 Maneuver Planning
 * All other Level-0 functions stay atomic (R-SCOPE-4).
 * ========================================================================== */

module AEB_Branch (
    ego_state : EgoState |
    predicted_trajectories : PredictedTrajectories |
    driver_intent : DriverIntent |
    route : Route |
    traffic_rules : TrafficRules |
    map_data : MapData
  ) manoeuvre : Manoeuvre | warning : Warning

/* ----------------------------------------------------------------- F3.1 --- */
/* §6 F3.1: predicted trajectories (F2), ego state -> TTC set.
   "minimum TTC over the object set together with the number of objects
   considered"; "If no object is considered, the TTC set shall report a
   count of 0."                                                            */

process F3_1_TTC_Computation (trajectories: PredictedTrajectories, ego: EgoState) out: ttcset: TTCSet
pre  trajectories.valid = 1 and ego.valid = 1
post ttcset.valid = 1
post ttcset.object_count <= trajectories.object_count
post if ttcset.object_count = 0 then ttcset.min_ttc_valid = 0
post if ttcset.min_ttc_valid = 1 then ttcset.object_count > 0
end_process

/* ----------------------------------------------------------------- F3.2 --- */
/* §6 F3.2: TTC set (F3.1), traffic rules (D4 read) -> risk level, warning (E7).
   Bands: no risk  TTC > T_risk_high ; caution  T_fcw < TTC <= T_risk_high ;
          critical TTC <= T_fcw.  A-5: T_risk_high = 3.0 s, T_fcw = 1.5 s.
   Because the warning is present already from TTC = 3.0 s <= 2.0 s, N-2
   ("the warning shall be present no later than TTC = 2.0 s") is satisfied.  */

process F3_2_Risk_Classification (ttcset: TTCSet, rules: TrafficRules) out: risk_level: String, warning: Warning
ext rd D4
pre  ttcset.valid = 1 and rules.valid = 1
post if ttcset.min_ttc_valid = 0 then risk_level = "no_risk" and warning.active = 0 and warning.warning_type = "none"
post if ttcset.min_ttc_valid = 1 and ttcset.min_ttc > 3.0 then risk_level = "no_risk" and warning.active = 0 and warning.warning_type = "none"
post if ttcset.min_ttc_valid = 1 and ttcset.min_ttc <= 3.0 and ttcset.min_ttc > 1.5 then risk_level = "caution" and warning.active = 1 and warning.warning_type = "caution"
post if ttcset.min_ttc_valid = 1 and ttcset.min_ttc <= 1.5 then risk_level = "critical" and warning.active = 1 and warning.warning_type = "imminent_collision"
end_process

/* ----------------------------------------------------------------- F3.3 --- */
/* §6 F3.3: risk level (F3.2), ego state, driver intent (E3), route (F4),
   D1(read) -> manoeuvre.
   §6 F3.3: no risk -> cruise/keep-lane ; caution -> non-zero deceleration ;
            critical -> required deceleration >= A_emergency = 6.0 m/s^2 and
            target speed 0 ; an accelerate request must not override the
            emergency manoeuvre, but takes precedence in the other risk levels. */

process F3_3_Maneuver_Planning (risk_level: String, ego: EgoState, intent: DriverIntent, route: Route, map: MapData) out: manoeuvre: Manoeuvre
ext rd D1
pre  ego.valid = 1 and route.valid = 1 and map.valid = 1
post manoeuvre.valid = 1
post if risk_level = "critical" then manoeuvre.maneouvre_type = "emergency_deceleration" and manoeuvre.required_deceleration <= -6.0 and manoeuvre.target_speed = 0.0
post if risk_level = "critical" and ego.speed <= 130.0 then manoeuvre.maneouvre_type = "emergency_deceleration" and manoeuvre.required_deceleration <= -6.0
post if risk_level = "caution" and intent.override_accelerate = 0 then manoeuvre.maneouvre_type = "lane_keeping_with_deceleration" and manoeuvre.required_deceleration < 0.0
post if risk_level = "caution" and intent.override_accelerate = 1 then manoeuvre.required_deceleration >= 0.0
post if risk_level = "no_risk" then manoeuvre.maneouvre_type = "keep_lane" and manoeuvre.required_deceleration >= 0.0
end_process

end_module
```

**Level-1 一致性**：F3.1→F3.2→F3.3 链路的输出（warning、manoeuvre）与 Level 0 的 `F3_Behaviour_Planning` 契约逐条对齐（同一 A-5 分带、同一 A-1 紧急减速、同一驾驶意图优先规则），因此 Level 1 是 Level 0 的合法细化而非另立一套语义。

---

## 4. CDFD 元素与连线清单

### 4.1 Level 0 — `ADAS_System`

**元素（共 20 个，严格等于 R-L0-1：7 + 4 + 9）**

| 类别 | ID | 名称 |
|---|---|---|
| Process | F1 | Perception & Localisation |
| Process | F2 | Prediction |
| Process | F3 | Behaviour Planning |
| Process | F4 | Route Planning |
| Process | F5 | Motion Planning |
| Process | F6 | Control |
| Process | F7 | Safety Shield |
| Data store | D1 | HD Map Store |
| Data store | D2 | Object Track Store |
| Data store | D3 | Ego State Store |
| Data store | D4 | Traffic Rules Store |
| External terminal | E1 | raw_sensor_data (in) |
| External terminal | E2 | gnss_imu (in) |
| External terminal | E3 | driver_intent (in) |
| External terminal | E4 | destination (in) |
| External terminal | E5 | map_data (in) |
| External terminal | E6 | traffic_rules (in) |
| External terminal | E7 | warning (out) |
| External terminal | E8 | checked_cmd (out) |
| External terminal | E9 | actuator_cmd (raw command, F6→F7) |

**数据流连线（33 条；`→` 指向消费者；store 方向标 rd / wr）**

| # | 起点 → 终点 | 数据流（类型） | 依据 |
|---|---|---|---|
| 01 | E1 → F1 | raw_sensor_data (RawSensorData) | §5 F1 |
| 02 | E2 → F1 | gnss_imu (GnssImu) | §5 F1 |
| 03 | E5 → D1 | map_data (MapData) **wr** | §4 D1「refreshed by E5」；MD-02 |
| 04 | E6 → D4 | traffic_rules (TrafficRules) **wr** | §4 D4「refreshed by E6」；MD-02 |
| 05 | E3 → F3 | driver_intent (DriverIntent) | §5 F3 |
| 06 | E4 → F4 | destination (Destination) | §5 F4 |
| 07 | D1 → F1 | map segment (MapData) **rd** | §5.1 store reads |
| 08 | D1 → F2 | map segment (MapData) **rd** | §5.1 store reads |
| 09 | D1 → F3 | map segment (MapData) **rd** | §5.1 store reads |
| 10 | D1 → F4 | map segment (MapData) **rd** | §5.1 store reads |
| 11 | D1 → F5 | map segment (MapData) **rd** | §5.1 store reads |
| 12 | D4 → F3 | traffic rules (TrafficRules) **rd** | §5.1 store reads |
| 13 | D4 → F5 | traffic rules (TrafficRules) **rd** | §5.1 store reads |
| 14 | D4 → F7 | traffic rules (TrafficRules) **rd** | §5.1 store reads |
| 15 | D3 → F6 | ego state (EgoState) **rd** | §5.1 store reads |
| 16 | D3 → F7 | ego state (EgoState) **rd** | §5.1 store reads |
| 17 | F1 → D2 | object table (ObjectTable) **wr** | §5.1 store writes |
| 18 | F1 → D3 | ego state (EgoState) **wr** | §5.1 store writes |
| 19 | F1 → F2 | ego state (EgoState) | §5.1「F1 → F2: ego pose and object table」；MD-04 |
| 20 | F1 → F2 | object table (ObjectTable) | §5.1 |
| 21 | F1 → F3 | ego state (EgoState) | §5 F3 输入；MD-03 |
| 22 | F1 → F4 | ego pose (EgoPose) | §5.1 |
| 23 | F1 → F5 | ego state (EgoState) | §5 F5 输入；MD-03 |
| 24 | F2 → F3 | predicted trajectories (PredictedTrajectories) | §5.1 |
| 25 | F2 → F5 | predicted trajectories (PredictedTrajectories) | §5.1 |
| 26 | F3 → F5 | manoeuvre (Manoeuvre) | §5.1 |
| 27 | F3 → E7 | warning (Warning) | §5.1 / R-E-1 |
| 28 | F4 → F3 | route (Route) | §5.1（规格明示双消费者） |
| 29 | F4 → F5 | route (Route) | §5.1（规格明示双消费者） |
| 30 | F5 → F6 | trajectory (Trajectory) | §5.1 |
| 31 | F6 → E9 | actuator_cmd (ActuationCommand) | §5.1 / R-E-2；MD-01 |
| 32 | E9 → F7 | actuator_cmd (ActuationCommand) | §5.1 / R-E-2；MD-01 |
| 33 | F7 → E8 | checked_cmd (ActuationCommand) | §5.1 / R-E-1 / R-E-2 |

**一致性检查**：每条数据流两端均为已声明元素；每条流单一生产者/单一消费者；`route`（28/29）与 `predicted trajectories`（24/25）的双消费者由 §5.1 明示授权；仅 27、33 两条流出系统边界（R-E-1）。

### 4.2 Level 1 — `AEB_Branch`

**元素（3 个 process + 2 个 data store + 6 个边界终端）**

| 类别 | ID | 名称 |
|---|---|---|
| Process | F3.1 | TTC Computation |
| Process | F3.2 | Risk Classification |
| Process | F3.3 | Maneuver Planning |
| Data store | D1 | HD Map Store（读） |
| Data store | D4 | Traffic Rules Store（读） |
| Terminal | T1 | ego_state（来自 F1，边界外） |
| Terminal | T2 | predicted_trajectories（来自 F2，边界外） |
| Terminal | T3 | driver_intent = E3（边界外） |
| Terminal | T4 | route（来自 F4，边界外） |
| Terminal | T5 | warning = E7（出） |
| Terminal | T6 | manoeuvre（送 F5，边界外） |

**数据流连线（11 条）**

| # | 起点 → 终点 | 数据流（类型） | 依据 |
|---|---|---|---|
| G01 | T1 → F3.1 | ego state (EgoState) | §6 F3.1 输入 |
| G02 | T1 → F3.3 | ego state (EgoState) | §6 F3.3 输入（规格明示 ego state 同时供给 F3.1 与 F3.3） |
| G03 | T2 → F3.1 | predicted trajectories (PredictedTrajectories) | §6 F3.1 输入 |
| G04 | F3.1 → F3.2 | TTC set (TTCSet) | §6 链 F3.1→F3.2 |
| G05 | D4 → F3.2 | traffic rules (TrafficRules) **rd** | §6 F3.2 输入 |
| G06 | F3.2 → F3.3 | risk level (String) | §6 链 F3.2→F3.3 |
| G07 | F3.2 → T5 (E7) | warning (Warning) | §6 F3.2 输出 / R-E-1 |
| G08 | T3 (E3) → F3.3 | driver intent (DriverIntent) | §6 F3.3 输入 |
| G09 | T4 (F4) → F3.3 | route (Route) | §6 F3.3 输入 |
| G10 | D1 → F3.3 | map segment (MapData) **rd** | §6 F3.3 输入 |
| G11 | F3.3 → T6 (F5) | manoeuvre (Manoeuvre) | §6 F3.3 输出 |

---

## 5. Open issues

### 5.1 规格 §11 提出的四个问题（含本模型答复）

| # | 问题 | 答复 |
|---|---|---|
| Q1 | 七个功能划分对 L2 是否充分？是否需要独立的驾驶员监视功能？ | **不新增元素**。R-L0-1 禁止 Level 0 出现第 8 个功能，R-SCOPE-3 禁止建模算法内部；E3 的 `attention_state` 仅为输入数据，本模型不据此派生任何行为。若引入 DM 功能，应作为 Level 2 对 F3/F7 的细化，而不是 Level 0 的新元素。 |
| Q2 | D3 由 F1 写、被 F6/F7 读，所有权是否可接受？ | **可接受，按规格保留**。D3 的 owner 就是 F1（§4），§5.1 明确把 D3 的读指派给 F6/F7，因此不违反 R-D-2；D3 正是感知链与控制/安全链之间的官方交接点。无需专职写入函数。 |
| Q3 | 规格固定阈值但不固定时序，紧急分支是否需要时序（周期）要求？ | **需要，但本模型不建模**。F3「at every planning cycle」（§5）与 N-6 的响应时间 ρ = 0.1 s（A-2）都预设了周期存在；但规格未给任何周期时间，故模型不发明时间基准数据 → 记为 MD-16。 |
| Q4 | AEB 分支作为 Level 1 细化是否恰当，是否应改为细化 F6/F7 动作链？ | **保持 F3 的 AEB 分支**。理由：阈值 A-1、A-5 本身就落在 AEB 决策里（N-2/N-3/N-4 都服务于「何时、以多大减速度介入」），而 F6/F7 只承担执行与仲裁，不承载风险分级；若改细化 F6/F7，A-1/A-5 将与执行包络纠缠。且 R-SCOPE-4/R-L1-1 已强制此分解。 |

### 5.2 建模决定与未决点

| ID | 类别 | 内容 | 处置 |
|---|---|---|---|
| MD-01 | 建模决定 | §3 把 E9 记为方向 "in"，但其生产者 F6 与消费者 F7 都在系统内部 | 渲染成承载 F6→F7 原始指令的边界终端（F31/F32），以同时满足 R-L0-1 的 E1–E9 清单与 R-E-2 的可读性 |
| MD-02 | 未决 | D1「refreshed by E5」、D4「refreshed by E6」，但没有任何功能被指派去写 D1/D4 | 建模为 E5→D1、E6→D4 的边界写流（连线 03/04）。与 R-D-1「只有 owner 写存储」存在张力：规格未指定 D1/D4 的写入 owner，模型不臆造写入方 |
| MD-03 | 建模决定 | §5 要求 F3、F5 的输入含 ego state，但 §5.1 的存储读清单只把 D3 的读给 F6/F7；若 F3/F5 去读 D3 将违反 R-D-2 | 增补 F1→F3、F1→F5 两条 ego state 流（连线 21/23）。这是 §5 输入清单强制要求的依赖，非新增功能/存储 |
| MD-04 | 建模决定 | §5 F2 的输入写 "ego state"，§5.1 却把 F1→F2 的载荷写作 "ego pose" | F1→F2 传 EgoState（含 pose 字段），同时满足两种表述 |
| MD-05 | 建模决定 | R-G-6 要求「读某数据的字段」的 post 必须被该数据的非空性守卫，但规格未定义任何有效性/空值语义，且本 SOFL 子集无 null 类型 | 为所有数据类型引入生产者写入的 `valid` 标志（以及 TTC 的 `min_ttc_valid`）：E5/E6 写 D1/D4 的 valid，F1 写 D2/D3 内容的 valid，F2/F3/F5/F6/F7 写各自输出。标志可为 0，故是真实约束而非恒真 |
| MD-06 | 建模决定 | 本子集无算术运算，无法把「≥ 6.0 m/s² 的减速度」与「轨迹允许的最大加速度」直接比较 | 统一符号约定：减速量带符号（制动为负），故 A-1 表达为 `required_deceleration <= -6.0`，F5 的「兑现减速要求」表达为 `max_permitted_acceleration <= manoeuvre.required_deceleration`；`brake_command` 为非负幅值 |
| MD-07 | 建模决定 | 规格中速度以 km/h 出现（N-1、N-4、E6），而 §7 推导用 m/s（30.6 m/s） | 模型内统一：速度 km/h、加速度 m/s²、时间 s、角速度 rad/s；不做换算，§7 推导中的 m/s 数值不进入契约 |
| MD-08 | 建模决定 | `signal_state`、`route_preference`、`object_class`、`attention_state`、`override_*` 的编码规格未给出 | 用整数码占位；`manoeuvre_type`/`risk_level`/`warning_type` 用规格原词作 String，不自造编号 |
| MD-09 | 建模决定 | 本 SOFL 子集禁用 `seq of`，无法表达逐目标列表 | ObjectTable 只承载 `object_count` + 前车目标运动学；D2 中「每个目标」的条目未逐字段建模 |
| MD-10 | 建模决定 | 车道拓扑、路线所需车道几何的结构规格未给出 | 最小编码：`LaneTopology.lane_link_count`；`Route.lane_count`、`Route.lane_width` |
| MD-11 | 未决（规格内部冲突） | §5 F2 规定「F2 是唯一计算 TTC 的功能」，§6 F3.1 又要求 F3.1「对每个预测目标计算 TTC」 | Level 0 让 F3 消费 F2 的 min TTC；Level 1 按 §6 由 F3.1 计算 TTC 集。两者对象集合是否相同规格未规定，故未断言 F3.1 的最小 TTC 与 F2 的 min TTC 之间的数值关系 |
| MD-12 | 未决 | §6 把 D4 列为 F3.2 输入，但风险分级只写成 TTC 的函数，D4 的作用未定义 | F3.2 保留对 D4 的读，但契约中不产生任何影响 |
| MD-13 | 未决 | N-5 的 RSS `d_min`（[S4] 式(1)）未在规格中复现 | 无法给出数值约束；仅映射到 F2 的前车目标运动学与 F5 的速度规划 |
| MD-14 | 未决 | N-6 的「危险状况持续」守卫与响应时间 ρ = 0.1 s 在 F7 的输入中无对应数据 | F7 无法表达该守卫；N-6 仅部分映射到 F3.3 的紧急减速（6.0 ≥ a_min,brake 4.0） |
| MD-15 | 未决 | N-7 的「横向加速度能力」无数值（A-4 的 3.5 rad/s 是横摆角速度上界，单位不同） | 只保留可检的 A-6 转向包络；Trajectory 类型不设横向加速度字段 |
| MD-16 | 未决 | A-1（6.0 m/s²）高于 A-2 的 `a_max,brake = a_min,brake = 4.0 m/s²` | F5「兑现减速要求」的 post 蕴含 6.0 m/s² 的可用制动能力，与 A-2 冲突；按「规格沉默即留空」原则不作调和 |
| MD-17 | 未决 | F7 的「safety envelope」无数值定义 | 复用 §5 F6 唯一引用的 A-3 / A-6 作为可检包络；F7 的制动幅值上限留空（制动指令按原样透传） |
| MD-18 | 建模决定 | §6 允许 no-risk 给出「cruise/keep-lane」，但本子集无析取 | 固定取 `keep_lane`；「caution + 驾驶员加速」情形下的 manoeuvre_type 不约束（规格未定义映射） |
| MD-19 | 建模决定 | 规格只规定「何时报警」，未规定报警类型与风险级的对应 | 约定 caution → "caution"、critical → "imminent_collision"、no risk → "none" |
| MD-20 | 未决 | D2 被 F1 写入，但 §5.1 未指派任何函数读 D2（目标表是经 F1→F2 直接流的） | 照规格建模：D2 存在、有写无读，记为规格层面的冗余 |
| MD-21 | 建模决定 | §5.1 给出了逐传感器有效性标志，但未给融合/降级规则 | F1 的 pre 要求三个传感器标志与 GNSS/IMU 标志均为 1；若需降级运行需另加规则 |
| MD-22 | 未决 | §8 A-5 的理由引用了「R-F2-1」，而文档中不存在该 R 编号 | 解释为 §5 F2 的「horizon of at least 3 s」子句（A-7 = 3.0 s） |
| MD-23 | 未决 | 目标车道选择规则、目标表逐目标字段、路线偏好语义规格均未给出 | `Manoeuvre.target_lane` 被携带但不约束；`Route.route_preference`/D2 逐目标字段见 MD-09 |
| MD-24 | 建模决定 | §5 F6 只说「把轨迹转成执行指令」，未给数值关系 | F6 增加一条定性链接 post：`accel_command <= trajectory.max_permitted_acceleration`（仅当轨迹上限严于 3.0 时） |
| MD-25 | 建模决定 | 规格未定义「无 TTC」时的风险分级 | 约定 `min_ttc_valid = 0` → `no_risk`、不报警、不要求减速 |
| MD-26 | 未决 | 规格未给「轨迹规划时域」与 A-7「预测时域 3.0 s」的关系 | 只约束 `horizon_duration > 0.0`，不引入 3.0 的数值约束 |

---

## 6. 可追溯性矩阵

### 6.1 R-xx 条款 → 模型元素

| 条款 | 模型元素 | 说明 |
|---|---|---|
| R-SCOPE-1 | `ADAS_System` 模块头；`DriverIntent.attention_state`；`F7_Safety_Shield` | 车载 L2：驾驶员意图为输入数据、防护为最后一道关；驾驶员监视本身不建模（Q1） |
| R-SCOPE-2 | 模块头端口 E1–E6（入）/ E7–E8（出）；终端 E9；无内部传感器/执行器元素 | 边界外一切仅作外部 I/O |
| R-SCOPE-3 | 全部 10 个 process 契约均为数据级契约 | 无检测器/跟踪器/规划器/控制器内部算法 |
| R-SCOPE-4 | `ADAS_System`（L0）+ `AEB_Branch`（L1）；F1/F2/F4/F5/F6/F7 在 L1 保持原子 | 恰好细化 F3 一个功能 |
| R-E-1 | 模块头输出端口仅 `E7_warning`、`E8_checked_cmd`；CDFD 仅连线 27、33 出边界 | 无其他对外信号 |
| R-E-2 | `F7_Safety_Shield` 全部 post；连线 31（F6→E9）、32（E9→F7）、33（F7→E8） | E9 必经 F7 才能出系统 |
| R-D-1 | `ext wr` 仅出现在 F1（D2、D3）；D1/D4 的写为边界刷新流（MD-02） | 其余 6 个函数无任何 `ext wr` |
| R-D-2 | `ext rd` 集合 = {F1:D1, F2:D1, F3:D1+D4, F4:D1, F5:D1+D4, F6:D3, F7:D3+D4}，与 §5.1 逐项一致 | 无越权读 |
| R-L0-1 | §4.1 元素表：7 process + 4 store + 9 terminal，无增删 | 20 个元素 |
| R-L1-1 | F3.1 / F3.2 / F3.3 三个 process，链 F3.1→F3.2→F3.3 | 恰好三个子功能 |
| R-G-1 | 10 个 process 全部具备 pre + post + 至少一条量化约束或定性 post（见 §7 自查表） | 量化项全部来自 §7/§8 |
| R-G-2 | 本矩阵 | — |
| R-G-3 | 每个元素均在上表出现；所有建模附加物列入 MD-01…MD-26 | 无孤儿元素 |
| R-G-4 | §4.1/§4.2 连线表：每条命名流单一生产者/单一消费者；仅 route 与 predicted trajectories 双消费者（§5.1 明示） | 无隐式依赖 |
| R-G-5 | 每个生产者的输出都有被点名的消费者：F1→D2/D3/F2/F3/F4/F5；F2→F3/F5；F3→F5/E7；F4→F3/F5；F5→F6；F6→E9；F7→E8 | 无「无人消费」的输出 |
| R-G-6 | 所有读取 datum 字段的 post 均带守卫（`valid = 1` / `min_ttc_valid = 1`）；validity 标志由生产者写入（MD-05） | 无空值泄漏 |

### 6.2 规范阈值 N-1…N-7 与假设值 A-1…A-7 → 模型元素

| 阈值 | 数值 | 落到哪个契约 | 状态 |
|---|---|---|---|
| N-1 | 130 km/h | `F3_3_Maneuver_Planning`：`critical` 分支在 `ego.speed <= 130.0` 时仍给出紧急减速 | 已建模（静止目标除外条件未建模，规格未给判据） |
| N-2 | 警告不晚于 TTC = 2.0 s | `F3_2_Risk_Classification` 警告自 TTC ≤ 3.0 s 起（早于 2.0 s）；Level 0 `F3` 同 | 已建模（满足关系由 post 蕴含） |
| N-3 | > 30 km/h 撞击速度降低 | A-1 的定尺依据 → `required_deceleration <= -6.0` | 仅作引用（模型不表达撞击速度） |
| N-4 | CCRm 60–130 km/h / 目标 20 km/h / −4 m/s² | A-1、A-2 的定尺依据 | 仅作引用（测试包络非车载功能） |
| N-5 | RSS `d_min` 安全距离 | F2 的前车目标运动学、F5 的速度规划 | **未数值化**（MD-13） |
| N-6 | 至少 `a_min,brake` 制动、响应时间 ρ | F3.3 紧急减速 6.0 ≥ 4.0 | **部分**（守卫/时序未决，MD-14） |
| N-7 | 横向加速度包络 | F5 的轨迹、F6/F7 的 A-6 转向包络 | **部分/未决**（MD-15） |
| A-1 | 6.0 m/s² | `F3_3`（及 Level 0 `F3`）：`required_deceleration <= -6.0` | 已建模 |
| A-2 | ρ=0.1 s；a_max,accel=2.0；a_max,brake=4.0；a_min,brake=4.0 | N-6 经 F3.3 引用；F7 的包络定义留空 | 部分 + 未决（MD-14/16/17） |
| A-3 | 3.0 m/s² | `F5`（`max_permitted_acceleration <= 3.0`）、`F6`、`F7` | 已建模 |
| A-4 | 3.5 rad/s | `F1`：`ego.yaw_rate <= 3.5 and ego.yaw_rate >= -3.5` | 已建模 |
| A-5 | T_risk_high=3.0 s；T_fcw=1.5 s | `F3_2`（及 Level 0 `F3`）分带 | 已建模 |
| A-6 | 转向 ±1.0 | `F6`、`F7` | 已建模 |
| A-7 | 预测时域 3.0 s | `F2`：`trajectories.horizon >= 3.0` | 已建模 |

---

## 7. 自查表：每个 process 的真实 pre 约束与依据

> 判定口径：守卫/前置条件必须在「类型的全部取值」下**不恒成立**，且能指向具体条款或阈值。

| Process | pre 中的真实约束 | 依据 | 量化 post（依据） | 备注 |
|---|---|---|---|---|
| **F1** | `raw.frame_count > 0` | §5 F1「convert raw sensor data into a fused object table」；E1 内容 | — | 帧数为 `nat`，`> 0` 非恒真 |
| | `raw.validity.camera_valid = 1 and radar_valid = 1 and lidar_valid = 1` | E1「per-sensor validity flags」；R-G-6 | `ego.yaw_rate <= 3.5 and ego.yaw_rate >= -3.5`（**A-4**） | 融合需全部有效；降级规则未定义（MD-21） |
| | `imu.gnss_valid = 1 and imu.imu_valid = 1` | E2「with validity flags」 | — | |
| | `map.valid = 1` | D1 内容 + R-G-6（MD-05） | `ego.timestamp >= raw.timestamp`（定性：自我状态不早于所用帧） | |
| **F2** | `table.valid = 1 and ego.valid = 1 and map.valid = 1` | 生产者写入的有效性标志；R-G-6 | `trajectories.horizon >= 3.0`（**A-7** + §5 F2「horizon of at least 3 s」） | 无恒真项 |
| **F3** | `ego.valid = 1 and trajectories.valid = 1 and route.valid = 1` | R-G-6 / MD-05 | 分带 `3.0` / `1.5`（**A-5**，并满足 **N-2**）；`required_deceleration <= -6.0`、`target_speed = 0.0`（**A-1** / §6 F3.3） | 驾驶意图优先规则来自 §6 F3.3 的原子投影 |
| **F4** | `destination.longitude >= -180.0 and destination.longitude <= 180.0` | E4「longitude, latitude」+ 地理量程 | `route.path_length >= 0.0`、`route.eta >= 0.0`、`route.lane_width > 0.0`（§7/§8 无 route 阈值 → 定性范围 post，R-G-1 兜底） | 这是量程型真实前置条件 |
| | `destination.latitude >= -90.0 and destination.latitude <= 90.0` | 同上 | — | |
| | `pose.valid = 1 and map.valid = 1` | R-G-6 | — | |
| **F5** | `manoeuvre.valid = 1 and route.valid = 1 and ego.valid = 1` | R-G-6 | `max_permitted_speed <= rules.posted_speed_limit`（§5 F5「never command a speed above the applicable speed limit」） | 与 D4 的限速值直接比较，非阈值号但为量化约束 |
| | `map.valid = 1 and rules.valid = 1` | R-G-6 | `max_permitted_acceleration <= manoeuvre.required_deceleration`（§5 F5「honour the deceleration requirement」）；`max_permitted_acceleration <= 3.0`（**A-3**） | |
| **F6** | `trajectory.valid = 1 and ego.valid = 1`（ego 来自 D3） | R-G-6 / §5.1 store reads | `accel_command <= 3.0`（**A-3**）；`steer_command <= 1.0 and >= -1.0`（**A-6**） | |
| **F7** | `actuator.valid = 1 and ego.valid = 1 and rules.valid = 1` | R-G-6 | `checked.accel_command <= 3.0`（**A-3**）；`checked.steer_command <= 1.0 and >= -1.0`（**A-6**）；`ego.speed >= rules.posted_speed_limit → checked.accel_command <= 0.0`（§5 F7「enforce the traffic rules」） | 转向保持与限幅各一条量化 post |
| **F3.1** | `trajectories.valid = 1 and ego.valid = 1` | R-G-6 | `ttcset.object_count <= trajectories.object_count`（§6 F3.1「number of objects considered」） | 无 §7/§8 专属阈值 → 用数量比较作量化约束 |
| | | | `object_count = 0 → min_ttc_valid = 0`（§6 F3.1「count of 0」） | |
| **F3.2** | `ttcset.valid = 1 and rules.valid = 1` | R-G-6 | `> 3.0` / `<= 3.0 and > 1.5` / `<= 1.5`（**A-5**）；警告起始 ≤ 2.0 s 满足 **N-2** | D4 已读入但契约无影响（MD-12） |
| **F3.3** | `ego.valid = 1 and route.valid = 1 and map.valid = 1` | R-G-6 | `required_deceleration <= -6.0`（**A-1**）；`target_speed = 0.0`（§6 F3.3）；`ego.speed <= 130.0`（**N-1**）；`required_deceleration < 0.0`（caution 非零减速，§6 F3.3）；`>= 0.0`（驾驶加速优先，§6 F3.3） | 紧急分支的守卫不含 intent → 加速请求无法覆盖紧急减速 |

**是否省略了 pre**：本模型中**没有**任何 process 省略 `pre`——每个功能都存在至少一条真实前置条件（有效性标志、量程条件或状态前置条件）。若某功能的输入只有规格直接给出的无附加约束的端口（例如本模型中不存在的「纯输入转出」类功能），则应按指示省略 `pre` 而不以恒真条件占位；本规格未出现此类情形。**未使用任何恒真条件**：`x <> null`、`x <> ""`、`x = x`、`n >= 0 (nat)`、`if true` 在全文中均不存在（`valid`/`min_ttc_valid` 均为生产者写入、取值可为 0 的 `nat` 字段）。
