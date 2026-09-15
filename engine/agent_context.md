# Revise Engine Agent Context

> Read this file before engine decisions or implementation changes. Update it when durable engine status, architecture, decisions, limitations, or roadmap change.

## Ownership and scope
- Repository: `Jatin4412/Revise`
- Own engine implementation and engine foundation only.
- Do not modify `web/` unless explicitly authorized.
- Preserve the provider-agnostic architecture; provider/model selection is runtime configuration, not core decision policy.
- Primary, Secondary, Verifier, and future deliberation roles are logical capabilities, not fixed model identities.

## Core objective
Build Reiterate as an evaluation- and deliberation-driven answer/revision engine: generate candidates through bounded reasoning, deliberately challenge the reasoning that produced them, make targeted corrections or change approach when warranted, then independently evaluate and verify the resulting candidate and retain the best valid result.

The central distinction is:
- **Deliberation generates and challenges reasoning.**
- **Evaluation assesses candidate quality.**
- **Verification establishes directly checkable evidence.**
- **Decision authority controls acceptance.**

Reiterate is not defined as simply running more validators or generating more words. Additional inference compute is a resource that may enable deeper deliberation, alternative approaches, correction attempts, and verification, but more compute alone is not proof of correctness.

## Core flow
```text
User -> Task Contract -> Mode / Profile / Model Routing
     -> Bounded Deliberation
        -> Plan -> Reason -> Reflect
        -> Correct / Change Approach when warranted
        -> Re-reason / Re-reflect within bounds
     -> Candidate
     -> Secondary Evaluation + Evidence
     -> Deterministic / External Verification
     -> Evidence Fusion
     -> Diagnosis (post-hoc synthesis)
     -> Revision Quality
     -> Decision Authority
        -> ACCEPT / ASK / REVISE
     -> best valid version
```

Deliberation is upstream and non-authoritative. The existing evaluation, verification, revision-quality, hard-gate, decision, and best-version mechanisms remain the trusted control layer.

## Foundation principles
1. User intent and explicit mode are authoritative.
2. The Task Contract defines the problem boundary; deliberation cannot silently redefine it.
3. Deliberation may challenge assumptions, interpretations, reasoning paths, and conclusions, but cannot authorize acceptance.
4. Reflection is adversarial self-questioning: it asks what could make the current reasoning wrong, incomplete, unsupported, contradictory, or based on a poor approach.
5. Correction is a targeted hypothesis about how to improve reasoning, not proof that the correction is valid.
6. Every materially corrected candidate must independently pass the applicable evaluation and verification path.
7. Evaluation is multidimensional and task-specific.
8. Deterministic/external evidence beats model opinion when the property can be directly verified.
9. Secondary returns reasons, issues, confidence, and revision guidance; it does not become final decision authority.
10. Unknown/low-confidence evaluation is not a pass.
11. Diagnosis is post-hoc synthesis of observed failures/improvements, not the reasoning engine and not acceptance authority.
12. Revisions must demonstrate improvement; regressions can revert to the best valid version.
13. Do not ask a model evaluator to judge things that can be directly verified.
14. Hard gates apply to safety/security/critical constraints; soft scores apply to quality/style dimensions.
15. Missing information or material ambiguity should lead to asking rather than inventing.
16. Strongest appropriate configured model belongs in Primary unless explicitly overridden.
17. More words, more tokens, more verification passes, or more deliberation do not inherently mean better output.
18. Flexible reasoning must have less authority than rigid evidence and decision policy.
19. Provider/model selection remains runtime configuration; roles must not encode provider-specific reasoning assumptions.
20. Prefer bounded, inspectable, additive reasoning mechanisms over generic agent frameworks or uncontrolled autonomous loops.

## Authority model
```text
Highest authority
    ↓
Decision / hard gates / required verification
    ↓
Deterministic and directly verifiable external evidence
    ↓
Evaluation
    ↓
Diagnosis
    ↓
Reflection
    ↓
Correction planning
    ↓
Reasoning / planning
    ↓
Most flexible, least authoritative
```

