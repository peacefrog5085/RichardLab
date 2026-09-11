from iot.http_probe import HTTPProbeResult


def test_http_probe_result_serializes():
    result = HTTPProbeResult(
        url="http://192.168.1.1:80/",
        status=200,
        server="TestServer",
        content_type="text/html",
        title="Router",
    )

    data = result.to_dict()

    assert data["url"] == "http://192.168.1.1:80/"
    assert data["status"] == 200
    assert data["server"] == "TestServer"
    assert data["content_type"] == "text/html"
    assert data["title"] == "Router"


def test_http_probe_result_can_record_error():
    result = HTTPProbeResult(
        url="http://192.168.1.50:80/",
        error="connection_error:TimeoutError",
    )

    assert result.status is None
    assert result.error == "connection_error:TimeoutError"
