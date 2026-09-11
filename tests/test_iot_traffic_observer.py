from iot.traffic.observer import TrafficObserver


def test_record_creates_flow():
    observer = TrafficObserver()

    observer.record(
        source_ip="192.168.1.165",
        destination_ip="192.168.1.1",
        protocol="TCP",
        source_port=50000,
        destination_port=443,
        packet_length=100,
    )

    flows = observer.snapshot()

    assert len(flows) == 1
    assert flows[0].source_ip == "192.168.1.165"
    assert flows[0].destination_ip == "192.168.1.1"
    assert flows[0].protocol == "TCP"
    assert flows[0].source_port == 50000
    assert flows[0].destination_port == 443
    assert flows[0].packets == 1
    assert flows[0].bytes == 100


def test_record_aggregates_same_flow():
    observer = TrafficObserver()

    for length in (100, 200, 300):
        observer.record(
            source_ip="192.168.1.165",
            destination_ip="192.168.1.1",
            protocol="TCP",
            source_port=50000,
            destination_port=443,
            packet_length=length,
        )

    flows = observer.snapshot()

    assert len(flows) == 1
    assert flows[0].packets == 3
    assert flows[0].bytes == 600


def test_different_flows_remain_separate():
    observer = TrafficObserver()

    observer.record(
        "192.168.1.165",
        "192.168.1.1",
        "TCP",
        50000,
        443,
        100,
    )

    observer.record(
        "192.168.1.165",
        "192.168.1.226",
        "TCP",
        50001,
        8443,
        200,
    )

    flows = observer.snapshot()

    assert len(flows) == 2


def test_clear_removes_observations():
    observer = TrafficObserver()

    observer.record(
        "192.168.1.165",
        "192.168.1.1",
        "UDP",
        50000,
        53,
        80,
    )

    assert len(observer.snapshot()) == 1

    observer.clear()

    assert observer.snapshot() == []
