# Revise Foundation Alignment — Analysis, Decisions & Foundation-Agent Response

> **Purpose:** Working document for our discussion and final implementation handoff to the Foundation Agent. This is where Revise-specific analysis, observations, decisions, proposed changes, architecture, tests, and implementation instructions belong.
>
> **Research separation rule:** `core/foundation_alignment_research.md` is research-only. Do not place project analysis or implementation decisions there. Add the external reasoning/model research there when supplied; interpret and discuss it in this document.

---

## 1. Current Objective

Bring the Revise engine foundation closer to the intended product behavior while preserving the established foundation invariants and avoiding unnecessary architectural complexity.

### Product goal clarified during discussion

The original reason for starting Revise remains the primary north star:

> **Build a self-correcting AI agent.**

This does **not** mean the core must become a large general-purpose agent framework immediately. It means the engine must reliably be able to:

```text
Generate -> Evaluate -> Detect problems -> Correct -> Re-evaluate ->
Accept the improved result OR Ask when reliable completion is blocked
```

The architecture should therefore be **flexible without becoming unstable or confusing**. New capabilities such as search, multiple candidates, tools, stronger reasoning models, or richer agent loops should be possible later through well-defined extensions rather than by repeatedly restructuring the foundation.

Current focus:

1. Make Lite / Basic / Pro / Auto meaningfully control available effort without reducing this to crude response-length limits.
2. Make Revise recognize when answer-critical context is missing and ask targeted clarification questions before producing an unreliable or unnecessarily generic answer.
3. Keep answers proportional to the task: more words are not inherently better.
4. Preserve provider-agnostic Primary / Secondary / Verifier roles, bounded execution, deterministic precedence, revision-quality rules, best-version preservation, fail-closed behavior, and the stable API.
5. Preserve a clean path toward future candidate search, tool use, richer orchestration, and agentic execution without making those capabilities mandatory in the first implementation.

---

## 2. Current Runtime Observations

### Basic response depth

Observed 2026-09-14 runtime traces:

```text
mode=basic
profile effort=medium max_revisions=1 max_verification_steps=2
OpenRouter Free response_length=2946
...
DECISION ACCEPT score=1.0
```

Another Basic request:

```text
OpenRouter Free response_length=4462
...
DECISION ACCEPT score=1.0
```

The selected effort currently affects the evaluation/revision/verification profile, but the current Primary generation prompt does not receive a corresponding explicit generation-effort/depth policy.

### Under-specified injury question

Observed product behavior for a question equivalent to:

> "I got hit by a ball, what should I do?"

was a very long generic injury response rather than first determining the few missing facts that materially affect appropriate guidance.

This is not necessarily a model-quality failure. It exposes a foundation gap: the engine has an ASK outcome and a `missing_context` field, but does not yet have a robust general mechanism for deciding that answer-critical context is missing.

---

## 3. Existing Foundation We Must Preserve

The protected foundation already establishes:

- intent is authoritative
- Auto cannot rewrite intent
- multidimensional task-specific evaluation
- deterministic/external evidence precedence
- unknown/low-confidence does not pass
- revisions must improve
- best valid version is preserved
- budgets are bounded
- malformed structured evaluation/evidence fails closed
- roles are provider-agnostic
- ASK is a valid terminal outcome
- verification claims remain bounded
- stable `/v1/engine` API remains small

No proposed change should weaken these invariants.

The new architectural direction adds one more protection:

> **Self-correction is the core behavior; general agent orchestration is an extensible capability around that core, not a reason to destabilize the core.**

---

## 4. Working Hypotheses — To Be Challenged by Research

These are hypotheses and discussion decisions, not yet an implementation specification.

### 4.1 Revise identity / scope

**Discussion conclusion:** Revise should optimize first for the self-correcting-agent goal, while keeping the underlying engine modular enough to grow.

We should distinguish two meanings of "agent":

1. **Self-correcting agent behavior — core Revise responsibility.**
   - generate a candidate
   - evaluate it
   - verify where possible
   - identify deficiencies
   - revise
   - stop when good enough or ask when reliable completion is blocked

2. **Broad autonomous agent orchestration — future extension.**
   - tool selection
   - web/browser interaction
   - long-horizon action loops
   - external environments
   - multi-agent delegation
   - persistent memory

The second category should not be forced into the foundation merely because modern AI products use it. The architecture should leave clean extension points for it.

### 4.2 Power

Power should mean **available effort / depth / resources**, not "maximum response length."

**Current decision:** The exact mechanism remains intentionally undecided until the discussion is complete. We should not prematurely equate Power with a single provider parameter or a token cap.

Potential conceptual model:

