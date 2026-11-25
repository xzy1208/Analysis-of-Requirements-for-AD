# MES — Model Exchange Schema v1

A machine-readable envelope that every one of the four requirement models
(M1 human SOFL, M2 LLM SOFL, M3 LLM DFD, M4 LLM UML) must deliver, so that the
six quality dimensions can be computed **by the same script** over all models.

Each model delivers one JSON file per level: `MES_<model>_<level>.json`
(e.g. `MES_M2_L0.json`, `MES_M2_L1.json`).

---

## 1. Top-level structure

```json
{
  "model_id": "M2",
  "model_title": "LLM-generated SOFL replica (single pass)",
  "level": "L0",
  "parent_module": null,
  "provenance": {
    "producer": "human" | "llm",
    "llm_family": "string or null",
    "generation_date": "YYYY-MM-DD",
    "passes": 1,
    "prompt_summary": "one-line description of the prompt actually used",
    "self_review_performed": false
  },
  "elements": [ ... ],
  "stores": [ ... ],
  "externals": [ ... ],
  "flows": [ ... ],
  "traceability": [ ... ],
  "open_issues": [ ... ]
}
```

`parent_module` is `null` for the root model and the root model's name for a
child model.

---

## 2. `elements` — one entry per function / process / class-method group

```json
{
  "id": "F1",
  "kind": "function",
  "name": "Perception_Localization",
  "responsibility": "one sentence, copied or paraphrased from the spec clause",
  "inputs":  [ {"name": "raw_sensor_data", "source": "E1"} ],
  "outputs": [ {"name": "objects", "consumers": ["F2"]} ],
  "stores_read":    ["D1"],
  "stores_written": ["D2", "D3"],
  "preconditions":  ["raw_sensor_data <> null", "map_data <> null"],
  "postconditions": [
     {"guard": "true", "effect": "objects <> null and objects.lead_speed >= 0"}
  ],
  "quantified": true,
  "invariants": ["..."],
  "notes": ""
}
```

Rules:

* `id` is a **stable local identifier**: use the spec's own IDs (`F1`…`F7`,
  `F3.1`…`F3.3`, `D1`…`D4`, `E1`…`E9`) wherever the element realises that spec
  item. If a modeller introduces an element that has **no** spec ID, give it a
  synthetic id `X1`, `X2`, … and declare it in `open_issues` (this is how
  hallucinated elements become visible).
* `inputs[].source` is the **spec id** of the producer (`E1`…`E9`, `D1`…`D4`,
  or another element's id).
* `outputs[].consumers` lists the spec ids of the consumers.
* `preconditions` / `postconditions` are given in the **same restricted
  expression syntax** as the source notation (SOFL syntax for M1/M2; for M3/M4
  use plain Boolean expressions over the same names). Keep them verbatim, do not
  paraphrase into prose.
* `quantified` = `true` iff at least one postcondition contains a numeric
  comparison (`>`, `>=`, `<`, `<=`, `=`) against a value that appears in §7/§8 of
  the specification.

---

## 3. `stores`

```json
{
  "id": "D2",
  "name": "Object_Track_DB",
  "content": ["obj_count", "lead_id", "lead_pos_x", "lead_pos_y", "lead_speed"],
  "owner": "F1",
  "writers": ["F1"],
  "readers": ["F2"],
  "persistent": true
}
```

---

## 4. `externals`

```json
{ "id": "E1", "name": "raw_sensor_data", "direction": "in",
  "content": ["camera frames", "radar frames", "lidar frames"], "consumers": ["F1"] }
```

`direction` is `"in"` or `"out"`.

---

## 5. `flows` — the explicit, named, directed data dependencies

```json
{ "name": "ego_pose",
  "producer": "F1",
  "consumer": "F2",
  "kind": "active" | "store_read" | "store_write" | "boundary_in" | "boundary_out",
  "carries": ["ego_pose"] }
```

* Every element input and every element output must be backed by exactly one
  entry in `flows`.
* A flow with two consumers must be declared twice (two `flows` entries with the
  same `name` but different `consumer`), so that "shared flow" defects are
  visible.

---

## 6. `traceability`

```json
{ "requirement": "R-F1-2", "elements": ["F1"], "realised_by": "postcondition",
  "note": "" }
```

* One entry per requirement clause of the specification that the model claims to
  realise. `requirement` uses the spec's clause IDs (`R-SCOPE-1`, `R-E-1`,
  `R-D-1`, `R-L0-1`, `R-L1-1`, `R-G-1`…`R-G-6`, `F1`…`F7`, `F3.1`…`F3.3`,
  `N-1`…`N-7`, `A-1`…`A-7`).
* `elements` lists the model elements that realise the clause.
* Clauses that the model does **not** realise are simply **absent** from the
  list — do not fabricate coverage.

---

## 7. `open_issues`

```json
{ "id": "OI-1", "issue": "one sentence",
  "related_requirement": "R-xx or Fx", "impact": "low|medium|high" }
```

Must contain the four issues the specification asks about (§11 of the spec), plus
any element or assumption the modeller had to introduce.

---

## 8. `provenance` — record it honestly

* `passes`: 1 = single-shot; 2 or more = generate → self-check → revise.
* `self_review_performed`: `true` only if a second, separate pass actually
  checked the first pass against the specification.
* `prompt_summary`: the actual instruction given to the generator.

---

## 9. Validation

The delivered JSON must satisfy:

1. every `id` in `elements` / `stores` / `externals` is unique;
2. every `inputs[].source` and every `flows[].producer` / `flows[].consumer`
   resolves to an id that exists (in the same file for L0, or in the parent's
   file for a child model — for a child model, mark parent-owned ids with
   `"level": "parent"` in the element record);
3. `traceability[].requirement` values are ids that exist in the specification;
4. the file parses as strict JSON (no comments, no trailing commas).
