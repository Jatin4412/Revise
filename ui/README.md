# Web

The Web layer is the user-facing bridge between the user and the Engine.

## Boundary

```text
User
  ↓
Web / React
  ↓
Engine Interface
  ↓
Engine / Python
```

Web owns presentation, interaction, and UI state. It must not depend on the Engine's internal implementation.

The transport and request/response contract are intentionally left open until the Engine interface is finalized.
