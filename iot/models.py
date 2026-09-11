from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DeviceObservation:
    ip: str
    mac: Optional[str] = None
    hostname: Optional[str] = None
    vendor: Optional[str] = None
    device_type: Optional[str] = None
    confidence: float = 0.0
    open_ports: list[int] = field(default_factory=list)
    protocols: list[str] = field(default_factory=list)
    observations: list[str] = field(default_factory=list)
    http_evidence: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "ip": self.ip,
            "mac": self.mac,
            "hostname": self.hostname,
            "vendor": self.vendor,
            "device_type": self.device_type,
            "confidence": self.confidence,
            "open_ports": sorted(self.open_ports),
            "protocols": sorted(self.protocols),
            "observations": list(self.observations),
            "http_evidence": list(self.http_evidence),
        }
