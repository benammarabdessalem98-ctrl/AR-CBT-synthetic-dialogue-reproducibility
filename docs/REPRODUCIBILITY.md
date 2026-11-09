# Reproducibility guide

## Historical audit

1. Create a Python environment using `historical_audit/code/requirements.txt`.
2. Run the included audit script on the public CSV files.
3. Compare generated outputs with `historical_audit/results/`.

## Prospective pilot

The repository publishes the frozen protocol and the resulting request/response traces. Exact LLM text generation may vary across hardware/software stacks even when model revision hashes are fixed.

For verification:
1. Inspect `prospective_pilot/protocol/`.
2. Inspect generator traces under `synthetic_dialogues/reference/`.
3. Inspect blinded judge requests/responses under `automated_judging/`.
4. Join B001–B020 to conditions using `analysis/blinding_map_public.json`.
5. Recompute the CSV summaries in `analysis/`.

Parsing failures should remain failures; do not retrospectively repair or drop them without reporting that change.
