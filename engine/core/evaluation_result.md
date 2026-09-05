# Evaluation Result

**Status:** Foundation v0.1

The Evaluation Result is the normalized output of one evaluation pass after evidence fusion.

## Conceptual Schema

```json
{
  "decision": "accept | revise | ask",
  "overall": {
    "score": 0.0,
    "confidence": 0.0
  },
  "dimensions": {},
  "issues": [],
  "evidence": [],
  "revision": {
    "strategy": null,
    "instructions": []
  },
  "verification": {
    "required": false,
    "method": null
  }
}
```

## Dimension Result

```json
{
  "score": 0.0,
  "confidence": 0.0,
  "status": "pass | partial | fail | unknown",
  "reason": "string"
}
```

## Issue

```json
{
  "type": "missing_requirement | incorrect_claim | constraint_violation | unsupported_claim | scope_drift | regression | other",
  "severity": "critical | major | moderate | minor | informational",
  "location": null,
  "description": "string",
  "evidence": []
}
```

## Evidence

Evidence should include provenance and verification method as the implementation matures.

```json
{
  "source": "deterministic | external | llm",
  "method": "string",
  "result": "string",
  "confidence": 0.0,
  "provenance": []
}
```

## Decision Semantics

### ACCEPT

Required hard gates pass and the response satisfies the Task Contract sufficiently for the selected mode.

### REVISE

A correctable deficiency exists, required information is available, and another attempt is justified.

### ASK

A material unknown prevents reliable completion, clarification is preferable to guessing, or the contract contains an unresolved contradiction.

## Important

A high aggregate score must not override a failed critical hard gate. A low soft-quality score should not automatically trigger revision when the task is otherwise successfully completed and another iteration has low expected value.
