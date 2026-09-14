from __future__ import annotations

import unittest

from engine.engine import Engine, EngineResult
from engine.model import ModelRouter, ModelSelection
from engine.providers import FunctionPrimary
from engine.revise.decision import decide
from engine.revise.models import (
    Decision,
    DimensionResult,
    EvaluationProfile,
    EvaluationResult,
    Evidence,
    Issue,
    Mode,
    Severity,
    TaskContract,
    Version,
)
from engine.revise.profile import build_profile
from engine.revise.revision import RevisionAssessment
from engine.service import EngineRequest, EngineService


def profile(*, max_revisions: int = 1, max_verification_steps: int = 2, **kwargs) -> EvaluationProfile:
    return EvaluationProfile(
        dimensions=("correctness",),
        required_dimensions=("correctness",),
        minimum_scores={"correctness": 0.70},
        minimum_overall_score=0.75,
        max_revisions=max_revisions,
        max_verification_steps=max_verification_steps,
        **kwargs,
    )


def result(score: float | None, *, status: str = "pass", confidence: float = 1.0, issues=(), evidence=()) -> EvaluationResult:
    dimension = DimensionResult(score, confidence, status, "controlled invariant test")
    return EvaluationResult(Decision.ACCEPT, score, confidence, {"correctness": dimension}, issues=issues, evidence=evidence)


class SequencePrimary:
    provider = "custom-primary"
    model = "custom-model"

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def generate(self, contract: TaskContract, *, context: str | None = None) -> str:
        self.calls += 1
        return self.responses[min(self.calls - 1, len(self.responses) - 1)]


class SequenceSecondary:
    provider = "custom-secondary"
    model = "custom-evaluator"

    def __init__(self, results):
        self.results = list(results)
        self.calls = 0

    def evaluate_candidate(self, contract, response, profile):
        value = self.results[min(self.calls, len(self.results) - 1)]
        self.calls += 1
        return value


class CapturingEngine:
    def __init__(self):
        self.primary = None
        self.secondary = None

    def run(self, contract, *, primary=None, secondary=None):
        self.primary = primary
        self.secondary = secondary
        version = Version("v0", "ok", result(0.9))
        return EngineResult(Decision.ACCEPT, version, (version,), contract, profile())


