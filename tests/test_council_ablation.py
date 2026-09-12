from dataclasses import dataclass

from ai.hive.ablation import CouncilAblation
from ai.hive.council import Council
from ai.hive.debate import AgentRole


@dataclass
class FakeResult:
    text: str
    provider: str = "fake"
    model: str = "fake"
    elapsed_seconds: float = 0.01
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {"response_id": self.text}


class FakeWorker:
    def __init__(self, name):
        self.name = name

    def execute(self, prompt, system=None):
        return FakeResult(f"{self.name}:{prompt[:80]}")


def make_council():
    roles = {
        name: (AgentRole(name, f"mission-{name}"), FakeWorker(name))
        for name in ("observer", "explorer", "contrarian")
    }
    auditor = FakeWorker("auditor")
    synthesizer = FakeWorker("synthesizer")
    return Council(roles, auditor=auditor, synthesizer=synthesizer)


def test_without_role_removes_only_requested_role():
    council = make_council()
    variant = council.without_role("observer")

    assert set(variant.debate.agents) == {"explorer", "contrarian"}
    assert set(council.debate.agents) == {"observer", "explorer", "contrarian"}
    assert variant.auditor is council.auditor
    assert variant.synthesizer is council.synthesizer


def test_ablation_runs_baseline_and_each_role_removal():
    report = CouncilAblation(make_council()).run("test ablation")

    assert report.baseline.removed_role is None
    assert [case.removed_role for case in report.variants] == [
        "observer", "explorer", "contrarian"
    ]
    assert report.baseline.debate_roles == ("contrarian", "explorer", "observer")
    assert report.variants[0].debate_roles == ("contrarian", "explorer")
    assert report.variants[1].debate_roles == ("contrarian", "observer")
    assert report.variants[2].debate_roles == ("explorer", "observer")
    assert all(case.trace_count >= 3 for case in report.variants)


def test_ablation_rejects_unknown_role():
    try:
        CouncilAblation(make_council()).run("test", roles=("not-a-role",))
    except ValueError as exc:
        assert "Unknown Council role" in str(exc)
    else:
        raise AssertionError("Unknown role must be rejected")
