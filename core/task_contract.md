# Task Contract

The Task Contract is the canonical representation of user intent passed into the engine. It defines what the system is trying to accomplish and the constraints against which any deliberated candidate must ultimately be assessed.

## Responsibilities

- Preserve the user's goal, requirements, constraints, desired output characteristics, and relevant context.
- Record missing context explicitly rather than silently inventing it.
- Preserve explicit mode and user constraints as authoritative.
- Define success criteria and verification requirements when known.
- Carry an explicit output schema when the user requires a machine-checkable structured result.
- Provide sufficient task context for bounded deliberation without allowing deliberation to redefine the user's intent.

## Deliberation relationship

The Task Contract is the boundary of the problem, not a prescribed reasoning algorithm.

Deliberation may:

- interpret the task within the contract;
- identify ambiguities or missing information;
- formulate assumptions that remain distinguishable from known context;
- plan and explore candidate approaches;
- challenge those assumptions and approaches;
- propose corrections or ask for clarification.

Deliberation must not silently alter the user's goal, constraints, required format, explicit mode, or explicit verification requirements. When ambiguity materially prevents reliable completion, the system should ask rather than invent intent.

## Output schema

`output_schema` is an optional JSON Schema object attached to the runtime `TaskContract`.

When present, the engine deterministically validates JSON output against a bounded, non-executing subset: primitive/object/array types, required properties, nested properties/items, additional-property control, enum/const, string length/pattern constraints, numeric minimum/maximum, array size/uniqueness constraints, and local `#/...` references. Unsupported or malformed schema constructs fail closed rather than being treated as valid.

Schema validation is a verification mechanism, not a replacement for semantic evaluation or deliberative reasoning: the Secondary still evaluates task success, correctness, relevance, and other applicable dimensions.

## Principles

1. User intent is authoritative.
2. Scope is locked to the requested task.
3. Missing information is represented explicitly.
4. Assumptions must be distinguishable from known context.
5. Deliberation may challenge an assumption but cannot promote an assumption into fact without supporting evidence.
6. Auto mode may choose effort, but must not change the user's intent, including explicit schema requirements.
7. A correction may change the reasoning approach, but may not change the task contract itself.

The runtime representation lives in `engine/revise/models.py` and is wrapped by engine state in `engine/contracts.py`.
