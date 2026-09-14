# Revise Foundation Alignment — Research & Change Working Document

> **Purpose:** Living research and decision document for bringing the Revise engine foundation closer to the intended product behavior. This file is deliberately separate from `engine/agent_context.md`: the context file records the established foundation; this file records **proposed changes, evidence, unresolved questions, decisions, and the eventual implementation brief**.
>
> **Status:** Research in progress. No proposed change in this document is considered approved for implementation until the evidence and design discussion are complete.
>
> **Owner/scope:** Engine/foundation only. Do not modify `web/` or unrelated projects from this work.

---

## 1. Current Goal

Align the Revise engine's core behavior more closely with the product goal envisioned for it, without weakening the existing foundation invariants or introducing unnecessary architectural complexity.

The immediate areas under investigation are:

1. **Power / effort semantics** — Lite, Basic, Pro, and Auto should produce meaningfully different levels of effort/depth while preserving user intent and correctness standards. Power must not simply become a crude response-length limiter.
2. **Context sufficiency / clarification** — Revise should recognize when the information supplied by the user is insufficient for a reliable or appropriately specific answer, ask targeted clarification questions, and only then proceed when the necessary context is available.
3. **Response proportionality** — More words must not be treated as better. The engine should favor the shortest response that adequately satisfies the task at the selected effort level and required depth.
4. **Foundation integrity** — Changes must preserve provider/model role independence, bounded execution, evidence precedence, revision quality, best-version preservation, fail-closed behavior, and the stable API boundary.

---

## 2. Established Foundation We Must Preserve

The current engine foundation establishes the following durable principles:

- User intent and explicit mode are authoritative.
- Auto chooses effort/verification, not intent.
- Evaluation is multidimensional and task-specific.
- Deterministic/external evidence beats model opinion when available.
- Secondary returns reasons, issues, confidence, and revision guidance.
- Unknown/low-confidence evaluation is not a pass.
- Revisions must demonstrate improvement; regressions can revert to the best valid version.
- Secondary should not judge things that can be directly verified.
- Hard gates apply to safety/security/critical constraints; soft scores apply to quality/style.
- Missing information should lead to asking rather than inventing.
- Strongest appropriate configured model belongs in Primary unless explicitly overridden.
- More words do not mean better output.

These are protected by `core/foundation_invariants.md` and the existing guardrail suite. The current lifecycle is broadly:

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

A major design question in this research is whether **context sufficiency must become an explicit pre-generation gate** while keeping the existing post-generation evaluation/decision loop intact.

---

## 3. Concrete Evidence From Current Runtime

### 3.1 Basic produced disproportionately long answers

Observed local trace on 2026-09-14:

```text
REQUEST RECEIVED | mode=basic
PROFILE SELECTED | ... effort=medium max_revisions=1 max_verification_steps=2
PRIMARY COMPLETE | provider=openrouter model=openrouter/free ... response_length=2946
...
DECISION ACCEPT | ... score=1.0
```

A second Basic request produced:

```text
PRIMARY COMPLETE | provider=openrouter model=openrouter/free ... response_length=4462
...
DECISION ACCEPT | ... score=1.0
```

The screenshot supplied during this investigation showed the answer occupying five pages for the question:

> "so i got hit by a ball, what should i do?"

The response attempted to cover multiple possible injury scenarios rather than first establishing the missing facts that materially affect appropriate advice.

### 3.2 Why this is a foundation issue, not merely a UI issue

The current profile implementation maps:

```text
Lite  -> low effort, 0 revisions, 1 verification
Basic -> medium effort, 1 revision, 2 verification
Pro   -> high effort, 2 revisions, 4 verification
Auto  -> medium effort, 1 revision, 3 verification
```

However, the current generation prompt does not receive an explicit generation-effort/depth policy. It contains task, requirements, constraints, format, length, style, context, and revision context, but not a meaningful instruction derived from the selected effort level.

Therefore, the current Power distinction primarily affects **evaluation/revision/verification budgets**, not the behavior of the initial generated answer.

This can produce a technically accepted but product-inappropriate result: a Basic answer may be much more verbose or involved than intended.

### 3.3 Current context handling gap

`TaskContract` already has:

- `known_context`
- `missing_context`

and the decision layer already returns `ASK` when `contract.missing_context` is populated.

