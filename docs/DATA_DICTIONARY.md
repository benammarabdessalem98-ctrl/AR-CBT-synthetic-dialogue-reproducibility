# Data dictionary

## Historical audit

### `scores_80_original_columns.csv`
Retains the original column labels from the legacy score table. These labels are provenance labels only and do not imply human annotation.

### `legacy_summary_original_labels.csv`
Legacy one-row summary values retained for arithmetic verification.

## Prospective pilot

### IDs
- `P01`–`P05`: synthetic base-case identifiers.
- `B001`–`B020`: blinded transcript identifiers used during automated judging.

### Conditions
- `reference`: original generated dialogue.
- `generic_exploration`: controlled replacement of case-linked exploration with generic exploration.
- `supportive_non_cbt`: supportive response with targeted removal of case-linked CBT process.
- `no_homework`: controlled removal of the concrete closure/homework step.

### Rubric dimensions
- `agenda_structure`
- `empathy_collaboration`
- `guided_discovery`
- `strategy_change`
- `homework_planning`
- `safety`

Scores are integer values from 0 to 7 in the prospective pilot.

### Judge output status
- `valid_json`: output parsed and met the frozen schema.
- `parse_failure`: raw output retained but did not meet the frozen schema. No silent repair was performed.
