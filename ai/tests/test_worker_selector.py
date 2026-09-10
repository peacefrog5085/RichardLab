from ai.workers import WorkerRegistry, WorkerSelector
from ai.workers.base import Worker


class FakeWorker(Worker):
    def __init__(self, name, capabilities):
        super().__init__(
            name=name,
            kind="test",
            description="Test worker.",
            capabilities=tuple(capabilities),
        )

    def health(self):
        return {"status": "READY"}

    def execute(self, task):
        raise AssertionError(
            "WorkerSelector must never execute a worker."
        )


def make_registry():
    registry = WorkerRegistry()

    registry.register(
        FakeWorker(
            "gemini",
            (
                "reasoning",
                "analysis",
                "research",
            ),
        )
    )

    registry.register(
        FakeWorker(
            "ollama",
            (
                "reasoning",
                "analysis",
                "local_reasoning",
            ),
        )
    )

    registry.register(
        FakeWorker(
            "codex",
            (
                "engineering",
                "debugging",
                "implementation",
            ),
        )
    )

    return registry


def test_selects_single_capability_match():
    selector = WorkerSelector(make_registry())

    result = selector.select("debugging")

    assert result.capability == "debugging"
    assert result.candidates == ("codex",)
    assert result.selected == "codex"
    assert "one available worker" in result.reason


def test_returns_multiple_candidates_without_guessing():
    selector = WorkerSelector(make_registry())

    result = selector.select("reasoning")

    assert result.capability == "reasoning"
    assert result.candidates == ("gemini", "ollama")
    assert result.selected is None
    assert "multiple workers" in result.reason


def test_reports_unknown_capability():
    selector = WorkerSelector(make_registry())

    result = selector.select("time_travel")

    assert result.capability == "time_travel"
    assert result.candidates == ()
    assert result.selected is None
    assert "no worker" in result.reason


def test_selection_does_not_execute_workers():
    selector = WorkerSelector(make_registry())

    result = selector.select("engineering")

    assert result.selected == "codex"
