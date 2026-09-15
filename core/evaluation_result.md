# Evaluation Result

An Evaluation Result is the normalized output of evaluation and verification for one candidate response. It describes evidence about the candidate; it does not replace the authoritative decision layer.

## Required concepts

- Decision: `ACCEPT`, `REVISE`, or `ASK` when a decision is produced by the authoritative control layer.
- Overall score and confidence, when meaningful.
- Per-dimension results with status and reasoning.
- Issues with type, severity, location, and supporting evidence.
- Revision instructions when revision is possible.
- Verification requirements and provenance.
- Separation between observed findings and proposed corrections.

## Principles

- Confidence is distinct from quality score.
- Unknown evaluation is not a passing evaluation.
- Evaluators should explain judgments, not only emit a scalar.
- Detection, localization, reflection, diagnosis, correction, and verification are distinct stages.
- Evidence provenance must remain attached to findings.
- Reflection may identify possible failure causes and alternative approaches, but does not establish correctness.
- A correction plan is a proposed response to a finding, not evidence that the proposed correction is valid.
- A materially corrected candidate must be independently evaluated and verified again as applicable.
- Deterministic and directly verifiable evidence retains precedence over model opinion where the property is directly checkable.

## Reasoning boundary

Evaluation answers questions such as:

> How well does this candidate satisfy the task and its required quality dimensions?

Reflection is a separate deliberative capability that asks:

> What could make the reasoning or candidate wrong, incomplete, or based on a bad approach?

These capabilities may consume related model infrastructure, but their contracts and authority must remain distinct. The evaluation result must not silently turn a model's reflection or correction proposal into an acceptance decision.

The runtime model lives in `engine/revise/models.py`.
