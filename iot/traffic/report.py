from dataclasses import dataclass, field

from iot.models import DeviceObservation
from iot.traffic.classification import classify_ip
from iot.traffic.observer import TrafficFlow


@dataclass
class TrafficReport:
    interface: str
    duration_seconds: int
    flows: list[dict] = field(default_factory=list)
    summary: dict = field(default_factory=dict)
    inventory_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "interface": self.interface,
            "duration_seconds": self.duration_seconds,
            "summary": dict(self.summary),
            "flows": list(self.flows),
            "inventory_notes": list(self.inventory_notes),
        }


def build_traffic_report(
    flows: list[TrafficFlow],
    interface: str,
    duration_seconds: int,
    local_network: str,
    inventory: list[DeviceObservation] | None = None,
) -> TrafficReport:
    inventory = inventory or []

    known_devices = {
        device.ip: device
        for device in inventory
    }

    report_flows = []
    lan_count = 0
    private_count = 0
    internet_count = 0
    localhost_count = 0
    invalid_count = 0

    observed_ips: set[str] = set()

    for flow in flows:
        source_class = classify_ip(
            flow.source_ip,
            local_network,
        )
        destination_class = classify_ip(
            flow.destination_ip,
            local_network,
        )

        observed_ips.add(flow.source_ip)
        observed_ips.add(flow.destination_ip)

        if source_class == "LOOPBACK" or destination_class == "LOOPBACK":
            localhost_count += 1

        if (
            source_class == "LOCAL_NETWORK"
            or destination_class == "LOCAL_NETWORK"
        ):
            lan_count += 1

        if (
            source_class == "PRIVATE_NETWORK"
            or destination_class == "PRIVATE_NETWORK"
        ):
            private_count += 1

        if (
            source_class == "PUBLIC_INTERNET"
            or destination_class == "PUBLIC_INTERNET"
        ):
            internet_count += 1

        if (
            source_class == "INVALID"
            or destination_class == "INVALID"
        ):
            invalid_count += 1

        report_flows.append(
            {
                **flow.to_dict(),
                "source_class": source_class,
                "destination_class": destination_class,
                "source_known_device": flow.source_ip in known_devices,
                "destination_known_device": flow.destination_ip in known_devices,
            }
        )

    inventory_notes = []

    for device in inventory:
        if device.ip in observed_ips:
            inventory_notes.append(
                f"{device.ip}: traffic observed during capture window"
            )
        else:
            inventory_notes.append(
                f"{device.ip}: no traffic observed during capture window"
            )

    summary = {
        "total_flows": len(flows),
        "lan_flows": lan_count,
        "private_flows": private_count,
        "internet_flows": internet_count,
        "localhost_flows": localhost_count,
        "invalid_flows": invalid_count,
    }

    return TrafficReport(
        interface=interface,
        duration_seconds=duration_seconds,
        flows=report_flows,
        summary=summary,
        inventory_notes=inventory_notes,
    )
