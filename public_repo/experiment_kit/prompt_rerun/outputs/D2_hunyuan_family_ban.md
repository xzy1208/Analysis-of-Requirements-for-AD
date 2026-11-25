# NL-RQ-ADAS-v1 — SOFL 形式化规格（重跑版：禁止恒真条件）

> 唯一输入：`C:/Users/zct11/WorkBuddy/2026-11-11-20-16-46/NL-RQ-ADAS-v1_spec.md`（v1.0）。
> 本版按新增段落重跑：pre / post 的守卫中**不出现任何对类型全域恒真的条件**。
> 具体删除：`x <> ""`（String 默认非空）、`n >= 0`（nat 下界由类型保证）、自等式、`if true`。
> 保留的 pre 全部是真实约束：有效性标志（nat 可能为 0）、real 字段的范围条件、§7/§8 阈值。
> 所有被删除的恒真条件及替代写法登记于 open-issues（O-19、O-20）。

---

## 0. 记号与建模约定

- 模块头：`( 入1: 类型 | 入2: 类型 ) 出1: 类型 | 出2: 类型, 出2b: 类型`；`|` 分端口，`,` 分同端口多条流。
- 过程：`process 名(入参) out: 出参` + `ext rd/wr` + `pre` + 一条或多条 `post if <守卫> then <谓词>` + `end_process`；多条 post 按合取理解。
- 可用算子仅 `and`、`=`、`<>`、`>`、`>=`、`<=`、`<` 与点号字段访问；不用 `or`、`not`、`=>`、量词、`seq of`。
- 类型按 SOFL 默认解释：String 非空、nat 下界 0。因此**不**写 `s <> ""`、`n >= 0` 作为约束。
- nat 作 0/1 标志：1 = 有效/是/激活，0 = 无效/否/未激活（O-14）。
- 速度 km/h，距离 m，加速度 m/s²，时间 s（O-12）。
- 禁止 `seq of`，逐对象集合用 `object_count`/`trajectory_count` + 聚合字段表示（O-13）。

---

# 1. 两个 module 完整文本

## 1.1 类型声明（两 module 共用）

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

字段溯源：E1 → `RawSensorData`；E2 → `GnssImu`；E3 → `DriverIntent`；E4 → `Destination`；E5/D1 → `MapSegment`；E6/D4 → `TrafficRules`；E7 → `Warning`；E8/E9 → `Actuation`；D2 → `ObjectTable`/`ObjectRecord`；D3 → `EgoState`；F2 → `PredictedTrajectories`；F3 → `Maneuver`；F4 → `Route`；F5 → `Trajectory`；F3.1 → `TtcSet`。

## 1.2 module ADAS_System（Level 0）

