# NL-RQ-ADAS-v1 — SOFL 形式化规格（模型：Tencent Hunyuan Hy-3）

> 唯一输入：`NL-RQ-ADAS-v1_spec.md`（v1.0）。只建模规格写明的内容；未写明的设计决定登记在 §5 open issues。
> 建模范围：Level 0 整车级 `ADAS_System` + Level 1 仅 F3 的 AEB 分支 `AEB_Branch`。
> 本版新增约束（相对前两次重跑）：**不写 `x <> null` 一类前置条件**。SOFL 中值按类型声明默认非空，此类检查是同义反复；本文所有 pre 只陈述真实约束——有效性标志、范围条件、规格阈值或已声明的域守卫。

## 0. 记号与表示约定（建模约定，均登记于 open issues）

- 模块头：`( 入1: 类型 | 入2: 类型 ) 出1: 类型 | 出2: 类型, 出2b: 类型`；`|` 分端口，`,` 分同端口多条流。
- 过程：`process 名(入参) out: 出参` + `ext rd/wr` + `pre` + 一条或多条 `post if <守卫> then <谓词>` + `end_process`。多条 `post if` 按**合取**理解。
- 可用算子仅 `and`、`=`、`<>`、`>`、`>=`、`<=`、`<` 与点号字段访问；不使用 `or`、`not`、`=>`、量词、`seq of`。
- nat 字段作 0/1 标志时：1 = 有效/是/激活，0 = 无效/否/未激活（O-14）。
- 类型均按 SOFL 默认非空解释；因此 pre/post 中**不出现** `null` 检查或 `x = x` 式自等式。
- 速度用 km/h，距离用 m，加速度用 m/s²，时间用 s；规格未统一单位，此约定见 O-12。
- 禁止 `seq of` 下，逐对象集合以聚合字段 + 计数表示（`object_count` / `trajectory_count`），见 O-13。
- 字符串枚举取值取自规格措辞；规格未定值的写法列于 O-15。

---

# 1. Module `ADAS_System`（Level 0）

## 1.1 完整类型声明（两个 module 共用，均须包含）

```
RawSensorData = composed of
  camera_valid: nat,
  radar_valid: nat,
  lidar_valid: nat,
  frame_timestamp: real
end

GnssImu = composed of
  pos_x: real,
  pos_y: real,
  heading: real,
  yaw_rate: real,
  acceleration: real,
  gnss_valid: nat,
  imu_valid: nat,
  timestamp: real
end

DriverIntent = composed of
  requested_cruise_speed: real,
  override_accelerate: nat,
  override_brake: nat,
  override_steer: nat,
  driver_attention: nat
end

Destination = composed of
  longitude: real,
  latitude: real,
  route_preferences: String
end

MapSegment = composed of
  road_id: String,
  lane_id: String,
  posted_speed_limit: real,
  curvature: real,
  lane_topology: String
end

TrafficRules = composed of
  posted_speed_limit: real,
  traffic_signal_state: String
end

Warning = composed of
  warning_type: String,
  active: nat
end

Actuation = composed of
  longitudinal_accel: real,
  brake: real,
  steering: real
end

EgoState = composed of
  pose_x: real,
  pose_y: real,
  speed: real,
  yaw_rate: real,
  acceleration: real,
  timestamp: real
end

EgoPose = composed of
  pose_x: real,
  pose_y: real
end

ObjectRecord = composed of
  object_id: String,
  pos_x: real,
  pos_y: real,
  velocity: real,
  object_class: String
end

ObjectTable = composed of
  object_count: nat,
  records: ObjectRecord,
  lead_object: ObjectRecord
end

PredictedTrajectory = composed of
  object_id: String,
  horizon: real,
  ttc: real,
  longitudinal_distance: real,
  rss_min_distance: real
end

PredictedTrajectories = composed of
  trajectory_count: nat,
  horizon: real,
  trajectories: PredictedTrajectory,
  minimum_ttc: real
end

Maneuver = composed of
  maneuver_type: String,
  target_speed: real,
  target_lane: String,
  required_deceleration: real
end

Route = composed of
  path_length: real,
  eta: real,
  lane_geometry: String
end

Trajectory = composed of
  max_speed: real,
  max_accel: real,
  horizon: real,
  required_deceleration: real
end

TtcSet = composed of
  object_count: nat,
  minimum_ttc: real
end
```

