# Revise Engine Agent Context

> Read this file before engine decisions or implementation changes. Update it when durable engine status, architecture, decisions, limitations, or roadmap change.

## Ownership and scope
- Repository: `Jatin4412/Revise`
- Own engine implementation and engine foundation only.
- Do not modify `web/` unless explicitly authorized.
- Preserve the provider-agnostic architecture; provider/model selection is runtime configuration, not core decision policy.
- Primary, Secondary, and Verifier are roles, not fixed model identities.

## Core objective
Build an evaluation-driven answer/revision engine that generates, independently evaluates, verifies where deterministic evidence exists, revises when necessary, and retains the best valid result.

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
- Provider-neutral Primary/Secondary/Verifier protocols exist.
- Runtime adapters currently support Gemini, Groq, OpenRouter, OpenAI, and Grok.
- Ollama is intentionally not part of the current testing/selector setup.
- Structured Secondary evaluation exists.
- HTTP boundary is stable: `GET /health`, `POST /v1/engine`, success `{text, decision, version_id}`, generic error `{error:{code,message}}`.
- Phase A execution observability is complete: structured trace records request, contract/profile, Primary, Secondary, per-dimension evaluation, verifier, decision, revisions, and final selection. Trace excludes prompts, responses, and credentials. Console trace is enabled for the local default service.
- Local end-to-end runtime has been verified for Gemini 3.1 Flash-Lite, OpenRouter Free, Groq GPT-OSS 120B, and Gemini 3.7 Flash after retry.
- Phase C deterministic verification primitives now exist in `engine/revise/verifiers.py`: arithmetic consistency checks, Python AST syntax checks without execution, and JSON syntax checks. Profiles select only relevant deterministic checks, and the engine fuses their evidence with Secondary/custom verifier evidence before decision policy.
- Arithmetic task detection now also recognizes explicit numeric expressions using ASCII or Unicode operators such as `25 × 17`, and the arithmetic verifier can compare a direct numeric answer against a single arithmetic expression in the task.
- Phase C deliberately does not execute arbitrary generated code; safe compiler/test execution remains a future bounded verifier capability.
- Phase D revision quality is implemented in `engine/revise/revision.py`. Each revision is compared with its immediately previous evaluated version; the engine tracks score delta/net improvement, resolved and introduced issues, improved and regressed dimensions, and an overall revision status.
- Revision issue identity is stable across severity changes using issue type, location, and normalized description. Severity changes are tracked separately as downgraded or escalated issues; escalations are regressions and downgrades count as improvement signals.
- Phase D decision policy rejects unchanged or regressed revisions, while allowing revisions with a genuine score/dimension improvement or relevant issue resolution. Material introduced issues and dimension regressions are treated as regressions. The best valid prior version remains selectable when a later revision is rejected.
- Revision assessment is stored in `Version.metadata` and summarized in the development trace; response payloads remain excluded from trace details.
- Deterministic evidence precedence is now enforced in `engine/revise/decision.py`: a deterministic `fail` blocks acceptance regardless of a confident LLM/model `pass`, causing `REVISE` while budget remains and `ASK` when exhausted.

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

## Phase C — Deterministic verification (implemented baseline)
- Added a provider-neutral deterministic verifier registry.
- Math-like tasks can select arithmetic consistency verification.
- Python tasks can select AST syntax verification without executing generated code.
- JSON-formatted tasks can select JSON syntax verification.
- Deterministic evidence is fused with Secondary/custom verifier evidence and participates in the existing evidence-precedence model.
- Decision policy now explicitly enforces deterministic-failure precedence after evidence fusion.
- Trace records deterministic verifier completion without storing candidate response payloads.
- Regression tests cover wrong arithmetic, direct numeric answers for Unicode multiplication expressions, Python syntax checking, JSON syntax checking, profile selection for explicit arithmetic expressions, and deterministic failure overriding a confident model pass.
- Safe runtime code tests, richer schema validation, citation/source verification, and broader external evidence remain follow-up work rather than being faked as complete.

## Phase D — Revision quality (implemented)
- Added `RevisionAssessment` and `assess_revision()` as a provider-neutral comparison layer.
- Tracks baseline/revised score, score delta/net improvement, resolved issues, introduced issues, improved dimensions, regressed dimensions, severity downgrades/escalations, and status (`improved`, `regressed`, `unchanged`).
- A revision with unchanged quality cannot be accepted solely because it crosses an absolute threshold.
- Regressions cannot be accepted; the bounded loop continues if budget remains and otherwise returns `ASK`, with best-version selection preserving the stronger valid candidate.
- A revision with no score increase can still qualify as improved when it resolves a relevant prior issue or improves a dimension.
- Issue identity is preserved across severity changes; severity downgrades and escalations are explicitly assessed rather than being misclassified as issue removal/introduction.
- Adversarial tests cover severity changes, severity escalation despite a higher overall score, dimension tradeoffs where a core dimension regresses, repeated revisions using the immediate previous baseline, and preservation of the stronger prior candidate after a regression.

## Current roadmap
### Phase C follow-up
- Add richer schema validation when the task contract can carry an explicit schema.
- Add safe, sandboxed code tests/compiler checks where infrastructure permits.
- Add citation/source verification and other external evidence adapters.

### Phase D follow-up
- Continue adversarial/corner-case testing around multi-issue interactions, missing dimensions, score ties, and mixed improvements/regressions.

## Phase E — Development trace exposure
Expose trace/status through an additive development interface for the UI agent. Do not casually change `/v1/engine`.

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
