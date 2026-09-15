# Evaluation Profile

An Evaluation Profile defines the smallest useful evaluation and verification plan for a task. It governs the authoritative assessment path; it does not dictate a single reasoning strategy.

## Responsibilities

- Select task-relevant evaluation dimensions.
- Define hard gates, deterministic checks, external verification, and model-based evaluators.
- Set evaluation effort, verification budget, revision budget, and stopping conditions.
- Validate that thresholds, weights, required dimensions, and budgets form a coherent policy before execution.
- Provide the control boundary against which candidates produced through deliberation are assessed.

## Deliberation relationship

Evaluation Profile and deliberation are complementary but distinct.

The profile answers:

> **What must be true for this task to be considered acceptable?**

Deliberation answers:

> **How should the system reason, reconsider, or change approach before presenting a candidate for evaluation?**

A profile may influence whether additional deliberation is warranted through task characteristics, risk, effort, or budgets, but it must not encode a rigid universal reasoning procedure. Deliberation remains bounded and non-authoritative.

## Policy contract

An `EvaluationProfile` is executable policy, not just configuration. Its dimension set is authoritative for model evaluation; required dimensions, dimension floors, confidence thresholds, and overall thresholds must reference that set and remain within valid bounds. Verification and revision budgets are non-negative execution limits. Invalid profiles fail at construction rather than silently degrading into an ambiguous runtime policy.

## Deterministic schema verification

When a Task Contract carries an explicit `output_schema`, the profile selects the deterministic `json_schema` check. This preserves the user's explicit structured-output requirement while keeping verification bounded and provider-neutral.

The schema verifier is preferred over model judgment for directly verifiable structural properties, but it does not replace semantic evaluation by the Secondary or deliberative reasoning that precedes it.

## External source verification

Research, source, citation, and factual tasks select `source_verification` as an external check while keeping `groundedness` and `evidence_quality` as model-evaluated dimensions. The source verifier checks only whether cited HTTP(S) sources are reachable; it does **not** claim that a source proves the candidate's factual statements. Missing citations fail closed when the Task Contract explicitly requires citations.

External checks are bounded by the verification budget and use provider-neutral evidence. Unsafe/private network targets are rejected by the default HTTP source fetcher.

## Principles

- Do not run every possible evaluator on every task.
- Deterministic and external checks should be preferred when they can directly verify a property.
- Explicit user mode is authoritative for expected effort/depth.
- Lite reduces effort, not correctness requirements.
- Auto may select additional reasoning or verification effort based on task characteristics and risk without changing user intent.
- More inference compute is a resource, not proof of correctness.
- Do not equate effort with repeated verification passes. Future effort controls may govern deliberation depth, reflection opportunities, alternative approaches, correction attempts, and verification/escalation together.
- A policy field must have runtime semantics before it is treated as authoritative foundation behavior.
- Deliberation may explore and propose; evaluation and verification establish evidence; decision authority enforces the final policy.

The runtime representation is `engine/revise/models.py`; profile construction is `engine/revise/profile.py`; external source verification is implemented in `engine/revise/external.py`.
