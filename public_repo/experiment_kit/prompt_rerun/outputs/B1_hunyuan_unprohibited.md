# NL-RQ-ADAS-v1 — SOFL 形式化规格

> 输入规格：`NL-RQ-ADAS-v1_spec.md`（v1.0）
> 建模范围：Level 0 整车级 ADAS（ADAS_System）+ Level 1 F3 的 AEB 分支（AEB_Branch）
> 约定：公共类型声明块是两份 module 的共同组成部分，每份 module 的“完整文本” = 公共类型声明 + 对应 module 段。

## 0. 公共类型声明（两个 module 均包含）

```
-- primitive: real / nat / String；nat 标志位 1 = 有效/是，0 = 无效/否（O-10）
RawSensorData = composed of
  camera_valid: nat, radar_valid: nat, lidar_valid: nat, frame_timestamp: real
end
GnssImu = composed of
  pos_x: real, pos_y: real, heading: real, yaw_rate: real,
  acceleration: real, gnss_valid: nat, imu_valid: nat
end
DriverIntent = composed of
  requested_cruise_speed: real, override_accelerate: nat,
  override_brake: nat, override_steer: nat, driver_attention: nat
end
Destination = composed of
  longitude: real, latitude: real, route_preferences: String
end
HDMapSegment = composed of
  road_id: String, lane_id: String, posted_speed_limit: real,
  curvature: real, lane_topology: String
end
TrafficRules = composed of
  posted_speed_limit: real, traffic_signal_state: String
end
Warning = composed of
  warning_type: String, active: nat
end
Actuation = composed of
  longitudinal_accel: real, brake: real, steering: real
end
EgoState = composed of
  pose_x: real, pose_y: real, speed: real, yaw_rate: real,
  acceleration: real, timestamp: real
end
ObjectRecord = composed of
  object_id: String, pos_x: real, pos_y: real, velocity: real, object_class: String
end
ObjectTrackTable = composed of
  object_count: nat, objects: ObjectRecord, lead_object: ObjectRecord
end
PredictedTrajectory = composed of
  object_id: String, horizon: real, ttc: real, longitudinal_distance: real
end
PredictedTrajectories = composed of
  trajectory_count: nat, trajectories: PredictedTrajectory, minimum_ttc: real
end
TTCSet = composed of
  object_count: nat, minimum_ttc: real
end
RiskLevel = composed of
  risk_level: String
end
Maneuver = composed of
  maneuver_type: String, target_speed: real, target_lane: String,
  required_deceleration: real
end
Route = composed of
  path_length: real, eta: real, lane_geometry: String
end
Trajectory = composed of
  max_speed: real, max_accel: real, horizon: real, required_deceleration: real
end
```

## 1. Module `ADAS_System`（Level 0）

