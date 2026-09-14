# Revise Engine — Release Readiness

The engine is moving from architecture expansion to a protected, presentable release candidate.

## Frozen architecture

```text
User Intent
    ↓
Task Contract
    ↓
Evaluation Profile
    ↓
Model Router
    ↓
Primary
    ↓
Secondary + Deterministic/External Verification
    ↓
Evidence Fusion
    ↓
Revision Assessment
    ↓
Decision
    ↓
Best Valid Version
```

No new abstraction should be added unless testing demonstrates a concrete architectural gap.

## Release gates

1. Run the dedicated foundation invariant suite.
2. Run the complete engine unit/integration test suite.
3. Verify full lifecycle scenarios: generation → evaluation → verification → revision → re-evaluation → final selection.
4. Verify conflicting evidence precedence and best-version preservation.
5. Verify provider/model role independence and explicit runtime model selection.
6. Verify revision and verification budgets cannot be bypassed.
7. Verify malformed structured evaluator/evidence output fails closed.
8. Verify `ASK` is returned for blocked or uncertain work rather than unsafe acceptance.
9. Verify the stable `/v1/engine` contract remains unchanged.
10. Keep `/v1/engine/trace` development-only and bounded to safe metadata.

## Presentable engine candidate

The first presentable version should prioritize **trustworthiness and predictable behavior** over feature count. It should demonstrate:

- provider-agnostic Primary/Secondary/Verifier roles
- Lite/Basic/Pro/Auto profiles
- deterministic arithmetic, syntax/compile, JSON, and schema checks
- bounded external source reachability verification
- evidence precedence
- bounded revision with best-version retention
- structured development trace
- stable HTTP execution contract

## Intentionally deferred

- secure runtime code execution until a genuine sandbox exists
- claims of semantic fact verification from URL reachability
- speculative routing abstractions
- UI-specific engine logic
- additional model/provider complexity without a demonstrated need

## Next phase after release candidate

Only expand the engine in response to measured gaps from real scenario testing. Candidate areas are task-specific evaluators, richer evidence adapters, secure sandbox execution, routing improvements, and performance/cost optimization.
