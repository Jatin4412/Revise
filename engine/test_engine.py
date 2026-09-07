from __future__ import annotations

import unittest

from engine import Engine, EngineRequest, EngineService, FunctionPrimary
from engine.llm import LLMSecondary
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


if __name__ == "__main__":
    unittest.main()
