from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

from engine import Engine, EngineRequest, EngineService, FunctionPrimary
from engine.llm import LLMSecondary, _groq_callable
from engine.model import ModelRouter, ModelSelection, SecondaryRouter
from engine.revise.models import DimensionResult, EvaluationProfile, Mode, TaskContract


class SequencePrimary:
    def __init__(self, responses: list[str]) -> None:
        self.responses = iter(responses)
        self.contexts: list[str | None] = []

    def generate(self, contract: TaskContract, *, context: str | None = None) -> str:
        self.contexts.append(context)
        return next(self.responses)


class BasicSecondary:
    def evaluators(self, contract: TaskContract, profile: EvaluationProfile):
        def task_completion(contract: TaskContract, response: str) -> DimensionResult:
            if "complete" in response.lower():
                return DimensionResult(1.0, 1.0, "pass", "response completes the task")
            return DimensionResult(0.2, 1.0, "fail", "response is incomplete")

        return {"task_completion": task_completion}


class FakeHTTPResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps({"choices": [{"message": {"content": "hello"}}]}).encode("utf-8")


class EngineTests(unittest.TestCase):
    def test_missing_evaluation_does_not_pass(self) -> None:
        primary = FunctionPrimary(lambda contract, context: "hello")
        result = Engine(primary).run(TaskContract(goal="say hello"))

        self.assertEqual(result.decision.value, "ask")
        self.assertEqual(result.final_version.response, "hello")
        self.assertEqual(len(result.versions), 1)

    def test_revision_context_reaches_primary(self) -> None:
        primary = SequencePrimary(["incomplete", "complete answer"])
        result = Engine(primary, secondary=BasicSecondary()).run(
            TaskContract(goal="complete the task"),
            profile=EvaluationProfile(
                dimensions=("task_completion",),
                max_revisions=1,
            ),
        )

        self.assertEqual(result.decision.value, "accept")
        self.assertEqual(result.final_version.response, "complete answer")
        self.assertEqual(len(result.versions), 2)
        self.assertIn("incomplete", primary.contexts[1])
        self.assertIn("response is incomplete", primary.contexts[1])

    def test_trace_records_revision_and_final_decision(self) -> None:
        primary = SequencePrimary(["incomplete", "complete answer"])
        result = Engine(primary, secondary=BasicSecondary()).run(
            TaskContract(goal="complete the task"),
            profile=EvaluationProfile(dimensions=("task_completion",), max_revisions=1),
        )

        events = [(event.stage, event.status) for event in result.trace]
        self.assertIn(("primary", "start"), events)
        self.assertIn(("primary", "complete"), events)
        self.assertIn(("secondary", "start"), events)
        self.assertIn(("evaluation", "dimension"), events)
        self.assertIn(("decision", "revise"), events)
        self.assertIn(("revision", "requested"), events)
        self.assertIn(("decision", "accept"), events)
        self.assertEqual(result.trace[-1].stage, "final")
        self.assertEqual(result.trace[-1].status, "selected")

    def test_trace_does_not_contain_response_payload(self) -> None:
        primary = FunctionPrimary(lambda contract, context: "SECRET_RESPONSE_SHOULD_NOT_BE_IN_TRACE")
        result = Engine(primary).run(TaskContract(goal="say hello"))
        trace_text = repr(result.trace)
        self.assertNotIn("SECRET_RESPONSE_SHOULD_NOT_BE_IN_TRACE", trace_text)

    def test_service_rejects_empty_prompt(self) -> None:
        service = EngineService(FunctionPrimary(lambda contract, context: "ok"))
        with self.assertRaises(ValueError):
            service.handle(EngineRequest(prompt="   ", mode=Mode.BASIC))

    def test_function_primary_adapter(self) -> None:
        seen: list[str] = []

        def generate(contract: TaskContract, context: str | None) -> str:
            seen.append(context or "none")
            return contract.goal

        class PassingSecondary:
            def evaluators(self, contract, profile):
                return {
                    name: lambda _contract, _response: DimensionResult(1.0, 1.0, "pass", "ok")
                    for name in profile.dimensions
                }

        service = EngineService(Engine(FunctionPrimary(generate), secondary=PassingSecondary()))
        response = service.handle(EngineRequest(prompt="test prompt"))

        self.assertEqual(response.text, "test prompt")
        self.assertEqual(response.version_id, "v0")
        self.assertEqual(seen, ["none"])

    def test_model_routers_are_role_independent(self) -> None:
        primary = ModelRouter({"fake": lambda model: ("primary", model)}, default=ModelSelection("fake", "strong"))
        secondary = SecondaryRouter({"fake": lambda model: ("secondary", model)}, default=ModelSelection("fake", "light"))

        self.assertEqual(primary.resolve().model, "strong")
        self.assertEqual(secondary.resolve().model, "light")

    def test_llm_secondary_parses_candidate_evaluation(self) -> None:
        seen: list[str] = []

        def generate(prompt: str) -> str:
            seen.append(prompt)
            return '{"dimensions":{"task_completion":{"score":1,"confidence":0.9,"status":"pass","reason":"complete"}},"issues":[],"revision":{"strategy":"none","instructions":[]}}'

        secondary = LLMSecondary(generate)
        result = secondary.evaluate_candidate(
            TaskContract(goal="do the task"),
            "candidate answer",
            EvaluationProfile(dimensions=("task_completion",)),
        )

        self.assertEqual(result.dimensions["task_completion"].status, "pass")
        self.assertIn("candidate answer", seen[0])

    def test_groq_request_uses_explicit_client_identity(self) -> None:
        previous = os.environ.get("GROQ_API_KEY")
        os.environ["GROQ_API_KEY"] = "test-key"
        captured = {}
        try:
            def fake_urlopen(req, timeout):
                captured["url"] = req.full_url
                captured["headers"] = dict(req.header_items())
                captured["timeout"] = timeout
                return FakeHTTPResponse()

            with patch("engine.llm.request.urlopen", fake_urlopen):
                result = _groq_callable("openai/gpt-oss-120b", role="primary")("hello")

            self.assertEqual(result, "hello")
            self.assertEqual(captured["url"], "https://api.groq.com/openai/v1/chat/completions")
            self.assertEqual(captured["headers"]["Authorization"], "Bearer test-key")
            self.assertEqual(captured["headers"]["User-agent"], "ReviseEngine/0.1")
            self.assertEqual(captured["timeout"], 60.0)
        finally:
            if previous is None:
                os.environ.pop("GROQ_API_KEY", None)
            else:
                os.environ["GROQ_API_KEY"] = previous


if __name__ == "__main__":
    unittest.main()
