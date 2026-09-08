import unittest

from engine.engine import EngineResult
from engine.execution import TraceEvent
from engine.revise.models import Decision, EvaluationProfile, Mode, TaskContract, Version
from engine.service import EngineRequest, EngineService


class _FakeEngine:
    def run(self, contract, *, primary, secondary):
        return EngineResult(
            decision=Decision.ACCEPT,
            final_version=Version("v0", "generated answer"),
            versions=(Version("v0", "generated answer"),),
            task_contract=contract,
            evaluation_profile=EvaluationProfile(dimensions=("correctness",)),
            trace=(
                TraceEvent("2026-01-01T00:00:00+00:00", "request", "received", {"mode": "basic"}),
                TraceEvent("2026-01-01T00:00:00+00:00", "primary", "complete", {"provider": "test", "model": "test-model"}),
            ),
        )


class DevelopmentTraceTests(unittest.TestCase):
    def test_trace_response_is_additive_and_safe(self):
        service = EngineService(_FakeEngine())
        response = service.handle_trace_payload({"prompt": "test prompt"})

        self.assertEqual(response["text"], "generated answer")
        self.assertEqual(response["decision"], "accept")
        self.assertEqual(response["version_id"], "v0")
        self.assertEqual(len(response["trace"]), 2)
        self.assertEqual(response["trace"][0]["stage"], "request")
        self.assertNotIn("generated answer", str(response["trace"]))
        self.assertNotIn("test prompt", str(response["trace"]))

    def test_normal_response_remains_unchanged(self):
        service = EngineService(_FakeEngine())
        response = service.handle(EngineRequest(prompt="test prompt"))

        self.assertEqual(response.to_dict(), {"text": "generated answer", "decision": "accept", "version_id": "v0"})
        self.assertNotIn("trace", response.to_dict())


if __name__ == "__main__":
    unittest.main()
