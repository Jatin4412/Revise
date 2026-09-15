# Revise Engine Agent Context

> Read this file before engine decisions or implementation changes. Update it when durable engine status, architecture, decisions, limitations, or roadmap change.

## Ownership and scope
- Repository: `Jatin4412/Revise`.
- This is the engine agent context file; the engine agent owns it and the `engine/` implementation.
- Core/foundation files remain foundation-owned; read/review them when needed, but do not modify them from this agent.
- Do not modify `web/` unless explicitly authorized.
- Preserve provider-agnostic architecture; Primary, Secondary, and Verifier are roles, not fixed model identities.

## Core objective
Build a trustworthy self-correcting answer/revision engine that generates, evaluates, verifies where deterministic/external evidence exists, diagnoses observed failure, selects a bounded correction path, and retains the best valid result.

## Current stable architecture
```text
User -> Task Contract -> Mode/Profile -> Model Router -> Primary
     -> Evaluation + Evidence -> Diagnosis -> Correction Recommendation
     -> existing Decision Authority -> bounded correction
     -> Evaluation + Evidence -> Revision Assessment -> Best Valid Version
```

The foundation contract remains authoritative and must not be weakened by adaptive behavior.

## Authority hierarchy
Authoritative:
1. Task Contract
2. Hard Gates
3. Deterministic Verification
4. Required Evidence
5. Decision Policy
6. Revision Assessment
7. Best-Version Selection

Advisory:
- Model Evaluation
- Diagnosis
- Correction Recommendation
- Approach Classification
- Power/Effort planning

Invariant: advisory diagnosis/recommendation/power planning may redirect execution effort or correction, but can never weaken, bypass, erase, or override an authoritative failure.

## Durable principles
1. User intent and explicit mode are authoritative.
2. Auto chooses effort/verification, not intent.
3. Evaluation is multidimensional and task-specific.
4. Deterministic/external evidence beats model opinion when available.
5. Secondary returns reasons, issues, confidence, and revision guidance.
6. Unknown/low-confidence evaluation is not a pass.
7. Revisions must demonstrate improvement; regressions can revert to the best valid version.
8. Do not ask Secondary to judge things that can be directly verified.
9. Hard gates apply to safety/security/critical constraints; soft scores apply to quality/style dimensions.
10. Missing information leads to asking rather than inventing.
11. Strongest appropriate configured model belongs in Primary unless explicitly overridden.
12. More words do not mean better output.
13. Diagnosis is advisory; it is never a second Decision engine.
14. `ACCEPT_CANDIDATE` is advisory only; only existing Decision can produce terminal `ACCEPT`.
15. An authoritative failure must be independently cleared by the authoritative machinery on any new attempt.
16. Power changes bounded execution effort, not user intent or authority.

## Current implementation baseline
- Task contracts/state, Lite/Basic/Pro/Auto modes, adaptive profiles, evidence fusion, Decision, bounded revision, versioning, best-version selection, provider-neutral Primary/Secondary/Verifier protocols, HTTP service boundary, and safe development trace exist.
- `TaskContract.output_schema` supports deterministic JSON schema verification.
- Deterministic verification includes arithmetic, Python AST syntax, Python compile-only, JSON syntax, and JSON schema validation; generated Python is never executed.
- External verification is bounded HTTP(S) source reachability only, with SSRF/redirect/size/source limits; reachability is not claim-truth verification.
- Evidence requirements, verifier budgets, stopping conditions, hard gates, malformed evaluation handling, malformed evidence handling, revision-quality assessment, issue identity/severity tracking, and best-version regression protection are implemented.
- `ASK` is a first-class terminal outcome when reliable completion is blocked; terminal ASK must never expose a rejected candidate as the final answer.
- Development trace excludes prompts, responses, credentials, and sensitive payloads; non-loopback trace access requires the configured token.
- Current runtime adapters support Gemini, Groq, OpenRouter, OpenAI, and Grok; Ollama remains outside the current selector/testing setup.
- Phase G adds provider-neutral Power planning in `engine/revise/power.py`. Lite resolves to low effort, Basic to medium, Pro to high, and Auto resolves low/medium/high from task complexity signals.
- Power effort now changes the Primary generation prompt and Secondary evaluation prompt, while retaining the same provider/model selection. This is provider-neutral and does not expose chain-of-thought.
- Resolved effort also controls bounded revision/verification budgets: low = 0 revisions/1 verification, medium = 1 revision/3 verification, high = 2 revisions/4 verification, with Basic retaining its existing 2-verification budget for backward compatibility.

## Phase-F implementation contract — LOCKED

