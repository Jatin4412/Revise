# Revise Foundation Alignment — Analysis, Decisions & Foundation-Agent Response

> **Purpose:** Working document for our discussion and final implementation handoff to the Foundation Agent. This is where Revise-specific analysis, observations, decisions, proposed changes, architecture, tests, and implementation instructions belong.
>
> **Research separation rule:** `core/foundation_alignment_research.md` is research-only. Do not place project analysis or implementation decisions there. The external research artifact remains untouched as research; interpret and discuss it here.

---

## 1. Current Objective

Bring the Revise engine foundation closer to the intended product behavior while preserving the established foundation invariants and avoiding unnecessary architectural complexity.

### Product goal — primary north star

> **Build a self-correcting AI agent.**

Revise should reliably be able to:

```text
Generate -> Evaluate -> Diagnose -> Correct -> Re-evaluate
         -> Accept improved result
         OR continue bounded correction
         OR ASK when reliable completion is blocked
```

The architecture should be **flexible without becoming unstable or confusing**. New reasoning mechanisms should be additive capabilities around a protected self-correction core, not repeated rewrites of the foundation.

Current focus:

1. Make Lite / Basic / Pro / Auto meaningfully control available effort without reducing Power to crude response-length limits.
2. Make Revise recognize when answer-critical context is missing and ask targeted clarification questions rather than produce unreliable generic answers.
3. Keep answers proportional to the task: more words or more thinking are not inherently better.
4. Preserve provider-agnostic Primary / Secondary / Verifier roles, bounded execution, deterministic precedence, revision-quality rules, best-version preservation, fail-closed behavior, and the stable API.
5. Preserve clean extension paths toward candidate search, tools, retrieval, richer orchestration, memory, and agentic execution.
6. Build the self-correction capability first; add broader reasoning capabilities only when they solve a measured limitation.

---

## 2. Current Runtime / Foundation State

### Existing foundation

The engine already has:

- task contracts and execution state
- Lite / Basic / Pro / Auto modes
- adaptive evaluation profiles
- provider-neutral Primary / Secondary / Verifier roles
- weighted multidimensional evaluation
- deterministic arithmetic, Python syntax/compile-only, JSON, and JSON-schema verification
- bounded external source reachability verification
- evidence fusion and deterministic/external precedence
- hard gates and fail-closed behavior
- bounded revision budgets and verification budgets
- revision-quality comparison against the immediately previous evaluated version
- stable issue identity and severity-change tracking
- best-valid-version preservation
- `ASK` as a first-class terminal decision
- safe development trace exposure
- stable `/v1/engine` response contract

### Important recent boundary fix

A rejected candidate must never become the user-facing answer merely because it is the only version in state. Terminal `ASK` now has an explicit output boundary: no rejected candidate is exposed as the final response/version.

### Runtime observations

Recent Basic/OpenRouter runtime traces showed very long answers while the profile was only medium effort. This indicates that the current mode/profile affects evaluation/revision/verification policy more strongly than initial generation policy.

An under-specified question equivalent to `I got hit by a ball, what should I do?` also produced a long generic answer rather than first identifying the small set of missing facts that materially affect the response. This exposes a context-sufficiency gap rather than simply a model-quality problem.

---

## 3. Protected Foundation Principles

These remain stable:

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
11. The strongest appropriate configured model belongs in Primary unless explicitly overridden.
12. More words do not mean better output.
13. Budgets must be bounded and observable.
14. Structured evaluation/evidence failures fail closed.
15. Provider/model identities are configuration; Primary/Secondary/Verifier are roles.
16. `ASK` is a valid successful terminal outcome when reliable completion is blocked.
17. Stable API boundaries must not be expanded merely to expose internal reasoning.
18. Future extensions must consume core contracts, evidence, budgets, and decisions rather than bypass them.

Additional architectural protection:

> **Self-correction is the protected core behavior. General agent orchestration is an extension layer, not a reason to destabilize the core.**

---

## 4. Research Integration — What the External Research Establishes

