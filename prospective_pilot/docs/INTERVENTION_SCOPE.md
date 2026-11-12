# Exact scope of the retained controls

The archived condition IDs are preserved for traceability; the names are not proof that the intended construct was completely removed.

| ID | Edited therapist responses | What remains |
|---|---|---|
| reference | none | Generated comparator; no independent quality certification |
| generic_exploration | 2 only | Other exploration, patient reasoning and earlier/later interventions |
| supportive_non_cbt | 2 and 3 | Original responses 1 and 4; this is not a wholly non-CBT session |
| no_homework | 4 only | All earlier therapist and patient content; this is a closure-only edit |

The `analysis_v11/11_control_edit_scope.csv` is a mechanical comparison, not independent clinical annotation. All patient utterances remain fixed. Changed response length and interaction with fixed subsequent patient utterances are confounds, not controlled factors.

For example, P01/B003 retains the third therapist response proposing twenty minutes of writing per day even though the final closure is generic. A persistent Homework score cannot therefore uniquely diagnose evaluator insensitivity. Original Arabic text is in `controlled_variants/labeled/P01__no_homework.json`.

No original control or primary score was altered to obtain a stronger result. A future session-wide absence-of-target test must be a separately dated experiment with its own manipulation checks.
