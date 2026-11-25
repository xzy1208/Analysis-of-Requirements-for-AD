# M2 — LLM-generated SOFL replica (single pass)

Vehicle-level ADAS onboard system, Level 0 root module + Level 1 refinement of the F3 AEB
branch. Generated from `NL-RQ-ADAS-v1_需求规格.md` only, under the SOFL XML dialect of
`SOFL_syntax_cheatsheet.md`.

| File | Content |
|---|---|
| `ADAS_System.cdfd` | Level-0 CDFD canvas: 7 processes, 4 data stores, 20 active flows, 14 store flows |
| `ADAS_System.fModule` | Level-0 formal module: 15 types, 4 store variables, 7 processes with pre/post |
| `AEB_Branch.cdfd` | Level-1 CDFD canvas: 3 processes, 9 active flows (no store elements — parent stores are referenced logically) |
| `AEB_Branch.fModule` | Level-1 formal module: 4 branch types, empty `variableDeclaration`, `moduleDecom = ADAS_System` |
| `MES_M2_L0.json` | Model exchange envelope for Level 0 |
| `MES_M2_L1.json` | Model exchange envelope for Level 1 |
| `README.md` | This file: design decisions, traceability matrix, open issues |

Provenance: `producer = llm`, `llm_family = MiniMax-M3.1-Flash`, `passes = 1`,
`self_review_performed = false` (single-shot generation, no second self-check pass).

---

## 1. Design decisions

### 1.1 Naming

* Processes (CDFD `process/@name` ↔ `.fModule` `process/@name` ↔ MES `elements[].name`):
  `Perception_Localisation` (F1), `Prediction` (F2), `Behaviour_Planning` (F3),
  `Route_Planning` (F4), `Motion_Planning` (F5), `Control` (F6), `Safety_Shield` (F7);
  Level 1: `TTC_Computation` (F3.1), `Risk_Classification` (F3.2), `Maneuver_Planning` (F3.3).
  The spec's own ids `F1…F7` / `F3.1…F3.3` are carried as the stable MES `id`.
* Stores (CDFD `dataStore/@name` ↔ `variableDeclaration` entries, character for character):
  `HD_Map_DB` (D1), `Object_Track_DB` (D2), `Ego_State_DB` (D3), `Traffic_Rules_DB` (D4).
* Flow names equal the datum carried. When the *same* datum feeds two consumers (spec §5.1
  shares `ego_pose`, `predicted_trajectories` and `route`), the flow name is suffixed
  `_for_<consumer>` so that every process port name stays unique and the `head` signature is
  unambiguous: `ego_pose` (F1→F2) / `ego_pose_for_route` (F1→F4), `ego_state` (F1→F3) /
  `ego_state_for_motion` (F1→F5), `predicted_trajectories` (F2→F3) /
  `predicted_trajectories_for_motion` (F2→F5), `route` (F4→F3) / `route_for_motion` (F4→F5).
  Each duplicated datum is declared as two separate flows (MES rule §5), so the sharing is visible.

### 1.2 Decomposition granularity

* Level 0 contains exactly the seven functions F1–F7, the four stores D1–D4 and the nine
  interfaces E1–E9 (R-L0-1). No function is decomposed further, no extra element is invented.
