from iot.discovery.network import discover_hosts


def test_discovery_attaches_neighbor_mac(monkeypatch):
    class FakeSocket:
        def settimeout(self, timeout):
            pass

        def connect_ex(self, address):
            return 0

        def close(self):
            pass

    monkeypatch.setattr(
        "iot.discovery.network.socket.socket",
        lambda *args, **kwargs: FakeSocket(),
    )

    monkeypatch.setattr(
        "iot.discovery.network.get_neighbor_mac",
        lambda ip: "e4:6c:d1:50:7f:1e",
    )

    results = discover_hosts(
        "192.0.2.1/32",
        ports=[80],
        timeout=0.01,
    )

    assert len(results) == 1
    assert results[0].mac == "e4:6c:d1:50:7f:1e"
