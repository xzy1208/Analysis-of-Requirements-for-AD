# ADAS Requirements Modeling — Reproduction Package

Companion artefacts for the paper *Requirements Modeling for Autonomous Driving
Systems: A Cross-Notation Comparison of Manual SOFL and LLM-Generated Models*.

All figures in the paper are schematic diagrams of the study's own specification
or renderings of the study's own artefacts; no third-party figure is reproduced.

## Layout

- `NL-RQ-ADAS-v1_spec.md`, `MES_schema.md` — unified input specification and exchange schema.
- `models/` — the five models (M1 manual SOFL, M1.1 threshold-table revision,
  M2 same-notation LLM control, M3 DFD, M4 UML, M5 state machine).
- `score_models_v2.py`, `scores_v2.json`, `score_table_v2.md` — indicators and scores.
- `coverage_manual.json`, `coverage_criterion_sensitivity.py/.json` — coverage labels and the three-criterion sensitivity check.
- `experiment_kit/prompt_rerun/` — prompts, raw rerun outputs, and all analysis scripts (tier decomposition, formal criterion checker, I4 range).
- `experiment_kit/second_annotator_kit/` — scripts, the discriminating-atom sampling template, and the **blank** annotator package (`handover/`). The primary labels are already public in `coverage_manual.json` (the paper reports the scores), so the sampling template repeats them; what is deliberately excluded is the **completed second-rater forms and results**, so that a fresh replication can recruit a new rater without seeing any prior judgements.
- `blind_review_pack/` — desensitised inputs and prompt for replicating the reviewer study.
- `figures/final`, `figures/pdf` — rendered figures; the two SOFL-tool screenshots are `fig2_M1_cdfd_L0_tool.png` and `fig_M1_cdfd_L1_tool.png`.
- `paper_draft_v3.md` (English final) and `paper_draft_v2_中文审核版.md` (Chinese review version).

## Notes

The double-annotation kit was executed in this study: an independent second
rater re-labelled the 30 discriminating judgements (Cohen's kappa = 0.650
unweighted, 0.723 linearly weighted, 80.0% exact agreement). The blank workbook
and form are provided so that the procedure can be repeated; the completed
second-rater forms and their results are deliberately excluded, so that a fresh
replication can recruit a new rater without seeing any prior judgements. The
primary labels themselves are public in `coverage_manual.json`, as required to
reproduce the reported scores.

See `MANIFEST.md` for the full file list with SHA-256 checksums.
