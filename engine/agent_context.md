# Revise Engine Agent Context

> Read this file before engine decisions or implementation changes. Update it when durable engine status, architecture, decisions, limitations, or roadmap change.

## Scope
- Repository: `Jatin4412/Revise`.
- Engine-owned implementation is under `engine/`.
- Do not modify `web/` unless explicitly authorized.
- Core/foundation files are authoritative and must be read-only from this agent.
- Provider/model selection is runtime configuration; roles are logical capabilities, not fixed model identities.

## Authoritative architecture
```text
User
 -> Task Contract
 -> Mode / Evaluation Profile / Model Routing
 -> Bounded Deliberation
      Plan -> Reason -> Reflect
      -> Correct / Change Approach when warranted
      -> Re-reason -> Re-reflect within bounds
 -> Candidate
 -> Secondary Evaluation + Evidence
 -> Deterministic / External Verification
 -> Evidence Fusion
 -> Diagnosis (post-hoc)
 -> Revision Quality
 -> Decision Authority
 -> ACCEPT / ASK / REVISE
 -> best valid version
```

Authority order is:
```text
Decision / hard gates / required verification
> deterministic / directly verifiable external evidence
> evaluation
> diagnosis
> reflection
> correction planning
> reasoning / planning
```

No deliberation role can accept, reject, redefine the Task Contract, bypass verification, or override Decision.

## Current implementation baseline
- `TaskContract` preserves goal, requirements, constraints, output characteristics, context, assumptions, success criteria, verification requirements, and optional output schema.
- `EvaluationProfile` provides evaluation dimensions, hard gates, evidence requirements, deterministic/external checks, thresholds, revision budget, verification budget, and stopping conditions.
- Secondary evaluation is validated fail-closed before evidence fusion and decision.
- Deterministic verification includes arithmetic, Python syntax/compile-only, JSON, and bounded JSON-schema checks.
- External verification is bounded source reachability only and cannot claim semantic factual support.
- Evidence precedence, hard gates, evidence requirements, revision-quality comparison, regression handling, stopping conditions, and best-version selection remain authoritative.
- Stable HTTP boundaries are unchanged.

## Phase-G deliberation implementation
### Objective
Provide a real, bounded `Plan -> Reason -> Reflect -> Correct -> Re-reason -> Re-reflect` capability before authoritative evaluation, without introducing a generic Agent/Strategy framework.

### Contracts
`engine/revise/deliberation.py` defines:
- `Plan`: bounded approach, subproblems, assumptions, open questions.
- `ReasoningState`: plan reference, current candidate, assumptions, open questions, cycle, approach id. It deliberately does not persist unrestricted chain-of-thought.
- `ReflectionConcern`: structured challenge kind, description, severity.
- `Reflection`: concerns, challenged assumptions, missing steps, contradictions, alternative interpretations/approaches, confidence, and advisory `actionable` flag.
- `CorrectionPlan`: problem, correction objective, required change, approach, and `change_approach` flag. It is a hypothesis, not evidence.
- `DeliberationResult`: current candidate plus bounded lifecycle metadata, reflections, corrections, cycle/correction counts, and stop reason.
- `DeliberationLimits`: independent `max_cycles` and `max_correction_attempts`.

### Model usage
- `LLMPrimary.deliberate(contract, prompt)` reuses the same configured Primary model and provider adapter for planning, reasoning, reflection, correction planning, and re-reasoning.
- No provider-specific reasoning API is used.
- Legacy/custom Primary adapters without `deliberate()` remain compatible and fall back to ordinary `generate()`.
- Deliberation prompts explicitly prohibit task-contract mutation, final decision authority, and raw chain-of-thought disclosure.

### Runtime insertion point
`engine/engine.py` now invokes `run_deliberation()` at the start of each candidate-generation/revision attempt. The resulting candidate is then passed unchanged into the existing evaluation -> verification -> evidence fusion -> diagnosis -> revision assessment -> decision path.

The existing revision loop remains intact: if Decision returns `REVISE`, the next attempt receives the existing evaluation-derived revision context and can itself run a fresh bounded deliberation.

