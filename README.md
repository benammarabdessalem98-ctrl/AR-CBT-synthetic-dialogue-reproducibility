# AR-CBT synthetic-dialogue reproducibility — V11 update

## Scope and evidence
This repository distinguishes the **historical arithmetic audit** from a separate **five-case controlled-edit pilot**. It is research material, not a validated clinical scoring instrument, treatment system, or tested Guardian.

The historical 80-record files retain three score columns. Their numeric relationships can be reproduced, but original evaluator identities, transcript links, and former 150-pair/50-prompt archives are missing. Legacy column labels do not mean human annotation.

The new pilot has five MSA synthetic cases, four scripted patient turns per case, Qwen2.5-7B-Instruct reference responses, and three localized text edits per case. The 20 transcripts were evaluated by Mistral-7B-Instruct-v0.3 and Phi-4-mini-instruct. No human clinical ratings were collected. Exact recorded model revisions and raw request/response traces are retained.

## What V11 changes
The V11 update leaves the original records and primary scores unchanged. It supplies:
- executable offline reproduction of primary statistics and post-unblinding diagnostics;
- 20 standalone reconstructed labelled transcripts and 20 minimal blinded input files, each checked against archived judge requests and original message hashes;
- explicit edit operators, primary parsing rules and equal-policy parsing checks;
- tests and a Kaggle notebook;
- optional scripts for **new-run-only** GPU call replay and dialogue regeneration, with no claim that those new calls were executed for V11.

The scripts were written after unblinding. They are documented reimplementations, not an authenticated original notebook.

## Run offline first
From the repository root:

```bash
python -m pip install -r requirements.txt
python prospective_pilot/code/reproduce_pilot.py
python -m unittest discover -s prospective_pilot/tests -v
python historical_audit/code/reanalyse_scores.py --out historical_audit/recomputed_v11
```

No GPU, model download, credentials, or API call is needed for these numerical checks. Newly computed pilot outputs are written to `prospective_pilot/analysis_v11/`, not over the preserved `analysis/` or raw model records. A conflicting existing output stops execution rather than silently overwriting it.

## Main results and their limits
Under the original primary policies, Mistral has 14 accepted ratings and six failures; Phi has 20 accepted ratings **after removal of outer Markdown fences**. These are format/schema outcomes, not accuracy against clinicians. In a secondary equal-policy check, raw strict parsing accepts 14 Mistral outputs and zero Phi outputs; outer-fence-only normalization applied equally accepts 14 and 20. No internal JSON value is converted or repaired.

With Phi, replacing therapist responses 2–3 with generic support yields mean control-minus-reference differences of −1.8 in Guided Discovery and −1.4 in Strategy for Change (four decreases in five paired cases each). The reference is not an expert-confirmed good session. The `no_homework` identifier means **replacement of the final response only**; earlier planning content remains. It must not be interpreted as total removal of homework from the conversation. See `docs/INTERVENTION_SCOPE.md`.

On 14 jointly accepted outputs, overall Pearson correlation is 0.053, Spearman correlation 0.078, mean Phi-minus-Mistral difference +0.202 and mean absolute difference 1.131 points. Safety has the highest score association but only 6/14 exact matches. These low-risk score comparisons do not validate crisis detection or safety.

All primary pairs, missing-pair counts, six dimensions, secondary aggregation variants and base-case influence checks are published. Twenty variants are nested in only five base cases. No population-level p-value or clinical effectiveness claim is made.

## Structure

```text
historical_audit/          retained numeric audit; incomplete historical provenance
prospective_pilot/
  protocol/               original frozen prompts/rubric/execution records
  synthetic_dialogues/    raw generator transcripts and calls
  controlled_variants/    V11 reconstructions and minimal judge-facing texts
  automated_judging/     raw Mistral/Phi calls; failures preserved
  analysis/               retained V1 outputs and public blinding map
  analysis_v11/           executed post-unblinding checks
  code/                   offline reproduction and new-run-only GPU scripts
  tests/                  implementation checks, not scientific validation
  notebooks/              Kaggle/standard Jupyter offline workflow
  technical_metadata/     recorded model/environment information
  docs/                   edit-scope and code-provenance documentation
docs/                     public release, privacy and verification manifests
```

## GPU scripts
`replay_models.py --role phi --dry-run` checks the plan without running a model. Actual GPU use requires `--execute --out <NEW_DIRECTORY>` and, when necessary, explicit acknowledgement of recorded environment differences. Archived input IDs are checked against tokenization before calls. Therapist replay conditions on the **recorded** preceding histories; `generate_new_dialogues.py` instead generates new evolving histories from the frozen scripts. Never substitute either new output for the original study data. GPU paths were not executed in the V11 offline audit.

## Privacy and release status
Only synthetic research data, code and non-identifying technical records are intended for public release. This bundle excludes title pages, author contacts, cover letters, reviewer/editor correspondence, screenshots, account credentials and secrets. `.gitignore` is not a privacy guarantee; inspect contents before committing. Checksums detect changes to included bytes; they are not proof of scientific validity or historical authenticity.

The V11 bundle is prepared locally; no automatic upload, GitHub release tag or DOI is asserted. Authors must publish/check the update before claiming it is accessible in the submitted paper. Bibliographic and licensing choices remain for the authors; no new license or author identity has been invented here.
