from __future__ import annotations

from dataclasses import dataclass

from .contracts import make_contract
from .engine import Engine
from .providers import OpenAIPrimary
from .revise.models import Decision, Mode


@dataclass(frozen=True)
class EngineRequest:
    """Minimal request boundary for UI-to-engine integration."""

    prompt: str
    mode: Mode = Mode.BASIC


@dataclass(frozen=True)
class EngineResponse:
    """Stable response boundary for UI-to-engine integration."""

    text: str
    decision: Decision
    version_id: str | None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "text": self.text,
            "decision": self.decision.value,
            "version_id": self.version_id,
        }


class EngineService:
    """Thin application boundary; HTTP/transport concerns stay outside the engine."""

    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def handle(self, request: EngineRequest) -> EngineResponse:
        prompt = request.prompt.strip()
        if not prompt:
            raise ValueError("prompt must not be empty")

        contract = make_contract(prompt, mode=request.mode)
        result = self.engine.run(contract)
        version = result.final_version
        return EngineResponse(
            text=version.response if version else "",
            decision=result.decision,
            version_id=version.id if version else None,
        )

    def handle_payload(self, payload: dict[str, object]) -> dict[str, str | None]:
        """Convert a transport payload into the stable engine response shape."""
        prompt = payload.get("prompt")
        if not isinstance(prompt, str):
            raise ValueError("prompt must be a string")

        raw_mode = payload.get("mode", Mode.BASIC.value)
        try:
            mode = Mode(raw_mode) if isinstance(raw_mode, str) else Mode.BASIC
        except ValueError as exc:
            raise ValueError(f"unsupported mode: {raw_mode}") from exc

        return self.handle(EngineRequest(prompt=prompt, mode=mode)).to_dict()


def create_default_service() -> EngineService:
    """Create the first real runtime using the configured OpenAI Primary."""
    return EngineService(Engine(OpenAIPrimary()))
