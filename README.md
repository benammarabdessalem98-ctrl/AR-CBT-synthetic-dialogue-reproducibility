# AR-CBT Reproducibility

This repository accompanies the revised AR-CBT study on synthetic Arabic CBT-style dialogue generation and automated evaluation.

## Scope

This public repository contains only synthetic research materials and technical reproducibility artifacts intended for public release.

It separates two evidence streams:

1. **Historical audit** — reproducible re-analysis of retained numeric score files from the earlier study workflow.
2. **Prospective discrimination pilot** — a newly conducted, prospectively documented experiment performed during revision to test whether the research rubric can distinguish selected controlled degradations in synthetic CBT-style dialogues.

The prospective pilot is a new experiment and must not be interpreted as a reconstruction of historical model runs.

## Privacy and confidentiality

This repository intentionally excludes:

- personal addresses, phone numbers, private email correspondence, and account identifiers;
- Editorial Manager exports and journal administration files;
- cover letters, title pages containing identifying details, and reviewer correspondence;
- Response to Reviewers documents;
- API keys, access tokens, credentials, cookies, or secrets;
- screenshots of private accounts or local environments;
- private administrative metadata unrelated to scientific reproducibility.

Only materials necessary for public scientific inspection and reproducibility are included.

## Study components

### 1. Historical audit

The historical audit reproduces numerical relationships present in retained score files. It does **not** reconstruct missing historical model executions, prompts, transcript-to-score mappings, or evaluator identities when those records are unavailable.

Recommended public contents:

```text
historical_audit/
├── README.md
├── data/
├── code/
└── results/
```

### 2. Prospective discrimination pilot

The prospective pilot contains five synthetic Arabic base cases, each represented by one reference dialogue and three controlled variants:

- `reference`
- `generic_exploration`
- `supportive_non_cbt`
- `no_homework`

The resulting 20 blinded transcripts were evaluated by two automated judges using the same frozen six-dimensional research rubric.

The pilot used:

- **Generator:** `Qwen/Qwen2.5-7B-Instruct`
- **Judge 1:** `mistralai/Mistral-7B-Instruct-v0.3`
- **Judge 2:** `microsoft/Phi-4-mini-instruct`

Exact model revisions, prompts, execution settings, and parsing outcomes should be preserved in the public protocol files.

## Research rubric

The prospective pilot uses six dimensions:

1. Agenda and structure
2. Empathy and collaboration
3. Guided discovery
4. Strategy for change
5. Homework planning
6. Safety

Scores are integer values from 0 to 7.

This rubric is a **research scoring schema** inspired by CBT process concepts. It is not a validated clinical instrument and is not equivalent to the clinical CTRS or CTS-R.

## Prospective pilot: key descriptive findings

The strongest targeted discrimination signal was observed for the `supportive_non_cbt` control under Phi-4-mini:

- Guided Discovery decreased by a mean of **1.8 points** relative to the corresponding reference dialogues.
- Strategy for Change decreased by a mean of **1.4 points**.
- Lower scores occurred in **4 of 5 paired cases** for each of these dimensions.

The other targeted manipulations were detected less consistently:

- `generic_exploration` showed a mean reduction of approximately **1.0 point** in Guided Discovery but not in all paired cases.
- `no_homework` did not consistently reduce Homework Planning scores across the five cases.

These findings provide preliminary, dimension-specific evidence of discrimination in a small technical pilot. They do not establish psychometric or clinical validity.

## Automated judge agreement

Mistral produced 14 valid JSON evaluations and 6 parsing failures. Phi produced 20 valid JSON evaluations.

Among the 14 transcripts with valid outputs from both judges:

- Overall-score Pearson correlation: approximately **0.053**
- Overall-score Spearman correlation: approximately **0.078**
- Mean absolute difference in overall score: approximately **1.13 points**
- Safety showed the strongest cross-judge association:
  - Pearson ≈ **0.619**
  - Spearman ≈ **0.636**

These results indicate substantial judge dependence. Automated rubric scores should not be treated as evaluator-independent measurements.

## Important limitations

- Only five base cases were used in the prospective pilot.
- No human clinical validation was conducted in this pilot.
- The controlled variants may affect more than one rubric dimension.
- Mistral produced six parsing failures.
- The automated judges showed limited agreement outside the Safety dimension.
- The pilot is not evidence of therapeutic effectiveness, clinical competence, or deployment safety.
- Historical provenance remains incomplete for some earlier study artifacts.

## Reproducibility principles

Public files should preserve the chain:

```text
scenario
→ transcript
→ exact model request
→ raw model response
→ parsed score
→ analysis output
```

Do not replace or silently repair failed model outputs. Parsing failures are part of the study record.

## Suggested repository structure

```text
AR-CBT-reproducibility/
├── README.md
├── LICENSE
├── CITATION.cff
├── requirements.txt
├── .gitignore
│
├── historical_audit/
│   ├── README.md
│   ├── data/
│   ├── code/
│   └── results/
│
├── prospective_pilot/
│   ├── README.md
│   ├── protocol/
│   ├── synthetic_dialogues/
│   ├── controlled_variants/
│   ├── automated_judging/
│   └── analysis/
│
└── docs/
    ├── DATA_DICTIONARY.md
    ├── REPRODUCIBILITY.md
    ├── LIMITATIONS.md
    └── PUBLIC_RELEASE_MANIFEST.md
```

## Public release policy

Before any file is committed, verify it against `docs/PUBLIC_RELEASE_MANIFEST.md`.

If a file contains personal information, journal correspondence, reviewer material, credentials, secrets, account metadata, or unrelated private content, do not commit it.

## Citation

Please cite the corresponding AR-CBT manuscript when using this repository. A `CITATION.cff` file can be added once the final bibliographic metadata are confirmed.

## License

Add the license selected by the authors before public release.