字段溯源：E1 → `RawSensorData`（§3：逐传感器 validity flags + timestamps）；E2 → `GnssImu`（§3：GNSS position/heading、IMU angular rate/acceleration + validity flags）；E3 → `DriverIntent`（§3：requested cruise speed、override accel/brake/steer、driver-attention）；E4 → `Destination`；E5/D1 → `MapSegment`（§3/§4：road/lane id、posted speed limit、curvature、lane topology）；E6/D4 → `TrafficRules`；E7 → `Warning`（§3：warning type + active flag）；E8/E9 → `Actuation`（§3：longitudinal acceleration、brake、steering）；D3 → `EgoState`；D2 → `ObjectTable`/`ObjectRecord`（§4：object count、per-object id/position/velocity/class、lead object + kinematics）；F2 → `PredictedTrajectories`/`PredictedTrajectory`（§5 F2：horizon、minimum TTC；`rss_min_distance` 对应 N-5 的 `d_min`，见 O-8）；F3 → `Maneuver`；F4 → `Route`；F5 → `Trajectory`；F3.1 → `TtcSet`。

## 1.2 Module head

```
module ADAS_System
( raw_sensor_data: RawSensorData | gnss_imu: GnssImu | driver_intent: DriverIntent | destination: Destination | map_data: MapSegment | traffic_rules: TrafficRules | actuator_cmd: Actuation ) warning: Warning | checked_cmd: Actuation

store hd_map_store: MapSegment
store object_track_store: ObjectTable
store ego_state_store: EgoState
store traffic_rules_store: TrafficRules
```

端口 = E1 `raw_sensor_data`、E2 `gnss_imu`、E3 `driver_intent`、E4 `destination`、E5 `map_data`、E6 `traffic_rules`、E9 `actuator_cmd`（入）；E7 `warning`、E8 `checked_cmd`（出）。系统输出仅 E7/E8（R-E-1）。存储严格为 D1–D4（R-L0-1）。

## 1.3 Process contracts（F1–F7）

