from __future__ import annotations

from typing import Callable, Iterable

from .evidence import fuse_evidence
from .models import DimensionResult, EvaluationProfile, EvaluationResult, Evidence, TaskContract

DimensionEvaluator = Callable[[TaskContract, str], DimensionResult]


def evaluate(
    contract: TaskContract,
    response: str,
    profile: EvaluationProfile,
    evaluators: dict[str, DimensionEvaluator],
    *,
    evidence: Iterable[Evidence] = (),
) -> EvaluationResult:
    dimensions: dict[str, DimensionResult] = {}
    for name in profile.dimensions:
        evaluator = evaluators.get(name)
        dimensions[name] = (
            DimensionResult(None, 0.0, "unknown", "no evaluator registered")
            if evaluator is None
            else evaluator(contract, response)
        )

    fused = fuse_evidence(evidence)
    known = [d for d in dimensions.values() if d.status != "unknown"]
    scores = [d.score for d in known if d.score is not None]
    confidence = sum(d.confidence for d in known) / len(known) if known else fused.confidence

    return EvaluationResult(
        decision=__import__("engine.revise.models", fromlist=["Decision"]).Decision.ACCEPT,
        overall_score=sum(scores) / len(scores) if scores else None,
        confidence=confidence,
        dimensions=dimensions,
        evidence=fused.evidence,
    )
