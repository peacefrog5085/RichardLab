from iot.traffic.classification import classify_ip


def test_loopback():
    assert classify_ip("127.0.0.1") == "LOOPBACK"


def test_local_network():
    assert (
        classify_ip(
            "192.168.1.226",
            local_network="192.168.1.0/24",
        )
        == "LOCAL_NETWORK"
    )


def test_private_network():
    assert classify_ip("10.0.0.50") == "PRIVATE_NETWORK"


def test_public_internet():
    assert classify_ip("104.18.32.47") == "PUBLIC_INTERNET"


def test_invalid_address():
    assert classify_ip("not-an-ip") == "INVALID"


def test_local_network_takes_precedence():
    assert (
        classify_ip(
            "192.168.1.165",
            local_network="192.168.1.0/24",
        )
        == "LOCAL_NETWORK"
    )
