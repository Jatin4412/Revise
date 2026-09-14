from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from .models import Decision, EvaluationResult, EvaluationProfile, Severity, TaskContract
from .revision import RevisionAssessment


class CorrectionRecommendation(str, Enum):
    """Advisory correction classes; these never authorize a Decision."""

    REVISE = "revise"
    VERIFY = "verify"
    CHANGE_APPROACH = "change_approach"
    ASK = "ask"
    ACCEPT_CANDIDATE = "accept_candidate"


@dataclass(frozen=True)
class Diagnosis:
    """Provider-neutral, advisory explanation of why an attempt likely failed."""

    status: str
    summary: str
    failure_categories: tuple[str, ...] = ()
    confidence: float = 0.0
    recommended_correction: CorrectionRecommendation = CorrectionRecommendation.REVISE
    affected_dimensions: tuple[str, ...] = ()
    affected_issues: tuple[str, ...] = ()
    evidence_basis: tuple[str, ...] = ()


class Diagnoser(Protocol):
    """Optional provider-neutral source of advisory diagnoses."""

    def diagnose(
        self,
        contract: TaskContract,
        result: EvaluationResult,
        profile: EvaluationProfile,
        revision_assessment: RevisionAssessment | None = None,
    ) -> Diagnosis:
        ...


_VALID_STATUSES = {"actionable", "uncertain"}
_MIN_CONFIDENCE = 0.60


def validate_diagnosis(
    diagnosis: Diagnosis,
    *,
    minimum_confidence: float = _MIN_CONFIDENCE,
) -> Diagnosis | None:
    """Validate advisory diagnosis data and fail closed when it is unreliable."""
    if not isinstance(diagnosis, Diagnosis):
        return None
    if diagnosis.status not in _VALID_STATUSES:
        return None
    if not isinstance(diagnosis.summary, str) or not diagnosis.summary.strip():
        return None
    if not isinstance(diagnosis.recommended_correction, CorrectionRecommendation):
        return None
    if (
        isinstance(diagnosis.confidence, bool)
        or not isinstance(diagnosis.confidence, (int, float))
        or not math.isfinite(diagnosis.confidence)
        or not 0 <= diagnosis.confidence <= 1
    ):
        return None
    if (
        isinstance(minimum_confidence, bool)
        or not isinstance(minimum_confidence, (int, float))
        or not math.isfinite(minimum_confidence)
        or not 0 <= minimum_confidence <= 1
    ):
        return None
    if diagnosis.confidence < minimum_confidence:
        return None
    for values in (
        diagnosis.failure_categories,
        diagnosis.affected_dimensions,
        diagnosis.affected_issues,
        diagnosis.evidence_basis,
    ):
        if not isinstance(values, tuple) or any(not isinstance(value, str) or not value.strip() for value in values):
            return None
    return diagnosis


def _evidence_label(evidence: object) -> str:
    """Return a stable string label for evidence provenance in diagnosis metadata."""
    provenance = getattr(evidence, "provenance", ())
    if provenance:
        return "/".join(str(item) for item in provenance)
    return "/".join(str(item) for item in (getattr(evidence, "source", ""), getattr(evidence, "method", "")))


def infer_diagnosis(
    contract: TaskContract,
    result: EvaluationResult,
    profile: EvaluationProfile,
    *,
    revision_assessment: RevisionAssessment | None = None,
    previous_recommendation: CorrectionRecommendation | None = None,
) -> Diagnosis:
    """Produce a conservative built-in diagnosis from authoritative observations.

    This is intentionally heuristic and advisory. It never changes the Decision
    and cannot turn a failed candidate into an accepted one.
    """
    if contract.missing_context:
        return Diagnosis(
            "actionable",
            "Required task context is missing.",
            ("missing_context",),
            0.98,
            CorrectionRecommendation.ASK,
            evidence_basis=("task_contract",),
        )

    hard_gate_issues = tuple(issue for issue in result.issues if issue.type in profile.hard_gates)
    deterministic_failures = tuple(e for e in result.evidence if e.method == "deterministic" and e.result == "fail")
    external_failures = tuple(e for e in result.evidence if e.method == "external" and e.result == "fail")

    if hard_gate_issues:
        return Diagnosis(
            "actionable",
            "An authoritative hard-gate failure requires correction.",
            ("hard_gate",),
            0.98,
            CorrectionRecommendation.CHANGE_APPROACH,
            affected_issues=tuple(issue.type for issue in hard_gate_issues),
            evidence_basis=("hard_gate",),
        )

    if deterministic_failures:
        return Diagnosis(
            "actionable",
            "Deterministic verification failed; the next attempt must independently satisfy the verifier.",
            ("deterministic_verification",),
            0.98,
            CorrectionRecommendation.CHANGE_APPROACH,
            evidence_basis=tuple(_evidence_label(e) for e in deterministic_failures),
        )

    if external_failures:
        return Diagnosis(
            "actionable",
            "External verification is limiting confidence or evidence completeness.",
            ("external_verification",),
            0.90,
            CorrectionRecommendation.VERIFY,
            evidence_basis=tuple(_evidence_label(e) for e in external_failures),
        )

    unknown_dimensions = tuple(name for name, dimension in result.dimensions.items() if dimension.status == "unknown")
    if result.confidence < profile.minimum_confidence or unknown_dimensions:
        return Diagnosis(
            "uncertain",
            "The evaluation is not sufficiently confident to justify acceptance.",
            ("low_confidence",),
            0.85,
            CorrectionRecommendation.VERIFY,
            affected_dimensions=unknown_dimensions,
            evidence_basis=("evaluation_confidence",),
        )

    if revision_assessment is not None and revision_assessment.status in {"regressed", "unchanged"}:
        return Diagnosis(
            "actionable",
            "The latest correction did not demonstrate sufficient improvement; a materially different approach is warranted.",
            (revision_assessment.status,),
            0.90,
            CorrectionRecommendation.CHANGE_APPROACH,
            affected_dimensions=revision_assessment.regressed_dimensions,
            affected_issues=revision_assessment.introduced_issues,
            evidence_basis=("revision_assessment",),
        )

    material_issues = tuple(issue for issue in result.issues if issue.severity in {Severity.CRITICAL, Severity.MAJOR, Severity.MODERATE})
    failing_dimensions = tuple(name for name, dimension in result.dimensions.items() if dimension.status in {"fail", "partial"})
    if result.decision is Decision.ACCEPT:
        return Diagnosis(
            "actionable",
            "The candidate appears acceptance-ready under the current evaluation.",
            confidence=0.90,
            recommended_correction=CorrectionRecommendation.ACCEPT_CANDIDATE,
            evidence_basis=("evaluation",),
        )

    if previous_recommendation == CorrectionRecommendation.CHANGE_APPROACH:
        return Diagnosis(
            "actionable",
            "The previous approach change did not produce acceptance; continue with bounded correction under existing policy.",
            ("approach_change_insufficient",),
            0.75,
            CorrectionRecommendation.REVISE,
            affected_dimensions=failing_dimensions,
            affected_issues=tuple(issue.type for issue in material_issues),
            evidence_basis=("evaluation",),
        )

    return Diagnosis(
        "actionable",
        "The candidate has correctable quality issues under the current approach.",
        ("quality",),
        0.80,
        CorrectionRecommendation.REVISE,
        affected_dimensions=failing_dimensions,
        affected_issues=tuple(issue.type for issue in material_issues),
        evidence_basis=("evaluation",),
    )