* Level 1 refines exactly one Level-0 function, F3, into the three sub-functions of §6.
* The child CDFD contains **no** `<dataStore>`: the parent stores are imported implicitly and
  referenced logically, i.e. `ext rd HD_Map_DB` / `ext rd Traffic_Rules_DB` in the child
  `.fModule` (and the child's `variableDeclaration` is empty, `moduleDecom = ADAS_System`).
* The child's boundary is the parent F3 interface. Inputs that the parent receives from F1,
  F2, F4 and E3 are therefore drawn as `outSide` endpoints of the branch and their producers
  are recorded in `MES_M2_L1.json` (`parent_elements`, level `parent`).

### 1.3 Type system

* Only `real`, `nat`, `String` are used. Composite types are declared in `typeDeclaration`
  (`Name = composed of` … `end`), 8-space field indent, 6-space `end`.
* `variableDeclaration` holds exactly the four stores; every `.fModule` variable name matches a
  `<dataStore name="…">` character for character.
* **Enumerated values are `nat` codes**, because the permitted expression grammar of the
  cheatsheet contains no string literals. Code tables:
  * `risk_code`: 0 = no risk, 1 = caution, 2 = critical
  * `warning_type`: 0 = none, 1 = caution, 2 = imminent collision
  * `manoeuvre_type`: 0 = cruise / keep-lane, 1 = keep-lane, 2 = lane-change,
    3 = lane-keeping-with-deceleration, 4 = emergency deceleration
  * `signal_state`: 0 = not applicable, 1 = red, 2 = amber, 3 = green
  * `attention_state`: 0 = unknown, 1 = attentive, 2 = inattentive; `odd_status`: 0 = in ODD, 1 = outside ODD
  * request/validity flags: `nat` 0/1
* **Units** (modeller's choice, documented because the spec mixes them): speeds in **km/h**
  (so N-1 = 130.0, N-4 = 60/130/20 and the posted speed limits are used verbatim),
  accelerations/decelerations in **m/s²**, yaw rate in **rad/s**, steering normalised, TTC in **s**,
  distances in **m**.
* Threshold values are taken verbatim from §7/§8 and inlined in the postconditions:
  130.0 (N-1), 1.5 / 2.0 (N-2), 4.0 (N-4 / A-2), 2.0 (A-2 a_max,accel), 6.0 (A-1),
  3.0 (A-3), 3.5 (A-4), 3.0 / 1.5 (A-5), 1.0 (A-6), 3.0 (A-7). No other numeric value is used.

### 1.4 Slot / port convention (as prescribed by the cheatsheet)

* Input slots: all `dataFlow` **reads** occupy slots `1..k` (1-based `connectorIndex`), then all
  `activeDataFlow` inputs occupy `k+1..N` (0-based `belongToConnector` + k).
* `head` lists the **active flow ports only** (store connections carry no name attribute and are
  declared by `ext rd` / `ext wr`), in slot order; output items follow the producing port order.
* Store read: `from` = DataStore / `Bottom` / `connectorIndex="0"`, `to` = ProcessTopBottom / `Top`
  / `connectorIndex = <read slot>`. Store write: `from` = ProcessTopBottom / `Bottom` /
  `connectorIndex="0"`, `to` = DataStore / `Bottom`.
* `<dataFlow>` carries **only** `fromX/fromY/toX/toY`; `<activeDataFlow>` carries only
  `name/type/fromX/fromY/toX/toY`. Boundary endpoints use `belongToType="outSide"`,
  `belongToConnector="-1"`, `shapeIndex="-1"`, empty `belongToName`/`no`.

---

## 2. Traceability matrix (requirement clause → model element)

### 2.1 Cross-cutting and boundary clauses

| Clause | Model element | Realised by |
|---|---|---|
| R-SCOPE-1 (SAE L2, driver supervises) | F1…F7 | model scope; no takeover element exists (OI-1) |
| R-SCOPE-2 (boundary = vehicle) | E1…E9 | only `outSide` endpoints of `activeDataFlow`; sensors/HMI/actuators/cloud are never internal elements |
| R-SCOPE-3 (vehicle level, no algorithm internals) | F2, F3, F5, F6 | model scope: no detector/tracker/planner/controller internals |
| R-SCOPE-4 (two levels) | F3 → AEB_Branch | child module with exactly 3 sub-functions |
| R-E-1 (only E7/E8 are outputs) | F3, F7 | the two `boundary_out` flows |
| R-E-2 (E8 = shield(E9), E9 never reaches actuators) | F6, F7 | flow `actuator_cmd` (F6→F7) + F7 postconditions |
| R-D-1 (only the owner writes) | F1, F5 | the 4 `store_write` flows |
| R-D-2 (no unassigned store reads) | F1…F7 | the 10 `store_read` flows, exactly as §5.1 |
| R-L0-1 (exactly 7 functions / 4 stores / 9 interfaces) | all | componentList + connectionList |
| R-G-1 (pre / post / quantified) | all 7 (+3 at L1) | `pre` line + `post` scenarios; F4 has only qualitative postconditions (no threshold applies) |
| R-G-2 (traceability) | — | this matrix |
| R-G-3 (no orphan elements) | — | §4 open issues + MES `open_issues` |
| R-G-4 (explicit named flows) | all | 34 flows (L0) / 11 flows (L1), each single producer + single consumer |
| R-G-5 (no output without consumer) | all | `outputs[].consumers` |
| R-G-6 (null safety) | all | every `pre` guards the datums read in `post` |

### 2.2 Functions

| Clause | Element | Key postcondition(s) |
|---|---|---|
| F1 Perception & Localisation | `Perception_Localisation` | `object_table.obj_count >= 0`; `ego_state.yaw_rate <= 3.5 and ego_state.yaw_rate >= -3.5`; writes D2, D3 (and D1) |
| F2 Prediction | `Prediction` | `predicted_trajectories.horizon >= 3.0`; `min_ttc >= 0` guarded by `obj_count > 0` |
| F3 Behaviour Planning | `Behaviour_Planning` | `manoeuvre.target_speed <= Traffic_Rules_DB.posted_speed_limit`; `warning_type = 2 → required_decel >= 6.0`; `warning_type = 1 → required_decel > 0` |
| F4 Route Planning | `Route_Planning` | `route.path_length >= 0 and route.eta >= 0`; `route.lane_count >= 1` |
| F5 Motion Planning | `Motion_Planning` | `max_speed <= posted_speed_limit`; `max_accel <= 2.0`; `decel_limit >= 4.0`; `manoeuvre.required_decel > 0 → decel_limit >= manoeuvre.required_decel` |
| F6 Control | `Control` | `long_accel_cmd <= 3.0 and >= -3.0`; `steer_cmd <= 1.0 and >= -1.0`; `long_accel_cmd <= trajectory.max_accel` |
| F7 Safety Shield | `Safety_Shield` | unconditional envelope on `checked_cmd`; steering preserved iff inside envelope; traffic rule enforced via `Ego_State_DB.speed >= posted_speed_limit` |
| F3.1 TTC Computation | `TTC_Computation` | `ttc_set.obj_count >= 0`; `ego_state.speed <= 130.0 → ttc_set <> null`; `min_ttc >= 0` when `obj_count > 0` |
| F3.2 Risk Classification | `Risk_Classification` | `min_ttc <= 1.5 → risk_code = 2`; `1.5 < min_ttc <= 3.0 → risk_code = 1`; `min_ttc > 3.0 → risk_code = 0`; `obj_count = 0 → risk_code = 0`; `min_ttc <= 2.0 → warning.active = 1` |
| F3.3 Maneuver Planning | `Maneuver_Planning` | `risk_code = 2 → manoeuvre_type = 4 and required_decel >= 6.0 and target_speed = 0`; `risk_code = 1 → manoeuvre_type = 3 and required_decel > 0`; `risk_code = 0 → manoeuvre_type = 0`; driver acceleration request cannot override the emergency manoeuvre |

### 2.3 Thresholds (§7 / §8) → where each value is used

| ID | Value | Element / postcondition | Note |
|---|---|---|---|
| N-1 | 130 km/h | `TTC_Computation`: `ego_state.speed <= 130.0 → ttc_set <> null` | AEB capability guaranteed over the whole speed range (not gated) |
| N-2 | TTC > 1.5 s / warning by 2.0 s | `Risk_Classification`: `min_ttc <= 2.0 → warning.active = 1`, band edge 1.5 | warning onset at 3.0 s is earlier than the 2.0 s staging point |
| N-3 | > 30 km/h impact-speed reduction | `Behaviour_Planning` / `Maneuver_Planning`: `required_decel >= 6.0` | sizing yardstick, realised through A-1 |
| N-4 | 60–130 km/h, target 20 km/h, −4 m/s² | `Motion_Planning`: `decel_limit >= 4.0` | 60/130/20 are assessment-scenario values without a runtime element (OI-14) |
| N-5 | RSS d_min | `Motion_Planning`: `min_gap >= 0` + `decel_limit >= 4.0` (A-2) | closed form not restated in the spec (OI-9) |
| N-6 | a_min,brake 4.0; a_max,accel 2.0; ρ 0.1 s | `Motion_Planning`: `max_accel <= 2.0`, `decel_limit >= 4.0` | ρ has no SOFL timing construct (OI-13) |
| N-7 | lateral-acceleration envelope | `Trajectory.lateral_accel`; steering envelope A-6 in F6/F7 | no numeric capability in §7/§8 (OI-10) |
| A-1 | 6.0 m/s² | `Behaviour_Planning`, `Maneuver_Planning` | emergency deceleration |
| A-2 | 2.0 / 4.0 / 4.0 (ρ 0.1 s) | `Motion_Planning` | RSS operating point |
| A-3 | 3.0 m/s² | `Control`, `Safety_Shield` | longitudinal actuation envelope |
| A-4 | 3.5 rad/s | `Perception_Localisation` | yaw-rate sanity envelope |
| A-5 | 3.0 s / 1.5 s | `Risk_Classification` | risk bands |
| A-6 | ±1.0 | `Control`, `Safety_Shield` | steering envelope |
| A-7 | 3.0 s | `Prediction` | prediction horizon |

### 2.4 Requirement → flow map (R-G-4 / R-G-5 evidence)

`E1→F1`, `E2→F1`, `E5→F1`, `E3→F3`, `E4→F4`, `E6→F5` (boundary in);
`F1→F2` (ego_pose, object_table), `F1→F4` (ego_pose), `F2→F3`, `F2→F5`, `F3→F5`,
`F4→F3`, `F4→F5`, `F5→F6`, `F6→F7` (active);
`F3→E7`, `F7→E8` (boundary out);
store reads: D1→F1,F2,F3,F4,F5; D4→F3,F5,F7; D3→F6,F7;
store writes: F1→D1,D2,D3; F5→D4.

---

## 3. Open issues (§11 answers + modeller's own)

The four questions of §11, answered (full text also in `MES_M2_L0.json` / `MES_M2_L1.json`):

1. **Is the seven-function split sufficient?** — *Partly.* For the stated ODD it is sufficient
   **only if driver monitoring stays an input**: E3 already carries the driver-attention state and
   the ODD status, and F3 consumes it. For a genuine SAE L2 handover (degradation detection,
   takeover request, hands-off detection, torque monitoring) a separate function is needed — but
   R-L0-1 forbids any eighth function, so this model keeps the driver attention as an external
   flag and records the gap. **OI-1, impact medium.**
2. **Is D3 ownership acceptable?** — *Accept, with a recorded consequence.* §5.1 explicitly
   assigns the D3 reads to F6 and F7, and §4 names F1 as owner, so a dedicated ego-state function
   would both contradict the spec and break R-L0-1. The consequence is that F1's update rate and
   freshness become a safety dependency of the shield (D3 holds `last_update`, which the model
   does not check). A dedicated owner would be the cleaner allocation if R-L0-1 were relaxed.
   **OI-2, impact medium.**
3. **Is a timing requirement needed?** — *Yes.* Thresholds alone do not make the emergency branch
   meaningful: the spec gives a response time only inside the RSS parameter set (ρ = 0.1 s) and
   derives a braking duration of ≈1.39 s for A-1, but never states a cycle time for the planning
   cycle. SOFL has no timing construct, so ρ is not formalised and no deadline appears in the
   model. **OI-3 (impact high), OI-13.**
4. **Is the AEB branch the right Level-1 refinement?** — *Defensible, but not optimal.* §6 gives
   the AEB branch an explicit three-way decomposition, so it is the only refinement the
   specification actually supports. The alternative — refining the F6/F7 actuation chain — would
   cover the two weakest parts of the model: N-7 (no numeric lateral-acceleration capability) and
   R-E-2 (the arbitration behaviour). **OI-4, impact medium.**

Additional open issues raised by the modeller (all recorded in the MES files):

| Id | Issue | Impact |
|---|---|---|
| OI-5 | E9 is listed as an external interface but §5/§5.1 place it inside the system; modelled as the internal F6→F7 flow | low |
| OI-6 | §4 gives D1 owner "F5 / F1" and D4 owner "F5", while §5 forbids F5 to write any store and §5.1 lists only F1→D2/D3; the model therefore has F1 write D1 (from E5) and F5 write D4 (from E6) so that E5/E6 are consumed and R-D-1 holds | medium |
| OI-7 | §5 makes F2 the only TTC-computing function, §6 has F3.1 compute a TTC set — TTC is computed twice | medium |
| OI-8 | §6: caution demands a deceleration manoeuvre, but a driver acceleration request takes precedence for every non-critical risk level — the caution+accelerate case is contradictory; the explicit caution rule is modelled | medium |
| OI-9 | N-5 gives no closed form for d_min and no unit convention; the safe-distance requirement is modelled qualitatively (`min_gap` + A-2 braking capability) | medium |
| OI-10 | N-7 has no numeric lateral-acceleration capability; `Trajectory.lateral_accel` is carried but cannot be checked by F6/F7 | medium |
| OI-11 | §8 refers to "R-F2-1", a clause that does not exist in §5 — missing traceability anchor | low |
| OI-12 | Derived convenience fields (`PredictedTrajectories.lead_gap/lead_speed`, `Trajectory.min_gap/lateral_accel`) and the ego-state flows F1→F3 / F1→F5 (needed because §5.1 omits F3/F5 from the D3 readers and R-D-2 forbids them reading D3) | low |
| OI-13 | ρ = 0.1 s cannot be expressed (no timing construct) | medium |
| OI-14 | N-4's 60–130 km/h / 20 km/h are assessment-scenario values without a runtime element | low |
| OI-15 | Enumerations encoded as `nat` codes (no string literals in the permitted grammar) | low |
| OI-16 | No sentinel value for `min_ttc` when the object count is 0 | low |

---

## 4. Consistency checks performed (single pass, no revision)

* Every `<process>` in a CDFD has exactly one `<process>` entry in the matching `.fModule` and
  vice versa (7 / 7 and 3 / 3).
* Every `variableDeclaration` entry matches a `<dataStore name="…">` exactly (4 / 4); the child
  module declares none, and references the parent stores only through `ext rd`.
* `head` order follows the global slot order for every process (store reads first, then active
  inputs by `belongToConnector`), and the `connectorIndex` of every store read equals its 1-based
  slot.
* Expressions use only `=`, `<>`, `>`, `>=`, `<`, `<=`, `and`, `null`, numbers, field access and
  arithmetic — no `or`, `not`, `=>`, quantifiers or `seq of`; `<` and `>` are XML-escaped.
* `<dataFlow>` elements carry only `fromX/fromY/toX/toY`; `<activeDataFlow>` elements carry only
  `name/type/fromX/fromY/toX/toY`.
* Both `.cdfd` and `.fModule` files are UTF-8 **with BOM**, XML-declared, 2-space indented.
* MES JSON files are strict JSON; all element/store/external ids are unique and every flow
  producer/consumer resolves to an id in the same file (or to a parent id marked
  `"level": "parent"` in the Level-1 file).
