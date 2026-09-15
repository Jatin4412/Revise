from __future__ import annotations

import json
import unittest

from engine.engine import Engine
from engine.providers import FunctionPrimary
from engine.revise.deliberation import DeliberationLimits, run_deliberation
from engine.revise.models import Decision, DimensionResult, EvaluationProfile, EvaluationResult, Mode, TaskContract
from engine.revise.profile import build_profile


class ScriptedDeliberativePrimary:
    provider = "fake"
    model = "deliberative-test"

    def __init__(self, *, reflection_sets: list[dict], corrected_candidate: str = "corrected answer", initial_candidate: str = "initial answer", second_candidate: str | None = None, malformed_stage: str | None = None) -> None:
        self.reflection_sets = iter(reflection_sets)
        self.corrected_candidate = corrected_candidate
        self.initial_candidate = initial_candidate
        self.second_candidate = second_candidate or corrected_candidate
        self.malformed_stage = malformed_stage
        self.calls: list[str] = []

    def generate(self, contract: TaskContract, *, context: str | None = None) -> str:
        self.calls.append("generate")
        return self.initial_candidate

    def deliberate(self, contract: TaskContract, prompt: str) -> str:
        del contract
        lowered = prompt.lower()
        if "correction-planning role" in lowered:
            stage = "correct"
            payload = {"problem": "the current approach relies on an unsupported assumption", "objective": "rebuild the answer without that assumption", "required_change": "replace the unsupported step with a task-grounded inference", "approach": "rebuild from explicit requirements", "change_approach": True}
        elif "planning role" in lowered:
            stage = "plan"
            payload = {"approach": "use the task requirements directly", "subproblems": [], "assumptions": [], "open_questions": []}
        elif "reasoning role" in lowered:
            stage = "re_reason" if "targeted correction plan" in lowered else "reason"
            candidate = self.second_candidate if stage == "re_reason" else self.initial_candidate
            payload = {"candidate": candidate, "assumptions": [], "open_questions": []}
        elif "adversarial reflection role" in lowered:
            stage = "reflect"
            try:
                payload = next(self.reflection_sets)
            except StopIteration:
                payload = {"concerns": [], "confidence": 0.9, "actionable": False}
        else:
            stage = "unknown"
            payload = {}
        self.calls.append(stage)
        if stage == self.malformed_stage:
            return "not valid json"
        return json.dumps(payload)


class ScoreSecondary:
    def evaluate_candidate(self, contract: TaskContract, response: str, profile: EvaluationProfile) -> EvaluationResult:
        del contract
        good = "corrected" in response.lower() or "robust" in response.lower()
        score = 1.0 if good else 0.2
        status = "pass" if good else "fail"
        return EvaluationResult(
            Decision.ACCEPT,
            score,
            1.0,
            {name: DimensionResult(score, 1.0, status, "scripted") for name in profile.dimensions},
        )


