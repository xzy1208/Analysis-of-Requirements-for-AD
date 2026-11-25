# NL-RQ-ADAS-v1 — Natural-Language Requirement Specification
## Vehicle-Level ADAS Onboard System (Level 0) with AEB Branch (Level 1)

**Status:** Baseline input document, version 1.0
**Purpose:** *Single common input* for all four requirement models compared in this
study (M1 human-modelled SOFL, M2 LLM-generated SOFL, M3 LLM-generated structured
DFD, M4 LLM-generated object-oriented UML).
**Rule for every modeller:** model **only** what is written here. Do not invent
functions, stores, signals, or thresholds. Where the specification is silent, the
model must leave the point open and record it in an open-issues list.

---

## 中文速读

本文件是**四个模型的唯一共同输入**（人工 SOFL、AI 复刻 SOFL、AI DFD、AI UML 全部以它为
唯一输入），以保证比较的可比性。它是一份面向整车级 ADAS 的自然语言需求规格，
包含 7 个顶层功能、4 个持久数据存储、7 个外部接口，以及 F3 的 AEB 三级细化分支。
所有数值分两档：**规范阈值 N**（有公开来源可引用）与**建模假设 A**（本文作者选定的
取值，明确标注为假设而非行业标准）。编号 N-/A-/F-/D-/E- 供后续四个模型做可追溯性
矩阵的锚点。

---

## 1. Scope and system boundary

**R-SCOPE-1.** The system under specification is the **onboard ADAS of a passenger
car**, operating at **SAE level 2** (driver supervises; system executes lateral and
longitudinal control within its operational design domain).

**R-SCOPE-2.** The system boundary is the **vehicle**. Everything outside the
vehicle — the perception sensor set, the GNSS/IMU, the HMI, the driveline/brake/
steer actuators, the V2X gateway, the cloud, the traffic infrastructure and other
road users — is modelled only as **external input/output** (E-interfaces), never as
an internal element.

**R-SCOPE-3.** The specification is **vehicle-level**: it constrains the *functional
allocation* across onboard functions and the *data dependencies* between them. It
does not constrain any individual algorithm (no detector, no tracker, no planner
internals, no controller tuning).

**R-SCOPE-4.** The specification is decomposed into two levels:
* **Level 0** — the complete vehicle-level functional architecture.
* **Level 1** — a refinement of **exactly one** Level-0 function: the
  emergency-braking branch of **F3 Behaviour Planning** (see §6). All other Level-0
  functions stay atomic.

---

## 2. Definitions

| Term | Meaning |
|---|---|
| TTC | Time-to-Collision: the time until the ego vehicle and a given object collide if their current relative kinematics continue unchanged, in seconds. |
| ODD | Operational Design Domain. |
| RSS | Responsibility-Sensitive Safety (Shalev-Shwartz et al.) [S4]. |
| FCW | Forward Collision Warning (driver-facing warning). |
| AEB | Autonomous Emergency Braking (actuation). |
| Lead object | The nearest relevant object ahead of the ego vehicle in the ego lane. |
| Ego state | Pose, speed, yaw rate and acceleration of the ego vehicle. |
| `$` | Numeric threshold defined in §7 (normative) or §8 (assumption). |

---

## 3. External interfaces (E)

Each external interface is a named data flow crossing the system boundary. The
modeller is free to decide the physical carrier (sensor bus, CAN/Ethernet,
etc.) — it is out of scope — but **must** model every interface below.

| ID | Interface | Direction | Content / semantics |
|---|---|---|---|
| E1 | `raw_sensor_data` | in | Time-synchronised sensor frames from the onboard perception sensor set (camera, radar, lidar), with per-sensor validity flags and timestamps. |
| E2 | `gnss_imu` | in | GNSS fix (position, heading) and IMU samples (angular rate, acceleration) of the ego vehicle, with validity flags. |
| E3 | `driver_intent` | in | Driver command / ODD status from the HMI: requested cruise speed, requested manual override (accelerate/brake/steer), driver-attention state. |
| E4 | `destination` | in | Navigation destination (longitude, latitude) and route preferences from the navigation unit. |
| E5 | `map_data` | in | HD-map segment for the current position: road id, lane id, posted speed limit, curvature, plus lane-level topology. |
| E6 | `traffic_rules` | in | Currently applicable traffic rules: posted speed limit and traffic-signal state for the current lane. |
| E7 | `warning` | out | Driver-facing warning signal: warning type (none / caution / imminent collision) and active flag. |
| E8 | `checked_cmd` | out | Final actuation command delivered to the vehicle actuators: longitudinal acceleration command, brake command, steering command. |
| E9 | `actuator_cmd` | in | Raw actuation command produced by the control function, before any safety arbitration. |

**R-E-1.** E7 and E8 are the only outputs of the system. No function may emit a
signal that is not E7 or E8.