A lower layer may propose information or changes to a higher layer, but cannot override it. In particular, a reflection saying `ACCEPT_CANDIDATE` or a correction saying that a problem is fixed does not authorize acceptance.

## Current implementation
- Task contracts/state, Lite/Basic/Pro/Auto modes, adaptive evaluation profiles, evidence fusion, decision engine, bounded revision loop, versioning, and best-version selection exist.
- TaskContract carries optional explicit `output_schema` for machine-checkable structured output requirements.
- Provider-neutral Primary/Secondary/Verifier protocols exist.
- Runtime adapters currently support Gemini, Groq, OpenRouter, OpenAI, and Grok; Ollama remains intentionally outside the current selector/testing setup.
- Structured Secondary evaluation exists.
- HTTP boundary remains stable: `GET /health`, `POST /v1/engine`, success `{text, decision, version_id}`, generic error `{error:{code,message}}`.
- Phase A execution observability is complete: structured trace records request, contract/profile, Primary, Secondary, per-dimension evaluation, verifier, decision, revisions, and final selection. Trace excludes prompts, responses, and credentials. Console trace is enabled for the local default service.
- Phase E adds an additive development-only response path at `POST /v1/engine/trace`. It returns the normal `{text, decision, version_id}` plus serialized safe trace events; the existing `/v1/engine` response is unchanged.
- Local end-to-end runtime has been verified for Gemini 3.1 Flash-Lite, OpenRouter Free, Groq GPT-OSS 120B, and Gemini 3.7 Flash after retry.
- Phase C deterministic verification includes arithmetic consistency, Python AST syntax checking, Python compile-only checking, JSON syntax, and explicit JSON schema validation. Generated Python is never executed.
- Richer JSON schema validation supports primitive/object/array types, required properties, nested properties/items, additional-property control, enum/const, string length/pattern constraints, numeric minimum/maximum, array size/uniqueness constraints, and local `#/...` references. Unsupported or malformed schemas fail closed.
- Phase C external source verification exists in `engine/revise/external.py`. Research/source/citation/factual profiles select it separately from `groundedness` and `evidence_quality`. The default verifier checks bounded HTTP(S) source reachability only, rejects private/loopback/link-local/reserved targets, rejects embedded URL credentials, validates redirect targets, limits sources and bytes, and never claims that reachability proves factual support.
- External verification failures participate in evidence precedence and block acceptance when a required cited source is unreachable or required citations are missing.
- Phase D revision quality is implemented in `engine/revise/revision.py`. Each revision is compared with its immediately previous evaluated version; the engine tracks score delta/net improvement, resolved and introduced issues, improved and regressed dimensions, and an overall revision status.
- Revision issue identity is stable across severity changes using issue type, location, and normalized description. Severity changes are tracked separately as downgraded or escalated issues; escalations are regressions and downgrades count as improvement signals.
- Phase D decision policy rejects unchanged or regressed revisions, while allowing revisions with a genuine score/dimension improvement or relevant issue resolution. Material introduced issues and dimension regressions are treated as regressions. The best valid prior version remains selectable when a later revision is rejected.
- Revision assessment is stored in `Version.metadata` and summarized in the development trace; response payloads remain excluded from trace details.
- Phase E service compatibility was hardened so the application boundary does not assume concrete `Engine` internals when used with injected or lightweight engine implementations.
- EvaluationProfile validates its policy structure at construction: non-empty unique dimensions, valid required-dimension references, finite bounded thresholds, supported effort values, non-negative integer budgets, and non-empty policy selectors.
- Profile construction considers the full task-contract text relevant to evaluation selection, including desired format/length/style, assumptions, success criteria, and verification requirements.
- Configured hard-gate issue types are enforced by the decision layer before ordinary severity/score acceptance checks.
- Configured deterministic and external verifiers fail closed when a requested verifier is missing from the registry instead of silently skipping verification.
- `max_verification_steps` is now an actual execution budget: configured deterministic/external verifier steps beyond the budget produce explicit failing evidence rather than silently disappearing. Source-count limits remain separate from verifier-step limits.
- `evidence_requirements` now participate in acceptance: every configured requirement must match a passing evidence item.
- Evaluator results are validated before evidence fusion/decision. Missing dimensions, invalid statuses, non-finite/out-of-range scores or confidence, and unexpected dimensions become a fail-closed unknown/ASK state.
- `stopping_conditions` supports `stop_on_no_improvement`, which terminates further revision when the latest revision does not demonstrate improvement; unsupported stopping conditions are rejected at profile construction.
- Best-version selection excludes revisions marked `regressed` or `unchanged`, preventing a rejected revision from displacing a stronger prior candidate.
- Latest stabilization work fixes required-dimension uniqueness validation and external verifier registry semantics; external source-limit regression coverage explicitly distinguishes deduplication from source-count overflow.
- Phase-F diagnosis work has been designed as a minimal provider-neutral diagnostic contract with explicit authority boundaries; it must remain subordinate to decision authority if/when merged.

