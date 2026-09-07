from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from .providers import Primary


@dataclass(frozen=True)
class ModelSelection:
    """User/system selection of a model provider and optional concrete model."""

    provider: str
    model: str | None = None


PrimaryFactory = Callable[[str | None], Primary]


class ModelRouter:
    """Resolve a model selection into the Primary implementation that serves it."""

    def __init__(
        self,
        providers: Mapping[str, PrimaryFactory],
        *,
        default: ModelSelection | None = None,
    ) -> None:
        self._providers = dict(providers)
        self.default = default

    def resolve(self, selection: ModelSelection | None = None) -> Primary:
        selected = selection or self.default
        if selected is None:
            raise ValueError("a model selection is required")

        factory = self._providers.get(selected.provider)
        if factory is None:
            available = ", ".join(sorted(self._providers)) or "none"
            raise ValueError(
                f"unsupported model provider: {selected.provider}; available: {available}"
            )
        return factory(selected.model)

    def available_providers(self) -> tuple[str, ...]:
        return tuple(sorted(self._providers))