```
module ADAS_System
( raw_sensor_data: RawSensorData | gnss_imu: GnssImu | driver_intent: DriverIntent | destination: Destination | map_data: MapSegment | traffic_rules: TrafficRules | actuator_cmd: Actuation ) warning: Warning | checked_cmd: Actuation

store hd_map_store: MapSegment
store object_track_store: ObjectTable
store ego_state_store: EgoState
store traffic_rules_store: TrafficRules

process F1_Perception(raw_sensor_data, gnss_imu) out: object_table, ego_state, ego_pose
ext rd hd_map_store
ext wr object_track_store
ext wr ego_state_store
pre raw_sensor_data.camera_valid = 1 and raw_sensor_data.radar_valid = 1 and raw_sensor_data.lidar_valid = 1 and raw_sensor_data.frame_timestamp >= 0 and gnss_imu.gnss_valid = 1 and gnss_imu.imu_valid = 1 and gnss_imu.timestamp >= 0
post if raw_sensor_data.camera_valid = 1 and raw_sensor_data.radar_valid = 1 and raw_sensor_data.lidar_valid = 1 then object_track_store.object_count = object_table.object_count
post if object_table.object_count > 0 then object_table.lead_object.object_id = object_table.records.object_id
post if gnss_imu.gnss_valid = 1 then ego_state.speed >= 0
post if gnss_imu.imu_valid = 1 then ego_state.yaw_rate <= 3.5
post if gnss_imu.imu_valid = 1 then ego_state.yaw_rate >= -3.5
post if gnss_imu.gnss_valid = 1 then ego_pose.pose_x = ego_state.pose_x
post if gnss_imu.gnss_valid = 1 then ego_pose.pose_y = ego_state.pose_y
post if gnss_imu.gnss_valid = 1 then ego_state_store.timestamp = ego_state.timestamp
end_process

process F2_Prediction(object_table, ego_pose) out: predicted_trajectories
ext rd hd_map_store
pre hd_map_store.posted_speed_limit > 0
post if object_table.object_count = 0 then predicted_trajectories.trajectory_count = 0
post if object_table.object_count > 0 then predicted_trajectories.trajectory_count = object_table.object_count
post if object_table.object_count > 0 then predicted_trajectories.horizon >= 3.0
post if object_table.object_count > 0 then predicted_trajectories.minimum_ttc >= 0
post if object_table.object_count > 0 then predicted_trajectories.trajectories.longitudinal_distance >= predicted_trajectories.trajectories.rss_min_distance
end_process

process F3_Planning(ego_state, driver_intent, route, predicted_trajectories) out: maneuver, warning
ext rd hd_map_store
ext rd traffic_rules_store
pre ego_state.speed >= 0 and traffic_rules_store.posted_speed_limit > 0 and route.path_length > 0
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
pre destination.latitude >= -90 and destination.latitude <= 90 and destination.longitude >= -180 and destination.longitude <= 180
post if destination.latitude >= -90 and destination.latitude <= 90 then route.path_length > 0
post if destination.longitude >= -180 and destination.longitude <= 180 then route.eta > 0
post if destination.latitude >= -90 then route.lane_geometry = hd_map_store.lane_topology
end_process

process F5_Motion(maneuver, route, ego_state, predicted_trajectories) out: trajectory
ext rd hd_map_store
ext rd traffic_rules_store
pre maneuver.required_deceleration >= 0 and route.path_length > 0 and ego_state.speed >= 0 and traffic_rules_store.posted_speed_limit > 0
post if traffic_rules_store.posted_speed_limit > 0 then trajectory.max_speed <= traffic_rules_store.posted_speed_limit
post if maneuver.maneuver_type = "emergency_deceleration" then trajectory.required_deceleration >= 6.0
post if maneuver.maneuver_type = "lane_keeping_with_deceleration" then trajectory.required_deceleration > 0
post if maneuver.required_deceleration >= 0 then trajectory.required_deceleration >= maneuver.required_deceleration
post if traffic_rules_store.posted_speed_limit > 0 then trajectory.max_accel <= 2.0
post if predicted_trajectories.trajectory_count > 0 then trajectory.horizon >= 3.0
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

## 1.3 module AEB_Branch（Level 1，F3 的 AEB 分支）

```
module AEB_Branch
( predicted_trajectories: PredictedTrajectories | ego_state: EgoState | driver_intent: DriverIntent | route: Route ) warning: Warning | maneuver: Maneuver

store hd_map_store: MapSegment
store traffic_rules_store: TrafficRules

process F3_1_TTC(predicted_trajectories, ego_state) out: ttc_set
pre predicted_trajectories.horizon >= 3.0 and ego_state.timestamp >= 0
post if predicted_trajectories.trajectory_count = 0 then ttc_set.object_count = 0
post if predicted_trajectories.trajectory_count > 0 then ttc_set.object_count = predicted_trajectories.trajectory_count
post if predicted_trajectories.trajectory_count > 0 then ttc_set.minimum_ttc = predicted_trajectories.minimum_ttc
post if predicted_trajectories.trajectory_count > 0 then ttc_set.minimum_ttc >= 0
end_process

process F3_2_Risk(ttc_set) out: risk, warning
ext rd traffic_rules_store
pre traffic_rules_store.posted_speed_limit > 0
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
pre ego_state.speed >= 0 and driver_intent.requested_cruise_speed >= 0 and route.path_length > 0 and hd_map_store.posted_speed_limit > 0
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

# 2. CDFD 元素与连线清单

