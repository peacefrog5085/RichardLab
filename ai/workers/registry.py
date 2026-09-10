from __future__ import annotations

from typing import Iterable

from .base import Worker


class WorkerRegistry:
    """Registry of available RichardLab workers."""

    def __init__(self) -> None:
        self._workers: dict[str, Worker] = {}

    def register(self, worker: Worker) -> None:
        if worker.name in self._workers:
            raise ValueError(
                f"Worker already registered: {worker.name}"
            )

        self._workers[worker.name] = worker

    def get(self, name: str) -> Worker:
        try:
            return self._workers[name]
        except KeyError:
            raise KeyError(
                f"Unknown RichardLab worker: {name}"
            ) from None

    def list(self) -> list[Worker]:
        return list(self._workers.values())

    def names(self) -> list[str]:
        return list(self._workers)

    def find_capable(self, capability: str) -> list[Worker]:
        return [
            worker
            for worker in self._workers.values()
            if worker.can_handle(capability)
        ]

    def __len__(self) -> int:
        return len(self._workers)


def build_registry(workers: Iterable[Worker]) -> WorkerRegistry:
    registry = WorkerRegistry()

    for worker in workers:
        registry.register(worker)

    return registry
