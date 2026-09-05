# Task Contract

**Status:** Foundation v0.1

The Task Contract is the canonical representation of the user's intended task for evaluation.

## Conceptual Contract

```json
{
  "goal": "string",
  "requirements": [],
  "constraints": [],
  "desired_output": {
    "format": null,
    "length": null,
    "style": null
  },
  "mode": "lite | basic | pro | auto",
  "known_context": [],
  "missing_context": [],
  "assumptions": [],
  "success_criteria": [],
  "verification_requirements": []
}
```

## Provenance

Important fields should eventually carry provenance:

- `user_explicit`
- `conversation_context`
- `secondary_inferred`
- `external_evidence`

Inference must never be silently presented as explicit user intent.

## Scope Lock

Once established, the contract defines the evaluation boundary. The evaluator may identify contradictions or missing information, but must not silently replace the goal.

## Missing Context

Missing context should be recorded when it materially affects task success. When the information cannot be safely inferred, prefer `ASK` over inventing an assumption.

## Success Criteria

Success criteria should be observable whenever possible.

Bad:

> Give a good answer.

Better:

> Return a valid Python function that passes the supplied tests.

## Mode

The explicit mode is authoritative. `auto` is the only mode where Revise may dynamically choose effort.

Mode affects reasoning effort, evaluator depth, verification breadth, revision budget, tool usage, and context-processing depth. It does not remove the baseline requirement for correctness.