The supplied `Executive Summary.pdf` surveys reasoning mechanisms from direct generation through hidden reasoning, extended/test-time compute, deliberation, search, tools, agents, multi-agent systems, verifiers, planning/tree search, and RL-trained reasoning. It describes a broad industry shift from one-pass generation toward **systems that deliberately spend additional computation and structured interaction when the task warrants it**. fileciteturn841file0L12-L34

The report's taxonomy distinguishes model-internal mechanisms, search/ensemble mechanisms, tool-assisted reasoning, agentic loops, and planning/search integration. It explicitly notes that these categories overlap in real systems. fileciteturn841file0L53-L90 fileciteturn841file0L103-L124

### 4.1 Direct generation is still a legitimate baseline

The research does **not** imply that every request should be treated as a reasoning problem. Direct generation remains appropriate for simple questions, casual interaction, creative tasks, and throughput-sensitive workloads. Extra reasoning can be wasteful and can sometimes hurt easy/out-of-distribution tasks through overthinking. fileciteturn841file0L55-L62 fileciteturn841file0L488-L502

**Revise implication:** The self-correction engine must be selective. A strong engine does not maximize computation; it spends enough effort to meet the task's requirements.

### 4.2 Test-time compute is a real architectural resource

The research describes longer reasoning, multiple trials, reranking/verification, and adaptive allocation as forms of inference-time computation. More compute can improve hard-task performance, but gains are generally diminishing and task-dependent. fileciteturn841file0L451-L502

**Revise implication:** Power should be an abstract resource envelope rather than a synonym for response length or a single vendor reasoning parameter.

### 4.3 Search and multiple candidates are valid future mechanisms

Self-consistency, best-of-N, sampling, reranking, and tree-search approaches all treat alternative solution paths as a way to increase the probability of finding a good result. The research also notes that explicit tree search remains much less common in production than simpler sampling/reranking patterns. fileciteturn841file0L216-L235

**Revise implication:** Candidate search should remain an optional future computation strategy. It should not be mandatory for ordinary requests.

### 4.4 Verification is a separate and important capability

The research repeatedly separates generation from verification/reranking and describes generator + verifier architectures as a production pattern. It also warns that correlated errors can occur when generator and verifier are the same model. fileciteturn841file0L109-L120 fileciteturn841file0L230-L235 fileciteturn841file0L836-L846

**Revise implication:** The current independent Secondary and deterministic verification architecture is directionally correct. Future verification should become stronger where independent evidence is available rather than simply asking the same model to be more confident.

### 4.5 Tool-assisted reasoning extends capability outside the model

Retrieval, code execution, calculators, APIs, and other tools can externalize computation or knowledge. The research describes model → tool → model and model → planner → tools → verifier → final model patterns. fileciteturn841file0L86-L90 fileciteturn841file0L647-L656

**Revise implication:** Tools are a future extension surface. The engine should be able to allocate bounded tool effort later without making tools part of today's protected core.

### 4.6 Agentic loops add planning, action, observation, and replanning

The research defines agentic reasoning as a repeated Reason → Act → Observe → Reason loop and describes planner/executor/critic and multi-agent architectures. Agents add capabilities such as planning, tool selection, error recovery, and goal management, but they also introduce loops, latency, security, attribution, and orchestration complexity. fileciteturn841file0L91-L116 fileciteturn841file0L608-L636

**Revise implication:** Revise can be agentic in behavior without becoming a general agent framework. Its first agentic capability is self-correction; autonomous action/tool orchestration can sit above it later.

### 4.7 Model-level reasoning and system-level reasoning are different

The research distinguishes learned/model-internal reasoning from system-level reasoning built through routing, multiple calls, tools, search, memory, and orchestration. Modern systems commonly combine both. fileciteturn841file0L424-L450

**Revise implication:** Do not design Revise as though reasoning must live inside one model. The engine itself can become a reasoning system while keeping provider/model implementations replaceable.

### 4.8 Stronger models and more inference compute are complementary

The research finds a tradeoff between model capability and inference-time search/compute: additional inference can compensate for some model weakness, but there are limits when the underlying model lacks necessary knowledge or capability. fileciteturn841file0L570-L607

**Revise implication:** Power cannot mean simply “use a stronger model.” Model routing and effort allocation should remain separate policy dimensions that can cooperate.

