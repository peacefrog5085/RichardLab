from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class AIResponse:
    text: str
    provider: str
    model: str | None = None
    elapsed_seconds: float | None = None
    metadata: dict[str, Any] | None = None


class AIProvider(ABC):
    name = "unknown"

    @abstractmethod
    def health(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def ask(self, prompt: str, system: str | None = None) -> AIResponse:
        raise NotImplementedError
