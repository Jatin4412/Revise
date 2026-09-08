# Revise Engine Agent Context

> Read this file before engine decisions or implementation changes. Update it when durable engine status, architecture, decisions, limitations, or roadmap change.

## Ownership and scope
- Repository: `Jatin4412/Revise`
- Own engine implementation and engine foundation only.
- Do not modify `web/` unless explicitly authorized.
- Preserve the provider-agnostic architecture; provider/model selection is runtime configuration, not core decision policy.
- Primary, Secondary, and Verifier are roles, not fixed model identities.

## Core objective
Build an evaluation-driven answer/revision engine that generates, independently evaluates, verifies where deterministic/external evidence exists, revises when necessary, and retains the best valid result.

## Core flow
```text
User -> Task Contract -> Mode/Profile -> Model Router -> Primary
     -> Evaluation + Evidence -> Revision Quality -> Decision
        -> ACCEPT / ASK / REVISE -> Primary again
     -> best valid version
```

## Foundation principles
1. User intent and explicit mode are authoritative.
2. Auto chooses effort/verification, not intent.
3. Evaluation is multidimensional and task-specific.
4. Deterministic/external evidence beats model opinion when available.
5. Secondary returns reasons, issues, confidence, and revision guidance.
6. Unknown/low-confidence evaluation is not a pass.
7. Revisions must demonstrate improvement; regressions can revert to the best valid version.
8. Do not ask Secondary to judge things that can be directly verified.
9. Hard gates apply to safety/security/critical constraints; soft scores apply to quality/style dimensions.
10. Missing information should lead to asking rather than inventing.
11. Strongest appropriate configured model belongs in Primary unless explicitly overridden.
12. More words do not mean better output.

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
- Latest stabilization work fixes required-dimension uniqueness validation and external verifier registry semantics; external source-limit regression coverage now explicitly distinguishes deduplication from source-count overflow.
- Evidence fusion now validates every evidence item before sorting or confidence aggregation; malformed types, results, metadata, provenance, and non-finite/out-of-range confidence fail closed instead of influencing acceptance.
- Revision comparison now normalizes case and all whitespace in issue identity and treats a previously evaluated dimension that disappears in a revision as a regression.

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
- Current adversarial audit adds coverage for score ties, mixed resolved/introduced issues, missing dimensions, normalized issue identity, and decision precedence across deterministic/external failures, hard gates, evidence requirements, revision regressions, and low-confidence evaluations.

## Phase E — Development trace exposure (implemented baseline)
- Added `POST /v1/engine/trace` as an additive development interface.
- The normal `/v1/engine` contract is unchanged.
- Trace responses serialize only `TraceEvent` timestamp/stage/status/details metadata and preserve the existing payload-safety boundary.
- Service compatibility is covered for concrete and lightweight/injected engine implementations.
- Stronger trace access control is implemented and merged: loopback remains available for local development when no token is configured; non-loopback trace access is denied without a token; configured `REVISE_TRACE_TOKEN` requires a matching `X-Revise-Trace-Token` header.
- Future work can add richer bounded status views without coupling the core engine to UI concerns.

## Foundation stabilization — current phase
- Policy objects fail closed when structurally invalid.
- Hard-gate policy is enforced by the decision layer rather than being decorative configuration.
- Missing configured deterministic/external verifiers fail closed rather than disappearing from the evaluation path.
- Verification budgets now have runtime semantics.
- Evidence requirements now affect acceptance.
- Evaluator result validation now fails closed.
- `stop_on_no_improvement` and best-version invariants are implemented.
- Stabilization regression fixes are merged to `main` and the current engine work is an additive adversarial audit branch.

## Roadmap after stabilization
### Phase C follow-up
- Add genuine sandboxed code execution/tests only when secure bounded infrastructure is available.
- Add richer external evidence adapters that can verify structured source metadata or task-specific facts without conflating reachability with claim truth.

### Phase D follow-up
- Continue adversarial/corner-case testing around multi-issue interactions, missing dimensions, score ties, mixed improvements/regressions, evidence conflicts, and malformed evidence.

### Phase E follow-up
- Consider bounded run/status metadata if the UI needs progress/state without exposing model payloads or internal prompts.

## Working procedure
1. Read this file first.
2. Inspect relevant current `engine/` and `core/` files.
3. Check for conflicts with the foundation.
4. Prefer the smallest additive change.
5. Test affected behavior before completion.
6. Update this file for durable changes.
7. If an approach cycles or fails repeatedly, stop and reassess instead of retrying blindly.

## UI handoff for current model changes
The UI agent owns `web/`. For the current test selector, use these runtime selections:
- Gemini 3.7 Flash: `{provider:"gemini", model:"gemini-3.7-flash"}`
- Gemini 3.1 Flash-Lite: `{provider:"gemini", model:"gemini-3.1-flash-lite"}`
- GPT-OSS 120B (Groq): `{provider:"groq", model:"openai/gpt-oss-120b"}`
- OpenRouter Free: `{provider:"openrouter", model:"openrouter/free"}`
Do not label Grok/OpenAI as free API options. Do not surface Ollama in the current selector.
