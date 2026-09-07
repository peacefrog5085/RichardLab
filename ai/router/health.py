from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProviderHealth:
    provider: str
    status: str
    reason: str | None = None
    model: str | None = None
    latency_seconds: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def usable(self):
        return self.status in {
            "READY",
            "DEGRADED",
        }

    def as_dict(self):
        return {
            "provider": self.provider,
            "status": self.status,
            "reason": self.reason,
            "model": self.model,
            "latency_seconds": self.latency_seconds,
            "metadata": self.metadata,
        }
