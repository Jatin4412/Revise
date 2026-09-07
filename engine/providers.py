from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from .revise.models import DimensionResult, EvaluationProfile, TaskContract, Evidence


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
    ) -> Mapping[str, callable[[TaskContract, str], DimensionResult]]:
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

    def __init__(self, function):
        self._function = function

    def generate(self, contract: TaskContract, *, context: str | None = None) -> str:
        return self._function(contract, context)
