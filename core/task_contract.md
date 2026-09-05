# Task Contract

The Task Contract is the canonical representation of user intent passed into the engine.

## Responsibilities

- Preserve the user's goal, requirements, constraints, desired output characteristics, and relevant context.
- Record missing context explicitly rather than silently inventing it.
- Preserve explicit mode and user constraints as authoritative.
- Define success criteria and verification requirements when known.

## Principles

1. User intent is authoritative.
2. Scope is locked to the requested task.
3. Missing information is represented explicitly.
4. Assumptions must be distinguishable from known context.
5. Auto mode may choose effort, but must not change the user's intent.

The runtime representation lives in `engine/revise/models.py` and is wrapped by engine state in `engine/contracts.py`.