```
process F1_Perception(raw_sensor_data, gnss_imu) out: object_table, ego_state, ego_pose
ext rd hd_map_store
ext wr object_track_store
ext wr ego_state_store
pre raw_sensor_data.camera_valid = 1 and raw_sensor_data.radar_valid = 1 and raw_sensor_data.lidar_valid = 1 and raw_sensor_data.frame_timestamp >= 0 and gnss_imu.gnss_valid = 1 and gnss_imu.imu_valid = 1 and gnss_imu.timestamp >= 0
post if raw_sensor_data.camera_valid = 1 and raw_sensor_data.radar_valid = 1 then object_table.object_count >= 0
post if object_table.object_count > 0 then object_table.lead_object.object_id <> ""
post if gnss_imu.gnss_valid = 1 then ego_state.speed >= 0
post if gnss_imu.imu_valid = 1 then ego_state.yaw_rate <= 3.5
post if gnss_imu.imu_valid = 1 then ego_state.yaw_rate >= -3.5
post if gnss_imu.gnss_valid = 1 then ego_pose.pose_x = ego_state.pose_x
post if gnss_imu.gnss_valid = 1 then ego_pose.pose_y = ego_state.pose_y
post if object_table.object_count >= 0 then object_track_store.object_count = object_table.object_count
post if ego_state.speed >= 0 then ego_state_store.timestamp = ego_state.timestamp
end_process

process F2_Prediction(object_table, ego_pose) out: predicted_trajectories
ext rd hd_map_store
pre object_table.object_count >= 0 and hd_map_store.road_id <> "" and hd_map_store.posted_speed_limit > 0
post if object_table.object_count = 0 then predicted_trajectories.trajectory_count = 0
post if object_table.object_count > 0 then predicted_trajectories.trajectory_count = object_table.object_count
post if object_table.object_count > 0 then predicted_trajectories.horizon >= 3.0
post if object_table.object_count > 0 then predicted_trajectories.minimum_ttc >= 0
post if object_table.object_count > 0 then predicted_trajectories.trajectories.longitudinal_distance >= predicted_trajectories.trajectories.rss_min_distance
end_process

process F3_Planning(ego_state, driver_intent, route, predicted_trajectories) out: maneuver, warning
ext rd hd_map_store
ext rd traffic_rules_store
pre ego_state.speed >= 0 and traffic_rules_store.posted_speed_limit > 0 and predicted_trajectories.trajectory_count >= 0 and route.path_length > 0 and hd_map_store.lane_id <> ""
post if predicted_trajectories.minimum_ttc > 3.0 then warning.active = 0
post if predicted_trajectories.minimum_ttc > 3.0 then warning.warning_type = "none"
post if predicted_trajectories.minimum_ttc > 3.0 then maneuver.maneuver_type = "cruise_keep_lane"
post if predicted_trajectories.minimum_ttc <= 3.0 and predicted_trajectories.minimum_ttc > 1.5 then warning.active = 1
post if predicted_trajectories.minimum_ttc <= 3.0 and predicted_trajectories.minimum_ttc > 1.5 then warning.warning_type = "caution"
post if predicted_trajectories.minimum_ttc <= 3.0 and predicted_trajectories.minimum_ttc > 1.5 then maneuver.required_deceleration > 0
post if predicted_trajectories.minimum_ttc <= 1.5 then warning.active = 1
post if predicted_trajectories.minimum_ttc <= 1.5 then warning.warning_type = "imminent_collision"
post if predicted_trajectories.minimum_ttc <= 1.5 then maneuver.maneuver_type = "emergency_deceleration"
post if predicted_trajectories.minimum_ttc <= 1.5 then maneuver.target_speed = 0
post if predicted_trajectories.minimum_ttc <= 1.5 then maneuver.required_deceleration >= 6.0
post if predicted_trajectories.minimum_ttc <= 2.0 then warning.active = 1
post if driver_intent.override_accelerate = 1 and predicted_trajectories.minimum_ttc > 1.5 then maneuver.maneuver_type = "cruise_keep_lane"
post if driver_intent.override_accelerate = 1 and predicted_trajectories.minimum_ttc <= 1.5 then maneuver.required_deceleration >= 6.0
post if maneuver.maneuver_type = "emergency_deceleration" then maneuver.target_lane = hd_map_store.lane_id
end_process

process F4_Route(destination, ego_pose) out: route
ext rd hd_map_store
pre destination.latitude >= -90 and destination.latitude <= 90 and destination.longitude >= -180 and destination.longitude <= 180 and hd_map_store.road_id <> ""
post if destination.latitude >= -90 then route.path_length > 0
post if route.path_length > 0 then route.eta > 0
post if hd_map_store.road_id <> "" then route.lane_geometry = hd_map_store.lane_topology
end_process

process F5_Motion(maneuver, route, ego_state, predicted_trajectories) out: trajectory
ext rd hd_map_store
ext rd traffic_rules_store
pre maneuver.required_deceleration >= 0 and route.path_length > 0 and ego_state.speed >= 0 and traffic_rules_store.posted_speed_limit > 0
post if traffic_rules_store.posted_speed_limit > 0 then trajectory.max_speed <= traffic_rules_store.posted_speed_limit
post if maneuver.maneuver_type = "emergency_deceleration" then trajectory.required_deceleration >= 6.0
post if maneuver.maneuver_type = "lane_keeping_with_deceleration" then maneuver.required_deceleration > 0
post if maneuver.required_deceleration >= 0 then trajectory.required_deceleration >= maneuver.required_deceleration
post if traffic_rules_store.posted_speed_limit > 0 then trajectory.max_accel <= 2.0
post if predicted_trajectories.trajectory_count >= 0 then trajectory.horizon > 0
post if maneuver.required_deceleration >= 0 then trajectory.max_speed >= 0
end_process

process F6_Control(trajectory) out: actuator_cmd
ext rd ego_state_store
pre trajectory.horizon > 0 and trajectory.max_speed >= 0 and ego_state_store.timestamp >= 0
post if trajectory.required_deceleration >= 4.0 then actuator_cmd.brake >= 4.0
post if trajectory.horizon > 0 then actuator_cmd.longitudinal_accel <= 3.0
post if trajectory.horizon > 0 then actuator_cmd.steering <= 1.0
post if trajectory.horizon > 0 then actuator_cmd.steering >= -1.0
end_process

process F7_Safety_Shield(actuator_cmd) out: checked_cmd
ext rd ego_state_store
ext rd traffic_rules_store
pre actuator_cmd.brake >= 0 and ego_state_store.timestamp >= 0 and traffic_rules_store.posted_speed_limit > 0
post if actuator_cmd.steering >= -1.0 and actuator_cmd.steering <= 1.0 then checked_cmd.steering = actuator_cmd.steering
post if actuator_cmd.steering > 1.0 then checked_cmd.steering = 1.0
post if actuator_cmd.steering < -1.0 then checked_cmd.steering = -1.0
post if traffic_rules_store.posted_speed_limit > 0 then checked_cmd.longitudinal_accel <= 3.0
post if actuator_cmd.brake >= 4.0 then checked_cmd.brake >= 4.0
post if actuator_cmd.brake >= 0 then checked_cmd.brake >= 0
end_process
```

