import re
import subprocess


_MAC_RE = re.compile(
    r"lladdr\s+([0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5})"
)


def get_neighbor_mac(ip: str) -> str | None:
    """
    Return the MAC address Linux currently associates with an IPv4
    neighbor, or None when no MAC is available.
    """
    try:
        result = subprocess.run(
            ["ip", "neigh", "show", ip],
            capture_output=True,
            text=True,
            timeout=2.0,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    match = _MAC_RE.search(result.stdout)

    if not match:
        return None

    return match.group(1).lower()
