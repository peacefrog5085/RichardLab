from __future__ import annotations

from dataclasses import dataclass

from .registry import WorkerRegistry
from .selector import WorkerSelection


@dataclass(frozen=True)
class WorkerPolicyDecision:
    """Deterministic worker-policy decision."""

    capability: str
    candidates: tuple[str, ...]
    selected: str | None
    policy: str
    reason: str


class WorkerPolicy:
    """Apply explicit worker-selection policy without executing workers."""

    def __init__(
        self,
        registry: WorkerRegistry,
        config: dict,
    ) -> None:
        self.registry = registry
        self.config = config

    def select(self, capability: str) -> WorkerPolicyDecision:
        candidates = self.registry.find_capable(capability)

        candidate_names = tuple(
            worker.name
            for worker in candidates
        )

        if not candidates:
            return WorkerPolicyDecision(
                capability=capability,
                candidates=(),
                selected=None,
                policy="capability_match",
                reason="no worker advertises this capability",
            )

        if len(candidates) == 1:
            return WorkerPolicyDecision(
                capability=capability,
                candidates=candidate_names,
                selected=candidates[0].name,
                policy="unique_capability",
                reason="exact capability match with one worker",
            )

        routing = self.config.get("routing", {})

        primary = routing.get("primary")
        fallback = routing.get("fallback")

        if primary in candidate_names:
            return WorkerPolicyDecision(
                capability=capability,
                candidates=candidate_names,
                selected=primary,
                policy="routing_primary",
                reason=(
                    f"{primary} is the configured primary provider "
                    "and advertises this capability"
                ),
            )

        if fallback in candidate_names:
            return WorkerPolicyDecision(
                capability=capability,
                candidates=candidate_names,
                selected=fallback,
                policy="routing_fallback",
                reason=(
                    f"{fallback} is the configured fallback provider "
                    "and advertises this capability"
                ),
            )

        return WorkerPolicyDecision(
            capability=capability,
            candidates=candidate_names,
            selected=None,
            policy="ambiguous",
            reason=(
                "multiple capable workers exist and none matches "
                "the configured routing preference"
            ),
        )