**R-E-2.** The *system* output E8 shall be the result of a **monitoring /
arbitration** function applied to E9; the raw command E9 shall never reach the
actuators directly.

---

## 4. Persistent data stores (D)

A data store is a persistent, vehicle-local database owned by the system. Stores
are shared between functions; a function accesses a store by **reading** or
**writing** it.

| ID | Store | Owner function | Content | Lifetime |
|---|---|---|---|---|
| D1 | HD Map Store | F5 / F1 | Cached HD-map segment for the current road: road id, lane id, posted speed limit, curvature, lane topology. | Persistent across drives; refreshed by E5. |
| D2 | Object Track Store | F1 | Fused object table: object count, per-object id, position (x, y), velocity, class, and the id + kinematics of the current lead object. | Rebuilt each perception cycle; retained for short-term fusion. |
| D3 | Ego State Store | F1 | Ego pose (x, y), speed, yaw rate, acceleration, and the timestamp of the last update. | Persistent across drives. |
| D4 | Traffic Rules Store | F5 | Applicable traffic rules: posted speed limit, traffic-signal state for the current lane. | Persistent across drives; refreshed by E6. |

**R-D-1.** A store's content shall be written **only** by its owner function.
**R-D-2.** A function shall not read a store it does not own unless the
specification explicitly assigns that read to it.

---

## 5. Level 0 — required functional architecture (F)

The specification mandates the **following seven vehicle-level functions** and the
**responsibility of each**. The modeller must realise every function as a separate
element and must respect the responsibility boundaries below. Naming of elements is
free; decomposition *below* this level is not permitted at Level 0.

### F1 — Perception & Localisation
**Inputs:** E1, E2, D1 (read). **Outputs:** object table (to D2), ego state (to D3),
and the *ego pose* and *object table* to other functions as needed.
**Responsibility:**
* F1 shall convert raw sensor data into a fused object table: id, position,
  velocity, class for every detected object, plus the identification of the lead
  object.
* F1 shall compute the ego state (pose, speed, yaw rate, acceleration) by fusing
  E2 with the vehicle's own motion signals.
* F1 shall **write** D2 and D3. It shall not read D2 or D3.

### F2 — Prediction
**Inputs:** object table, ego state, D1 (read). **Output:** predicted trajectories
of the relevant objects.
**Responsibility:**
* F2 shall predict, for each relevant object, its future motion over a horizon of
  at least 3 s, and shall derive from the predictions the **minimum TTC** to the
  ego vehicle over that horizon.
* F2 shall be the **only** function that computes TTC.
* F2 shall not write any store.

### F3 — Behaviour Planning
**Inputs:** ego state, traffic rules (D4 read), predicted trajectories, driver
intent (E3), route (from F4), D1 (read). **Outputs:** manoeuvre, warning (E7).
**Responsibility:**
* F3 shall decide, at every planning cycle, the *target manoeuvre* of the ego
  vehicle: cruise / keep-lane / lane-change / lane-keeping-with-deceleration /
  emergency deceleration, expressed as a manoeuvre type together with a target
  speed, target lane and a required deceleration.
* F3 shall decide whether to issue a driver warning (E7) and which warning type.
* F3 shall respect the applicable traffic rules (D4) and the driver intent (E3).
* F3 shall not write any store.

### F4 — Route Planning
**Inputs:** E4, ego pose, D1 (read). **Output:** route.
**Responsibility:**
* F4 shall compute the route to E4: path length and estimated time of arrival,
  together with the lane geometry needed by F3 and F5.
* F4 shall not write any store.

### F5 — Motion Planning
**Inputs:** manoeuvre (from F3), route (from F4), ego state, D1 and D4 (read).
**Output:** trajectory.
**Responsibility:**
* F5 shall convert the manoeuvre into a **kinematically feasible** trajectory over
  the planning horizon: maximum permitted speed, maximum permitted acceleration,
  horizon duration.
* F5 shall never command a speed above the applicable speed limit (D4).
* F5 shall honour the deceleration requirement carried by the manoeuvre.
* F5 shall not write any store.

### F6 — Control
**Inputs:** trajectory (from F5), ego state (D3 read). **Output:** `actuator_cmd` (E9).
**Responsibility:**
* F6 shall convert the trajectory into an actuation command: longitudinal
  acceleration command, brake command, steering command.
* F6 shall keep the commands inside the actuator envelope (§8, A-3/A-6).
* F6 shall not write any store.

### F7 — Safety Shield (monitoring & arbitration)
**Inputs:** `actuator_cmd` (E9), ego state (D3 read), D4 (read). **Output:**
`checked_cmd` (E8).
**Responsibility:**
* F7 shall supervise the command produced by F6 and shall output a command that
  satisfies the safety envelope, even when F6's command violates it.
