from dataclasses import dataclass
from datetime import datetime, timezone
from collections import defaultdict
from typing import Iterable


@dataclass(frozen=True)
class TrafficFlow:
    timestamp: str
    source_ip: str
    destination_ip: str
    protocol: str
    source_port: int | None
    destination_port: int | None
    packets: int
    bytes: int

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "source_ip": self.source_ip,
            "destination_ip": self.destination_ip,
            "protocol": self.protocol,
            "source_port": self.source_port,
            "destination_port": self.destination_port,
            "packets": self.packets,
            "bytes": self.bytes,
        }


class TrafficObserver:
    """
    Metadata-only traffic observer.

    This class intentionally stores flow metadata rather than packet
    payloads. It does not authenticate to devices or modify traffic.
    """

    def __init__(self):
        self._flows = defaultdict(
            lambda: {
                "packets": 0,
                "bytes": 0,
            }
        )

    def record(
        self,
        source_ip: str,
        destination_ip: str,
        protocol: str,
        source_port: int | None,
        destination_port: int | None,
        packet_length: int,
    ) -> None:
        key = (
            source_ip,
            destination_ip,
            protocol,
            source_port,
            destination_port,
        )

        self._flows[key]["packets"] += 1
        self._flows[key]["bytes"] += packet_length

    def snapshot(self) -> list[TrafficFlow]:
        timestamp = datetime.now(timezone.utc).isoformat()

        results = []

        for key, totals in sorted(self._flows.items()):
            (
                source_ip,
                destination_ip,
                protocol,
                source_port,
                destination_port,
            ) = key

            results.append(
                TrafficFlow(
                    timestamp=timestamp,
                    source_ip=source_ip,
                    destination_ip=destination_ip,
                    protocol=protocol,
                    source_port=source_port,
                    destination_port=destination_port,
                    packets=totals["packets"],
                    bytes=totals["bytes"],
                )
            )

        return results

    def clear(self) -> None:
        self._flows.clear()
