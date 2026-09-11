from dataclasses import dataclass, field


@dataclass
class DeviceChanges:
    ip: str
    changes: list[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(self.changes)

    def to_dict(self) -> dict:
        return {
            "ip": self.ip,
            "changed": self.changed,
            "changes": list(self.changes),
        }


def compare_devices(previous: dict | None, current: dict) -> DeviceChanges:
    """
    Compare two observations of the same network device.

    This function only compares recorded evidence. It does not
    contact or modify network devices.
    """
    ip = current.get("ip", "")

    if previous is None:
        return DeviceChanges(
            ip=ip,
            changes=["new_device"],
        )

    changes: list[str] = []

    if previous.get("mac") != current.get("mac"):
        if previous.get("mac") and current.get("mac"):
            changes.append("mac_changed")

    if sorted(previous.get("open_ports", [])) != sorted(
        current.get("open_ports", [])
    ):
        changes.append("open_ports_changed")

    if sorted(previous.get("protocols", [])) != sorted(
        current.get("protocols", [])
    ):
        changes.append("protocols_changed")

    if previous.get("hostname") != current.get("hostname"):
        changes.append("hostname_changed")

    previous_vendor = previous.get("vendor")
    current_vendor = current.get("vendor")

    # Treat historical placeholder values such as "Unknown" as
    # equivalent to an absent vendor. Unknown is not an identity.
    if previous_vendor == "Unknown":
        previous_vendor = None

    if current_vendor == "Unknown":
        current_vendor = None

    if previous_vendor != current_vendor:
        changes.append("vendor_changed")

    if previous.get("device_type") != current.get("device_type"):
        changes.append("device_type_changed")

    if previous.get("confidence") != current.get("confidence"):
        changes.append("confidence_changed")

    return DeviceChanges(
        ip=ip,
        changes=changes,
    )
