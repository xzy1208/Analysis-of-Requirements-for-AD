# NL-RQ-ADAS-v1 — SOFL Formal Specification (Model M1)

**Generating model:** MiniMax-M3.1-Flash
**Input document (sole source):** `NL-RQ-ADAS-v1_spec.md` (v1.0, baseline input)
**Deliverable:** SOFL model — Level 0 module `ADAS_System`, Level 1 module `AEB_Branch`
**Rule applied:** only what the specification states is modelled. Every silence is recorded in
§4 (open issues), never silently filled.

---

## 0. Modelling conventions (read first)

These conventions are *notation* choices, not new content. They are listed here so that the
contracts can be read unambiguously.

| # | Convention | Reason |
|---|---|---|
| C1 | Units: speed in **m/s**, acceleration in **m/s²**, time in **s**, distance in **m**. Normative km/h values are converted (1 km/h = 1/3.6 m/s): 130 → `36.1111`, 60 → `16.6667`, 20 → `5.5556`, 30 → `8.3333`. | §7/§8 mix km/h and m/s²; a single unit system is required for the comparisons in F5/F7. Unit of the *posted speed limit* is not stated by the specification → OISS-12. |
| C2 | Every datum carries a field `present: nat` (1 = present, 0 = null). | Required by R-G-6 (null-safety). No other content is implied by the flag. |
| C3 | `present` guards: any `post` that reads a field of an **input** datum *X* is guarded by `X.present = 1`. Output datums are governed by the `post <out>.present = 1` clause. | R-G-6. |
| C4 | A field whose declared content is not enumerated by the specification carries an opaque payload (`String`) or a `count` + `entries` list pair. | R-SCOPE-3 (no algorithm internals); avoids inventing structure. |
| C5 | `entries` is a list of the declared element type; `count` is its length. | Readability. |
| C6 | Boolean-ish signals (`validity flags`, `override_accelerate/brake`, `warning.active`) are encoded as `nat` 0/1. | The permitted type vocabulary is `real`, `nat`, `String`. |
| C7 | Operator set used in `pre`/`post`: `and`, `=`, `<>`, `>`, `>=`, `<=`, `<`, dot-field access. **No** `or`, `not`, `=>`, quantifiers, `seq of`. Where the specification states a disjunction (e.g. "cruise/keep-lane") it is encoded as the exclusion of the alternatives that must *not* hold → OISS-13. |
| C8 | Store declarations use `store <id>: <Type>`; the module head declares the external interfaces E1–E9. | The requested notation did not cover store declarations. |
| C9 | Module `AEB_Branch` imports the datum types it shares with `ADAS_System` (explicit import list) and declares only the types it introduces. | Keeps the two modules consistent without duplicating 25 declarations. |

---

## 1. Module `ADAS_System` — Level 0

### 1.1 Module head (external interfaces E1–E9)

Table columns = `[input port group] [output port 1] [output port 2]`; `|` separates ports/entries,
`,` separates several flows inside one port.

```sofl
module ADAS_System

|  |  |  |
| --- | --- | --- |
| ( E1_raw_sensor_data: RawSensorData | E2_gnss_imu: GnssImuData | E3_driver_intent: DriverIntent | E4_destination: Destination | E5_map_data: MapSegment | E6_traffic_rules: TrafficRules | E9_actuator_cmd: ActuatorCmd ) | E7_warning: WarningSignal | E8_checked_cmd: CheckedCmd
```

### 1.2 Type declarations

```sofl
Validity = composed of
  present: nat,
  valid_count: nat
end

RawSensorData = composed of
  present: nat,
  sensor_frames: SensorFrames,
  validity: Validity,
  timestamps: Timestamps
end

SensorFrames = composed of
  present: nat,
  payload: String
end

Timestamps = composed of
  present: nat,
  frame_time: real
end

GnssImuData = composed of
  present: nat,
  gnss_fix: GnssFix,
  imu_samples: ImuSamples,
  validity: Validity
end

GnssFix = composed of
  present: nat,
  longitude: real,
  latitude: real,
  heading: real
end

ImuSamples = composed of
  present: nat,
  angular_rate: real,
  acceleration: real
end

DriverIntent = composed of
  present: nat,
  requested_cruise_speed: real,
  override_accelerate: nat,
  override_brake: nat,
  override_steer: real,
  attention_state: String
end

Destination = composed of
  present: nat,
  longitude: real,
  latitude: real,
  route_preferences: String
end

MapSegment = composed of
  present: nat,
  road_id: String,
  lane_id: String,
  posted_speed_limit: real,
  curvature: real,
  lane_topology: String
end

TrafficRules = composed of
  present: nat,
  posted_speed_limit: real,
  signal_state: String
end

EgoPose = composed of
  present: nat,
  pose_x: real,
  pose_y: real
end

EgoState = composed of
  present: nat,
  pose: EgoPose,
  speed: real,
  yaw_rate: real,
  acceleration: real,
  last_update: real
end

ObjectPosition = composed of
  present: nat,
  x: real,
  y: real
end

ObjectVelocity = composed of
  present: nat,
  vx: real,
  vy: real
end

ObjectEntry = composed of
  present: nat,
  object_id: String,
  position: ObjectPosition,
  velocity: ObjectVelocity,
  object_class: String
end

ObjectList = composed of
  present: nat,
  count: nat,
  entries: ObjectEntry
end

LeadObject = composed of
  present: nat,
  object_id: String,
  position: ObjectPosition,
  velocity: ObjectVelocity,
  object_class: String
end

ObjectTable = composed of
  present: nat,
  object_count: nat,
  objects: ObjectList,
  lead_object: LeadObject
end

TrajectorySample = composed of
  present: nat,
  t: real,
  x: real,
  y: real,
  vx: real,
  vy: real
end

SampleList = composed of
  present: nat,
  count: nat,
  entries: TrajectorySample
end

ObjectTrajectory = composed of
  present: nat,
  object_id: String,
  samples: SampleList
end

TrajectoryList = composed of
  present: nat,
  count: nat,
  entries: ObjectTrajectory
end

PredictedTrajectories = composed of
  present: nat,
  horizon: real,
  trajectories: TrajectoryList,
  min_ttc: real
end

LaneGeometry = composed of
  present: nat,
  lane_count: nat,
  lane_ids: String
end

Route = composed of
  present: nat,
  path_length: real,
  eta: real,
  lane_geometry: LaneGeometry
end

Manoeuvre = composed of
  present: nat,
  manoeuvre_type: String,
  target_speed: real,
  target_lane: String,
  required_deceleration: real
end

Trajectory = composed of
  present: nat,
  max_permitted_speed: real,
  max_permitted_acceleration: real,
  horizon_duration: real
end

ActuatorCmd = composed of
  present: nat,
  longitudinal_acceleration: real,
  brake_command: real,
  steering_command: real
end

CheckedCmd = composed of
  present: nat,
  longitudinal_acceleration: real,
  brake_command: real,
  steering_command: real
end

WarningSignal = composed of
  present: nat,
  warning_type: String,
  active: nat
end
```

