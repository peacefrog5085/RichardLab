from iot.fingerprint import fingerprint
from iot.models import DeviceObservation


def test_micro_httpd_adds_embedded_device_evidence():
    device = DeviceObservation(
        ip="192.168.1.1",
        open_ports=[80],
        protocols=["http"],
        http_evidence=[
            {
                "url": "http://192.168.1.1:80/",
                "status": 200,
                "server": "micro_httpd",
                "content_type": "text/html",
                "title": None,
                "error": None,
            }
        ],
    )

    result = fingerprint(device)

    assert result.device_type == "network_appliance"
    assert "http_server:micro_httpd" in result.observations
    assert result.confidence > 0.15


def test_http_error_does_not_create_server_identity():
    device = DeviceObservation(
        ip="192.168.1.50",
        open_ports=[80],
        protocols=["http"],
        http_evidence=[
            {
                "url": "http://192.168.1.50:80/",
                "status": None,
                "server": None,
                "content_type": None,
                "title": None,
                "error": "connection_error:TimeoutError",
            }
        ],
    )

    result = fingerprint(device)

    assert "http_server:None" not in result.observations