However, contract creation currently passes supplied context into `known_context` without an independent mechanism that determines whether answer-critical context is absent.

Thus the existing invariant:

```text
missing required context -> ASK
```

is present, but the system does not yet have a sufficiently general mechanism for discovering:

```text
this task requires information X/Y before a reliable answer can be produced
```

This is the central context-sufficiency gap.

---

## 4. Intended Product Behavior Under Investigation

### 4.1 Power

Power should represent **available effort/depth/resources**, not simply maximum output length.

Proposed conceptual behavior:

| Mode | Intended behavior |
|---|---|
| Lite | Fast, concise, minimal necessary reasoning and verification |
| Basic | Balanced effort and depth; enough reasoning for ordinary tasks without unnecessary expansion |
| Pro | Higher effort/deeper analysis when the task benefits from it; more revision/verification budget |
| Auto | Select effort/verification adaptively based on task characteristics while never rewriting user intent |

Important constraints:

- Do not implement Power as a hard character/token cap alone.
- Do not lower correctness requirements merely because the mode is Lite.
- Do not force Pro answers to be long when the task is simple.
- Do not allow Basic to become "verbose by default."
- Do not let Power override explicit user requests for a particular format or length.
- If the user explicitly asks for a short answer, that instruction remains authoritative.
- If the task genuinely requires depth, the selected mode should permit the necessary depth.

### 4.2 Context sufficiency

For an under-specified request such as:

> "I got hit by a ball, what should I do?"

Revise should ideally identify the information whose absence materially changes the answer, then ask a small number of targeted questions rather than generating a large generic answer covering every possibility.

Potentially relevant context might include:

- location of impact
- symptoms/severity
- type of object/ball where it materially changes risk
- approximate force/speed where genuinely useful
- timing
- other critical circumstances

The engine should **not** ask every conceivable question. It should ask only for context whose absence materially affects reliable task completion.

The intended interaction is therefore:

```text
User request
   -> determine whether answer-critical context is sufficient
      -> YES: continue to generation/evaluation
      -> NO: ASK targeted clarification
             -> user supplies context
             -> continue
```

### 4.3 ASK semantics

ASK is already a first-class terminal outcome when reliable completion is blocked. The desired clarification mechanism should reuse that existing concept rather than inventing a separate success/failure state.

However, research must determine whether the best architecture is:

```text
Task Contract
 -> Context Sufficiency Gate
 -> Profile / Primary
```

or whether context sufficiency should be integrated into contract analysis/profile construction while preserving the same observable `ASK` outcome.

---

## 5. Proposed Architectural Direction — Not Yet Approved

A candidate lifecycle is:

```text
User
  -> Task Contract
  -> Context Sufficiency
       |-- insufficient -> ASK + targeted clarification questions
       |
       `-- sufficient
             -> Mode / Profile
             -> Model Router
             -> Primary
             -> Secondary + deterministic/external verification
             -> Evidence Fusion
             -> Revision Assessment
             -> Decision
             -> Best Valid Version
