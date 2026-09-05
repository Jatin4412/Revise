from __future__ import annotations

from dataclasses import dataclass

from revise.models import Mode, TaskContract


@dataclass(frozen=True)
class TaskState:
    """Runtime state shared across analysis, generation, verification and revision."""

    contract: TaskContract
    current_response: str | None = None
    failures: tuple[str, ...] = ()
    corrections: tuple[str, ...] = ()
    confidence: float = 0.0


def make_contract(
    goal: str,
    *,
    mode: Mode = Mode.BASIC,
    requirements: tuple[str, ...] = (),
    constraints: tuple[str, ...] = (),
    context: tuple[str, ...] = (),
) -> TaskContract:
    return TaskContract(
        goal=goal,
        mode=mode,
        requirements=requirements,
        constraints=constraints,
        known_context=context,
    )