| Mode | Intended behavior |
|---|---|
| Lite | fast, concise, minimal necessary effort |
| Basic | balanced effort and depth |
| Pro | deeper effort when task complexity warrants it |
| Auto | dynamically select appropriate effort/resources |

Potential resources Power may eventually govern:

- model capability/tier selection where policy allows
- hidden/provider-native reasoning effort where supported
- number of candidate attempts
- verification budget
- revision budget
- tool/search budget when those capabilities exist
- stopping/early-completion policy

The important architectural rule is:

```text
Power = bounded computation/resource policy
Power != answer verbosity
Power != user intent
```

Provider-specific controls should be adapters underneath this policy, never the foundation definition of Power.

### 4.3 Context sufficiency

The likely desired lifecycle is:

```text
User
  -> Task Contract
  -> Context Sufficiency
       |-- insufficient -> ASK targeted clarification
       |
       `-- sufficient
             -> Profile / Power
             -> Primary
             -> Evaluation + Verification
             -> Revision / Decision
```

The key question is whether context sufficiency should be an explicit pre-generation gate, part of contract construction, or another carefully bounded foundation component.

The mechanism must not become a brittle set of keyword rules.

### 4.4 Minimal clarification

The desired behavior is not "ask lots of questions."

It should identify the smallest set of missing facts whose absence materially affects reliable task completion.

For example, the ball-injury scenario may require location and symptoms, but not irrelevant details such as ball color or brand.

### 4.5 Candidate search / multiple solutions

**Discussion direction:** Keep the architecture open to candidate generation and reranking/verification, but do not make best-of-N a mandatory first implementation.

The likely future evolution is:

```text
Primary -> candidate(s) -> evaluation/verification -> select/revise
```

rather than assuming every request must generate many candidates.

This should be treated as an additional bounded computation strategy that Power may eventually allocate when justified by task difficulty or reliability requirements.

### 4.6 Agentic orchestration

**Discussion conclusion:** Do **not** turn the current foundation into a general agent framework yet.

Instead, preserve a layered direction:

```text
                    Future extensions
       tools / search / memory / multi-agent / actions
                              |
                              v
                    orchestration layer
                              |
                              v
        -----------------------------------------------
        Revise self-correction engine (protected core)
        -----------------------------------------------
        Contract -> Profile -> Primary -> Evaluate/Verify
                   -> Revise -> Decide -> Best/ASK
```

This gives Revise a strong identity now while avoiding a future dead end. If agentic capabilities are added, they should consume the core's contracts, budgets, evidence, decisions, and safety boundaries rather than bypassing them.

---

## 5. Research Integration Plan

When the external reasoning/model research report is added to `core/foundation_alignment_research.md`:

1. Read it as the research source, preserving its claims and terminology.
2. Extract findings relevant to Revise's Power/effort model, adaptive compute, orchestration, verification, clarification, ambiguity handling, and agentic behavior.
3. Separate documented facts from inference and speculation.
4. Verify important current-production claims against primary/current sources when needed.
5. Compare the research findings against the current Revise implementation.
6. Record conclusions here, not in the research file.
7. Challenge our initial hypotheses where the evidence disagrees.
8. Decide the smallest foundation changes justified by the evidence.
9. Draft the final Foundation Agent implementation response only after the design is settled.

---

## 6. Discussion / Evidence Notes

### Finding A — Power currently under-specifies generation behavior

**Status:** Confirmed from current Revise implementation/runtime.

The profile selects an effort value, but generation currently does not receive a generation policy derived from that effort. The existing distinction is therefore weighted toward evaluation/revision/verification rather than initial generation behavior.

**Research relevance:** The supplied research describes production systems increasingly treating inference compute as a controllable resource, including explicit effort/depth controls and adaptive allocation. This supports the direction of a provider-neutral effort policy, but does **not** by itself determine Revise's exact implementation.

### Finding B — `missing_context -> ASK` already exists

**Status:** Confirmed.

The foundation already treats missing context as an ASK condition. The missing piece is context discovery / sufficiency assessment.

**Research relevance:** The supplied research emphasizes adaptive orchestration and choosing the simplest sufficient path, but it does not provide a sufficiently specific general algorithm for Revise's context-sufficiency problem. This remains an architectural design problem we need to solve deliberately rather than copy a vendor pattern.

### Finding C — ASK must remain a first-class product outcome

**Status:** Confirmed foundation principle and recently strengthened at the output boundary.

Rejected candidates must not leak through as user-facing answers when the terminal decision is ASK.

**Research relevance:** The research's broader reliability discussion supports bounded verification and escalation, but the exact ASK semantics remain a Revise foundation decision.

### Finding D — Self-correction should remain the core before broad agentification

**Status:** Discussion conclusion.

The research shows that production systems increasingly combine reasoning models with tools, search, routing, and agent loops. However, that does not mean Revise should absorb all of those concerns into its core immediately.

The stronger foundation is to make self-correction a stable primitive that future orchestration can call. This keeps the core comprehensible and makes later tools/agents additive instead of foundational rewrites.

### Finding E — Power should likely govern a resource envelope, not one mechanism

**Status:** Working architectural direction; exact policy not finalized.

The research identifies several forms of inference-time compute: longer reasoning, multiple candidates, reranking/verification, tool calls, and agent loops. This suggests that defining Power as merely "reasoning tokens" would be too narrow for Revise's long-term direction.

The current working abstraction is therefore:

```text
Power -> allowed effort/resource envelope
       -> provider/model-specific mechanisms
