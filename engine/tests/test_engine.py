from revise.models import DimensionResult, Mode, TaskContract
from engine.engine import Engine


def passing(_contract, _response):
    return DimensionResult(0.95, 0.95, "pass", "ok")


def test_engine_accepts_valid_response():
    contract = TaskContract(goal="Answer the question", mode=Mode.LITE)
    names = ("goal_alignment", "task_completion", "correctness", "relevance", "completeness", "instruction_following")

    engine = Engine(lambda _contract, _context: "good", evaluators={name: passing for name in names})
    result = engine.run(contract)

    assert result.decision.value == "accept"
    assert result.final_version is not None
    assert result.final_version.id == "v0"


def test_engine_bounds_revision_loop():
    def failing(_contract, _response):
        return DimensionResult(0.1, 0.95, "fail", "bad")

    contract = TaskContract(goal="Answer the question", mode=Mode.BASIC)
    names = ("goal_alignment", "task_completion", "correctness", "relevance", "completeness", "instruction_following")
    engine = Engine(lambda _contract, _context: "bad", evaluators={name: failing for name in names})
    result = engine.run(contract)

    assert len(result.versions) == 2
