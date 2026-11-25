# M3 — AI-generated Structured DFD (Yourdon/DeMarco)

Vehicle-level ADAS onboard system. **Single-pass generation** (`passes = 1`,
`self_review_performed = false`). Sole input: `NL-RQ-ADAS-v1_需求规格.md`.
Exchange envelope per `MES_schema.md`.

## Files

| File | Content |
|---|---|
| `M3_L0.dot` | Level 0 DFD (7 processes, 4 stores, 9 external entities) |
| `M3_L1.dot` | Level 1 DFD (F3 refined into F3.1/F3.2/F3.3) |
| `M3_process_dictionary.md` | Semantic annex: I/O, pre/postconditions, rules |
| `MES_M3_L0.json` | MES envelope, root (`parent_module = null`) |
| `MES_M3_L1.json` | MES envelope, child (`parent_module = "M3_L0"`) |
| `README.md` | This file |

## Key design decisions

1. **Element counts (R-L0-1):** exactly 7 processes `1.0..7.0` = F1..F7, exactly
   4 stores `D1..D4`, exactly 9 external entities `E1..E9`. No extra element.
2. **Notation mapping:** process = `box`; external entity = `box` with
   `style="rounded,filled"` + light-grey fill; data store = `cylinder`;
   flow = labelled directed edge. Store **write** = solid blue edge;
   store **read** = dashed grey edge; active/boundary = solid black edge.
3. **Semantics externalised:** DFD carries structure only; all pre/postconditions
   and processing rules live in `M3_process_dictionary.md` — an inherent trait of
   the notation, shown explicitly for comparison.
4. **Threshold discipline:** every numeric value comes from §7 (N-1..N-7) and
   §8 (A-1..A-7). No invented numbers.
5. **Restricted booleans:** only `= <> > >= < <= and`; disjunction and negation
   are excluded. Vacuous null-value guards are excluded; real field constraints
   (`valid = 1`, `speed_limit >= 0`) are used, and `>= 0` is never applied to a
   `nat` field. Conditionals are expressed as mutually exclusive guarded
   postconditions instead of disjunctions.
6. **E9 interface:** §3 mandates E9 as an external entity, so the raw command is
   routed `F6 -> E9 -> F7`; E8 is always `monitor(E9)` (R-E-2).
7. **D1/D4 refresh:** E5->D1 and E6->D4 are modelled as store writes because §4
   says "refreshed by E5/E6", even though §5.1 assigns no in-function writer —
   recorded as OI-5.
8. **F3 ego_state:** modelled as `F1 -> F3` (and split to F3.1/F3.3 at Level 1)
   so every input has a single named producer, satisfying R-G-4.

## Parent/child balance (Level 0 F3 <-> Level 1)

| L0 F3 interface | L1 realisation |
|---|---|
| IN `predicted_trajectories` (F2) | -> F3.1 |
| IN `ego_state` (F1) | -> F3.1 and -> F3.3 |
| IN `traffic_rules` (D4, read) | -> F3.2 |
| IN `driver_intent` (E3) | -> F3.3 |
| IN `route` (F4) | -> F3.3 |
| IN `hd_map_segment` (D1, read) | -> F3.3 |
| OUT `manoeuvre` (-> F5) | <- F3.3 |
| OUT `warning` (-> E7) | <- F3.2 |

All eight boundary interfaces are preserved; none is added, none removed.

## Traceability matrix (R-G-2)

