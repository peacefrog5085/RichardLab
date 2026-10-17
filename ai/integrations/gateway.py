from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from .registry import IntegrationRegistry


SENSITIVE_KEY = re.compile(r"password|secret|token|api[_-]?key|authorization|cookie", re.I)
SENSITIVE_VALUE = re.compile(r"(?:sk-|xai-|gh[pousr]_)[A-Za-z0-9_-]{12,}")


class IntegrationPolicyError(PermissionError):
    pass


@dataclass(frozen=True)
class Approval:
    operation_id: str
    integration_id: str
    capability: str
    actor: str
    expires_at: datetime

    def permits(self, operation_id: str, integration_id: str, capability: str) -> bool:
        now = datetime.now(timezone.utc)
        expiry = self.expires_at
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        return (
            self.operation_id == operation_id
            and self.integration_id == integration_id
            and self.capability == capability
            and bool(self.actor.strip())
            and expiry > now
        )


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if SENSITIVE_KEY.search(str(key)) else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact(item) for item in value]
    if isinstance(value, str):
        return SENSITIVE_VALUE.sub("[REDACTED]", value)
    return value


class IntegrationGateway:
    """Policy boundary for adapters supplied by the application.

    The gateway contains no credentials and performs no network I/O itself.
    """

    def __init__(self, registry: IntegrationRegistry, audit_sink: Callable[[dict[str, Any]], None]) -> None:
        self.registry = registry
        self.audit_sink = audit_sink

    def execute(
        self,
        *,
        operation_id: str,
        integration_id: str,
        capability_name: str,
        inputs: dict[str, Any],
        adapter: Callable[[dict[str, Any]], Any],
        approval: Approval | None = None,
    ) -> Any:
        capability = self.registry.get(integration_id, capability_name)
        if not capability.enabled or capability.connection_status != "verified":
            raise IntegrationPolicyError("Integration is disabled or unverified")
        if capability.mutates_state:
            if capability.access == "read_only":
                raise IntegrationPolicyError("Capability is blocked by read-only access")
            if capability.writes_require_approval and (
                approval is None
                or not approval.permits(operation_id, integration_id, capability_name)
            ):
                raise IntegrationPolicyError("Exact, unexpired approval is required")

        sanitized_inputs = redact(inputs)
        provenance = {
            "operation_id": operation_id,
            "integration_id": integration_id,
            "capability": capability_name,
            "actor": approval.actor if approval else "system-read-only",
            "input_sha256": hashlib.sha256(
                json.dumps(sanitized_inputs, sort_keys=True, default=str).encode("utf-8")
            ).hexdigest(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.audit_sink({"event": "integration.request", **provenance, "inputs": sanitized_inputs})
        try:
            result = adapter(inputs)
        except Exception as exc:
            self.audit_sink({
                "event": "integration.failure",
                **provenance,
                "error_type": type(exc).__name__,
            })
            raise
        self.audit_sink({"event": "integration.success", **provenance})
        return result
