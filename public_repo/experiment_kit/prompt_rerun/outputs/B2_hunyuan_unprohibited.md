# SOFL 形式化规格 — NL-RQ-ADAS-v1

> 建模范围：仅规格中写明的内容。未写明的设计决定不新增函数/存储/信号/阈值，统一登记在 §5 open issues。

## 0. 记号与表示约定（建模约定，见 OI-10 / OI-16）

- 模块头格式：`( 入1: 类型 | 入2: 类型 ) 出1: 类型 | 出2: 类型, 出2b: 类型`。`|` 分端口，`,` 分同端口多条流，条目为 `名: 类型`。
- 一个过程允许多个 `post if ... then ...` 子句，按**合取**理解（各守卫分别触发各自谓词）；不使用 `or / not / => / 量词 / seq of`。
- 每个 composed 类型带 `valid: nat` 存在标志（1 = 数据存在），用于满足 R-G-6 的非空守卫；E1/E2 的 valid 字段直接对应规格中的 validity flags，其余 valid 为表示约定（OI-10）。布尔量以 nat 0/1 编码（OI-10）。
- 速度、距离单位为 km/h / m，加速度为 m/s²，时间为 s；规格未统一声明单位，此约定记入 OI-16。
- 预/后置中的 `<> ""` 与 `>= 0` 为良构性守卫，不是规范阈值。

---

# 1. Module `ADAS_System`（Level 0）

## 1.1 Module head

```
module ADAS_System
( raw_sensor_data: RawSensorData | gnss_imu: GnssImuData | driver_intent: DriverIntent | destination: Destination | map_data: MapData | traffic_rules: TrafficRules | actuator_cmd: ActuatorCmd )
warning: Warning | checked_cmd: CheckedCmd
```

端口对应：E1 `raw_sensor_data`、E2 `gnss_imu`、E3 `driver_intent`、E4 `destination`、E5 `map_data`、E6 `traffic_rules`、E9 `actuator_cmd` 为入端口；E7 `warning`、E8 `checked_cmd` 为出端口（R-E-1）。

## 1.2 Type declarations

```
RawSensorData = composed of
  camera: SensorFrame,
  radar: SensorFrame,
  lidar: SensorFrame,
  valid: nat
end

SensorFrame = composed of
  valid: nat,
  timestamp: real
end

GnssImuData = composed of
  gnss: GnssFix,
  imu: ImuSample,
  valid: nat
end

GnssFix = composed of
  position: Pose,
  heading: real,
  valid: nat
end

ImuSample = composed of
  angular_rate: real,
  acceleration: real,
  valid: nat
end

Pose = composed of
  x: real,
  y: real,
  valid: nat
end

DriverIntent = composed of
  requested_cruise_speed: real,
  override_accelerate: nat,
  override_brake: nat,
  override_steer: nat,
  driver_attention: String,
  valid: nat
end

Destination = composed of
  longitude: real,
  latitude: real,
  route_preferences: String,
  valid: nat
end

MapData = composed of
  road_id: String,
  lane_id: String,
  posted_speed_limit: real,
  curvature: real,
  lane_topology: String,
  valid: nat
end

TrafficRules = composed of
  posted_speed_limit: real,
  signal_state: String,
  valid: nat
end

ObjectInfo = composed of
  id: String,
  x: real,
  y: real,
  velocity: real,
  class: String,
  valid: nat
end

ObjectTable = composed of
  object_count: nat,
  records: String,
  lead_object: ObjectInfo,
  valid: nat
end

EgoState = composed of
  pose: Pose,
  speed: real,
  yaw_rate: real,
  acceleration: real,
  timestamp: real,
  valid: nat
end

PredictedTrajectories = composed of
  object_count: nat,
  horizon: real,
  trajectories: String,
  valid: nat
end

Manoeuvre = composed of
  manoeuvre_type: String,
  target_speed: real,
  target_lane: String,
  required_deceleration: real,
  valid: nat
end

Route = composed of
  path_length: real,
  eta: real,
  lane_geometry: String,
  valid: nat
end

Trajectory = composed of
  max_speed: real,
  max_accel: real,
  horizon: real,
  valid: nat
end

ActuatorCmd = composed of
  longitudinal_accel: real,
  brake: real,
  steering: real,
  valid: nat
end

CheckedCmd = composed of
  longitudinal_accel: real,
  brake: real,
  steering: real,
  valid: nat
end

Warning = composed of
  warning_type: String,
  active: nat,
  valid: nat
end
```

