# Revise Engine Agent Context

> Working context for the Revise engine agent. Read this file before making engine decisions or implementation changes. Keep it updated when durable engine work, plans, architecture decisions, or milestones change.

## Ownership and scope

- Repository: `Jatin4412/Revise`
- Agent ownership: engine implementation and engine foundation only.
- Do not modify `web/` or other UI/site layers unless explicitly authorized.
- Preserve established architecture and foundation; prefer additive, modular, backward-compatible changes.
- Provider-specific choices belong to runtime configuration, not core decision policy.
- Primary and Secondary are roles, not fixed model identities. Runtime providers/models may be Gemini, OpenAI, Grok, Ollama, or future providers.

## Core objective

Build Revise as a provider-agnostic, evaluation-driven answer/revision engine that improves task success rather than merely generating text. The engine should be able to generate, independently evaluate, verify where deterministic evidence is available, revise when necessary, and retain the best valid result.

## Established foundation

The intended core flow is:

```text
User
  -> Task Contract / State
  -> Mode / Evaluation Profile
  -> Model Selection / Router
  -> Primary generation
  -> Evaluation + evidence fusion
  -> Decision Engine
       -> ACCEPT
       -> ASK
       -> REVISE -> Primary again
  -> best valid version
```

Role policy:

- Primary: actual task generation; prefer the strongest appropriate configured model.
- Secondary: independent evaluator/critic; often cheaper/faster; explains judgments rather than returning only a scalar.
- Verifier: deterministic/external checks where model judgment should not be trusted as the sole source of truth.

Foundation principles to preserve:

1. User intent is authoritative.
2. Explicit mode is authoritative.
3. Auto chooses effort/verification, not user intent.
4. Scope is locked.
5. Evaluation is multidimensional and task-specific.
6. Deterministic/external evidence beats model opinion when available.
7. Secondary returns reasons, issues, confidence, and revision guidance.
8. Evaluators may be uncertain; unknown is not a passing result.
9. Revisions must demonstrate improvement; failed revisions can revert to the best valid version.
10. Do not ask Secondary to judge things that can be directly verified deterministically.
11. Distinguish detection, localization, diagnosis, correction, and verification.
12. More words do not mean better output.
13. Hard gates apply to safety/security/critical constraints; soft scores apply to clarity/style-type qualities.
14. Missing information should lead to asking the user rather than inventing facts.
15. Explicit mode controls expected effort/depth; it does not waive correctness.
16. Central success metric is final task success versus baseline, not judge score alone.
17. Strongest appropriate configured model belongs in Primary unless the user explicitly chooses otherwise.
18. Provider/model selection is a runtime concern, not core decision policy.

## Evaluation taxonomy

Use task-specific subsets rather than blindly running every dimension.

### Core
- Goal Alignment
- Task Completion
- Correctness
- Relevance
- Completeness
- Instruction Following

### Communication
- Coherence
- Clarity
- Usability
- Appropriate Depth
- Conciseness

### Reliability
- Groundedness
- Evidence Quality
- Uncertainty Calibration
- Assumption Quality
- Context Utilization

### Specialized / deterministic-sensitive
- Mathematical validity
- Code correctness / functional correctness
- Tool correctness
- Retrieval quality
- Citation accuracy
- Logical validity
- Domain-specific constraints

### Hard gates
- Safety
- Security
- Critical constraints / policy

## Current implementation status

### Implemented

- Task contracts and task state foundation exist.
- Evaluation profiles exist and adapt dimensions based on task text.
- Modes exist: Lite, Basic, Pro, Auto.
- Provider-neutral Primary, Secondary, and Verifier protocols exist.
- Runtime model routing separates Primary and Secondary selection.
- Provider adapters exist for Gemini, OpenAI, Grok, and Ollama.
- Structured Secondary evaluation exists. It receives the selected profile and returns dimension scores, confidence, status, reasons, issues, and revision instructions.
- Decision engine handles ACCEPT / ASK / REVISE and treats unknown evaluation as non-passing.
- Bounded revision loop exists. Versions are created as `v0`, `v1`, etc.; revision context includes prior response, issues, and revision instructions.
- Best-version selection exists and prefers accepted versions.
- Evidence fusion exists.
- Local HTTP boundary exists:
  - `GET /health`
  - `POST /v1/engine`
  - stable `{text, decision, version_id}` success response
  - stable `{error:{code,message}}` error response
  - default local CORS for `http://localhost:3000`
- Local `.env` loading exists for engine startup/import.
- End-to-end local runtime has been verified: Primary generation + Secondary evaluation + decision returned `accept` for `what is 2+2`.
- HTTP integration has also been verified after fixing the handler service-factory binding issue.

