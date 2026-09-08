from __future__ import annotations

from .models import Decision, EvaluationProfile, EvaluationResult, Evidence, Severity, TaskContract
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

    material = [issue for issue in result.issues if issue.severity in {Severity.CRITICAL, Severity.MAJOR, Severity.MODERATE}]
    if material:
        return _next_action(result, profile, revisions_used)

    # Explicit hard-gate policy outranks model severity and quality scores.
    if any(issue.type in profile.hard_gates for issue in result.issues):
        return _next_action(result, profile, revisions_used)

    if any(e.method == "deterministic" and e.result == "fail" for e in result.evidence):
        return _next_action(result, profile, revisions_used)
    if any(e.method == "external" and e.result == "fail" for e in result.evidence):
        return _next_action(result, profile, revisions_used)

    # Every configured evidence requirement must have a passing evidence item.
    unmet = [requirement for requirement in profile.evidence_requirements if not _evidence_requirement_met(requirement, result.evidence)]
    if unmet:
        return _next_action(result, profile, revisions_used)

    if revision_assessment is not None and revision_assessment.status == "regressed":
        return _next_action(result, profile, revisions_used)
    if revision_assessment is not None and revision_assessment.status == "unchanged":
        return _next_action(result, profile, revisions_used)

    if any(d.status == "unknown" for d in result.dimensions.values()):
        return _with_decision(result, Decision.ASK)
    if any(d.status in {"fail", "partial"} for d in result.dimensions.values()):
        return _next_action(result, profile, revisions_used)

    for name in profile.required_dimensions:
        dimension = result.dimensions.get(name)
        if dimension is None or dimension.score is None:
            return _with_decision(result, Decision.ASK)
        if dimension.score < profile.minimum_scores.get(name, 0.70):
            return _next_action(result, profile, revisions_used)

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


def _evidence_requirement_met(requirement: str, evidence: tuple[Evidence, ...]) -> bool:
    target = requirement.strip().lower()
    if not target:
        return False
    for item in evidence:
        if item.result != "pass":
            continue
        haystack = " ".join((item.source, item.method, *item.provenance)).lower()
        if target == item.method.lower() or target == item.source.lower() or target in haystack:
            return True
    return False


def _next_action(result: EvaluationResult, profile: EvaluationProfile, revisions_used: int) -> EvaluationResult:
    if revisions_used < profile.max_revisions:
        return _with_decision(result, Decision.REVISE)
    return _with_decision(result, Decision.ASK)


def _with_decision(result: EvaluationResult, decision: Decision) -> EvaluationResult:
    return EvaluationResult(decision, result.overall_score, result.confidence, result.dimensions, result.issues, result.evidence, result.revision, result.verification)
