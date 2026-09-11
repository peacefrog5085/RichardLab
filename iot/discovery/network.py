import ipaddress
import socket
from typing import Iterable

from iot.discovery.neighbor import get_neighbor_mac
from iot.models import DeviceObservation


COMMON_PORTS = (
    22,
    23,
    53,
    80,
    443,
    1883,
    5683,
    8080,
    8443,
)


def discover_hosts(
    network: str,
    ports: Iterable[int] = COMMON_PORTS,
    timeout: float = 0.25,
) -> list[DeviceObservation]:
    """
    Perform conservative TCP-based discovery against a network.

    This intentionally does not exploit, authenticate to, or modify
    discovered devices.
    """
    subnet = ipaddress.ip_network(network, strict=False)
    results: list[DeviceObservation] = []

    for address in subnet.hosts():
        ip = str(address)
        open_ports: list[int] = []

        for port in ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)

            try:
                if sock.connect_ex((ip, port)) == 0:
                    open_ports.append(port)
            finally:
                sock.close()

        if open_ports:
            hostname = None

            try:
                hostname = socket.gethostbyaddr(ip)[0]
            except (socket.herror, socket.gaierror, OSError):
                pass

            mac = get_neighbor_mac(ip)

            protocols = []

            if 22 in open_ports:
                protocols.append("ssh")
            if 23 in open_ports:
                protocols.append("telnet")
            if 80 in open_ports or 8080 in open_ports:
                protocols.append("http")
            if 443 in open_ports or 8443 in open_ports:
                protocols.append("https")
            if 1883 in open_ports:
                protocols.append("mqtt")
            if 5683 in open_ports:
                protocols.append("coap")

            results.append(
                DeviceObservation(
                    ip=ip,
                    mac=mac,
                    hostname=hostname,
                    open_ports=open_ports,
                    protocols=protocols,
                    observations=["tcp_service_detected"],
                )
            )

    return results