## 1.3 Process contracts

```
// F1 — Perception & Localisation   [§5 F1, R-G-1, R-D-1]
process F1(raw_sensor_data: RawSensorData, gnss_imu: GnssImuData, map_data: MapData) out: object_table: ObjectTable, ego_state: EgoState, ego_pose: Pose
ext rd D1
ext wr D2
ext wr D3
pre raw_sensor_data.valid = 1 and raw_sensor_data.camera.valid = 1 and raw_sensor_data.radar.valid = 1 and raw_sensor_data.lidar.valid = 1 and gnss_imu.valid = 1 and gnss_imu.gnss.valid = 1 and gnss_imu.imu.valid = 1 and map_data.valid = 1
post if raw_sensor_data.camera.valid = 1 and raw_sensor_data.radar.valid = 1 and raw_sensor_data.lidar.valid = 1 then object_table.valid = 1 and object_table.object_count >= 0 and ego_state.valid = 1 and ego_pose.valid = 1
post if gnss_imu.gnss.valid = 1 then ego_state.yaw_rate <= 3.5 and ego_state.yaw_rate >= -3.5
post if ego_pose.valid = 1 then ego_pose.x = ego_state.pose.x and ego_pose.y = ego_state.pose.y
end_process

// F2 — Prediction   [§5 F2, §5.1, A-7]
process F2(object_table: ObjectTable, ego_pose: Pose, map_data: MapData) out: predicted_trajectories: PredictedTrajectories
ext rd D1
pre object_table.valid = 1 and ego_pose.valid = 1 and map_data.valid = 1 and object_table.object_count >= 0
post if object_table.object_count > 0 then predicted_trajectories.valid = 1 and predicted_trajectories.object_count = object_table.object_count and predicted_trajectories.horizon >= 3.0
post if object_table.object_count = 0 then predicted_trajectories.valid = 1 and predicted_trajectories.object_count = 0
post if predicted_trajectories.object_count > 0 then predicted_trajectories.trajectories <> ""
end_process

// F3 — Behaviour Planning   [§5 F3; 量化约束在 Level 1 的 F3_2/F3_3 中给出]
process F3(ego_state: EgoState, traffic_rules: TrafficRules, predicted_trajectories: PredictedTrajectories, driver_intent: DriverIntent, route: Route, map_data: MapData) out: manoeuvre: Manoeuvre, warning: Warning
ext rd D1
ext rd D4
pre ego_state.valid = 1 and traffic_rules.valid = 1 and predicted_trajectories.valid = 1 and driver_intent.valid = 1 and route.valid = 1 and map_data.valid = 1
post if predicted_trajectories.valid = 1 then manoeuvre.valid = 1 and manoeuvre.manoeuvre_type <> "" and manoeuvre.target_lane <> "" and warning.valid = 1 and warning.warning_type <> "" and warning.active >= 0
post if manoeuvre.required_deceleration > 0 then manoeuvre.target_speed >= 0
end_process

// F4 — Route Planning   [§5 F4]
process F4(destination: Destination, ego_pose: Pose, map_data: MapData) out: route: Route
ext rd D1
pre destination.valid = 1 and ego_pose.valid = 1 and map_data.valid = 1
post if destination.valid = 1 and map_data.valid = 1 then route.valid = 1 and route.path_length >= 0 and route.eta >= 0 and route.lane_geometry <> ""
post if ego_pose.valid = 1 then route.lane_geometry <> ""
end_process

// F5 — Motion Planning   [§5 F5; 速度上限来自 D4]
process F5(manoeuvre: Manoeuvre, route: Route, ego_state: EgoState, predicted_trajectories: PredictedTrajectories, map_data: MapData, traffic_rules: TrafficRules) out: trajectory: Trajectory
ext rd D1
ext rd D4
pre manoeuvre.valid = 1 and route.valid = 1 and ego_state.valid = 1 and predicted_trajectories.valid = 1 and map_data.valid = 1 and traffic_rules.valid = 1
post if traffic_rules.valid = 1 then trajectory.valid = 1 and trajectory.max_speed <= traffic_rules.posted_speed_limit
post if manoeuvre.required_deceleration > 0 then trajectory.max_speed <= manoeuvre.target_speed
post if route.valid = 1 and predicted_trajectories.valid = 1 then trajectory.horizon >= 0 and trajectory.max_accel >= 0
end_process

// F6 — Control   [§5 F6, A-3, A-6]
process F6(trajectory: Trajectory, ego_state: EgoState) out: actuator_cmd: ActuatorCmd
ext rd D3
pre trajectory.valid = 1 and ego_state.valid = 1 and trajectory.horizon > 0
post if trajectory.valid = 1 then actuator_cmd.valid = 1 and actuator_cmd.longitudinal_accel <= 3.0 and actuator_cmd.steering <= 1.0 and actuator_cmd.steering >= -1.0
post if actuator_cmd.valid = 1 then actuator_cmd.brake >= 0
end_process

// F7 — Safety Shield   [§5 F7, R-E-2, A-3, A-6]
process F7(actuator_cmd: ActuatorCmd, ego_state: EgoState, traffic_rules: TrafficRules) out: checked_cmd: CheckedCmd
ext rd D3
ext rd D4
pre actuator_cmd.valid = 1 and ego_state.valid = 1 and traffic_rules.valid = 1
post if actuator_cmd.steering >= -1.0 and actuator_cmd.steering <= 1.0 then checked_cmd.steering = actuator_cmd.steering
post if actuator_cmd.steering > 1.0 then checked_cmd.steering = 1.0
post if actuator_cmd.steering < -1.0 then checked_cmd.steering = -1.0
post if traffic_rules.valid = 1 then checked_cmd.valid = 1 and checked_cmd.longitudinal_accel <= 3.0 and checked_cmd.brake >= 0
end_process
```

