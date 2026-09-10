from __future__ import annotations

from typing import Any

from .base import Worker


class OllamaWorker(Worker):
    """RichardLab worker for the local Ollama AI interface."""

    def __init__(self, config, provider_factory) -> None:
        super().__init__(
            name="ollama",
            kind="ai",
            description="Local reasoning and analysis worker.",
            capabilities=(
                "reasoning",
                "analysis",
                "local_reasoning",
                "private_processing",
                "fallback_reasoning",
                "offline_capable",
            ),
        )

        self.config = config
        self.provider_factory = provider_factory
        self.provider = provider_factory("ollama", config)

    def health(self) -> dict[str, Any]:
        return self.provider.health()

    def execute(
        self,
        task: Any,
        *,
        system: str | None = None,
    ) -> Any:
        prompt = task if isinstance(task, str) else str(task)

        return self.provider.ask(
            prompt,
            system=system,
        )
