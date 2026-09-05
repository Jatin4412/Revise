# Revise Engine

The Engine is the evaluator/control-plane foundation. It owns orchestration; provider-specific models, UI, API, and site concerns stay outside this package.

## Flow

```text
Task Contract
     ↓
Evaluation Profile
     ↓
Primary generation
     ↓
Evaluation + evidence fusion
     ↓
Decision Engine
  ├─ ACCEPT → best valid version
  ├─ ASK    → stop for clarification
  └─ REVISE → Primary again (bounded)
```

The engine is intentionally provider-agnostic. Primary and dimension evaluators are injected as callables.
