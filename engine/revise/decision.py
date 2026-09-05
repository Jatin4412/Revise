from __future__ import annotations

from .models import Decision, EvaluationProfile, EvaluationResult, Issue, Severity, TaskContract


_HARD_FAILURES = {Severity.CRITICAL}
_REVISION_SEVERITIES = {Severity.CRITICAL, Severity.MAJOR, Severity.MODERATE}


def _has_hard_failure(result: EvaluationResult, profile: EvaluationProfile) -> bool:
    if not profile.hard_gates:
        return any(issue.severity in _HARD_FAILURES for issue in result.issues)

    # A critical issue always wins. Explicit hard-gate failures may be represented
    # by a dimension named in the profile with status != pass.
    if any(issue.severity in _HARD_FAILURES for issue in result.issues):
        return True
    for gate in profile.hard_gates:
        dimension = result.dimensions.get(gate)
        if dimension is not None and dimension.status != "pass":
            return True
    return False


def _has_material_unknown(contract: TaskContract, result: EvaluationResult) -> bool:
    if contract.missing_context:
        return True
    return any(d.status == "unknown" and (d.confidence < 0.8) for d in result.dimensions.values())


def decide(
    contract: TaskContract,
    profile: EvaluationProfile,
    result: EvaluationResult,
    *,
    revisions_used: int = 0,
) -> EvaluationResult:
    """Apply policy ordering to an evaluation result.

    This function deliberately does not calculate a weighted quality score. Hard
    gates, missing information, task completion, and correctness take precedence
    over softer communication signals.
    """
    if _has_hard_failure(result, profile):
        return EvaluationResult(
            decision=Decision.REVISE if revisions_used < profile.max_revisions else Decision.ASK,
            overall_score=result.overall_score,
            confidence=result.confidence,
            dimensions=result.dimensions,
            issues=result.issues,
            evidence=result.evidence,
            revision=result.revision,
            verification=result.verification,
        )

    if _has_material_unknown(contract, result):
        return EvaluationResult(
            decision=Decision.ASK,
            overall_score=result.overall_score,
            confidence=result.confidence,
            dimensions=result.dimensions,
            issues=result.issues,
            evidence=result.evidence,
            revision=result.revision,
            verification=result.verification,
        )

    completion = result.dimensions.get("task_completion")
    correctness = result.dimensions.get("correctness")
    instruction = result.dimensions.get("instruction_following")

    material_failure = any(
        dimension is not None and dimension.status == "fail"
        for dimension in (completion, correctness, instruction)
    )
    material_issue = any(issue.severity in _REVISION_SEVERITIES for issue in result.issues)

    if (material_failure or material_issue) and revisions_used < profile.max_revisions:
        decision = Decision.REVISE
    elif material_failure or material_issue:
        decision = Decision.ACCEPT if not material_failure else Decision.ASK
    else:
        decision = Decision.ACCEPT

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
