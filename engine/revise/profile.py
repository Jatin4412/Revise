from __future__ import annotations

import re

from .models import EvaluationProfile, Mode, TaskContract

CORE = ("goal_alignment", "task_completion", "correctness", "relevance", "completeness", "instruction_following")
COMMUNICATION = ("coherence", "clarity", "usability", "appropriate_depth", "conciseness")
RELIABILITY = ("groundedness", "evidence_quality", "uncertainty_calibration", "assumption_quality", "context_utilization")
SPECIALIZED = ("mathematical_validity", "code_correctness", "logical_validity")
_MATH_EXPRESSION_RE = re.compile(r"\d+(?:\s*(?:[+\-*/×÷])\s*\d+)+")


def build_profile(contract: TaskContract) -> EvaluationProfile:
    dimensions = list(CORE)
    text = " ".join((contract.goal, *contract.requirements, *contract.known_context)).lower()
    deterministic_checks: list[str] = []
    if any(k in text for k in ("code", "python", "program", "function", "implement")):
        dimensions.append("code_correctness")
        if "python" in text:
            deterministic_checks.extend(("python_syntax", "python_compile"))
    if any(k in text for k in ("math", "calculate", "equation", "formula", "arithmetic")) or _MATH_EXPRESSION_RE.search(text):
        dimensions.append("mathematical_validity")
        deterministic_checks.append("arithmetic")
    if any(k in text for k in ("logic", "proof", "reasoning")): dimensions.append("logical_validity")
    if any(k in text for k in ("research", "source", "citation", "fact", "factual")): dimensions.extend(("groundedness", "evidence_quality", "source_verification"))
    if "json" in (contract.desired_format or "").lower() or any("json" in item.lower() for item in contract.verification_requirements): deterministic_checks.append("json")
    if contract.output_schema is not None: deterministic_checks.append("json_schema")
    if contract.mode is Mode.LITE: effort, revisions, verification = "low", 0, 1
    elif contract.mode is Mode.PRO: effort, revisions, verification = "high", 2, 4
    elif contract.mode is Mode.AUTO: effort, revisions, verification = "medium", 1, 3
    else: effort, revisions, verification = "medium", 1, 2
    weights = {name: 1.0 for name in dimensions}
    for name in ("goal_alignment", "task_completion", "correctness", "instruction_following"):
        weights[name] = 1.25
    for name in ("coherence", "clarity", "usability", "appropriate_depth", "conciseness"):
        if name in weights: weights[name] = 0.75
    for name in ("mathematical_validity", "code_correctness", "logical_validity"):
        if name in weights: weights[name] = 1.25
    minimum_scores = {name: 0.70 for name in dimensions}
    required = tuple(name for name in ("goal_alignment", "task_completion", "correctness", "instruction_following") if name in dimensions)
    hard_gate_terms = ("safety", "security", "critical", "medical", "legal")
    hard_gates = ("safety",) if any(k in text for k in hard_gate_terms) else ()
    return EvaluationProfile(dimensions=tuple(dict.fromkeys(dimensions)), hard_gates=hard_gates, deterministic_checks=tuple(dict.fromkeys(deterministic_checks)), external_verification=("source_verification",) if "source_verification" in dimensions else (), dimension_weights=weights, minimum_scores=minimum_scores, required_dimensions=required, minimum_confidence=0.60, minimum_overall_score=0.75, evaluation_effort=effort, max_revisions=revisions, max_verification_steps=verification)
