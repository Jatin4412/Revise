from __future__ import annotations

from dataclasses import dataclass

from .models import EvaluationResult


@dataclass(frozen=True)
class Diagnosis:
    """Post-hoc synthesis of observed evaluation/verification findings.

    Diagnosis is advisory metadata. It never produces or overrides a Decision.
    """

    category: str
    summary: str
    confidence: float
    basis: tuple[str, ...] = ()


def diagnose(result: EvaluationResult) -> Diagnosis:
    basis: list[str] = []
    if any(item.method == "deterministic" and item.result == "fail" for item in result.evidence):
        basis.append("deterministic_failure")
        return Diagnosis("verification_failure", "A directly checkable deterministic property failed.", 1.0, tuple(basis))
    if any(item.method == "external" and item.result == "fail" for item in result.evidence):
        basis.append("external_verification_failure")
        return Diagnosis("verification_failure", "A required external verification check did not pass.", 1.0, tuple(basis))
    if any(item.status == "unknown" for item in result.dimensions.values()):
        basis.append("unknown_evaluation")
        return Diagnosis("evaluation_uncertainty", "At least one required evaluation dimension is unknown or unavailable.", 0.95, tuple(basis))
    material_issues = [item for item in result.issues if item.severity.value in {"critical", "major", "moderate"}]
    if material_issues:
        basis.extend(f"issue:{item.type}" for item in material_issues[:4])
        return Diagnosis("evaluation_failure", "The candidate has material evaluation findings requiring attention.", 0.90, tuple(basis))
    if result.overall_score is not None and result.overall_score < 0.75:
        basis.append("low_overall_score")
        return Diagnosis("quality_failure", "The candidate is below the configured overall quality floor.", 0.85, tuple(basis))
    return Diagnosis("no_material_failure", "No material failure cause was observed in the evaluation and evidence available to diagnosis.", 0.70, ("evaluation_and_evidence_consistent",))
