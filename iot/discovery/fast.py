from concurrent.futures import ThreadPoolExecutor, as_completed
import ipaddress
import socket
from typing import Iterable

from iot.discovery.neighbor import get_neighbor_mac
from iot.models import DeviceObservation


# Small set used only to determine whether an address is alive.
# These are common services, not exploit attempts.
PRESENCE_PORTS = (
    22,    # SSH
    53,    # DNS
    80,    # HTTP
    443,   # HTTPS
    1883,  # MQTT
    5683,  # CoAP
    8080,  # HTTP alternate
    8443,  # HTTPS alternate
)


def _probe_port(
    ip: str,
    port: int,
    timeout: float,
) -> tuple[str, int, bool]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)

    try:
        return ip, port, sock.connect_ex((ip, port)) == 0
    except OSError:
        return ip, port, False
    finally:
        sock.close()


def discover_live_hosts(
    network: str,
    ports: Iterable[int] = PRESENCE_PORTS,
    timeout: float = 0.15,
    workers: int = 64,
) -> dict[str, set[int]]:
    """
    Quickly identify IPv4 hosts responding on one or more TCP ports.

    This is intentionally read-only. It performs connection attempts
    only and does not authenticate, exploit, or modify remote systems.
    """
    subnet = ipaddress.ip_network(network, strict=False)
    addresses = [str(address) for address in subnet.hosts()]
    ports = tuple(ports)

    found: dict[str, set[int]] = {}

    jobs = [
        (ip, port)
        for ip in addresses
        for port in ports
    ]

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_probe_port, ip, port, timeout): (ip, port)
            for ip, port in jobs
        }

        for future in as_completed(futures):
            ip, port = futures[future]

            try:
                _, _, is_open = future.result()
            except Exception:
                continue

            if is_open:
                found.setdefault(ip, set()).add(port)

    return found


def discover_hosts_fast(
    network: str,
    ports: Iterable[int] = PRESENCE_PORTS,
    timeout: float = 0.15,
    workers: int = 64,
) -> list[DeviceObservation]:
    """
    Fast LAN discovery using parallel TCP presence checks.

    Only hosts with at least one responding service are returned.
    """
    live_hosts = discover_live_hosts(
        network,
        ports=ports,
        timeout=timeout,
        workers=workers,
    )

    results: list[DeviceObservation] = []

    for ip in sorted(live_hosts, key=ipaddress.ip_address):
        open_ports = sorted(live_hosts[ip])

        hostname = None
        try:
            hostname = socket.gethostbyaddr(ip)[0]
        except (socket.herror, socket.gaierror, OSError):
            pass

        mac = get_neighbor_mac(ip)

        protocols: list[str] = []

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
                observations=["tcp_service_detected", "fast_host_discovery"],
            )
        )

    return results