Pre 说明（均为真实约束，无空检查）：F1 用 E1/E2 自带 validity flags 与时间戳非负；F2/F4 用地图 road id 非空与 speed limit 为正；F3 用速度非负、速度限制为正、计数非负、路径长度为正与 lane id 非空；F5 用减速需求非负、路径/限速为正；F6 用轨迹 horizon 为正；F7 用 brake 非负（F7 必须能处理 F6 越界的 steering，故 pre **不**限制 steering 在包线内）。

---

# 2. Module `AEB_Branch`（Level 1，仅 F3 的 AEB 分支）

## 2.1 Module head

```
module AEB_Branch
( predicted_trajectories: PredictedTrajectories | ego_state: EgoState | driver_intent: DriverIntent | route: Route ) warning: Warning | maneuver: Maneuver

store hd_map_store: MapSegment
store traffic_rules_store: TrafficRules
```

D1/D4 作为被 F3 读取的全局存储进入子模块；子模块不写任何存储（§5 F3 “shall not write any store”）。

## 2.2 Process contracts（F3.1 → F3.2 → F3.3）

```
process F3_1_TTC(predicted_trajectories, ego_state) out: ttc_set
pre predicted_trajectories.trajectory_count >= 0 and predicted_trajectories.horizon >= 3.0 and ego_state.timestamp >= 0
post if predicted_trajectories.trajectory_count = 0 then ttc_set.object_count = 0
post if predicted_trajectories.trajectory_count > 0 then ttc_set.object_count = predicted_trajectories.trajectory_count
post if predicted_trajectories.trajectory_count > 0 then ttc_set.minimum_ttc = predicted_trajectories.minimum_ttc
post if predicted_trajectories.trajectory_count > 0 then ttc_set.minimum_ttc >= 0
end_process

process F3_2_Risk(ttc_set) out: risk, warning
ext rd traffic_rules_store
pre ttc_set.object_count >= 0 and traffic_rules_store.posted_speed_limit > 0
post if ttc_set.object_count = 0 then risk = "no risk"
post if ttc_set.object_count = 0 then warning.active = 0
post if ttc_set.object_count = 0 then warning.warning_type = "none"
post if ttc_set.minimum_ttc > 3.0 then risk = "no risk"
post if ttc_set.minimum_ttc > 3.0 then warning.active = 0
post if ttc_set.minimum_ttc > 3.0 then warning.warning_type = "none"
post if ttc_set.minimum_ttc <= 3.0 and ttc_set.minimum_ttc > 1.5 then risk = "caution"
post if ttc_set.minimum_ttc <= 3.0 and ttc_set.minimum_ttc > 1.5 then warning.active = 1
post if ttc_set.minimum_ttc <= 3.0 and ttc_set.minimum_ttc > 1.5 then warning.warning_type = "caution"
post if ttc_set.minimum_ttc <= 1.5 then risk = "critical"
post if ttc_set.minimum_ttc <= 1.5 then warning.active = 1
post if ttc_set.minimum_ttc <= 1.5 then warning.warning_type = "imminent_collision"
post if ttc_set.minimum_ttc <= 2.0 then warning.active = 1
end_process

process F3_3_Maneuver(risk, ego_state, driver_intent, route) out: maneuver
ext rd hd_map_store
pre risk <> "" and ego_state.speed >= 0 and driver_intent.requested_cruise_speed >= 0 and route.path_length > 0 and hd_map_store.lane_id <> ""
post if risk = "no risk" then maneuver.maneuver_type = "cruise_keep_lane"
post if risk = "no risk" then maneuver.required_deceleration = 0
post if risk = "caution" then maneuver.maneuver_type = "deceleration"
post if risk = "caution" then maneuver.required_deceleration > 0
post if risk = "critical" then maneuver.maneuver_type = "emergency_deceleration"
post if risk = "critical" then maneuver.target_speed = 0
post if risk = "critical" then maneuver.required_deceleration >= 6.0
post if risk = "critical" and driver_intent.override_accelerate = 1 then maneuver.required_deceleration >= 6.0
post if risk = "critical" and ego_state.speed <= 130 then maneuver.required_deceleration >= 6.0
post if risk = "no risk" and driver_intent.override_accelerate = 1 then maneuver.target_speed >= driver_intent.requested_cruise_speed
post if risk = "caution" and driver_intent.override_accelerate = 1 then maneuver.target_speed >= driver_intent.requested_cruise_speed
post if maneuver.maneuver_type = "cruise_keep_lane" then maneuver.target_lane = hd_map_store.lane_id
end_process
```

---

# 3. CDFD 元素与连线清单

## 3.1 Level 0 — `ADAS_System`（恰好 7 process / 4 store / 9 外部终端，R-L0-1）