### 1.3 Data stores

```sofl
store D1: MapSegment      # HD Map Store        - content refreshed by E5        (§4)
store D2: ObjectTable     # Object Track Store  - written by F1                 (§4)
store D3: EgoState        # Ego State Store     - written by F1                 (§4)
store D4: TrafficRules    # Traffic Rules Store - content refreshed by E6        (§4)
```

### 1.4 Process contracts (F1–F7)

```sofl
process F1_Perception_Localisation(raw_sensor_data: RawSensorData, gnss_imu: GnssImuData) out: object_table: ObjectTable, ego_state: EgoState, ego_pose: EgoPose
ext rd D1
ext wr D2
ext wr D3
pre raw_sensor_data.present = 1
pre gnss_imu.present = 1
pre raw_sensor_data.validity.valid_count > 0
pre gnss_imu.validity.valid_count > 0
post object_table.present = 1
post object_table.object_count = object_table.objects.count
post object_table.lead_object.object_id <> ""
post ego_state.present = 1
post ego_state.speed >= 0.0
post ego_state.yaw_rate <= 3.5
post ego_state.yaw_rate >= -3.5
post ego_state.last_update > 0.0
post ego_pose.present = 1
post ego_pose.pose_x = ego_state.pose.pose_x
post ego_pose.pose_y = ego_state.pose.pose_y
end_process

process F2_Prediction(object_table: ObjectTable, ego_state: EgoState) out: predicted_trajectories: PredictedTrajectories
ext rd D1
pre object_table.present = 1
pre ego_state.present = 1
pre object_table.object_count >= 0
post predicted_trajectories.present = 1
post predicted_trajectories.horizon >= 3.0
post predicted_trajectories.min_ttc >= 0.0
post predicted_trajectories.min_ttc <= predicted_trajectories.horizon
post predicted_trajectories.trajectories.count <= object_table.object_count
end_process

process F3_Behaviour_Planning(ego_state: EgoState, predicted_trajectories: PredictedTrajectories, driver_intent: DriverIntent, route: Route) out: manoeuvre: Manoeuvre, warning: WarningSignal
ext rd D1
ext rd D4
pre ego_state.present = 1
pre predicted_trajectories.present = 1
pre driver_intent.present = 1
pre route.present = 1
post manoeuvre.present = 1
post warning.present = 1
post manoeuvre.manoeuvre_type <> ""
post manoeuvre.target_speed >= 0.0
post manoeuvre.required_deceleration >= 0.0
post if D4.present = 1 and D4.posted_speed_limit > 0.0 then manoeuvre.target_speed <= D4.posted_speed_limit
post if predicted_trajectories.present = 1 and predicted_trajectories.min_ttc > 3.0 then warning.warning_type = "none"
post if predicted_trajectories.present = 1 and predicted_trajectories.min_ttc > 1.5 and predicted_trajectories.min_ttc <= 3.0 then warning.warning_type = "caution"
post if predicted_trajectories.present = 1 and predicted_trajectories.min_ttc <= 1.5 then warning.warning_type = "imminent collision"
post if warning.warning_type = "none" then warning.active = 0
post if warning.warning_type = "caution" then warning.active = 1
post if warning.warning_type = "imminent collision" then warning.active = 1
post if predicted_trajectories.present = 1 and predicted_trajectories.min_ttc <= 2.0 then warning.active = 1
post if predicted_trajectories.present = 1 and predicted_trajectories.min_ttc > 3.0 then manoeuvre.required_deceleration = 0.0
post if predicted_trajectories.present = 1 and predicted_trajectories.min_ttc > 3.0 then manoeuvre.manoeuvre_type <> "lane-keeping-with-deceleration"
post if predicted_trajectories.present = 1 and predicted_trajectories.min_ttc > 3.0 then manoeuvre.manoeuvre_type <> "emergency deceleration"
post if predicted_trajectories.present = 1 and predicted_trajectories.min_ttc > 1.5 and predicted_trajectories.min_ttc <= 3.0 and driver_intent.present = 1 and driver_intent.override_accelerate = 0 then manoeuvre.required_deceleration > 0.0
post if predicted_trajectories.present = 1 and predicted_trajectories.min_ttc > 1.5 and predicted_trajectories.min_ttc <= 3.0 and driver_intent.present = 1 and driver_intent.override_accelerate = 1 then manoeuvre.required_deceleration = 0.0
post if predicted_trajectories.present = 1 and predicted_trajectories.min_ttc > 1.5 and predicted_trajectories.min_ttc <= 3.0 and driver_intent.present = 1 and driver_intent.override_accelerate = 0 then manoeuvre.manoeuvre_type = "lane-keeping-with-deceleration"
post if predicted_trajectories.present = 1 and predicted_trajectories.min_ttc > 1.5 and predicted_trajectories.min_ttc <= 3.0 and driver_intent.present = 1 and driver_intent.override_accelerate = 1 then manoeuvre.manoeuvre_type <> "lane-keeping-with-deceleration"
post if predicted_trajectories.present = 1 and predicted_trajectories.min_ttc <= 1.5 then manoeuvre.required_deceleration >= 6.0
post if predicted_trajectories.present = 1 and predicted_trajectories.min_ttc <= 1.5 then manoeuvre.target_speed = 0.0
post if predicted_trajectories.present = 1 and predicted_trajectories.min_ttc <= 1.5 then manoeuvre.manoeuvre_type = "emergency deceleration"
post if predicted_trajectories.present = 1 and predicted_trajectories.min_ttc <= 1.5 and driver_intent.present = 1 and driver_intent.override_accelerate = 1 then manoeuvre.required_deceleration >= 6.0
post if predicted_trajectories.present = 1 and predicted_trajectories.min_ttc <= 0.1 then manoeuvre.required_deceleration >= 4.0
post if predicted_trajectories.present = 1 and predicted_trajectories.min_ttc <= 1.5 and ego_state.present = 1 and ego_state.speed <= 36.1111 then manoeuvre.required_deceleration >= 6.0
post if predicted_trajectories.present = 1 and predicted_trajectories.min_ttc <= 1.5 and ego_state.present = 1 and ego_state.speed <= 36.1111 then manoeuvre.target_speed = 0.0
end_process

process F4_Route_Planning(destination: Destination, ego_pose: EgoPose) out: route: Route
ext rd D1
pre destination.present = 1
pre ego_pose.present = 1
pre destination.longitude >= -180.0
pre destination.longitude <= 180.0
pre destination.latitude >= -90.0
pre destination.latitude <= 90.0
post route.present = 1
post route.path_length >= 0.0
post route.eta >= 0.0
post route.lane_geometry.present = 1
post route.lane_geometry.lane_count >= 0
end_process

process F5_Motion_Planning(manoeuvre: Manoeuvre, route: Route, ego_state: EgoState) out: trajectory: Trajectory
ext rd D1
ext rd D4
pre manoeuvre.present = 1
pre route.present = 1
pre ego_state.present = 1
post trajectory.present = 1
post trajectory.max_permitted_speed >= 0.0
post trajectory.max_permitted_acceleration <= 3.0
post trajectory.max_permitted_acceleration >= -6.0
post trajectory.horizon_duration >= 0.0
post if D4.present = 1 and D4.posted_speed_limit > 0.0 then trajectory.max_permitted_speed <= D4.posted_speed_limit
post if manoeuvre.required_deceleration > 0.0 then trajectory.max_permitted_acceleration <= 0.0
post if manoeuvre.required_deceleration >= 6.0 then trajectory.max_permitted_acceleration <= -6.0
post if manoeuvre.required_deceleration > 0.0 then trajectory.max_permitted_speed <= manoeuvre.target_speed
end_process

process F6_Control(trajectory: Trajectory) out: actuator_cmd: ActuatorCmd
ext rd D3
pre trajectory.present = 1
pre D3.present = 1
post actuator_cmd.present = 1
post actuator_cmd.longitudinal_acceleration <= 3.0
post actuator_cmd.brake_command >= 0.0
post actuator_cmd.steering_command <= 1.0
post actuator_cmd.steering_command >= -1.0
post if trajectory.max_permitted_acceleration <= 0.0 then actuator_cmd.longitudinal_acceleration <= 0.0
post if trajectory.max_permitted_acceleration <= -6.0 then actuator_cmd.brake_command >= 6.0
end_process

process F7_Safety_Shield(actuator_cmd: ActuatorCmd) out: checked_cmd: CheckedCmd
ext rd D3
ext rd D4
pre actuator_cmd.present = 1
pre D3.present = 1
post checked_cmd.present = 1
post checked_cmd.longitudinal_acceleration <= 3.0
post checked_cmd.brake_command >= 0.0
post checked_cmd.steering_command <= 1.0
post checked_cmd.steering_command >= -1.0
post if actuator_cmd.steering_command >= -1.0 and actuator_cmd.steering_command <= 1.0 then checked_cmd.steering_command = actuator_cmd.steering_command
post if D3.present = 1 and D4.present = 1 and D4.posted_speed_limit > 0.0 and D3.speed > D4.posted_speed_limit then checked_cmd.longitudinal_acceleration <= 0.0
post if D4.present = 1 and D4.signal_state = "red" then checked_cmd.longitudinal_acceleration <= 0.0
end_process
```

