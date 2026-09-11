from __future__ import annotations

from ai.hive.core import HiveCore


class FakeWorker:
    def __init__(self, name: str):
        self.name = name

    def health(self):
        return {"status": "READY", "worker": self.name}

    def execute(self, task, *, system=None):
        return f"{self.name}: result"


def make_core():
    config = {
        "routing": {
            "primary": "openai",
            "fallback": "ollama",
        },
        "council": {
            "observer": {"worker": "openai"},
            "explorer": {"worker": "openai"},
            "contrarian": {"worker": "openai"},
            "auditor": {"worker": "openai"},
            "synthesizer": {"worker": "openai"},
        },
    }

    core = object.__new__(HiveCore)
    core.config = config
    core.worker_registry = type(
        "Registry",
        (),
        {
            "_workers": {
                "openai": FakeWorker("openai"),
                "ollama": FakeWorker("ollama"),
            },
            "get": lambda self, name: self._workers[name],
            "names": lambda self: list(self._workers),
        },
    )()

    core.council = core._build_council()

    return core


def test_hive_builds_council_from_worker_registry():
    core = make_core()

    council = core._build_council()

    assert council.auditor.name == "openai"
    assert council.synthesizer.name == "openai"

    roles = {
        role: worker.name
        for role, (_, worker) in council.debate.agents.items()
    }

    assert roles == {
        "observer": "openai",
        "explorer": "openai",
        "contrarian": "openai",
    }


def test_hive_council_role_can_use_different_workers():
    core = make_core()

    core.config["council"]["contrarian"] = {"worker": "ollama"}
    core.config["council"]["auditor"] = {"worker": "ollama"}

    council = core._build_council()

    assert council.debate.agents["observer"][1].name == "openai"
    assert council.debate.agents["explorer"][1].name == "openai"
    assert council.debate.agents["contrarian"][1].name == "ollama"
    assert council.auditor.name == "ollama"
    assert council.synthesizer.name == "openai"


def test_hive_council_can_deliberate_with_registered_workers():
    core = make_core()

    result = core.council.deliberate("What is the evidence?")

    assert result.question == "What is the evidence?"
    assert len(result.debate.responses) == 3
    assert result.audit is not None
    assert result.synthesis == "openai: result"