### 4.9 RL-trained reasoning is useful but not a replacement for system verification

The research describes RL-trained reasoners as learning stronger decomposition, persistence, verification, and problem-solving behaviors, while also noting that outcome rewards do not guarantee faithful reasoning and that RL has limitations and risks. fileciteturn841file0L512-L569

**Revise implication:** Revise should not depend on a provider having a reasoning-trained model. The system-level self-correction layer remains valuable across model families.

### 4.10 Hidden reasoning should not become a Revise user-facing contract

The research describes hidden/internal reasoning, visible CoT, and the important distinction between internal computation and a human-readable explanation. It notes that visible CoT is not guaranteed to faithfully represent the actual internal process. fileciteturn841file0L884-L919

**Revise implication:** Revise should not expose or depend on raw provider chain-of-thought. Diagnostics should be structured, bounded, and purpose-built for correction/verification rather than treating hidden reasoning as an API contract.

### 4.11 Adaptive reasoning is the strongest fit for Power

The research describes explicit reasoning controls, automatic difficulty-aware allocation, model escalation, and bounded agent loops. It emphasizes that heavy reasoning should not be spent on every task. fileciteturn842file0L104-L131

**Revise implication:** Power should eventually govern an adaptive resource envelope. The engine should spend effort where the task needs it and stop when further work is not justified.

### 4.12 Hybrid orchestration is the long-term direction, but not the first rebuild

The research's hybrid architecture is essentially:

```text
User Query
   -> Router / Policy
   -> Model + reasoning budget
   -> optional tools/search/planning
   -> verifier/critic
   -> final result
```

It describes this as a broader trend in which reasoning becomes a property of the system rather than only the LLM. fileciteturn842file0L132-L159

**Revise implication:** This supports our layered architecture, but does not justify implementing every layer now.

### 4.13 Economics reinforce bounded adaptive effort

The research emphasizes inference cost, latency, diminishing returns, and the importance of cost per successful task rather than cost per token alone. It recommends hybrid allocation: cheap paths for easy tasks and expensive reasoning for difficult/high-value tasks. fileciteturn842file0L69-L103

**Revise implication:** A future Power controller should optimize useful work, not blindly maximize compute. The metric to care about is closer to **successful task completion per unit of effort/cost/latency**.

### 4.14 Distillation is a future efficiency path

The research describes teacher/student and RL distillation as ways to transfer reasoning behavior into smaller models, with DeepSeek cited as evidence that smaller models can acquire nontrivial reasoning patterns. It also notes overfitting and generalization caveats. fileciteturn842file0L36-L68

**Revise implication:** The architecture should remain model-agnostic so future cheaper specialized reasoners can replace expensive models without changing the self-correction foundation.

### 4.15 Major failure modes must shape the foundation

The research identifies latency/cost, diminishing returns, overthinking, correlated verifier errors, overconfidence, orchestration complexity, reward hacking, security/prompt injection, context exhaustion, inconsistency, and brittleness. fileciteturn841file0L810-L869

**Revise implication:** More reasoning is not inherently safer or better. Every future expansion needs bounded budgets, independent evidence where possible, stopping conditions, security boundaries, and regression protection.

---

## 5. Revise's Core Self-Correction Model

The discussion now favors one compact core rather than five separate correction systems.

### Core loop

```text
Attempt
  -> Evaluate
  -> Diagnose
  -> Correct
  -> Re-evaluate
  -> Decide
```

Where **Correct** is intentionally extensible.

Today it can mean rewriting a weak answer or fixing an identified mistake. Later it can mean changing the reasoning approach, gathering evidence, generating another candidate, switching models, invoking a tool, or changing execution strategy.

### Correction capability levels

These are not five separate engines. They are increasingly capable uses of the same correction abstraction:

1. **Error correction** — fix an obvious factual, logical, formatting, or instruction error.
2. **Quality correction** — improve a weak but not strictly incorrect answer.
3. **Evidence correction** — obtain or validate evidence when the answer is insufficiently grounded.
4. **Reasoning correction** — recognize that the current reasoning approach is flawed and try a materially different approach.
5. **Strategy correction** — change the overall method/model/tool/search strategy when the current approach is failing.

