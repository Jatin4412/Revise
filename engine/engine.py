from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from .execution import ExecutionTrace, TraceEvent
from .providers import Primary, Secondary, Verifier
from .revise.decision import decide
from .revise.evaluator import evaluate
from .revise.evidence import fuse_evidence
from .revise.models import Decision, EvaluationProfile, EvaluationResult, Evidence, TaskContract, Version
from .revise.profile import build_profile


TraceSink = Callable[[TraceEvent], None]


@dataclass(frozen=True)
class EngineResult:
    decision: Decision
    final_version: Version | None
    versions: tuple[Version, ...]
    task_contract: TaskContract
    evaluation_profile: EvaluationProfile
    trace: tuple[TraceEvent, ...] = ()


class Engine:
    """Provider-agnostic generation, evaluation, revision, and verification loop."""

    def __init__(
        self,
        primary: Primary,
        *,
        secondary: Secondary | None = None,
        verifier: Verifier | None = None,
        trace_sink: TraceSink | None = None,
    ) -> None:
        self.primary = primary
        self.secondary = secondary
        self.verifier = verifier
        self.trace_sink = trace_sink

    def run(
        self,
        contract: TaskContract,
        *,
        profile: EvaluationProfile | None = None,
        initial_context: str | None = None,
        evidence: Iterable[Evidence] = (),
        primary: Primary | None = None,
        secondary: Secondary | None = None,
    ) -> EngineResult:
        """Run the bounded Revise loop with optional per-request role overrides."""
        profile = profile or build_profile(contract)
        active_primary = primary or self.primary
        active_secondary = secondary or self.secondary
        supplied_evidence = tuple(evidence)
        versions: list[Version] = []
        previous: Version | None = None
        trace = ExecutionTrace()

        self._emit(trace, "request", "received", mode=contract.mode.value)
        self._emit(trace, "contract", "created", requirements=len(contract.requirements), constraints=len(contract.constraints))
        self._emit(
            trace,
            "profile",
            "selected",
            dimensions=", ".join(profile.dimensions),
            effort=profile.evaluation_effort,
            max_revisions=profile.max_revisions,
            max_verification_steps=profile.max_verification_steps,
        )

        for revision_index in range(profile.max_revisions + 1):
            context = initial_context if previous is None else self._revision_context(previous)
            version_id = f"v{len(versions)}"
            self._emit(
                trace,
                "primary",
                "start",
                provider=_provider_name(active_primary),
                model=_model_name(active_primary),
                version=version_id,
                revision=revision_index,
            )
            try:
                response = active_primary.generate(contract, context=context)
            except Exception as exc:
                self._emit(trace, "primary", "failed", provider=_provider_name(active_primary), model=_model_name(active_primary), version=version_id, error=type(exc).__name__)
                raise
            self._emit(trace, "primary", "complete", provider=_provider_name(active_primary), model=_model_name(active_primary), version=version_id)

            version = Version(version_id, response, parent_id=previous.id if previous else None)
            result = self._evaluate(
                contract,
                response,
                profile,
                secondary=active_secondary,
                evidence=supplied_evidence,
                revisions_used=revision_index,
                trace=trace,
            )
            version = Version(version.id, version.response, result, version.parent_id)
            versions.append(version)

            self._emit(trace, "decision", result.decision.value, version=version.id, score=result.overall_score, confidence=result.confidence)

            if result.decision in (Decision.ACCEPT, Decision.ASK):
                final = self._best_version(versions)
                self._emit(trace, "final", "selected", version=final.id if final else None, decision=result.decision.value)
                return EngineResult(result.decision, final, tuple(versions), contract, profile, trace.snapshot())
            previous = version
            self._emit(trace, "revision", "requested", from_version=version.id, next_version=f"v{len(versions)}")

        final = self._best_version(versions)
        self._emit(trace, "final", "selected", version=final.id if final else None, decision=Decision.REVISE.value)
        return EngineResult(Decision.REVISE, final, tuple(versions), contract, profile, trace.snapshot())

    def _evaluate(
        self,
        contract: TaskContract,
        response: str,
        profile: EvaluationProfile,
        *,
        secondary: Secondary | None,
        evidence: Iterable[Evidence],
        revisions_used: int,
        trace: ExecutionTrace,
    ) -> EvaluationResult:
        if secondary is not None:
            self._emit(trace, "secondary", "start", provider=_provider_name(secondary), model=_model_name(secondary))
        try:
            if secondary is not None and hasattr(secondary, "evaluate_candidate"):
                base = secondary.evaluate_candidate(contract, response, profile)  # type: ignore[attr-defined]
            else:
                evaluators = secondary.evaluators(contract, profile) if secondary else {}
                base = evaluate(contract, response, profile, dict(evaluators), evidence=evidence)
        except Exception as exc:
            if secondary is not None:
                self._emit(trace, "secondary", "failed", provider=_provider_name(secondary), model=_model_name(secondary), error=type(exc).__name__)
            raise

        if secondary is not None:
            self._emit(trace, "secondary", "complete", provider=_provider_name(secondary), model=_model_name(secondary))

        for name, dimension in base.dimensions.items():
            self._emit(
                trace,
                "evaluation",
                "dimension",
                name=name,
                evaluation_status=dimension.status,
                score=dimension.score,
                confidence=dimension.confidence,
            )
        if base.issues:
            self._emit(trace, "evaluation", "issues", count=len(base.issues))
        if base.revision.instructions:
            self._emit(trace, "evaluation", "revision_guidance", count=len(base.revision.instructions))

        verifier_evidence = ()
        if self.verifier is not None:
            self._emit(trace, "verifier", "start", verifier=type(self.verifier).__name__)
            try:
                verifier_evidence = self.verifier.verify(contract, response, profile)
            except Exception as exc:
                self._emit(trace, "verifier", "failed", verifier=type(self.verifier).__name__, error=type(exc).__name__)
                raise
            self._emit(trace, "verifier", "complete", verifier=type(self.verifier).__name__, evidence=len(verifier_evidence))

        fused = fuse_evidence((*base.evidence, *evidence, *verifier_evidence))
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

    def _emit(self, trace: ExecutionTrace, stage: str, event_status: str, **details: object) -> None:
        event = trace.record(stage, event_status, **details)
        if self.trace_sink is not None:
            try:
                self.trace_sink(event)
            except Exception:
                pass

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


def _provider_name(component: object) -> str:
    return str(getattr(component, "provider", None) or "custom")


def _model_name(component: object) -> str:
    return str(getattr(component, "model", None) or "custom")
