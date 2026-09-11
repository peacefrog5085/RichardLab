from iot.inventory import DeviceInventory
from iot.models import DeviceObservation


def test_record_with_changes_detects_new_device(tmp_path):
    inventory = DeviceInventory(tmp_path / "inventory.json")

    device = DeviceObservation(
        ip="192.168.1.50",
        mac="aa:bb:cc:dd:ee:ff",
        open_ports=[80],
        protocols=["http"],
    )

    result = inventory.record_with_changes(device)

    assert result["ip"] == "192.168.1.50"
    assert result["changed"] is True
    assert result["changes"] == ["new_device"]

    assert inventory.get("192.168.1.50") is not None


def test_record_with_changes_detects_port_change(tmp_path):
    inventory = DeviceInventory(tmp_path / "inventory.json")

    first = DeviceObservation(
        ip="192.168.1.50",
        mac="aa:bb:cc:dd:ee:ff",
        open_ports=[80],
        protocols=["http"],
    )

    second = DeviceObservation(
        ip="192.168.1.50",
        mac="aa:bb:cc:dd:ee:ff",
        open_ports=[80, 443],
        protocols=["http", "https"],
    )

    inventory.record(first)

    result = inventory.record_with_changes(second)

    assert result["changed"] is True
    assert "open_ports_changed" in result["changes"]
    assert "protocols_changed" in result["changes"]


def test_record_with_changes_detects_no_change(tmp_path):
    inventory = DeviceInventory(tmp_path / "inventory.json")

    device = DeviceObservation(
        ip="192.168.1.50",
        mac="aa:bb:cc:dd:ee:ff",
        open_ports=[80],
        protocols=["http"],
    )

    inventory.record(device)

    result = inventory.record_with_changes(device)

    assert result["changed"] is False
    assert result["changes"] == []


def test_record_with_changes_updates_inventory(tmp_path):
    inventory = DeviceInventory(tmp_path / "inventory.json")

    first = DeviceObservation(
        ip="192.168.1.50",
        mac="aa:bb:cc:dd:ee:ff",
        open_ports=[80],
    )

    second = DeviceObservation(
        ip="192.168.1.50",
        mac="11:22:33:44:55:66",
        open_ports=[443],
    )

    inventory.record(first)
    inventory.record_with_changes(second)

    stored = inventory.get("192.168.1.50")

    assert stored["mac"] == "11:22:33:44:55:66"
    assert stored["open_ports"] == [443]