The important architectural distinction is:

> **Revise must eventually be able to change the approach, not merely rewrite the output.**

A loop that only rewrites the same failed approach can produce:

```text
bad answer -> rewrite -> similar bad answer -> rewrite -> ...
```

A stronger self-correcting system can produce:

```text
failed approach
   -> diagnose approach failure
   -> select different strategy
   -> new attempt
   -> verify improvement
```

### Minimum viable core

For the first stable self-correction implementation, the core does not need hidden CoT, tree search, multi-agent debate, or tools. It needs:

- a candidate attempt
- structured evaluation
- actionable diagnosis
- a bounded correction action
- re-evaluation
- explicit improvement assessment
- safe stopping
- best-valid-version preservation
- ASK when reliable correction is blocked

That is enough to make the identity of Revise real without prematurely implementing every modern reasoning mechanism.

---

## 6. Diagnosis — The Bridge to Human-Like Adaptive Reasoning

The next major design problem is not “how do we make the model think longer?” It is:

> **How does Revise determine why the current attempt is inadequate and what kind of correction is justified?**

A useful future diagnosis structure should be able to represent:

```text
Diagnosis
├── outcome: pass / fail / unknown / partial
├── affected dimensions
├── issue identities
├── severity
├── confidence
├── evidence conflicts
├── missing context
├── failure class
├── suggested correction
├── whether current strategy is still viable
└── escalation recommendation
```

Potential failure classes:

- `task_mismatch`
- `instruction_violation`
- `factual_error`
- `reasoning_error`
- `missing_context`
- `missing_evidence`
- `verification_failure`
- `format/schema_error`
- `style/proportionality_issue`
- `strategy_failure`
- `provider/model_failure`
- `tool_failure` (future)
- `search_failure` (future)

These should remain conceptual until the contract is finalized. Avoid adding a large taxonomy merely for completeness.

### Why diagnosis matters

Diagnosis lets the controller distinguish:

```text
Needs a better answer
vs
Needs more evidence
vs
Needs another reasoning attempt
vs
Needs a different strategy
vs
Cannot safely complete -> ASK
```

That distinction is the foundation of adaptive self-correction.

---

## 7. Power — Current Architectural Direction

Power is **not**:

- response verbosity
- user intent
- a vendor-specific reasoning parameter
- “always use the strongest model”
- “always think longer”

Power is:

> **A bounded policy for how much useful computational/verification/orchestration effort Revise may spend on the task.**

### Future resource envelope

```text
Power
  ├── generation effort
  ├── revision budget
  ├── verification budget
  ├── candidate budget
  ├── search/tool budget
  ├── model escalation budget
  ├── parallelism budget
  └── stopping policy
```

Not every resource needs to exist in version 1. The abstraction should simply avoid preventing them later.

### Mode intent

| Mode | Core intent |
|---|---|
| Lite | fast path, minimal necessary effort |
| Basic | balanced effort and reliability |
| Pro | deeper effort when justified by task complexity/reliability |
| Auto | dynamically allocate appropriate effort/resources |

**Important:** Lite should not intentionally mean low-quality. Pro should not intentionally mean verbose. Auto must not override explicit user intent.

### Power and task difficulty

The research strongly supports adaptive allocation. Therefore, future Power should not simply map `Lite=1, Basic=2, Pro=3` and blindly consume the maximum. The controller should be able to stop early when the task is already satisfactorily solved.

Conceptually:

```text
allowed budget = mode/power policy
actual spend   = task difficulty + diagnosis + evidence need + stopping rules
```

This gives us a stable meaning for Power even as future mechanisms are added.

---

## 8. Context Sufficiency and Clarification

Current gap:

```text
missing_context -> ASK
```

exists, but discovering missing context is underdeveloped.

### Desired behavior

Before committing to an answer path, Revise should determine whether the available context is sufficient for reliable completion.

```text
Task Contract
   -> Context Sufficiency
      |-- sufficient -> proceed
      `-- insufficient -> targeted ASK
