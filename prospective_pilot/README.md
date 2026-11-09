# Prospective discrimination pilot

This directory contains the public research artifacts for a new prospective technical pilot conducted during revision.

## Design

Five synthetic Arabic base cases were used. Each base case contributed four conditions:

- `reference`
- `generic_exploration`
- `supportive_non_cbt`
- `no_homework`

This yields 20 transcripts.

The transcripts were blinded as B001–B020 before automated judging. The public post-study mapping is available in `analysis/blinding_map_public.json`.

## Models

- Generator: `Qwen/Qwen2.5-7B-Instruct`
- Automated judge 1: `mistralai/Mistral-7B-Instruct-v0.3`
- Automated judge 2: `microsoft/Phi-4-mini-instruct`

Exact recorded revision hashes and execution metadata are retained in the protocol/technical metadata files.

## Judging

Both judges used the same frozen six-dimensional research rubric:

1. Agenda and structure
2. Empathy and collaboration
3. Guided discovery
4. Strategy for change
5. Homework planning
6. Safety

Mistral produced 14 valid JSON evaluations and 6 parsing failures. Phi produced 20 valid JSON evaluations. Parsing failures are preserved rather than silently repaired.

## Public artifacts

- `protocol/` — cases, prompts, rubric, schemas, execution protocols, parsing rules.
- `synthetic_dialogues/reference/` — reference transcripts plus generator request/response traces.
- `automated_judging/` — exact request/response records for Mistral and Phi.
- `analysis/` — post-unblinding score tables and condition-level analyses.
- `technical_metadata/` — generator preparation and loading metadata.

## Limitations

This is a small technical pilot with five base cases. It is not a clinical validation study. No human clinical ratings were collected for this pilot. Controlled edits may affect multiple rubric dimensions. Automated judges showed substantial judge dependence outside the Safety dimension.
