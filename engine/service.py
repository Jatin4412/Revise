from __future__ import annotations

from dataclasses import dataclass

from .contracts import make_contract
from .engine import Engine
from .revise.models import Decision, Mode


@dataclass(frozen=True)
class EngineRequest:
    """Minimal request boundary for the first UI-to-engine integration."""

    prompt: str
    mode: Mode = Mode.BASIC


@dataclass(frozen=True)
class EngineResponse:
    """Stable response boundary for the first UI-to-engine integration."""

    text: str
    decision: Decision
    version_id: str | None


class EngineService:
    """Thin application boundary; transport concerns stay outside the engine."""

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