---

# 2. Module `AEB_Branch`（Level 1，F3 的 AEB 分支细化）

## 2.1 Module head

```
module AEB_Branch
( predicted_trajectories: PredictedTrajectories | ego_state: EgoState | traffic_rules: TrafficRules | driver_intent: DriverIntent | route: Route | map_data: MapData )
manoeuvre: Manoeuvre | warning: Warning
```

## 2.2 Type declarations

```
PredictedTrajectories = composed of
  object_count: nat,
  horizon: real,
  trajectories: String,
  valid: nat
end

EgoState = composed of
  pose: Pose,
  speed: real,
  yaw_rate: real,
  acceleration: real,
  timestamp: real,
  valid: nat
end

Pose = composed of
  x: real,
  y: real,
  valid: nat
end

TrafficRules = composed of
  posted_speed_limit: real,
  signal_state: String,
  valid: nat
end

DriverIntent = composed of
  requested_cruise_speed: real,
  override_accelerate: nat,
  override_brake: nat,
  override_steer: nat,
  driver_attention: String,
  valid: nat
end

Route = composed of
  path_length: real,
  eta: real,
  lane_geometry: String,
  valid: nat
end

MapData = composed of
  road_id: String,
  lane_id: String,
  posted_speed_limit: real,
  curvature: real,
  lane_topology: String,
  valid: nat
end

TtcSet = composed of
  object_count: nat,
  min_ttc: real,
  valid: nat
end

Manoeuvre = composed of
  manoeuvre_type: String,
  target_speed: real,
  target_lane: String,
  required_deceleration: real,
  valid: nat
end

Warning = composed of
  warning_type: String,
  active: nat,
  valid: nat
end
```

## 2.3 Process contracts