## Current model/runtime policy
- Default Primary: `gemini / gemini-3.7-flash`.
- Default Secondary: `gemini / gemini-3.1-flash-lite`.
- Current free testing lineup: Gemini 3.7 Flash, Gemini 3.1 Flash-Lite, Groq GPT-OSS 120B, and OpenRouter Free.
- Groq uses the official OpenAI-compatible Chat Completions endpoint with `openai/gpt-oss-120b`.
- OpenRouter uses the OpenAI-compatible Chat Completions endpoint with `openrouter/free`.
- Groq/OpenRouter compatible requests send `User-Agent: ReviseEngine/0.1`.
- Grok and OpenAI adapters remain supported for users with paid API access but are not presented as free choices.

## Provider testing status
- Primary-only matrix: 4 providers x 3 prompts completed with 2 transient failures on Gemini 3.7 Flash; Gemini 3.1, Groq, and OpenRouter were 3/3.
- Full-pipeline matrix: 4 providers x 3 prompts completed with 0 failures.
- Current provider testing is considered green; transient Gemini capacity errors are treated as provider availability rather than engine defects.

## Phase B — Strengthened evaluation (implemented)
- `EvaluationProfile` supports dimension weights, per-dimension minimum scores, required dimensions, minimum evaluator confidence, and minimum overall score.
- Default adaptive profiles weight task-success and specialized correctness dimensions more heavily than communication polish.
- Default dimension floor is 0.70, required core task dimensions are goal alignment, task completion, correctness, and instruction following, minimum confidence is 0.60, and minimum overall score is 0.75.
- Evaluation computes a weighted overall score instead of an unweighted average.
- Decision policy rejects unknown, partial, failing, low-floor, low-confidence, and below-overall-threshold evaluations; material issues still trigger revision or ask according to revision budget.
- Revision feedback includes dimension status/score/confidence/reason in addition to explicit issues and revision instructions.
- Model router preserves `resolve()` as adapter resolution and exposes `selection()` separately for runtime selection descriptors.
- Tests cover weighted scoring, partial-result rejection, low-confidence rejection, dimension-floor revision, overall-floor revision, revision context propagation, trace revision flow, and role-independent model routing.