**Processes（7）**：`F1_Perception`、`F2_Prediction`、`F3_Planning`、`F4_Route`、`F5_Motion`、`F6_Control`、`F7_Safety_Shield`。

**Data stores（4）**：D1 `hd_map_store`: MapSegment、D2 `object_track_store`: ObjectTable、D3 `ego_state_store`: EgoState、D4 `traffic_rules_store`: TrafficRules。

**External terminals（9）**：E1 `raw_sensor_data`(in)、E2 `gnss_imu`(in)、E3 `driver_intent`(in)、E4 `destination`(in)、E5 `map_data`(in)、E6 `traffic_rules`(in)、E7 `warning`(out)、E8 `checked_cmd`(out)、E9 `actuator_cmd`(in)。

**数据流连线（全部具名、有向、单生产者/单消费者）**

| # | 数据流 | 起点 → 终点 | 类型 | 依据 |
|---|---|---|---|---|
| 1 | `raw_sensor_data` | E1 → F1 | RawSensorData | §3 E1、§5 F1 |
| 2 | `gnss_imu` | E2 → F1 | GnssImu | §3 E2、§5 F1 |
| 3 | `driver_intent` | E3 → F3 | DriverIntent | §5 F3 |
| 4 | `destination` | E4 → F4 | Destination | §5 F4 |
| 5 | `map_data` | E5 → D1（外部刷新） | MapSegment | §4 D1“refreshed by E5”，见 O-2 |
| 6 | `traffic_rules` | E6 → D4（外部刷新） | TrafficRules | §4 D4“refreshed by E6”，见 O-2 |
| 7 | `ego_pose` | F1 → F2 | EgoPose | §5.1 |
| 8 | `object_table` | F1 → F2 | ObjectTable | §5.1 |
| 9 | `ego_pose` | F1 → F4 | EgoPose | §5.1 |
| 10 | `ego_state` | F1 → F3 | EgoState | §5 F3 输入条款，见 O-4 |
| 11 | `ego_state` | F1 → F5 | EgoState | §5 F5 输入条款，见 O-4 |
| 12 | `predicted_trajectories` | F2 → F3 | PredictedTrajectories | §5.1 |
| 13 | `predicted_trajectories` | F2 → F5 | PredictedTrajectories | §5.1（规格明确双消费者） |
| 14 | `manoeuvre` | F3 → F5 | Maneuver | §5.1 |
| 15 | `route` | F4 → F3 | Route | §5.1 |
| 16 | `route` | F4 → F5 | Route | §5.1（规格明确双消费者；`route` 同供 F3/F5） |
| 17 | `trajectory` | F5 → F6 | Trajectory | §5.1 |
| 18 | `actuator_cmd` | F6 → F7（E9 为该流上的外部接口节点） | Actuation | §5 F6/F7、§5.1、R-E-2，见 O-1 |
| 19 | `warning` | F3 → E7 | Warning | §5.1、R-E-1 |
| 20 | `checked_cmd` | F7 → E8 | Actuation | §5.1、R-E-1 |

**存储读写连线（与 process 的 `ext rd/wr` 逐条一致）**

| 连线 | 方向 | 依据 |
|---|---|---|
| F1 ↔ D1 | read (`ext rd hd_map_store`) | §5.1 |
| F1 → D2 | write (`ext wr object_track_store`) | §5.1 |
| F1 → D3 | write (`ext wr ego_state_store`) | §5.1 |
| F2 ↔ D1 | read | §5.1 |
| F3 ↔ D1 | read | §5.1 |
| F3 ↔ D4 | read | §5.1 |
| F4 ↔ D1 | read | §5.1 |
| F5 ↔ D1 | read | §5.1 |
| F5 ↔ D4 | read | §5.1 |
| F6 ↔ D3 | read | §5.1 |
| F7 ↔ D3 | read | §5.1 |
| F7 ↔ D4 | read | §5.1 |

> D2 只有 F1 写入、§5.1 未分配读者；按 R-G-5 不虚构读者（O-3）。F2/F4 的双消费者流按 §5.1 明确允许画成两条同名有向流，各自单生产者/单消费者（R-G-4）。

## 3.2 Level 1 — `AEB_Branch`（恰好 F3.1 → F3.2 → F3.3，R-L1-1）

**元素**：process F3.1 `F3_1_TTC`、F3.2 `F3_2_Risk`、F3.3 `F3_3_Maneuver`；store D1 `hd_map_store`、D4 `traffic_rules_store`（只读）；外部终端 E3 `driver_intent`(in)、E7 `warning`(out)；边界继承端口：`predicted_trajectories`（来自 F2）、`ego_state`（来自 F1）、`route`（来自 F4）、`manoeuvre`（送往 F5）。不新增外部终端。

