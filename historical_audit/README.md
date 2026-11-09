# Historical audit

This directory contains a reproducible numerical audit of retained legacy score tables.

## Important scope limitation

The historical audit reproduces arithmetic relationships present in the retained score files. It does **not** reconstruct missing historical model executions, original prompts, evaluator identities, transcript-to-score links, or human validation.

The original workbook filenames included legacy labels such as `Human_Evaluation`. Those labels are not treated as evidence of human annotation. The public release therefore prioritizes neutral CSV exports and reproducibility code.

## Contents

- `data/` — retained numeric score exports and legacy summary values.
- `code/` — scripts, tests, and notebook used to reproduce the audit.
- `results/` — descriptive statistics, correlations, and record-level audit outputs.
- `documentation/` — provenance and source-verification notes.

No personal, editorial, reviewer, or account information is included.
