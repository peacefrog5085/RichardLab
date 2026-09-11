import ipaddress


def classify_ip(ip: str, local_network: str | None = None) -> str:
    """
    Deterministically classify an IPv4 address.

    Results:
      LOOPBACK
      LOCAL_NETWORK
      PRIVATE_NETWORK
      PUBLIC_INTERNET
      INVALID
    """
    try:
        address = ipaddress.ip_address(ip)
    except ValueError:
        return "INVALID"

    if address.is_loopback:
        return "LOOPBACK"

    if local_network is not None:
        try:
            network = ipaddress.ip_network(local_network, strict=False)
            if address in network:
                return "LOCAL_NETWORK"
        except ValueError:
            pass

    if address.is_private:
        return "PRIVATE_NETWORK"

    return "PUBLIC_INTERNET"
