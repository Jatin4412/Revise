# Revise Engine Agent Context

> Read this file before engine decisions or implementation changes. Update it when durable engine status, architecture, decisions, limitations, or roadmap changes.

## Ownership and scope
- Repository: `Jatin4412/Revise`
- Own engine implementation and engine foundation only.
- Do not modify `web/` unless explicitly authorized.
- Preserve the provider-agnostic architecture; provider/model selection is runtime configuration, not core decision policy.
- Primary and Secondary are roles, not fixed model identities.

## Core objective
Build an evaluation-driven answer/revision engine that generates, independently evaluates, verifies where deterministic evidence exists, revises when necessary, and retains the best valid result.

## Core flow
```text
User -> Task Contract -> Mode/Profile -> Model Router -> Primary
     -> Evaluation + Evidence -> Decision
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
- Task contracts/state, modes, adaptive evaluation profiles, evidence fusion, decision engine, bounded revision loop, versioning, and best-version selection exist.
- Provider-neutral Primary/Secondary/Verifier protocols exist.
- Runtime adapters currently support Gemini, Groq, OpenRouter, OpenAI, and Grok.
- Ollama is intentionally not part of the current testing/selector setup.
- Structured Secondary evaluation exists.
- HTTP boundary is stable: `GET /health`, `POST /v1/engine`, success `{text, decision, version_id}`, generic error `{error:{code,message}}`.
- Phase A execution observability is complete: structured trace records request, contract/profile, Primary, Secondary, per-dimension evaluation, verifier, decision, revisions, and final selection. Trace excludes prompts, responses, and credentials. Console trace is enabled for the local default service.
- Local end-to-end runtime has been verified for Gemini 3.1 Flash-Lite, OpenRouter Free, and Groq GPT-OSS 120B. Gemini 3.7 Flash has also completed the full pipeline on retry; earlier 503/high-demand responses were transient provider availability.

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
- Full-pipeline matrix: 4 providers x 3 prompts completed with 0 failures. Each exercised Primary -> Gemini 3.1 Secondary -> evaluation -> decision -> final selection.
- Current provider testing is considered green; transient Gemini capacity errors are treated as provider availability rather than engine defects.

## Phase B — Strengthened evaluation (implemented)
- `EvaluationProfile` now supports dimension weights, per-dimension minimum scores, required dimensions, minimum evaluator confidence, and minimum overall score.
- Default adaptive profiles weight task-success and specialized correctness dimensions more heavily than communication polish.
- Default dimension floor is 0.70, required core task dimensions are goal alignment, task completion, correctness, and instruction following, minimum confidence is 0.60, and minimum overall score is 0.75.
- Evaluation computes a weighted overall score instead of an unweighted average.
- Decision policy now rejects unknown, partial, failing, low-floor, low-confidence, and below-overall-threshold evaluations; material issues still trigger revision or ask according to revision budget.
- Tests cover weighted scoring, partial-result rejection, low-confidence rejection, dimension-floor revision, and overall-floor revision.

## Current roadmap
### Phase B follow-up
- Add deliberate adversarial/incomplete candidate tests against the real LLM Secondary.
- Refine task-specific profile selection beyond keyword detection.
- Add explicit hard-gate dimension semantics for safety/security/critical constraints.

### Phase C — Deterministic verification
- Math -> deterministic checking.
- Code -> safe tests/compiler/static checks where appropriate.
- Structured output -> schema validation.
- Citations/sources -> source verification.
- Other externally verifiable claims -> evidence/retrieval as appropriate.

### Phase D — Revision quality
Require revisions to materially improve task success or resolve relevant issues; track baseline quality, revision quality, resolved/introduced issues, and net improvement.

### Phase E — Development trace exposure
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