### Lifecycle
1. Plan once for the current attempt.
2. Reason to produce a candidate and bounded state.
3. Reflect adversarially; reflection searches for failure modes rather than scoring/defending the candidate.
4. If there is no actionable concern, submit the current candidate to evaluation.
5. If a concern is actionable and correction budget remains, create one targeted `CorrectionPlan`.
6. Re-reason using that correction; a changed approach receives a new approach id.
7. Re-reflect on the corrected candidate.
8. Stop on no actionable concern, correction budget exhaustion, deliberation cycle exhaustion, or safe model-output failure.
9. Submit the current candidate to the authoritative evaluation/verification/decision path regardless of whether correction occurred.

### Budgets
`EvaluationProfile` now has additive bounded deliberation fields:
- `max_deliberation_cycles`
- `max_correction_attempts`

They are intentionally separate from `max_revisions` and `max_verification_steps`.

Current profile defaults:
- Lite: 0 deliberation cycles / 0 correction attempts.
- Basic: 2 cycles / 1 correction attempt.
- Pro: 3 cycles / 2 correction attempts.
- Auto: 2 cycles / 1 correction attempt.

This is a bounded deliberation budget, not a new Power/Effort framework and not a rule that more verification means more effort.

### Failure behavior
- Plan failure: safely fall back to ordinary Primary generation.
- Initial reasoning failure: safely fall back to ordinary Primary generation.
- Reflection failure: submit the current candidate without correction.
- Correction failure: submit the current candidate without applying an invalid correction.
- Re-reason failure: submit the last valid candidate.
- Malformed JSON, invalid fields, unsupported severity, empty required strings, non-finite confidence, and unbounded lists are rejected fail-closed inside the deliberation parser.
- The Task Contract is never mutated by deliberation output.
- A reflection or correction cannot create an engine decision.

### Candidate metadata / trace
Version metadata records only bounded lifecycle information: cycle count, correction count, stop reason, corrected flag, concern count, approach id, and approach summary. It does not persist raw reflection text or chain-of-thought.
Trace records deliberation stage/status/provider/model and bounded counters only; response payloads remain excluded.

## Diagnosis boundary
The current main branch did not yet contain the Phase-F diagnosis runtime despite the foundation documenting the post-hoc diagnosis boundary. To keep the foundation contract internally consistent without importing the larger Phase-F framework, Phase-G adds a minimal `engine/revise/diagnosis.py` implementation.

`Diagnosis` is advisory post-hoc metadata only. It classifies observed verification/evaluation findings and is executed after evidence fusion and revision assessment, immediately before `decide()`. It cannot alter or produce the final decision.

This is intentionally smaller than the previously explored Phase-F recommendation vocabulary; richer correction recommendations remain deferred until they can be introduced without duplicating deliberation policy.

## Test coverage
`engine/test_deliberation.py` covers:
- genuine correction followed by re-reflection and acceptance;
- false correction not being accepted blindly;
- reflection cannot authorize acceptance;
- malformed reflection safe fallback;
- bounded cycle/correction behavior;
- Task Contract immutability;
- hidden assumption, wrong approach, missing inference, ambiguity, and self-reinforcing-error reflection categories;
- no-concern stability without manufactured correction;
- legacy Primary compatibility;
- deliberation budget distinct from verification budget.

Existing engine tests remain the regression suite and are discovered by the existing test runner.

## Explicitly deferred
- Generic `Agent` / `Strategy` abstractions.
- Arbitrary multi-agent orchestration.
- Tree search, MCTS, broad self-consistency search.
- Autonomous browser/tool loops.
- Persistent reasoning memory.
- Provider-specific reasoning controls.
- New Power/Effort abstraction.
- UI changes.
- Raw chain-of-thought as a public or persistent contract.
- Replacing Secondary evaluation, verification, revision quality, best-version selection, or Decision authority.

## Review invariants
Before extending deliberation, verify:
1. User intent and explicit Task Contract remain immutable.
2. Reflection is adversarial and non-authoritative.
3. Correction is a hypothesis, never proof.
4. Corrected candidates reach independent evaluation and applicable verification.
5. Deterministic/external evidence and hard gates retain precedence.
6. Diagnosis remains post-hoc and subordinate to Decision.
7. Deliberation is explicitly bounded.
8. Malformed model output fails safely.
9. Provider/model selection remains generic.
10. Existing behavior remains compatible when deliberation is disabled or unsupported.
