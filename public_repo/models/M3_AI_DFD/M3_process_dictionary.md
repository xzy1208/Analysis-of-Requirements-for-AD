# M3 — Process Dictionary (DFD Semantic Externalisation)

This dictionary is the semantic annex of the two DFDs (`M3_L0.dot`, `M3_L1.dot`).
In Yourdon/DeMarco DFD the graphs carry only *structure* (processes, flows, stores,
externals); the *meaning* of each process is externalised here. This is an inherent
characteristic of the notation and is rendered explicitly for horizontal comparison.

## Expression conventions (restricted Boolean syntax)

* Allowed operators only: `=`, `<>`, `>`, `>=`, `<`, `<=`, `and`.
  The disjunction and negation operators are excluded throughout.
* Vacuous null-value guards are excluded: values are non-null by type in the
  source specification, so such a check would be meaningless. Real field
  constraints are used instead (e.g. `valid = 1`, `speed_limit >= 0`). The
  `>= 0` form is never applied to a `nat`-typed field.
* `guard` selects which `effect` fires; several guarded postconditions together
  express a conditional via mutually exclusive guards, with no disjunction.
* Numeric constants are taken **only** from specification §7 (N-1..N-7) and §8
  (A-1..A-7). No value is invented.

---

## Level 0 processes

### 1.0 / F1 — Perception & Localisation
* **Inputs:** `raw_sensor_data` (E1), `gnss_imu` (E2), `hd_map_segment` (D1 read).
* **Outputs:** `object_table` → D2 (write) and → F2; `ego_state` → D3 (write) and → F2, F3.
* **Preconditions:**
  - `raw_sensor_data.valid = 1`
  - `gnss_imu.valid = 1`
* **Postconditions:**
  - guard `true` → `ego_state.speed >= 0 and object_table.lead_velocity >= 0`
* **Processing rules:** Fuse E1 frames with per-sensor validity into a fused object
  table (id, position, velocity, class) and identify the lead object. Fuse E2 with
  vehicle motion signals to obtain ego pose, speed, yaw rate, acceleration. Write
  D2 and D3; never read D2 and D3. Yaw-rate sanity uses the A-4 envelope
  (`yaw_rate <= 3.5`). Qualitative postcondition (no §7/§8 threshold on this output).
* **quantified:** false

### 2.0 / F2 — Prediction
* **Inputs:** `object_table` (F1), `ego_state` (F1), `hd_map_segment` (D1 read).
* **Outputs:** `predicted_trajectories` → F3, F5.
* **Preconditions:**
  - `ego_state.speed >= 0`
  - `object_table.lead_velocity >= 0`
* **Postconditions:**
  - guard `true` → `predicted_trajectories.horizon >= 3.0 and min_ttc >= 0`
* **Processing rules:** For each relevant object predict future motion over a
  horizon of at least 3.0 s (A-7) and derive the minimum TTC to the ego vehicle.
  F2 is the only function that computes TTC. Writes no store.
* **quantified:** true (3.0 from A-7)

### 3.0 / F3 — Behaviour Planning
* **Inputs:** `ego_state` (F1), `traffic_rules` (D4 read), `predicted_trajectories`
  (F2), `driver_intent` (E3), `route` (F4), `hd_map_segment` (D1 read).
* **Outputs:** `manoeuvre` → F5; `warning` → E7.
* **Preconditions:**
  - `traffic_rules.speed_limit >= 0`
  - `driver_intent.requested_speed >= 0`
  - `route.path_length > 0`
* **Postconditions:**
  - guard `true` → `manoeuvre.target_speed >= 0 and manoeuvre.required_decel >= 0`
* **Processing rules:** Decide at every planning cycle the target manoeuvre
  (cruise / keep-lane / lane-change / lane-keeping-with-deceleration / emergency
  deceleration) as a type plus target speed, target lane and required
  deceleration; decide the driver warning; respect D4 and E3. Writes no store.
  The §7/§8 numeric thresholds are realised in the Level 1 refinement (F3.2/F3.3),
  so the Level 0 postcondition is qualitative.
* **quantified:** false

### 4.0 / F4 — Route Planning
* **Inputs:** `destination` (E4), `ego_pose` (F1), `hd_map_segment` (D1 read).
* **Outputs:** `route` → F3, F5.
* **Preconditions:**
  - `hd_map_segment.road_id > 0`
