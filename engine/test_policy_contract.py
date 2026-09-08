import unittest

from engine.revise.models import EvaluationProfile


class EvaluationPolicyContractTests(unittest.TestCase):
    def test_duplicate_dimensions_are_rejected(self):
        with self.assertRaises(ValueError):
            EvaluationProfile(dimensions=("correctness", "correctness"))

    def test_required_dimensions_must_exist(self):
        with self.assertRaises(ValueError):
            EvaluationProfile(dimensions=("correctness",), required_dimensions=("clarity",))

    def test_weight_and_floor_maps_must_reference_dimensions(self):
        with self.assertRaises(ValueError):
            EvaluationProfile(dimensions=("correctness",), dimension_weights={"clarity": 1.0})
        with self.assertRaises(ValueError):
            EvaluationProfile(dimensions=("correctness",), minimum_scores={"clarity": 0.7})

    def test_weights_cannot_be_negative(self):
        with self.assertRaises(ValueError):
            EvaluationProfile(dimensions=("correctness",), dimension_weights={"correctness": -1.0})

    def test_thresholds_must_be_bounded(self):
        for field, value in (("minimum_confidence", 1.1), ("minimum_overall_score", -0.1)):
            with self.assertRaises(ValueError):
                EvaluationProfile(dimensions=("correctness",), **{field: value})
        with self.assertRaises(ValueError):
            EvaluationProfile(dimensions=("correctness",), minimum_scores={"correctness": 1.1})

    def test_budgets_must_be_non_negative_integers(self):
        for field in ("max_revisions", "max_verification_steps"):
            with self.assertRaises(ValueError):
                EvaluationProfile(dimensions=("correctness",), **{field: -1})


if __name__ == "__main__":
    unittest.main()