```
// F3.1 — TTC Computation   [§6 F3.1]
process F3_1(predicted_trajectories: PredictedTrajectories, ego_state: EgoState) out: ttc_set: TtcSet
pre predicted_trajectories.valid = 1 and ego_state.valid = 1
post if predicted_trajectories.object_count = 0 then ttc_set.valid = 1 and ttc_set.object_count = 0
post if predicted_trajectories.object_count > 0 then ttc_set.valid = 1 and ttc_set.object_count = predicted_trajectories.object_count and ttc_set.min_ttc >= 0
end_process

// F3.2 — Risk Classification   [§6 F3.2, A-5, N-2]
process F3_2(ttc_set: TtcSet, traffic_rules: TrafficRules) out: risk_level: String, warning: Warning
ext rd D4
pre ttc_set.valid = 1 and traffic_rules.valid = 1
post if ttc_set.object_count = 0 then risk_level = "no risk" and warning.valid = 1 and warning.active = 0 and warning.warning_type = "none"
post if ttc_set.min_ttc > 3.0 then risk_level = "no risk" and warning.valid = 1 and warning.active = 0 and warning.warning_type = "none"
post if ttc_set.min_ttc <= 3.0 and ttc_set.min_ttc > 1.5 then risk_level = "caution" and warning.valid = 1 and warning.active = 1 and warning.warning_type = "caution"
post if ttc_set.min_ttc <= 1.5 then risk_level = "critical" and warning.valid = 1 and warning.active = 1 and warning.warning_type = "imminent collision"
end_process

// F3.3 — Maneuver Planning   [§6 F3.3, N-1, N-3, N-6, A-1, A-2]
process F3_3(risk_level: String, ego_state: EgoState, driver_intent: DriverIntent, route: Route, map_data: MapData) out: manoeuvre: Manoeuvre
ext rd D1
pre ego_state.valid = 1 and driver_intent.valid = 1 and route.valid = 1 and map_data.valid = 1 and risk_level <> ""
post if risk_level = "no risk" then manoeuvre.valid = 1 and manoeuvre.manoeuvre_type = "cruise/keep-lane" and manoeuvre.required_deceleration = 0
post if risk_level = "caution" then manoeuvre.valid = 1 and manoeuvre.manoeuvre_type = "deceleration" and manoeuvre.required_deceleration > 0
post if risk_level = "critical" and ego_state.speed <= 130 then manoeuvre.valid = 1 and manoeuvre.manoeuvre_type = "emergency deceleration" and manoeuvre.required_deceleration >= 6.0 and manoeuvre.target_speed = 0
post if risk_level = "critical" and driver_intent.override_accelerate = 1 then manoeuvre.required_deceleration >= 6.0 and manoeuvre.target_speed = 0
post if risk_level = "caution" and driver_intent.override_accelerate = 1 then manoeuvre.target_speed >= driver_intent.requested_cruise_speed
end_process
```

---

# 3. CDFD — Level 0（`ADAS_System`）

## 3.1 元素（恰好 20 个，R-L0-1）

- **Processes (7)：** F1 Perception & Localisation、F2 Prediction、F3 Behaviour Planning、F4 Route Planning、F5 Motion Planning、F6 Control、F7 Safety Shield。
- **Data stores (4)：** D1 HD Map Store、D2 Object Track Store、D3 Ego State Store、D4 Traffic Rules Store。
- **External terminals (9)：** E1 `raw_sensor_data`(in)、E2 `gnss_imu`(in)、E3 `driver_intent`(in)、E4 `destination`(in)、E5 `map_data`(in)、E6 `traffic_rules`(in)、E7 `warning`(out)、E8 `checked_cmd`(out)、E9 `actuator_cmd`(in)。

## 3.2 数据流连线（均为具名、有向、单生产者）

| # | 数据流 | 起点 → 终点 | 类型 | 依据 |
|---|---|---|---|---|
| 1 | `raw_sensor_data` | E1 → F1 | RawSensorData | §5 F1 |
| 2 | `gnss_imu` | E2 → F1 | GnssImuData | §5 F1 |
| 3 | `driver_intent` | E3 → F3 | DriverIntent | §5 F3 |
| 4 | `destination` | E4 → F4 | Destination | §5 F4 |
| 5 | `map_data` | E5 → D1（外部刷新） | MapData | §4 D1 |
| 6 | `traffic_rules` | E6 → D4（外部刷新） | TrafficRules | §4 D4 |
| 7 | `ego_pose` | F1 → F2 | Pose | §5.1 |
| 8 | `object_table` | F1 → F2 | ObjectTable | §5.1 |
| 9 | `ego_pose` | F1 → F4 | Pose | §5.1 |
| 10 | `predicted_trajectories` | F2 → F3 | PredictedTrajectories | §5.1 |
| 11 | `predicted_trajectories` | F2 → F5 | PredictedTrajectories | §5.1（规格明确双消费者） |
| 12 | `manoeuvre` | F3 → F5 | Manoeuvre | §5.1 |
| 13 | `route` | F4 → F3 | Route | §5.1 |
| 14 | `route` | F4 → F5 | Route | §5.1（规格明确双消费者） |
| 15 | `trajectory` | F5 → F6 | Trajectory | §5.1 |
| 16 | `actuator_cmd` | F6 →（E9 接口节点）→ F7 | ActuatorCmd | §5 F6/F7、§5.1、R-E-2；见 OI-8 |
| 17 | `warning` | F3 → E7 | Warning | §5.1、R-E-1 |
| 18 | `checked_cmd` | F7 → E8 | CheckedCmd | §5.1、R-E-1 |

