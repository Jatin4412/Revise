from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .providers import Primary, Secondary, Verifier
from .revise.decision import decide
from .revise.evaluator import evaluate
from .revise.evidence import fuse_evidence
from .revise.models import Decision, EvaluationProfile, EvaluationResult, Evidence, TaskContract, Version
from .revise.profile import build_profile


@dataclass(frozen=True)
class EngineResult:
    decision: Decision
    final_version: Version | None
    versions: tuple[Version, ...]
    task_contract: TaskContract
    evaluation_profile: EvaluationProfile


class Engine:
    """Provider-agnostic generation, evaluation, revision, and verification loop."""

    def __init__(
        self,
        primary: Primary,
        *,
        secondary: Secondary | None = None,
        verifier: Verifier | None = None,
    ) -> None:
        self.primary = primary
        self.secondary = secondary
        self.verifier = verifier

    def run(
        self,
        contract: TaskContract,
        *,
        profile: EvaluationProfile | None = None,
        initial_context: str | None = None,
        evidence: Iterable[Evidence] = (),
        primary: Primary | None = None,
    ) -> EngineResult:
        """Run the engine, optionally overriding the configured Primary for this request."""
        profile = profile or build_profile(contract)
        active_primary = primary or self.primary
        supplied_evidence = tuple(evidence)
        versions: list[Version] = []
        previous: Version | None = None

        for revision_index in range(profile.max_revisions + 1):
            context = initial_context if previous is None else self._revision_context(previous)
            response = active_primary.generate(contract, context=context)
            version = Version(f"v{len(versions)}", response, parent_id=previous.id if previous else None)

            result = self._evaluate(
                contract,
                response,
                profile,
                evidence=supplied_evidence,
                revisions_used=revision_index,
            )
            version = Version(version.id, version.response, result, version.parent_id)
            versions.append(version)

            if result.decision in (Decision.ACCEPT, Decision.ASK):
                return EngineResult(result.decision, self._best_version(versions), tuple(versions), contract, profile)
            previous = version

        return EngineResult(Decision.REVISE, self._best_version(versions), tuple(versions), contract, profile)

    def _evaluate(
        self,
        contract: TaskContract,
        response: str,
        profile: EvaluationProfile,
        *,
        evidence: Iterable[Evidence],
        revisions_used: int,
    ) -> EvaluationResult:
        evaluators = self.secondary.evaluators(contract, profile) if self.secondary else {}
        base = evaluate(contract, response, profile, dict(evaluators), evidence=evidence)
        verifier_evidence = self.verifier.verify(contract, response, profile) if self.verifier else ()
        fused = fuse_evidence((*base.evidence, *verifier_evidence))
        result = EvaluationResult(
            decision=base.decision,
            overall_score=base.overall_score,
            confidence=base.confidence,
            dimensions=base.dimensions,
            issues=base.issues,
            evidence=fused.evidence,
            revision=base.revision,
            verification=base.verification,
        )
        return decide(contract, profile, result, revisions_used=revisions_used)

    @staticmethod
    def _revision_context(previous: Version) -> str:
        evaluation = previous.evaluation
        if evaluation is None:
            return previous.response
        parts = ["Revise the previous response using the evaluation feedback.", previous.response]
        issues = tuple(issue.description for issue in evaluation.issues)
        if issues:
            parts.append("Issues:\n" + "\n".join(f"- {item}" for item in issues))
        if evaluation.revision.instructions:
            parts.append("Revision instructions:\n" + "\n".join(f"- {item}" for item in evaluation.revision.instructions))
        return "\n\n".join(parts)

    @staticmethod
    def _best_version(versions: list[Version]) -> Version | None:
        accepted = [v for v in versions if v.evaluation and v.evaluation.decision is Decision.ACCEPT]
        candidates = accepted or [v for v in versions if v.evaluation]
        return max(candidates, key=lambda v: (v.evaluation.overall_score or 0.0, v.evaluation.confidence), default=None)
