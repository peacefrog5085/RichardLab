from unittest.mock import patch

from iot.discovery.fast import discover_hosts_fast, discover_live_hosts


def test_discover_live_hosts_finds_responsive_host():
    def fake_probe(ip, port, timeout):
        return ip, port, ip == "192.168.1.1" and port == 80

    with patch(
        "iot.discovery.fast._probe_port",
        side_effect=fake_probe,
    ):
        result = discover_live_hosts(
            "192.168.1.0/30",
            ports=[80, 443],
            timeout=0.01,
            workers=4,
        )

    assert result == {"192.168.1.1": {80}}

def test_discover_live_hosts_records_open_ports():
    def fake_probe(ip, port, timeout):
        return ip, port, (
            ip == "192.168.1.1" and port in {53, 80}
        )

    with patch(
        "iot.discovery.fast._probe_port",
        side_effect=fake_probe,
    ):
        result = discover_live_hosts(
            "192.168.1.0/30",
            ports=[53, 80, 443],
            timeout=0.01,
            workers=4,
        )

    assert result["192.168.1.1"] == {53, 80}


def test_discover_hosts_fast_builds_observation():
    def fake_live_hosts(*args, **kwargs):
        return {
            "192.168.1.1": {53, 80, 443},
        }

    with patch(
        "iot.discovery.fast.discover_live_hosts",
        side_effect=fake_live_hosts,
    ), patch(
        "iot.discovery.fast.get_neighbor_mac",
        return_value=None,
    ), patch(
        "iot.discovery.fast.socket.gethostbyaddr",
        side_effect=OSError,
    ):
        results = discover_hosts_fast(
            "192.168.1.0/24",
        )

    assert len(results) == 1
    assert results[0].ip == "192.168.1.1"
    assert results[0].open_ports == [53, 80, 443]
    assert set(results[0].protocols) == {"http", "https"}
    assert "fast_host_discovery" in results[0].observations
