# Evaluation Result

An Evaluation Result is the normalized output of verification for one candidate response.

## Required concepts

- Decision: `ACCEPT`, `REVISE`, or `ASK`.
- Overall score and confidence, when meaningful.
- Per-dimension results with status and reasoning.
- Issues with type, severity, location, and supporting evidence.
- Revision instructions when revision is possible.
- Verification requirements and provenance.

## Principles

- Confidence is distinct from quality score.
- Unknown evaluation is not a passing evaluation.
- Evaluators should explain judgments, not only emit a scalar.
- Detection, localization, diagnosis, correction, and verification are distinct stages.
- Evidence provenance must remain attached to findings.

The runtime model lives in `engine/revise/models.py`.
