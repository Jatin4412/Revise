# Engine Agent Execution Rules

These rules supplement `engine/agent_context.md` and are part of the engine agent's working context.

## Communication
- State the concrete goal first when reporting work or a problem.
- Do not give vague progress statements such as "I'll look into it" without immediately identifying what is being checked or changed.
- Do not ask the user to perform simple checks that the agent can perform from the repository, logs, tests, or available tools.
- When the request is clear, investigate and implement directly; only ask when a missing detail genuinely changes the implementation.
- Do not stop after identifying a symptom. Trace it to the responsible layer, make the smallest sound fix, and verify the affected behavior.
- If the first approach fails, reassess and choose a different practical path instead of repeating the same check.

## Execution
- For runtime bugs, inspect the actual engine path end-to-end: request -> contract -> model selection -> Primary -> evaluation -> verification -> decision -> final selection.
- Distinguish an engine defect from an external provider response or a UI-layer defect before changing foundation policy.
- Never weaken a foundation invariant just to make a bad candidate pass.
- Prefer a tested, minimal engine fix over speculative workarounds.
- Keep the engine provider-agnostic and do not move UI responsibilities into the engine.
