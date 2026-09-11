from iot.models import DeviceObservation


def test_device_observation_supports_http_evidence():
    device = DeviceObservation(
        ip="192.168.1.1",
        open_ports=[80],
        protocols=["http"],
        http_evidence=[
            {
                "url": "http://192.168.1.1:80/",
                "status": 200,
                "server": "TestServer",
                "content_type": "text/html",
                "title": "Router",
            }
        ],
    )

    data = device.to_dict()

    assert len(data["http_evidence"]) == 1
    assert data["http_evidence"][0]["status"] == 200
    assert data["http_evidence"][0]["title"] == "Router"