## 3.3 存储读写连线

| 连线 | 方向 | 依据 |
|---|---|---|
| F1 ↔ D1 | read | §5.1 |
| F1 ↔ D2 | write | §5.1 |
| F1 ↔ D3 | write | §5.1 |
| F2 ↔ D1 | read | §5.1 |
| F3 ↔ D1 | read | §5.1 |
| F3 ↔ D4 | read | §5.1 |
| F4 ↔ D1 | read | §5.1 |
| F5 ↔ D1 | read | §5.1 |
| F5 ↔ D4 | read | §5.1 |
| F6 ↔ D3 | read | §5.1 |
| F7 ↔ D3 | read | §5.1 |
| F7 ↔ D4 | read | §5.1 |

> D2 在 Level 0 只有写入者 F1、没有读取者：§5.1 的 store-reads 清单未给 D2 分配读者，故不新增读取连线（OI-9）。

---

# 4. CDFD — Level 1（`AEB_Branch`，仅 F3 的 AEB 分支）

## 4.1 元素

- **Processes (3)：** F3.1 TTC Computation、F3.2 Risk Classification、F3.3 Maneuver Planning（R-L1-1）。
- **Data stores (2，均为被 F3 读取的全局存储)：** D1、D4。
- **External terminals / 边界端口：** E3 `driver_intent`(in)、E7 `warning`(out)，以及继承自 Level 0 的边界端口：`predicted_trajectories`(来自 F2)、`ego_state`(来自 F1/D3)、`route`(来自 F4)、`manoeuvre`(送往 F5)。D1/D4 已作为 store 声明，不再重复作为终端。

## 4.2 数据流连线

| # | 数据流 | 起点 → 终点 | 类型 | 依据 |
|---|---|---|---|---|
| 1 | `predicted_trajectories` | (F2 边界端口) → F3.1 | PredictedTrajectories | §6 F3.1 |
| 2 | `ego_state` | (F1/D3 边界端口) → F3.1 | EgoState | §6 F3.1 |
| 3 | `ttc_set` | F3.1 → F3.2 | TtcSet | §6 F3.2 |
| 4 | `risk_level` | F3.2 → F3.3 | String | §6 F3.3 |
| 5 | `warning` | F3.2 → E7 | Warning | §6 F3.2、R-E-1 |
| 6 | `ego_state` | (F1/D3 边界端口) → F3.3 | EgoState | §6 F3.3 |
| 7 | `driver_intent` | E3 → F3.3 | DriverIntent | §6 F3.3 |
| 8 | `route` | (F4 边界端口) → F3.3 | Route | §6 F3.3 |
| 9 | `manoeuvre` | F3.3 → (F5 边界端口) | Manoeuvre | §6 F3.3 |

## 4.3 存储读写连线

| 连线 | 方向 | 依据 |
|---|---|---|
| F3.2 ↔ D4 | read | §6 F3.2：“traffic rules (D4)” |
| F3.3 ↔ D1 | read | §6 F3.3：“D1” |

> Level 1 中 F3.1/F3.2/F3.3 均未写任何存储，符合 §5 F3 “shall not write any store”。

---

# 5. Open issues

