from __future__ import annotations

from typing import Any

from .base import Worker


class CodexWorker(Worker):
    """RichardLab worker for the Codex engineering interface."""

    def __init__(self, config, provider_factory) -> None:
        super().__init__(
            name="codex",
            kind="ai",
            description="Software engineering and repository implementation worker.",
            capabilities=(
                "engineering",
                "code_analysis",
                "repository_inspection",
                "implementation",
                "debugging",
                "testing",
                "refactoring",
            ),
        )

        self.config = config
        self.provider_factory = provider_factory
        self.provider = provider_factory("codex", config)

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