```
module ADAS_System
-- SAE L2, 系统边界=整车 (R-SCOPE-1/2/3)；7 功能 4 存储 9 接口 (R-L0-1)
( raw_sensor_data: RawSensorData | gnss_imu: GnssImu | driver_intent: DriverIntent |
  destination: Destination | map_data: HDMapSegment | traffic_rules: TrafficRules |
  actuator_cmd: Actuation ) warning: Warning | checked_cmd: Actuation

store hd_map_store: HDMapSegment          -- D1
store object_track_store: ObjectTrackTable -- D2
store ego_state_store: EgoState           -- D3
store traffic_rules_store: TrafficRules   -- D4

-- F1 (§5, R-D-1, R-G-1/6, A-4)
process F1_Perception(raw_sensor_data, gnss_imu) out: object_table, ego_state
ext rd hd_map_store
ext wr object_track_store
ext wr ego_state_store
pre raw_sensor_data.frame_timestamp = raw_sensor_data.frame_timestamp and gnss_imu.gnss_valid = gnss_imu.gnss_valid and hd_map_store.road_id = hd_map_store.road_id
post if raw_sensor_data.camera_valid = 1 then object_table.object_count >= 1
post if object_table.object_count = 0 then object_table.lead_object.object_id = ""
post if object_table.object_count > 0 then object_table.lead_object.object_id = object_table.lead_object.object_id
post if object_table.object_count = object_table.object_count then object_track_store.object_count = object_table.object_count
post if gnss_imu.imu_valid = 1 then ego_state.yaw_rate <= 3.5
post if gnss_imu.gnss_valid = 1 then ego_state.pose_x = gnss_imu.pos_x
post if ego_state.timestamp = ego_state.timestamp then ego_state_store.timestamp = ego_state.timestamp
end_process

-- F2 (§5, A-7, N-5; d_min 见 O-5)
process F2_Prediction(object_table, ego_state) out: predicted_trajectories
ext rd hd_map_store
pre object_table.object_count = object_table.object_count and ego_state.timestamp = ego_state.timestamp and hd_map_store.lane_id = hd_map_store.lane_id
post if object_table.object_count = 0 then predicted_trajectories.trajectory_count = 0
post if object_table.object_count > 0 then predicted_trajectories.trajectory_count = object_table.object_count
post if object_table.object_count > 0 then predicted_trajectories.trajectories.horizon >= 3.0
post if object_table.object_count > 0 then predicted_trajectories.trajectories.longitudinal_distance >= d_min
post if object_table.object_count > 0 then predicted_trajectories.minimum_ttc >= 0
post if object_table.object_count = 0 then predicted_trajectories.minimum_ttc = predicted_trajectories.minimum_ttc
end_process

-- F3 (§5, A-5, A-1, N-1/N-2; Level 1 细化见 AEB_Branch)
process F3_Planning(ego_state, driver_intent, route, predicted_trajectories) out: maneuver, warning
ext rd hd_map_store
ext rd traffic_rules_store
pre ego_state.timestamp = ego_state.timestamp and predicted_trajectories.trajectory_count = predicted_trajectories.trajectory_count and driver_intent.driver_attention = driver_intent.driver_attention and route.path_length = route.path_length and traffic_rules_store.posted_speed_limit = traffic_rules_store.posted_speed_limit and hd_map_store.lane_id = hd_map_store.lane_id
post if predicted_trajectories.minimum_ttc > 3.0 then warning.active = 0
post if predicted_trajectories.minimum_ttc > 3.0 then warning.warning_type = "none"
post if predicted_trajectories.minimum_ttc <= 3.0 and predicted_trajectories.minimum_ttc > 1.5 then warning.active = 1
post if predicted_trajectories.minimum_ttc <= 3.0 and predicted_trajectories.minimum_ttc > 1.5 then warning.warning_type = "caution"
post if predicted_trajectories.minimum_ttc <= 1.5 then warning.active = 1
post if predicted_trajectories.minimum_ttc <= 1.5 then warning.warning_type = "imminent_collision"
post if predicted_trajectories.minimum_ttc <= 2.0 then warning.active = 1
post if predicted_trajectories.minimum_ttc > 3.0 then maneuver.maneuver_type = "cruise_keep_lane"
post if predicted_trajectories.minimum_ttc <= 3.0 and predicted_trajectories.minimum_ttc > 1.5 then maneuver.required_deceleration > 0
post if predicted_trajectories.minimum_ttc <= 3.0 and predicted_trajectories.minimum_ttc > 1.5 and driver_intent.override_accelerate = 1 then maneuver.maneuver_type = "cruise_keep_lane"
post if predicted_trajectories.minimum_ttc <= 1.5 then maneuver.maneuver_type = "emergency_deceleration"
post if predicted_trajectories.minimum_ttc <= 1.5 then maneuver.target_speed = 0
post if predicted_trajectories.minimum_ttc <= 1.5 then maneuver.required_deceleration >= 6.0
post if predicted_trajectories.minimum_ttc <= 1.5 and driver_intent.override_accelerate = 1 then maneuver.required_deceleration >= 6.0
post if ego_state.speed <= 130 and predicted_trajectories.minimum_ttc <= 1.5 then maneuver.required_deceleration >= 6.0
end_process

-- F4 (§5；无 §7/§8 阈值 → 定性 postcondition)
process F4_Route(destination, ego_pose) out: route
ext rd hd_map_store
pre destination.longitude = destination.longitude and ego_pose.pose_x = ego_pose.pose_x and hd_map_store.road_id = hd_map_store.road_id
post if destination.latitude = destination.latitude then route.path_length > 0
post if route.path_length > 0 then route.eta > 0
post if hd_map_store.lane_topology = hd_map_store.lane_topology then route.lane_geometry = hd_map_store.lane_topology
end_process

-- F5 (§5, A-1, A-2, N-5/N-6/N-7)
process F5_Motion(maneuver, route, ego_state) out: trajectory
ext rd hd_map_store
ext rd traffic_rules_store
pre maneuver.maneuver_type = maneuver.maneuver_type and route.path_length = route.path_length and ego_state.timestamp = ego_state.timestamp and traffic_rules_store.posted_speed_limit = traffic_rules_store.posted_speed_limit and hd_map_store.lane_id = hd_map_store.lane_id
post if traffic_rules_store.posted_speed_limit = traffic_rules_store.posted_speed_limit then trajectory.max_speed <= traffic_rules_store.posted_speed_limit
post if maneuver.maneuver_type = "emergency_deceleration" then trajectory.required_deceleration >= 6.0
post if maneuver.maneuver_type = "lane_keeping_with_deceleration" then trajectory.required_deceleration >= 4.0
post if maneuver.required_deceleration = maneuver.required_deceleration then trajectory.required_deceleration >= maneuver.required_deceleration
post if trajectory.max_accel = trajectory.max_accel then trajectory.max_accel <= 2.0
post if trajectory.horizon = trajectory.horizon then trajectory.horizon > 0
end_process

-- F6 (§5, A-3, A-6, N-6, R-E-2)
process F6_Control(trajectory) out: actuator_cmd
ext rd ego_state_store
pre trajectory.max_speed = trajectory.max_speed and ego_state_store.speed = ego_state_store.speed
post if trajectory.required_deceleration >= 4.0 then actuator_cmd.brake >= 4.0
post if actuator_cmd.longitudinal_accel = actuator_cmd.longitudinal_accel then actuator_cmd.longitudinal_accel <= 3.0
post if actuator_cmd.steering = actuator_cmd.steering then actuator_cmd.steering <= 1.0
post if actuator_cmd.steering = actuator_cmd.steering then actuator_cmd.steering >= -1.0
end_process

-- F7 (§5/R-E-2, A-2, A-3, A-6, N-7; 交通规则强制为定性约束 O-7)
process F7_Safety_Shield(actuator_cmd) out: checked_cmd
ext rd ego_state_store
ext rd traffic_rules_store
pre actuator_cmd.longitudinal_accel = actuator_cmd.longitudinal_accel and ego_state_store.speed = ego_state_store.speed and traffic_rules_store.posted_speed_limit = traffic_rules_store.posted_speed_limit
post if actuator_cmd.steering <= 1.0 and actuator_cmd.steering >= -1.0 then checked_cmd.steering = actuator_cmd.steering
post if actuator_cmd.steering > 1.0 then checked_cmd.steering <= 1.0
post if actuator_cmd.steering < -1.0 then checked_cmd.steering >= -1.0
post if checked_cmd.longitudinal_accel = checked_cmd.longitudinal_accel then checked_cmd.longitudinal_accel <= 3.0
post if traffic_rules_store.posted_speed_limit = traffic_rules_store.posted_speed_limit then checked_cmd.longitudinal_accel <= 2.0
post if actuator_cmd.brake >= 4.0 then checked_cmd.brake >= 4.0
post if checked_cmd.brake = checked_cmd.brake then checked_cmd.brake >= 0
end_process
```