| ID | 问题 | 本模型采取的处理 |
|---|---|---|
| OI-1 | （规格 §11.1）7 功能划分是否足够覆盖 L2 驾驶员监控/接管？ | 不新增功能；保持 F1–F7。 |
| OI-2 | （§11.2）D3 由 F1 写、F6/F7 读，所有权是否可接受？ | 按 §5.1 实现，未改所有权。 |
| OI-3 | （§11.3）规格只给阈值未给周期时间；紧急分支是否需要时序约束？ | 不引入时序元素。 |
| OI-4 | （§11.4）Level 1 是否应细化 F6/F7 而非 F3？ | 按 R-SCOPE-4/R-L1-1 细化 F3。 |
| OI-5 | D1 标注 owner F5/F1、D4 标注 owner F5 且“refreshed by E5/E6”，但 §5.1 的 store-writes 只有 F1 写 D2/D3；R-D-1 要求只有 owner 写。 | 按 §4 将 E5→D1、E6→D4 建为外部刷新连线；不为 D1/D4 虚构写入函数。此点与 R-D-1 的严格字面含义冲突，需规格方澄清。 |
| OI-6 | §5 将 ego state 列为 F3/F5 输入，但 §5.1 只给 F1→F2/F4 的 ego pose，且 F3/F5 未获授权读 D3（R-D-2）。 | 契约的 pre 仍列 `ego_state`（忠于 §5），CDFD 严格按 §5.1 不画该流；这是规格内部缺口，不是遗漏的建模元素。 |
| OI-7 | §5 F2 要求“derive the minimum TTC”，但 §5 F2 的输出只有 predicted trajectories，§5.1 也没有 TTC 流；§6 F3.1 又自行计算 TTC。 | F2 契约只约束 trajectories/horizon；min TTC 无独立输出，避免违反 R-G-5。F2 的 TTC 推导责任未在模型中落成流，需澄清。 |
| OI-8 | E9 在 §3 方向为 in，但 §5 F6 写“Output: actuator_cmd (E9)”；R-E-1 又禁止 E7/E8 之外的输出。 | 将 `actuator_cmd` 建成一条 F6→F7 的单一具名流，E9 作为该流上的外部接口节点（对 F7 而言为 in），不新增系统输出。方向语义需澄清。 |
| OI-9 | D2 在 §5.1 中只有 F1 写入，没有任何函数读取；F2 直接从 F1 拿 object table。 | 保留写入连线，不虚构读者。 |
| OI-10 | 用户给定类型系统禁止 `seq of`，但 D2/ObjectTable 要求“per-object id, position, velocity, class for every detected object”。 | 用 `object_count` + `records: String`（不透明编码）+ `lead_object` 表示；`records` 与所有 `valid: nat` 均为表示约定，不是新信号或阈值。 |
| OI-11 | N-5 的 `d_min`（Eq.(1) 未在规格中给出，仅有 A-2 参数集）和 N-6 的 ρ 期间 `a_max,accel` 未分配给任何函数。 | 不虚构距离/时间流；N-6 的制动下界通过 A-1/A-2 在 F3.3 体现，其余在矩阵中标为未闭合。 |
| OI-12 | N-7 要求横向加速度在车辆能力内，但 §7/§8 未给横向加速度数值（A-4 是 yaw-rate 的 sanity envelope）。 | F6/F7 只量化 A-6 的 ±1.0 归一化转向包络；N-7 的横向加速度数值约束保持定性。 |
| OI-13 | N-1 写“up to at least 130 km/h”，是能力下界而非速度上界。 | F3.3 以 `ego_state.speed <= 130` 作为已建模域的守卫；高于 130 km/h 的 AEB 行为留空。 |
| OI-14 | §6 F3.3：caution 必须产生非零减速，但同一条又允许“其他风险级别的加速请求优先”。 | 并行给出两条 post：默认 caution 减速；若 `override_accelerate=1` 则按请求提高 `target_speed`。两 clause 的冲突需澄清。 |
| OI-15 | §8 A-5 引用了 `R-F2-1`，但全文没有定义该条款。 | 按 A-5 自身给出的 3.0 s/1.5 s 取值建模，不补造条款。 |
| OI-16 | 规格未统一单位（N-1/N-4 用 km/h，A-1/A-2/A-3 用 m/s²）。 | 约定 speed 用 km/h、加速度用 m/s²；未在模型中做单位换算。 |
| OI-17 | `brake` 命令与纵向加速度命令的关系、brake 的数值包络未在 §7/§8 给出。 | F6/F7 只给 `brake >= 0` 良构性约束，不设阈值。 |

---

# 6. 可追溯性矩阵

## 6.1 R-xx 条款 → 模型元素