### 1.5 Threshold placement inside the Level-0 contracts

| Threshold | Value used | Contract clause |
|---|---|---|
| N-1 | 130 km/h → `36.1111` m/s | `F3`: `min_ttc <= 1.5 and ego_state.speed <= 36.1111 ⇒ required_deceleration >= 6.0` |
| N-2 | TTC ≤ 2.0 s | `F3`: `min_ttc <= 2.0 ⇒ warning.active = 1` (and the A-5 caution band from 3.0 s) |
| N-3 | > 30 km/h impact-speed reduction | `F3`/`F3.3`: `required_deceleration >= 6.0` (the sizing target of A-1) |
| N-4 | closing speed 30.6 m/s, CCRb −4 m/s² | `F3`: `min_ttc <= 0.1 ⇒ required_deceleration >= 4.0` (brake authority used for the CCRb sizing) |
| N-5 | RSS `d_min` (Eq. (1) of [S4]) | `F3`: `min_ttc <= 0.1 ⇒ required_deceleration >= 4.0` (the RSS-unsafe implication that the operator set can express) → OISS-07 |
| N-6 | `a_min,brake` = 4.0, `a_max,accel` = 2.0, `ρ` = 0.1 s (A-2) | `F3`: `required_deceleration >= 4.0`; `F6`: `max_permitted_acceleration <= 0.0 ⇒ longitudinal_acceleration <= 0.0`; `F7`: `longitudinal_acceleration <= 3.0` |
| N-7 | lateral-acceleration envelope | `F6`/`F7`: `steering_command <= 1.0`, `>= -1.0`; `F1`: `yaw_rate <= 3.5`, `>= -3.5` → OISS-08 |
| A-1 | 6.0 m/s² | `F3`, `F3.3`, `F5` (`max_permitted_acceleration <= -6.0`) |
| A-2 | 0.1 / 2.0 / 4.0 / 4.0 | `F3` (`>= 4.0`), `F5` (`>= -6.0` from A-1), OISS-07 |
| A-3 | 3.0 m/s² | `F5` (`max_permitted_acceleration <= 3.0`), `F6`, `F7` (`longitudinal_acceleration <= 3.0`) |
| A-4 | 3.5 rad/s | `F1` (`yaw_rate <= 3.5`, `>= -3.5`) |
| A-5 | 3.0 s / 1.5 s | `F3`, `F3.2` (warning bands) |
| A-6 | ±1.0 | `F6`, `F7` (steering envelope; preservation clause in F7) |
| A-7 | 3.0 s | `F2` (`horizon >= 3.0`, `min_ttc <= horizon`) |

