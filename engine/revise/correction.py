from __future__ import annotations

from dataclasses import dataclass

from .diagnosis import CorrectionRecommendation, Diagnosis, validate_diagnosis
from .models import Decision, EvaluationProfile, EvaluationResult, Severity


@dataclass(frozen=True)
class Correction:
    recommendation: CorrectionRecommendation
    approach_id: str
    approach_changed: bool = False


def diagnose_result(result: EvaluationResult, profile: EvaluationProfile, *, missing_context: bool = False) -> Diagnosis:
    """Derive a conservative advisory diagnosis from current observations."""
    if missing_context:
        return Diagnosis("actionable", "Required task context is unavailable.", confidence=1.0, recommended_correction=CorrectionRecommendation.ASK)
    if any(issue.severity == Severity.CRITICAL for issue in result.issues):
        return Diagnosis("actionable", "A critical issue blocks the current attempt.", tuple(i.type for i in result.issues if i.severity == Severity.CRITICAL), 0.98, CorrectionRecommendation.CHANGE_APPROACH)
    if any(e.result == "fail" and e.method in {"deterministic", "external"} for e in result.evidence):
        return Diagnosis("actionable", "Authoritative verification failed; the attempt requires a corrected path.", confidence=0.98, recommended_correction=CorrectionRecommendation.CHANGE_APPROACH, evidence_basis=tuple(e.method for e in result.evidence if e.result == "fail"))
    if any(e.result == "unknown" for e in result.evidence):
        return Diagnosis("uncertain", "Available evidence is insufficient to establish correctness.", confidence=0.75, recommended_correction=CorrectionRecommendation.VERIFY)
    unmet = []
    for requirement in profile.evidence_requirements:
        target = requirement.strip().lower()
        if not any(item.result == "pass" and target in " ".join((item.source, item.method, *item.provenance)).lower() for item in result.evidence):
            unmet.append(requirement)
    if unmet:
        return Diagnosis("actionable", "A required evidence condition is not yet satisfied.", tuple(unmet), 0.95, CorrectionRecommendation.VERIFY)
    if any(d.status == "unknown" for d in result.dimensions.values()) or result.confidence < profile.minimum_confidence:
        return Diagnosis("uncertain", "The evaluation is too uncertain for a reliable correction choice.", confidence=0.90, recommended_correction=CorrectionRecommendation.ASK)
    if result.decision is Decision.ACCEPT:
        return Diagnosis("actionable", "The attempt appears acceptance-ready under the evaluated criteria.", confidence=0.95, recommended_correction=CorrectionRecommendation.ACCEPT_CANDIDATE)
    if any(d.status in {"fail", "partial"} for d in result.dimensions.values()):
        return Diagnosis("actionable", "One or more evaluation dimensions require correction.", tuple(name for name, d in result.dimensions.items() if d.status in {"fail", "partial"}), 0.90, CorrectionRecommendation.REVISE)
    if result.overall_score is not None and result.overall_score < profile.minimum_overall_score:
        return Diagnosis("actionable", "The candidate does not yet meet the overall quality threshold.", confidence=0.90, recommended_correction=CorrectionRecommendation.REVISE)
    return Diagnosis("uncertain", "The current result does not provide a sufficiently clear correction signal.", confidence=0.65, recommended_correction=CorrectionRecommendation.ASK)


def choose_correction(diagnosis: Diagnosis, *, current_approach_id: str, remaining_revisions: int, remaining_verification_steps: int) -> Correction:
    """Convert an advisory diagnosis into bounded correction metadata."""
    validated = validate_diagnosis(diagnosis)
    if validated is None:
        return Correction(CorrectionRecommendation.ASK, current_approach_id, False)
    recommendation = validated.recommended_correction
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


def correction_context(recommendation: CorrectionRecommendation, previous_response: str, *, diagnosis: Diagnosis | None = None) -> str:
    """Build bounded next-attempt context without exposing internal reasoning."""
    if recommendation == CorrectionRecommendation.CHANGE_APPROACH:
        lead = "Use a materially different solution approach from the previous attempt. Do not merely reword or lightly edit it."
    elif recommendation == CorrectionRecommendation.VERIFY:
        lead = "Reassess the previous attempt with particular attention to evidence and verification requirements before producing the next answer."
    else:
        lead = "Revise the previous response using the evaluation feedback while preserving correct work."
    parts = [lead, previous_response]
    if diagnosis is not None and diagnosis.summary:
        parts.append("Correction focus: " + diagnosis.summary)
    return "\n\n".join(parts)