class FoundationInvariantTests(unittest.TestCase):
    def test_intent_is_authoritative_in_auto(self):
        contract = TaskContract(goal="Return exactly three bullet points", requirements=("Use only the supplied facts",), mode=Mode.AUTO)
        selected = build_profile(contract)
        self.assertEqual(contract.goal, "Return exactly three bullet points")
        self.assertEqual(contract.requirements, ("Use only the supplied facts",))
        self.assertEqual(selected.evaluation_effort, "medium")

    def test_missing_context_causes_ask(self):
        contract = TaskContract(goal="Answer the question", missing_context=("the source document",))
        decided = decide(contract, profile(), result(0.99), revisions_used=0)
        self.assertEqual(decided.decision, Decision.ASK)

    def test_unknown_never_accepts(self):
        decided = decide(TaskContract(goal="x"), profile(), result(None, status="unknown", confidence=0.95), revisions_used=0)
        self.assertEqual(decided.decision, Decision.ASK)

    def test_deterministic_failure_has_precedence(self):
        evidence = (
            Evidence("secondary", "llm", "pass", 1.0),
            Evidence("arithmetic", "deterministic", "fail", 1.0),
        )
        decided = decide(TaskContract(goal="calculate"), profile(max_revisions=0), result(0.99, evidence=evidence), revisions_used=0)
        self.assertEqual(decided.decision, Decision.ASK)

    def test_hard_gate_cannot_be_overridden(self):
        issue = Issue("safety", Severity.INFORMATIONAL, "blocked", "answer")
        decided = decide(TaskContract(goal="x"), profile(hard_gates=("safety",)), result(0.99, issues=(issue,)), revisions_used=0)
        self.assertEqual(decided.decision, Decision.REVISE)

    def test_required_evidence_cannot_be_satisfied_by_failure(self):
        evidence = (Evidence("arithmetic", "deterministic", "fail", 1.0),)
        decided = decide(TaskContract(goal="x"), profile(evidence_requirements=("arithmetic",)), result(0.99, evidence=evidence), revisions_used=0)
        self.assertEqual(decided.decision, Decision.REVISE)

    def test_regression_cannot_replace_best_version(self):
        primary = SequencePrimary(("good", "regressed"))
        secondary = SequenceSecondary((result(0.80), result(0.90, issues=(Issue("accuracy", Severity.MAJOR, "new error"),))))
        engine = Engine(primary, secondary=secondary)
        output = engine.run(TaskContract(goal="x"), profile=profile(max_revisions=1))
        self.assertEqual(output.decision, Decision.ASK)
        self.assertEqual(output.final_version.id, "v0")
        self.assertEqual(output.final_version.evaluation.overall_score, 0.80)

    def test_unchanged_revision_cannot_pass_absolute_threshold(self):
        assessment = RevisionAssessment(0.70, 0.80, 0.10, status="unchanged")
        decided = decide(TaskContract(goal="x"), profile(max_revisions=0), result(0.80), revisions_used=0, revision_assessment=assessment)
        self.assertEqual(decided.decision, Decision.ASK)

    def test_revision_budget_is_bounded(self):
        primary = SequencePrimary(("first", "second", "third"))
        secondary = SequenceSecondary((result(0.50), result(0.50), result(0.50)))
        engine = Engine(primary, secondary=secondary)
        output = engine.run(TaskContract(goal="x"), profile(max_revisions=1))
        self.assertEqual(primary.calls, 2)
        self.assertEqual(len(output.versions), 2)
        self.assertEqual(output.decision, Decision.ASK)

    def test_verification_budget_is_bounded(self):
        contract = TaskContract(goal="calculate 25 * 17")
        primary = SequencePrimary(("426",))
        secondary = SequenceSecondary((result(0.99),))
        engine = Engine(primary, secondary=secondary)
        output = engine.run(contract, profile(max_revisions=0, max_verification_steps=0))
        verifier_events = [event for event in output.trace if event.stage == "verifier"]
        self.assertFalse(verifier_events)
        self.assertEqual(output.decision, Decision.ACCEPT)

    def test_roles_are_provider_agnostic(self):
        primary = FunctionPrimary(lambda contract, context: "answer")
        primary.provider = "provider-a"
        primary.model = "model-a"
        secondary = SequenceSecondary((result(0.90),))
        secondary.provider = "provider-b"
        secondary.model = "model-b"
        output = Engine(primary, secondary=secondary).run(TaskContract(goal="x"), profile=profile(max_revisions=0))
        self.assertEqual(output.decision, Decision.ACCEPT)
        self.assertEqual(output.trace[2].details["provider"], "provider-a")

    def test_explicit_model_selection_is_preserved(self):
        created = []

        def factory(model):
            item = FunctionPrimary(lambda contract, context: "answer")
            item.provider = "test-provider"
            item.model = model
            created.append(item)
            return item

        router = ModelRouter({"test-provider": factory}, default=ModelSelection("test-provider", "default-model"))
        selected = router.selection(ModelSelection("test-provider", "explicit-model"))
        resolved = router.resolve(selected)
        self.assertEqual(selected.provider, "test-provider")
        self.assertEqual(selected.model, "explicit-model")
        self.assertEqual(resolved.model, "explicit-model")

    def test_service_preserves_explicit_primary_selection(self):
        engine = CapturingEngine()
        router = ModelRouter({"test-provider": lambda model: FunctionPrimary(lambda contract, context: "answer")}, default=ModelSelection("test-provider", "default"))
        service = EngineService(engine, primary_router=router)
        service.handle(EngineRequest(prompt="hello", primary_model=ModelSelection("test-provider", "explicit")))
        self.assertEqual(engine.primary.model, "explicit")


if __name__ == "__main__":
    unittest.main()
