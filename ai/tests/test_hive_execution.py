from dataclasses import dataclass

from ai.hive.core import HiveCore
from ai.workers.base import Worker
from ai.workers.registry import WorkerRegistry
from ai.workers.policy import WorkerPolicy


@dataclass
class FakeResponse:
    text: str
    provider: str
    model: str = "test-model"
    success: bool = True
    elapsed_seconds: float = 0.01
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class FakeWorker(Worker):
    def __init__(self, name, capabilities, response_text):
        super().__init__(
            name=name,
            kind="test",
            description="Test Hive worker.",
            capabilities=tuple(capabilities),
        )
        self.response_text = response_text
        self.executed = False
        self.last_task = None
        self.last_system = None

    def health(self):
        return {
            "status": "READY",
            "provider": self.name,
        }

    def execute(self, task, *, system=None):
        self.executed = True
        self.last_task = task
        self.last_system = system

        return FakeResponse(
            text=self.response_text,
            provider=self.name,
        )


def build_test_hive(workers, routing=None):
    config = {
        "routing": routing or {
            "primary": "gemini",
            "fallback": "ollama",
            "allow_automatic_fallback": True,
        },
        "providers": {},
    }

    registry = WorkerRegistry()

    for worker in workers:
        registry.register(worker)

    hive = HiveCore.__new__(HiveCore)

    hive.config = config
    hive.provider_factory = None
    hive.router_factory = None
    hive.worker_registry = registry
    hive.worker_policy = WorkerPolicy(registry, config)

    return hive


def test_hive_executes_policy_selected_worker():
    gemini = FakeWorker(
        "gemini",
        ("reasoning",),
        "Gemini executed the task.",
    )

    ollama = FakeWorker(
        "ollama",
        ("reasoning",),
        "Ollama executed the task.",
    )

    hive = build_test_hive([gemini, ollama])

    result = hive.dispatch_reasoning(
        "Explain the evidence.",
    )

    assert gemini.executed is True
    assert ollama.executed is False

    assert result.worker == "gemini"
    assert result.provider == "gemini"
    assert result.result == "Gemini executed the task."

    assert result.metadata["worker_selection"]["selected"] == "gemini"
    assert result.metadata["worker_execution"]["selected"] == "gemini"
    assert result.metadata["worker_execution"]["executed"] == "gemini"
    assert result.metadata["worker_execution"]["fallback_used"] is False


def test_hive_executes_unique_capability_worker():
    codex = FakeWorker(
        "codex",
        ("reasoning",),
        "Codex executed the task.",
    )

    hive = build_test_hive(
        [codex],
        routing={
            "primary": "gemini",
            "fallback": "ollama",
            "allow_automatic_fallback": True,
        },
    )

    result = hive.dispatch_reasoning(
        "Analyze the repository.",
    )

    assert codex.executed is True

    assert result.worker == "codex"
    assert result.provider == "codex"
    assert result.result == "Codex executed the task."

    assert result.metadata["worker_selection"]["selected"] == "codex"
    assert result.metadata["worker_selection"]["policy"] == "unique_capability"
    assert result.metadata["worker_execution"]["executed"] == "codex"


def test_hive_records_worker_execution_metadata():
    gemini = FakeWorker(
        "gemini",
        ("reasoning",),
        "Execution recorded.",
    )

    ollama = FakeWorker(
        "ollama",
        ("reasoning",),
        "Should not execute.",
    )

    hive = build_test_hive([gemini, ollama])

    result = hive.dispatch_reasoning(
        "Test execution accounting.",
    )

    execution = result.metadata["worker_execution"]

    assert execution == {
        "selected": "gemini",
        "executed": "gemini",
        "fallback_used": False,
    }

    assert gemini.last_task
    assert gemini.last_system == (
        "You are the reasoning system for RichardLab."
    )


class FailingWorker(FakeWorker):
    def execute(self, task, *, system=None):
        self.executed = True
        self.last_task = task
        self.last_system = system
        raise RuntimeError("simulated primary worker failure")


def test_hive_falls_back_to_capable_worker():
    gemini = FailingWorker(
        "gemini",
        ("reasoning",),
        "Primary should not produce this.",
    )

    ollama = FakeWorker(
        "ollama",
        ("reasoning",),
        "Ollama handled the fallback.",
    )

    hive = build_test_hive([gemini, ollama])

    result = hive.dispatch_reasoning(
        "Test automatic worker fallback.",
    )

    assert gemini.executed is True
    assert ollama.executed is True

    assert result.worker == "ollama"
    assert result.provider == "ollama"
    assert result.result == "Ollama handled the fallback."

    assert result.metadata["worker_execution"] == {
        "selected": "gemini",
        "executed": "ollama",
        "fallback_used": True,
    }

    assert result.metadata["router_fallback"] is True
    assert result.metadata["router_primary_provider"] == "gemini"
