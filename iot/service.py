from iot.discovery import discover_hosts
from iot.fingerprint import fingerprint
from iot.http_probe import probe_http
from iot.inventory import DeviceInventory


class IoTService:
    """
    High-level IoT discovery workflow.

    Performs discovery, read-only protocol probing, deterministic
    fingerprinting, change detection, and inventory recording.
    """

    def __init__(self, inventory_path="data/iot_inventory.json"):
        self.inventory = DeviceInventory(inventory_path)

    def discover(
        self,
        network: str,
        ports=None,
        timeout: float = 0.25,
        probe_http_services: bool = True,
    ):
        kwargs = {"timeout": timeout}

        if ports is not None:
            kwargs["ports"] = ports

        devices = discover_hosts(network, **kwargs)

        results = []

        for device in devices:

            # First collect communication evidence.
            if probe_http_services:
                self._probe_http(device, timeout)

            # Then interpret ALL collected evidence.
            device = fingerprint(device)

            # Compare against the previous inventory state and persist
            # the current observation.
            change_report = self.inventory.record_with_changes(device)

            device.changes = change_report["changes"]

            results.append(device)

        return results

    def _probe_http(self, device, timeout: float) -> None:
        http_ports = []

        if 80 in device.open_ports:
            http_ports.append(80)

        if 8080 in device.open_ports:
            http_ports.append(8080)

        for port in http_ports:
            result = probe_http(
                device.ip,
                port=port,
                timeout=min(timeout, 2.0),
            )

            device.http_evidence.append(result.to_dict())
            device.observations.append(
                f"http_probe:{port}:{result.status}"
            )