* F7 shall preserve the steering command of F6 unless it violates the envelope.
* F7 shall enforce the traffic rules (D4) on the final command.
* F7 shall not write any store.

### 5.1 Mandatory data dependencies (Level 0)

* F1 → F2: ego pose and object table.
* F1 → F4: ego pose.
* F2 → F3: predicted trajectories.
* F2 → F5: predicted trajectories.
* F3 → F5: manoeuvre.
* F4 → F3 and F4 → F5: route.
* F5 → F6: trajectory.
* F6 → F7: actuator command.
* F7 → outside: checked command (E8).
* F3 → outside: warning (E7).
* Store reads: F1 reads D1; F2 reads D1; F3 reads D1 and D4; F4 reads D1;
  F5 reads D1 and D4; F6 reads D3; F7 reads D3 and D4.
* Store writes: F1 writes D2 and D3.

**R-L0-1.** The Level-0 model shall contain exactly the seven functions F1–F7,
the four stores D1–D4, and the external interfaces E1–E9 listed above, and **no
other** element.

---

## 6. Level 1 — refinement of the AEB branch of F3

**R-L1-1.** F3 shall be decomposed into exactly three sub-functions, which together
realise the emergency-braking capability:

### F3.1 — TTC Computation
**Inputs:** predicted trajectories (from F2), ego state. **Output:** TTC set.
* Shall compute, for each predicted object, the TTC to the ego vehicle, and report
  the **minimum** TTC over the object set together with the number of objects
  considered.
* If no object is considered, the TTC set shall report a count of 0.

### F3.2 — Risk Classification
**Inputs:** TTC set (from F3.1), traffic rules (D4). **Outputs:** risk level, warning (E7).
* Shall classify the situation into a risk level as a function of the minimum TTC:
  * **no risk** — TTC above `$T_risk_high`;
  * **caution** — TTC at or below `$T_risk_high` and above `$T_fcw`;
  * **critical** — TTC at or below `$T_fcw`.
* Shall raise the driver warning for *caution* and *critical*, and shall not raise
  it for *no risk*.

### F3.3 — Maneuver Planning
**Inputs:** risk level (from F3.2), ego state, driver intent (E3), route (from F4),
D1. **Output:** manoeuvre.
* Shall produce a **cruise/keep-lane** manoeuvre for *no risk*.
* Shall produce a **deceleration** manoeuvre (non-zero required deceleration) for
  *caution*.
* Shall produce an **emergency deceleration** manoeuvre with a required
  deceleration of at least `$A_emergency` m/s² and a target speed of 0 for
  *critical*.
* Shall not override the emergency manoeuvre with a driver request to accelerate;
  for the other risk levels a driver request to accelerate shall take precedence.

---

## 7. Normative thresholds (N)

These values are traceable to public sources and are **not** negotiable by the
modeller.

| ID | Value | Requirement | Source |
|---|---|---|---|
| **N-1** | operational speed up to **130 km/h** | The AEB capability shall be operational up to a vehicle speed of at least 130 km/h (stationary targets excluded). | [S3] |
| **N-2** | FCW at **TTC > 1.5 s** | A forward-collision warning issued at a TTC greater than 1.5 s is credited by the assessment protocol; therefore the warning shall be present no later than TTC = 2.0 s (the TTC at which the cut-out safety-back-up scenario is staged). | [S2] |
| **N-3** | **> 30 km/h** impact-speed reduction | An intervention that does not avoid the collision but reduces the impact speed by more than 30 km/h is credited; this is the yardstick against which the emergency deceleration capability is sized. | [S2] |
| **N-4** | CCRm test envelope: VUT **60–130 km/h**, target **20 km/h**; CCRb target decelerating at **−4 m/s²** | Defines the worst-case closing speed used for sizing the emergency deceleration. | [S2] |
| **N-5** | RSS longitudinal safe distance | The ego vehicle shall maintain a longitudinal distance to the lead object of at least the RSS minimum safe distance, `d_min` of Eq. (1) of [S4], computed with an integrator-defined parameter set (see A-2). | [S4], [S5] |
| **N-6** | RSS braking profile | While a dangerous situation persists, the ego shall brake with at least `a_min,brake`; it shall not accelerate longitudinally above `a_max,accel` during the response time `ρ`. | [S4] |
| **N-7** | Euclidean manoeuvring envelope | The commanded lateral acceleration implied by the trajectory and by the steering command shall remain within the vehicle's lateral-acceleration capability; violations are a safety violation, not a comfort violation. | [S3] (safety-critical lateral control) |

