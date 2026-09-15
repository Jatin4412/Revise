from __future__ import annotations

import unittest

from engine.llm import LLMPrimary, _evaluation_prompt, _generation_prompt
from engine.revise.models import Mode, TaskContract
from engine.revise.power import select_power_plan
from engine.revise.profile import build_profile


class PowerPlanTests(unittest.TestCase):
    def test_explicit_modes_have_distinct_effort(self) -> None:
        plans = {
            mode: select_power_plan(TaskContract(goal="Explain integration", mode=mode))
            for mode in (Mode.LITE, Mode.BASIC, Mode.PRO)
        }
        self.assertEqual(plans[Mode.LITE].effort, "low")
        self.assertEqual(plans[Mode.BASIC].effort, "medium")
        self.assertEqual(plans[Mode.PRO].effort, "high")
        self.assertEqual(len({plan.generation_guidance for plan in plans.values()}), 3)
        self.assertEqual(len({plan.evaluation_guidance for plan in plans.values()}), 3)

    def test_auto_uses_task_complexity(self) -> None:
        simple = select_power_plan(TaskContract(goal="What is photosynthesis?", mode=Mode.AUTO))
        standard = select_power_plan(TaskContract(goal="Compare photosynthesis and cellular respiration.", mode=Mode.AUTO))
        complex = select_power_plan(TaskContract(goal="Prove the equation and calculate 25 × 17, then explain the result.", mode=Mode.AUTO))
        self.assertEqual(simple.effort, "low")
        self.assertEqual(standard.effort, "medium")
        self.assertEqual(complex.effort, "high")

    def test_profile_budget_tracks_resolved_power(self) -> None:
        lite = build_profile(TaskContract(goal="Explain integration", mode=Mode.LITE))
        basic = build_profile(TaskContract(goal="Explain integration", mode=Mode.BASIC))
        pro = build_profile(TaskContract(goal="Explain integration", mode=Mode.PRO))
        auto_simple = build_profile(TaskContract(goal="What is photosynthesis?", mode=Mode.AUTO))
        auto_complex = build_profile(TaskContract(goal="Prove the equation and calculate 25 × 17.", mode=Mode.AUTO))
        self.assertEqual((lite.evaluation_effort, lite.max_revisions, lite.max_verification_steps), ("low", 0, 1))
        self.assertEqual((basic.evaluation_effort, basic.max_revisions, basic.max_verification_steps), ("medium", 1, 2))
        self.assertEqual((pro.evaluation_effort, pro.max_revisions, pro.max_verification_steps), ("high", 2, 4))
        self.assertEqual((auto_simple.evaluation_effort, auto_simple.max_revisions, auto_simple.max_verification_steps), ("low", 0, 1))
        self.assertEqual((auto_complex.evaluation_effort, auto_complex.max_revisions, auto_complex.max_verification_steps), ("high", 2, 4))


class PowerPromptTests(unittest.TestCase):
    def test_generation_prompt_carries_power_guidance(self) -> None:
        prompts = {
            mode: _generation_prompt(TaskContract(goal="Explain integration", mode=mode), None)
            for mode in (Mode.LITE, Mode.BASIC, Mode.PRO)
        }
        self.assertIn("Execution effort: low", prompts[Mode.LITE])
        self.assertIn("Execution effort: medium", prompts[Mode.BASIC])
        self.assertIn("Execution effort: high", prompts[Mode.PRO])
        self.assertNotEqual(prompts[Mode.LITE], prompts[Mode.PRO])

    def test_auto_generation_prompt_adapts(self) -> None:
        simple = _generation_prompt(TaskContract(goal="What is photosynthesis?", mode=Mode.AUTO), None)
        complex = _generation_prompt(TaskContract(goal="Prove the equation and calculate 25 × 17.", mode=Mode.AUTO), None)
        self.assertIn("Execution effort: low", simple)
        self.assertIn("Execution effort: high", complex)
        self.assertNotEqual(simple, complex)

    def test_evaluation_prompt_carries_power_guidance(self) -> None:
        lite_profile = build_profile(TaskContract(goal="Explain integration", mode=Mode.LITE))
        pro_profile = build_profile(TaskContract(goal="Explain integration", mode=Mode.PRO))
        lite_prompt = _evaluation_prompt(TaskContract(goal="Explain integration", mode=Mode.LITE), "candidate", lite_profile)
        pro_prompt = _evaluation_prompt(TaskContract(goal="Explain integration", mode=Mode.PRO), "candidate", pro_profile)
        self.assertIn("Evaluation effort: low", lite_prompt)
        self.assertIn("Evaluation effort: high", pro_prompt)
        self.assertNotEqual(lite_prompt, pro_prompt)

    def test_primary_adapter_uses_power_aware_prompt(self) -> None:
        captured: list[str] = []
        primary = LLMPrimary(lambda prompt: captured.append(prompt) or "answer")
        primary.generate(TaskContract(goal="Explain integration", mode=Mode.PRO))
        self.assertEqual(len(captured), 1)
        self.assertIn("Execution effort: high", captured[0])
        self.assertIn("high execution effort", captured[0].lower())


if __name__ == "__main__":
    unittest.main()
