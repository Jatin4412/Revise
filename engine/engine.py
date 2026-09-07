from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .providers import Primary, Secondary, Verifier
from .revise.decision import decide
from .revise.evaluator import evaluate
from .revise.evidence import fuse_evidence
from .revise.models import (
    Decision,
    EvaluationProfile,
    EvaluationResult,
    Evidence,
    TaskContract,
    Version,
)
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
    ) -> EngineResult:
        profile = profile or build_profile(contract)
        supplied_evidence = tuple(evidence)
        versions: list[Version] = []
        previous: Version | None = None

        for revision_index in range(profile.max_revisions + 1):
            revision_context = self._revision_context(previous)
            response = self.primary.generate(
                contract,
                context=initial_context if previous is None else revision_context,
            )
            version = Version(
                id=f"v{len(versions)}",
                response=response,
                parent_id=previous.id if previous else None,
            )

            result = self._evaluate(
                contract,
                response,
                profile,
                evidence=supplied_evidence,
                revisions_used=revision_index,
            )
            version = Version(
                version.id,
                version.response,
                result,
                version.parent_id,
            )
            versions.append(version)

            if result.decision is Decision.ACCEPT:
                return EngineResult(Decision.ACCEPT, self._best_accepted(versions), tuple(versions), contract, profile)
            if result.decision is Decision.ASK:
                return EngineResult(Decision.ASK, self._best_accepted(versions), tuple(versions), contract, profile)

            previous = version

        return EngineResult(Decision.REVISE, self._best_accepted(versions), tuple(versions), contract, profile)

    def _evaluate(
        self,
        contract: TaskContract,
        response: str,
        profile: EvaluationProfile,
        *,
        evidence: Iterable[Evidence],
        revisions_used: int,
    ) -> EvaluationResult:
        # Secondary is optional in the first implementation. A supplied secondary
        # can add dimension judgments; deterministic verifier evidence is fused in
        # before the decision is made.
        evaluators = self.secondary.evaluators(contract, profile) if self.secondary else {}
        base = evaluate(contract, response, profile, evaluators, evidence=evidence)

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
    def _revision_context(previous: Version | None) -> str | None:
        if previous is None or previous.evaluation is None:
            return None
        instructions = previous.evaluation.revision.instructions
        issues = tuple(issue.description for issue in previous.evaluation.issues)
        parts = ["Revise the previous response using the evaluation feedback.", previous.response]
        if issues:
            parts.append("Issues:\n" + "\n".join(f"- {item}" for item in issues))
        if instructions:
            parts.append("Revision instructions:\n" + "\n".join(f"- {item}" for item in instructions))
        return "\n\n".join(parts)

    @staticmethod
    def _best_accepted(versions: list[Version]) -> Version | None:
        accepted = [v for v in versions if v.evaluation and v.evaluation.decision is Decision.ACCEPT]
        if not accepted:
            return None
        return max(
            accepted,
            key=lambda v: (v.evaluation.overall_score or 0.0, v.evaluation.confidence),
        )
