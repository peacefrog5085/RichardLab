from iot.change_detection import compare_devices


def test_new_device():
    result = compare_devices(
        None,
        {"ip": "192.168.1.50"},
    )

    assert result.changed is True
    assert result.changes == ["new_device"]


def test_no_change():
    device = {
        "ip": "192.168.1.50",
        "mac": "aa:bb:cc:dd:ee:ff",
        "hostname": "camera",
        "vendor": "Example",
        "device_type": "probable_iot",
        "confidence": 0.55,
        "open_ports": [80, 1883],
        "protocols": ["http", "mqtt"],
    }

    result = compare_devices(device, dict(device))

    assert result.changed is False
    assert result.changes == []


def test_mac_change():
    previous = {
        "ip": "192.168.1.50",
        "mac": "aa:bb:cc:dd:ee:ff",
    }

    current = {
        "ip": "192.168.1.50",
        "mac": "11:22:33:44:55:66",
    }

    result = compare_devices(previous, current)

    assert result.changed is True
    assert "mac_changed" in result.changes


def test_port_change():
    previous = {
        "ip": "192.168.1.50",
        "open_ports": [80],
    }

    current = {
        "ip": "192.168.1.50",
        "open_ports": [80, 443],
    }

    result = compare_devices(previous, current)

    assert "open_ports_changed" in result.changes


def test_protocol_change():
    previous = {
        "ip": "192.168.1.50",
        "protocols": ["http"],
    }

    current = {
        "ip": "192.168.1.50",
        "protocols": ["http", "mqtt"],
    }

    result = compare_devices(previous, current)

    assert "protocols_changed" in result.changes


def test_multiple_changes():
    previous = {
        "ip": "192.168.1.50",
        "mac": "aa:bb:cc:dd:ee:ff",
        "open_ports": [80],
        "protocols": ["http"],
    }

    current = {
        "ip": "192.168.1.50",
        "mac": "11:22:33:44:55:66",
        "open_ports": [443],
        "protocols": ["https"],
    }

    result = compare_devices(previous, current)

    assert result.changed is True
    assert "mac_changed" in result.changes
    assert "open_ports_changed" in result.changes
    assert "protocols_changed" in result.changes


def test_unknown_vendor_is_equivalent_to_missing_vendor():
    previous = {
        "ip": "192.168.1.1",
        "vendor": "Unknown",
    }

    current = {
        "ip": "192.168.1.1",
        "vendor": None,
    }

    result = compare_devices(previous, current)

    assert "vendor_changed" not in result.changes