```

The envelope must remain bounded, observable, and policy-driven.

---

## 7. Scenario Matrix

| Scenario | Desired behavior | Main foundation question |
|---|---|---|
| Simple factual question | Answer directly | Avoid unnecessary reasoning/verbosity |
| Simple arithmetic | Answer + deterministic verification | Keep deterministic precedence |
| Explicit short-answer request | Respect requested brevity | User instruction outranks adaptive depth |
| Complex coding/debugging | Deep enough effort + verification | Power should enable more work, not force verbosity |
| Missing source/document | ASK | Do not invent unavailable context |
| "I got hit by a ball" | ASK for critical context if needed | Context sufficiency + safety |
| Fully specified medical question | Answer with safeguards | Do not over-ask |
| Ambiguous legal/financial question | ASK if material facts/jurisdiction missing | Domain-sensitive sufficiency |
| Creative writing | Usually answer directly | Avoid needless clarification |
| Complex planning | Answer or ASK depending on missing constraints | Determine what is actually necessary |
| Structured JSON task | Generate + schema verification | Preserve deterministic verification |
| Auto difficult task | Increase effort/resources adaptively | Difficulty-aware allocation |
| Hard reliability-critical task | Potentially multiple candidates + stronger verification | Future candidate-search policy |
| Tool-dependent task | Future bounded tool/orchestration path | Keep tools outside protected core initially |
| Long-horizon autonomous task | Future agent layer over core | Do not destabilize self-correction foundation |

---

## 8. Candidate Foundation Changes — NOT APPROVED YET

These remain candidates until research and discussion settle them.

### Candidate 1 — Generation effort policy

Introduce a provider-neutral generation policy associated with the selected profile/mode, capable of influencing the Primary without changing user intent.

Potential dimensions:

- desired reasoning effort
- response-depth guidance
- generation budget where provider supports it
- tool/search budget where applicable in future
- stopping/early-completion behavior

Do not assume all providers expose the same controls.

### Candidate 2 — Context Sufficiency Gate

Introduce a provider-neutral context-sufficiency assessment before normal generation when the task may require information not supplied by the user.

Possible output:

```text
SUFFICIENT
or
INSUFFICIENT + prioritized clarification questions
```

It must be bounded and avoid endless clarification loops.

### Candidate 3 — Clarification state

Determine whether the Task Contract or adjacent state needs a durable representation of:

- known context
- missing context
- clarification questions already asked
- user answers to those questions
- remaining unresolved context

This must integrate with the existing engine contract rather than create an unrelated conversation-state system.

### Candidate 4 — Stronger proportionality evaluation

Investigate whether the evaluator needs a more explicit notion of task-appropriate depth/conciseness so a very long answer cannot receive perfect quality merely because it contains correct information.

This must not turn into a simplistic word-count rule.

### Candidate 5 — Future candidate/search abstraction

Consider a provider-neutral bounded candidate-generation abstraction that can later support best-of-N, sampling, reranking, or alternative solution paths.

This should remain optional and should not force multiple generation passes for ordinary tasks.

### Candidate 6 — Future orchestration boundary

Define an extension boundary for future tools, search, memory, and agentic action loops without implementing those capabilities in the current stabilization/rebuild unless a concrete requirement justifies them.

The extension boundary should consume the existing engine contracts and decision/evidence rules rather than create a parallel control architecture.

---

## 9. Risks to Investigate

- Extra context-analysis calls could increase latency/cost more than they improve reliability.
- A context gate could over-question users.
- A weak context assessor could incorrectly block straightforward tasks.
- Provider-specific reasoning controls could leak into core policy.
- Generation-length limits could conflict with legitimate user requirements.
- Stronger brevity scoring could penalize necessary detailed answers.
- Adaptive reasoning could become unpredictable if not bounded.
- Clarification could become an infinite multi-turn loop.
- Context handling could duplicate evaluation responsibilities.
- Safety-sensitive clarification must not imply that asking questions guarantees safety.
- Candidate search can multiply cost quickly and can amplify correlated model errors.
- Multi-agent orchestration can make failures harder to attribute and can weaken a clean decision boundary if agents bypass core evaluation/verification.
- Tool use introduces external failure and security surfaces that must remain bounded and observable.

---

## 10. Non-Goals

Do not use this work to:

- redesign the UI
- change the stable API unnecessarily
- expose hidden chain-of-thought
- lock the engine to a particular reasoning provider/model
- replace deterministic verification with LLM judgment
- make Lite intentionally lower-quality
- force Pro responses to be long
- add multi-agent orchestration without evidence that it belongs in the core foundation
- introduce a large agent framework merely because modern systems use agents
- rewrite working foundation components without a demonstrated requirement
- treat vendor-specific reasoning controls as Revise's permanent Power definition

---

## 11. Current Discussion Conclusion — Not Yet Final Implementation Specification

At this point we have a clearer architectural direction, but **we are not ready to draft the Foundation Agent implementation response yet**.

What is now reasonably settled:

1. **North star:** self-correcting AI agent behavior is the primary product goal.
2. **Foundation strategy:** flexible, modular, bounded, and difficult to destabilize.
3. **Core vs future:** self-correction belongs in the protected core; broad agentic orchestration should be an extension layer.
4. **Power direction:** Power represents a bounded effort/resource envelope, not response length or intent. Exact mechanics remain open.
5. **Candidate search:** desirable future capability, but not mandatory for the first rebuild.
6. **Research role:** use the research to challenge and refine these decisions, not to blindly copy production architectures.
7. **Research artifact separation:** the research file remains strictly research-only; all interpretation and decisions stay here.

### What we still need to settle before implementation

- What exactly is the **minimum viable self-correction loop** we want to call the Revise core?
- What should **Power actually control in version 1**, and what should merely be reserved in the abstraction?
- Where should **context sufficiency** live and how should it avoid over-questioning?
- Should clarification happen **before generation, after an initial attempt, or adaptively** depending on task type?
- How should the engine distinguish **missing context** from **uncertainty that can be resolved through reasoning/verification**?
- What should trigger **more effort vs revision vs verification vs ASK**?
- What should the engine consider a **successful self-correction** beyond a higher aggregate score?
- What contracts must be protected so future tools/search/agents cannot bypass the foundation?
- Which research claims require external verification before they influence an implementation decision?

We should continue discussing these questions before modifying/rebuilding the foundation.

---

## 12. Final Foundation Agent Response — Reserved

This section will be completed only after the research has been integrated and the design has been discussed and settled.

The final response should give the Foundation Agent:

1. **Clear objective**
2. **Confirmed current problems**
3. **Evidence and research basis**
4. **Final architectural decision**
5. **Exact files/layers to modify**
6. **Required contract/model changes**
7. **Power semantics**
8. **Context sufficiency semantics**
9. **ASK/clarification behavior**
10. **State/continuation behavior**
11. **Safety/ambiguity rules**
12. **Tests and invariant updates**
13. **Acceptance criteria**
14. **Non-goals / protected elements**
15. **Implementation sequence**
16. **Validation plan**

The Foundation Agent should implement from this final section only after the recommendation is settled.

---

## 13. Decision Log

### 2026-09-14 — Research workspace separated

**Decision:** Keep the external reasoning/model research artifact completely clean. Project-specific analysis and implementation decisions belong only in this response document.

**Decision:** Use `core/foundation_alignment_research.md` solely as the research artifact and this file as the Revise-specific interpretation/decision/handoff document.

### 2026-09-14 — Discussion Round 1: product identity and extensibility

**Decision:** Revise's primary goal is a self-correcting AI agent. The foundation should optimize for reliable generation → evaluation/verification → correction → decision rather than becoming a general-purpose agent framework immediately.

**Decision:** Broad agentic capabilities such as tools, search, memory, long-horizon actions, and multi-agent delegation should have future extension points but must not destabilize or bypass the protected self-correction core.

**Decision:** Power is conceptually a bounded effort/resource envelope, not response verbosity or user intent. Exact Power mechanics remain intentionally open pending further discussion.

**Decision:** Candidate generation/search should remain architecturally possible but optional; do not add best-of-N simply because it appears in modern systems.

**Next:** Continue discussion around the minimum self-correction loop, Power semantics, context sufficiency, clarification timing, escalation rules, and protected extension boundaries before drafting the implementation response.
