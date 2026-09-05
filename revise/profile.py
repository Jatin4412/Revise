from __future__ import annotations

from .models import EvaluationProfile, Mode, TaskContract

CORE = (
    "goal_alignment",
    "task_completion",
    "correctness",
    "relevance",
    "completeness",
    "instruction_following",
)
COMMUNICATION = (
    "coherence",
    "clarity",
    "usability",
    "appropriate_depth",
    "conciseness",
)
RELIABILITY = (
    "groundedness",
    "evidence_quality",
    "uncertainty_calibration",
    "assumption_quality",
    "context_utilization",
)


def _has_any(values: tuple[str, ...], keywords: tuple[str, ...]) -> bool:
    text = " ".join(values).lower()
    return any(keyword in text for keyword in keywords)


def build_profile(contract: TaskContract) -> EvaluationProfile:
    """Build the smallest useful evaluator profile without judging the response yet."""
    task_text = " ".join(
        (
            contract.goal,
            *contract.requirements,
            *contract.constraints,
            *contract.success_criteria,
            *contract.verification_requirements,
        )
    ).lower()

    dimensions = list(CORE)
    deterministic: list[str] = []
    external: list[str] = []
    specialized: list[str] = []
    hard_gates: list[str] = []

    if any(k in task_text for k in ("code", "python", "javascript", "function", "program", "test")):
        specialized.append("code_correctness")
        deterministic.append("compile_or_tests")

    if any(k in task_text for k in ("math", "calculate", "equation", "arithmetic", "percentage")):
        specialized.append("mathematical_validity")
        deterministic.append("calculator")

    if any(k in task_text for k in ("json", "schema", "structured output")):
        deterministic.append("schema_validation")

    if any(k in task_text for k in ("citation", "cite", "source", "sources", "research", "latest", "current")):
        dimensions.extend(("groundedness", "evidence_quality"))
        external.append("source_verification")

    if any(k in task_text for k in ("logic", "proof", "reasoning", "derive", "argument")):
        specialized.append("logical_validity")

    if contract.known_context or contract.missing_context:
        dimensions.append("context_utilization")

    if contract.desired_format or contract.desired_style or contract.desired_length:
        dimensions.extend(("clarity", "usability"))

    if contract.mode in (Mode.BASIC, Mode.PRO, Mode.AUTO):
        dimensions.append("appropriate_depth")

    # Safety/security/critical constraints are hard gates when explicitly implicated.
    if any(k in task_text for k in ("safety", "secure", "security", "critical", "medical", "legal")):
        hard_gates.append("critical_constraints")

    # Deduplicate while preserving order.
    dimensions = list(dict.fromkeys(dimensions + specialized))

    if contract.mode is Mode.LITE:
        effort, revisions, verification = "low", 0, 1
    elif contract.mode is Mode.PRO:
        effort, revisions, verification = "high", 2, 4
    elif contract.mode is Mode.AUTO:
        effort, revisions, verification = "medium", 1, 3
    else:
        effort, revisions, verification = "medium", 1, 2

    return EvaluationProfile(
        dimensions=tuple(dimensions),
        hard_gates=tuple(hard_gates),
        deterministic_checks=tuple(dict.fromkeys(deterministic)),
        external_verification=tuple(dict.fromkeys(external)),
        llm_evaluators=("general_evaluator",),
        evidence_requirements=tuple(external),
        evaluation_effort=effort,
        max_revisions=revisions,
        max_verification_steps=verification,
        stopping_conditions=("required_gates_pass", "revision_budget_exhausted", "diminishing_returns"),
    )