* **Postconditions:**
  - guard `true` → `route.path_length > 0 and route.eta >= 0`
* **Processing rules:** Compute the route to E4: path length and estimated time of
  arrival, together with lane geometry needed by F3 and F5. Writes no store.
* **quantified:** false

### 5.0 / F5 — Motion Planning
* **Inputs:** `manoeuvre` (F3), `route` (F4), `ego_state` (F1), `hd_map_segment`
  (D1 read), `traffic_rules` (D4 read).
  (Also consumes `predicted_trajectories` from F2 per §5.1.)
* **Outputs:** `trajectory` → F6.
* **Preconditions:**
  - `traffic_rules.speed_limit >= 0`
  - `manoeuvre.target_speed >= 0`
  - `route.path_length > 0`
* **Postconditions:**
  - guard `true` → `trajectory.max_speed <= traffic_rules.speed_limit and trajectory.max_accel <= 3.0 and trajectory.required_decel >= manoeuvre.required_decel`
* **Processing rules:** Convert the manoeuvre into a kinematically feasible
  trajectory (max permitted speed, max permitted acceleration, horizon duration).
  Never command a speed above the D4 speed limit; honour the manoeuvre's
  deceleration requirement; respect the RSS longitudinal safe distance (N-5) with
  A-2 parameters (`rho = 0.1`, `a_max_accel = 2.0`, `a_max_brake = 4.0`,
  `a_min_brake = 4.0`) and the Euclidean lateral envelope (N-7). Writes no store.
* **quantified:** true (3.0 from A-3)

### 6.0 / F6 — Control
* **Inputs:** `trajectory` (F5), `ego_state` (D3 read).
* **Outputs:** `actuator_cmd` = E9 → F7 (via named interface E9).
* **Preconditions:**
  - `trajectory.max_accel <= 3.0`
  - `ego_state.speed >= 0`
* **Postconditions:**
  - guard `true` → `actuator_cmd.longitudinal_accel <= 3.0 and actuator_cmd.steering <= 1.0 and actuator_cmd.steering >= -1.0`
* **Processing rules:** Convert the trajectory into an actuation command
  (longitudinal acceleration, brake, steering). Keep commands inside the actuator
  envelope: comfort longitudinal limit 3.0 m/s² (A-3), steering ±1.0 (A-6),
  yaw-rate sanity 3.5 rad/s (A-4). Writes no store.
* **quantified:** true (3.0 from A-3, 1.0 from A-6)

### 7.0 / F7 — Safety Shield (monitoring & arbitration)
* **Inputs:** `actuator_cmd` = E9 (F6), `ego_state` (D3 read), `traffic_rules`
  (D4 read).
* **Outputs:** `checked_cmd` = E8 (out).
* **Preconditions:**
  - `traffic_rules.speed_limit >= 0`
  - `ego_state.speed >= 0`
  - `actuator_cmd.steering <= 1.0`
* **Postconditions (guarded, disjunction-free):**
  - guard `true` → `checked_cmd.longitudinal_accel <= 3.0 and checked_cmd.brake >= 0`
  - guard `actuator_cmd.steering <= 1.0 and actuator_cmd.steering >= -1.0` → `checked_cmd.steering = actuator_cmd.steering`
  - guard `actuator_cmd.steering > 1.0` → `checked_cmd.steering = 1.0`
  - guard `actuator_cmd.steering < -1.0` → `checked_cmd.steering = -1.0`