---

## 2. Module `AEB_Branch` — Level 1 (refinement of F3)

### 2.1 Module head

```sofl
module AEB_Branch

|  |  |  |
| --- | --- | --- |
| ( predicted_trajectories: PredictedTrajectories | ego_state: EgoState | driver_intent: DriverIntent | route: Route ) | E7_warning: WarningSignal | manoeuvre: Manoeuvre
```

### 2.2 Type declarations

Types shared with `ADAS_System` are imported, not re-declared:
`Validity, RawSensorData, SensorFrames, Timestamps, GnssImuData, GnssFix, ImuSamples, DriverIntent,
Destination, MapSegment, TrafficRules, EgoPose, EgoState, ObjectPosition, ObjectVelocity, ObjectEntry,
ObjectList, LeadObject, ObjectTable, TrajectorySample, SampleList, ObjectTrajectory, TrajectoryList,
PredictedTrajectories, LaneGeometry, Route, Manoeuvre, Trajectory, ActuatorCmd, CheckedCmd, WarningSignal`.

```sofl
ObjectTtc = composed of
  present: nat,
  object_id: String,
  ttc: real
end

ObjectTtcList = composed of
  present: nat,
  count: nat,
  entries: ObjectTtc
end

TtcSet = composed of
  present: nat,
  object_count: nat,
  min_ttc: real,
  object_ttcs: ObjectTtcList
end

RiskLevel = composed of
  present: nat,
  risk_class: String
end
```

### 2.3 Data stores

```sofl
store D1: MapSegment      # read by F3.3                      (§5.1: F3 reads D1)
store D4: TrafficRules    # read by F3.2                      (§6: F3.2 inputs D4)
```

### 2.4 Process contracts (F3.1 → F3.2 → F3.3)

```sofl
process F3.1_TTC_Computation(predicted_trajectories: PredictedTrajectories, ego_state: EgoState) out: ttc_set: TtcSet
pre predicted_trajectories.present = 1
pre ego_state.present = 1
post ttc_set.present = 1
post ttc_set.object_count = predicted_trajectories.trajectories.count
post if predicted_trajectories.present = 1 and ttc_set.object_count = 0 then ttc_set.min_ttc = 0.0
post if predicted_trajectories.present = 1 and ttc_set.object_count > 0 then ttc_set.min_ttc >= 0.0
post if predicted_trajectories.present = 1 and ttc_set.object_count > 0 then ttc_set.min_ttc <= predicted_trajectories.horizon
post if predicted_trajectories.present = 1 and ttc_set.object_count > 0 then ttc_set.min_ttc <= predicted_trajectories.min_ttc
post if predicted_trajectories.present = 1 and ttc_set.object_count > 0 then ttc_set.object_ttcs.count = ttc_set.object_count
end_process

process F3.2_Risk_Classification(ttc_set: TtcSet) out: risk_level: RiskLevel, warning: WarningSignal
ext rd D4
pre ttc_set.present = 1
post risk_level.present = 1
post warning.present = 1
post if ttc_set.present = 1 and ttc_set.min_ttc > 3.0 then risk_level.risk_class = "no risk"
post if ttc_set.present = 1 and ttc_set.min_ttc <= 3.0 and ttc_set.min_ttc > 1.5 then risk_level.risk_class = "caution"
post if ttc_set.present = 1 and ttc_set.min_ttc <= 1.5 then risk_level.risk_class = "critical"
post if risk_level.risk_class = "no risk" then warning.warning_type = "none"
post if risk_level.risk_class = "caution" then warning.warning_type = "caution"
post if risk_level.risk_class = "critical" then warning.warning_type = "imminent collision"
post if risk_level.risk_class = "no risk" then warning.active = 0
post if risk_level.risk_class = "caution" then warning.active = 1
post if risk_level.risk_class = "critical" then warning.active = 1
post if warning.active = 1 then warning.warning_type <> "none"
post if warning.active = 0 then warning.warning_type = "none"
post if ttc_set.present = 1 and ttc_set.min_ttc <= 2.0 then warning.active = 1
end_process

process F3.3_Maneuver_Planning(risk_level: RiskLevel, ego_state: EgoState, driver_intent: DriverIntent, route: Route) out: manoeuvre: Manoeuvre
ext rd D1
pre risk_level.present = 1
pre ego_state.present = 1
pre driver_intent.present = 1
pre route.present = 1
post manoeuvre.present = 1
post manoeuvre.manoeuvre_type <> ""
post manoeuvre.target_speed >= 0.0
post manoeuvre.required_deceleration >= 0.0
post if risk_level.risk_class = "no risk" then manoeuvre.required_deceleration = 0.0
post if risk_level.risk_class = "no risk" then manoeuvre.manoeuvre_type <> "lane-keeping-with-deceleration"
post if risk_level.risk_class = "no risk" then manoeuvre.manoeuvre_type <> "emergency deceleration"
post if risk_level.risk_class = "caution" and driver_intent.present = 1 and driver_intent.override_accelerate = 0 then manoeuvre.required_deceleration > 0.0
post if risk_level.risk_class = "caution" and driver_intent.present = 1 and driver_intent.override_accelerate = 0 then manoeuvre.manoeuvre_type = "lane-keeping-with-deceleration"
post if risk_level.risk_class = "caution" and driver_intent.present = 1 and driver_intent.override_accelerate = 1 then manoeuvre.required_deceleration = 0.0
post if risk_level.risk_class = "caution" and driver_intent.present = 1 and driver_intent.override_accelerate = 1 then manoeuvre.manoeuvre_type <> "lane-keeping-with-deceleration"
post if risk_level.risk_class = "caution" and driver_intent.present = 1 and driver_intent.override_accelerate = 1 then manoeuvre.manoeuvre_type <> "emergency deceleration"
post if risk_level.risk_class = "critical" then manoeuvre.required_deceleration >= 6.0
post if risk_level.risk_class = "critical" then manoeuvre.target_speed = 0.0
post if risk_level.risk_class = "critical" then manoeuvre.manoeuvre_type = "emergency deceleration"
post if risk_level.risk_class = "critical" and driver_intent.present = 1 and driver_intent.override_accelerate = 1 then manoeuvre.required_deceleration >= 6.0
post if risk_level.risk_class = "critical" and ego_state.present = 1 and ego_state.speed <= 36.1111 then manoeuvre.required_deceleration >= 6.0
post if risk_level.risk_class = "critical" and ego_state.present = 1 and ego_state.speed <= 36.1111 then manoeuvre.target_speed = 0.0
post if D1.present = 1 and D1.lane_id <> "" then manoeuvre.target_lane <> ""
end_process
```

