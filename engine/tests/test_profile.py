from revise.models import Mode, TaskContract
from revise.profile import build_profile


def test_lite_keeps_profile_light():
    profile = build_profile(TaskContract(goal="Explain this concept simply", mode=Mode.LITE))
    assert profile.evaluation_effort == "low"
    assert profile.max_revisions == 0
    assert "correctness" in profile.dimensions


def test_code_task_prefers_deterministic_verification():
    profile = build_profile(
        TaskContract(goal="Write a Python function that passes the supplied tests", mode=Mode.BASIC)
    )
    assert "code_correctness" in profile.dimensions
    assert "compile_or_tests" in profile.deterministic_checks


def test_factual_research_adds_external_verification():
    profile = build_profile(TaskContract(goal="Research the latest sources and cite them", mode=Mode.BASIC))
    assert "groundedness" in profile.dimensions
    assert "source_verification" in profile.external_verification
