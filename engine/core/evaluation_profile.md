# Evaluation Profile

**Status:** Foundation v0.1

An Evaluation Profile determines what Revise evaluates for a particular Task Contract.

## Conceptual Schema

```json
{
  "dimensions": [],
  "hard_gates": [],
  "deterministic_checks": [],
  "external_verification": [],
  "llm_evaluators": [],
  "evidence_requirements": [],
  "budget": {
    "evaluation_effort": "low | medium | high",
    "max_revisions": 0,
    "max_verification_steps": 0
  },
  "stopping_conditions": []
}
```

## Construction

The profile should be derived from:

1. Task Contract
2. Explicit user mode
3. Risk/criticality
4. Output type
5. Availability of deterministic verification
6. Need for external evidence

## Base Dimensions

- goal alignment
- task completion
- correctness
- relevance
- completeness
- instruction following

## Optional Communication Dimensions

- coherence
- clarity
- usability
- appropriate depth
- conciseness
- fluency

## Reliability Dimensions

- groundedness
- evidence quality
- uncertainty calibration
- assumption quality
- context utilization

## Specialized Verification

| Task characteristic | Preferred evaluator |
|---|---|
| arithmetic | calculator |
| executable code | compiler/tests |
| structured JSON | schema validator |
| factual claims | retrieval/source verification |
| citations | source/claim verifier |
| safety-critical task | hard-gate safety evaluator |
| open-ended writing | LLM evaluator + instruction checks |

## Selection Principle

Do not use an LLM judge where a sufficiently reliable deterministic verifier can answer the question directly.

Do not activate dimensions merely because they exist. The profile should be the smallest set of checks that can establish whether the response satisfies the Task Contract with sufficient confidence for the selected mode.
