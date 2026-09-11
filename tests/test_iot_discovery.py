from iot.discovery.network import discover_hosts


def test_discovery_returns_empty_for_unreachable_test_network():
    result = discover_hosts(
        "192.0.2.0/30",
        ports=[1],
        timeout=0.01,
    )

    assert isinstance(result, list)
    assert result == []