## Phase C — Deterministic and external verification (implemented baseline + follow-up)
- Added a provider-neutral deterministic verifier registry.
- Math-like tasks can select arithmetic consistency verification.
- Python tasks select AST syntax and compile-only verification without executing generated code.
- JSON-formatted tasks can select JSON syntax verification.
- Explicit output schemas select deterministic JSON schema verification.
- Deterministic evidence is fused with Secondary/custom verifier evidence and participates in evidence precedence.
- Decision policy explicitly enforces deterministic-failure precedence after evidence fusion.
- Added bounded external source verification for cited HTTP(S) URLs. It is reachability verification, not claim-truth verification, and is isolated behind a provider-neutral fetcher/verifier boundary.
- External source verification is selected for research/source/citation/factual tasks, while semantic groundedness/evidence quality remain separate model dimensions.
- External source failures are handled as non-passing evidence and cannot be overridden by model acceptance.
- Tests cover Python compiler behavior, non-execution, source reachability, unavailable sources, required citations, source bounds/deduplication, fetch errors, registry execution, profile selection, and verifier budgets.
- Safe runtime code tests beyond compile-only verification remain deferred until genuine sandbox infrastructure exists.
- Broader external evidence adapters remain follow-up work; do not fake semantic claim verification.

## Phase D — Revision quality (implemented)
- Added `RevisionAssessment` and `assess_revision()` as a provider-neutral comparison layer.
- Tracks baseline/revised score, score delta/net improvement, resolved issues, introduced issues, improved dimensions, regressed dimensions, severity downgrades/escalations, and status (`improved`, `regressed`, `unchanged`).
- A revision with unchanged quality cannot be accepted solely because it crosses an absolute threshold.
- Regressions cannot be accepted; the bounded loop continues if budget remains and otherwise returns `ASK`, with best-version selection preserving the stronger valid candidate.
- A revision with no score increase can still qualify as improved when it resolves a relevant prior issue or improves a dimension.
- Issue identity is preserved across severity changes; severity downgrades and escalations are explicitly assessed rather than being misclassified as issue removal/introduction.
- Adversarial tests cover severity changes, severity escalation despite a higher overall score, dimension tradeoffs where a core dimension regresses, repeated revisions using the immediate previous baseline, and preservation of the stronger prior candidate after a regression.
- Policy-contract and stabilization tests validate profile structure, evidence requirements, verifier budgets, malformed evaluator outputs, stopping behavior, hard gates, and best-version invariants.

## Phase E — Development trace exposure (implemented baseline)
- Added `POST /v1/engine/trace` as an additive development interface.
- The normal `/v1/engine` contract is unchanged.
- Trace responses serialize only `TraceEvent` timestamp/stage/status/details metadata and preserve the existing payload-safety boundary.
- Service compatibility is covered for concrete and lightweight/injected engine implementations.
- Future work can add authenticated/protected development access or richer status views without coupling the core engine to UI concerns.

## Phase F — Diagnosis boundary (designed / partial)
- Diagnosis is treated as post-hoc synthesis, not the core reasoning mechanism.
- A minimal provider-neutral Diagnosis vocabulary has been explored: `REVISE`, `VERIFY`, `CHANGE_APPROACH`, `ASK`, and `ACCEPT_CANDIDATE`.
- Structural validation must fail closed.
- Diagnosis may recommend an action but cannot override deterministic failures, hard gates, required verification, or final Decision authority.
- Before merging or extending Phase F, preserve these authority boundaries and avoid turning Diagnosis into a generic strategy framework.

## Phase G — Deliberative reasoning foundation (next)

### Objective
Prove that a bounded `Plan -> Reason -> Reflect -> Correct/Change Approach -> Re-reason -> Re-reflect` loop can improve reliability on tasks where deterministic verification cannot fully establish correctness, while preserving the existing authoritative evaluation/verification/decision foundation.

### Foundation model
- **Plan**: form a task-bounded approach or decomposition when useful.
- **Reason**: develop the candidate or intermediate reasoning state.
- **Reflect**: deliberately search for reasons the current reasoning may be wrong, incomplete, unsupported, contradictory, misinterpreted, or based on an unsuitable approach.
- **Correct**: convert a reflection finding into a targeted correction objective; changing approach is allowed when the issue is methodological rather than local.
- **Re-reason / Re-reflect**: independently reconsider the changed candidate before it enters the authoritative evaluation path.

These are logical capabilities, not necessarily separate agents or models. The first implementation should permit the same configured model to perform multiple roles through provider-neutral contracts, while keeping role boundaries explicit.

