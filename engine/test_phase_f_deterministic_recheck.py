from __future__ import annotations

import unittest

from .engine import Engine
from .revise.models import Decision, DimensionResult, EvaluationProfile, EvaluationResult, TaskContract


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
    def __init__(self) -> None:
        self.calls = 0

    def evaluate_candidate(self, contract: TaskContract, response: str, profile: EvaluationProfile) -> EvaluationResult:
        del contract, response, profile
        self.calls += 1
        return EvaluationResult(
            Decision.ACCEPT,
            0.95 if self.calls == 2 else 0.80,
            0.95,
            {"correctness": DimensionResult(0.95 if self.calls == 2 else 0.80, 0.95, "pass", "scripted")},
        )


class PhaseFDeterministicRecheckTests(unittest.TestCase):
    def test_changed_approach_must_pass_deterministic_verifier_again(self) -> None:
        primary = ScriptedPrimary(["5", "4"])
        secondary = ScriptedSecondary()
        profile = EvaluationProfile(
            dimensions=("correctness",),
            required_dimensions=("correctness",),
            minimum_scores={"correctness": 0.70},
            minimum_overall_score=0.75,
            minimum_confidence=0.60,
            deterministic_checks=("arithmetic",),
            max_revisions=1,
            max_verification_steps=1,
        )

        outcome = Engine(primary, secondary=secondary).run(
            TaskContract(goal="What is 2 + 2?"),
            profile=profile,
        )

        self.assertEqual(outcome.decision, Decision.ACCEPT)
        self.assertEqual(len(outcome.versions), 2)
        self.assertEqual(outcome.versions[0].response, "5")
        self.assertEqual(outcome.versions[1].response, "4")
        self.assertEqual(outcome.versions[0].metadata["approach_id"], "approach-0")
        self.assertEqual(outcome.versions[1].metadata["approach_id"], "approach-1")
        self.assertEqual(
            [e.result for e in outcome.versions[0].evaluation.evidence if e.method == "deterministic"],
            ["fail"],
        )
        self.assertEqual(
            [e.result for e in outcome.versions[1].evaluation.evidence if e.method == "deterministic"],
            ["pass"],
        )
        self.assertEqual(secondary.calls, 2)


if __name__ == "__main__":
    unittest.main()
