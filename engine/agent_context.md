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
- Runtime adapters exist for Gemini, OpenAI, Grok, and Ollama.
- Structured Secondary evaluation exists.
- HTTP boundary is stable: `GET /health`, `POST /v1/engine`, success `{text, decision, version_id}`, generic error `{error:{code,message}}`.
- Phase A execution observability is complete: structured trace records request, contract/profile, Primary, Secondary, per-dimension evaluation, verifier, decision, revisions, and final selection. Trace excludes prompts, responses, and credentials. Console trace is enabled for the local default service.
- Local end-to-end runtime has been verified for the basic `2+2` request.

## Current model/runtime policy
- Default Primary: `gemini / gemini-3.7-flash`.
- Default Secondary: `gemini / gemini-3.1-flash-lite`.
- These are chosen because Google's current Gemini API pricing lists free-tier input/output for both models.
- Previous defaults `gemini-3.8-flash` and `gemini-3.5-flash-lite` are removed from engine defaults because they are not the current documented free-tier model IDs.
- Ollama remains an optional no-API-key local path. `.env.example` documents `gemma4:e4b` as an optional Primary and `qwen3:4b` as an optional Secondary.
- Grok and OpenAI adapters remain supported for users who have paid API access, but they are not presented as free choices.

## Current known limitations / next roadmap
### Phase B — Strengthen evaluation (next)
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
The UI agent owns `web/`. For the model selector, use real runtime selections rather than display-only names:
- Gemini 3.7 Flash: `{provider:"gemini", model:"gemini-3.7-flash"}`
- Gemini 3.1 Flash-Lite: `{provider:"gemini", model:"gemini-3.1-flash-lite"}`
- Optional local Ollama Gemma 4 E4B: `{provider:"ollama", model:"gemma4:e4b"}`
- Optional local Ollama Qwen 3 4B: `{provider:"ollama", model:"qwen3:4b"}`
Do not label Grok/OpenAI as free API options.