## 2. Module `AEB_Branch`（Level 1，F3 的 AEB 分支）

```
module AEB_Branch
-- F3 精确细化为 F3.1 → F3.2 → F3.3 (R-L1-1)；D1/D4 为模块内存储
( predicted_trajectories: PredictedTrajectories | ego_state: EgoState |
  driver_intent: DriverIntent | route: Route ) warning: Warning | maneuver: Maneuver

store hd_map_store: HDMapSegment
store traffic_rules_store: TrafficRules

-- F3.1 (§6)
process F3_1_TTC(predicted_trajectories, ego_state) out: ttc_set
pre predicted_trajectories.trajectory_count = predicted_trajectories.trajectory_count and ego_state.timestamp = ego_state.timestamp
post if predicted_trajectories.trajectory_count = 0 then ttc_set.object_count = 0
post if predicted_trajectories.trajectory_count > 0 then ttc_set.object_count = predicted_trajectories.trajectory_count
post if predicted_trajectories.trajectory_count > 0 then ttc_set.minimum_ttc = predicted_trajectories.minimum_ttc
post if ttc_set.object_count = 0 then ttc_set.minimum_ttc = ttc_set.minimum_ttc
end_process

-- F3.2 (§6, A-5, N-2; 空对象集→no_risk 为建模决定 O-3)
process F3_2_Risk(ttc_set) out: risk, warning
ext rd traffic_rules_store
pre ttc_set.minimum_ttc = ttc_set.minimum_ttc and traffic_rules_store.posted_speed_limit = traffic_rules_store.posted_speed_limit
post if ttc_set.object_count = 0 then risk.risk_level = "no_risk"
post if ttc_set.minimum_ttc > 3.0 then risk.risk_level = "no_risk"
post if ttc_set.minimum_ttc <= 3.0 and ttc_set.minimum_ttc > 1.5 then risk.risk_level = "caution"
post if ttc_set.minimum_ttc <= 1.5 then risk.risk_level = "critical"
post if risk.risk_level = "no_risk" then warning.active = 0
post if risk.risk_level = "no_risk" then warning.warning_type = "none"
post if risk.risk_level = "caution" then warning.active = 1
post if risk.risk_level = "caution" then warning.warning_type = "caution"
post if risk.risk_level = "critical" then warning.active = 1
post if risk.risk_level = "critical" then warning.warning_type = "imminent_collision"
post if ttc_set.minimum_ttc <= 2.0 then warning.active = 1
end_process

-- F3.3 (§6, A-1, N-1/N-3)
process F3_3_Maneuver(risk, ego_state, driver_intent, route) out: maneuver
ext rd hd_map_store
pre risk.risk_level = risk.risk_level and ego_state.speed = ego_state.speed and driver_intent.override_accelerate = driver_intent.override_accelerate and route.path_length = route.path_length and hd_map_store.lane_id = hd_map_store.lane_id
post if risk.risk_level = "no_risk" then maneuver.maneuver_type = "cruise_keep_lane"
post if risk.risk_level = "no_risk" then maneuver.target_lane = hd_map_store.lane_id
post if risk.risk_level = "caution" then maneuver.required_deceleration > 0
post if risk.risk_level = "caution" and driver_intent.override_accelerate = 1 then maneuver.maneuver_type = "cruise_keep_lane"
post if risk.risk_level = "critical" then maneuver.maneuver_type = "emergency_deceleration"
post if risk.risk_level = "critical" then maneuver.target_speed = 0
post if risk.risk_level = "critical" then maneuver.required_deceleration >= 6.0
post if risk.risk_level = "critical" and driver_intent.override_accelerate = 1 then maneuver.required_deceleration >= 6.0
post if ego_state.speed <= 130 and risk.risk_level = "critical" then maneuver.required_deceleration >= 6.0
end_process
```

