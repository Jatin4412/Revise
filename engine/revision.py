from __future__ import annotations

from .revise.models import EvaluationResult, Version


def should_replace(previous: Version, candidate: Version) -> bool:
    """Replace only when the candidate is demonstrably at least as good."""
    if previous.evaluation is None:
        return True
    if candidate.evaluation is None:
        return False

    previous_accept = previous.evaluation.decision.value == "accept"
    candidate_accept = candidate.evaluation.decision.value == "accept"
    if candidate_accept != previous_accept:
        return candidate_accept

    previous_score = previous.evaluation.overall_score or 0.0
    candidate_score = candidate.evaluation.overall_score or 0.0
    if candidate_score != previous_score:
        return candidate_score > previous_score
    return candidate.evaluation.confidence >= previous.evaluation.confidence


def revision_instructions(result: EvaluationResult) -> tuple[str, ...]:
    """Turn findings into bounded instructions for the next Primary pass."""
    instructions = list(result.revision.instructions)
    if not instructions:
        instructions.extend(issue.description for issue in result.issues)
    return tuple(dict.fromkeys(instructions))
