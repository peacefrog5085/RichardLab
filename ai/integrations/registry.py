from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


REGISTRY_PATH = Path(__file__).with_name("registry.json")
WRITE_SUFFIXES = (".write", ".send", ".run", ".delete", ".deploy")


@dataclass(frozen=True)
class Capability:
    integration_id: str
    name: str
    purpose: str
    enabled: bool
    connection_status: str
    access: str
    writes_require_approval: bool

    @property
    def mutates_state(self) -> bool:
        return self.name.endswith(WRITE_SUFFIXES)


class IntegrationRegistry:
    """Loads declared capabilities; absence and malformed data fail closed."""

    def __init__(self, path: Path = REGISTRY_PATH) -> None:
        self.path = Path(path)
        self._capabilities = self._load()

    def _load(self) -> dict[tuple[str, str], Capability]:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if data.get("schema_version") != 1:
            raise ValueError("Unsupported integration registry schema")

        defaults = data.get("defaults", {})
        result: dict[tuple[str, str], Capability] = {}
        for integration in data.get("integrations", []):
            integration_id = integration["id"]
            for name in integration.get("capabilities", []):
                key = (integration_id, name)
                if key in result:
                    raise ValueError(f"Duplicate capability: {integration_id}/{name}")
                result[key] = Capability(
                    integration_id=integration_id,
                    name=name,
                    purpose=integration["purpose"],
                    enabled=bool(integration.get("enabled", defaults.get("enabled", False))),
                    connection_status=integration.get("connection_status", defaults.get("connection_status", "unverified")),
                    access=integration.get("access", defaults.get("access", "read_only")),
                    writes_require_approval=bool(integration.get("writes_require_approval", defaults.get("writes_require_approval", True))),
                )
        return result

    def get(self, integration_id: str, capability: str) -> Capability:
        try:
            return self._capabilities[(integration_id, capability)]
        except KeyError as exc:
            raise KeyError(f"Undeclared capability: {integration_id}/{capability}") from exc

    def list(self) -> tuple[Capability, ...]:
        return tuple(self._capabilities.values())
