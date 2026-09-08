from __future__ import annotations

import unittest

from engine.revise.decision import decide
from engine.revise.models import Decision, DimensionResult, EvaluationProfile, EvaluationResult, Evidence, Issue, Severity, TaskContract
from engine.revise.revision import RevisionAssessment


def passing_result(*, evidence=(), issues=()):
    return EvaluationResult(
        Decision.ACCEPT,
        0.95,
        1.0,
        {"correctness": DimensionResult(0.95, 1.0, "pass")},
        issues=issues,
        evidence=evidence,
    )


class DecisionPrecedenceAdversarialTests(unittest.TestCase):
    def profile(self, **kwargs):
        return EvaluationProfile(
            dimensions=("correctness",),
            required_dimensions=("correctness",),
            minimum_scores={"correctness": 0.70},
            minimum_overall_score=0.70,
            max_revisions=1,
            **kwargs,
        )

    def test_deterministic_failure_beats_model_and_external_pass(self):
        result = passing_result(evidence=(
            Evidence("secondary", "llm", "pass", 1.0),
            Evidence("source", "external", "pass", 1.0),
            Evidence("arithmetic", "deterministic", "fail", 1.0),
        ))
        decided = decide(TaskContract(goal="calculate"), self.profile(), result, revisions_used=0)
        self.assertEqual(decided.decision, Decision.REVISE)

    def test_external_failure_beats_model_pass(self):
        result = passing_result(evidence=(
            Evidence("secondary", "llm", "pass", 1.0),
            Evidence("source", "external", "fail", 1.0),
        ))
        decided = decide(TaskContract(goal="research"), self.profile(), result, revisions_used=0)
        self.assertEqual(decided.decision, Decision.REVISE)

    def test_hard_gate_beats_high_score_and_passing_evidence(self):
        issue = Issue("safety_gate", Severity.INFORMATIONAL, "blocked", "answer")
        result = passing_result(evidence=(Evidence("checker", "deterministic", "pass", 1.0),), issues=(issue,))
        decided = decide(TaskContract(goal="x"), self.profile(hard_gates=("safety_gate",)), result, revisions_used=0)
        self.assertEqual(decided.decision, Decision.REVISE)

    def test_evidence_requirement_is_not_satisfied_by_failed_matching_evidence(self):
        result = passing_result(evidence=(Evidence("arithmetic", "deterministic", "fail", 1.0),))
        decided = decide(TaskContract(goal="x"), self.profile(evidence_requirements=("deterministic",)), result, revisions_used=0)
        self.assertEqual(decided.decision, Decision.REVISE)

    def test_revision_regression_beats_acceptance_threshold(self):
        assessment = RevisionAssessment(0.80, 0.95, 0.15, status="regressed", regressed_dimensions=("correctness",))
        decided = decide(TaskContract(goal="x"), self.profile(), passing_result(), revisions_used=1, revision_assessment=assessment)
        self.assertEqual(decided.decision, Decision.ASK)

    def test_low_confidence_beats_high_score(self):
        result = EvaluationResult(
            Decision.ACCEPT,
            0.99,
            0.20,
            {"correctness": DimensionResult(0.99, 0.20, "pass")},
        )
        decided = decide(TaskContract(goal="x"), self.profile(minimum_confidence=0.60), result, revisions_used=0)
        self.assertEqual(decided.decision, Decision.ASK)


if __name__ == "__main__":
    unittest.main()
