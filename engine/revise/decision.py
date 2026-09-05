from __future__ import annotations

from .models import Decision, EvaluationProfile, EvaluationResult, Severity, TaskContract


def decide(
    contract: TaskContract,
    profile: EvaluationProfile,
    result: EvaluationResult,
    *,
    revisions_used: int,
) -> EvaluationResult:
    if contract.missing_context:
        return _with_decision(result, Decision.ASK)

    material = [issue for issue in result.issues if issue.severity in {Severity.CRITICAL, Severity.MAJOR, Severity.MODERATE}]
    failed_required = any(
        name in result.dimensions and result.dimensions[name].status in {"fail", "partial"}
        for name in ("goal_alignment", "task_completion", "correctness", "instruction_following")
    )

    if material or failed_required:
        if revisions_used < profile.max_revisions:
            return _with_decision(result, Decision.REVISE)
        return _with_decision(result, Decision.ASK)

    return _with_decision(result, Decision.ACCEPT)


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
