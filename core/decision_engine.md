# Decision Engine

The Decision Engine is the authoritative control layer of Reiterate. It converts evaluation and verification findings into a bounded control decision after the candidate has passed through the engine's deliberation process.

## Decisions

- **ACCEPT** — the candidate satisfies required conditions with sufficient evidence.
- **REVISE** — a material correctable failure exists and revision budget remains.
- **ASK** — required information is missing, ambiguity blocks reliable completion, evaluation is unavailable/unknown, or continued revision cannot safely resolve the problem.

## Runtime flow

```text
Task Contract
    ↓
Mode / Evaluation Profile / Model Routing
    ↓
Bounded Deliberation
  ├─ Plan
  ├─ Reason
  ├─ Reflect
  ├─ Correct / Change Approach (when warranted)
  └─ Re-reason / Re-reflect within bounds
    ↓
Candidate
    ↓
Secondary Evaluation + Evidence
    ↓
Deterministic / External Verification
    ↓
Evidence Fusion
    ↓
Diagnosis (post-hoc synthesis)
    ↓
Revision Quality Comparison
    ↓
Decision Authority
 ├─ ACCEPT → return best accepted version
 ├─ REVISE → bounded further deliberation / revision
 └─ ASK    → stop and return best available candidate
```

Deliberation is an upstream reasoning capability, not a replacement for evaluation, verification, or decision authority. A reflection, correction plan, or reasoning state may identify uncertainty, propose a correction, or recommend changing approach, but it cannot by itself authorize acceptance.

The engine is provider-agnostic. The core understands logical roles such as **Primary**, **Secondary**, and **Verifier** and may add deliberation capabilities without binding them to fixed model identities. Provider adapters and model identifiers stay outside core decision policy.

Primary, Secondary, and deliberation model selections are independently configurable. A provider may be used for multiple roles, but role configuration remains separate so combinations such as Gemini + Gemini, Gemini + Grok, OpenAI + Gemini, or local Ollama models can be used without changing engine logic.

## Authority boundary

The engine follows the principle:

> **Flexible reasoning may explore and propose; authoritative control decides and enforces.**

In particular:

- Planning, reasoning, reflection, and correction are non-authoritative.
- Model evaluation is evidence about quality, not final authority.
- Deterministic and directly verifiable external evidence takes precedence over model opinion when applicable.
- Hard safety, security, critical-constraint, and required-verification failures cannot be overridden by deliberation or model judgment.
- A correction is a hypothesis about how to improve a candidate, not proof that the corrected candidate is valid.
- Every materially changed candidate must independently pass the applicable evaluation and verification path.

## Policy order

1. Preserve user intent, explicit mode, constraints, and required output structure.
2. Enforce hard safety, security, and critical user constraints.
3. Resolve material missing context through `ASK` rather than invention.
4. Allow bounded deliberation to reason, challenge assumptions, reconsider approaches, and propose targeted corrections when the task warrants it.
5. Evaluate the resulting candidate using task-specific dimensions and evidence.
6. Treat unknown or unavailable evaluation as non-passing; do not claim an unevaluated candidate is verified.
7. Prefer deterministic and external evidence when it can directly verify a property. Deterministic failures cannot be overridden by model judgment. External source-verification failures also block acceptance when a required cited source is unreachable or missing.
8. Diagnose the observed failure or improvement after evaluation and verification; diagnosis does not replace decision authority.
9. For revisions, compare against the immediately previous evaluated version; require material quality improvement, resolved relevant issues, or both.
10. Treat regressions or unchanged revisions as non-acceptable and continue within the revision budget; when no budget remains, `ASK` and retain the best valid version.
11. Respect deliberation, revision, and verification budgets.
12. Compare candidate versions and retain the best valid result.

External source verification is deliberately narrower than factual claim verification: it can establish that a cited HTTP(S) source was reachable, but not that the source supports every claim in the answer. Semantic groundedness and evidence quality remain separate evaluation dimensions.

Revision quality tracks baseline score, revised score, score delta/net improvement, resolved issues, introduced issues, improved dimensions, and regressed dimensions. A revision can qualify as improved without increasing its overall score when it resolves a relevant prior issue. Material introduced issues or dimension regressions make the revision regressed.

Numerical weighting is intentionally not frozen at this foundation stage. Policy correctness and evidence precedence come first.

The runtime decision policy lives in `engine/revise/decision.py`. Deliberation contracts and runtime orchestration are expected to live alongside the existing provider-neutral revision/evaluation contracts rather than replacing the decision layer.
