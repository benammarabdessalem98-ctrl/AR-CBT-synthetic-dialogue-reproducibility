# PUBLIC RELEASE MANIFEST

## Purpose

This manifest defines what may be published in the public AR-CBT reproducibility repository and what must remain private.

The repository should contain only materials necessary for scientific transparency, reproducibility, and verification.

---

## PUBLIC — allowed to publish

### Research code
- analysis scripts;
- reproducibility notebooks;
- parsing and validation code;
- plotting scripts;
- environment or dependency files;
- tests used to verify calculations.

### Synthetic research data
- synthetic scenarios;
- synthetic patient utterances;
- synthetic therapist/model responses;
- controlled synthetic variants;
- blinded transcript identifiers;
- public de-blinding maps containing only research identifiers;
- automated judge outputs;
- parse failures and raw model outputs where needed for reproducibility.

### Experimental protocol
- frozen prompts;
- rubric definitions;
- output schemas;
- model IDs;
- immutable model revision hashes;
- generation parameters;
- execution order;
- blinding procedure;
- technical parsing rules;
- reproducibility manifests;
- SHA-256 hashes.

### Analysis outputs
- descriptive statistics;
- paired control-versus-reference differences;
- judge-agreement tables;
- condition summaries;
- public result CSV/JSON files;
- non-identifying figures.

### Scientific documentation
- README files;
- data dictionary;
- reproducibility notes;
- limitations;
- public methodological supplements that contain no personal or editorial information.

---

## PRIVATE — do not publish

### Personal information
- home address;
- private telephone numbers;
- personal identification numbers;
- private contact information not already intentionally public;
- account identifiers;
- authentication metadata.

### Credentials and secrets
- API keys;
- Hugging Face tokens;
- GitHub tokens;
- Kaggle credentials;
- cookies;
- session tokens;
- `.env` files;
- passwords;
- SSH keys;
- access tokens.

### Journal and editorial material
- cover letters;
- title pages containing identifying author details if not intended for repository publication;
- reviewer reports;
- Response to Reviewers;
- Editorial Manager exports;
- decision letters;
- confidential editor correspondence;
- screenshots of submission systems.

### Private working material
- screenshots of private accounts;
- local desktop screenshots;
- browser history;
- private file-system paths when they contain identifying information;
- temporary debugging files unrelated to the published experiment;
- draft documents containing unsupported or superseded claims;
- internal notes not required for scientific verification.

---

## PUBLIC de-blinding map

Do not publish a file named `PRIVATE_BLINDING_KEY.json`.

For final reproducibility, create a public neutral file such as:

```text
prospective_pilot/analysis/blinding_map_public.json
```

Allowed fields:

```json
{
  "blind_id": "B001",
  "base_case_id": "P04",
  "condition": "reference",
  "transcript_id": "P04__reference",
  "content_sha256": "..."
}
```

Do not include any personal information.

---

## Pre-commit privacy checklist

Before committing any file:

1. Open the file and inspect its contents.
2. Search for:
   - `@`
   - `token`
   - `secret`
   - `password`
   - `apikey`
   - `api_key`
   - `authorization`
   - `cookie`
   - `bearer`
   - `phone`
   - `address`
3. Confirm the file is required for scientific reproducibility.
4. Confirm it contains no journal correspondence.
5. Confirm it contains no reviewer/editor material.
6. Confirm it contains no personal account information.
7. Confirm model outputs are synthetic and non-identifying.
8. Confirm filenames do not reveal private administrative information.

If uncertain, keep the file private.

---

## Repository principle

**Public by scientific necessity, private by default.**

A file should be published only when it contributes directly to scientific transparency, verification, or reproducibility.
