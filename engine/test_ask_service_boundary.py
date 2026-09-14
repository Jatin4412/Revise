from __future__ import annotations

import unittest

from engine import Engine, EngineService, FunctionPrimary
from engine.revise.models import Decision, DimensionResult, EvaluationProfile, TaskContract


class RejectingSecondary:
    def evaluators(self, contract: TaskContract, profile: EvaluationProfile):
        return {
            name: lambda _contract, _response: DimensionResult(
                0.0,
                1.0,
                "fail",
                "candidate does not answer the task",
            )
            for name in profile.dimensions
        }


class AskServiceBoundaryTests(unittest.TestCase):
    def test_http_response_does_not_expose_rejected_candidate(self) -> None:
        service = EngineService(
            Engine(
                FunctionPrimary(lambda _contract, _context: "User Safety: safe"),
                secondary=RejectingSecondary(),
            )
        )

        response = service.handle_payload(
            {
                "prompt": "answer the user's task",
                "mode": "basic",
            }
        )

        self.assertEqual(response["decision"], Decision.ASK.value)
        self.assertEqual(response["text"], "")
        self.assertIsNone(response["version_id"])

    def test_trace_keeps_rejected_candidate_internal_only(self) -> None:
        service = EngineService(
            Engine(
                FunctionPrimary(lambda _contract, _context: "User Safety: safe"),
                secondary=RejectingSecondary(),
            )
        )

        response = service.handle_trace_payload(
            {
                "prompt": "answer the user's task",
                "mode": "basic",
            }
        )

        self.assertEqual(response["decision"], Decision.ASK.value)
        self.assertEqual(response["text"], "")
        self.assertIsNone(response["version_id"])
        self.assertNotIn("User Safety: safe", repr(response))
        self.assertIsInstance(response["trace"], list)


if __name__ == "__main__":
    unittest.main()
