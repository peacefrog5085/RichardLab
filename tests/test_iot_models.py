from iot.models import DeviceObservation


def test_device_observation_serializes():
    device = DeviceObservation(
        ip="192.168.1.10",
        hostname="test-device",
        open_ports=[443, 80],
        protocols=["https", "http"],
    )

    data = device.to_dict()

    assert data["ip"] == "192.168.1.10"
    assert data["hostname"] == "test-device"
    assert data["open_ports"] == [80, 443]
    assert data["protocols"] == ["http", "https"]
