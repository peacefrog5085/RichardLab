from ai.integrations.registry import IntegrationRegistry


def test_only_github_read_capabilities_are_verified_and_disabled():
    registry = IntegrationRegistry()
    verified_reads = {
        "repository.read",
        "issues.read",
        "pull_requests.read",
        "checks.read",
    }

    for name in verified_reads:
        capability = registry.get("github", name)
        assert capability.connection_status == "verified"
        assert capability.enabled is False
        assert capability.access == "read_only"
        assert capability.mutates_state is False

    for name in {"repository.write", "issues.write", "pull_requests.write"}:
        capability = registry.get("github", name)
        assert capability.connection_status == "unverified"
        assert capability.enabled is False
        assert capability.access == "write"
        assert capability.writes_require_approval is True
        assert capability.mutates_state is True


def test_every_declared_capability_remains_disabled():
    assert all(not capability.enabled for capability in IntegrationRegistry().list())