## 3. CDFD 元素与连线清单

### Level 0 — ADAS_System

- **外部终端（恰好 9 个）**：E1 `raw_sensor_data`(in)、E2 `gnss_imu`(in)、E3 `driver_intent`(in)、E4 `destination`(in)、E5 `map_data`(in)、E6 `traffic_rules`(in)、E7 `warning`(out)、E8 `checked_cmd`(out)、E9 `actuator_cmd`(in，见 O-1)。
- **数据存储（恰好 4 个）**：D1 `HDMapSegment`、D2 `ObjectTrackTable`、D3 `EgoState`、D4 `TrafficRules`。
- **外部流**：E1→F1；E2→F1；E3→F3；E4→F4；E5→D1（刷新，写者未指定 O-2）；E6→D4（刷新，O-2）；F3→E7 `warning`；F7→E8 `checked_cmd`；E9 为 F6→F7 流 `actuator_cmd` 在边界上的同一命名表示（O-1）。
- **功能间流（§5.1 强制清单）**：F1→F2 `ego_pose`；F1→F2 `object_table`；F1→F4 `ego_pose`；F2→F3 `predicted_trajectories`；F2→F5 `predicted_trajectories`；F3→F5 `maneuver`；F4→F3 `route`；F4→F5 `route`；F5→F6 `trajectory`；F6→F7 `actuator_cmd`。
- **按 §5 输入条款补齐的显式流**：F1→F3 `ego_state`、F1→F5 `ego_state`（O-4）。
- **存储读写**：rd: F1→D1、F2→D1、F3→D1、F3→D4、F4→D1、F5→D1、F5→D4、F6→D3、F7→D3、F7→D4；wr: F1→D2、F1→D3。
- **扇出说明**：F2 与 F4 的输出按 §5.1 明确同时供给两个消费者，故画成两条同名有向流，各自单一生产者/单一消费者（R-G-4）。