## 2.1 Level 0 — ADAS_System

恰好 7 个 process、4 个 store、9 个外部终端（R-L0-1）。

**Processes**：F1_Perception、F2_Prediction、F3_Planning、F4_Route、F5_Motion、F6_Control、F7_Safety_Shield。

**Data stores**：D1 `hd_map_store`: MapSegment；D2 `object_track_store`: ObjectTable；D3 `ego_state_store`: EgoState；D4 `traffic_rules_store`: TrafficRules。

**External terminals**：E1 `raw_sensor_data`(in)、E2 `gnss_imu`(in)、E3 `driver_intent`(in)、E4 `destination`(in)、E5 `map_data`(in)、E6 `traffic_rules`(in)、E7 `warning`(out)、E8 `checked_cmd`(out)、E9 `actuator_cmd`(in)。

**数据流连线（具名、有向、单生产者/单消费者）**

| # | 数据流 | 起点 → 终点 | 类型 | 依据 |
|---|---|---|---|---|
| 1 | raw_sensor_data | E1 → F1 | RawSensorData | §3 E1、§5 F1 |
| 2 | gnss_imu | E2 → F1 | GnssImu | §3 E2、§5 F1 |
| 3 | driver_intent | E3 → F3 | DriverIntent | §5 F3 |
| 4 | destination | E4 → F4 | Destination | §5 F4 |
| 5 | map_data | E5 → D1（外部刷新） | MapSegment | §4 D1，O-2 |
| 6 | traffic_rules | E6 → D4（外部刷新） | TrafficRules | §4 D4，O-2 |
| 7 | ego_pose | F1 → F2 | EgoPose | §5.1 |
| 8 | object_table | F1 → F2 | ObjectTable | §5.1 |
| 9 | ego_pose | F1 → F4 | EgoPose | §5.1 |
| 10 | ego_state | F1 → F3 | EgoState | §5 F3，O-4 |
| 11 | ego_state | F1 → F5 | EgoState | §5 F5，O-4 |
| 12 | predicted_trajectories | F2 → F3 | PredictedTrajectories | §5.1 |
| 13 | predicted_trajectories | F2 → F5 | PredictedTrajectories | §5.1（规格明确双消费者） |
| 14 | manoeuvre | F3 → F5 | Maneuver | §5.1 |
| 15 | route | F4 → F3 | Route | §5.1 |
| 16 | route | F4 → F5 | Route | §5.1（route 同时供 F3 与 F5） |
| 17 | trajectory | F5 → F6 | Trajectory | §5.1 |
| 18 | actuator_cmd | F6 → F7（E9 为该流上的接口节点） | Actuation | §5 F6/F7、R-E-2，O-1 |
| 19 | warning | F3 → E7 | Warning | §5.1、R-E-1 |
| 20 | checked_cmd | F7 → E8 | Actuation | §5.1、R-E-1 |

**存储读写连线（与 ext rd/wr 一致）**

| 连线 | 方向 | 依据 |
|---|---|---|
| F1 ↔ D1 | read | §5.1 |
| F1 → D2 | write | §5.1 |
| F1 → D3 | write | §5.1 |
| F2 ↔ D1 | read | §5.1 |
| F3 ↔ D1 | read | §5.1 |
| F3 ↔ D4 | read | §5.1 |
| F4 ↔ D1 | read | §5.1 |
| F5 ↔ D1 | read | §5.1 |
| F5 ↔ D4 | read | §5.1 |
| F6 ↔ D3 | read | §5.1 |
| F7 ↔ D3 | read | §5.1 |
| F7 ↔ D4 | read | §5.1 |

D2 只有 F1 写入、§5.1 未分配读者，不虚构读者（O-3）。

## 2.2 Level 1 — AEB_Branch

恰好 F3.1 → F3.2 → F3.3（R-L1-1）。

**元素**：process F3_1_TTC、F3_2_Risk、F3_3_Maneuver；store D1 `hd_map_store`（只读）、D4 `traffic_rules_store`（只读）；外部终端 E3 `driver_intent`(in)、E7 `warning`(out)；边界继承端口 `predicted_trajectories`(来自 F2)、`ego_state`(来自 F1)、`route`(来自 F4)、`manoeuvre`(送往 F5)。不新增外部终端。