### Target lifecycle
```text
Evaluation
    ↓
Evidence
    ↓
Diagnosis
    ↓
Correction Recommendation
    ↓
Existing Decision Authority
    ↓
Existing bounded execution machinery
    ↓
Revision Assessment
    ↓
Best Valid Version
```

### Diagnosis contract
- Minimal provider-neutral `Diagnosis` exists in `engine/revise/diagnosis.py`.
- Advisory recommendations are:
  - `REVISE`
  - `VERIFY`
  - `CHANGE_APPROACH`
  - `ASK`
  - `ACCEPT_CANDIDATE`
- `ACCEPT_CANDIDATE` never authorizes acceptance.
- Diagnosis validation is structural and fail-closed with bounded confidence.
- Invalid/low-confidence diagnosis must not mutate evaluation, evidence, decision, version, or best-candidate state.

### Correction layer
- `engine/revise/correction.py` provides bounded correction primitives.
- Baseline diagnosis is conservative/deterministic from current observations; future diagnostic providers may be layered behind the same advisory contract.
- `REVISE` uses existing revision machinery.
- `VERIFY` uses existing verification machinery and verification budget; the budget is scoped to each evaluation attempt, so a VERIFY recommendation preserves the configured bounded verification capacity for the next attempt rather than being erased by steps already consumed while evaluating the current attempt.
- `CHANGE_APPROACH` creates a lightweight new approach identity and a materially different correction instruction; it does not introduce a Strategy framework.
- `ASK` terminates when existing Decision requires it.
- Existing Decision remains the only acceptance authority.
- Correction context preserves the previous evaluation's issue, dimension, and revision feedback instead of replacing it with generic Phase-F text.

### Approach tracking
- Approach identity is lightweight metadata (`approach-0`, `approach-1`, ...), attached to versions/traces.
- `CHANGE_APPROACH` increments approach identity before the next Primary attempt is generated.
- Approach identity is not claimed to be perfect semantic classification; it records a bounded requested/material change in correction path.
- A changed approach is never treated as automatic improvement.

### Authority preservation
- Hard-gate failures remain authoritative.
- Deterministic/external failures remain authoritative.
- Required evidence remains authoritative.
- A new candidate after `CHANGE_APPROACH` must independently pass authoritative checks.
- A diagnosis recommending `ACCEPT_CANDIDATE` cannot turn a failing hard gate/verifier into `ACCEPT`.
- The evaluator's `EvaluationResult.decision` is provisional; the engine establishes the authoritative Decision before Diagnosis interprets the attempt.

### Bounded execution
- Use existing revision/verification budgets and stopping conditions.
- Do not introduce a unified Power/Effort abstraction in Phase-F; Phase G now provides a separate provider-neutral effort planner without changing the Phase-F authority model.
- Do not introduce generic Agent/Strategy frameworks.
- No unbounded correction loops.

### Revision and best-version invariants
- Every corrected candidate goes through existing Revision Assessment.
- `CHANGE_APPROACH` does not bypass unchanged/regressed rejection.
- A worse approach is rejected and cannot displace a stronger valid version.
- Best-valid-version selection remains authoritative internally.
- Terminal ASK exposes no rejected candidate as `final_version`, even when an internal best historical candidate exists.

### Trace
Phase-F trace may safely expose metadata for:
- attempt
- evaluation
- evidence
- diagnosis
- recommendation
- approach identity/change
- correction
- resource use
- revision assessment
- decision
- final/best selection

Never expose prompts, raw responses, credentials, or sensitive payloads.

## Phase-F test contract
At minimum prove:
1. bad attempt -> `CHANGE_APPROACH` -> different approach -> improved attempt -> `ACCEPT`.
2. bad attempt -> `CHANGE_APPROACH` -> worse attempt -> regression -> previous best retained internally and not exposed on terminal ASK.
3. repeated same-approach failure is bounded by existing budgets/stopping conditions.
4. missing critical context -> `ASK` -> rejected candidate never exposed.
5. model pass + `ACCEPT_CANDIDATE` + deterministic fail -> not accepted.
6. hard-gate fail + `ACCEPT_CANDIDATE` -> not accepted.
7. deterministic fail + `CHANGE_APPROACH` -> new candidate must independently pass deterministic verification.
8. verification-limited attempt -> `VERIFY` -> bounded verification path -> re-evaluation/decision.
9. low-confidence/malformed diagnosis fails closed.
10. invalid diagnosis cannot mutate authoritative evaluation/evidence/decision/version state.
11. changed approach without improvement is not successful.
12. hard gates and deterministic verifiers are rerun/reenforced after approach change where applicable.
13. best-valid-version survives all rejected/regressed corrections.
14. evaluator provisional ACCEPT cannot cause Diagnosis to describe a failed candidate as acceptance-ready.
15. correction context retains actionable evaluator feedback for the next attempt.