| # | 数据流 | 起点 → 终点 | 类型 | 依据 |
|---|---|---|---|---|
| 1 | `predicted_trajectories` | (F2 边界端口) → F3.1 | PredictedTrajectories | §6 F3.1 |
| 2 | `ego_state` | (F1 边界端口) → F3.1 | EgoState | §6 F3.1 |
| 3 | `ttc_set` | F3.1 → F3.2 | TtcSet | §6 F3.2 |
| 4 | `risk` | F3.2 → F3.3 | String | §6 F3.3 |
| 5 | `warning` | F3.2 → E7 | Warning | §6 F3.2、R-E-1 |
| 6 | `ego_state` | (F1 边界端口) → F3.3 | EgoState | §6 F3.3 |
| 7 | `driver_intent` | E3 → F3.3 | DriverIntent | §6 F3.3 |
| 8 | `route` | (F4 边界端口) → F3.3 | Route | §6 F3.3 |
| 9 | `manoeuvre` | F3.3 → (F5 边界端口) | Maneuver | §6 F3.3 |

**存储读写连线**

| 连线 | 方向 | 依据 |
|---|---|---|
| F3.2 ↔ D4 | read (`ext rd traffic_rules_store`) | §6 F3.2 “traffic rules (D4)” |
| F3.3 ↔ D1 | read (`ext rd hd_map_store`) | §6 F3.3 “D1” |

Level 1 无任何 `ext wr`，与 §5 F3 “shall not write any store” 一致。

---

# 4. 可追溯性说明

## 4.1 R-xx 条款 → 模型元素

| 条款 | 对应元素 |
|---|---|
| R-SCOPE-1 | 两 module 边界；SAE L2 语义由 E3 `driver_attention` + F3_3 的 override 处理表达 |
| R-SCOPE-2 | Level 0 的 E1–E9 仅为外部终端；无内部传感器/执行器元素 |
| R-SCOPE-3 | F1/F2/F4/F5/F6/F7 为原子 process，契约只约束功能与命名数据流，不含算法内部 |
| R-SCOPE-4 | `ADAS_System` + `AEB_Branch` 两个 module；仅 F3 细化 |
| R-E-1 | 两 module 出端口仅 `warning`(E7)/`checked_cmd`(E8)；Level 0 流 19/20、Level 1 流 5 |
| R-E-2 | F7 契约；Level 0 流 18（F6 → E9 → F7）与流 20（F7 → E8） |
| R-D-1 | `ext wr` 仅出现在 F1（D2/D3）；D1/D4 的外部刷新见 O-2 |
| R-D-2 | §3.1 存储读写 12 连线与 §5.1 读/写清单逐条一致；无未授权读取 |
| R-L0-1 | §3.1 元素清单：恰好 7 process / 4 store / 9 external terminal |
| R-L1-1 | §3.2 元素清单：F3.1/F3.2/F3.3 及三条内部流 |
| R-G-1 | §1.3 与 §2.2 全部 process 的 pre + post；无 §7/§8 阈值者（F4/F3.1）给定性/范围 post |
| R-G-2 | 本 §4 矩阵 |
| R-G-3 | §5 open issues 登记所有建模便利项（O-1…O-16） |
| R-G-4 | §3.1/§3.2 具名有向流；共享流仅 F2→F3/F5 与 F4→F3/F5（§5.1 明确允许） |
| R-G-5 | 每个生产者均有 §5.1/§6 指定的消费者；D2 只读者空缺见 O-3 |
| R-G-6 | 按本次新增约束，SOFL 值默认非空，故不以 `x <> null` 守卫；pre 改用有效性标志/范围条件/阈值，post 守卫用真实条件（如 `object_count > 0`、`minimum_ttc <= 1.5`） |
| §5 F1 | F1 process；流 1/2/7/8/9/10/11；D1 rd、D2/D3 wr；A-4 约束 |
| §5 F2 | F2 process；流 7/8/12/13；D1 rd；A-7、N-5 约束 |
| §5 F3 | F3 process；流 3/12/14/15/19；D1/D4 rd；A-1/A-5、N-1/N-2 |
| §5 F4 | F4 process；流 4/9/15/16；D1 rd；定性 post |
| §5 F5 | F5 process；流 11/13/14/16/17；D1/D4 rd；A-2/A-7 |
| §5 F6 | F6 process；流 17/18；D3 rd；A-3/A-6 |
| §5 F7 | F7 process；流 18/20；D3/D4 rd；A-3/A-6、N-7 |
| §5.1 | §3.1 全部 20 条流 + 12 条读写连线 |
| §6 F3.1 / F3.2 / F3.3 | §2.2 三个 process + §3.2 连线 |
| R-F2-1（§8 A-5 引用但未定义） | 理解为 F2 horizon ≥ 3.0（A-7），见 O-5 |
| §11.1–11.4 | O-16 中逐条回答 |

