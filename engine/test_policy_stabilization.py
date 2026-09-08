import math
import unittest

from engine.engine import Engine
from engine.revise.decision import decide
from engine.revise.evaluator import validate_evaluation_result
from engine.revise.models import Decision, DimensionResult, EvaluationProfile, EvaluationResult, Evidence, Issue, Severity, TaskContract, Version
from engine.revise.verifiers import run_deterministic_verifiers


class FakePrimary:
    provider = "fake"
    model = "test"

    def __init__(self, responses): self.responses = iter(responses)
    def generate(self, contract, *, context=None):
        del contract, context
        return next(self.responses)


class FakeSecondary:
    provider = "fake"
    model = "judge"

    def __init__(self, scores): self.scores = iter(scores)
    def evaluate_candidate(self, contract, response, profile):
        del contract, response
        score = next(self.scores)
        return EvaluationResult(Decision.ACCEPT, score, 1.0, {profile.dimensions[0]: DimensionResult(score, 1.0, "pass")})


class PolicyStabilizationTests(unittest.TestCase):
    def test_evidence_requirement_blocks_acceptance(self):
        profile = EvaluationProfile(dimensions=("correctness",), required_dimensions=("correctness",), minimum_scores={"correctness": 0.7}, evidence_requirements=("deterministic",), minimum_overall_score=0.7)
        result = EvaluationResult(Decision.ACCEPT, 0.95, 1.0, {"correctness": DimensionResult(0.95, 1.0, "pass")}, evidence=(Evidence("secondary", "llm", "pass", 1.0),))
        self.assertEqual(decide(TaskContract(goal="x"), profile, result, revisions_used=0).decision, Decision.REVISE)

    def test_evidence_requirement_accepts_matching_pass(self):
        profile = EvaluationProfile(dimensions=("correctness",), required_dimensions=("correctness",), minimum_scores={"correctness": 0.7}, evidence_requirements=("deterministic",), minimum_overall_score=0.7)
        result = EvaluationResult(Decision.ACCEPT, 0.95, 1.0, {"correctness": DimensionResult(0.95, 1.0, "pass")}, evidence=(Evidence("deterministic.arithmetic", "deterministic", "pass", 1.0),))
        self.assertEqual(decide(TaskContract(goal="x"), profile, result, revisions_used=0).decision, Decision.ACCEPT)

    def test_malformed_dimension_fails_closed(self):
        profile = EvaluationProfile(dimensions=("correctness",))
        result = EvaluationResult(Decision.ACCEPT, 0.9, 1.0, {"correctness": DimensionResult(2.0, 1.0, "pass")})
        normalized = validate_evaluation_result(result, profile)
        self.assertEqual(normalized.decision, Decision.ASK)
        self.assertEqual(normalized.dimensions["correctness"].status, "unknown")

    def test_missing_dimension_fails_closed(self):
        profile = EvaluationProfile(dimensions=("correctness", "relevance"))
        result = EvaluationResult(Decision.ACCEPT, 0.9, 1.0, {"correctness": DimensionResult(0.9, 1.0, "pass")})
        normalized = validate_evaluation_result(result, profile)
        self.assertEqual(normalized.decision, Decision.ASK)
        self.assertEqual(normalized.dimensions["relevance"].status, "unknown")

    def test_non_finite_result_fails_closed(self):
        profile = EvaluationProfile(dimensions=("correctness",))
        result = EvaluationResult(Decision.ACCEPT, math.nan, math.inf, {"correctness": DimensionResult(0.9, 1.0, "pass")})
        normalized = validate_evaluation_result(result, profile)
        self.assertEqual(normalized.decision, Decision.ASK)
        self.assertEqual(normalized.confidence, 0.0)

    def test_verification_budget_fails_closed_for_unrun_deterministic_check(self):
        profile = EvaluationProfile(dimensions=("correctness",), deterministic_checks=("arithmetic", "json"), max_verification_steps=1)
        evidence = run_deterministic_verifiers(TaskContract(goal="calculate 2 + 2"), "4", profile)
        self.assertTrue(any(item.result == "fail" and "verification_budget_exhausted" in item.provenance for item in evidence))

    def test_hard_gate_blocks_even_when_issue_is_minor(self):
        profile = EvaluationProfile(dimensions=("correctness",), required_dimensions=("correctness",), minimum_scores={"correctness": 0.7}, hard_gates=("blocked_claim",), minimum_overall_score=0.7)
        result = EvaluationResult(Decision.ACCEPT, 0.95, 1.0, {"correctness": DimensionResult(0.95, 1.0, "pass")}, issues=(Issue("blocked_claim", Severity.MINOR, "blocked"),))
        self.assertEqual(decide(TaskContract(goal="x"), profile, result, revisions_used=0).decision, Decision.REVISE)

    def test_stop_on_no_improvement_ends_revision_loop(self):
        profile = EvaluationProfile(dimensions=("correctness",), required_dimensions=("correctness",), minimum_scores={"correctness": 0.7}, minimum_overall_score=0.7, max_revisions=3, stopping_conditions=("stop_on_no_improvement",))
        engine = Engine(FakePrimary(["first", "second", "third"]), secondary=FakeSecondary([0.6, 0.6, 0.6]))
        result = engine.run(TaskContract(goal="x"), profile=profile)
        self.assertEqual(result.decision, Decision.ASK)
        self.assertEqual(len(result.versions), 2)

    def test_best_version_excludes_regressed_revision(self):
        baseline = Version("v0", "good", EvaluationResult(Decision.ACCEPT, 0.9, 0.9, {"correctness": DimensionResult(0.9, 0.9, "pass")}))
        bad_eval = EvaluationResult(Decision.ACCEPT, 0.95, 0.95, {"correctness": DimensionResult(0.95, 0.95, "pass")})
        assessment = type("Assessment", (), {"status": "regressed"})()
        bad = Version("v1", "bad", bad_eval, parent_id="v0", metadata={"revision_assessment": assessment})
        selected = Engine._best_version([baseline, bad])
        self.assertEqual(selected.id, "v0")


if __name__ == "__main__": unittest.main()
