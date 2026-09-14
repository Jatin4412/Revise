from __future__ import annotations

from dataclasses import dataclass

from .diagnosis import CorrectionRecommendation, Diagnosis, validate_diagnosis


@dataclass(frozen=True)
class Correction:
    recommendation: CorrectionRecommendation
    approach_id: str
    approach_changed: bool = False


def choose_correction(
    diagnosis: Diagnosis,
    *,
    current_approach_id: str,
    remaining_revisions: int,
    remaining_verification_steps: int,
) -> Correction:
    """Convert an advisory diagnosis into bounded correction metadata."""
    validated = validate_diagnosis(diagnosis)
    if validated is None:
        return Correction(CorrectionRecommendation.ASK, current_approach_id, False)

    recommendation = validated.recommended_correction
    if recommendation == CorrectionRecommendation.ACCEPT_CANDIDATE:
        # Acceptance is never a correction action; Decision remains authoritative.
        return Correction(CorrectionRecommendation.ACCEPT_CANDIDATE, current_approach_id, False)
    if recommendation == CorrectionRecommendation.VERIFY and remaining_verification_steps <= 0:
        recommendation = CorrectionRecommendation.REVISE if remaining_revisions > 0 else CorrectionRecommendation.ASK
    elif recommendation in {CorrectionRecommendation.REVISE, CorrectionRecommendation.CHANGE_APPROACH} and remaining_revisions <= 0:
        recommendation = CorrectionRecommendation.ASK

    changed = recommendation == CorrectionRecommendation.CHANGE_APPROACH
    if changed and current_approach_id.startswith("approach-") and current_approach_id.rsplit("-", 1)[-1].isdigit():
        approach_id = f"approach-{int(current_approach_id.rsplit('-', 1)[-1]) + 1}"
    else:
        approach_id = "approach-1" if changed else current_approach_id
    return Correction(recommendation, approach_id, changed)


def correction_context(
    recommendation: CorrectionRecommendation,
    previous_response: str,
    *,
    diagnosis: Diagnosis | None = None,
) -> str:
    """Build bounded next-attempt context without exposing internal reasoning."""
    if recommendation == CorrectionRecommendation.CHANGE_APPROACH:
        lead = "Use a materially different solution approach from the previous attempt. Do not merely reword or lightly edit it."
    elif recommendation == CorrectionRecommendation.VERIFY:
        lead = "Reassess the previous attempt with particular attention to evidence and verification requirements before producing the next answer."
    elif recommendation == CorrectionRecommendation.ACCEPT_CANDIDATE:
        lead = "The previous attempt appeared acceptance-ready; preserve correct work while following any required bounded correction."
    else:
        lead = "Revise the previous response using the evaluation feedback while preserving correct work."
    parts = [lead, previous_response]
    if diagnosis is not None and diagnosis.summary:
        parts.append("Correction focus: " + diagnosis.summary)
    return "\n\n".join(parts)