| # | 数据流 | 起点 → 终点 | 类型 | 依据 |
|---|---|---|---|---|
| 1 | predicted_trajectories | (F2 边界) → F3.1 | PredictedTrajectories | §6 F3.1 |
| 2 | ego_state | (F1 边界) → F3.1 | EgoState | §6 F3.1 |
| 3 | ttc_set | F3.1 → F3.2 | TtcSet | §6 F3.2 |
| 4 | risk | F3.2 → F3.3 | String | §6 F3.3 |
| 5 | warning | F3.2 → E7 | Warning | §6 F3.2、R-E-1 |
| 6 | ego_state | (F1 边界) → F3.3 | EgoState | §6 F3.3 |
| 7 | driver_intent | E3 → F3.3 | DriverIntent | §6 F3.3 |
| 8 | route | (F4 边界) → F3.3 | Route | §6 F3.3 |
| 9 | manoeuvre | F3.3 → (F5 边界) | Maneuver | §6 F3.3 |

**存储读写**：F3.2 ↔ D4 read（§6 F3.2）；F3.3 ↔ D1 read（§6 F3.3）。Level 1 无任何 `ext wr`，与 §5 F3 “shall not write any store” 一致。

---

# 3. Open issues

| ID | 问题 | 本模型处理 |
|---|---|---|
| O-1 | §3 E9 方向为 in，但 §5 F6 写 Output: actuator_cmd (E9)，且 R-E-1 禁止 E7/E8 之外输出。 | 建成 F6→F7 单一具名流，E9 作为该流上的接口节点（对 F7 为 in），不新增输出。 |
| O-2 | §4 称 D1/D4 由 E5/E6 刷新，但 §5.1 的 store-writes 只有 F1 写 D2/D3；R-D-1 要求仅 owner 写。 | 建 E5→D1、E6→D4 外部刷新连线，不为 D1/D4 虚构写入函数；冲突待澄清。 |
| O-3 | D2 在 §5.1 只有 F1 写入、无读者。 | 保留写入连线，不虚构读者。 |
| O-4 | §5 将 ego state 列为 F3/F5 输入，但 §5.1 只给 F1→F2/F4 的 ego pose，且 F3/F5 未获授权读 D3。 | 补 F1→F3、F1→F5 的 ego_state 流（流 10/11）；属规格内部缺口，非新增信号。 |
| O-5 | §8 A-5 引用未定义的 R-F2-1。 | 按 A-5 自身取值建模，将 R-F2-1 理解为 F2 时域 ≥ 3.0 s；不补造条款。 |
| O-6 | §5 F2 “only function that computes TTC” 与 §6 F3.1 “shall compute TTC” 冲突。 | F2 在 PredictedTrajectories 中给出 minimum_ttc；F3.1 仅形成 TTC 集合并取最小/计数。 |
| O-7 | 对象数为 0 时 minimum_ttc 取值未定义。 | count=0 时 TTC 集合计数为 0、风险为 no risk；哨兵值待定。 |
| O-8 | N-5 的 d_min（RSS Eq.(1)）无公式，仅有 A-2 参数集。 | 以 rss_min_distance 字段承载符号，不赋数值；公式需集成方提供。 |
| O-9 | N-1 “up to at least 130 km/h” 是能力下界而非速度上界。 | 以 `ego_state.speed <= 130` 作为已建模域守卫；>130 行为留空。 |
| O-10 | N-7 要求横向加速度在能力内，但 §7/§8 无横向加速度数值（A-4 是 yaw-rate）。 | 只量化 A-6 的 ±1.0 转向包络；N-7 保持定性。 |
| O-11 | A-2 的 a_max,accel = 2.0 限定在响应时间内，但规格无时间模型。 | 写作无时间限定的 `max_accel <= 2.0`；时间限定无法表达。 |
| O-12 | 规格未统一单位。 | speed/max_speed 为 km/h，加速度为 m/s²，时间 s；不做单位换算。 |
| O-13 | 禁止 `seq of`，但 D2 要求逐对象记录。 | 用 object_count + 聚合字段 records/trajectories 表示；聚合编码不透明。 |
| O-14 | nat 作布尔编码未定。 | 1 = 有效/是/激活，0 = 无效/否/未激活。 |
| O-15 | 字符串枚举值未定。 | 采用规格措辞 snake_case："cruise_keep_lane"、"lane_keeping_with_deceleration"、"emergency_deceleration"、"none"/"caution"/"imminent_collision"、"no risk"/"caution"/"critical"。 |
| O-16 | 规格 §11 要求回答的四个问题。 | ①维持 F1–F7，不新增驾驶员监控功能；②D3 由 F1 写、F6/F7 读已获 §5.1 授权，可接受；③需要周期时间约束但规格未给，不加；④Level 1 细化 F3 是 §6 规定，不改 F6/F7。 |
| O-17 | A-1(6.0)、A-2 的 a_min,brake(4.0) 与 A-3(3.0) 量级并存。 | 紧急减速放 required_deceleration/brake，A-3 放 longitudinal_accel；语义关系待澄清。 |
| O-18 | §3 只说逐传感器 validity flags，未给融合所需最小有效组合。 | F1 取三者全有效的保守约束；部分失效行为未定义。 |
| O-19 | **（本次重跑新增）** 上一版含恒真条件：`road_id <> ""`、`lane_id <> ""`、`risk <> ""`、`lead_object.object_id <> ""`（String 默认非空），以及 `object_count >= 0`、`trajectory_count >= 0`（nat 下界由类型保证）。 | 全部删除。D1/D4 的读取条件改用真实范围条件 `posted_speed_limit > 0`；nat 计数只用 `= 0` / `> 0` 这两种可假情形作为守卫。 |
| O-20 | **（本次重跑新增）** 删除恒真条件后，F1 关于 lead object 的 post 需改成可假的 relational 约束。 | 写为 `lead_object.object_id = records.object_id`（两个不同字段间的等式，可假）；records 为 O-13 的聚合代表记录，此等价是建模约定。 |
| O-21 | **（本次重跑新增）** 本次所有 process 均保留了至少一条真实 pre，无省略情形。 | 若后续删去 F2/F3.2 的 `posted_speed_limit > 0`，它们将只依赖已声明输入端口而须省略 pre；当前保留该 real 范围条件，故未省略。 |

