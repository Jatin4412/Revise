from __future__ import annotations

import unittest

from engine import Engine, FunctionPrimary
from engine.revise.models import Decision, DimensionResult, EvaluationProfile, TaskContract


class RejectingSecondary:
    def evaluators(self, contract: TaskContract, profile: EvaluationProfile):
        return {
            name: lambda _contract, _response: DimensionResult(
                0.0, 1.0, "fail", "candidate does not answer the task"
            )
            for name in profile.dimensions
        }


class PassingSecondary:
    def evaluators(self, contract: TaskContract, profile: EvaluationProfile):
        return {
            name: lambda _contract, _response: DimensionResult(
                1.0, 1.0, "pass", "candidate answers the task"
            )
            for name in profile.dimensions
        }


class AskCandidateBoundaryTests(unittest.TestCase):
    def test_ask_does_not_surface_rejected_candidate(self) -> None:
        result = Engine(
            FunctionPrimary(lambda _contract, _context: "User Safety: safe"),
            secondary=RejectingSecondary(),
        ).run(
            TaskContract(goal="answer the user's task"),
            profile=EvaluationProfile(
                dimensions=("task_completion",),
                required_dimensions=("task_completion",),
                max_revisions=0,
            ),
        )

        self.assertEqual(result.decision, Decision.ASK)
        self.assertIsNone(result.final_version)
        self.assertEqual(len(result.versions), 1)
        self.assertEqual(result.versions[0].response, "User Safety: safe")
        self.assertEqual(result.trace[-1].stage, "final")
        self.assertIsNone(result.trace[-1].details["version"])

    def test_accept_still_surfaces_accepted_candidate(self) -> None:
        result = Engine(
            FunctionPrimary(lambda _contract, _context: "actual answer"),
            secondary=PassingSecondary(),
        ).run(
            TaskContract(goal="answer the user's task"),
            profile=EvaluationProfile(
                dimensions=("task_completion",),
                required_dimensions=("task_completion",),
                max_revisions=0,
            ),
        )

        self.assertEqual(result.decision, Decision.ACCEPT)
        self.assertIsNotNone(result.final_version)
        self.assertEqual(result.final_version.response, "actual answer")


if __name__ == "__main__":
    unittest.main()
