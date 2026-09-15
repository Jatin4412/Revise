from __future__ import annotations

import json
import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ..providers import Primary
from .models import TaskContract


_GENERATION = "generate"


@dataclass(frozen=True)
class Plan:
    approach: str
    subproblems: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    open_questions: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReasoningState:
    plan: Plan
    candidate: str
    assumptions: tuple[str, ...] = ()
    open_questions: tuple[str, ...] = ()
    cycle: int = 0
    approach_id: str = "approach-0"


@dataclass(frozen=True)
class ReflectionConcern:
    kind: str
    description: str
    severity: str = "moderate"


@dataclass(frozen=True)
class Reflection:
    concerns: tuple[ReflectionConcern, ...] = ()
    challenged_assumptions: tuple[str, ...] = ()
    missing_steps: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()
    alternative_interpretations: tuple[str, ...] = ()
    alternative_approaches: tuple[str, ...] = ()
    confidence: float = 0.0
    actionable: bool = False

    @property
    def concern_count(self) -> int:
        return len(self.concerns) + len(self.challenged_assumptions) + len(self.missing_steps) + len(self.contradictions) + len(self.alternative_interpretations) + len(self.alternative_approaches)


@dataclass(frozen=True)
class CorrectionPlan:
    problem: str
    objective: str
    required_change: str
    approach: str
    change_approach: bool = False


@dataclass(frozen=True)
class DeliberationResult:
    candidate: str
    plan: Plan | None
    state: ReasoningState | None
    reflections: tuple[Reflection, ...] = ()
    corrections: tuple[CorrectionPlan, ...] = ()
    cycles: int = 0
    correction_attempts: int = 0
    stop_reason: str = "disabled"

    @property
    def corrected(self) -> bool:
        return bool(self.corrections)

    @property
    def concern_count(self) -> int:
        return sum(item.concern_count for item in self.reflections)


@dataclass(frozen=True)
class DeliberationLimits:
    max_cycles: int = 0
    max_correction_attempts: int = 0


Trace = Callable[[str, str], None]


def run_deliberation(
    contract: TaskContract,
    primary: Primary,
    *,
    context: str | None = None,
    limits: DeliberationLimits = DeliberationLimits(),
    trace: Trace | None = None,
) -> DeliberationResult:
    """Run one bounded deliberation lifecycle using the configured Primary role.

    Deliberation is deliberately optional for legacy Primary adapters. Adapters that
    expose ``deliberate(contract, prompt)`` can participate without changing provider
    selection or introducing a separate agent/model abstraction.
    """
    max_cycles = max(0, limits.max_cycles)
    max_corrections = max(0, limits.max_correction_attempts)
    deliberate = getattr(primary, "deliberate", None)

    if max_cycles == 0 or not callable(deliberate):
        if trace:
            trace("skipped", "disabled_or_unsupported")
        candidate = primary.generate(contract, context=context)
        return DeliberationResult(candidate=candidate, plan=None, state=None, stop_reason="disabled")

    try:
        plan = _call_structured(
            deliberate,
            contract,
            _plan_prompt(contract, context),
            _parse_plan,
        )
        _trace(trace, "plan", "complete")
    except Exception as exc:
        _trace(trace, "plan", f"failed:{type(exc).__name__}")
        return _fallback(contract, primary, context, trace, "plan_failed")

    try:
        state = _call_structured(
            deliberate,
            contract,
            _reason_prompt(contract, plan, context=context),
            _parse_reasoning_state,
        )
        state = ReasoningState(
            plan=plan,
            candidate=state.candidate,
            assumptions=state.assumptions,
            open_questions=state.open_questions,
            cycle=0,
            approach_id="approach-0",
        )
        _trace(trace, "reason", "complete",)
    except Exception as exc:
        _trace(trace, "reason", f"failed:{type(exc).__name__}")
        return _fallback(contract, primary, context, trace, "reason_failed")

    reflections: list[Reflection] = []
    corrections: list[CorrectionPlan] = []
    current = state

    for cycle in range(1, max_cycles + 1):
        try:
            reflection = _call_structured(
                deliberate,
                contract,
                _reflection_prompt(contract, current),
                _parse_reflection,
            )
            reflections.append(reflection)
            _trace(trace, "reflect", "complete", cycle=cycle, concerns=reflection.concern_count, actionable=reflection.actionable)
        except Exception as exc:
            _trace(trace, "reflect", f"failed:{type(exc).__name__}", cycle=cycle)
            return DeliberationResult(current.candidate, plan, current, tuple(reflections), tuple(corrections), cycle - 1, len(corrections), "reflection_failed")

        if not reflection.actionable or reflection.concern_count == 0:
            return DeliberationResult(current.candidate, plan, current, tuple(reflections), tuple(corrections), cycle, len(corrections), "no_actionable_concern")
        if len(corrections) >= max_corrections:
            return DeliberationResult(current.candidate, plan, current, tuple(reflections), tuple(corrections), cycle, len(corrections), "correction_budget_exhausted")

        try:
            correction = _call_structured(
                deliberate,
                contract,
                _correction_prompt(contract, current, reflection),
                _parse_correction,
            )
            corrections.append(correction)
            next_approach = f"approach-{len(corrections)}" if correction.change_approach else current.approach_id
            _trace(trace, "correct", "complete", cycle=cycle, approach_id=next_approach, changed=correction.change_approach)
        except Exception as exc:
            _trace(trace, "correct", f"failed:{type(exc).__name__}", cycle=cycle)
            return DeliberationResult(current.candidate, plan, current, tuple(reflections), tuple(corrections), cycle, len(corrections), "correction_failed")

        try:
            current = _call_structured(
                deliberate,
                contract,
                _reason_prompt(contract, plan, context=context, prior=current, correction=correction, cycle=cycle),
                _parse_reasoning_state,
            )
            current = ReasoningState(
                plan=plan,
                candidate=current.candidate,
                assumptions=current.assumptions,
                open_questions=current.open_questions,
                cycle=cycle,
                approach_id=next_approach,
            )
            _trace(trace, "re_reason", "complete", cycle=cycle, approach_id=next_approach)
        except Exception as exc:
            _trace(trace, "re_reason", f"failed:{type(exc).__name__}", cycle=cycle)
            return DeliberationResult(current.candidate, plan, current, tuple(reflections), tuple(corrections), cycle, len(corrections), "re_reason_failed")

    return DeliberationResult(current.candidate, plan, current, tuple(reflections), tuple(corrections), max_cycles, len(corrections), "deliberation_budget_exhausted")


