from __future__ import annotations

import unittest

from engine import Engine
from engine.revise.models import DimensionResult, EvaluationProfile, TaskContract


class SequencePrimary:
    def __init__(self) -> None:
        self.responses = iter(("incomplete", "complete answer"))

    def generate(self, contract: TaskContract, *, context: str | None = None) -> str:
        return next(self.responses)


class RevisionSecondary:
    def evaluators(self, contract: TaskContract, profile: EvaluationProfile):
        def task_completion(_contract: TaskContract, response: str) -> DimensionResult:
            if response == "complete answer":
                return DimensionResult(1.0, 1.0, "pass", "complete")
            return DimensionResult(0.2, 1.0, "fail", "incomplete")

        return {"task_completion": task_completion}


class RevisionTraceTests(unittest.TestCase):
    def test_revision_assessment_trace_does_not_collide_with_event_status(self) -> None:
        result = Engine(SequencePrimary(), secondary=RevisionSecondary()).run(
            TaskContract(goal="complete the task"),
            profile=EvaluationProfile(
                dimensions=("task_completion",),
                minimum_scores={"task_completion": 0.70},
                max_revisions=1,
            ),
        )

        self.assertEqual(result.decision.value, "accept")
        assessed = [event for event in result.trace if event.stage == "revision" and event.status == "assessed"]
        self.assertEqual(len(assessed), 1)
        self.assertEqual(assessed[0].details["revision_status"], "improved")


if __name__ == "__main__":
    unittest.main()
