from __future__ import annotations

import os
from dataclasses import dataclass

from .contracts import make_contract
from .engine import Engine
from .execution import console_trace_sink
from .llm import build_primary, build_secondary
from .model import ModelRouter, ModelSelection, SecondaryRouter
from .providers import FunctionPrimary
from .revise.models import Decision, Mode


@dataclass(frozen=True)
class EngineRequest:
    prompt: str
    mode: Mode = Mode.BASIC
    model: ModelSelection | None = None
    primary_model: ModelSelection | None = None
    secondary_model: ModelSelection | None = None


@dataclass(frozen=True)
class EngineResponse:
    text: str
    decision: Decision
    version_id: str | None

    def to_dict(self) -> dict[str, str | None]:
        return {"text": self.text, "decision": self.decision.value, "version_id": self.version_id}


class EngineService:
    """Application boundary; transport concerns stay outside the engine."""

    def __init__(self, engine: Engine, *, model_router: ModelRouter | None = None, primary_router: ModelRouter | None = None, secondary_router: SecondaryRouter | None = None) -> None:
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
        _annotate_model(primary, primary_selection)
        _annotate_model(secondary, request.secondary_model or (self.secondary_router.default if self.secondary_router else None))
        result = self.engine.run(contract, primary=primary, secondary=secondary)
        version = result.final_version
        return EngineResponse(version.response if version else "", result.decision, version.id if version else None)

    def handle_payload(self, payload: dict[str, object]) -> dict[str, str | None]:
        prompt = payload.get("prompt")
        if not isinstance(prompt, str):
            raise ValueError("prompt must be a string")
        raw_mode = payload.get("mode", Mode.BASIC.value)
        try:
            mode = Mode(raw_mode) if isinstance(raw_mode, str) else Mode.BASIC
        except ValueError as exc:
            raise ValueError(f"unsupported mode: {raw_mode}") from exc
        primary = _parse_model_selection(payload.get("primary_model")) or _parse_model_selection(payload.get("model"))
        secondary = _parse_model_selection(payload.get("secondary_model"))
        return self.handle(EngineRequest(prompt=prompt, mode=mode, primary_model=primary, secondary_model=secondary)).to_dict()


def create_default_service() -> EngineService:
    """Create the provider-configured runtime without leaking provider details into Engine."""
    primary_provider = os.environ.get("REVISE_PRIMARY_PROVIDER", "gemini").strip().lower()
    secondary_provider = os.environ.get("REVISE_SECONDARY_PROVIDER", "gemini").strip().lower()
    primary_model = os.environ.get("REVISE_PRIMARY_MODEL") or os.environ.get("GEMINI_PRIMARY_MODEL") or os.environ.get("GEMINI_MODEL") or "gemini-3.8-flash"
    secondary_model = os.environ.get("REVISE_SECONDARY_MODEL") or os.environ.get("GEMINI_SECONDARY_MODEL") or "gemini-3.5-flash-lite"

    primary_router = ModelRouter({provider: lambda model, provider=provider: build_primary(provider, model) for provider in ("gemini", "openai", "grok", "ollama")}, default=ModelSelection(primary_provider, primary_model))
    secondary_router = SecondaryRouter({provider: lambda model, provider=provider: build_secondary(provider, model) for provider in ("gemini", "openai", "grok", "ollama")}, default=ModelSelection(secondary_provider, secondary_model))
    return Engine(
        FunctionPrimary(lambda _contract, _context: ""),
        trace_sink=console_trace_sink,
    ) if False else EngineService(
        Engine(FunctionPrimary(lambda _contract, _context: ""), trace_sink=console_trace_sink),
        primary_router=primary_router,
        secondary_router=secondary_router,
    )


def _annotate_model(component: object | None, selection: ModelSelection | None) -> None:
    if component is None or selection is None:
        return
    try:
        setattr(component, "provider", selection.provider)
        setattr(component, "model", selection.model or "configured-default")
    except (AttributeError, TypeError):
        pass


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
    return ModelSelection(provider.strip(), model.strip() if model else None)