### New contracts to design
1. `ReasoningState` — minimal state needed to preserve task interpretation, current approach, assumptions, unresolved questions, candidate conclusion, and uncertainty.
2. `Reflection` — structured concerns, challenged assumptions, missing steps, contradictions, alternative interpretations/approaches, confidence, and a non-authoritative recommendation.
3. `CorrectionPlan` — issue, cause hypothesis, correction objective, required change, and selected approach.
4. `Candidate` lifecycle metadata — enough to distinguish original reasoning, corrected reasoning, and independently evaluated versions without exposing raw internal reasoning as a user-facing contract.

### Required authority rules
- Reflection cannot authorize acceptance.
- Correction cannot establish its own correctness.
- A corrected candidate must be re-evaluated and re-verified as applicable.
- Deterministic/external failures and hard gates cannot be overridden by deliberation.
- Missing information remains an `ASK` path rather than an invented assumption.
- Deliberation must be bounded; no autonomous infinite loops.

### Initial reasoning benchmark
Build adversarial tests around:
- hidden assumption;
- wrong reasoning approach;
- missing inference step;
- ambiguity requiring clarification;
- contradiction;
- weak/unsupported evidence;
- self-reinforcing error that reflection misses but verification catches;
- false correction that introduces a regression;
- genuine correction that improves the candidate;
- already-correct/easy task where unnecessary deliberation should not manufacture a problem.

### Explicitly deferred from Phase G
- Power/Effort as a new abstraction.
- Generic `Agent`, `Strategy`, or orchestration frameworks.
- Tree search / MCTS / broad search infrastructure.
- Autonomous tool use or browser loops.
- Persistent memory.
- Multi-agent orchestration.
- Provider-specific reasoning controls in the core.
- UI changes.

Power/Effort may be revisited only after deliberation itself is proven. Its eventual meaning should be an adaptive compute policy spanning reasoning depth, reflection opportunities, alternative approaches, correction attempts, verification, and escalation—not merely a count of verification passes.

## Roadmap after stabilization
### Immediate
- Finalize and review the foundation changes for deliberative reasoning before implementation.
- Inspect current engine contracts and lifecycle to identify the smallest additive insertion point for bounded deliberation.
- Design Phase-G contracts and lifecycle tests before implementing the loop.

### Phase C follow-up
- Add genuine sandboxed code execution/tests only when secure bounded infrastructure is available.
- Add richer external evidence adapters that can verify structured source metadata or task-specific facts without conflating reachability with claim truth.

### Phase D follow-up
- Continue adversarial/corner-case testing around multi-issue interactions, missing dimensions, score ties, and mixed improvements/regressions.

### Phase E follow-up
- Add stronger access control if the development trace endpoint is ever exposed beyond a trusted local/development environment.
- Consider bounded run/status metadata if the UI needs progress/state without exposing model payloads or internal prompts.

## Working procedure
1. Read this file first.
2. Inspect relevant current `engine/` and `core/` files.
3. Check for conflicts with the foundation.
4. Preserve the authority boundary: flexible deliberation cannot override rigid evidence or decision policy.
5. Prefer the smallest additive change.
6. Design contracts and tests before introducing new orchestration.
7. Test affected behavior before completion.
8. Update this file for durable changes.
9. If an approach cycles or fails repeatedly, stop and reassess instead of retrying blindly.

## UI handoff for current model changes
The UI agent owns `web/`. For the current test selector, use these runtime selections:
- Gemini 3.7 Flash: `{provider:"gemini", model:"gemini-3.7-flash"}`
- Gemini 3.1 Flash-Lite: `{provider:"gemini", model:"gemini-3.1-flash-lite"}`
- GPT-OSS 120B (Groq): `{provider:"groq", model:"openai/gpt-oss-120b"}`
- OpenRouter Free: `{provider:"openrouter", model:"openrouter/free"}`
Do not label Grok/OpenAI as free API options. Do not surface Ollama in the current selector.
