# Evaluation Profile

An Evaluation Profile defines the smallest useful evaluation plan for a task.

## Responsibilities

- Select task-relevant evaluation dimensions.
- Define hard gates, deterministic checks, external verification, and model-based evaluators.
- Set evaluation effort, verification budget, revision budget, and stopping conditions.

## Principles

- Do not run every possible evaluator on every task.
- Deterministic and external checks should be preferred when they can directly verify a property.
- Explicit user mode is authoritative for expected effort/depth.
- Lite reduces effort, not correctness requirements.
- Auto selects effort based on task characteristics and risk without changing intent.

The runtime representation is `engine/revise/models.py`; profile construction is `engine/revise/profile.py`.