---

# 4. 可追溯性说明

## 4.1 R-xx 条款 → 模型元素

| 条款 | 对应元素 |
|---|---|
| R-SCOPE-1 | 两 module 边界；SAE L2 语义由 E3 `driver_attention` 与 F3_3 的 override 处理表达 |
| R-SCOPE-2 | Level 0 的 E1–E9 仅为外部终端，无内部传感器/执行器元素 |
| R-SCOPE-3 | F1/F2/F4/F5/F6/F7 为原子 process，契约只约束功能与命名数据流 |
| R-SCOPE-4 | `ADAS_System` + `AEB_Branch` 两个 module，仅 F3 细化 |
| R-E-1 | 两 module 出端口仅 `warning`(E7)/`checked_cmd`(E8)；流 19/20、Level 1 流 5 |
| R-E-2 | F7 契约；流 18（F6→E9→F7）与流 20（F7→E8） |
| R-D-1 | `ext wr` 仅 F1（D2/D3）；D1/D4 外部刷新见 O-2 |
| R-D-2 | §2.1 的 12 条读写连线与 §5.1 逐条一致 |
| R-L0-1 | §2.1 元素清单：恰好 7 process / 4 store / 9 external terminal |
| R-L1-1 | §2.2 元素清单：F3.1/F3.2/F3.3 及内部流 1/3/4 |
| R-G-1 | §1.2 与 §1.3 全部 10 个 process 的 pre + post；有阈值者给出量化约束，无阈值者（F4/F3.1）给定性/范围 post |
| R-G-2 | 本 §4 矩阵 |
| R-G-3 | §3 open issues O-1…O-21 |
| R-G-4 | §2.1/§2.2 具名有向流；共享流仅 F2→F3/F5 与 F4→F3/F5（§5.1 明确允许） |
| R-G-5 | 每个生产者均有 §5.1/§6 指定消费者；D2 无读者见 O-3 |
| R-G-6 | 本次按新增约束：不写 `x <> null`、不写 `x <> ""`、不写 `n >= 0`；pre 用有效性标志/real 范围/§7§8 阈值，post 守卫用可假情形（如 `minimum_ttc <= 1.5`、`object_count = 0`） |
| §5 F1 | F1 process；流 1/2/7/8/9/10/11；D1 rd、D2/D3 wr；A-4 |
| §5 F2 | F2 process；流 7/8/12/13；D1 rd；A-7、N-5 |
| §5 F3 | F3 process；流 3/12/14/15/19；D1/D4 rd；A-1/A-5、N-1/N-2 |
| §5 F4 | F4 process；流 4/9/15/16；D1 rd；定性 post |
| §5 F5 | F5 process；流 11/13/14/16/17；D1/D4 rd；A-2/A-7 |
| §5 F6 | F6 process；流 17/18；D3 rd；A-2/A-3/A-6 |
| §5 F7 | F7 process；流 18/20；D3/D4 rd；A-3/A-6、N-7 |
| §5.1 | §2.1 全部 20 条流 + 12 条读写连线 |
| §6 F3.1/F3.2/F3.3 | §1.3 三个 process + §2.2 连线 |
| §7 N-1…N-7、§8 A-1…A-7 | 见 §4.2 |
| §11.1–11.4 | O-16 |

