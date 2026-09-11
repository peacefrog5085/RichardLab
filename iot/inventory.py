import json
from pathlib import Path

from iot.change_detection import compare_devices
from iot.models import DeviceObservation


class DeviceInventory:
    def __init__(self, path: str | Path = "data/iot_inventory.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> list[dict]:
        if not self.path.exists():
            return []

        with self.path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("IoT inventory must contain a JSON list")

        return data

    def save(self, devices: list[dict]) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(devices, f, indent=2, sort_keys=True)

    def record(self, device: DeviceObservation) -> None:
        devices = self.load()
        record = device.to_dict()

        for index, existing in enumerate(devices):
            if existing.get("ip") == device.ip:
                devices[index] = record
                self.save(devices)
                return

        devices.append(record)
        self.save(devices)

    def record_with_changes(self, device: DeviceObservation) -> dict:
        """
        Compare the current observation with the stored observation,
        then persist the current observation.

        Returns a deterministic change report.
        """
        devices = self.load()
        record = device.to_dict()

        previous = None

        for existing in devices:
            if existing.get("ip") == device.ip:
                previous = existing
                break

        changes = compare_devices(previous, record)

        self.record(device)

        return changes.to_dict()

    def get(self, ip: str) -> dict | None:
        for device in self.load():
            if device.get("ip") == ip:
                return device

        return None

    def all(self) -> list[dict]:
        return self.load()
