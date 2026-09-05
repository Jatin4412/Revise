from __future__ import annotations

from dataclasses import replace
from typing import Callable, Iterable

from .decision import decide
from .evidence import fuse_evidence
from .models import (
    Decision,
    DimensionResult,
    EvaluationProfile,
    EvaluationResult,
    Evidence,
    Issue,
    Severity,
    TaskContract,
    VerificationPlan,
)
from .profile import build_profile


DimensionEvaluator = Callable[[TaskContract, str], DimensionResult]


def _baseline_dimension(status: str, score: float, confidence: float, reason: str) -> DimensionResult:
    return DimensionResult(score=max(0.0, min(1.0, score)), confidence=max(0.0, min(1.0, confidence)), status=status, reason=reason)


def evaluate(
    contract: TaskContract,
    response: str,
    *,
    profile: EvaluationProfile | None = None,
    evaluators: dict[str, DimensionEvaluator] | None = None,
    evidence: Iterable[Evidence] = (),
    revisions_used: int = 0,
) -> EvaluationResult:
    """Run the evaluator pipeline around supplied dimension evaluators.

    The secondary LLM is intentionally injected through ``evaluators`` rather than
    hard-coded. This keeps the core independent of a provider and lets deterministic
    or external verifiers contribute evidence separately.
    """
    profile = profile or build_profile(contract)
    evaluators = evaluators or {}
    dimensions: dict[str, DimensionResult] = {}
    issues: list[Issue] = []

    for name in profile.dimensions:
        evaluator = evaluators.get(name)
        if evaluator is None:
            # Unimplemented judges remain explicit unknowns instead of silently passing.
            dimensions[name] = _baseline_dimension("unknown", None if False else 0.0, 0.0, "no evaluator registered")
            continue
        result = evaluator(contract, response)
        dimensions[name] = result

    fused = fuse_evidence(evidence)
    required_failures = [
        name for name in ("task_completion", "correctness", "instruction_following")
        if name in dimensions and dimensions[name].status == "fail"
    ]
    for name in required_failures:
        issues.append(
            Issue(
                type="evaluation_failure",
                severity=Severity.MAJOR,
                description=f"Required dimension failed: {name}",
            )
        )

    scores = [d.score for d in dimensions.values() if d.score is not None and d.status != "unknown"]
    overall = sum(scores) / len(scores) if scores else None
    confidence_values = [d.confidence for d in dimensions.values() if d.status != "unknown"]
    confidence = sum(confidence_values) / len(confidence_values) if confidence_values else fused.confidence

    provisional = EvaluationResult(
        decision=Decision.ACCEPT,
        overall_score=overall,
        confidence=confidence,
        dimensions=dimensions,
        issues=tuple(issues),
        evidence=fused.evidence,
        verification=VerificationPlan(
            required=bool(profile.deterministic_checks or profile.external_verification),
            method=(profile.deterministic_checks[0] if profile.deterministic_checks else (profile.external_verification[0] if profile.external_verification else None)),
        ),
    )
    return decide(contract, profile, provisional, revisions_used=revisions_used)
