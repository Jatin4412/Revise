from __future__ import annotations

from dataclasses import dataclass

from .models import EvaluationResult, Issue, Severity


_EPSILON = 1e-9
_MATERIAL_SEVERITIES = {Severity.CRITICAL, Severity.MAJOR, Severity.MODERATE}
_SEVERITY_RANK = {
    Severity.INFORMATIONAL: 0,
    Severity.MINOR: 1,
    Severity.MODERATE: 2,
    Severity.MAJOR: 3,
    Severity.CRITICAL: 4,
}
_STATUS_RANK = {"unknown": 0, "partial": 1, "fail": 1, "pass": 2}


@dataclass(frozen=True)
class RevisionAssessment:
    """Comparison between a candidate revision and the immediately previous version."""

    baseline_score: float | None
    revised_score: float | None
    score_delta: float | None
    resolved_issues: tuple[str, ...] = ()
    introduced_issues: tuple[str, ...] = ()
    improved_dimensions: tuple[str, ...] = ()
    regressed_dimensions: tuple[str, ...] = ()
    net_improvement: float | None = None
    status: str = "unknown"
    downgraded_issues: tuple[str, ...] = ()
    escalated_issues: tuple[str, ...] = ()


def assess_revision(baseline: EvaluationResult | None, revised: EvaluationResult) -> RevisionAssessment | None:
    """Assess whether a revision materially improves or regresses on its baseline."""
    if baseline is None:
        return None

    baseline_score = baseline.overall_score
    revised_score = revised.overall_score
    score_delta = None if baseline_score is None or revised_score is None else revised_score - baseline_score

    baseline_issues = {_issue_key(issue): issue for issue in baseline.issues}
    revised_issues = {_issue_key(issue): issue for issue in revised.issues}
    resolved = tuple(sorted(set(baseline_issues) - set(revised_issues)))
    introduced = tuple(sorted(set(revised_issues) - set(baseline_issues)))

    downgraded: list[str] = []
    escalated: list[str] = []
    for key in sorted(set(baseline_issues) & set(revised_issues)):
        before = baseline_issues[key].severity
        after = revised_issues[key].severity
        if _SEVERITY_RANK[after] < _SEVERITY_RANK[before]:
            downgraded.append(key)
        elif _SEVERITY_RANK[after] > _SEVERITY_RANK[before]:
            escalated.append(key)

    improved: list[str] = []
    regressed: list[str] = []
    for name in set(baseline.dimensions) | set(revised.dimensions):
        before = baseline.dimensions.get(name)
        after = revised.dimensions.get(name)
        if before is None or after is None:
            continue
        if _dimension_improved(before, after):
            improved.append(name)
        elif _dimension_regressed(before, after):
            regressed.append(name)

    improved.sort()
    regressed.sort()

    net_improvement = score_delta
    material_introduced = any(revised_issues[key].severity in _MATERIAL_SEVERITIES for key in introduced)
    has_improvement = bool(
        resolved
        or downgraded
        or improved
        or (score_delta is not None and score_delta > _EPSILON)
    )
    has_regression = bool(
        escalated
        or regressed
        or material_introduced
        or (score_delta is not None and score_delta < -_EPSILON)
    )

    if has_regression:
        status = "regressed"
    elif has_improvement:
        status = "improved"
    else:
        status = "unchanged"

    return RevisionAssessment(
        baseline_score=baseline_score,
        revised_score=revised_score,
        score_delta=score_delta,
        resolved_issues=resolved,
        introduced_issues=introduced,
        improved_dimensions=tuple(improved),
        regressed_dimensions=tuple(regressed),
        net_improvement=net_improvement,
        status=status,
        downgraded_issues=tuple(downgraded),
        escalated_issues=tuple(escalated),
    )


def _issue_key(issue: Issue) -> str:
    """Identify the same issue across revisions without encoding its changing severity."""
    return f"{issue.type}|{issue.location or ''}|{issue.description.strip().lower()}"


def _dimension_improved(before, after) -> bool:
    if before.score is not None and after.score is not None and after.score > before.score + _EPSILON:
        return True
    return _STATUS_RANK.get(after.status, 0) > _STATUS_RANK.get(before.status, 0)


def _dimension_regressed(before, after) -> bool:
    if before.score is not None and after.score is not None and after.score < before.score - _EPSILON:
        return True
    return _STATUS_RANK.get(after.status, 0) < _STATUS_RANK.get(before.status, 0)
