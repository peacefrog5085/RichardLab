from iot.models import DeviceObservation
from iot.traffic.observer import TrafficObserver
from iot.traffic.report import build_traffic_report


def test_report_classifies_internet_flow():
    observer = TrafficObserver()

    observer.record(
        source_ip="192.168.1.165",
        destination_ip="104.18.32.47",
        protocol="TCP",
        source_port=54742,
        destination_port=443,
        packet_length=12662,
    )

    report = build_traffic_report(
        flows=observer.snapshot(),
        interface="wlp0s20f3",
        duration_seconds=10,
        local_network="192.168.1.0/24",
    )

    assert report.summary["total_flows"] == 1
    assert report.summary["internet_flows"] == 1
    assert report.flows[0]["source_class"] == "LOCAL_NETWORK"
    assert report.flows[0]["destination_class"] == "PUBLIC_INTERNET"


def test_report_correlates_known_device():
    observer = TrafficObserver()

    observer.record(
        source_ip="192.168.1.165",
        destination_ip="192.168.1.226",
        protocol="TCP",
        source_port=40000,
        destination_port=8443,
        packet_length=500,
    )

    device = DeviceObservation(
        ip="192.168.1.226",
        mac="78:80:38:68:1a:a0",
    )

    report = build_traffic_report(
        flows=observer.snapshot(),
        interface="wlp0s20f3",
        duration_seconds=10,
        local_network="192.168.1.0/24",
        inventory=[device],
    )

    assert report.summary["lan_flows"] == 1
    assert report.flows[0]["destination_known_device"] is True
    assert report.inventory_notes == [
        "192.168.1.226: traffic observed during capture window"
    ]


def test_report_distinguishes_unobserved_inventory_device():
    observer = TrafficObserver()

    device = DeviceObservation(
        ip="192.168.1.226",
        mac="78:80:38:68:1a:a0",
    )

    report = build_traffic_report(
        flows=observer.snapshot(),
        interface="wlp0s20f3",
        duration_seconds=10,
        local_network="192.168.1.0/24",
        inventory=[device],
    )

    assert report.summary["total_flows"] == 0
    assert report.inventory_notes == [
        "192.168.1.226: no traffic observed during capture window"
    ]


def test_report_serializes():
    observer = TrafficObserver()

    observer.record(
        source_ip="127.0.0.1",
        destination_ip="127.0.0.1",
        protocol="TCP",
        source_port=1000,
        destination_port=2000,
        packet_length=50,
    )

    report = build_traffic_report(
        flows=observer.snapshot(),
        interface="lo",
        duration_seconds=1,
        local_network="192.168.1.0/24",
    )

    data = report.to_dict()

    assert data["interface"] == "lo"
    assert data["duration_seconds"] == 1
    assert data["summary"]["localhost_flows"] == 1
    assert len(data["flows"]) == 1
