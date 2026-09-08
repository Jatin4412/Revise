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
- Local end-to-end runtime has been verified for Gemini 3.1 Flash-Lite and OpenRouter Free. Gemini 3.7 Flash returned a provider-side 503 high-demand response during testing. Groq GPT-OSS 120B returned HTTP 403 with Cloudflare error code 1010 during testing.

## Current model/runtime policy
- Default Primary: `gemini / gemini-3.7-flash`.
- Default Secondary: `gemini / gemini-3.1-flash-lite`.
- Current free testing lineup: Gemini 3.7 Flash, Gemini 3.1 Flash-Lite, Groq GPT-OSS 120B, and OpenRouter Free.
- Groq uses the official OpenAI-compatible Chat Completions endpoint with `openai/gpt-oss-120b`.
- OpenRouter uses the OpenAI-compatible Chat Completions endpoint with `openrouter/free`.
- Grok and OpenAI adapters remain supported for users with paid API access but are not presented as free choices.

## Current provider diagnosis
- Groq's official documentation confirms `https://api.groq.com/openai/v1/chat/completions` and `openai/gpt-oss-120b` are valid. The observed 403/1010 is therefore not explained by an invalid endpoint or model ID.
- The Groq adapter now sends an explicit `User-Agent: ReviseEngine/0.1` on OpenAI-compatible requests. This is a small compatibility change aimed at the observed Cloudflare edge rejection; it does not alter core engine behavior.
- A unit test covers the Groq request endpoint, authorization header, client identity, and timeout. The real API key/network path still needs a local runtime retest after updating the repo.

## Current known limitations / next roadmap
### Provider testing (current)
- Retest Groq after pulling the latest engine commit.
- If Groq still returns 403/1010, treat it as an environment/network/edge restriction rather than changing core evaluation behavior; compare with a direct curl request using the same key.
- Run a small consistent prompt matrix across Gemini 3.1 Flash-Lite and OpenRouter Free before Phase B.

### Phase B — Strengthen evaluation (next after provider testing)
- Make profiles drive rigorous task-specific checks.
- Add explicit quality thresholds/hard gates where justified.
- Weight dimensions by task needs.
- Preserve uncertainty and prevent weak evaluator false passes.

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
