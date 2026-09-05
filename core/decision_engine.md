# Decision Engine

The Decision Engine converts evaluation findings into a bounded control decision.

## Decisions

- **ACCEPT** — the candidate satisfies required conditions with sufficient evidence.
- **REVISE** — a material correctable failure exists and revision budget remains.
- **ASK** — required information is missing, ambiguity blocks reliable completion, or continued revision cannot safely resolve the problem.

## Policy order

1. Enforce hard safety, security, and critical user constraints.
2. Resolve material missing context through `ASK` rather than invention.
3. Check required task completion and correctness.
4. Apply task-specific quality dimensions and evidence.
5. Respect revision and verification budgets.
6. Compare candidate versions and retain the best valid result.

Numerical weighting is intentionally not frozen at this foundation stage. Policy correctness and evidence precedence come first.

The runtime decision policy lives in `engine/revise/decision.py`.