### Level 1 — AEB_Branch

- **元素**：F3.1、F3.2、F3.3；存储 D1、D4（只读）；外部终端 E3(in)、E7(out)；另有来自 Level-0 F1/F2/F4 的边界继承流（非新增终端）。
- **连线**：F2(边界)→F3.1 `predicted_trajectories`；F1(边界)→F3.1 `ego_state`；F3.1→F3.2 `ttc_set`；D4→F3.2 读；F3.2→E7 `warning`；F3.2→F3.3 `risk`；F1(边界)→F3.3 `ego_state`；E3→F3.3 `driver_intent`；F4(边界)→F3.3 `route`；D1→F3.3 读；F3.3→F5(边界) `maneuver`。

## 4. Open issues

1. **O-1** E9 在 §3 为 in，但 §5.1 规定由 F6 产生、F7 消费；本次按“边界别名”处理，不引入第二生产者；方向语义待确认（R-E-2/R-G-4）。
2. **O-2** §4 说 D1/D4 由 E5/E6 刷新，但没有任何函数被授予对 D1/D4 的写权限（§5 中 F5/F1 为 D1 owner 却禁写，F1 仅写 D2/D3）。现画为外部终端→存储刷新流，写者待定（R-D-1）。
3. **O-3** 对象数为 0 时 `minimum_ttc` 的取值未定义；现建模决定为“空集→no_risk”，TTC 哨兵值待定（§6 F3.1/F3.2）。
4. **O-4** F1→F3、F1→F5 的 `ego_state` 仅见于 §5 输入条款，未列入 §5.1 强制清单；为消除隐式依赖而补线，待确认（R-G-4）。
5. **O-5** N-5 的 `d_min` 公式（RSS Eq.1）未在规格中给出，仅以符号 `d_min` + A-2 参数引用，需集成方提供公式。
6. **O-6** N-7 的横向加速度能力无数值；只给出 A-6 转向包线 ±1.0 与定性约束，量化阈值待补。
7. **O-7** “F7 强制交通规则（D4）”未给出信号态→命令的映射；现以 D4 读守卫下的纵向约束表达，属定性处理。
8. **O-8** A-1（6.0 m/s²）与 A-3（3.0 m/s²）、A-2 的 `a_min,brake=4.0` 存在量级冲突；本次将紧急减速放在 `brake`/`required_deceleration` 字段、A-3 放在 `longitudinal_accel` 字段以避开矛盾，语义需确认。
9. **O-9** A-2 的 `a_max,accel=2.0` 限定在响应时间内，但规格无任何时间/周期模型；现作无时间限定的上界处理。
10. **O-10** 速度单位（E3/E6/N-1 为 km/h）与加速度单位（m/s²）混用；字段约定 speed/max_speed 为 km/h、加速度为 m/s²，`brake` 为非负幅值，`longitudinal_accel` 正向为加速。
11. **O-11** 禁止 `seq of` 下，`objects`、`trajectories` 用名义聚合字段表示逐对象集合，基数由 `object_count`/`trajectory_count` 给出。
12. **O-12** §8 A-5 引用了未定义的 **R-F2-1**；本次将其理解为 F2 预测 horizons ≥3.0 s（A-7）。
13. **O-13** 字符串枚举值（route_preferences、lane_topology、traffic_signal_state、lane_geometry、warning_type 中 “imminent collision” 的写法）未在规格中定值。
14. **O-14** Level-1 F3.1 “compute TTC” 与 §5 “F2 是唯一计算 TTC 的函数”冲突；现按 F2 已在轨迹中提供逐对象 TTC、F3.1 仅取最小值与计数处理。