class DeliberationTests(unittest.TestCase):
    def _profile(self, **overrides) -> EvaluationProfile:
        values = {
            "dimensions": ("correctness",),
            "required_dimensions": ("correctness",),
            "minimum_scores": {"correctness": 0.70},
            "minimum_overall_score": 0.70,
            "max_revisions": 0,
            "max_deliberation_cycles": 2,
            "max_correction_attempts": 1,
        }
        values.update(overrides)
        return EvaluationProfile(**values)

    @staticmethod
    def _concern(kind: str, description: str) -> dict:
        return {
            "concerns": [{"kind": kind, "description": description, "severity": "major"}],
            "challenged_assumptions": [description],
            "missing_steps": [],
            "contradictions": [],
            "alternative_interpretations": [],
            "alternative_approaches": [],
            "confidence": 0.9,
            "actionable": True,
        }

    def test_genuine_correction_reaches_re_reflection_and_evaluation(self) -> None:
        primary = ScriptedDeliberativePrimary(
            reflection_sets=[self._concern("hidden_assumption", "the answer assumes an unstated condition"), {"concerns": [], "confidence": 0.95, "actionable": False}],
            initial_candidate="initial answer",
            corrected_candidate="corrected answer",
        )
        result = Engine(primary, secondary=ScoreSecondary()).run(TaskContract(goal="solve the task"), profile=self._profile())
        self.assertEqual(result.decision, Decision.ACCEPT)
        self.assertEqual(result.final_version.response, "corrected answer")
        self.assertTrue(result.final_version.metadata["deliberation_corrected"])
        self.assertEqual(result.final_version.metadata["deliberation_correction_attempts"], 1)
        self.assertIn("reflect", primary.calls)
        self.assertIn("correct", primary.calls)
        self.assertIn("re_reason", primary.calls)
        self.assertEqual(primary.calls[-1], "reflect")

    def test_false_correction_is_not_accepted_blindly(self) -> None:
        primary = ScriptedDeliberativePrimary(
            reflection_sets=[self._concern("wrong_approach", "the proposed method is unsuitable"), self._concern("contradiction", "the correction now conflicts with a requirement")],
            initial_candidate="initial answer",
            corrected_candidate="wrong correction",
        )
        result = Engine(primary, secondary=ScoreSecondary()).run(TaskContract(goal="follow the requirement"), profile=self._profile())
        self.assertEqual(result.decision, Decision.ASK)
        self.assertEqual(result.final_version.response, "wrong correction")
        self.assertEqual(result.final_version.metadata["deliberation_stop_reason"], "correction_budget_exhausted")
        self.assertEqual(len(result.versions), 1)

    def test_reflection_cannot_authorize_acceptance(self) -> None:
        reflection = self._concern("other", "possible issue")
        reflection["actionable"] = False
        reflection["decision"] = "ACCEPT"
        primary = ScriptedDeliberativePrimary(reflection_sets=[reflection], initial_candidate="initial answer")
        result = Engine(primary, secondary=ScoreSecondary()).run(TaskContract(goal="task"), profile=self._profile(max_correction_attempts=0))
        self.assertEqual(result.decision, Decision.ASK)
        self.assertEqual(result.final_version.response, "initial answer")

    def test_malformed_reflection_falls_back_to_current_candidate(self) -> None:
        primary = ScriptedDeliberativePrimary(reflection_sets=[], malformed_stage="reflect", initial_candidate="corrected answer")
        result = Engine(primary, secondary=ScoreSecondary()).run(TaskContract(goal="task"), profile=self._profile())
        self.assertEqual(result.decision, Decision.ACCEPT)
        self.assertEqual(result.final_version.response, "corrected answer")
        self.assertEqual(result.final_version.metadata["deliberation_stop_reason"], "reflection_failed")

    def test_deliberation_is_bounded_by_cycles_and_corrections(self) -> None:
        primary = ScriptedDeliberativePrimary(
            reflection_sets=[self._concern("self_reinforcing_error", "the conclusion is being used as its own support"), self._concern("missing_inference", "a required inference is still absent")],
            initial_candidate="initial answer",
            corrected_candidate="corrected answer",
        )
        result = Engine(primary, secondary=ScoreSecondary()).run(TaskContract(goal="task"), profile=self._profile(max_deliberation_cycles=2, max_correction_attempts=1))
        self.assertEqual(result.decision, Decision.ACCEPT)
        self.assertEqual(result.final_version.metadata["deliberation_stop_reason"], "correction_budget_exhausted")
        self.assertEqual(result.final_version.metadata["deliberation_correction_attempts"], 1)

    def test_contract_remains_immutable_through_correction(self) -> None:
        contract = TaskContract(goal="original goal", requirements=("must keep this requirement",), constraints=("must not change task",))
        primary = ScriptedDeliberativePrimary(
            reflection_sets=[self._concern("ambiguity", "the task could be interpreted in two ways"), {"concerns": [], "confidence": 0.9, "actionable": False}],
        )
        result = Engine(primary, secondary=ScoreSecondary()).run(contract, profile=self._profile())
        self.assertEqual(result.task_contract, contract)
        self.assertEqual(result.task_contract.goal, "original goal")
        self.assertEqual(result.task_contract.requirements, ("must keep this requirement",))

    def test_reasoning_failure_categories_are_structured(self) -> None:
        categories = [
            ("hidden_assumption", "an assumption is unstated"),
            ("wrong_approach", "the method is inappropriate"),
            ("missing_inference", "a necessary step is missing"),
            ("ambiguity", "two interpretations remain plausible"),
            ("self_reinforcing_error", "the conclusion is being used as evidence"),
        ]
        for kind, description in categories:
            with self.subTest(kind=kind):
                primary = ScriptedDeliberativePrimary(reflection_sets=[self._concern(kind, description)], initial_candidate="initial answer")
                result = run_deliberation(TaskContract(goal="task"), primary, limits=DeliberationLimits(1, 0))
                self.assertEqual(result.reflections[0].concerns[0].kind, kind)
                self.assertTrue(result.reflections[0].actionable)

    def test_no_concern_does_not_manufacture_a_correction(self) -> None:
        primary = ScriptedDeliberativePrimary(reflection_sets=[{"concerns": [], "confidence": 0.95, "actionable": False}], initial_candidate="robust answer")
        result = Engine(primary, secondary=ScoreSecondary()).run(TaskContract(goal="easy task"), profile=self._profile(max_correction_attempts=1))
        self.assertEqual(result.decision, Decision.ACCEPT)
        self.assertFalse(result.final_version.metadata["deliberation_corrected"])
        self.assertEqual(result.final_version.metadata["deliberation_stop_reason"], "no_actionable_concern")
        self.assertNotIn("correct", primary.calls)

    def test_legacy_primary_without_deliberate_method_remains_compatible(self) -> None:
        primary = FunctionPrimary(lambda contract, context: "legacy response")
        result = Engine(primary).run(TaskContract(goal="task"), profile=self._profile())
        self.assertEqual(result.decision, Decision.ASK)
        self.assertEqual(result.final_version.response, "legacy response")
        self.assertEqual(result.final_version.metadata["deliberation_stop_reason"], "disabled")

    def test_profile_deliberation_budget_is_not_verification_budget(self) -> None:
        profile = build_profile(TaskContract(goal="reason about an architecture", mode=Mode.BASIC))
        self.assertEqual(profile.max_deliberation_cycles, 2)
        self.assertEqual(profile.max_correction_attempts, 1)
        self.assertEqual(profile.max_verification_steps, 2)
        custom = EvaluationProfile(dimensions=("correctness",), max_deliberation_cycles=3, max_correction_attempts=2, max_verification_steps=1)
        self.assertEqual(custom.max_deliberation_cycles, 3)
        self.assertEqual(custom.max_verification_steps, 1)


if __name__ == "__main__":
    unittest.main()
