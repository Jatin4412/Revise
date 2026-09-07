from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from .providers import Primary, Secondary


@dataclass(frozen=True)
class ModelSelection:
    """Runtime selection of a provider and optional concrete model."""

    provider: str
    model: str | None = None


PrimaryFactory = Callable[[str | None], Primary]
SecondaryFactory = Callable[[str | None], Secondary]


class ModelRouter:
    """Resolve runtime model selections into provider adapters for one role."""

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


class SecondaryRouter:
    """Resolve runtime model selections into provider adapters for Secondary."""

    def __init__(
        self,
        providers: Mapping[str, SecondaryFactory],
        *,
        default: ModelSelection | None = None,
    ) -> None:
        self._providers = dict(providers)
        self.default = default

    def resolve(self, selection: ModelSelection | None = None) -> Secondary:
        selected = selection or self.default
        if selected is None:
            raise ValueError("a secondary model selection is required")
        factory = self._providers.get(selected.provider)
        if factory is None:
            available = ", ".join(sorted(self._providers)) or "none"
            raise ValueError(
                f"unsupported secondary model provider: {selected.provider}; available: {available}"
            )
        return factory(selected.model)

    def available_providers(self) -> tuple[str, ...]:
        return tuple(sorted(self._providers))