## 4.2 阈值落点（仅取自 §7 / §8）

| 阈值 | 值 | 落点 |
|---|---|---|
| N-1 | 130 km/h | F3_3：`risk = "critical" and ego_state.speed <= 130` → `required_deceleration >= 6.0` |
| N-2 | TTC ≤ 2.0 s 须预警 | F3/F3_2：`minimum_ttc <= 2.0` → `warning.active = 1`；1.5 s 作 critical 边界（A-5） |
| N-3 | > 30 km/h 降速 | 经 A-1 推导：F3/F3_3/F5 的 `required_deceleration >= 6.0` |
| N-4 | CCRm/CCRb 包线 | A-1 推导依据，间接落在 `>= 6.0` |
| N-5 | RSS d_min | F2：`longitudinal_distance >= rss_min_distance`；公式缺失见 O-8 |
| N-6 | RSS 制动剖面 | F5 `max_accel <= 2.0`；F6/F7 `brake >= 4.0`（A-2） |
| N-7 | 横向包络 | F6/F7 转向 ±1.0（A-6）与 F7 保向；数值横向加速度缺失见 O-10 |
| A-1 | 6.0 m/s² | F3、F3_3、F5 的 `required_deceleration >= 6.0` |
| A-2 | ρ=0.1, accel=2.0, brake=4.0 | F5 `max_accel <= 2.0`；F6/F7 `brake >= 4.0` |
| A-3 | 3.0 m/s² | F6/F7 `longitudinal_accel <= 3.0` |
| A-4 | 3.5 rad/s | F1 `yaw_rate <= 3.5 and yaw_rate >= -3.5` |
| A-5 | 3.0 s / 1.5 s | F3 与 F3_2 三档风险边界（R-F2-1 缺失见 O-5） |
| A-6 | ±1.0 转向 | F6/F7 转向上/下界，F7 保向 |
| A-7 | 3.0 s 预测时域 | F2 `horizon >= 3.0`；F5 `trajectory.horizon >= 3.0`；F3.1 pre `horizon >= 3.0` |

---

# 5. 自查表：pre 中的真实约束及依据

判定口径：条件若对类型声明的所有取值成立即为恒真，不得出现。nat 的 `>= 0`、String 的 `<> ""`、自等式、`if true` 均已剔除。

