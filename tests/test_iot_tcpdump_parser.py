from iot.traffic.observer import TrafficObserver
from iot.traffic.tcpdump_parser import parse_line, parse_lines


def test_parse_tcpdump_tcp_line():
    observer = TrafficObserver()

    line = (
        "14:26:48.322488 IP "
        "192.168.1.165.33192 > "
        "173.194.133.2.443: tcp 3519"
    )

    assert parse_line(line, observer)

    flows = observer.snapshot()

    assert len(flows) == 1
    assert flows[0].source_ip == "192.168.1.165"
    assert flows[0].destination_ip == "173.194.133.2"
    assert flows[0].protocol == "TCP"
    assert flows[0].source_port == 33192
    assert flows[0].destination_port == 443
    assert flows[0].packets == 1
    assert flows[0].bytes == 3519


def test_parse_multiple_packets_aggregates_flow():
    lines = [
        "14:26:48.322488 IP 192.168.1.165.33192 > 173.194.133.2.443: tcp 3519",
        "14:26:48.333696 IP 173.194.133.2.443 > 192.168.1.165.33192: tcp 0",
        "14:26:48.376255 IP 173.194.133.2.443 > 192.168.1.165.33192: tcp 975",
    ]

    observer = parse_lines(lines)

    flows = observer.snapshot()

    assert len(flows) == 2

    outbound = next(
        flow for flow in flows
        if flow.source_ip == "192.168.1.165"
    )

    inbound = next(
        flow for flow in flows
        if flow.source_ip == "173.194.133.2"
    )

    assert outbound.packets == 1
    assert outbound.bytes == 3519

    assert inbound.packets == 2
    assert inbound.bytes == 975


def test_invalid_line_is_ignored():
    observer = TrafficObserver()

    assert not parse_line(
        "tcpdump: listening on wlp0s20f3",
        observer,
    )

    assert observer.snapshot() == []