**Derived threshold (used by §8, A-1).** With N-4 the worst-case CCRm closing
speed is 130 − 20 = 110 km/h = 30.6 m/s. To satisfy N-3 the ego must shed
8.33 m/s of relative speed. A constant longitudinal deceleration of
**6.0 m/s²** over ≈1.39 s does exactly that (and requires ≈37 m of clear road),
which is comfortably inside the capability of a production braking system at
≈0.61 g. This is the basis of assumption **A-1**.

---

## 8. Modelling assumptions (A)

These values are **the modeller's explicit choices**, not industry-nominated values.
They are stated so that the comparison across the four models is fair and so that
the sensitivity of the results can be discussed.

| ID | Value | Rationale |
|---|---|---|
| **A-1** | Emergency deceleration **6.0 m/s²** | Sized from N-3/N-4 as derived above. |
| **A-2** | RSS parameter set: `ρ = 0.1 s`, `a_max,accel = 2.0 m/s²`, `a_max,brake = 4.0 m/s²`, `a_min,brake = 4.0 m/s²` | RSS parameter values are explicitly integrator-configurable and the reference implementation is parameter-independent [S5]; the values above are a conservative operating point for a production passenger car. |
| **A-3** | Comfortable longitudinal acceleration limit **3.0 m/s²** | Upper bound of the longitudinal actuation envelope used by F6/F7. |
| **A-4** | Lateral / yaw-rate envelope **3.5 rad/s** (≈200 °/s) | Generic upper bound of the vehicle's yaw-rate capability, used as a sanity envelope on the localisation output. |
| **A-5** | Risk thresholds: `$T_risk_high = 3.0 s`, `$T_fcw = 1.5 s` | `$T_fcw = 1.5 s` follows N-2 (the TTC below which a warning is no longer creditable); `$T_risk_high = 3.0 s` is the onset of the *caution* band and equals the prediction horizon of F2 (R-F2-1). |
| **A-6** | Steering command envelope **±1.0** (normalised) | Actuator envelope of F6. |
| **A-7** | Prediction horizon **3.0 s** | Long enough to cover the caution band of A-5. |

---

## 9. Additional cross-cutting requirements

**R-G-1 (formalisation).** Where a model notation permits it, every function
shall be specified with (i) a *precondition* naming the data it requires,
(ii) a *postcondition* naming the data it produces, and (iii) at least one
*quantified* constraint on its output where §7/§8 give a threshold. Functions
whose output has no threshold in §7/§8 shall still carry at least one
qualitative postcondition.

**R-G-2 (traceability).** Every requirement clause R-xx of this document shall be
traceable to at least one element of the model. The modeller shall deliver a
traceability matrix.

**R-G-3 (no orphan elements).** No element of the model shall exist without being
traceable to a requirement clause. Any element introduced for modelling
convenience shall be declared in an open-issues list with a justification.

**R-G-4 (no implicit data dependency).** Every data dependency between two
elements shall be an explicit, named, directed flow with a single producer and a
single consumer. A flow shall not be shared by two consumers unless the
specification says so.

**R-G-5 (interface discipline).** The output of a function shall be consumed only
by functions that the specification names as its consumers. A producer that
outputs a datum no consumer requests is a defect.

**R-G-6 (null-safety).** A precondition that requires a datum shall be stated
explicitly; a postcondition that reads a field of a datum shall be guarded by the
non-nullness of that datum.

---

## 10. Source list

* **[S1]** Euro NCAP, *AEB Car-to-Car Test Protocol*, v3.0.2.
* **[S2]** Euro NCAP, *Assisted Driving — Highway & Interurban Assist Systems Protocol*, v1.1 (Oct. 2025).
* **[S3]** Euro NCAP, *Assessment Protocol — Safety Assist*, v9.1.
* **[S4]** S. Shalev-Shwartz et al., "On a formal model of safe and scalable self-driving cars (RSS)," arXiv:1708.06374, 2017; IEEE P2846.
* **[S5]** Intel, *ad-rss-lib — High-Level Design: Key Design Decisions and Alternatives* (RSS parameters are integrator-defined).
* **[S6]** Y. Zhu et al., "A survey on LLM-powered autonomous driving," *Engineering*, 2025, doi:10.1016/j.eng.2025.07.038 (preprint arXiv:2409.14165).
* **[S7]** Y. Hu et al., "Planning-oriented autonomous driving (UniAD)," CVPR 2023.

---

## 11. Open issues to be reported by the modeller

1. Is the seven-function split of §5 sufficient for the stated ODD, or is a
   separate function needed for driver monitoring (L2 handover)? Justify.
2. D3 (Ego State Store) is written by F1 but read by F6/F7 — is that ownership
   acceptable, or should the store be written by a dedicated function?
3. The specification fixes thresholds but not timing; is a timing requirement
   (cycle time) needed for the emergency branch to be meaningful?
4. Is the AEB branch of F3 the right Level-1 refinement, or should Level 1 refine
   the F6/F7 actuation chain instead?
