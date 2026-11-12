# Reproduction and release checklist — V11

1. Install the small analysis dependency set in `requirements.txt` in a separate environment.
2. Run `python prospective_pilot/code/reproduce_pilot.py` and the tests in `prospective_pilot/tests`.
3. Inspect `analysis_v11/SUMMARY.json`, parsing-policy tables, intervention-scope table and all per-case deltas.
4. Run the historical audit with a NEW `--out` directory. Original results must not be overwritten.
5. Optional GPU scripts require explicit execution authorization and a new external output directory. They are not needed to verify published arithmetic.
6. Preserve original raw files and recorded failures. The code distinguishes processing failure from clinical-quality measurement.
7. Upload the V11 update to the correct repository; verify public file access and only then finalize manuscript availability wording.
8. Record an actual commit/release identifier when it exists. Do not invent a tag or DOI.

The source archives describe a five-case technical pilot; no code can recreate unavailable historical provenance or count as an independent human or safety evaluation.
