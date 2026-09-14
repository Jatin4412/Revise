from __future__ import annotations

import unittest

from .engine import Engine
from .revise.diagnosis import CorrectionRecommendation
from .revise.models import Decision, DimensionResult, EvaluationProfile, EvaluationResult, Evidence, Issue, Severity, TaskContract


class ScriptedPrimary:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.calls: list[str | None] = []

    def generate(self, contract: TaskContract, *, context: str | None = None) -> str:
        self.calls.append(context)
        return self.responses[len(self.calls) - 1]


class ScriptedSecondary:
    def __init__(self, results: list[EvaluationResult]) -> None:
        self.results = results
        self.calls = 0

    def evaluate_candidate(self, contract: TaskContract, response: str, profile: EvaluationProfile) -> EvaluationResult:
        result = self.results[self.calls]
        self.calls += 1
        return result


def profile(*, max_revisions: int = 1, stopping_conditions: tuple[str, ...] = ()) -> EvaluationProfile:
    return EvaluationProfile(
        dimensions=("correctness",),
        required_dimensions=("correctness",),
        minimum_scores={"correctness": 0.70},
        minimum_overall_score=0.75,
        minimum_confidence=0.60,
        max_revisions=max_revisions,
        max_verification_steps=0,
        stopping_conditions=stopping_conditions,
    )


def result(score: float, *, status: str = "pass", evidence: tuple[Evidence, ...] = (), issues: tuple[Issue, ...] = ()) -> EvaluationResult:
    return EvaluationResult(
        Decision.ACCEPT if status == "pass" and not issues else Decision.REVISE,
        score,
        0.95,
        {"correctness": DimensionResult(score, 0.95, status, "scripted")},
        issues,
        evidence,
    )


class PhaseFSelfCorrectionTests(unittest.TestCase):
    def test_change_approach_produces_new_approach_and_can_accept(self) -> None:
        primary = ScriptedPrimary(["failed method", "different successful method"])
        secondary = ScriptedSecondary([
            result(0.80, status="pass", evidence=(Evidence("checker", "deterministic", "fail", 1.0),)),
            result(0.95, status="pass", evidence=(Evidence("checker", "deterministic", "pass", 1.0),)),
        ])
        engine = Engine(primary, secondary=secondary)

        outcome = engine.run(TaskContract(goal="solve the task"), profile=profile())

        self.assertEqual(outcome.decision, Decision.ACCEPT)
        self.assertEqual(len(outcome.versions), 2)
        self.assertEqual(outcome.versions[0].metadata["approach_id"], "approach-0")
        self.assertEqual(outcome.versions[1].metadata["approach_id"], "approach-1")
        self.assertTrue(outcome.versions[1].metadata["approach_changed"])
        self.assertIn("materially different solution approach", primary.calls[1] or "")
        diagnosis_events = [e for e in outcome.trace if e.stage == "diagnosis"]
        self.assertEqual(diagnosis_events[0].status, "change_approach")

    def test_worse_changed_approach_is_regression_and_does_not_replace_previous(self) -> None:
        primary = ScriptedPrimary(["first attempt", "worse different attempt"])
        secondary = ScriptedSecondary([
            result(0.80, status="partial", issues=(Issue("quality", Severity.MODERATE, "needs work"),)),
            result(0.70, status="fail", issues=(Issue("quality", Severity.MAJOR, "worse"),)),
        ])
        engine = Engine(primary, secondary=secondary)

        outcome = engine.run(TaskContract(goal="solve the task"), profile=profile())

        self.assertEqual(outcome.decision, Decision.ASK)
        self.assertIsNone(outcome.final_version)
        self.assertEqual(len(outcome.versions), 2)
        self.assertEqual(outcome.versions[0].metadata["approach_id"], "approach-0")
        self.assertEqual(outcome.versions[1].metadata["approach_id"], "approach-0")
        self.assertEqual(outcome.versions[1].metadata["revision_assessment"].status, "regressed")

    def test_repeated_failure_stops_without_infinite_correction(self) -> None:
        primary = ScriptedPrimary(["same failure", "same failure", "same failure"])
        issue = Issue("quality", Severity.MODERATE, "still wrong")
        secondary = ScriptedSecondary([result(0.60, status="fail", issues=(issue,))] * 3)
        engine = Engine(primary, secondary=secondary)

        outcome = engine.run(TaskContract(goal="solve the task"), profile=profile(max_revisions=2, stopping_conditions=("stop_on_no_improvement",)))

        self.assertEqual(outcome.decision, Decision.ASK)
        self.assertEqual(len(outcome.versions), 2)
        self.assertIsNone(outcome.final_version)

    def test_diagnosis_accept_candidate_does_not_override_authoritative_failure(self) -> None:
        primary = ScriptedPrimary(["answer"])
        secondary = ScriptedSecondary([result(0.95, evidence=(Evidence("checker", "deterministic", "fail", 1.0),))])
        engine = Engine(primary, secondary=secondary)

        outcome = engine.run(TaskContract(goal="solve the task"), profile=profile(max_revisions=0))

        self.assertEqual(outcome.decision, Decision.ASK)
        self.assertIsNone(outcome.final_version)
        self.assertEqual(outcome.versions[0].metadata["diagnosis"].recommended_correction, CorrectionRecommendation.CHANGE_APPROACH)


if __name__ == "__main__":
    unittest.main()