| 条款 | 模型元素 |
|---|---|
| R-SCOPE-1 | 两个 module 的系统边界；F3_3 的 emergency deceleration 契约 |
| R-SCOPE-2 | Level 0 的 E1–E9 外部终端；无内部感知/执行器元素 |
| R-SCOPE-3 | F1/F2/F4/F5/F6/F7 为原子 process，契约只约束功能与数据流 |
| R-SCOPE-4 | `ADAS_System` + `AEB_Branch` 两个 module；仅 F3 被细化 |
| R-E-1 | Module head 出端口仅 `warning`(E7)/`checked_cmd`(E8)；CDFD 中仅 17/18 号出流 |
| R-E-2 | F7 契约；CDFD 流 16（F6 → E9 → F7）与流 18（F7 → E8） |
| R-D-1 | `ext wr` 仅出现在 F1（D2/D3）；D1/D4 无函数写入（OI-5） |
| R-D-2 | §3.3 的 12 条读/写连线与 §5.1 逐条一致 |
| R-L0-1 | §3.1 元素清单：7 processes / 4 stores / 9 external terminals |
| R-L1-1 | §4.1 元素清单：F3.1、F3.2、F3.3 |
| R-G-1 | §1.3 与 §2.3 全部 process 的 pre/post；量化约束见 §6.2 |
| R-G-2 | 本矩阵 |
| R-G-3 | §5 open issues 登记所有表示约定（OI-10/OI-16 等） |
| R-G-4 | §3.2、§4.2 的具名有向流清单；共享流仅 F2→F3/F5 与 F4→F3/F5（§5.1 明确允许） |
| R-G-5 | 每个生产者的消费者均按 §5.1/§6；F2 的 min TTC 无消费者故不产流（OI-7） |
| R-G-6 | 各契约 pre 中的 `.valid = 1` / `.object_count >= 0` 守卫；post 读取字段前均有 valid/count 守卫 |
| §5 F1 | F1 process；流 1/2/7/8/9；D1 rd、D2/D3 wr |
| §5 F2 | F2 process；流 7/8/10/11；D1 rd；A-7 约束 |
| §5 F3 | F3 process；流 3/10/13/17；D1/D4 rd |
| §5 F4 | F4 process；流 4/9/13/14；D1 rd |
| §5 F5 | F5 process；流 11/12/14/15；D1/D4 rd |
| §5 F6 | F6 process；流 15/16；D3 rd；A-3/A-6 |
| §5 F7 | F7 process；流 16/18；D3/D4 rd；A-3/A-6 |
| §5.1 | §3.2 全部 18 条流 + §3.3 全部读写连线 |
| §6 F3.1 / F3.2 / F3.3 | `AEB_Branch` 的三个 process 与 §4.2/§4.3 连线 |
| §11.1–11.4 | OI-1 – OI-4 |

## 6.2 N/A 阈值 → 契约中的约束

| 阈值 | 取值来源 | 落点 |
|---|---|---|
| N-1 | §7 | F3_3：`speed <= 130` 守卫下的 emergency deceleration（OI-13） |
| N-2 | §7 | F3_2：caution（1.5 < TTC <= 3.0）与 critical（TTC <= 1.5）均 `warning.active = 1`，覆盖 TTC=2.0 之前发出警告 |
| N-3 | §7 | 由 A-1 落实：F3_3 `required_deceleration >= 6.0` |
| N-4 | §7 | A-1 的推导依据；间接落在 F3_3 的 6.0 约束上 |
| N-5 | §7 | 未闭合：`d_min` 数值 Eq.(1) 与责任函数均未给出（OI-11） |
| N-6 | §7 | F3_3 `required_deceleration >= 6.0` 满足 A-2 的 `a_min,brake = 4.0`；ρ 期间 `a_max,accel` 未闭合（OI-11） |
| N-7 | §7 | F6/F7 的 `steering` 包络 ±1.0（A-6）；横向加速度数值未给（OI-12） |
| A-1 | §8 | F3_3 critical：`required_deceleration >= 6.0` |
| A-2 | §8 | F3_3：`a_min,brake = 4.0` 由 6.0 覆盖；其余参数见 OI-11 |
| A-3 | §8 | F6/F7：`longitudinal_accel <= 3.0` |
| A-4 | §8 | F1：`yaw_rate <= 3.5 and yaw_rate >= -3.5` |
| A-5 | §8 | F3_2：3.0 s / 1.5 s 三档风险边界（关联条款 R-F2-1 缺失，OI-15） |
| A-6 | §8 | F6/F7：`steering <= 1.0 and steering >= -1.0` |
| A-7 | §8 | F2：`horizon >= 3.0` |
