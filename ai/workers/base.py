from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Worker(ABC):
    """
    Base contract for every RichardLab worker.

    A worker represents a capable participant in the Hive.
    Providers and tools are implementation mechanisms underneath workers.
    """

    name: str
    kind: str
    description: str
    capabilities: tuple[str, ...]

    def __init__(
        self,
        *,
        name: str,
        kind: str,
        description: str,
        capabilities: tuple[str, ...],
    ) -> None:
        self.name = name
        self.kind = kind
        self.description = description
        self.capabilities = capabilities

    def can_handle(self, capability: str) -> bool:
        return capability in self.capabilities

    def info(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "description": self.description,
            "capabilities": list(self.capabilities),
        }

    @abstractmethod
    def health(self) -> dict[str, Any]:
        """Return the current worker health state."""
        raise NotImplementedError

    @abstractmethod
    def execute(self, task: Any) -> Any:
        """Execute a task assigned to this worker."""
        raise NotImplementedError