| Requirement clause | DFD element(s) | Realised by |
|---|---|---|
| R-SCOPE-1 | F1..F7 | whole system model |
| R-SCOPE-2 | E1..E9 | external entities |
| R-SCOPE-3 | F1..F7 | functional allocation only |
| R-SCOPE-4 | F3, F3.1, F3.2, F3.3 | two-level split |
| R-E-1 | E7, E8, F3, F7 | boundary_out flows |
| R-E-2 | E9, E8, F6, F7 | monitoring/arbitration path |
| R-D-1 | D1..D4, F1, F5 | store ownership (see OI-5) |
| R-D-2 | F1..F7 | store_read flows |
| R-L0-1 | F1..F7, D1..D4, E1..E9 | exact element counts |
| R-L1-1 | F3.1, F3.2, F3.3 | three sub-processes |
| R-G-1 | F1..F7, F3.1..F3.3 | pre/postconditions in dictionary |
| R-G-2 | all elements | this matrix |
| R-G-3 | all elements | no synthetic element at L0/L1 |
| R-G-4 | all processes | explicit named directed flows |
| R-G-5 | all processes | consumers lists |
| R-G-6 | all processes | field-level guards, vacuous null checks excluded |
| F1 | 1.0 | process |
| F2 | 2.0 | process |
| F3 | 3.0 (+3.1/3.2/3.3) | process / refinement |
| F4 | 4.0 | process |
| F5 | 5.0 | process |
| F6 | 6.0 | process |
| F7 | 7.0 | process |
| D1 | cylinder D1 | store (read by F1,F2,F3,F4,F5; refreshed by E5) |
| D2 | cylinder D2 | store (written by F1) |
| D3 | cylinder D3 | store (written by F1; read by F6,F7) |
| D4 | cylinder D4 | store (read by F3,F5,F7; refreshed by E6) |
| E1 | box E1 | raw_sensor_data in -> F1 |
| E2 | box E2 | gnss_imu in -> F1 |
| E3 | box E3 | driver_intent in -> F3/F3.3 |
| E4 | box E4 | destination in -> F4 |
| E5 | box E5 | map_data in -> D1 |
| E6 | box E6 | traffic_rules in -> D4 |
| E7 | box E7 | warning out <- F3/F3.2 |
| E8 | box E8 | checked_cmd out <- F7 |
| E9 | box E9 | actuator_cmd F6 -> F7 |
| F3.1 | 3.1 | TTC Computation |
| F3.2 | 3.2 | Risk Classification |
| F3.3 | 3.3 | Maneuver Planning |
| N-1 | F3.3, F1 | AEB up to 130 km/h (sizing context) |
| N-2 | F3.2 | warning by TTC = 2.0 s |
| N-3 | F3.3 | >30 km/h impact-speed reduction |
| N-4 | F3.3 | CCRm envelope |
| N-5 | F5 | RSS minimum safe distance |
| N-6 | F6, F7 | RSS braking profile |
| N-7 | F5, F7, F1 | Euclidean lateral envelope |
| A-1 | F3.3 | 6.0 m/s2 emergency deceleration |
| A-2 | F5, F7 | RSS parameter set |
| A-3 | F6, F7 | 3.0 m/s2 longitudinal limit |
| A-4 | F1, F6 | 3.5 rad/s yaw-rate envelope |
| A-5 | F3.2 | 3.0 / 1.5 s risk thresholds |
| A-6 | F6, F7 | +/-1.0 steering envelope |
| A-7 | F2, F3.1 | 3.0 s prediction horizon |

## Answers to the four open issues (§11)

**OI-1 — Is the seven-function split sufficient; is a separate driver-monitoring
(L2 handover) function needed?**
The model keeps the mandated seven (R-L0-1, F1..F7). Driver attention already
arrives as a field of E3 `driver_intent` and is consumed by F3 (and F3.3 for
accelerate-request arbitration), so handover *state* is represented without a new
element. However R-SCOPE-1 fixes SAE L2 (driver supervises); active handover
execution would need timing and a dedicated monitor absent from the spec.
Conclusion: sufficient for the stated *functional* allocation; insufficient if
active handover management is in scope. Impact: medium. Recorded as OI-1.

**OI-2 — Is D3 ownership (written by F1, read by F6/F7) acceptable?**
Acceptable as modelled: D3 is a single-writer store (F1 only), which satisfies
R-D-1; F6/F7 reads are explicitly assigned by §5.1, satisfying R-D-2. The DFD
shows the split cleanly (one solid write edge from 1.0, two dashed read edges to
6.0 and 7.0). The concern is only architectural: a localisation-owned store
becomes a safety-critical input to the shield, so a dedicated writer and a validated
snapshot would improve assurance. The current spec mandates neither, so the
model leaves it open. Impact: medium. Recorded as OI-2.

**OI-3 — Is a timing (cycle-time) requirement needed for the emergency branch?**
Yes. §7/§8 fix magnitudes (6.0 m/s2, 3.0 s, 1.5 s) but never a planning/actuation
period. Without a bound on the F2->F3.1->F3.2->F3.3->F5->F6->F7 latency, the
"no later than TTC = 2.0 s" warning (N-2) and the emergency intervention cannot be
guaranteed. The model therefore includes no cycle-time number (none is given) and
flags this as the highest-impact gap. Impact: high. Recorded as OI-3.

**OI-4 — Is the AEB branch the right Level-1 refinement; should Level 1 refine
F6/F7?**
The model follows R-SCOPE-4 and R-L1-1, which explicitly name the F3 emergency
branch — so it is the correct choice *for this specification*. It is also where
the §8 thresholds (A-1, A-5) and the E7 warning originate, giving the richest
formalisation surface. Refining F6/F7 would instead expose the arbitration
envelope (A-3/A-6, N-6/N-7), which is equally safety-critical yet left unmandated
here. Impact: medium. Recorded as OI-4.

## Validation notes

* Both JSON files parse with `json.load`; ids are unique within each file;
  parent-owned ids in the child resolve in `MES_M3_L0.json`.
* DOT sources use standard Graphviz syntax; render with `dot -Tsvg M3_L0.dot -o M3_L0.svg`
  (and likewise for L1) if Graphviz is installed.
