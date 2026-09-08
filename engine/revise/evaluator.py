from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Callable

from .evidence import fuse_evidence
from .models import Decision, DimensionResult, EvaluationProfile, EvaluationResult, Evidence, Severity, TaskContract

DimensionEvaluator = Callable[[TaskContract, str], DimensionResult]
_VALID_STATUSES = {"pass", "partial", "fail", "unknown"}


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
    return _build_result(profile, dimensions, fused.evidence)


def validate_evaluation_result(result: EvaluationResult, profile: EvaluationProfile) -> EvaluationResult:
    """Fail closed on malformed evaluator output without allowing it to pass."""
    dimensions: dict[str, DimensionResult] = {}
    issues = list(result.issues)
    malformed = False
    for name in profile.dimensions:
        dimension = result.dimensions.get(name)
        if dimension is None:
            dimensions[name] = DimensionResult(None, 0.0, "unknown", "dimension missing from evaluator result")
            malformed = True
            continue
        if not isinstance(dimension, DimensionResult):
            dimensions[name] = DimensionResult(None, 0.0, "unknown", "malformed dimension result")
            malformed = True
            continue
        status = dimension.status if dimension.status in _VALID_STATUSES else "unknown"
        score = dimension.score
        confidence = dimension.confidence
        if status != dimension.status or (score is not None and (isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score) or not 0 <= score <= 1)) or isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
            dimensions[name] = DimensionResult(None, 0.0, "unknown", "malformed dimension score, confidence, or status")
            malformed = True
        else:
            dimensions[name] = dimension
    if any(name not in profile.dimensions for name in result.dimensions):
        malformed = True
        issues.append(__import__("engine.revise.models", fromlist=["Issue"]).Issue("malformed_evaluation", Severity.MAJOR, "evaluator returned an unexpected dimension"))
    overall = result.overall_score
    confidence = result.confidence
    if isinstance(overall, bool) or (overall is not None and (not isinstance(overall, (int, float)) or not math.isfinite(overall) or not 0 <= overall <= 1)):
        overall = None
        malformed = True
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
        confidence = 0.0
        malformed = True
    if malformed:
        issues.append(__import__("engine.revise.models", fromlist=["Issue"]).Issue("malformed_evaluation", Severity.MAJOR, "evaluator output failed schema validation and was converted to fail-closed unknown state"))
        return EvaluationResult(Decision.ASK, overall, confidence, dimensions, tuple(issues), result.evidence, result.revision, result.verification)
    return EvaluationResult(result.decision, overall, confidence, dimensions, tuple(issues), result.evidence, result.revision, result.verification)


def _build_result(profile: EvaluationProfile, dimensions: dict[str, DimensionResult], evidence: tuple[Evidence, ...]) -> EvaluationResult:
    known = [d for d in dimensions.values() if d.status != "unknown"]
    weighted = [(name, dimensions[name]) for name in profile.dimensions if name in dimensions and dimensions[name].status != "unknown" and dimensions[name].score is not None]
    total_weight = sum(max(0.0, profile.dimension_weights.get(name, 1.0)) for name, _ in weighted)
    overall_score = (sum(float(d.score) * max(0.0, profile.dimension_weights.get(name, 1.0)) for name, d in weighted) / total_weight) if total_weight else None
    confidence = sum(d.confidence for d in known) / len(known) if known else 0.0
    return EvaluationResult(Decision.ACCEPT, overall_score, confidence, dimensions, evidence=evidence)
