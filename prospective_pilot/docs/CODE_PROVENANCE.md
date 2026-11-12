# Code provenance and what was executed

## Retained evidence
Original generator and judge request/response JSON files remain byte-for-byte unchanged from the provided archives. Model IDs, revision arguments and environment metadata are recorded evidence, not an independent audit of GPU weights.

## V11 reimplementations
`common.py` and `reproduce_pilot.py` were written after unblinding. They reproduce archived text edits, verify all 20 original content hashes and 40 request/response links, and reproduce primary statuses and targeted statistics. They also calculate explicitly secondary parsing parity, ordinal agreement, signed differences, aggregation and leave-one-base-case-out diagnostics.

These offline routines and 20 software tests were executed. The historical audit's existing tests and numerical rerun are separate. Software tests do not establish rubric or clinical validity.

`replay_models.py` replays individual archived calls using recorded input IDs and configurations in a fresh external output directory. Its therapist mode conditions each call on recorded prior turns. `generate_new_dialogues.py` permits a separate evolving-history new run from frozen scripted inputs. Both are implementation aids, not claims of additional collected evidence. Their syntax and dry-run paths were checked; full GPU execution was not performed here.

## No hidden repairs
Primary Mistral failures remain failures; integer-like strings are not converted. Primary Phi normalization remains the original outer-fence-only rule. Secondary common parsing counts do not replace these primary statuses. No labels or scores from the other judge enter model-facing requests.

## Operational rubric
The actual pilot uses `protocol/rubric_v1.json`, with generic anchors and dimension definitions. It must not be silently substituted with more elaborate conceptual examples from a manuscript appendix. The output parser checks field structure, not the correctness of evidence or clinical judgement.