| process | pre 中的真实约束（逐条） | 为什么真实 | 依据 |
|---|---|---|---|
| F1_Perception | `camera_valid = 1`、`radar_valid = 1`、`lidar_valid = 1` | nat 可为 0，标志由 E1 生产者写入 | §3 E1、O-18 |
| F1_Perception | `frame_timestamp >= 0`、`gnss_imu.timestamp >= 0` | real 字段，可为负 | §3 E1/E2 时间戳、O-12 |
| F1_Perception | `gnss_valid = 1`、`imu_valid = 1` | nat 可为 0，标志由 E2 写入 | §3 E2 |
| F2_Prediction | `hd_map_store.posted_speed_limit > 0` | real 字段，可为 0/负；替代被删的 `road_id <> ""` | §4 D1、§5 F2、O-19 |
| F3_Planning | `ego_state.speed >= 0` | real 字段，可为负 | §5 F3、量纲 |
| F3_Planning | `traffic_rules_store.posted_speed_limit > 0` | real 字段，可为 0/负 | §4 D4、§5 F3 |
| F3_Planning | `route.path_length > 0` | real 字段，可为 0/负 | §5 F4→F3 依赖 |
| F4_Route | `latitude >= -90 and latitude <= 90`、`longitude >= -180 and longitude <= 180` | real 字段，可越界；替代被删的 `road_id <> ""` | §3 E4、O-19 |
| F5_Motion | `maneuver.required_deceleration >= 0` | real 字段，可为负 | §5 F3→F5、A-1 |
| F5_Motion | `route.path_length > 0`、`ego_state.speed >= 0` | real 字段，可为 0/负 | §5 F5 |
| F5_Motion | `traffic_rules_store.posted_speed_limit > 0` | real 字段，可为 0/负 | §4 D4、§5 F5 |
| F6_Control | `trajectory.horizon > 0` | real 字段，可为 0/负 | §8 A-7、§5 F5→F6 |
| F6_Control | `trajectory.max_speed >= 0`、`ego_state_store.timestamp >= 0` | real 字段，可为负 | §5 F5/F6、§4 D3 |
| F7_Safety_Shield | `actuator_cmd.brake >= 0` | real 字段，可为负；F7 须能处理 F6 越界转向，故不约束 steering 在包线内 | §5 F7、R-E-2 |
| F7_Safety_Shield | `ego_state_store.timestamp >= 0` | real 字段，可为负 | §4 D3 |
| F7_Safety_Shield | `traffic_rules_store.posted_speed_limit > 0` | real 字段，可为 0/负 | §4 D4、§5 F7 |
| F3_1_TTC | `predicted_trajectories.horizon >= 3.0` | real 字段，可小于 3.0；替代被删的 `trajectory_count >= 0` | §8 A-7、O-19 |
| F3_1_TTC | `ego_state.timestamp >= 0` | real 字段，可为负 | §6 F3.1、§4 D3 |
| F3_2_Risk | `traffic_rules_store.posted_speed_limit > 0` | real 字段，可为 0/负；替代被删的 `object_count >= 0` | §6 F3.2、§4 D4、O-19 |
| F3_3_Maneuver | `ego_state.speed >= 0` | real 字段，可为负 | §6 F3.3、N-1 |
| F3_3_Maneuver | `driver_intent.requested_cruise_speed >= 0` | real 字段，可为负 | §3 E3、§6 F3.3 |
| F3_3_Maneuver | `route.path_length > 0`、`hd_map_store.posted_speed_limit > 0` | real 字段，可为 0/负；替代被删的 `risk <> ""` 与 `lane_id <> ""` | §6 F3.3、§4 D1、O-19 |

**省略 pre 的 process**：无。本次 10 个 process 均保留了至少一条可假的真实约束（见上表），因此没有需要按“无实质前置条件”省略 pre 的情形；F2 与 F3.2 的边界情况见 O-21。

**post 守卫自查**：所有 `post if` 的守卫均可假——`object_count = 0` / `> 0`（nat 可取 0 或正）、`minimum_ttc > 3.0` / `<= 3.0 and > 1.5` / `<= 1.5` / `<= 2.0`（real）、`override_accelerate = 1`（nat 可为 0）、`steering >= -1.0 and <= 1.0` / `> 1.0` / `< -1.0`（real）、`risk = "no risk"` 等（String 可取其它枚举值）。无 `if true`、无自等式、无非空串恒真检查。