## 4.2 N / A 阈值 → 契约落点

| 阈值 | 来源 | 落点 |
|---|---|---|
| N-1（130 km/h） | §7 | F3_3：`risk = "critical" and ego_state.speed <= 130` 守卫下的 emergency deceleration；130 以上留空（O-9） |
| N-2（TTC > 1.5 s 才计入 FCW；不晚于 2.0 s 预警） | §7 | F3 与 F3_2：`minimum_ttc <= 2.0 → warning.active = 1`；1.5 s 为 critical 边界（A-5） |
| N-3（> 30 km/h 降速） | §7 | 经 A-1 推导：F3/F3_3/F5 的 `required_deceleration >= 6.0` |
| N-4（CCRm/CCRb 包线） | §7 | A-1 的推导依据，间接落在 `>= 6.0` |
| N-5（RSS `d_min`） | §7 | F2：`trajectories.longitudinal_distance >= trajectories.rss_min_distance`；公式缺失见 O-8 |
| N-6（RSS 制动剖面） | §7 | F5 `max_accel <= 2.0`、F6/F7 `brake >= 4.0`（A-2）；ρ 期间时间限定未闭合（O-11） |
| N-7（横向加速度包络） | §7 | F6/F7 的 `steering` ±1.0（A-6）与 F7 保向约束；数值横向加速度未给（O-10） |
| A-1（6.0 m/s²） | §8 | F3、F3_3、F5 的 `required_deceleration >= 6.0` |
| A-2（ρ=0.1, accel=2.0, brake=4.0, min_brake=4.0） | §8 | F5 `max_accel <= 2.0`；F6/F7 `brake >= 4.0`；`d_min` 参数集见 O-8 |
| A-3（3.0 m/s²） | §8 | F6/F7 `longitudinal_accel <= 3.0` |
| A-4（3.5 rad/s yaw-rate） | §8 | F1 `yaw_rate <= 3.5 and yaw_rate >= -3.5` |
| A-5（3.0 s / 1.5 s） | §8 | F3 与 F3_2 三档风险边界（关联条款 R-F2-1 缺失，O-5） |
| A-6（±1.0 转向） | §8 | F6/F7 `steering <= 1.0 / >= -1.0`，F7 保向 |
| A-7（3.0 s 预测时域） | §8 | F2 `horizon >= 3.0`、F3.1 pre `horizon >= 3.0` |

---

# 5. Open issues（建模决定与规格缺口）

