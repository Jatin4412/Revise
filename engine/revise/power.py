"""Provider-neutral execution effort planning for Revise Power modes."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .models import Mode, TaskContract


@dataclass(frozen=True)
class PowerPlan:
    """Resolved execution effort for one task."""

    mode: Mode
    effort: str
    complexity: str
    generation_guidance: str
    evaluation_guidance: str


_MATH_EXPRESSION_RE = re.compile(r"\d+(?:\s*(?:[+\-*/×÷])\s*\d+)+")
_HIGH_SIGNAL = (
    "debug", "prove", "proof", "implement", "program", "code", "research",
    "citation", "source", "compare", "design", "analyze", "analyse", "derive",
    "calculate", "equation", "formula", "architecture", "security",
)


def select_power_plan(contract: TaskContract) -> PowerPlan:
    """Resolve explicit Power, with Auto adapting effort to task complexity."""
    if contract.mode is Mode.LITE:
        return _plan(contract.mode, "low", "simple")
    if contract.mode is Mode.BASIC:
        return _plan(contract.mode, "medium", "standard")
    if contract.mode is Mode.PRO:
        return _plan(contract.mode, "high", "deep")

    text = " ".join(
        (
            contract.goal,
            *contract.requirements,
            *contract.constraints,
            contract.desired_format or "",
            contract.desired_length or "",
            contract.desired_style or "",
            *contract.known_context,
            *contract.assumptions,
            *contract.success_criteria,
            *contract.verification_requirements,
        )
    ).lower()
    signals = sum(1 for term in _HIGH_SIGNAL if term in text)
    if _MATH_EXPRESSION_RE.search(text):
        signals += 1
    if len(contract.requirements) >= 3 or len(contract.constraints) >= 3:
        signals += 1
    if len(text) >= 900:
        signals += 1

    if signals >= 2:
        return _plan(contract.mode, "high", "complex")
    if signals == 0:
        return _plan(contract.mode, "low", "simple")
    return _plan(contract.mode, "medium", "standard")


def _plan(mode: Mode, effort: str, complexity: str) -> PowerPlan:
    if effort == "low":
        generation = (
            "Answer directly and efficiently. Focus on the user's requested outcome, "
            "avoid unnecessary elaboration, and perform a quick internal consistency check "
            "before responding."
        )
        evaluation = (
            "Use a focused evaluation. Check the task requirements and correctness first; "
            "do not invent shortcomings merely for stylistic preference."
        )
    elif effort == "high":
        generation = (
            "Use high execution effort. Carefully reason through the task, check important "
            "requirements and constraints before answering, and prioritize correctness, "
            "completeness, and useful structure over speed. Do not add length that does not "
            "improve the answer."
        )
        evaluation = (
            "Use rigorous evaluation. Independently check every requested dimension, look "
            "for subtle correctness or requirement failures, distinguish real issues from "
            "style preferences, and give actionable revision guidance when needed."
        )
    else:
        generation = (
            "Use normal execution effort. Address the task carefully, satisfy the explicit "
            "requirements and constraints, and keep the response proportionate to the task."
        )
        evaluation = (
            "Use balanced evaluation. Check the important requirements, correctness, and "
            "quality dimensions without over-penalizing harmless stylistic differences."
        )
    return PowerPlan(mode, effort, complexity, generation, evaluation)
