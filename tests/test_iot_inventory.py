import json

from iot.inventory import DeviceInventory
from iot.models import DeviceObservation


def test_inventory_records_device(tmp_path):
    inventory = DeviceInventory(tmp_path / "inventory.json")

    device = DeviceObservation(
        ip="192.168.1.50",
        hostname="test-device",
        open_ports=[80],
        protocols=["http"],
    )

    inventory.record(device)

    assert inventory.get("192.168.1.50")["hostname"] == "test-device"


def test_inventory_updates_existing_device(tmp_path):
    inventory = DeviceInventory(tmp_path / "inventory.json")

    first = DeviceObservation(
        ip="192.168.1.50",
        open_ports=[80],
        protocols=["http"],
    )

    second = DeviceObservation(
        ip="192.168.1.50",
        open_ports=[80, 443],
        protocols=["http", "https"],
    )

    inventory.record(first)
    inventory.record(second)

    devices = inventory.all()

    assert len(devices) == 1
    assert devices[0]["open_ports"] == [80, 443]


def test_inventory_file_is_valid_json(tmp_path):
    path = tmp_path / "inventory.json"
    inventory = DeviceInventory(path)

    inventory.record(
        DeviceObservation(ip="192.168.1.60")
    )

    with path.open() as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert data[0]["ip"] == "192.168.1.60"
