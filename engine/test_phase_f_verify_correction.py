from __future__ import annotations

import unittest

from .engine import Engine
from .revise.diagnosis import CorrectionRecommendation
from .revise.models import Decision, DimensionResult, EvaluationProfile, EvaluationResult, Evidence, TaskContract


class ScriptedPrimary:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.calls: list[str | None] = []

    def generate(self, contract: TaskContract, *, context: str | None = None) -> str:
        self.calls.append(context)
        return self.responses[len(self.calls) - 1]


class ScriptedSecondary:
    def __init__(self, results: list[EvaluationResult]) -> None:
        self.results = results
        self.calls = 0

    def evaluate_candidate(self, contract: TaskContract, response: str, profile: EvaluationProfile) -> EvaluationResult:
        result = self.results[self.calls]
        self.calls += 1
        return result


def profile() -> EvaluationProfile:
    return EvaluationProfile(
        dimensions=("correctness",),
        required_dimensions=("correctness",),
        minimum_scores={"correctness": 0.70},
        minimum_overall_score=0.75,
        minimum_confidence=0.60,
        max_revisions=1,
        max_verification_steps=1,
    )


def result(score: float, evidence: tuple[Evidence, ...]) -> EvaluationResult:
    return EvaluationResult(
        Decision.ACCEPT if score >= 0.75 else Decision.REVISE,
        score,
        0.95,
        {"correctness": DimensionResult(score, 0.95, "pass" if score >= 0.75 else "partial", "scripted")},
        evidence=evidence,
    )


class PhaseFVerifyCorrectionTests(unittest.TestCase):
    def test_verify_recommendation_survives_current_attempt_budget_and_guides_next_attempt(self) -> None:
        primary = ScriptedPrimary(["evidence-limited answer", "verified answer"])
        secondary = ScriptedSecondary([
            result(0.80, (Evidence("source", "external", "fail", 0.95, ("source_unreachable",)),)),
            result(0.95, (Evidence("source", "external", "pass", 0.95, ("source_reachable",)),)),
        ])

        outcome = Engine(primary, secondary=secondary).run(TaskContract(goal="answer with evidence"), profile=profile())

        self.assertEqual(outcome.decision, Decision.ACCEPT)
        self.assertEqual(len(outcome.versions), 2)
        self.assertEqual(outcome.versions[0].metadata["diagnosis"].recommended_correction, CorrectionRecommendation.VERIFY)
        self.assertEqual(outcome.versions[0].metadata["correction_recommendation"], CorrectionRecommendation.VERIFY.value)
        self.assertEqual(outcome.versions[1].metadata["correction"], CorrectionRecommendation.VERIFY.value)
        self.assertIn("evidence and verification", primary.calls[1] or "")
        self.assertEqual(outcome.versions[1].metadata["revision_assessment"].status, "improved")


if __name__ == "__main__":
    unittest.main()
