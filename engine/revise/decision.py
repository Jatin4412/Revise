from __future__ import annotations

from .models import Decision, EvaluationProfile, EvaluationResult, Severity, TaskContract
from .revision import RevisionAssessment


def decide(
    contract: TaskContract,
    profile: EvaluationProfile,
    result: EvaluationResult,
    *,
    revisions_used: int,
    revision_assessment: RevisionAssessment | None = None,
) -> EvaluationResult:
    if contract.missing_context:
        return _with_decision(result, Decision.ASK)

    # Safety/security/critical failures remain hard stops. Model confidence cannot override them.
    material = [
        issue
        for issue in result.issues
        if issue.severity in {Severity.CRITICAL, Severity.MAJOR, Severity.MODERATE}
    ]
    if material:
        return _next_action(result, profile, revisions_used)

    # Direct deterministic failures outrank model evaluation. A model PASS cannot
    # override a deterministic verifier that proves the candidate is invalid.
    if any(e.method == "deterministic" and e.result == "fail" for e in result.evidence):
        return _next_action(result, profile, revisions_used)

    # Required external source checks also outrank model acceptance. A source
    # verification failure means the candidate cannot claim a verified citation.
    if any(e.method == "external" and e.result == "fail" for e in result.evidence):
        return _next_action(result, profile, revisions_used)

    # A revision must earn its place. Regressions are never accepted merely because
    # the candidate clears the absolute quality thresholds.
    if revision_assessment is not None and revision_assessment.status == "regressed":
        return _next_action(result, profile, revisions_used)
    if revision_assessment is not None and revision_assessment.status == "unchanged":
        return _next_action(result, profile, revisions_used)

    # Unknown evaluation is never treated as success.
    if any(d.status == "unknown" for d in result.dimensions.values()):
        return _with_decision(result, Decision.ASK)

    # Any partial/failing dimension needs another pass. This prevents a high average
    # score from hiding a meaningful weakness.
    if any(d.status in {"fail", "partial"} for d in result.dimensions.values()):
        return _next_action(result, profile, revisions_used)

    # Required dimensions have individual floors in addition to the overall score.
    for name in profile.required_dimensions:
        dimension = result.dimensions.get(name)
        if dimension is None or dimension.score is None:
            return _with_decision(result, Decision.ASK)
        minimum = profile.minimum_scores.get(name, 0.70)
        if dimension.score < minimum:
            return _next_action(result, profile, revisions_used)

    # Optional dimensions can also block acceptance when their configured floor is missed.
    for name, minimum in profile.minimum_scores.items():
        dimension = result.dimensions.get(name)
        if dimension is not None and dimension.score is not None and dimension.score < minimum:
            return _next_action(result, profile, revisions_used)

    if result.confidence < profile.minimum_confidence:
        return _with_decision(result, Decision.ASK)

    if result.overall_score is None:
        return _with_decision(result, Decision.ASK)
    if result.overall_score < profile.minimum_overall_score:
        return _next_action(result, profile, revisions_used)

    return _with_decision(result, Decision.ACCEPT)


def _next_action(result: EvaluationResult, profile: EvaluationProfile, revisions_used: int) -> EvaluationResult:
    if revisions_used < profile.max_revisions:
        return _with_decision(result, Decision.REVISE)
    return _with_decision(result, Decision.ASK)


def _with_decision(result: EvaluationResult, decision: Decision) -> EvaluationResult:
    return EvaluationResult(
        decision=decision,
        overall_score=result.overall_score,
        confidence=result.confidence,
        dimensions=result.dimensions,
        issues=result.issues,
        evidence=result.evidence,
        revision=result.revision,
        verification=result.verification,
    )
