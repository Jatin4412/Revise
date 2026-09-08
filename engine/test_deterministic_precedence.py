from __future__ import annotations

import unittest

from engine.revise.decision import decide
from engine.revise.models import Decision, DimensionResult, EvaluationProfile, EvaluationResult, Evidence, Issue, Severity, TaskContract
from engine.revise.verifiers import run_deterministic_verifiers


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

    def test_configured_hard_gate_blocks_acceptance_even_for_minor_issue(self) -> None:
        contract = TaskContract(goal="handle a safety-sensitive task")
        profile = EvaluationProfile(
            dimensions=("correctness",),
            hard_gates=("safety",),
            minimum_scores={"correctness": 0.70},
            minimum_overall_score=0.75,
            max_revisions=1,
        )
        result = EvaluationResult(
            Decision.ACCEPT,
            1.0,
            1.0,
            {"correctness": DimensionResult(1.0, 1.0, "pass", "looks correct")},
            issues=(Issue("safety", Severity.MINOR, "unsafe edge case"),),
        )
        decided = decide(contract, profile, result, revisions_used=0)
        self.assertEqual(decided.decision, Decision.REVISE)

    def test_unavailable_configured_deterministic_verifier_fails_closed(self) -> None:
        contract = TaskContract(goal="task")
        profile = EvaluationProfile(dimensions=("correctness",), deterministic_checks=("missing_check",))
        evidence = run_deterministic_verifiers(contract, "answer", profile, registry={})
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0].result, "fail")
        self.assertIn("verifier_unavailable:missing_check", evidence[0].provenance)


if __name__ == "__main__":
    unittest.main()