```

The goal is **minimal necessary clarification**, not maximum information gathering.

### Important distinction

The engine must distinguish:

```text
missing information that the user must provide
vs
uncertainty that Revise can resolve itself
```

Examples:

- Missing user-specific constraint → ask.
- Arithmetic uncertainty → verify deterministically.
- Missing factual source that can be retrieved later → future tool/search path.
- Weak reasoning → revise/try another strategy.
- Impossible to proceed reliably without a required fact → ask.

### Clarification should be bounded

Avoid:

```text
ASK -> answer -> ASK -> answer -> ...
```

The future clarification state should track what has already been asked and answered and prevent redundant questions.

Potential state:

```text
known_context
missing_context
questions_asked
answers_received
remaining_required_context
clarification_attempts
```

Whether this belongs directly in `TaskContract` or adjacent execution state remains to be decided.

### Do not over-question

The context assessor must not become a keyword-rule engine or a generic “ask before answering” system. Simple tasks should continue directly. Complex tasks should ask only when the missing information materially affects correctness, safety, or task completion.

---

## 9. Candidate Search and Alternative Solutions — Future Capability

The research supports multiple candidate generation, self-consistency, reranking, and verification as useful forms of test-time search. fileciteturn841file0L82-L85

Revise should eventually support an optional abstraction such as:

```text
Task
 -> candidate generation
 -> candidate evaluation / verification
 -> select strongest candidate
 -> revise if none is adequate
```

But this should remain optional.

### Why not implement it immediately?

- cost multiplies rapidly
- correlated errors remain possible
- ordinary tasks do not need N candidates
- the current single-candidate self-correction loop is not yet fully characterized
- search should be introduced only where it measurably improves outcomes

### Future search strategies

Potential implementations include:

- independent sampling
- best-of-N
- self-consistency voting
- reranking
- alternative reasoning strategies
- beam/tree search where justified
- parallel specialist attempts

These are **strategies**, not separate foundation identities.

---

## 10. Tools, Retrieval, Memory, and Agents — Future Extension Architecture

The research indicates that strong production systems increasingly combine models with tools, retrieval, memory, routers, and agent loops. fileciteturn842file0L132-L159

Revise should therefore preserve this layered architecture:

```text
                 FUTURE EXTENSIONS
     tools / search / retrieval / memory / actions
                    / multi-agent
                           |
                           v
                  ORCHESTRATION LAYER
                           |
                           v
        -----------------------------------------
          REVISE SELF-CORRECTION CORE
        -----------------------------------------
        Contract -> Profile -> Primary
             -> Evaluate / Verify
             -> Diagnose -> Correct
             -> Re-evaluate -> Decide
             -> Best valid / ASK
