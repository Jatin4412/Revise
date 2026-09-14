from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum


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


_VALID_STATUSES = {"actionable", "uncertain"}
_MIN_CONFIDENCE = 0.60


def validate_diagnosis(
    diagnosis: Diagnosis,
    *,
    minimum_confidence: float = _MIN_CONFIDENCE,
) -> Diagnosis | None:
    """Validate advisory diagnosis data and fail closed when it is unreliable.

    Validation is intentionally structural. It does not evaluate whether a
    recommendation is permitted; that remains the responsibility of the
    existing Decision policy and authoritative evidence checks.
    """
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
