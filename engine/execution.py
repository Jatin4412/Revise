from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Mapping


@dataclass(frozen=True)
class TraceEvent:
    """One safe, structured event from an engine run."""

    timestamp: str
    stage: str
    status: str
    details: Mapping[str, object] = field(default_factory=dict)


@dataclass
class ExecutionTrace:
    """Structured execution history for one Engine.run invocation.

    Trace data intentionally excludes prompts, model responses, credentials, and other
    potentially sensitive payloads. It records execution state and safe metadata only.
    """

    events: list[TraceEvent] = field(default_factory=list)

    def record(self, stage: str, status: str, **details: object) -> TraceEvent:
        event = TraceEvent(
            timestamp=datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            stage=stage,
            status=status,
            details=details,
        )
        self.events.append(event)
        return event

    def snapshot(self) -> tuple[TraceEvent, ...]:
        return tuple(self.events)


TraceSink = Callable[[TraceEvent], None]


def console_trace_sink(event: TraceEvent) -> None:
    """Render a concise developer-facing trace without exposing payload contents."""
    details = " ".join(f"{key}={value}" for key, value in event.details.items())
    suffix = f" | {details}" if details else ""
    print(f"[{event.timestamp}] {event.stage.upper()} {event.status.upper()}{suffix}")
