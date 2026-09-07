from __future__ import annotations

from collections.abc import Mapping
from typing import Callable, Protocol

from .revise.models import DimensionResult, EvaluationProfile, Evidence, TaskContract

DimensionEvaluator = Callable[[TaskContract, str], DimensionResult]


class Primary(Protocol):
    """Generates a candidate response for a task."""

    def generate(self, contract: TaskContract, *, context: str | None = None) -> str:
        ...


class Secondary(Protocol):
    """Provides task-specific evaluator functions for a candidate response."""

    def evaluators(
        self,
        contract: TaskContract,
        profile: EvaluationProfile,
    ) -> Mapping[str, DimensionEvaluator]:
        ...


class Verifier(Protocol):
    """Runs deterministic or external checks and returns evidence."""

    def verify(
        self,
        contract: TaskContract,
        response: str,
        profile: EvaluationProfile,
    ) -> tuple[Evidence, ...]:
        ...


class FunctionPrimary:
    """Small adapter for a plain generation function."""

    def __init__(self, function: Callable[[TaskContract, str | None], str]) -> None:
        self._function = function

    def generate(self, contract: TaskContract, *, context: str | None = None) -> str:
        return self._function(contract, context)
