from iot.fingerprint import fingerprint
from iot.models import DeviceObservation


def test_mqtt_device_is_identified_as_probable_iot():
    device = DeviceObservation(
        ip="192.168.1.20",
        open_ports=[1883],
        protocols=["mqtt"],
    )

    result = fingerprint(device)

    assert result.device_type == "probable_iot"
    assert result.confidence == 0.55
    assert "iot_protocol_detected" in result.observations


def test_http_device_is_identified_as_network_appliance():
    device = DeviceObservation(
        ip="192.168.1.30",
        open_ports=[80],
        protocols=["http"],
    )

    result = fingerprint(device)

    assert result.device_type == "network_appliance"
    assert result.confidence == 0.15


def test_unknown_device_remains_unclassified():
    device = DeviceObservation(
        ip="192.168.1.40",
        open_ports=[],
        protocols=[],
    )

    result = fingerprint(device)

    assert result.device_type is None
    assert result.confidence == 0.0
