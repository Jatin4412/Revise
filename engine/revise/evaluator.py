from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Callable

from .evidence import fuse_evidence
from .models import Decision, DimensionResult, EvaluationProfile, EvaluationResult, Evidence, Issue, Severity, TaskContract

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
        valid_score = score is None or (not isinstance(score, bool) and isinstance(score, (int, float)) and math.isfinite(score) and 0 <= score <= 1)
        valid_confidence = not isinstance(confidence, bool) and isinstance(confidence, (int, float)) and math.isfinite(confidence) and 0 <= confidence <= 1
        if status != dimension.status or not valid_score or not valid_confidence:
            dimensions[name] = DimensionResult(None, 0.0, "unknown", "malformed dimension score, confidence, or status")
            malformed = True
        else:
            dimensions[name] = dimension
    if any(name not in profile.dimensions for name in result.dimensions):
        malformed = True
        issues.append(Issue("malformed_evaluation", Severity.MAJOR, "evaluator returned an unexpected dimension"))
    overall = result.overall_score
    confidence = result.confidence
    valid_overall = overall is None or (not isinstance(overall, bool) and isinstance(overall, (int, float)) and math.isfinite(overall) and 0 <= overall <= 1)
    valid_confidence = not isinstance(confidence, bool) and isinstance(confidence, (int, float)) and math.isfinite(confidence) and 0 <= confidence <= 1
    if not valid_overall:
        overall = None
        malformed = True
    if not valid_confidence:
        confidence = 0.0
        malformed = True
    if malformed:
        issues.append(Issue("malformed_evaluation", Severity.MAJOR, "evaluator output failed schema validation and was converted to a fail-closed unknown state"))
        return EvaluationResult(Decision.ASK, overall, confidence, dimensions, tuple(issues), result.evidence, result.revision, result.verification)
    return EvaluationResult(result.decision, overall, confidence, dimensions, tuple(issues), result.evidence, result.revision, result.verification)


def _build_result(profile: EvaluationProfile, dimensions: dict[str, DimensionResult], evidence: tuple[Evidence, ...]) -> EvaluationResult:
    known = [d for d in dimensions.values() if d.status != "unknown"]
    weighted = [(name, dimensions[name]) for name in profile.dimensions if name in dimensions and dimensions[name].status != "unknown" and dimensions[name].score is not None]
    total_weight = sum(max(0.0, profile.dimension_weights.get(name, 1.0)) for name, _ in weighted)
    overall_score = (sum(float(d.score) * max(0.0, profile.dimension_weights.get(name, 1.0)) for name, d in weighted) / total_weight) if total_weight else None
    confidence = sum(d.confidence for d in known) / len(known) if known else 0.0
    return EvaluationResult(Decision.ACCEPT, overall_score, confidence, dimensions, evidence=evidence)
