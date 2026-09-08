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

    def resolve(self, selection: ModelSelection | None = None) -> ModelSelection:
        """Validate and return the selected runtime model descriptor.

        Adapters can be resolved separately by service/runtime code; the router's
        core contract remains a model selection, not a provider-specific adapter.
        """
        selected = selection or self.default
        if selected is None:
            raise ValueError("a model selection is required")
        if selected.provider not in self._providers:
            available = ", ".join(sorted(self._providers)) or "none"
            raise ValueError(
                f"unsupported model provider: {selected.provider}; available: {available}"
            )
        return selected

    def adapter(self, selection: ModelSelection | None = None) -> Primary:
        selected = self.resolve(selection)
        return self._providers[selected.provider](selected.model)

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

    def resolve(self, selection: ModelSelection | None = None) -> ModelSelection:
        selected = selection or self.default
        if selected is None:
            raise ValueError("a secondary model selection is required")
        if selected.provider not in self._providers:
            available = ", ".join(sorted(self._providers)) or "none"
            raise ValueError(
                f"unsupported secondary model provider: {selected.provider}; available: {available}"
            )
        return selected

    def adapter(self, selection: ModelSelection | None = None) -> Secondary:
        selected = self.resolve(selection)
        return self._providers[selected.provider](selected.model)

    def available_providers(self) -> tuple[str, ...]:
        return tuple(sorted(self._providers))
