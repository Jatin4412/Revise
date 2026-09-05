# Decision Engine

**Status:** Foundation v0.1

The Decision Engine converts evaluator evidence into the control decision:

```text
ACCEPT
REVISE
ASK
```

## Inputs

- Task Contract
- Evaluation Profile
- Evaluation Results
- Deterministic verification results
- External evidence
- Previous response/version
- Revision budget
- Selected mode

## Priority Order

Conceptual policy ordering:

```text
1. Safety / critical hard gates
2. Missing material information
3. Required task completion
4. Correctness / deterministic verification
5. Instruction and constraint compliance
6. Reliability / evidence
7. Communication quality
8. Cost of another iteration
```

This is intentionally a policy ordering, not yet a finalized mathematical scoring function.

## ACCEPT

Accept when all required hard gates pass and the response meets the contract sufficiently for the selected mode. Do not require perfection.

## REVISE

Revise when a correctable issue is significant, required information is available, revision is likely to improve the response, and revision budget remains. Prefer targeted revision over unnecessary full regeneration.

## ASK

Ask when a material required input is unavailable, user intent is genuinely ambiguous, contradictory constraints cannot be resolved, or proceeding would require an unsafe/unreliable assumption.

## Evidence Precedence

When sources conflict, prefer:

```text
Reliable deterministic verification
        ↓
Direct external evidence
        ↓
Specialized verifier
        ↓
Independent LLM evaluator
        ↓
General LLM judgment
```

This ordering may be specialized by task type.

## Revision Stopping

Stop revising when:

- required gates pass,
- improvement is below expected cost,
- revision budget is exhausted,
- repeated attempts fail for the same reason,
- revisions oscillate,
- or a previous version is clearly better.

## Version Selection

Every response is versioned (`v0`, `v1`, `v2`, ...). Retain the best valid version rather than blindly selecting the newest version.

A new version must not be accepted merely because it fixes the triggering issue; it must also avoid unacceptable regressions.

## Future Formalization

Still intentionally unfrozen:

- numerical score aggregation
- confidence weighting
- evaluator arbitration
- expected-value-of-revision calculation
- exact stopping thresholds
- mode-specific budgets

These should be validated experimentally before becoming permanent policy.
