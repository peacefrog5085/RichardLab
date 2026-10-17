import json
from datetime import datetime, timedelta, timezone

import pytest

from ai.integrations.gateway import Approval, IntegrationGateway, IntegrationPolicyError, redact
from ai.integrations.registry import IntegrationRegistry


def write_registry(tmp_path, *, enabled=True, status="verified", access="read_only"):
    path = tmp_path / "registry.json"
    path.write_text(json.dumps({
        "schema_version": 1,
        "defaults": {
            "enabled": enabled,
            "connection_status": status,
            "access": access,
            "writes_require_approval": True,
        },
        "integrations": [{
            "id": "example",
            "purpose": "test boundary",
            "capabilities": ["records.read", "records.write"],
        }],
    }), encoding="utf-8")
    return IntegrationRegistry(path)


def test_production_registry_defaults_every_capability_disabled_and_unverified():
    capabilities = IntegrationRegistry().list()
    assert capabilities
    assert all(not item.enabled for item in capabilities)
    assert all(item.connection_status == "unverified" for item in capabilities)
    assert all(item.access == "read_only" for item in capabilities)


def test_disabled_integration_fails_closed(tmp_path):
    gateway = IntegrationGateway(write_registry(tmp_path, enabled=False), lambda event: None)
    with pytest.raises(IntegrationPolicyError, match="disabled or unverified"):
        gateway.execute(
            operation_id="op-1", integration_id="example", capability_name="records.read",
            inputs={}, adapter=lambda inputs: "must not run",
        )


def test_verified_read_runs_without_write_approval_and_records_provenance(tmp_path):
    events = []
    gateway = IntegrationGateway(write_registry(tmp_path), events.append)
    result = gateway.execute(
        operation_id="op-read", integration_id="example", capability_name="records.read",
        inputs={"query": "safe", "api_token": "never-log-this"}, adapter=lambda inputs: [1],
    )
    assert result == [1]
    assert [event["event"] for event in events] == ["integration.request", "integration.success"]
    assert events[0]["inputs"]["api_token"] == "[REDACTED]"
    assert events[0]["operation_id"] == "op-read"
    assert len(events[0]["input_sha256"]) == 64


def test_write_is_blocked_by_read_only_policy_even_with_approval(tmp_path):
    approval = Approval(
        operation_id="op-write", integration_id="example", capability="records.write",
        actor="reviewer", expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    )
    gateway = IntegrationGateway(write_registry(tmp_path), lambda event: None)
    with pytest.raises(IntegrationPolicyError, match="read-only"):
        gateway.execute(
            operation_id="op-write", integration_id="example", capability_name="records.write",
            inputs={}, adapter=lambda inputs: None, approval=approval,
        )


def test_write_requires_exact_unexpired_approval(tmp_path):
    gateway = IntegrationGateway(write_registry(tmp_path, access="read_write"), lambda event: None)
    wrong = Approval(
        operation_id="another-operation", integration_id="example", capability="records.write",
        actor="reviewer", expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    )
    with pytest.raises(IntegrationPolicyError, match="approval"):
        gateway.execute(
            operation_id="op-write", integration_id="example", capability_name="records.write",
            inputs={}, adapter=lambda inputs: None, approval=wrong,
        )


def test_redaction_handles_nested_secret_fields_and_token_values():
    value = {"nested": [{"password": "visible"}], "note": "key ghp_abcdefghijklmnop"}
    redacted = redact(value)
    assert redacted["nested"][0]["password"] == "[REDACTED]"
    assert "ghp_" not in redacted["note"]
