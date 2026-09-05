# Revise Evaluation Specification

**Status:** Foundation v0.1
**Scope:** Evaluator foundation/core

## Purpose

The evaluator determines whether a Primary model response satisfies the user's task and, when it does not, produces actionable evidence for correction.

Decisions:
- `ACCEPT` — sufficiently valid for the requested scope and mode.
- `REVISE` — a correctable deficiency was detected and another Primary attempt is justified.
- `ASK` — required information is missing or ambiguity prevents reliable completion.

## Core Principles

1. User intent is authoritative.
2. Explicit mode is authoritative. Auto may select effort but must not override explicit user intent.
3. Scope is locked; evaluation must not silently expand the task.
4. Correctness is a baseline. Lite reduces effort/depth; it does not authorize avoidable errors.
5. Task complexity does not determine desired answer depth.
6. Evaluation is task-specific; do not run every metric on every task.
7. Deterministic evidence beats model opinion when available.
8. Significant judgments should be explainable and evidence-backed.
9. Evaluator confidence matters.
10. More text is not inherently better.
11. Critical constraints are hard gates; communication qualities are generally soft signals.
12. Revisions must demonstrate improvement.
13. Failed or regressive revisions may be rejected/reverted.
14. Missing material information should lead to `ASK`, not invented assumptions.
15. Revise itself must be evaluated by outcome, not evaluator scores alone.

## Pipeline

```text
User → Task Analyzer → Task Contract → Evaluation Profile → Primary
→ Response → Deterministic/External Checks → Secondary Evaluation
→ Evidence Fusion → Decision Engine → ACCEPT / REVISE / ASK
```

## Base Evaluation Dimensions

- Goal Alignment
- Task Completion
- Correctness
- Relevance
- Completeness
- Instruction Following

Optional communication dimensions: coherence, clarity, usability, appropriate depth, conciseness, fluency.

Optional reliability dimensions: groundedness, evidence quality, uncertainty calibration, assumption quality, context utilization.

Specialized dimensions may include mathematical validity, code/functional correctness, tool correctness, retrieval quality, citation accuracy, logical validity, schema validity, domain constraints, security, and safety.

## Verification Principle

Prefer reliable direct verification over LLM judgment where available:

```text
Math → calculator/symbolic check
Code → compiler/tests/static analysis
JSON → schema validator
Citation → source/claim verification
Tool call → tool-result validation
```

## Task Contract

The contract is the evaluation source of truth and conceptually contains:

```json
{
  "goal": "...",
  "requirements": [],
  "constraints": [],
  "desired_output": {},
  "mode": "lite | basic | pro | auto",
  "known_context": [],
  "missing_context": [],
  "assumptions": [],
  "success_criteria": [],
  "verification_requirements": []
}
```

Important provenance distinctions are required between user-explicit information, conversation context, Secondary inference, assumptions, and external evidence.

## Evaluation Profile

The profile selects the smallest sufficient set of checks for the Task Contract, mode, risk, output type, and available verification methods. It may specify dimensions, hard gates, deterministic checks, external verification, LLM evaluators, evidence requirements, evaluation/revision budgets, and stopping conditions.

## Hard Gates and Soft Scores

Hard-gate failures normally prevent `ACCEPT`, including critical requirement omissions, safety violations, required executable code failing tests, incorrect required mathematical results, invalid required schemas, or fabricated required evidence.

Soft scores help choose between otherwise viable responses, such as clarity, conciseness, organization, and style.

## Claim-Level Verification

Important factual claims may be verified individually. High-impact claims should receive stronger verification than incidental details.

## Evaluation Result

Conceptual v0.1 result:

```json
{
  "decision": "accept | revise | ask",
  "overall": {"score": 0.0, "confidence": 0.0},
  "dimensions": {},
  "issues": [],
  "evidence": [],
  "revision": {"strategy": null, "instructions": []},
  "verification": {"required": false, "method": null}
}
```

## Severity

`critical`, `major`, `moderate`, `minor`, `informational`.

Severity is relative to the Task Contract and Evaluation Profile.

## Revision

Prefer the smallest correction that reliably resolves a detected issue:
- `targeted`
- `partial_regeneration`
- `full_regeneration`
- `clarification`
- `verification_only`

Revision instructions should state what failed, where, why it matters, what must change, and what must be preserved.

Every retry is versioned (`v0`, `v1`, `v2`, ...). The newest version is not automatically the best. Detect regressions and retain/revert to the best valid version.

## Modes

| Mode | Primary effort | Evaluation depth | Revision budget | Verification |
|---|---|---|---|---|
| Lite | Low | Minimal | Low | Targeted |
| Basic | Medium | Standard | Moderate | Task-dependent |
| Pro | High | Deep | Higher | Broad where justified |
| Auto | Dynamic | Dynamic | Dynamic | Risk/need-based |

Effort does not imply answer length. Evaluation follows requested scope and mode.

## Decision Engine

Conceptual priority:

1. Safety / critical hard gates
2. Missing material information
3. Required task completion
4. Correctness / deterministic verification
5. Instruction and constraint compliance
6. Reliability / evidence
7. Communication quality
8. Cost of another iteration

`ACCEPT` when required gates pass and the response is sufficiently successful for the selected mode. `REVISE` when a correctable deficiency remains and another attempt is justified. `ASK` when reliable completion requires clarification or unresolved contradictory constraints prevent progress.

A high aggregate score must not override a failed critical hard gate.

## Reliability Controls

Because LLM evaluators can be wrong:
- prefer deterministic checks
- require evidence for significant judgments
- track confidence
- separate observation, diagnosis, and correction
- use independent evaluators for high-risk tasks when justified
- consider pairwise comparison for candidate selection
- avoid blind trust in scalar judge scores
- record evidence provenance

## Revise-Level Metrics

Measure final task success, improvement over the unverified Primary baseline, error detection, missed errors, false revisions, regressions, revision success, ASK precision/recall where measurable, deterministic verification accuracy, human/evaluator agreement, token overhead, latency, and cost.

The central metric is whether the Revise loop improves the final result enough to justify its cost.

## Open Decisions

Not yet frozen: score normalization/aggregation, confidence calibration, evaluator arbitration, exact revision budgets, task taxonomy, model selection policy, memory schema, persistence, observability, and benchmark suite.

These should be resolved through implementation and evaluation rather than prematurely hard-coded.
