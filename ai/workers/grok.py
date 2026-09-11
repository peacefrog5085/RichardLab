from __future__ import annotations

from typing import Any

from .base import Worker


class GrokWorker(Worker):
    """RichardLab worker for the Grok/xAI AI interface."""

    def __init__(self, config, provider_factory) -> None:
        super().__init__(
            name="grok",
            kind="ai",
            description="Grok reasoning, analysis, and independent review worker.",
            capabilities=(
                "reasoning",
                "analysis",
                "synthesis",
                "research",
                "hypothesis_generation",
                "independent_review",
            ),
        )

        self.config = config
        self.provider_factory = provider_factory
        self.provider = provider_factory("grok", config)

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
