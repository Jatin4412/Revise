from revise.evaluator import evaluate
from revise.models import DimensionResult, Mode, TaskContract


def passing(_contract, _response):
    return DimensionResult(0.95, 0.95, "pass", "meets requirement")


def failing(_contract, _response):
    return DimensionResult(0.2, 0.95, "fail", "requirement missing")


def test_unknown_evaluator_does_not_auto_accept():
    result = evaluate(TaskContract(goal="Answer the question", mode=Mode.BASIC), "answer")
    assert result.decision.value == "ask"


def test_passing_evaluators_accept():
    result = evaluate(
        TaskContract(goal="Answer the question", mode=Mode.LITE),
        "answer",
        evaluators={name: passing for name in (
            "goal_alignment", "task_completion", "correctness", "relevance",
            "completeness", "instruction_following"
        )},
    )
    assert result.decision.value == "accept"


def test_material_failure_revises_when_budget_exists():
    result = evaluate(
        TaskContract(goal="Answer the question", mode=Mode.BASIC),
        "bad answer",
        evaluators={
            "goal_alignment": passing,
            "task_completion": failing,
            "correctness": failing,
            "relevance": passing,
            "completeness": failing,
            "instruction_following": passing,
        },
    )
    assert result.decision.value == "revise"