**§11 指定回答**：

1. 维持七功能拆分——L2 驾驶员注意状态已由 E3 进入 F3，R-L0-1 禁止新增功能；但 L2 交接时序未规定。
2. D3 由 F1 写、F6/F7 读在 §5.1 中明确授权，可接受。
3. 需要周期时间约束才使紧急分支有意义，规格未给，本模型不加。
4. Level 1 细化 F3 是 §6 明确规定，不改为 F6/F7。

## 5. 可追溯性说明（R-xx / N / A → 模型元素）

| 条款 | 对应元素 |
|---|---|
| R-SCOPE-1/2/3 | 两 module 头注释；E1–E9 仅为外部终端；process 仅黑盒契约 |
| R-SCOPE-4 | `ADAS_System` 与 `AEB_Branch` 两个 module |
| R-E-1 | 两 module 出端口仅 `warning`、`checked_cmd` |
| R-E-2 | F6→F7 `actuator_cmd`、F7 `checked_cmd` 契约、O-1 |
| R-D-1 | F1 的 `ext wr` D2/D3；D1/D4 刷新见 O-2 |
| R-D-2 | 各 process 的 `ext rd` 与 §5.1 读清单逐项一致 |
| R-L0-1 | Level 0 的 F1–F7、D1–D4、E1–E9 |
| R-L1-1 | F3.1 / F3.2 / F3.3 及三条内部流 |
| R-F2-1（§8 引用） | F2 `horizon >= 3.0`、O-12 |
| R-G-1 | 全部 process 的 pre/post；无阈值者（F4/F3.1/部分 F7）给定性 post |
| R-G-2 | 本表 |
| R-G-3 | 全部建模便利项见 O-1…O-14 |
| R-G-4 | CDFD 全部命名有向流；扇出与边界别名见 O-1/O-4 |
| R-G-5 | 每个输出均有规格指定消费者（F3.1→F3.2→F3.3；F6→F7；F7→E8） |
| R-G-6 | 各 pre 中的自等式非空守卫（如 `ttc_set.minimum_ttc = ttc_set.minimum_ttc`） |
| N-1 | F3、F3.3 中 `speed <= 130` 守卫 |
| N-2 | F3、F3.2 中 `minimum_ttc <= 2.0 → warning.active = 1` |
| N-3 / N-4 | A-1 的推导依据 → F3.3、F5 的 `>= 6.0` |
| N-5 | F2 `longitudinal_distance >= d_min`、O-5 |
| N-6 | F5 `required_deceleration >= 4.0`、`max_accel <= 2.0`；F6/F7 `brake >= 4.0` |
| N-7 | F5/F7 定性包线 + A-6 转向约束、O-6 |
| A-1 | F3、F3.3、F5 的 `6.0` |
| A-2 | F5/F7 的 `4.0`/`2.0`；`d_min` 参数集、O-5/O-9 |
| A-3 | F6/F7 `longitudinal_accel <= 3.0`、O-8 |
| A-4 | F1 `yaw_rate <= 3.5` |
| A-5 | F3、F3.2 的 `3.0`/`1.5` 风险分界 |
| A-6 | F6 与 F7 的 `steering <= 1.0 / >= -1.0` |
| A-7 | F2 `horizon >= 3.0` |

关键未决点集中在：E9 方向（O-1）、D1/D4 刷新写者（O-2）、空对象集 TTC（O-3）、`d_min` 公式（O-5）以及 A-1/A-3 的量级冲突（O-8）。这些均未用规格外数值填补。
