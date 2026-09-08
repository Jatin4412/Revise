from __future__ import annotations

import unittest

from engine import Engine
from engine.revise.decision import decide
from engine.revise.models import Decision, DimensionResult, EvaluationProfile, EvaluationResult, Issue, Severity, TaskContract
from engine.revise.revision import assess_revision


class ScriptedPrimary:
    def __init__(self, responses: list[str]) -> None:
        self.responses = iter(responses)

    def generate(self, contract: TaskContract, *, context: str | None = None) -> str:
        return next(self.responses)


class ScriptedSecondary:
    def __init__(self, evaluations: list[EvaluationResult]) -> None:
        self.evaluations = iter(evaluations)

    def evaluate_candidate(self, contract: TaskContract, response: str, profile: EvaluationProfile) -> EvaluationResult:
        return next(self.evaluations)


def evaluation(
    score: float,
    *,
    correctness: float | None = None,
    clarity: float | None = None,
    issues: tuple[Issue, ...] = (),
    decision: Decision = Decision.ACCEPT,
) -> EvaluationResult:
    dimensions = {}
    if correctness is not None:
        dimensions["correctness"] = DimensionResult(correctness, 1.0, "pass", "controlled correctness")
    if clarity is not None:
        dimensions["clarity"] = DimensionResult(clarity, 1.0, "pass", "controlled clarity")
    return EvaluationResult(decision, score, 1.0, dimensions, issues=issues)


class RevisionQualityAdversarialTests(unittest.TestCase):
    def test_issue_identity_survives_severity_change(self) -> None:
        issue_before = Issue("accuracy", Severity.MAJOR, "wrong claim", "paragraph 2")
        issue_after = Issue("accuracy", Severity.MINOR, "wrong claim", "paragraph 2")
        assessment = assess_revision(
            evaluation(0.70, issues=(issue_before,)),
            evaluation(0.80, issues=(issue_after,)),
        )
        self.assertEqual(assessment.resolved_issues, ())
        self.assertEqual(assessment.introduced_issues, ())
        self.assertEqual(len(assessment.downgraded_issues), 1)
        self.assertEqual(assessment.status, "improved")

    def test_severity_escalation_is_regression_even_when_score_rises(self) -> None:
        issue_before = Issue("accuracy", Severity.MODERATE, "wrong claim", "paragraph 2")
        issue_after = Issue("accuracy", Severity.MAJOR, "wrong claim", "paragraph 2")
        assessment = assess_revision(
            evaluation(0.80, issues=(issue_before,)),
            evaluation(0.90, issues=(issue_after,)),
        )
        self.assertEqual(assessment.status, "regressed")
        self.assertEqual(len(assessment.escalated_issues), 1)

    def test_dimension_regression_blocks_revision_even_when_overall_score_rises(self) -> None:
        baseline = evaluation(0.85, correctness=1.0, clarity=0.70)
        revised = evaluation(0.90, correctness=0.80, clarity=1.0)
        assessment = assess_revision(baseline, revised)
        self.assertEqual(assessment.status, "regressed")
        self.assertEqual(assessment.regressed_dimensions, ("correctness",))
        profile = EvaluationProfile(
            dimensions=("correctness", "clarity"),
            minimum_scores={"correctness": 0.70, "clarity": 0.70},
            required_dimensions=("correctness",),
            minimum_overall_score=0.75,
            max_revisions=1,
        )
        decided = decide(TaskContract(goal="task"), profile, revised, revisions_used=1, revision_assessment=assessment)
        self.assertEqual(decided.decision, Decision.ASK)

    def test_repeated_revisions_compare_against_immediate_previous(self) -> None:
        issue = Issue("quality", Severity.MODERATE, "needs improvement")
        secondary = ScriptedSecondary(
            [
                evaluation(0.70, correctness=0.70, issues=(issue,), decision=Decision.REVISE),
                evaluation(0.80, correctness=0.80, issues=(issue,), decision=Decision.REVISE),
                evaluation(0.90, correctness=0.90, issues=(), decision=Decision.ACCEPT),
            ]
        )
        result = Engine(ScriptedPrimary(["v0", "v1", "v2"]), secondary=secondary).run(
            TaskContract(goal="task"),
            profile=EvaluationProfile(
                dimensions=("correctness",),
                required_dimensions=("correctness",),
                minimum_scores={"correctness": 0.70},
                minimum_overall_score=0.75,
                max_revisions=2,
            ),
        )
        self.assertEqual(result.decision, Decision.ACCEPT)
        self.assertEqual([version.id for version in result.versions], ["v0", "v1", "v2"])
        self.assertEqual(result.versions[1].metadata["revision_assessment"].baseline_score, 0.70)
        self.assertEqual(result.versions[2].metadata["revision_assessment"].baseline_score, 0.80)
        self.assertEqual(result.final_version.id, "v2")

    def test_regressed_revision_cannot_replace_accepted_prior_version(self) -> None:
        issue = Issue("quality", Severity.MODERATE, "new problem")
        secondary = ScriptedSecondary(
            [
                evaluation(0.90, correctness=0.90, issues=()),
                evaluation(0.80, correctness=0.80, issues=(issue,)),
            ]
        )
        result = Engine(ScriptedPrimary(["good", "worse"]), secondary=secondary).run(
            TaskContract(goal="task"),
            profile=EvaluationProfile(
                dimensions=("correctness",),
                required_dimensions=("correctness",),
                minimum_scores={"correctness": 0.70},
                minimum_overall_score=0.75,
                max_revisions=1,
            ),
        )
        self.assertEqual(result.decision, Decision.REVISE)
        self.assertEqual(result.final_version.id, "v0")
        self.assertEqual(result.final_version.response, "good")
        self.assertEqual(result.versions[1].metadata["revision_assessment"].status, "regressed")


if __name__ == "__main__":
    unittest.main()
