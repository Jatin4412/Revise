from __future__ import annotations

import unittest

from engine.revise.models import Decision, DimensionResult, EvaluationResult, Issue, Severity
from engine.revise.revision import assess_revision


def evaluation(score: float, *, dimensions: dict[str, float] | None = None, issues: tuple[Issue, ...] = ()) -> EvaluationResult:
    dimension_results = {
        name: DimensionResult(value, 1.0, "pass", f"controlled {name}")
        for name, value in (dimensions or {"correctness": score}).items()
    }
    return EvaluationResult(Decision.ACCEPT, score, 1.0, dimension_results, issues=issues)


class RevisionAdversarialEdgeTests(unittest.TestCase):
    def test_issue_identity_ignores_case_and_whitespace_variation(self):
        before = Issue(" Accuracy ", Severity.MAJOR, "wrong   claim", " paragraph 2 ")
        after = Issue("accuracy", Severity.MINOR, "WRONG claim", "paragraph   2")
        assessment = assess_revision(evaluation(0.70, issues=(before,)), evaluation(0.80, issues=(after,)))
        self.assertEqual(assessment.resolved_issues, ())
        self.assertEqual(assessment.introduced_issues, ())
        self.assertEqual(assessment.downgraded_issues, ("accuracy|paragraph 2|wrong claim",))
        self.assertEqual(assessment.status, "improved")

    def test_missing_dimension_is_regression(self):
        baseline = evaluation(0.80, dimensions={"correctness": 0.80, "clarity": 0.80})
        revised = evaluation(0.85, dimensions={"correctness": 0.85})
        assessment = assess_revision(baseline, revised)
        self.assertEqual(assessment.status, "regressed")
        self.assertEqual(assessment.regressed_dimensions, ("clarity",))

    def test_score_tie_with_issue_resolution_is_improvement(self):
        issue = Issue("accuracy", Severity.MODERATE, "wrong claim", "paragraph 2")
        assessment = assess_revision(evaluation(0.80, issues=(issue,)), evaluation(0.80))
        self.assertEqual(assessment.status, "improved")
        self.assertEqual(assessment.score_delta, 0.0)

    def test_score_tie_without_change_is_unchanged(self):
        baseline = evaluation(0.80, dimensions={"correctness": 0.80, "clarity": 0.80})
        revised = evaluation(0.80, dimensions={"correctness": 0.80, "clarity": 0.80})
        assessment = assess_revision(baseline, revised)
        self.assertEqual(assessment.status, "unchanged")

    def test_resolved_issue_plus_material_new_issue_is_regression(self):
        resolved = Issue("accuracy", Severity.MODERATE, "wrong claim", "paragraph 2")
        introduced = Issue("safety", Severity.MAJOR, "unsafe instruction", "paragraph 4")
        assessment = assess_revision(evaluation(0.80, issues=(resolved,)), evaluation(0.80, issues=(introduced,)))
        self.assertEqual(assessment.status, "regressed")
        self.assertEqual(len(assessment.resolved_issues), 1)
        self.assertEqual(len(assessment.introduced_issues), 1)

    def test_dimension_regression_overrides_overall_score_gain(self):
        baseline = evaluation(0.85, dimensions={"correctness": 1.0, "clarity": 0.70})
        revised = evaluation(0.90, dimensions={"correctness": 0.80, "clarity": 1.0})
        assessment = assess_revision(baseline, revised)
        self.assertEqual(assessment.status, "regressed")
        self.assertEqual(assessment.regressed_dimensions, ("correctness",))


if __name__ == "__main__":
    unittest.main()