## Explicit Phase-F non-goals
Do not add in Phase-F:
- unified Power/Effort abstraction
- generic Agent framework
- generic Strategy framework
- search/tree search/candidate search
- multi-agent orchestration
- autonomous tool loops
- memory
- complex planning graphs
- provider-specific reasoning controls
- raw chain-of-thought storage/exposure
- UI changes

## Current Phase-F status
- PR #4 / branch `phase-f-diagnosis-foundation` contains the minimal Diagnosis contract and authority-boundary tests.
- `engine/revise/correction.py` has bounded diagnosis-to-correction primitives and now preserves evaluation feedback in correction context.
- `engine/engine.py` integrates Diagnosis, correction metadata, lightweight approach tracking, correction context, safe diagnosis/correction/approach trace events, and terminal ASK output protection.
- The engine now establishes the authoritative Decision before running Diagnosis, preventing provisional evaluator ACCEPT values from masking failed dimensions/evidence.
- RevisionAssessment issue collections remain stable string identities; Diagnosis consumes those identities directly rather than treating them as Issue objects.
- VERIFY correction preserves the configured per-attempt verification capacity for the next bounded attempt instead of being downgraded merely because the current attempt already consumed its verification steps.
- `engine/test_phase_f_verify_correction.py` exercises VERIFY through the provider-neutral verifier machinery and confirms verifier evidence is re-evaluated on the next attempt.
- `engine/test_phase_f_deterministic_recheck.py` confirms deterministic verification is independently rerun after an approach change.
- `engine/test_phase_f_best_version.py` covers a multi-attempt regression and confirms the strongest non-regressed candidate remains the best selectable internal version while terminal ASK exposes no candidate.
- CI engine discovery uses package-aware unittest discovery: `python -m unittest discover -s engine -t . -p 'test*.py' -v`.
- Full repository test execution must be verified from a local checkout or successful GitHub Actions run; do not claim green without actually running it.

## Phase-G Power contract
- Power is execution effort, not a second intent system and not a replacement for the authoritative Decision machinery.
- Explicit Lite/Basic/Pro map to low/medium/high execution effort respectively.
- Auto is task-sensitive: simple tasks use low effort, moderate complexity uses medium effort, and complex/high-signal tasks use high effort.
- Power affects provider-neutral Primary generation guidance and Secondary evaluation guidance. It does not select a different provider/model and does not add provider-specific reasoning controls.
- Power preserves bounded execution: low = 0 revisions/1 verification, medium = 1 revision/3 verification, high = 2 revisions/4 verification. Basic retains 2 verification steps to preserve its existing bounded behavior.
- Power guidance must not request, store, expose, or depend on raw chain-of-thought.
- Automated coverage is in `engine/test_power_effort.py` and proves explicit mode effort, Auto task sensitivity, profile budgets, generation prompts, evaluation prompts, and Primary adapter usage.

## Agent execution workflow
- The user maintains a local **agent MD file** used directly to run/coordinate agent work.
- Treat that agent MD file as an execution workflow input when the user provides or references it; do not assume it is foundation-owned.
- The launcher/workflow should provide a direct **test-check option** so engine tests can be run without starting the web UI.
- Preferred engine test command: `python -m unittest discover -s engine -t . -p "test*.py" -v` from the repository root.
- A test-check path should report pass/fail and return to the launcher menu rather than starting or leaving the engine/web services running.
- Do not let the test option silently switch away from the branch the user selected; tests should run against the currently selected/synchronized branch.

## Working procedure
1. Read this file first.
2. Inspect relevant current `engine/` and `core/` files.
3. Check for conflicts with the foundation.
4. Prefer the smallest additive change.
5. Test affected behavior before completion.
6. Update this context file for durable engine status/architecture changes.
7. If an approach cycles or fails repeatedly, stop and reassess instead of retrying blindly.

## UI handoff for current model changes
The UI agent owns `web/`. For the current test selector, use these runtime selections:
- Gemini 3.7 Flash: `{provider:"gemini", model:"gemini-3.7-flash"}`
- Gemini 3.1 Flash-Lite: `{provider:"gemini", model:"gemini-3.1-flash-lite"}`
- GPT-OSS 120B (Groq): `{provider:"groq", model:"openai/gpt-oss-120b"}`
- OpenRouter Free: `{provider:"openrouter", model:"openrouter/free"}`
Do not label Grok/OpenAI as free API options. Do not surface Ollama in the current selector.
