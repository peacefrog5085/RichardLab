from iot.http_probe import HTTPProbeResult
from iot.models import DeviceObservation
from iot.service import IoTService


def test_service_collects_http_evidence_and_fingerprints_it(
    tmp_path,
    monkeypatch,
):
    fake_device = DeviceObservation(
        ip="192.168.1.25",
        open_ports=[80],
        protocols=["http"],
    )

    monkeypatch.setattr(
        "iot.service.discover_hosts",
        lambda *args, **kwargs: [fake_device],
    )

    monkeypatch.setattr(
        "iot.service.probe_http",
        lambda ip, port, timeout: HTTPProbeResult(
            url=f"http://{ip}:{port}/",
            status=200,
            server="micro_httpd",
            content_type="text/html",
            title="Test Router",
        ),
    )

    service = IoTService(tmp_path / "inventory.json")

    results = service.discover("192.168.1.0/24")

    assert len(results) == 1

    device = results[0]

    assert len(device.http_evidence) == 1
    assert device.http_evidence[0]["status"] == 200
    assert device.http_evidence[0]["server"] == "micro_httpd"

    # Critical regression check:
    # fingerprinting must happen AFTER HTTP evidence collection.
    assert device.device_type == "network_appliance"
    assert device.confidence == 0.40
    assert "http_server:micro_httpd" in device.observations

    stored = service.inventory.get("192.168.1.25")

    assert stored["confidence"] == 0.40
    assert stored["http_evidence"][0]["server"] == "micro_httpd"
