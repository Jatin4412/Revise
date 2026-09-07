# Decision Engine

The Decision Engine converts evaluation findings into a bounded control decision.

## Decisions

- **ACCEPT** — the candidate satisfies required conditions with sufficient evidence.
- **REVISE** — a material correctable failure exists and revision budget remains.
- **ASK** — required information is missing, ambiguity blocks reliable completion, evaluation is unavailable/unknown, or continued revision cannot safely resolve the problem.

## Runtime flow

```text
Task Contract
    ↓
Role-specific Model Selection / Router
    ↓
Primary generation
    ↓
Secondary evaluation
    ↓
Deterministic / external verification
    ↓
Evidence fusion
    ↓
Decision
 ├─ ACCEPT → return best accepted version
 ├─ REVISE → regenerate with evaluation feedback (bounded)
 └─ ASK    → stop and return best available candidate
```

The engine is provider-agnostic. The core understands only the roles **Primary**, **Secondary**, and **Verifier**. Provider adapters and model identifiers stay outside the core decision policy.

Primary and Secondary model selections are independent. When selection is automatic, the system should prefer the strongest appropriate configured model for **Primary** generation and a suitable independent model for **Secondary** evaluation. Explicit model selections remain authoritative and are not silently replaced.

A provider may be used for both roles, but role configuration remains separate so the system can use combinations such as Gemini + Gemini, Gemini + Grok, OpenAI + Gemini, or local Ollama models without changing engine logic.

## Policy order

1. Enforce hard safety, security, and critical user constraints.
2. Resolve material missing context through `ASK` rather than invention.
3. Check required task completion and correctness.
4. Apply task-specific quality dimensions and evidence.
5. Treat unknown or unavailable evaluation as non-passing; do not claim an unevaluated candidate is verified.
6. Prefer deterministic and external evidence when it can directly verify a property.
7. Respect revision and verification budgets.
8. Compare candidate versions and retain the best valid result.

Numerical weighting is intentionally not frozen at this foundation stage. Policy correctness and evidence precedence come first.

The runtime decision policy lives in `engine/revise/decision.py`.
