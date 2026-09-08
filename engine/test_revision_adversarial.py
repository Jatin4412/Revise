from __future__ import annotations

import unittest

from engine.revise.models import Decision, DimensionResult, EvaluationResult, Issue, Severity
from engine.revise.revision import assess_revision


def evaluation(
    score: float,
    *,
    dimensions: dict[str, float] | None = None,
    issues: tuple[Issue, ...] = (),
) -> EvaluationResult:
    dimension_results = {
        name: DimensionResult(value, 1.0, "pass", f"controlled {name}")
        for name, value in (dimensions or {"correctness": score}).items()
    }
    return EvaluationResult(Decision.ACCEPT, score, 1.0, dimension_results, issues=issues)


class RevisionAdversarialEdgeTests(unittest.TestCase):
    def test_score_tie_with_issue_resolution_is_an_improvement(self) -> None:
        issue = Issue("accuracy", Severity.MODERATE, "wrong claim", "paragraph 2")
        assessment = assess_revision(
            evaluation(0.80, issues=(issue,)),
            evaluation(0.80),
        )
        self.assertEqual(assessment.status, "improved")
        self.assertEqual(assessment.score_delta, 0.0)
        self.assertEqual(len(assessment.resolved_issues), 1)

    def test_score_tie_with_no_quality_change_is_unchanged(self) -> None:
        baseline = evaluation(0.80, dimensions={"correctness": 0.80, "clarity": 0.80})
        revised = evaluation(0.80, dimensions={"correctness": 0.80, "clarity": 0.80})
        assessment = assess_revision(baseline, revised)
        self.assertEqual(assessment.status, "unchanged")
        self.assertEqual(assessment.score_delta, 0.0)
        self.assertEqual(assessment.improved_dimensions, ())
        self.assertEqual(assessment.regressed_dimensions, ())

    def test_mixed_issue_changes_regress_when_a_material_issue_is_introduced(self) -> None:
        resolved = Issue("accuracy", Severity.MODERATE, "wrong claim", "paragraph 2")
        introduced = Issue("safety", Severity.MAJOR, "unsafe instruction", "paragraph 4")
        assessment = assess_revision(
            evaluation(0.80, issues=(resolved,)),
            evaluation(0.80, issues=(introduced,)),
        )
        self.assertEqual(assessment.status, "regressed")
        self.assertEqual(len(assessment.resolved_issues), 1)
        self.assertEqual(len(assessment.introduced_issues), 1)

    def test_missing_dimension_is_not_falsely_counted_as_improvement(self) -> None:
        baseline = evaluation(0.80, dimensions={"correctness": 0.80, "clarity": 0.80})
        revised = evaluation(0.85, dimensions={"correctness": 0.85})
        assessment = assess_revision(baseline, revised)
        self.assertEqual(assessment.status, "improved")
        self.assertEqual(assessment.improved_dimensions, ("correctness",))
        self.assertEqual(assessment.regressed_dimensions, ())


if __name__ == "__main__":
    unittest.main()
