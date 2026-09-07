from __future__ import annotations

import os
from dataclasses import dataclass

from .contracts import make_contract
from .engine import Engine
from .model import ModelRouter, ModelSelection
from .providers import GeminiPrimary, OpenAIPrimary
from .revise.models import Decision, Mode


@dataclass(frozen=True)
class EngineRequest:
    """Minimal request boundary for UI-to-engine integration."""

    prompt: str
    mode: Mode = Mode.BASIC
    model: ModelSelection | None = None


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

    def __init__(self, engine: Engine, *, model_router: ModelRouter | None = None) -> None:
        self.engine = engine
        self.model_router = model_router

    def handle(self, request: EngineRequest) -> EngineResponse:
        prompt = request.prompt.strip()
        if not prompt:
            raise ValueError("prompt must not be empty")

        contract = make_contract(prompt, mode=request.mode)
        primary = self.model_router.resolve(request.model) if self.model_router else None
        result = self.engine.run(contract, primary=primary)
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

        model = _parse_model_selection(payload.get("model"))
        return self.handle(EngineRequest(prompt=prompt, mode=mode, model=model)).to_dict()


def create_default_service() -> EngineService:
    """Create the runtime with provider selection kept outside the core engine."""
    default_provider = os.environ.get("REVISE_PROVIDER", "gemini")
    default_model = os.environ.get("REVISE_MODEL")
    default_selection = ModelSelection(default_provider, default_model)

    router = ModelRouter(
        {
            "gemini": lambda model: GeminiPrimary(model=model),
            "openai": lambda model: OpenAIPrimary(model=model),
        },
        default=default_selection,
    )
    return EngineService(Engine(FunctionPrimary(lambda _contract, _context: "")), model_router=router)


def _parse_model_selection(raw: object) -> ModelSelection | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("model must be an object with provider and optional model")

    provider = raw.get("provider")
    model = raw.get("model")
    if not isinstance(provider, str) or not provider.strip():
        raise ValueError("model.provider must be a non-empty string")
    if model is not None and not isinstance(model, str):
        raise ValueError("model.model must be a string when provided")
    return ModelSelection(provider=provider.strip(), model=model.strip() if model else None)


from .providers import FunctionPrimary
