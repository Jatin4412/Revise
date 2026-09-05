from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from revise.decision import decide
from revise.evidence import fuse_evidence
from revise.models import (
    Decision,
    DimensionResult,
    EvaluationProfile,
    EvaluationResult,
    Evidence,
    TaskContract,
    Version,
)
from revise.profile import build_profile


Primary = Callable[[TaskContract, str | None], str]
DimensionEvaluator = Callable[[TaskContract, str], DimensionResult]


@dataclass(frozen=True)
class EngineResult:
    decision: Decision
    final_version: Version | None
    versions: tuple[Version, ...]
    task_contract: TaskContract
    evaluation_profile: EvaluationProfile


class Engine:
    """Provider-agnostic control loop for Primary generation and Secondary evaluation."""

    def __init__(
        self,
        primary: Primary,
        *,
        evaluators: dict[str, DimensionEvaluator] | None = None,
    ) -> None:
        self.primary = primary
        self.evaluators = evaluators or {}

    def run(
        self,
        contract: TaskContract,
        *,
        profile: EvaluationProfile | None = None,
        initial_context: str | None = None,
        evidence: Iterable[Evidence] = (),
    ) -> EngineResult:
        profile = profile or build_profile(contract)
        versions: list[Version] = []
        previous: Version | None = None
        revisions_used = 0

        while True:
            response = self.primary(contract, initial_context if previous is None else previous.response)
            version = Version(
                id=f"v{len(versions)}",
                response=response,
                parent_id=previous.id if previous else None,
            )

            result = self._evaluate(
                contract,
                response,
                profile,
                evidence=evidence,
                revisions_used=revisions_used,
            )
            version = Version(
                id=version.id,
                response=version.response,
                evaluation=result,
                parent_id=version.parent_id,
            )
            versions.append(version)

            if result.decision is Decision.ACCEPT:
                best = self._best_valid_version(versions)
                return EngineResult(Decision.ACCEPT, best, tuple(versions), contract, profile)

            if result.decision is Decision.ASK:
                best = self._best_valid_version(versions)
                return EngineResult(Decision.ASK, best, tuple(versions), contract, profile)

            if revisions_used >= profile.max_revisions:
                best = self._best_valid_version(versions)
                return EngineResult(Decision.REVISE, best, tuple(versions), contract, profile)

            previous = version
            revisions_used += 1

    def _evaluate(
        self,
        contract: TaskContract,
        response: str,
        profile: EvaluationProfile,
        *,
        evidence: Iterable[Evidence],
        revisions_used: int,
    ) -> EvaluationResult:
        dimensions: dict[str, DimensionResult] = {}
        for name in profile.dimensions:
            evaluator = self.evaluators.get(name)
            if evaluator is None:
                dimensions[name] = DimensionResult(None, 0.0, "unknown", "no evaluator registered")
            else:
                dimensions[name] = evaluator(contract, response)

        fused = fuse_evidence(evidence)
        scores = [d.score for d in dimensions.values() if d.score is not None and d.status != "unknown"]
        confidence = (
            sum(d.confidence for d in dimensions.values() if d.status != "unknown")
            / len([d for d in dimensions.values() if d.status != "unknown"])
            if any(d.status != "unknown" for d in dimensions.values())
            else fused.confidence
        )
        provisional = EvaluationResult(
            decision=Decision.ACCEPT,
            overall_score=sum(scores) / len(scores) if scores else None,
            confidence=confidence,
            dimensions=dimensions,
            evidence=fused.evidence,
        )
        return decide(contract, profile, provisional, revisions_used=revisions_used)

    @staticmethod
    def _best_valid_version(versions: list[Version]) -> Version | None:
        valid = [v for v in versions if v.evaluation and v.evaluation.decision is Decision.ACCEPT]
        if valid:
            return max(valid, key=lambda v: (v.evaluation.overall_score or 0.0, v.evaluation.confidence))
        evaluated = [v for v in versions if v.evaluation]
        return max(evaluated, key=lambda v: (v.evaluation.overall_score or 0.0, v.evaluation.confidence), default=None)