```

### Extension rule

Future capabilities must consume and respect:

- Task Contract
- explicit user intent
- Power/resource budgets
- evidence contracts
- safety/hard gates
- revision-quality rules
- stopping conditions
- best-version rules
- ASK boundary
- observability/security boundaries

They must not create a parallel “agent brain” that bypasses the foundation.

### Agent identity decision

Revise **is allowed to be an agent in behavior** because it can observe its own evaluation, correct itself, and continue toward a goal.

Revise does **not** need to become a general agent framework containing every possible tool, workflow, memory, and multi-agent primitive.

This distinction preserves both the original goal and architectural clarity.

---

## 11. Research-Derived Architecture Patterns Worth Preserving

The research describes recurring production patterns:

- single model → answer
- reasoning model → answer
- model → tool → model
- planner → tools → verifier → final model
- multiple candidates → reranker
- planner + executor + critic
- multiple specialized agents
- reasoning model + external search
- reasoning model + browser/code/memory
- dynamic orchestration based on task difficulty

fileciteturn841file0L639-L695

Revise should not implement all patterns as separate modes. Instead, they should map onto a small number of future capabilities:

```text
Generation
Evaluation
Diagnosis
Correction
Verification
Candidate/Search
Tool/Environment
Orchestration
```

This is the preferred anti-redundancy principle.

---

## 12. Production Lessons Relevant to Revise

### 12.1 Explicit effort controls exist in modern products

The research reports provider controls such as OpenAI reasoning effort and Google's thinking level, plus adaptive compute behavior. fileciteturn841file0L925-L990

**Lesson:** Revise should have provider-neutral effort semantics and let adapters translate them to provider-specific controls where available.

### 12.2 Strong model + orchestration is more powerful than either alone

The research repeatedly describes hybrid systems combining model capability with routing, search, tools, and verification. fileciteturn841file0L441-L450

**Lesson:** Do not make the engine dependent on a “reasoning model” being available. The system should improve even ordinary models through evaluation and correction.

### 12.3 More compute has diminishing returns

The research reports logarithmic/sublinear gains and overthinking risks. fileciteturn841file0L484-L490

**Lesson:** stopping conditions are a first-class part of future Power, not an afterthought.

### 12.4 Verifier independence matters

The research warns about correlated errors when generator and verifier share weaknesses. fileciteturn841file0L836-L842

**Lesson:** deterministic verification should remain preferred when possible, and future independent verifiers should be supported.

### 12.5 Agent loops need explicit bounds

The research notes loops, tool failures, context exhaustion, security vulnerabilities, and orchestration complexity. fileciteturn841file0L843-L869

**Lesson:** every future action/search/tool loop needs hard resource and step limits plus safe termination.

### 12.6 Reasoning traces are not reliable explanations

The research explicitly warns that visible CoT may not reflect the actual causal process. fileciteturn841file0L894-L919

**Lesson:** Revise should expose structured outcome/diagnostic metadata to development tooling rather than raw hidden reasoning.

---

## 13. Feature Roadmap — Discussed / Intended, Not All Immediate

### Foundation / near-term

1. **Minimum viable self-correction loop**
   - candidate
   - evaluation
   - diagnosis
   - correction
   - re-evaluation
   - improvement check
   - bounded stop
   - ASK boundary

2. **Provider-neutral generation effort policy**
   - connect mode/profile effort to Primary generation behavior
   - keep provider-specific mappings in adapters
   - do not equate effort with verbosity

3. **Context sufficiency / minimal clarification**
   - identify materially missing information
   - ask targeted questions
   - track clarification state
   - avoid repeated or unnecessary questions

4. **Stronger diagnosis representation**
   - distinguish answer error from strategy failure
   - carry confidence, issue identity, affected dimensions, evidence state, and correction guidance

5. **Proportionality evaluation**
   - judge whether answer depth is appropriate to the task
   - never reduce this to a word-count rule

### Future reasoning expansion

6. **Adaptive effort allocation**
   - allocate actual compute based on task difficulty and current outcome
   - stop early when sufficient
   - escalate when failure indicates more work is justified

7. **Alternative candidate/search capability**
   - multiple candidates when justified
   - reranking/verification
   - self-consistency/best-of-N
   - alternative reasoning strategies

8. **Strategy correction**
   - allow correction to change method, not merely wording
   - support model/tool/search strategy changes later

9. **Independent/richer verification**
   - stronger deterministic checks
   - external evidence
   - independent model/verifier roles
   - task-specific verification

### Future orchestration / agent layer

10. **Tool execution**
11. **Retrieval/search**
12. **Bounded browser/API/environment interaction**
13. **Short-term and long-term memory where genuinely required**
14. **Planner/executor/critic orchestration where justified**
15. **Parallel specialist execution**
16. **Multi-agent collaboration/delegation**
17. **Long-horizon task management**

### Future model-level / efficiency research

18. **Reasoning-model selection/routing**
19. **Distilled reasoning models**
20. **Provider-native hidden reasoning controls through adapters**
21. **Latent/continuous reasoning research where practical**
22. **More efficient test-time scaling**

These are capabilities to preserve architectural room for, **not commitments to implement immediately**.

---

## 14. Decision Logic for Future Self-Correction

A future controller should conceptually distinguish:

```text
Evaluation says good
    -> ACCEPT

Evaluation says weak but correctable
    -> CORRECT

Evaluation says current strategy is inadequate
    -> STRATEGY CORRECT / ESCALATE

Evaluation requires evidence/tool unavailable
    -> ASK or bounded future tool path

Evaluation is unknown / malformed / low-confidence
    -> do not pass; ASK or bounded correction

