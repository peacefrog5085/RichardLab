from ai.gateway import build_provider, load_config
from ai.workers import WorkerRegistry, WorkerPolicy
from ai.workers.base import Worker
from ai.workers.codex import CodexWorker
from ai.workers.gemini import GeminiWorker
from ai.workers.ollama import OllamaWorker


def provider_factory(name, cfg):
    return build_provider(name, cfg)


def build_real_registry(config):
    registry = WorkerRegistry()

    for worker in (
        GeminiWorker(config, provider_factory),
        OllamaWorker(config, provider_factory),
        CodexWorker(config, provider_factory),
    ):
        registry.register(worker)

    return registry


def test_reasoning_uses_configured_primary():
    config = load_config()
    registry = build_real_registry(config)
    policy = WorkerPolicy(registry, config)

    decision = policy.select("reasoning")

    assert decision.candidates == ("gemini", "ollama")
    assert decision.selected == "gemini"
    assert decision.policy == "routing_primary"


def test_unique_capability_selects_worker():
    config = load_config()
    registry = build_real_registry(config)
    policy = WorkerPolicy(registry, config)

    decision = policy.select("engineering")

    assert decision.candidates == ("codex",)
    assert decision.selected == "codex"
    assert decision.policy == "unique_capability"


def test_ollama_unique_capability():
    config = load_config()
    registry = build_real_registry(config)
    policy = WorkerPolicy(registry, config)

    decision = policy.select("local_reasoning")

    assert decision.candidates == ("ollama",)
    assert decision.selected == "ollama"
    assert decision.policy == "unique_capability"


def test_unknown_capability_is_not_invented():
    config = load_config()
    registry = build_real_registry(config)
    policy = WorkerPolicy(registry, config)

    decision = policy.select("time_travel")

    assert decision.candidates == ()
    assert decision.selected is None
    assert decision.policy == "capability_match"


class FakeWorker(Worker):
    def __init__(self, name, capabilities):
        super().__init__(
            name=name,
            kind="test",
            description="Test worker",
            capabilities=tuple(capabilities),
        )
        self.executed = False

    def health(self):
        return {"status": "READY"}

    def execute(self, task):
        self.executed = True
        raise AssertionError("WorkerPolicy must not execute workers")


def test_policy_does_not_execute_workers():
    config = {
        "routing": {
            "primary": "fake-a",
            "fallback": "fake-b",
            "allow_automatic_fallback": True,
        }
    }

    worker_a = FakeWorker("fake-a", ("reasoning",))
    worker_b = FakeWorker("fake-b", ("reasoning",))

    registry = WorkerRegistry()
    registry.register(worker_a)
    registry.register(worker_b)

    policy = WorkerPolicy(registry, config)

    decision = policy.select("reasoning")

    assert decision.selected == "fake-a"
    assert worker_a.executed is False
    assert worker_b.executed is False
