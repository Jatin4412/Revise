from __future__ import annotations

import unittest

from engine.revise.decision import decide
from engine.revise.models import Decision, DimensionResult, EvaluationProfile, EvaluationResult, Evidence, TaskContract


class DeterministicPrecedenceTests(unittest.TestCase):
    def test_deterministic_failure_overrides_confident_llm_pass(self) -> None:
        contract = TaskContract(goal="calculate 2 + 3")
        profile = EvaluationProfile(
            dimensions=("correctness",),
            required_dimensions=("correctness",),
            minimum_scores={"correctness": 0.70},
            minimum_overall_score=0.75,
            max_revisions=1,
        )
        result = EvaluationResult(
            Decision.ACCEPT,
            1.0,
            1.0,
            {"correctness": DimensionResult(1.0, 1.0, "pass", "confident model pass")},
            evidence=(
                Evidence("secondary", "llm", "pass", 1.0, ("confident model pass",)),
                Evidence("deterministic.arithmetic", "deterministic", "fail", 1.0, ("2 + 3 = 6",)),
            ),
        )
        decided = decide(contract, profile, result, revisions_used=0)
        self.assertEqual(decided.decision, Decision.REVISE)

    def test_deterministic_failure_asks_when_revision_budget_is_exhausted(self) -> None:
        contract = TaskContract(goal="calculate 2 + 3")
        profile = EvaluationProfile(dimensions=("correctness",), minimum_overall_score=0.75, max_revisions=1)
        result = EvaluationResult(
            Decision.ACCEPT,
            1.0,
            1.0,
            {"correctness": DimensionResult(1.0, 1.0, "pass", "confident model pass")},
            evidence=(Evidence("deterministic.arithmetic", "deterministic", "fail", 1.0, ("2 + 3 = 6",)),),
        )
        decided = decide(contract, profile, result, revisions_used=1)
        self.assertEqual(decided.decision, Decision.ASK)


if __name__ == "__main__":
    unittest.main()
