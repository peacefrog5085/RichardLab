from iot.discovery.neighbor import get_neighbor_mac


def test_neighbor_parser_finds_mac(monkeypatch):
    class Result:
        stdout = (
            "192.168.1.1 dev wlp0s20f3 "
            "lladdr E4:6C:D1:50:7F:1E REACHABLE\n"
        )

    def fake_run(*args, **kwargs):
        return Result()

    monkeypatch.setattr(
        "iot.discovery.neighbor.subprocess.run",
        fake_run,
    )

    assert get_neighbor_mac("192.168.1.1") == "e4:6c:d1:50:7f:1e"


def test_neighbor_parser_returns_none_without_mac(monkeypatch):
    class Result:
        stdout = "192.168.1.50 dev wlp0s20f3 FAILED\n"

    def fake_run(*args, **kwargs):
        return Result()

    monkeypatch.setattr(
        "iot.discovery.neighbor.subprocess.run",
        fake_run,
    )

    assert get_neighbor_mac("192.168.1.50") is None