| ID | 问题 | 本模型处理 |
|---|---|---|
| O-1 | §3 中 E9 方向为 in，但 §5 F6 写 “Output: actuator_cmd (E9)”，且 R-E-1 禁止 E7/E8 之外的输出。 | 将 `actuator_cmd` 建成 F6→F7 单一具名流，E9 作为该流上的外部接口节点（对 F7 为 in），不新增系统输出。方向语义待规格方澄清。 |
| O-2 | §4 称 D1/D4 由 E5/E6 刷新，但 §5.1 的 store-writes 只有 F1 写 D2/D3；R-D-1 要求只有 owner 写。 | 按 §4 建 E5→D1、E6→D4 外部刷新连线，不为 D1/D4 虚构写入函数；与 R-D-1 字面含义的冲突待澄清。 |
| O-3 | D2 在 §5.1 只有 F1 写入、无读者；F2 直接从 F1 取 object table。 | 保留写入连线，不虚构读者。 |
| O-4 | §5 将 ego state 列为 F3/F5 输入，但 §5.1 只给 F1→F2/F4 的 ego pose，且 F3/F5 未获授权读 D3（R-D-2）。 | 为消除隐式依赖，补 F1→F3、F1→F5 的 `ego_state` 流（流 10/11）；这是规格内部缺口，非新增信号。 |
| O-5 | §8 A-5 引用了全文未定义的 `R-F2-1`。 | 按 A-5 自身给出的 3.0 s/1.5 s 取值建模，并将 R-F2-1 理解为 F2 时域 ≥ 3.0 s；不补造条款。 |
| O-6 | §5 F2 “shall be the only function that computes TTC”，而 §6 F3.1 “shall compute TTC”。 | F2 在 `PredictedTrajectories` 中给出逐对象 `ttc` 与 `minimum_ttc`；F3.1 仅形成 TTC 集合并取最小值/计数，不重新计算逐对象 TTC。 |
| O-7 | 对象数为 0 时 `minimum_ttc` 取值未定义。 | 建模决定：count = 0 时 TTC 集合计数为 0、风险为 no risk；哨兵值待定。 |
| O-8 | N-5 的 `d_min`（RSS Eq.(1)）未在规格中给出公式，仅有 A-2 参数集。 | 以 `PredictedTrajectory.rss_min_distance` 字段承载该符号，不赋予数值；公式需集成方提供。 |
| O-9 | N-1 的 “up to at least 130 km/h” 是能力下界，不是速度上界。 | 以 `ego_state.speed <= 130` 作为已建模域的守卫；高于 130 km/h 的 AEB 行为留空。 |
| O-10 | N-7 要求横向加速度在车辆能力内，但 §7/§8 无横向加速度数值（A-4 是 yaw-rate 包络）。 | F6/F7 只量化 A-6 的 ±1.0 归一化转向包络；N-7 保持定性，数值阈值待补。 |
| O-11 | A-2 的 `a_max,accel = 2.0` 限定在响应时间 ρ 内，但规格无任何时间/周期模型。 | 作为无时间限定的上界写入 F5 `max_accel <= 2.0`；时间限定无法表达。 |
| O-12 | 规格未统一单位（N-1/N-4 用 km/h，A-1/A-2/A-3 用 m/s²）。 | 约定 speed/max_speed 为 km/h、加速度为 m/s²；模型内不做单位换算。 |
| O-13 | 禁止 `seq of`，但 D2 要求 “per-object id, position, velocity, class for every detected object”。 | 以 `object_count` + 聚合字段 `records`/`trajectories` 表示集合，基数为 count；聚合编码不透明，属表示约定。 |
| O-14 | 布尔量在 nat 中的编码规格未定。 | 约定 1 = 有效/是/激活、0 = 无效/否/未激活；E1/E2 的 validity flags 直接对应规格语义。 |
| O-15 | 字符串枚举值未在规格中定值（manoeuvre 类型、warning 类型中 “imminent collision” 的写法、signal state、attention state、route preferences、lane topology 编码）。 | 采用规格措辞的 snake_case：`"cruise_keep_lane"`、`"lane_keeping_with_deceleration"`、`"emergency_deceleration"`、`"none"/"caution"/"imminent_collision"`、`"no risk"/"caution"/"critical"`；具体编码待定。 |
| O-16 | 规格 §11 要求建模者回答的四个问题。 | ①维持 F1–F7，不新增驾驶员监控功能（L2 注意状态经 E3 进入 F3），但交接时序未规定；②D3 由 F1 写、F6/F7 读在 §5.1 中明确授权，可接受；③需要周期时间约束才使紧急分支有意义，规格未给，本模型不加；④Level 1 细化 F3 是 §6 明确规定，不改 F6/F7。 |
| O-17 | A-1（6.0）、A-2 的 `a_min,brake`（4.0）与 A-3（3.0）量级并存。 | 将紧急减速放在 `brake` 与 `required_deceleration` 字段，A-3 放在 `longitudinal_accel` 字段以避开矛盾；两者语义关系待澄清。 |
| O-18 | F1 pre 要求 camera/radar/lidar 三个 validity flags 均为 1。 | 规格只给出 “per-sensor validity flags”，未给融合所需的最小有效传感器组合；本模型取全有效的保守约束，部分失效时的行为未定义。 |

## §11 指定回答（摘录，对应 O-16）

1. 维持七功能拆分——L2 驾驶员注意状态已由 E3 进入 F3，R-L0-1 禁止新增功能；L2 交接时序未规定。
2. D3 由 F1 写、F6/F7 读在 §5.1 中明确授权，可接受。
3. 需要周期时间约束才使紧急分支有意义，规格未给，本模型不加。
4. Level 1 细化 F3 是 §6 明确规定，不改为 F6/F7。

---

## 6. 关键未决点摘要

E9 方向（O-1）、D1/D4 刷新写者（O-2）、D2 无读者（O-3）、F3/F5 的 ego state 来源（O-4）、空对象集 TTC（O-7）、`d_min` 公式（O-8）、N-7 横向加速度数值（O-10）、A-1/A-3 量级关系（O-17）和 F1 最小有效传感器组合（O-18）均未用规格外数值或元素填补。所有 pre 仅陈述有效性标志、范围条件或规格阈值，未出现 `x <> null` 式同义反复。
