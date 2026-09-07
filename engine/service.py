from __future__ import annotations

import os
from dataclasses import dataclass

from .contracts import make_contract
from .engine import Engine
from .llm import build_primary, build_secondary
from .model import ModelRouter, ModelSelection, SecondaryRouter
from .providers import FunctionPrimary
from .revise.models import Decision, Mode


@dataclass(frozen=True)
class EngineRequest:
    """Minimal request boundary with independent Primary and Secondary selections."""

    prompt: str
    mode: Mode = Mode.BASIC
    model: ModelSelection | None = None  # Backward-compatible alias for Primary selection.
    primary_model: ModelSelection | None = None
    secondary_model: ModelSelection | None = None


@dataclass(frozen=True)
class EngineResponse:
    """Stable response boundary for UI-to-engine integration."""

    text: str
    decision: Decision
    version_id: str | None

    def to_dict(self) -> dict[str, str | None]:
        return {"text": self.text, "decision": self.decision.value, "version_id": self.version_id}


class EngineService:
    """Thin application boundary; transport concerns stay outside the engine."""

    def __init__(
        self,
        engine: Engine,
        *,
        model_router: ModelRouter | None = None,
        primary_router: ModelRouter | None = None,
        secondary_router: SecondaryRouter | None = None,
    ) -> None:
        self.engine = engine
        self.primary_router = primary_router or model_router
        self.secondary_router = secondary_router

    def handle(self, request: EngineRequest) -> EngineResponse:
        prompt = request.prompt.strip()
        if not prompt:
            raise ValueError("prompt must not be empty")

        contract = make_contract(prompt, mode=request.mode)
        primary_selection = request.primary_model or request.model
        primary = self.primary_router.resolve(primary_selection) if self.primary_router else None
        secondary = self.secondary_router.resolve(request.secondary_model) if self.secondary_router else None
        result = self.engine.run(contract, primary=primary, secondary=secondary)
        version = result.final_version
        return EngineResponse(
            text=version.response if version else "",
            decision=result.decision,
            version_id=version.id if version else None,
        )

    def handle_payload(self, payload: dict[str, object]) -> dict[str, str | None]:
        prompt = payload.get("prompt")
        if not isinstance(prompt, str):
            raise ValueError("prompt must be a string")

        raw_mode = payload.get("mode", Mode.BASIC.value)
        try:
            mode = Mode(raw_mode) if isinstance(raw_mode, str) else Mode.BASIC
        except ValueError as exc:
            raise ValueError(f"unsupported mode: {raw_mode}") from exc

        legacy_primary = _parse_model_selection(payload.get("model"))
        primary = _parse_model_selection(payload.get("primary_model")) or legacy_primary
        secondary = _parse_model_selection(payload.get("secondary_model"))
        return self.handle(
            EngineRequest(prompt=prompt, mode=mode, primary_model=primary, secondary_model=secondary)
        ).to_dict()


def create_default_service() -> EngineService:
    """Create the runtime with role and provider selection outside the core engine."""
    primary_selection = ModelSelection(
        os.environ.get("REVISE_PRIMARY_PROVIDER", "gemini"),
        os.environ.get("REVISE_PRIMARY_MODEL") or os.environ.get("GEMINI_PRIMARY_MODEL"),
    )
    secondary_selection = ModelSelection(
        os.environ.get("REVISE_SECONDARY_PROVIDER", "gemini"),
        os.environ.get("REVISE_SECONDARY_MODEL") or os.environ.get("GEMINI_SECONDARY_MODEL"),
    )

    primary_router = ModelRouter(
        {
            "gemini": lambda model: build_primary("gemini", model),
            "openai": lambda model: build_primary("openai", model),
            "grok": lambda model: build_primary("grok", model),
            "ollama": lambda model: build_primary("ollama", model),
        },
        default=primary_selection,
    )
    secondary_router = SecondaryRouter(
        {
            "gemini": lambda model: build_secondary("gemini", model),
            "openai": lambda model: build_secondary("openai", model),
            "grok": lambda model: build_secondary("grok", model),
            "ollama": lambda model: build_secondary("ollama", model),
        },
        default=secondary_selection,
    )

    return EngineService(
        Engine(FunctionPrimary(lambda _contract, _context: "")),
        primary_router=primary_router,
        secondary_router=secondary_router,
    )


def _parse_model_selection(raw: object) -> ModelSelection | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("model selection must be an object with provider and optional model")
    provider = raw.get("provider")
    model = raw.get("model")
    if not isinstance(provider, str) or not provider.strip():
        raise ValueError("model.provider must be a non-empty string")
    if model is not None and not isinstance(model, str):
        raise ValueError("model.model must be a string when provided")
    return ModelSelection(provider=provider.strip(), model=model.strip() if model else None)
