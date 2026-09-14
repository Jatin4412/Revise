# Revise Foundation Invariants

This document is the protected contract for the engine foundation. It is intentionally smaller than the implementation and should change only when a demonstrated architectural requirement changes the contract.

## Core lifecycle

```text
User intent
  -> Task Contract
  -> Evaluation Profile
  -> Model Router
  -> Primary
  -> Secondary + deterministic/external verification
  -> Evidence Fusion
  -> Revision Assessment
  -> Decision
  -> Best Valid Version
```

## Invariants

1. **Intent is authoritative.** Auto may select effort and verification policy, but it must not rewrite the user's goal or explicit task requirements.
2. **Missing context asks.** When required information is explicitly missing, the engine must return `ASK`; generated content must not turn missing information into an accepted answer.
3. **Unknown never accepts.** Unknown or insufficient-confidence evaluation cannot become `ACCEPT` through score alone.
4. **Deterministic failure wins.** A deterministic verifier failure cannot be overridden by model, external, or aggregate score evidence.
5. **Hard gates win.** Configured hard-gate failures cannot be overridden by quality scores or model acceptance.
6. **Required evidence is real.** Configured evidence requirements must be satisfied by passing evidence; failed evidence does not satisfy a requirement.
7. **Revisions must improve.** A regression or unchanged revision cannot replace a stronger valid version merely because it crosses an absolute quality threshold.
8. **Best valid version is preserved.** Rejected regressions and unchanged revisions cannot displace the strongest eligible prior result.
9. **Budgets are bounded.** Revision and verification budgets are execution constraints, not decorative metadata.
10. **Malformed evaluator/evidence data fails closed.** Invalid scores, confidence, statuses, dimensions, evidence, or equivalent structured results must not cause unsafe acceptance.
11. **Roles are provider-agnostic.** Core engine policy depends on Primary/Secondary/Verifier roles, not provider identities. Provider/model selection remains runtime configuration behind adapters.
12. **ASK is a valid terminal outcome.** It is used when reliable completion is blocked by missing information, ambiguity, failed required verification, unknown evaluation, or exhausted safe revision paths.
13. **Verification claims stay bounded.** Deterministic checks prove only what they can prove; external source verification establishes bounded source properties such as reachability, not factual truth by implication.
14. **The stable API stays small.** `/v1/engine` remains the product execution contract. `/v1/engine/trace` is development infrastructure and must not become a dependency of the core decision path.

## Guardrail tests

`engine/test_foundation_invariants.py` is the dedicated guardrail suite. It is separate from ordinary feature tests and should run as part of every engine release-readiness check.

The suite intentionally includes conflicting signals and full lifecycle scenarios, not only happy-path unit behavior.