* **Processing rules:** Supervise F6's command and output one satisfying the
  safety envelope even when F6's command violates it; preserve F6's steering
  unless it violates the envelope (the four guards above encode "preserve unless
  violated" without a disjunction); enforce D4 traffic rules on the final command;
  enforce RSS braking profile (N-6: at least `a_min_brake = 4.0`, no acceleration
  above `a_max_accel = 2.0` during `rho = 0.1`) and lateral envelope (N-7).
  Writes no store. E8 is always the result of monitoring E9 (R-E-2).
* **quantified:** true (3.0 from A-3, 1.0 from A-6, 4.0/2.0/0.1 from A-2/N-6)

---

## Level 1 processes (refinement of F3; parent 3.0)

### 3.1 / F3.1 — TTC Computation
* **Inputs:** `predicted_trajectories` (F2), `ego_state` (F1).
* **Outputs:** `ttc_set` → F3.2.
* **Preconditions:**
  - `predicted_trajectories.horizon >= 3.0`
  - `ego_state.speed >= 0`
* **Postconditions (guarded):**
  - guard `true` → `ttc_set.min_ttc >= 0 and ttc_set.min_ttc <= 3.0`
  - guard `ttc_set.count = 0` → `ttc_set.min_ttc = 0`
* **Processing rules:** Compute, for each predicted object, the TTC to the ego
  vehicle; report the minimum TTC over the object set and the number of objects
  considered. If no object is considered, report `count = 0`. Writes no store.
* **quantified:** true (3.0 from A-7)

### 3.2 / F3.2 — Risk Classification
* **Inputs:** `ttc_set` (F3.1), `traffic_rules` (D4 read).
* **Outputs:** `risk_level` → F3.3; `warning` → E7.
* **Preconditions:**
  - `ttc_set.min_ttc >= 0`
  - `traffic_rules.speed_limit >= 0`
* **Postconditions (guarded):**
  - guard `ttc_set.min_ttc > 3.0` → `risk_level = 0 and warning.active = 0 and warning.type = 0`
  - guard `ttc_set.min_ttc <= 3.0 and ttc_set.min_ttc > 1.5` → `risk_level = 1 and warning.active = 1 and warning.type = 1`
  - guard `ttc_set.min_ttc <= 1.5` → `risk_level = 2 and warning.active = 1 and warning.type = 2`
* **Processing rules:** Classify risk from the minimum TTC: no risk (above
  `$T_risk_high = 3.0`), caution (`<= 3.0` and above `$T_fcw = 1.5`),
  critical (`<= 1.5`). Raise the driver warning for caution and critical;
  leave it inactive for no risk. Warning type follows E7: `0 = none`, `1 = caution`,
  `2 = imminent collision`. FCW timing follows N-2 (no later than TTC = 2.0 s).
  The three mutually exclusive guards cover all cases without a disjunction.
* **quantified:** true (3.0 and 1.5 from A-5)

### 3.3 / F3.3 — Maneuver Planning
* **Inputs:** `risk_level` (F3.2), `ego_state` (F1), `driver_intent` (E3), `route`
  (F4), `hd_map_segment` (D1 read).
* **Outputs:** `manoeuvre` → F5.
* **Preconditions:**
  - `risk_level >= 0 and risk_level <= 2`
  - `driver_intent.requested_speed >= 0`
  - `route.path_length > 0`
* **Postconditions (guarded):**
  - guard `risk_level = 0` → `manoeuvre.type = 0 and manoeuvre.target_speed >= 0`
  - guard `risk_level = 1` → `manoeuvre.type = 1 and manoeuvre.required_decel > 0`
  - guard `risk_level = 2` → `manoeuvre.type = 2 and manoeuvre.required_decel >= 6.0 and manoeuvre.target_speed = 0`
  - guard `risk_level = 2 and driver_intent.accelerate = 1` → `manoeuvre.required_decel >= 6.0`
  - guard `risk_level = 0 and driver_intent.accelerate = 1` → `manoeuvre.target_speed >= driver_intent.requested_speed`
  - guard `risk_level = 1 and driver_intent.accelerate = 1` → `manoeuvre.target_speed >= driver_intent.requested_speed`
* **Processing rules:** Produce cruise/keep-lane for no risk; deceleration with
  non-zero required deceleration for caution; emergency deceleration with required
  deceleration at least `$A_emergency = 6.0` m/s² (A-1, sized from N-3/N-4) and
  target speed 0 for critical. A driver accelerate request must never override
  the emergency manoeuvre, yet takes precedence for the other two risk levels;
  the separate guards encode this precedence without a disjunction. Writes no store.
* **quantified:** true (6.0 from A-1)

---

## Store access summary (owner / writers / readers)

| Store | Owner | Writers | Readers |
|---|---|---|---|
| D1 HD Map Store | F5 / F1 | E5 refresh | F1, F2, F3, F4, F5 |
| D2 Object Track Store | F1 | F1 | F2 (via object_table flow) |
| D3 Ego State Store | F1 | F1 | F6, F7 |
| D4 Traffic Rules Store | F5 | E6 refresh | F3, F5, F7 |

Note: D1/D4 refresh flows from E5/E6 and the E9 interface routing are recorded as
open issues in `README.md` / `MES_M3_*.json`, because §5.1 assigns no in-function
writer for D1/D4 and §3 mandates E9 as an external interface.
