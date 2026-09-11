from iot.models import DeviceObservation
from iot.service import IoTService


def test_service_connects_discovery_fingerprint_and_inventory(
    tmp_path,
    monkeypatch,
):
    fake_device = DeviceObservation(
        ip="192.168.1.25",
        open_ports=[1883],
        protocols=["mqtt"],
    )

    monkeypatch.setattr(
        "iot.service.discover_hosts",
        lambda *args, **kwargs: [fake_device],
    )

    service = IoTService(tmp_path / "inventory.json")

    results = service.discover("192.168.1.0/24")

    assert len(results) == 1
    assert results[0].device_type == "probable_iot"
    assert results[0].confidence == 0.55

    stored = service.inventory.get("192.168.1.25")

    assert stored is not None
    assert stored["device_type"] == "probable_iot"
    assert stored["open_ports"] == [1883]
