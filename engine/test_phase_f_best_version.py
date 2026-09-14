from __future__ import annotations

import unittest

from .engine import Engine
from .revise.models import Decision, DimensionResult, EvaluationProfile, EvaluationResult, Issue, Severity, TaskContract


class ScriptedPrimary:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.calls = 0

    def generate(self, contract: TaskContract, *, context: str | None = None) -> str:
        del contract, context
        response = self.responses[self.calls]
        self.calls += 1
        return response


class ScriptedSecondary:
    def __init__(self, results: list[EvaluationResult]) -> None:
        self.results = results
        self.calls = 0

    def evaluate_candidate(self, contract: TaskContract, response: str, profile: EvaluationProfile) -> EvaluationResult:
        del contract, response, profile
        result = self.results[self.calls]
        self.calls += 1
        return result


def profile() -> EvaluationProfile:
    return EvaluationProfile(
        dimensions=("correctness",),
        required_dimensions=("correctness",),
        minimum_scores={"correctness": 0.70},
        minimum_overall_score=0.95,
        minimum_confidence=0.60,
        max_revisions=2,
        max_verification_steps=0,
    )


def result(score: float, status: str, issue: Issue | None = None) -> EvaluationResult:
    return EvaluationResult(
        Decision.ACCEPT if status == "pass" and issue is None else Decision.REVISE,
        score,
        0.95,
        {"correctness": DimensionResult(score, 0.95, status, "scripted")},
        (issue,) if issue else (),
    )


class PhaseFBestVersionTests(unittest.TestCase):
    def test_rejected_later_revision_cannot_displace_best_valid_version(self) -> None:
        primary = ScriptedPrimary(["first valid attempt", "improved attempt", "worse attempt"])
        secondary = ScriptedSecondary([
            result(0.80, "partial", Issue("quality", Severity.MODERATE, "needs improvement")),
            result(0.90, "partial"),
            result(0.60, "fail", Issue("quality", Severity.MAJOR, "regressed")),
        ])

        outcome = Engine(primary, secondary=secondary).run(TaskContract(goal="solve the task"), profile=profile())

        self.assertEqual(outcome.decision, Decision.ASK)
        self.assertIsNone(outcome.final_version)
        self.assertEqual(len(outcome.versions), 3)
        self.assertEqual(outcome.versions[1].metadata["revision_assessment"].status, "improved")
        self.assertEqual(outcome.versions[2].metadata["revision_assessment"].status, "regressed")
        best = Engine._best_version(list(outcome.versions))
        self.assertIsNotNone(best)
        self.assertEqual(best.id, "v1")
        self.assertEqual(best.response, "improved attempt")

    def test_terminal_ask_does_not_expose_best_nonaccepted_candidate(self) -> None:
        primary = ScriptedPrimary(["weak attempt", "still weak"])
        secondary = ScriptedSecondary([
            result(0.60, "fail", Issue("quality", Severity.MODERATE, "wrong")),
            result(0.60, "fail", Issue("quality", Severity.MODERATE, "still wrong")),
        ])

        outcome = Engine(primary, secondary=secondary).run(TaskContract(goal="solve the task"), profile=profile())

        self.assertEqual(outcome.decision, Decision.ASK)
        self.assertIsNone(outcome.final_version)


if __name__ == "__main__":
    unittest.main()