### Current known limitations / gaps

- The Verifier protocol/evidence path exists, but the default runtime does not yet configure substantive deterministic verifiers.
- Mathematical, code, schema, citation, and similar checks still need stronger deterministic verification where appropriate rather than relying primarily on Secondary.
- Revision quality is not yet enforced with a strong explicit improvement criterion; the loop exists, but improvement-over-baseline should become a first-class decision signal.
- Runtime execution is currently not exposed through a structured trace/logging layer. Terminal traceback exists for unexpected HTTP errors, but this is not the desired engine observability system.
- Evaluation scoring/thresholds can be strengthened so that weak or overly permissive Secondary judgments cannot pass simply because all requested dimensions are nominally marked pass.
- Current profile selection uses lightweight task-text heuristics; this should evolve carefully without weakening explicit user mode semantics.

## Current roadmap / active plan

### Phase A — Execution observability (NEXT)

Build a first-class structured execution trace for every engine run. It should capture, at minimum:

- request / mode
- task contract creation
- evaluation profile and selected dimensions
- Primary invocation: role/provider/model, start/end, version ID, success/failure
- Secondary invocation: role/provider/model, start/end, success/failure
- per-dimension evaluation status/score/confidence/reason
- issues and revision instructions
- verifier invocations and evidence
- decision taken and why
- revision number / parent version
- final selected version

Provide clean developer/runtime logging derived from the trace, e.g.:

```text
[time] PRIMARY -> provider/model
[time] PRIMARY OK -> v0
[time] SECONDARY -> provider/model
[time] SECONDARY OK -> evaluation complete
[time] DECISION -> ACCEPT
```

Do not expose raw secrets or full prompts/responses by default. Keep the existing HTTP success/error contract stable.

### Phase B — Strengthen evaluation

- Make evaluation profiles drive rigorous checks.
- Add explicit quality thresholds/hard gates where justified.
- Weight dimensions by task needs rather than treating every dimension as equally decisive.
- Preserve uncertainty as a real state.
- Ensure a weak/partial evaluator cannot accidentally create a false pass.

### Phase C — Deterministic verification

Implement modular verifiers for appropriate task classes, for example:

- math -> deterministic calculation/checking
- code -> safe tests/compiler/static checks where appropriate
- structured output -> schema validation
- citations/sources -> source verification
- other externally verifiable claims -> evidence/retrieval mechanisms as appropriate

Feed verifier evidence into the existing evidence-fusion path. Secondary should interpret evidence rather than replace it.

### Phase D — Revision quality

Strengthen revision decisions so a revision is accepted only when it materially improves task success or resolves the relevant issue(s). Preserve the best valid prior version when a revision regresses.

Track:

- baseline quality
- revision quality
- resolved issues
- introduced issues
- net improvement

Repeated failure patterns may later become reusable evaluation rules/quality signals.

### Phase E — Development trace exposure

After the engine trace is stable, expose it through an additive development/debug interface that the UI agent can visualize. Do not casually change `/v1/engine`; future trace/streaming/status capabilities should be additive.

## Stable HTTP boundary

Keep this contract stable unless there is an explicit architectural reason to change it:

```text
GET  /health
POST /v1/engine
```

Success:

```json
{"text":"...","decision":"accept|revise|ask","version_id":"v0"}
```

Error:

```json
{"error":{"code":"...","message":"..."}}
```

Engine internals should not leak into this contract. Future streaming/status/trace functionality must be additive.

## Verified runtime state

As of the latest working test:

```text
Local Python engine: working
HTTP /health: working
POST /v1/engine: working
Primary Gemini generation: working
Secondary evaluation: working
Decision: working
UI -> HTTP -> Engine integration: verified
```

The basic `2+2` request correctly returned `2 + 2 = 4`, `accept`, `v0`.

## Working procedure for this agent

Before making a substantive engine decision or implementation change:

1. Read this file first.
2. Inspect the relevant current source/foundation files in `engine/` and `core/`.
3. Check whether the requested change conflicts with an established foundation principle.
4. Prefer the smallest additive change that advances the active roadmap.
5. Test the affected behavior before considering the work complete.
6. Update this context file when durable status, architecture, decisions, limitations, or roadmap state changes.
7. Do not enter repetitive retry loops; if an approach fails repeatedly, stop and reassess.

## Immediate next action

**Do not start another UI redesign or provider migration.** The next engine task is to implement **Phase A: structured execution observability**, then use the resulting trace to verify that Primary -> Secondary -> evaluation -> decision -> revision behavior is actually occurring as designed.
