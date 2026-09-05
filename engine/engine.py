from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from .revise.decision import decide
from .revise.evidence import fuse_evidence
from .revise.models import Decision, DimensionResult, EvaluationProfile, EvaluationResult, Evidence, TaskContract, Version
from .revise.profile import build_profile

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
    """Provider-agnostic control loop for Primary generation and evaluation."""

    def __init__(self, primary: Primary, *, evaluators: dict[str, DimensionEvaluator] | None = None) -> None:
        self.primary = primary
        self.evaluators = evaluators or {}

    def run(self, contract: TaskContract, *, profile: EvaluationProfile | None = None, initial_context: str | None = None, evidence: Iterable[Evidence] = ()) -> EngineResult:
        profile = profile or build_profile(contract)
        versions: list[Version] = []
        previous: Version | None = None

        for revision_index in range(profile.max_revisions + 1):
            response = self.primary(contract, initial_context if previous is None else previous.response)
            version = Version(f"v{len(versions)}", response, parent_id=previous.id if previous else None)
            evaluation = self._evaluate(contract, response, profile, evidence=evidence, revisions_used=revision_index)
            version = Version(version.id, version.response, evaluation, version.parent_id)
            versions.append(version)

            if evaluation.decision in (Decision.ACCEPT, Decision.ASK):
                return EngineResult(evaluation.decision, self._best_version(versions), tuple(versions), contract, profile)
            previous = version

        return EngineResult(Decision.REVISE, self._best_version(versions), tuple(versions), contract, profile)

    def _evaluate(self, contract: TaskContract, response: str, profile: EvaluationProfile, *, evidence: Iterable[Evidence], revisions_used: int) -> EvaluationResult:
        dimensions = {
            name: self.evaluators[name](contract, response) if name in self.evaluators else DimensionResult(None, 0.0, "unknown", "no evaluator registered")
            for name in profile.dimensions
        }
        fused = fuse_evidence(evidence)
        known = [d for d in dimensions.values() if d.status != "unknown"]
        scores = [d.score for d in known if d.score is not None]
        confidence = sum(d.confidence for d in known) / len(known) if known else fused.confidence
        provisional = EvaluationResult(Decision.ACCEPT, sum(scores) / len(scores) if scores else None, confidence, dimensions, evidence=fused.evidence)
        return decide(contract, profile, provisional, revisions_used=revisions_used)

    @staticmethod
    def _best_version(versions: list[Version]) -> Version | None:
        accepted = [v for v in versions if v.evaluation and v.evaluation.decision is Decision.ACCEPT]
        candidates = accepted or [v for v in versions if v.evaluation]
        return max(candidates, key=lambda v: (v.evaluation.overall_score or 0.0, v.evaluation.confidence), default=None)