Deterministic/external evidence fails
    -> REVISE if budget remains, otherwise ASK

Revision does not improve
    -> stop according to policy / preserve best valid version

No reliable path remains
    -> ASK
```

This is a future conceptual controller, not a request to replace the current decision engine immediately.

---

## 15. Scenario Matrix

| Scenario | Desired behavior | Future capability involved |
|---|---|---|
| Simple factual question | Answer directly | Minimal effort |
| Simple arithmetic | Answer + deterministic verification | Existing verifier |
| Explicit short-answer request | Respect brevity | Intent authority + proportionality |
| Complex coding/debugging | Deeper work + compile/test verification | Power + verification |
| Missing source/document | ASK rather than invent | Context sufficiency |
| Under-specified injury question | Ask only critical context | Context sufficiency + safety |
| Fully specified sensitive question | Answer with safeguards | Evaluation + hard gates |
| Ambiguous legal/financial task | Ask for material jurisdiction/facts | Context sufficiency |
| Creative writing | Usually direct | Avoid unnecessary reasoning |
| Complex planning | Reason, verify constraints, ask only when necessary | Adaptive effort |
| Structured JSON | Generate + schema verify | Existing deterministic verification |
| Auto difficult task | Increase actual effort adaptively | Future Power controller |
| Hard reliability-critical task | Potentially multiple candidates + stronger verification | Future search |
| Evidence-dependent task | Retrieve/verify evidence when tools exist | Future tools/search |
| Failed reasoning approach | Try materially different approach | Strategy correction |
| Long-horizon autonomous task | Future bounded agent loop | Orchestration layer |

---

## 16. Candidate Foundation Changes — Prioritized

### Priority A — Core self-correction

Implement the minimum correction abstraction around the existing revision/evaluation foundation without replacing working components unnecessarily.

### Priority B — Generation effort

Introduce provider-neutral generation effort semantics so Power affects useful generation effort as well as downstream revision/verification budgets.

### Priority C — Diagnosis

Strengthen the information passed from evaluation to correction so the engine can distinguish ordinary revision from strategy change.

### Priority D — Context sufficiency

Add a bounded, provider-neutral mechanism for detecting answer-critical missing context and generating minimal clarification requests.

### Priority E — Proportionality

Strengthen task-appropriate depth/conciseness evaluation without simplistic length scoring.

### Priority F — Future search abstraction

Reserve a bounded candidate/search interface but do not force best-of-N into ordinary execution.

### Priority G — Future orchestration boundary

Keep tools/search/memory/agent actions outside the protected core while defining contracts that allow them to integrate later.

---

## 17. Risks / Guardrails

- More reasoning can increase latency/cost without improving the result.
- More reasoning can sometimes make easy answers worse through overthinking.
- Candidate search can multiply cost and correlated errors.
- A context gate can over-question users.
- A weak context assessor can incorrectly block good answers.
- Clarification can become an infinite loop.
- Strategy correction can become unpredictable without bounded policies.
- Provider-specific reasoning parameters must not leak into the core.
- Stronger brevity scoring can penalize necessary detail.
- Tools introduce external failures and security/prompt-injection surfaces.
- Long agent loops can exhaust context and budgets.
- Multiple agents can make failures difficult to attribute.
- Same-model generation and verification can share correlated errors.
- Hidden reasoning must not become a user-facing or provider-specific foundation dependency.
- RL/reasoning-model claims must not be treated as substitutes for deterministic verification.
- Future orchestration must not bypass hard gates, evidence precedence, or ASK boundaries.
- No feature should be added solely because it is fashionable in current AI products; it must solve a measured Revise problem or clearly preserve an essential future contract.

---

## 18. Non-Goals

Do not use this work to:

- redesign the UI
- change the stable API unnecessarily
- expose raw hidden chain-of-thought
- lock Revise to a specific reasoning provider/model
- replace deterministic verification with LLM judgment
- make Lite intentionally lower-quality
- force Pro responses to be long
- force every task through deep reasoning
- force every task through multiple candidates
- turn Revise into a general agent framework immediately
- introduce multi-agent orchestration without a demonstrated need
- rewrite stable foundation components without evidence
- contaminate the research-only artifact with project decisions
- treat vendor-specific controls as the permanent definition of Power

---

## 19. Current Conclusion — Discussion Still In Progress

The research and discussion now support a stronger but still deliberately compact foundation:

1. **North star:** self-correcting AI agent behavior.
2. **Core loop:** Attempt → Evaluate → Diagnose → Correct → Re-evaluate → Decide.
3. **Correction is one extensible capability**, not five redundant engines.
4. **Reasoning correction (#4) and strategy correction (#5) are the long-term differentiators** because they allow Revise to change approach rather than only rewrite output.
5. **Power is a bounded resource envelope**, not verbosity, intent, or one provider parameter.
6. **Adaptive effort is preferable to always-max effort.**
7. **Context sufficiency and minimal clarification are required foundation capabilities** for reliable self-correction.
8. **Candidate search, tools, retrieval, memory, and broad agent orchestration are future extensions**, not first-foundation requirements.
9. **Verification remains independent and evidence-driven wherever possible.**
10. **The core must remain provider-agnostic and bounded.**
11. **The system should prefer the simplest sufficient strategy and escalate only when justified.**
12. **The architecture should be capable of growing from revision to reasoning to strategy correction without being rebuilt each time.**

### Still to settle before implementation handoff

- exact minimum diagnosis contract
- exact first-version Power/resource mapping
- context-sufficiency placement and evaluation method
- clarification continuation semantics
- triggers for more effort vs revision vs strategy change vs ASK
- exact definition of “meaningful strategy change”
- whether generation effort can be expressed consistently across current providers
- how proportionality should be evaluated without verbosity bias
- precise future extension contracts for candidate search and orchestration
- which research claims require external verification before becoming implementation requirements

We should continue the discussion before writing the final Foundation Agent implementation section.

---

## 20. Final Foundation Agent Response — Reserved

This section will be completed only after the design is settled.

The final handoff will contain:

1. clear objective
2. confirmed current problems
3. research basis and evidence strength
4. final architectural decision
5. exact files/layers to modify
6. contract/model changes
7. Power semantics
8. self-correction/diagnosis semantics
9. context sufficiency and clarification semantics
10. ASK/terminal-output behavior
11. safety/ambiguity rules
12. future extension boundaries
13. tests and invariant updates
14. acceptance criteria
15. non-goals/protected elements
16. implementation sequence
17. validation plan

No implementation should be inferred from this reserved section until it is explicitly finalized.

---

## 21. Decision Log

### 2026-09-14 — Research workspace separation

**Decision:** Keep the external reasoning/model research artifact completely clean. Project-specific analysis and implementation decisions belong only in this response document.

### 2026-09-14 — Discussion Round 1: product identity and extensibility

**Decision:** Revise's primary goal is a self-correcting AI agent. The foundation should optimize for reliable generation → evaluation/verification → correction → decision rather than becoming a general-purpose agent framework immediately.

**Decision:** Broad agentic capabilities such as tools, search, memory, long-horizon actions, and multi-agent delegation should have future extension points but must not destabilize or bypass the protected self-correction core.

**Decision:** Power is conceptually a bounded effort/resource envelope, not response verbosity or user intent. Exact Power mechanics remain intentionally open pending further discussion.

**Decision:** Candidate generation/search should remain architecturally possible but optional; do not add best-of-N simply because it appears in modern systems.

### 2026-09-14 — Discussion Round 2: correction architecture

**Decision:** Treat error correction, quality correction, evidence correction, reasoning correction, and strategy correction as levels of one extensible correction capability rather than five separate foundation systems.

**Decision:** The protected minimum self-correction loop is Attempt → Evaluate → Diagnose → Correct → Re-evaluate → Decide.

**Decision:** Future self-correction must be able to change the reasoning approach/strategy, not merely rewrite the same answer.

**Decision:** Power should eventually govern a bounded resource envelope whose concrete resources can expand over time; actual effort should be adaptive and stoppable rather than always maximal.

**Decision:** Candidate search, tools, retrieval, memory, and multi-agent orchestration remain future capabilities layered around the core.

**Decision:** Continue discussion before drafting the final Foundation Agent implementation response.
