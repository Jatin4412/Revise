import math
import unittest

from engine.revise.models import EvaluationProfile


class EvaluationPolicyContractTests(unittest.TestCase):
    def test_duplicate_dimensions_are_rejected(self):
        with self.assertRaises(ValueError):
            EvaluationProfile(dimensions=("correctness", "correctness"))

    def test_empty_dimensions_are_rejected(self):
        with self.assertRaises(ValueError):
            EvaluationProfile(dimensions=())

    def test_required_dimensions_must_exist_and_be_unique(self):
        with self.assertRaises(ValueError):
            EvaluationProfile(dimensions=("correctness",), required_dimensions=("clarity",))
        with self.assertRaises(ValueError):
            EvaluationProfile(dimensions=("correctness",), required_dimensions=("correctness", "correctness"))

    def test_weight_and_floor_maps_must_reference_dimensions(self):
        with self.assertRaises(ValueError):
            EvaluationProfile(dimensions=("correctness",), dimension_weights={"clarity": 1.0})
        with self.assertRaises(ValueError):
            EvaluationProfile(dimensions=("correctness",), minimum_scores={"clarity": 0.7})

    def test_weights_must_be_finite_and_non_negative(self):
        for weight in (-1.0, float("nan"), float("inf"), True):
            with self.assertRaises(ValueError):
                EvaluationProfile(dimensions=("correctness",), dimension_weights={"correctness": weight})

    def test_thresholds_must_be_finite_and_bounded(self):
        for field, value in (
            ("minimum_confidence", 1.1),
            ("minimum_confidence", -0.1),
            ("minimum_confidence", float("nan")),
            ("minimum_confidence", float("inf")),
            ("minimum_overall_score", -0.1),
            ("minimum_overall_score", 1.1),
            ("minimum_overall_score", float("nan")),
            ("minimum_overall_score", float("inf")),
        ):
            with self.assertRaises(ValueError):
                EvaluationProfile(dimensions=("correctness",), **{field: value})
        with self.assertRaises(ValueError):
            EvaluationProfile(dimensions=("correctness",), minimum_scores={"correctness": 1.1})
        with self.assertRaises(ValueError):
            EvaluationProfile(dimensions=("correctness",), minimum_scores={"correctness": float("nan")})

    def test_budgets_must_be_non_negative_integers(self):
        for field in ("max_revisions", "max_verification_steps"):
            for value in (-1, True, 1.5):
                with self.assertRaises(ValueError):
                    EvaluationProfile(dimensions=("correctness",), **{field: value})

    def test_effort_must_use_supported_policy_value(self):
        for value in ("tiny", "extreme", ""):
            with self.assertRaises(ValueError):
                EvaluationProfile(dimensions=("correctness",), evaluation_effort=value)

    def test_policy_selector_fields_must_not_contain_empty_values(self):
        for field in ("hard_gates", "deterministic_checks", "external_verification", "llm_evaluators", "evidence_requirements", "stopping_conditions"):
            with self.assertRaises(ValueError):
                EvaluationProfile(dimensions=("correctness",), **{field: ("",)})


if __name__ == "__main__":
    unittest.main()
