from __future__ import annotations

from .models import EvaluationProfile, Mode, TaskContract

CORE = ("goal_alignment", "task_completion", "correctness", "relevance", "completeness", "instruction_following")
COMMUNICATION = ("coherence", "clarity", "usability", "appropriate_depth", "conciseness")
RELIABILITY = ("groundedness", "evidence_quality", "uncertainty_calibration", "assumption_quality", "context_utilization")
SPECIALIZED = ("mathematical_validity", "code_correctness", "logical_validity")


def build_profile(contract: TaskContract) -> EvaluationProfile:
    dimensions = list(CORE)
    text = " ".join((contract.goal, *contract.requirements, *contract.known_context)).lower()

    if any(k in text for k in ("code", "python", "program", "function", "implement")):
        dimensions.append("code_correctness")
    if any(k in text for k in ("math", "calculate", "equation", "formula", "arithmetic")):
        dimensions.append("mathematical_validity")
    if any(k in text for k in ("logic", "proof", "reasoning")):
        dimensions.append("logical_validity")
    if any(k in text for k in ("research", "source", "citation", "fact", "factual")):
        dimensions.extend(("groundedness", "evidence_quality", "source_verification"))

    if contract.mode is Mode.LITE:
        effort, revisions, verification = "low", 0, 1
    elif contract.mode is Mode.PRO:
        effort, revisions, verification = "high", 2, 4
    elif contract.mode is Mode.AUTO:
        effort, revisions, verification = "medium", 1, 3
    else:
        effort, revisions, verification = "medium", 1, 2

    hard_gate_terms = ("safety", "security", "critical", "medical", "legal")
    hard_gates = ("safety",) if any(k in text for k in hard_gate_terms) else ()

    return EvaluationProfile(
        dimensions=tuple(dict.fromkeys(dimensions)),
        hard_gates=hard_gates,
        deterministic_checks=(),
        external_verification=("source_verification",) if "source_verification" in dimensions else (),
        evaluation_effort=effort,
        max_revisions=revisions,
        max_verification_steps=verification,
    )
