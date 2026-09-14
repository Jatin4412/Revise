import math
import unittest

from engine.revise.diagnosis import CorrectionRecommendation, Diagnosis, validate_diagnosis
from engine.revise.decision import decide
from engine.revise.models import Decision, DimensionResult, EvaluationProfile, EvaluationResult, Evidence, Issue, Severity, TaskContract


class DiagnosisFoundationTests(unittest.TestCase):
    def _passing_profile(self, **kwargs):
        return EvaluationProfile(
            dimensions=("correctness",),
            required_dimensions=("correctness",),
            minimum_scores={"correctness": 0.7},
            minimum_overall_score=0.7,
            **kwargs,
        )

    def _passing_result(self, **kwargs):
        return EvaluationResult(
            Decision.ACCEPT,
            0.95,
            0.95,
            {"correctness": DimensionResult(0.95, 0.95, "pass")},
            **kwargs,
        )

    def test_all_correction_recommendations_are_advisory_values(self):
        self.assertEqual(
            {item.value for item in CorrectionRecommendation},
            {"revise", "verify", "change_approach", "ask", "accept_candidate"},
        )

    def test_valid_diagnosis_is_structured_and_provider_neutral(self):
        diagnosis = Diagnosis(
            status="actionable",
            summary="The current solution approach is failing on the core constraint.",
            failure_categories=("reasoning_error", "strategy_failure"),
            confidence=0.9,
            recommended_correction=CorrectionRecommendation.CHANGE_APPROACH,
            affected_dimensions=("correctness",),
            affected_issues=("reasoning_error||core constraint",),
            evidence_basis=("evaluation:correctness",),
        )
        self.assertIs(validate_diagnosis(diagnosis), diagnosis)

    def test_low_confidence_diagnosis_fails_closed(self):
        diagnosis = Diagnosis("actionable", "uncertain diagnosis", confidence=0.59)
        self.assertIsNone(validate_diagnosis(diagnosis))

    def test_non_finite_confidence_fails_closed(self):
        for confidence in (math.nan, math.inf, -math.inf):
            diagnosis = Diagnosis("actionable", "bad confidence", confidence=confidence)
            self.assertIsNone(validate_diagnosis(diagnosis))

    def test_malformed_diagnosis_fails_closed(self):
        self.assertIsNone(validate_diagnosis("not a diagnosis"))
        self.assertIsNone(validate_diagnosis(Diagnosis("invalid", "unsupported status", confidence=0.9)))
        self.assertIsNone(validate_diagnosis(Diagnosis("actionable", "", confidence=0.9)))
        self.assertIsNone(validate_diagnosis(Diagnosis("actionable", "bad recommendation", confidence=0.9, recommended_correction="accept_candidate")))
        self.assertIsNone(validate_diagnosis(Diagnosis("actionable", "bad categories", confidence=0.9, failure_categories=("",))))

    def test_accept_candidate_does_not_create_acceptance_authority(self):
        profile = self._passing_profile()
        result = self._passing_result()
        diagnosis = Diagnosis("actionable", "candidate appears ready", confidence=0.95, recommended_correction=CorrectionRecommendation.ACCEPT_CANDIDATE)
        self.assertIsNotNone(validate_diagnosis(diagnosis))
        self.assertEqual(decide(TaskContract(goal="x"), profile, result, revisions_used=0).decision, Decision.ACCEPT)

    def test_hard_gate_failure_remains_authoritative(self):
        profile = self._passing_profile(hard_gates=("blocked_claim",))
        result = self._passing_result(issues=(Issue("blocked_claim", Severity.MINOR, "blocked"),))
        diagnosis = Diagnosis("actionable", "candidate appears acceptable", confidence=0.99, recommended_correction=CorrectionRecommendation.ACCEPT_CANDIDATE)
        self.assertIsNotNone(validate_diagnosis(diagnosis))
        self.assertNotEqual(decide(TaskContract(goal="x"), profile, result, revisions_used=0).decision, Decision.ACCEPT)

    def test_deterministic_failure_remains_authoritative(self):
        profile = self._passing_profile(deterministic_checks=("arithmetic",))
        result = self._passing_result(evidence=(Evidence("arithmetic", "deterministic", "fail", 1.0),))
        diagnosis = Diagnosis("actionable", "try a different approach", confidence=0.95, recommended_correction=CorrectionRecommendation.CHANGE_APPROACH)
        self.assertIsNotNone(validate_diagnosis(diagnosis))
        self.assertNotEqual(decide(TaskContract(goal="calculate"), profile, result, revisions_used=0).decision, Decision.ACCEPT)

    def test_invalid_diagnosis_never_mutates_evaluation(self):
        result = self._passing_result()
        original = result
        self.assertIsNone(validate_diagnosis(Diagnosis("actionable", "low confidence", confidence=0.1)))
        self.assertIs(result, original)
        self.assertEqual(result.decision, Decision.ACCEPT)


if __name__ == "__main__":
    unittest.main()