---

## 3. CDFD — elements and connections

### 3.1 `ADAS_System` (Level 0)

**Elements**

| Kind | ID | Name / content |
|---|---|---|
| External terminal (in) | E1 | `raw_sensor_data` — RawSensorData |
| External terminal (in) | E2 | `gnss_imu` — GnssImuData |
| External terminal (in) | E3 | `driver_intent` — DriverIntent |
| External terminal (in) | E4 | `destination` — Destination |
| External terminal (in) | E5 | `map_data` — MapSegment |
| External terminal (in) | E6 | `traffic_rules` — TrafficRules |
| External terminal (in) | E9 | `actuator_cmd` — ActuatorCmd (raw command, pre-arbitration) |
| External terminal (out) | E7 | `warning` — WarningSignal |
| External terminal (out) | E8 | `checked_cmd` — CheckedCmd |
| Process | F1 | Perception & Localisation |
| Process | F2 | Prediction |
| Process | F3 | Behaviour Planning |
| Process | F4 | Route Planning |
| Process | F5 | Motion Planning |
| Process | F6 | Control |
| Process | F7 | Safety Shield (monitoring & arbitration) |
| Data store | D1 | HD Map Store — MapSegment |
| Data store | D2 | Object Track Store — ObjectTable |
| Data store | D3 | Ego State Store — EgoState |
| Data store | D4 | Traffic Rules Store — TrafficRules |

Counts: 9 external interfaces, 7 processes, 4 stores — exactly the elements of R-L0-1, no more.

**Connections**

| # | From | To | Flow (type) | Kind |
|---|---|---|---|---|
| 1 | E1 | F1 | `raw_sensor_data` (RawSensorData) | data flow |
| 2 | E2 | F1 | `gnss_imu` (GnssImuData) | data flow |
| 3 | E5 | D1 | `map_data` → D1 content (MapSegment) | store write |
| 4 | E6 | D4 | `traffic_rules` → D4 content (TrafficRules) | store write |
| 5 | D1 | F1 | `map_segment` (MapSegment) | store read |
| 6 | D1 | F2 | `map_segment` (MapSegment) | store read |
| 7 | D1 | F3 | `map_segment` (MapSegment) | store read |
| 8 | D1 | F4 | `map_segment` (MapSegment) | store read |
| 9 | D1 | F5 | `map_segment` (MapSegment) | store read |
| 10 | D4 | F3 | `traffic_rules` (TrafficRules) | store read |
| 11 | D4 | F5 | `traffic_rules` (TrafficRules) | store read |
| 12 | D4 | F7 | `traffic_rules` (TrafficRules) | store read |
| 13 | F1 | D2 | `object_table` (ObjectTable) | store write |
| 14 | F1 | D3 | `ego_state` (EgoState) | store write |
| 15 | F1 | F2 | `ego_state` (EgoState) — carries the ego pose | data flow |
| 16 | F1 | F2 | `object_table` (ObjectTable) | data flow |
| 17 | F1 | F3 | `ego_state` (EgoState) | data flow — see OISS-01 |
| 18 | F1 | F4 | `ego_pose` (EgoPose) | data flow |
| 19 | F1 | F5 | `ego_state` (EgoState) | data flow — see OISS-01 |
| 20 | E3 | F3 | `driver_intent` (DriverIntent) | data flow |
| 21 | E4 | F4 | `destination` (Destination) | data flow |
| 22 | F2 | F3 | `predicted_trajectories` (PredictedTrajectories) | data flow |
| 23 | F2 | F5 | `predicted_trajectories` (PredictedTrajectories) | data flow |
| 24 | F3 | F5 | `manoeuvre` (Manoeuvre) | data flow |
| 25 | F3 | E7 | `warning` (WarningSignal) | data flow (system output) |
| 26 | F4 | F3 | `route` (Route) | data flow |
| 27 | F4 | F5 | `route` (Route) | data flow |
| 28 | F5 | F6 | `trajectory` (Trajectory) | data flow |
| 29 | F6 | E9 | `actuator_cmd` (ActuatorCmd) | data flow → external interface E9 |
| 30 | E9 | F7 | `actuator_cmd` (ActuatorCmd) | data flow (external interface E9) |
| 31 | F7 | E8 | `checked_cmd` (CheckedCmd) | data flow (system output) |

Store edges are consistent with the `ext rd` / `ext wr` declarations of §1.4: writes exist only for
D2 and D3 (both F1); reads exist for D1 (F1–F5), D3 (F6, F7), D4 (F3, F5, F7) — exactly §5.1.

### 3.2 `AEB_Branch` (Level 1)

**Elements**

| Kind | ID | Name / content |
|---|---|---|
| External terminal (in) | — | `predicted_trajectories` (PredictedTrajectories) — from F2 |
| External terminal (in) | — | `ego_state` (EgoState) — from F1 |
| External terminal (in) | E3 | `driver_intent` (DriverIntent) |
| External terminal (in) | — | `route` (Route) — from F4 |
| External terminal (out) | E7 | `warning` (WarningSignal) |
| External terminal (out) | — | `manoeuvre` (Manoeuvre) — to F5 |
| Process | F3.1 | TTC Computation |
| Process | F3.2 | Risk Classification |
| Process | F3.3 | Maneuver Planning |
| Data store | D1 | HD Map Store — MapSegment (read by F3.3) |
| Data store | D4 | Traffic Rules Store — TrafficRules (read by F3.2) |

