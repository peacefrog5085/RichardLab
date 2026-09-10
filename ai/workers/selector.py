from __future__ import annotations

from dataclasses import dataclass

from .base import Worker
from .registry import WorkerRegistry


@dataclass(frozen=True)
class WorkerSelection:
    """Deterministic worker-selection decision."""

    capability: str
    candidates: tuple[str, ...]
    selected: str | None
    reason: str


class WorkerSelector:
    """Select workers from a registry without executing them."""

    def __init__(self, registry: WorkerRegistry) -> None:
        self.registry = registry

    def select(self, capability: str) -> WorkerSelection:
        candidates: list[Worker] = self.registry.find_capable(
            capability
        )

        candidate_names = tuple(
            worker.name
            for worker in candidates
        )

        if not candidates:
            return WorkerSelection(
                capability=capability,
                candidates=(),
                selected=None,
                reason="no worker advertises this capability",
            )

        if len(candidates) == 1:
            return WorkerSelection(
                capability=capability,
                candidates=candidate_names,
                selected=candidates[0].name,
                reason="exact capability match with one available worker",
            )

        return WorkerSelection(
            capability=capability,
            candidates=candidate_names,
            selected=None,
            reason="multiple workers advertise this capability",
        )
