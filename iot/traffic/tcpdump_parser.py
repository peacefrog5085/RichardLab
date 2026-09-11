import re

from iot.traffic.observer import TrafficObserver


_TCPDUMP_RE = re.compile(
    r"^\S+\s+IP\s+"
    r"(?P<src>[^ ]+)\s+>\s+"
    r"(?P<dst>[^:]+):\s+"
    r"(?P<proto>tcp|udp)\s+"
    r"(?P<length>\d+)"
)


def _split_endpoint(value: str) -> tuple[str, int | None]:
    """
    Split tcpdump's endpoint representation into host and port.

    IPv4 is the initial target. IPv6 support will be added separately
    rather than pretending regex is a networking protocol.
    """
    if "." not in value:
        return value, None

    host, separator, port = value.rpartition(".")

    if not separator:
        return value, None

    try:
        return host, int(port)
    except ValueError:
        return value, None


def parse_line(
    line: str,
    observer: TrafficObserver,
) -> bool:
    """
    Parse one tcpdump -q IPv4 line.

    Returns True when a packet was successfully recorded.
    Payload contents are never parsed or stored.
    """
    match = _TCPDUMP_RE.match(line.strip())

    if not match:
        return False

    source_ip, source_port = _split_endpoint(match.group("src"))
    destination_ip, destination_port = _split_endpoint(
        match.group("dst")
    )

    observer.record(
        source_ip=source_ip,
        destination_ip=destination_ip,
        protocol=match.group("proto").upper(),
        source_port=source_port,
        destination_port=destination_port,
        packet_length=int(match.group("length")),
    )

    return True


def parse_lines(
    lines: list[str],
    observer: TrafficObserver | None = None,
) -> TrafficObserver:
    """
    Parse tcpdump metadata into an aggregated TrafficObserver.
    """
    if observer is None:
        observer = TrafficObserver()

    for line in lines:
        parse_line(line, observer)

    return observer