```

This is intentionally a **small additive gate**. It must not duplicate the evaluator or turn the foundation into a large collection of domain-specific heuristics.

Potential implementation principles to investigate:

1. Provider-neutral interface.
2. Explicit distinction between **missing**, **ambiguous**, and **optional** context.
3. Answer-critical context should be identified based on the task, not only keyword matching.
4. Clarification should be minimal and prioritized by expected impact on answer quality/safety.
5. The mechanism should be able to say "enough context" and continue.
6. It should fail safely when confidence is insufficient.
7. Safety/medical/legal/financial tasks may justify a stricter context threshold.
8. Clarification questions themselves should be concise and understandable.
9. The user should not be forced through unnecessary multi-turn questioning.
10. Context sufficiency should not become a substitute for actual verification or evidence.

---

## 6. Research Questions

These questions should be answered before implementation:

### Power / adaptive effort

- How do current production AI systems expose reasoning/effort controls?
- Does effort control change generation, hidden reasoning, token budget, model selection, tool use, verification, or some combination?
- Which parts are model-level versus orchestration-level?
- Does higher reasoning effort reliably improve difficult tasks while harming latency/cost?
- How do production systems avoid overthinking simple tasks?
- Is a response-depth instruction preferable to a hard output cap?
- How should Revise distinguish **reasoning effort** from **answer length**?
- Should Auto select a generation policy, model, verification budget, or all three?
- What should happen when user-requested length conflicts with selected Power?

### Context sufficiency / clarification

- How do production chatbots determine when they need clarification?
- What architectures exist for question understanding and missing-information detection?
- Are there established concepts such as task completeness, ambiguity detection, information gain, or clarification policies that are useful here?
- Should a separate model/LLM perform context sufficiency analysis, or can structured task analysis handle most cases?
- When should clarification happen before generation versus after an initial answer?
- How can the system identify the **minimum sufficient context**?
- How should uncertainty in context sufficiency map to ASK?
- How should context sufficiency behave in safety-critical domains?
- How can the system avoid excessive questioning?
- How should clarification state persist across turns?
- How should user-provided answers update the Task Contract?

### Architecture / foundation integrity

- Can the new mechanisms be added without making the core engine provider-dependent?
- Which current invariants need strengthening?
- Which new invariants are required?
- Which current tests should become regression tests?
- What trace metadata is useful without exposing prompts/responses or sensitive data?

---

## 7. Research Evidence Log

This section will be populated from the separate model/reasoning research report and additional web research where appropriate.

For each important finding, record:

- **Claim / finding**
- **Source**
- **Date**
- **Evidence level:** Confirmed / Strongly supported / Inferred / Speculative
- **Relevance to Revise**
- **Potential architectural implication**
- **Open uncertainty**

### Entry template

```text
### Finding N — <short title>
Claim:
Source:
Date:
Evidence level:
Relevance to Revise:
Implication:
Uncertainty:
```

Do not convert model-generated research claims into project facts without checking the cited evidence when the claim affects architecture or foundation policy.

---

## 8. Scenario Matrix

The final design should be evaluated against at least these categories:

| Scenario | Context sufficient? | Expected action | Power sensitivity | Key concern |
|---|---:|---|---|---|
| Simple factual question | Usually yes | Answer | Low | Avoid unnecessary reasoning/verbosity |
| Simple calculation | Yes | Answer + deterministic verification | Low | Deterministic correctness |
| User explicitly requests short answer | Usually yes | Short answer | Low | User length instruction wins |
| Complex coding/debugging task | Usually depends | Answer / clarify | High | Deeper reasoning + verification |
| Research question with missing source/material | No | ASK | Medium/High | Do not invent unavailable source context |
| "I got hit by a ball, what should I do?" | Potentially no | ASK targeted context | Medium/High | Avoid generic overbroad advice; safety |
| Fully specified medical question | Depends | Answer with appropriate safeguards | Medium/High | Correctness + safety + uncertainty |
| Ambiguous legal/financial question | Often no | ASK | High | Jurisdiction/facts may materially change answer |
| Creative writing prompt | Often yes | Answer | Low/Medium | Don't over-question or over-reason |
| Multi-step planning request | Depends | Answer or ASK | Medium/High | Need constraints/goals before planning |
| Explicitly complete structured-output task | Yes | Generate + schema verification | Depends | Output contract is authoritative |
| Auto-mode difficult task | Depends | Adaptive effort | Adaptive | Difficulty-aware resource allocation |

This matrix should expand as research reveals additional important cases.

---

## 9. Design Principles Under Consideration

These are candidate principles, not yet final foundation invariants:

1. **Power is effort, not verbosity.**
2. **Answer length should be proportional to task requirements.**
3. **Context sufficiency precedes reliable completion.**
4. **Ask only when missing information materially affects the answer.**
5. **Ask the minimum useful clarification questions.**
6. **User-provided constraints remain authoritative over adaptive effort.**
7. **Easy tasks should not pay the cost of difficult-task reasoning.**
8. **Safety-critical ambiguity should bias toward clarification rather than unsupported assumptions.**
9. **Context analysis must remain provider-agnostic.**
10. **Clarification must not become an endless loop.**
11. **The engine should preserve enough state to use answers to clarification questions on the next turn.**
12. **No single model's confidence should be treated as proof that a task is sufficiently specified.**

These must be tested against production research before being promoted into `core/foundation_invariants.md`.

---

## 10. Things We Should Explicitly Avoid

- Hard-coded domain keyword rules as the primary context mechanism.
- Treating every ambiguity as a blocker.
- Asking questions whose answers do not materially change the response.
- Using response length as a proxy for reasoning quality.
- Making Lite intentionally inaccurate or under-verified.
- Making Pro verbose regardless of task requirements.
- Letting Auto rewrite explicit user intent.
- Coupling the engine to one provider's reasoning API.
- Exposing hidden chain-of-thought merely to make Revise appear to reason.
- Adding model calls without a clear reliability/quality benefit.
- Replacing deterministic verification with LLM judgment.
- Expanding the foundation with abstractions before a measured requirement exists.
- Using marketing terminology as proof of technical architecture.

---

## 11. Relationship to Current Foundation Files

| File | Role in this work |
|---|---|
| `engine/agent_context.md` | Established engine continuity, architecture, current status, roadmap |
| `engine/agent_execution_rules.md` | Execution/communication rules for engine work |
| `core/foundation_invariants.md` | Protected durable foundation invariants; update only after decisions are settled |
| `core/engine_release_readiness.md` | Release gates and presentable candidate criteria |
| `engine/revise/models.py` | Task/profile/state contracts; likely context/power data-model implications |
| `engine/contracts.py` | Task contract construction; likely context-sufficiency integration point |
| `engine/revise/profile.py` | Mode/profile selection and effort/verification budgets |
| `engine/llm.py` | Current Primary/Secondary generation/evaluation prompts and provider adapters |
| `engine/engine.py` | Main generation/evaluation/revision/decision lifecycle |
| `engine/revise/decision.py` | Terminal decision policy, including ASK |
| `engine/test_foundation_invariants.py` | Protected invariant regression suite |

No implementation changes should be made from this document until the research and final design are explicitly settled.

---

## 12. Decision Log

### 2026-09-14 — Initial investigation

**Decision:** Treat Power behavior and context sufficiency as two distinct foundation-alignment problems.

**Observation:** Current mode profiles already vary effort/revision/verification budgets, but generation does not receive a corresponding explicit effort/depth policy.

**Observation:** Current `missing_context -> ASK` invariant exists, but the system lacks a general mechanism for discovering answer-critical missing context.

**Decision:** Research both areas before implementation rather than applying crude output-length limits or keyword-based clarification rules.

**Next:** Add the separate reasoning/model research report to this working document's evidence base; analyze it; perform any needed current-source verification; then draft a precise implementation response for the Foundation Agent.

---

## 13. Research Report Integration

### External model/reasoning research file

**Status:** Awaiting user-provided research report.

When added, record its filename/path here and summarize only the findings relevant to Revise foundation decisions. Preserve the research report as a reference artifact rather than rewriting it into this document.

### Integration procedure

1. Read the research report in full.
2. Extract claims relevant to Power/effort, adaptive reasoning, clarification/context sufficiency, verification, agent orchestration, and production architecture.
3. Mark claims by evidence strength.
4. Cross-check important architectural claims against primary/current sources where needed.
5. Compare research findings with Revise's existing invariants and implementation.
6. Identify where Revise currently aligns with industry practice and where it diverges intentionally.
7. Decide which changes are actually justified.
8. Update the decision log and scenario matrix.
9. Draft the final Foundation Agent implementation response only after the above is complete.

---

## 14. Final Implementation Brief — Reserved

This section will eventually contain the researched, implementation-ready response for the Foundation Agent.

It should include:

### Objective

### Confirmed current problems

### Evidence

### Final architectural decision

### Exact files/layers to change

### New/changed contracts

### Runtime behavior

### Power semantics

### Context sufficiency semantics

### ASK/clarification behavior

### Safety and ambiguity handling

### State/continuation behavior

### Tests and invariants

### Regression scenarios

### Acceptance criteria

### Non-goals / protected foundation elements

### Implementation sequence

### Validation plan

**Important:** Do not fill this section with assumptions prematurely. It is the final handoff artifact and should be written only after the research and design discussion are complete.

---

## 15. Working Rule

This document is a **research and decision workspace**, not permission to implement every idea recorded here.

When new evidence contradicts an earlier proposal:

1. Keep the earlier observation for history.
2. Record the contradiction.
3. Reassess the design.
4. Prefer the smallest architecture that satisfies the demonstrated requirement.
5. Update the final recommendation only after the evidence is clear.

The end goal is not to make Revise resemble every modern AI system. The goal is to use current industry knowledge to make the **Revise foundation itself more coherent, reliable, adaptive, and faithful to its intended product behavior**.
