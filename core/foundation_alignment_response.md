# Revise Foundation Alignment — Analysis, Decisions & Foundation-Agent Response

> **Purpose:** Working document for our discussion and final implementation handoff to the Foundation Agent. This is where Revise-specific analysis, observations, decisions, proposed changes, architecture, tests, and implementation instructions belong.
>
> **Research separation rule:** `core/foundation_alignment_research.md` is research-only. Do not place project analysis or implementation decisions there. Add the external reasoning/model research there when supplied; interpret and discuss it in this document.

---

## 1. Current Objective

Bring the Revise engine foundation closer to the intended product behavior while preserving the established foundation invariants and avoiding unnecessary architectural complexity.

Current focus:

1. Make Lite / Basic / Pro / Auto meaningfully control available effort without reducing this to crude response-length limits.
2. Make Revise recognize when answer-critical context is missing and ask targeted clarification questions before producing an unreliable or unnecessarily generic answer.
3. Keep answers proportional to the task: more words are not inherently better.
4. Preserve provider-agnostic Primary / Secondary / Verifier roles, bounded execution, deterministic precedence, revision-quality rules, best-version preservation, fail-closed behavior, and the stable API.

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

---

## 4. Working Hypotheses — To Be Challenged by Research

These are hypotheses, not approved implementation decisions.

### 4.1 Power

Power should mean **available effort / depth / resources**, not "maximum response length."

Potential conceptual model:

| Mode | Intended behavior |
|---|---|
| Lite | fast, concise, minimal necessary effort |
| Basic | balanced effort and depth |
| Pro | deeper effort when task complexity warrants it |
| Auto | dynamically select appropriate effort/resources |

Important distinction:

```text
Reasoning effort != answer length
```

A simple task may need substantial internal verification but a short final answer. A complex task may require a longer final answer. The engine should not force either relationship.

### 4.2 Context sufficiency

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

### 4.3 Minimal clarification

The desired behavior is not "ask lots of questions."

It should identify the smallest set of missing facts whose absence materially affects reliable task completion.

For example, the ball-injury scenario may require location and symptoms, but not irrelevant details such as ball color or brand.

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

**Question for research:** How do production systems separate reasoning effort from answer verbosity, and which mechanisms are practical for Revise's provider-agnostic architecture?

### Finding B — `missing_context -> ASK` already exists

**Status:** Confirmed.

The foundation already treats missing context as an ASK condition. The missing piece is context discovery / sufficiency assessment.

**Question for research:** What is the most reliable and economical way to discover answer-critical missing information without introducing excessive model calls or brittle domain logic?

### Finding C — ASK must remain a first-class product outcome

**Status:** Confirmed foundation principle and recently strengthened at the output boundary.

Rejected candidates must not leak through as user-facing answers when the terminal decision is ASK.

**Question for research:** How should clarification content be represented and carried across turns while retaining this boundary?

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

---

## 11. Final Foundation Agent Response — Reserved

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

## 12. Decision Log

### 2026-09-14 — Research workspace separated

**Decision:** Keep the external reasoning/model research artifact completely clean. Project-specific analysis and implementation decisions belong only in this response document.

**Decision:** Use `core/foundation_alignment_research.md` solely as the research artifact and this file as the Revise-specific interpretation/decision/handoff document.

**Next:** User will provide the external deep-research report. Integrate it here through evidence-based analysis, then produce the final Foundation Agent response.