**Connections**

| # | From | To | Flow (type) | Kind |
|---|---|---|---|---|
| 1 | `predicted_trajectories` | F3.1 | PredictedTrajectories | data flow |
| 2 | `ego_state` | F3.1 | EgoState | data flow |
| 3 | F3.1 | F3.2 | `ttc_set` (TtcSet) | data flow |
| 4 | D4 | F3.2 | `traffic_rules` (TrafficRules) | store read |
| 5 | F3.2 | F3.3 | `risk_level` (RiskLevel) | data flow |
| 6 | F3.2 | E7 | `warning` (WarningSignal) | data flow (system output) |
| 7 | `ego_state` | F3.3 | EgoState | data flow |
| 8 | E3 | F3.3 | `driver_intent` (DriverIntent) | data flow |
| 9 | `route` | F3.3 | Route | data flow |
| 10 | D1 | F3.3 | `map_segment` (MapSegment) | store read |
| 11 | F3.3 | `manoeuvre` | Manoeuvre → F5 | data flow (system output) |

---

## 4. Open issues

Every item is a place where the specification is silent, ambiguous, or self-contradictory. Nothing
here has been "fixed" by invention in the model.

| ID | Issue | Modelling decision taken | Impact |
|---|---|---|---|
| OISS-01 | §5 F3 and F5 list "ego state" among their inputs, but §5.1's mandatory dependency list contains neither `F1 → F3` nor `F1 → F5`, and its store-read list gives F3 only D1/D4 and F5 only D1/D4 (so neither may read D3 — R-D-2). | The ego state reaches F3 and F5 through explicit flows `F1 → F3` and `F1 → F5` (connections 17 and 19), justified by the §5 input lists. Reading D3 instead would violate §5.1 and R-D-2. | Two flows beyond the §5.1 list; flagged for the comparison of the four models. |
| OISS-02 | §5.1 says "F1 → F2: ego pose and object table", §5 F2 says "Inputs: object table, ego state". | `F1 → F2` carries `ego_state` (which embeds the ego pose) plus `object_table`; `ego_pose` as a separate datum is delivered only to F4, whose §5 input is "ego pose". | Naming difference only; no data is invented. |
| OISS-03 | D1 lists **two** owner functions ("F5 / F1", §4), which contradicts R-D-1 ("a store's content shall be written only by its owner function"). | No internal function writes D1; the refresh is modelled as the external write flow `E5 → D1`, as stated in D1's lifetime column ("refreshed by E5"). | D1 is write-only from inside the system. |
| OISS-04 | D4's owner is "F5" (§4), but §5 F5 states "F5 shall not write any store". Direct contradiction. | Same resolution as OISS-03: external write flow `E6 → D4` ("refreshed by E6"); F5 only reads D4. | D4 is write-only from inside the system. |
| OISS-05 | §5 F2: "F2 shall be the **only** function that computes TTC" vs §6 F3.1, which computes a TTC per object and reports the minimum. | Both are modelled as written (F2 in Level 0, F3.1 in Level 1); F3.1's minimum is constrained to be ≤ F2's minimum, but the specification states no precedence or sharing rule between the two. | Possible duplicate computation of the same quantity; undecided upstream. |
| OISS-06 | A-1 sizes the emergency deceleration at **6.0 m/s²**, while A-3 makes 3.0 m/s² the "upper bound of the longitudinal actuation envelope used by F6/F7". A-2's `a_max,brake` = 4.0 m/s² is a third candidate brake limit. | A-3 is applied literally as an **upper** bound of the longitudinal acceleration command (`<= 3.0`); the brake command magnitude is left unbounded above because §7/§8 give no actuator limit for it. The contracts are therefore satisfiable, but the gap between the demanded 6.0 m/s² and the envelope is unresolved. | If A-3 (or 4.0) is the real actuator ceiling, the N-3 target (impact-speed reduction > 30 km/h) is unreachable — the specification does not say which threshold wins. |
| OISS-07 | N-5 requires the RSS minimum safe distance `d_min` of Eq. (1) of [S4], i.e. an **arithmetic** expression over ego speed and the A-2 parameter set. The permitted operator set (`and`, `=`, `<>`, `>`, `>=`, `<=`, `<`, dot access) contains no arithmetic operator. | N-5 is expressed through the implication that the operator set *can* state: the RSS-safe condition `τ ≥ ρ + v/(2·a_min,brake)` is certainly violated when `τ ≤ ρ`, so `min_ttc <= 0.1 ⇒ required_deceleration >= 4.0`. The full margin (4.6139 s at 130 km/h with A-2) is not computable in the model. | N-5 is only partially formalised; it needs an arithmetic extension or an explicit RSS evaluation element. |
| OISS-08 | N-7 requires the commanded lateral acceleration to stay inside the vehicle's lateral-acceleration capability, but **no lateral-acceleration limit** appears in §7/§8 (A-4 is a yaw-rate envelope of 3.5 rad/s, stated as a localisation sanity check). Deriving lateral acceleration from a steering command also needs wheelbase/speed, which the specification does not provide. | N-7 is traced to the A-6 steering envelope in F6/F7 (including the "preserve the steering command" clause) and to the A-4 yaw-rate check in F1. | The lateral-acceleration envelope itself remains unquantified. |
| OISS-09 | §6 F3.2 lists D4 (traffic rules) as an input, but no rule in §6 uses it. Symmetrically, §5 requires F3 to "respect the applicable traffic rules (D4)", but F3.3 has no D4 access. | `ext rd D4` is kept in F3.2 and no rule is invented for it. At Level 0 the requirement is quantified as `target_speed <= D4.posted_speed_limit` (F3). | The Level-1 branch cannot enforce D4; a rule change in §6 is needed. |
| OISS-10 | §5.1 assigns store reads of D1 to F1, F2, F4, F5 (and F3), but no rule in §5/§5.1 says what any of them does with the map segment. | The reads are declared (`ext rd D1`) and no rule is invented. | Four processes read data they do not use — visible model smell, but spec-mandated. |
| OISS-11 | The traffic-signal state vocabulary is not enumerated in §3/§4 (E6/D4 only say "traffic-signal state"). | F7 uses the token `"red"` to express "no positive longitudinal acceleration at a red signal". The token is an added vocabulary item; no rule is stated for yellow/green/unknown. | Minor invented vocabulary, flagged. |
| OISS-12 | The unit of the *posted speed limit* (E5/E6, D1, D4) is never stated, while §7/§8 mix km/h (speeds) and m/s² (accelerations). | The model uses m/s throughout and converts the normative km/h values (130 → 36.1111, 60 → 16.6667, 20 → 5.5556, 30 → 8.3333). The F5/F7 comparisons against `posted_speed_limit` therefore assume m/s. | If the data supplies km/h, the F5/F7 comparisons are unit-mismatched. |
| OISS-13 | The permitted operator set has no `or`, so the two-valued outcome "cruise/keep-lane" (§6 F3.3) cannot be written as an enumeration. | Encoded as the exclusion of the two deceleration manoeuvre types, which leaves `cruise`, `keep-lane` **and** `lane-change` admissible in the no-risk band (the third type appears in §5's manoeuvre list). | A lane-change may remain possible in the no-risk band although §6 lists only cruise/keep-lane. |
| OISS-14 | The specification fixes thresholds but **no timing** (specification §11, question 3): "at every planning cycle" (§5 F3), "rebuilt each perception cycle" (D2) and the response time `ρ` (A-2, N-6) have no time dimension in the model. | No temporal constraint is expressed. N-6's "shall not accelerate above `a_max,accel` **during** ρ" is therefore modelled only through the deceleration demand, and the RSS-margin computation of OISS-07 loses its time argument. | The emergency branch cannot be shown to be *timely*; a cycle-time requirement is missing from the specification. |
| OISS-15 | E9 is listed in §3 as an external interface with direction **in**, while §5 F6 makes it the product of the control function *inside* the system; §5.1 draws it as `F6 → F7`. | E9 is modelled as the named flow between F6 and F7 (connections 29/30) and appears as an input port of the module head, as §3 prescribes. | None — a presentation decision that keeps §3 and §5.1 simultaneously satisfiable. |
| OISS-16 | The specification fixes the *semantics* of each datum, never its fields. The model therefore had to choose: the `present` flag (R-G-6), the aggregation of "per-sensor validity flags" into `valid_count`, the opaque `String` payloads for sensor frames / lane geometry / lane topology / route preferences, and the split of "velocity" into `vx`/`vy`. Also unspecified: whether `brake_command` is a normalised magnitude or a deceleration in m/s², and what happens when a raw signal violates the A-4 yaw-rate envelope (clip, flag or reject — the contract assumes the published value is inside the envelope). | All of these are declared as conventions C2–C6 in §0 and are visible in the type declarations. | Affects syntactic comparability across the four models; semantic content is unchanged. |
| OISS-17 | D2 is written by F1 but **no function is permitted to read it** (§5.1 assigns no read of D2), while the object table reaches F2 only through the direct flow `F1 → F2`. | D2 is modelled as a write-only store, exactly as §5.1 prescribes. | The persistent "short-term fusion" store has no consumer in the specified architecture. |
| OISS-18 | RSS time margin vs prediction horizon: with A-2 (`ρ` = 0.1 s, `a_min,brake` = 4.0 m/s²) the RSS margin is `0.1 + v/8`, i.e. 4.6139 s at the N-1 speed of 36.1111 m/s; A-7 caps the prediction horizon (and therefore the largest observable TTC) at 3.0 s. The margin exceeds the horizon already above v = 23.2 m/s (83.52 km/h). | Not "fixed": F2's contract states `min_ttc <= horizon` (= 3.0 s), F3 states the RSS-unsafe implication of OISS-07. | Above ≈83.5 km/h the model's TTC cannot certify RSS safety (N-5) — a substantive coverage gap, not a modelling artefact. |

### 4.1 Answers to the specification's own open questions (§11)

1. **Is the seven-function split sufficient for the stated ODD (or is a driver-monitoring function needed)?**
   For the *specified* scope — functional allocation and data dependencies (R-SCOPE-3) — the split is
   sufficient: every requirement clause maps onto the seven functions and every datum needed by them
   has a specified producer. A driver-monitoring function is **not** added, because R-L0-1 forbids
   additional elements. The L2 driver-monitoring / handover obligation (R-SCOPE-1) is nevertheless
   only *partially* covered: the driver-attention state arrives as E3 and is consumed by F3, but no
   function is required to act on a low-attention state — a scope gap in the specification, not in the
   model.
2. **Is it acceptable that D3 is written by F1 and read by F6/F7?**
   Yes, and it is consistent with the document: D3's owner is F1 (§4), R-D-1 forbids only *other*
   writers (there are none), and R-D-2 permits the reads because §5.1 explicitly assigns the D3 reads
   to F6 and F7. A dedicated writer would be an additional element and is therefore forbidden.
3. **Are thresholds without timing sufficient for the emergency branch?**
   No. A-1 was sized assuming ≈1.39 s of braking at 6.0 m/s² (N-3/N-4 derivation); the detection-to-
   command latency therefore has to be smaller than the remaining TTC margin, which the specification
   never bounds. Without a cycle-time requirement the emergency branch can be shown to be *correct*
   but not *timely*. This is recorded as OISS-14.
4. **Is the AEB branch of F3 the right Level-1 refinement?**
   Yes, for this specification: F3 is the only function that consumes the minimum TTC, and it is the
   only place where the warning type (§6), the driver-override precedence (§6) and the thresholds
   A-1/A-5 coincide; refining F6/F7 instead would leave the risk decision atomic. The one objection
   the document raises itself is that F2 is declared the *only* function computing TTC while F3.1 also
   computes it — recorded as OISS-05.

---

## 5. Traceability matrix

| Clause | Model element(s) | How it is realised |
|---|---|---|
| R-SCOPE-1 | `ADAS_System` (all 7 processes), module head | The vehicle-level onboard system is the module; no element exists outside it. |
| R-SCOPE-2 | module head E1–E9; no internal sensor/actuator element | Sensors, GNSS/IMU, HMI, driveline, V2X, cloud, infrastructure exist only as E1–E9. |
| R-SCOPE-3 | `SensorFrames.payload`, `LaneGeometry`, opaque payloads (C4) | No detector/tracker/planner/controller internals are modelled. |
| R-SCOPE-4 | two modules: `ADAS_System` (Level 0), `AEB_Branch` (Level 1) | Exactly one Level-0 function (F3) is refined; F1, F2, F4–F7 stay atomic. |
| R-E-1 | CDFD connections 25 and 31 | Only `F3 → E7` and `F7 → E8` leave the system. |
| R-E-2 | `F7_Safety_Shield` + connections 29/30/31 | E9 is consumed only by F7; only F7 produces E8. |
| R-D-1 | store declarations §1.3; `ext wr` only in F1 (D2, D3) | D1/D4 are refreshed by E5/E6 (OISS-03/04). |
| R-D-2 | `ext rd` lists: F1:D1, F2:D1, F3:D1+D4, F4:D1, F5:D1+D4, F6:D3, F7:D3+D4 | Identical to §5.1's store-read list. |
| R-L0-1 | element table §3.1 (9 + 7 + 4) | Exactly E1–E9, F1–F7, D1–D4. |
| R-L1-1 | `F3.1`, `F3.2`, `F3.3` in `AEB_Branch` | Exactly three sub-functions, chained F3.1 → F3.2 → F3.3. |
| R-G-1 | all 10 process contracts | Each has preconditions naming the required data, postconditions naming the produced data, and at least one quantified constraint (numeric) where §7/§8 give a threshold, otherwise a qualitative postcondition. |
| R-G-2 | this matrix | Every clause below is mapped to at least one element. |
| R-G-3 | element tables §3.1/§3.2 + open issues §4 | Each element is traced to a clause; every remaining choice is listed in §4. |
| R-G-4 | CDFD connection lists | Every flow is named, directed and single-consumer; the two shared producers (`route` → F3/F5, `predicted_trajectories` → F3/F5) are explicitly authorised by §5.1. |
| R-G-5 | CDFD connection lists | Each output is consumed only by the consumer named by §5/§5.1. |
| R-G-6 | `present: nat` in every datum; guarded `post` clauses (C2/C3) | Posts that read an input datum's fields are guarded by `X.present = 1`. |
| §5 F1 | `F1_Perception_Localisation`; writes D2/D3; reads D1 | Object table + lead object, ego state, ego pose published. |
| §5 F2 | `F2_Prediction`; reads D1; no `ext wr` | Horizon ≥ 3.0 s (A-7), minimum TTC derived; TTC computed only here at Level 0. |
| §5 F3 | `F3_Behaviour_Planning`; reads D1/D4; no `ext wr` | Manoeuvre (type, target speed, target lane, required deceleration) + warning E7; traffic rules and driver intent respected. |
| §5 F4 | `F4_Route_Planning`; reads D1; no `ext wr` | Route with path length, ETA, lane geometry. |
| §5 F5 | `F5_Motion_Planning`; reads D1/D4; no `ext wr` | Kinematic trajectory; speed ≤ posted limit (D4); deceleration demand honoured. |
| §5 F6 | `F6_Control`; reads D3 | Actuator command E9 inside the actuator envelope (A-3, A-6). |
| §5 F7 | `F7_Safety_Shield`; reads D3/D4 | Checked command E8; steering preserved unless out of envelope; traffic rules enforced. |
| §5.1 | CDFD connection lists §3.1 | All mandatory dependencies are drawn; two additions are justified in OISS-01. |
| §6 F3.1 | `F3.1_TTC_Computation` | TTC per object, minimum TTC, object count; count = 0 ⇒ min TTC = 0. |
| §6 F3.2 | `F3.2_Risk_Classification` | Risk bands on `T_risk_high` = 3.0 / `T_fcw` = 1.5 (A-5); warning raised for caution and critical only; reads D4. |
| §6 F3.3 | `F3.3_Maneuver_Planning` | cruise/keep-lane for no risk; non-zero deceleration for caution; ≥ 6.0 m/s² and target speed 0 for critical; driver-accelerate precedence except for critical; reads D1, uses E3 and route. |
| N-1 | `F3`, `F3.3` (`ego_state.speed <= 36.1111`) | AEB capability demanded up to 130 km/h. |
| N-2 | `F3`, `F3.2` (`min_ttc <= 2.0 ⇒ warning.active = 1`) | FCW present no later than TTC = 2.0 s. |
| N-3 | `F3`, `F3.3` (`required_deceleration >= 6.0`) | The deceleration sized for the 30 km/h impact-speed reduction. |
| N-4 | `F3` (`min_ttc <= 0.1 ⇒ required_deceleration >= 4.0`), `F3.3` | CCRm/CCRb sizing envelope (closing speed 30.6 m/s, brake authority 4.0 m/s²). |
| N-5 | `F3` (RSS-unsafe implication), `F2` (horizon), `AEB_Branch` `F3.1` | Partially formalised — OISS-07/OISS-18. |
| N-6 | `F3`, `F3.3` (`>= 4.0`, `>= 6.0`), `F6`, `F7` | `a_min,brake` braking demand; no positive acceleration in the emergency band; ρ-window not expressible (OISS-14). |
| N-7 | `F6`, `F7` (steering envelope), `F1` (A-4 yaw-rate) | Lateral-acceleration envelope itself unquantified — OISS-08. |
| A-1 | `F3`, `F3.3`, `F5` | 6.0 m/s² emergency deceleration. |
| A-2 | `F3`, `F5` | RSS parameter set (`ρ` = 0.1, `a_min,brake` = 4.0). |
| A-3 | `F5`, `F6`, `F7` | 3.0 m/s² longitudinal envelope upper bound (OISS-06). |
| A-4 | `F1` | 3.5 rad/s localisation sanity envelope. |
| A-5 | `F3`, `F3.2` | Risk thresholds 3.0 s / 1.5 s. |
| A-6 | `F6`, `F7` | Steering envelope ±1.0 and its preservation clause. |
| A-7 | `F2` | Prediction horizon 3.0 s. |