def _fallback(contract: TaskContract, primary: Primary, context: str | None, trace: Trace | None, reason: str) -> DeliberationResult:
    try:
        candidate = primary.generate(contract, context=context)
    except Exception:
        raise
    _trace(trace, "fallback", reason)
    return DeliberationResult(candidate=candidate, plan=None, state=None, stop_reason=reason)


def _call_structured(call: Callable[..., str], contract: TaskContract, prompt: str, parser: Callable[[dict[str, Any]], Any]) -> Any:
    raw = call(contract, prompt)
    payload = _parse_json_object(raw)
    return parser(payload)


def _parse_json_object(raw: str) -> dict[str, Any]:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("deliberation output was empty")
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned[3:].strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError("deliberation output was not valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("deliberation output must be a JSON object")
    return payload


def _text(value: Any, field: str, *, required: bool = True, max_length: int = 2000) -> str:
    if value is None and not required:
        return ""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()[:max_length]


def _strings(value: Any, field: str, *, max_items: int = 8, max_length: int = 500) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or len(value) > max_items:
        raise ValueError(f"{field} must be a bounded list")
    result = []
    for item in value:
        result.append(_text(item, field, max_length=max_length))
    return tuple(result)


def _parse_plan(payload: dict[str, Any]) -> Plan:
    return Plan(
        approach=_text(payload.get("approach"), "approach", max_length=1000),
        subproblems=_strings(payload.get("subproblems"), "subproblems"),
        assumptions=_strings(payload.get("assumptions"), "assumptions"),
        open_questions=_strings(payload.get("open_questions"), "open_questions"),
    )


def _parse_reasoning_state(payload: dict[str, Any]) -> ReasoningState:
    candidate = _text(payload.get("candidate"), "candidate", max_length=20000)
    assumptions = _strings(payload.get("assumptions"), "assumptions")
    open_questions = _strings(payload.get("open_questions"), "open_questions")
    return ReasoningState(Plan("placeholder"), candidate, assumptions, open_questions)


def _parse_reflection(payload: dict[str, Any]) -> Reflection:
    raw_concerns = payload.get("concerns", [])
    if not isinstance(raw_concerns, list) or len(raw_concerns) > 8:
        raise ValueError("concerns must be a bounded list")
    concerns = []
    for item in raw_concerns:
        if not isinstance(item, dict):
            raise ValueError("reflection concern must be an object")
        kind = _text(item.get("kind"), "concern.kind", max_length=100)
        description = _text(item.get("description"), "concern.description", max_length=800)
        severity = item.get("severity", "moderate")
        if severity not in {"critical", "major", "moderate", "minor", "informational"}:
            raise ValueError("invalid reflection severity")
        concerns.append(ReflectionConcern(kind, description, severity))
    confidence = payload.get("confidence", 0.0)
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
        raise ValueError("reflection confidence must be between 0 and 1")
    actionable = payload.get("actionable", False)
    if not isinstance(actionable, bool):
        raise ValueError("reflection actionable must be boolean")
    return Reflection(
        concerns=tuple(concerns),
        challenged_assumptions=_strings(payload.get("challenged_assumptions"), "challenged_assumptions"),
        missing_steps=_strings(payload.get("missing_steps"), "missing_steps"),
        contradictions=_strings(payload.get("contradictions"), "contradictions"),
        alternative_interpretations=_strings(payload.get("alternative_interpretations"), "alternative_interpretations"),
        alternative_approaches=_strings(payload.get("alternative_approaches"), "alternative_approaches"),
        confidence=float(confidence),
        actionable=actionable,
    )


def _parse_correction(payload: dict[str, Any]) -> CorrectionPlan:
    change_approach = payload.get("change_approach", False)
    if not isinstance(change_approach, bool):
        raise ValueError("change_approach must be boolean")
    return CorrectionPlan(
        problem=_text(payload.get("problem"), "problem", max_length=1000),
        objective=_text(payload.get("objective"), "objective", max_length=1000),
        required_change=_text(payload.get("required_change"), "required_change", max_length=1200),
        approach=_text(payload.get("approach"), "approach", max_length=1000),
        change_approach=change_approach,
    )


def _task_sections(contract: TaskContract) -> str:
    parts = [f"Task:\n{contract.goal}"]
    if contract.requirements:
        parts.append("Requirements:\n" + "\n".join(f"- {item}" for item in contract.requirements))
    if contract.constraints:
        parts.append("Constraints:\n" + "\n".join(f"- {item}" for item in contract.constraints))
    if contract.desired_format:
        parts.append(f"Format: {contract.desired_format}")
    if contract.desired_length:
        parts.append(f"Length: {contract.desired_length}")
    if contract.desired_style:
        parts.append(f"Style: {contract.desired_style}")
    if contract.known_context:
        parts.append("Known context:\n" + "\n".join(contract.known_context))
    return "\n\n".join(parts)


def _plan_prompt(contract: TaskContract, context: str | None) -> str:
    revision = f"\n\nPrior attempt context:\n{context}" if context else ""
    return f"""You are the planning role in Reiterate deliberation. Build a task-bounded approach before producing an answer. Do not change the task contract. Do not decide whether an answer is acceptable. Do not expose chain-of-thought; return only a concise structured plan.\n\n{_task_sections(contract)}{revision}\n\nReturn ONLY JSON:\n{{\n  \"approach\": \"brief method for solving the task\",\n  \"subproblems\": [\"bounded subproblem\"],\n  \"assumptions\": [\"assumption that remains distinguishable from fact\"],\n  \"open_questions\": [\"question that may block reliable completion\"]\n}}"""


def _reason_prompt(contract: TaskContract, plan: Plan, *, context: str | None = None, prior: ReasoningState | None = None, correction: CorrectionPlan | None = None, cycle: int = 0) -> str:
    parts = [
        "You are the reasoning role in Reiterate deliberation. Construct or rebuild the candidate from the task and the supplied plan.",
        "Do not redefine the task contract. Do not decide acceptance. Do not expose chain-of-thought. Return a concise structured reasoning state with the candidate answer and only bounded metadata.",
        _task_sections(contract),
        f"Plan approach: {plan.approach}",
    ]
    if plan.subproblems:
        parts.append("Plan subproblems:\n" + "\n".join(f"- {item}" for item in plan.subproblems))
    if plan.assumptions:
        parts.append("Plan assumptions:\n" + "\n".join(f"- {item}" for item in plan.assumptions))
    if context:
        parts.append("Prior attempt context:\n" + context)
    if prior:
        parts.append(f"Current candidate:\n{prior.candidate}")
        if prior.assumptions:
            parts.append("Current assumptions:\n" + "\n".join(f"- {item}" for item in prior.assumptions))
        if prior.open_questions:
            parts.append("Open questions:\n" + "\n".join(f"- {item}" for item in prior.open_questions))
    if correction:
        parts.append(
            "Targeted correction plan:\n"
            f"Problem: {correction.problem}\n"
            f"Objective: {correction.objective}\n"
            f"Required change: {correction.required_change}\n"
            f"Approach: {correction.approach}\n"
            f"Change approach: {correction.change_approach}"
        )
    parts.append(f"Deliberation cycle: {cycle}")
    parts.append("Return ONLY JSON:\n{\n  \"candidate\": \"complete candidate response\",\n  \"assumptions\": [\"bounded assumption\"],\n  \"open_questions\": [\"remaining uncertainty\"]\n}")
    return "\n\n".join(parts)


def _reflection_prompt(contract: TaskContract, state: ReasoningState) -> str:
    return f"""You are the adversarial reflection role in Reiterate. Your job is to try to destabilize the current reasoning, not to defend it and not to score or accept the candidate. Search actively for unsupported assumptions, invalid or weak inferences, missing steps, contradictions, ambiguous interpretations, ignored requirements, weak evidence, circular reasoning, wrong framing, unsuitable approach, and other plausible failure modes. A correction is only warranted when a concern is actionable. Do not change the task contract. Do not issue ACCEPT, REVISE, or ASK decisions. Do not expose chain-of-thought.\n\n{_task_sections(contract)}\n\nCurrent approach:\n{state.plan.approach}\n\nCurrent candidate:\n{state.candidate}\n\nKnown assumptions:\n{chr(10).join(f'- {x}' for x in state.assumptions) or '- none'}\n\nReturn ONLY JSON:\n{{\n  \"concerns\": [{{\"kind\": \"hidden_assumption|wrong_approach|missing_inference|ambiguity|contradiction|weak_evidence|circular_reasoning|other\", \"description\": \"specific challenge\", \"severity\": \"critical|major|moderate|minor|informational\"}}],\n  \"challenged_assumptions\": [\"assumption to reconsider\"],\n  \"missing_steps\": [\"required inference that is absent\"],\n  \"contradictions\": [\"specific contradiction\"],\n  \"alternative_interpretations\": [\"plausible alternative reading\"],\n  \"alternative_approaches\": [\"materially different approach if warranted\"],\n  \"confidence\": 0.0,\n  \"actionable\": false\n}}\n\nSet actionable=true only when at least one concern can be addressed by a concrete correction or approach change. Never treat reflection itself as proof of correctness."""


def _correction_prompt(contract: TaskContract, state: ReasoningState, reflection: Reflection) -> str:
    concerns = "\n".join(f"- {item.kind}: {item.description} ({item.severity})" for item in reflection.concerns) or "- none"
    return f"""You are the correction-planning role in Reiterate. Convert the reflection findings into one targeted correction hypothesis. Do not decide whether the candidate is correct. Do not claim that the correction proves correctness. Do not change the task contract. The next reasoning attempt must actually rebuild or modify the candidate in response to this plan.\n\n{_task_sections(contract)}\n\nCurrent approach:\n{state.plan.approach}\n\nCurrent candidate:\n{state.candidate}\n\nReflection concerns:\n{concerns}\n\nChallenged assumptions:\n{chr(10).join(f'- {x}' for x in reflection.challenged_assumptions) or '- none'}\n\nMissing steps:\n{chr(10).join(f'- {x}' for x in reflection.missing_steps) or '- none'}\n\nAlternative approaches:\n{chr(10).join(f'- {x}' for x in reflection.alternative_approaches) or '- none'}\n\nReturn ONLY JSON:\n{{\n  \"problem\": \"specific problem being corrected\",\n  \"objective\": \"what the next reasoning attempt must establish\",\n  \"required_change\": \"concrete change required in the reasoning or candidate\",\n  \"approach\": \"how the next attempt should proceed\",\n  \"change_approach\": false\n}}"""


def _trace(trace: Trace | None, stage: str, status: str, **details: object) -> None:
    if trace:
        trace(stage, status, **details)
