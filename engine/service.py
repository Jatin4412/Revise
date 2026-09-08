from __future__ import annotations

import os
from dataclasses import dataclass

from .contracts import make_contract
from .engine import Engine, EngineResult
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
        result = self._run(request)
        return self._response(result)

    def handle_payload(self, payload: dict[str, object]) -> dict[str, str | None]:
        return self.handle(self._parse_request(payload)).to_dict()

    def handle_trace_payload(self, payload: dict[str, object]) -> dict[str, object]:
        """Return the normal result plus safe development trace metadata.

        This is intentionally additive to the stable /v1/engine response. Trace events
        contain execution state only; prompts, generated responses, credentials, and
        other payload contents remain excluded by ExecutionTrace.
        """
        result = self._run(self._parse_request(payload))
        response = self._response(result).to_dict()
        response["trace"] = [
            {
                "timestamp": event.timestamp,
                "stage": event.stage,
                "status": event.status,
                "details": dict(event.details),
            }
            for event in result.trace
        ]
        return response

    def _run(self, request: EngineRequest) -> EngineResult:
        prompt = request.prompt.strip()
        if not prompt:
            raise ValueError("prompt must not be empty")
        contract = make_contract(prompt, mode=request.mode)

        # The service supports two valid execution modes:
        # 1. router-backed runtime selection (production HTTP path), and
        # 2. direct engine injection (unit tests/custom embeddings).
        # Do not impose concrete Engine attributes on arbitrary engine doubles.
        if self.primary_router is not None:
            primary_selection = request.primary_model or request.model or self.primary_router.default
            primary = self.primary_router.resolve(primary_selection)
        else:
            primary_selection = request.primary_model or request.model
            primary = getattr(self.engine, "primary", None)

        if self.secondary_router is not None:
            secondary_selection = request.secondary_model or self.secondary_router.default
            secondary = self.secondary_router.resolve(secondary_selection)
        else:
            secondary_selection = request.secondary_model
            secondary = getattr(self.engine, "secondary", None)

        _annotate_model(primary, primary_selection)
        _annotate_model(secondary, secondary_selection)

        # A real Engine can be injected without exposing its internal model objects
        # as an API requirement. Lightweight fakes may consume these arguments
        # themselves, so only reject an absent Primary when the concrete engine does.
        if primary is None and isinstance(self.engine, Engine):
            raise ValueError("no primary model is configured")
        return self.engine.run(contract, primary=primary, secondary=secondary)

    @staticmethod
    def _response(result: EngineResult) -> EngineResponse:
        version = result.final_version
        return EngineResponse(version.response if version else "", result.decision, version.id if version else None)

    @staticmethod
    def _parse_request(payload: dict[str, object]) -> EngineRequest:
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
        return EngineRequest(prompt=prompt, mode=mode, primary_model=primary, secondary_model=secondary)


def create_default_service() -> EngineService:
    """Create the provider-configured runtime without leaking provider details into Engine."""
    primary_provider = os.environ.get("REVISE_PRIMARY_PROVIDER", "gemini").strip().lower()
    secondary_provider = os.environ.get("REVISE_SECONDARY_PROVIDER", "gemini").strip().lower()
    primary_model = os.environ.get("REVISE_PRIMARY_MODEL") or os.environ.get("GEMINI_PRIMARY_MODEL") or os.environ.get("GEMINI_MODEL") or "gemini-3.7-flash"
    secondary_model = os.environ.get("REVISE_SECONDARY_MODEL") or os.environ.get("GEMINI_SECONDARY_MODEL") or "gemini-3.1-flash-lite"

    providers = ("gemini", "groq", "openrouter", "openai", "grok")
    primary_router = ModelRouter({provider: lambda model, provider=provider: build_primary(provider, model) for provider in providers}, default=ModelSelection(primary_provider, primary_model))
    secondary_router = SecondaryRouter({provider: lambda model, provider=provider: build_secondary(provider, model) for provider in providers}, default=ModelSelection(secondary_provider, secondary_model))
    return EngineService(
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
