# Evaluation Profile

An Evaluation Profile defines the smallest useful evaluation plan for a task.

## Responsibilities

- Select task-relevant evaluation dimensions.
- Define hard gates, deterministic checks, external verification, and model-based evaluators.
- Set evaluation effort, verification budget, revision budget, and stopping conditions.
- Validate that thresholds, weights, required dimensions, and budgets form a coherent policy before execution.

## Policy contract

An `EvaluationProfile` is executable policy, not just configuration. Its dimension set is authoritative for model evaluation; required dimensions, dimension floors, confidence thresholds, and overall thresholds must reference that set and remain within valid bounds. Verification and revision budgets are non-negative execution limits. Invalid profiles fail at construction rather than silently degrading into an ambiguous runtime policy.

## Deterministic schema verification

When a Task Contract carries an explicit `output_schema`, the profile selects the deterministic `json_schema` check. This preserves the user's explicit structured-output requirement while keeping verification bounded and provider-neutral.

The schema verifier is preferred over model judgment for directly verifiable structural properties, but it does not replace semantic evaluation by the Secondary.

## External source verification

Research, source, citation, and factual tasks select `source_verification` as an external check while keeping `groundedness` and `evidence_quality` as model-evaluated dimensions. The source verifier checks only whether cited HTTP(S) sources are reachable; it does **not** claim that a source proves the candidate's factual statements. Missing citations fail closed when the Task Contract explicitly requires citations.

External checks are bounded by the verification budget and use provider-neutral evidence. Unsafe/private network targets are rejected by the default HTTP source fetcher.

## Principles

- Do not run every possible evaluator on every task.
- Deterministic and external checks should be preferred when they can directly verify a property.
- Explicit user mode is authoritative for expected effort/depth.
- Lite reduces effort, not correctness requirements.
- Auto selects effort based on task characteristics and risk without changing intent.
- A policy field must have runtime semantics before it is treated as authoritative foundation behavior.

The runtime representation is `engine/revise/models.py`; profile construction is `engine/revise/profile.py`; external source verification is implemented in `engine/revise/external.py`.
