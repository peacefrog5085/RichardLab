import io
import json
from contextlib import nullcontext
from email.message import Message
from unittest.mock import Mock

import pytest

from cli import echo_bridge
from core.runtime.echo_status import get_echo_status


TOKEN = "test-credential-for-echo-bridge-only"


@pytest.fixture
def endpoint(monkeypatch):
    headers = Message()
    headers["Content-Type"] = "application/json"
    response = Mock(status=200, headers=headers)
    response.read = io.BytesIO(json.dumps(get_echo_status()).encode()).read
    connection = Mock()
    connection.getresponse.return_value = nullcontext(response)
    factory = Mock(return_value=connection)
    monkeypatch.setattr(echo_bridge, "HTTPConnection", factory)
    return factory, connection, response


def test_bridge_prints_only_status_json(endpoint, monkeypatch, capsys):
    factory, connection, _ = endpoint
    monkeypatch.setenv("RICHARDLAB_ECHO_STATUS_TOKEN", TOKEN)
    monkeypatch.setattr(echo_bridge.sys, "argv", ["echo_bridge"])

    assert echo_bridge.main() == 0

    factory.assert_called_once_with("127.0.0.1", 8081, timeout=3)
    connection.request.assert_called_once_with("GET", "/api/v1/echo/status", headers={
        "Accept": "application/json", "Authorization": f"Bearer {TOKEN}",
    })
    connection.close.assert_called_once()
    captured = capsys.readouterr()
    assert json.loads(captured.out) == get_echo_status()
    assert captured.err == ""


@pytest.mark.parametrize("mode", ["redirect", "denied", "unavailable", "unexpected-data",
                                  "malformed", "oversized", "wrong-type", "offline"])
def test_bridge_fails_without_sharing_response_or_credential(
    mode, endpoint, monkeypatch, capsys,
):
    _, connection, response = endpoint
    monkeypatch.setenv("RICHARDLAB_ECHO_STATUS_TOKEN", TOKEN)
    monkeypatch.setattr(echo_bridge.sys, "argv", ["echo_bridge"])
    if mode == "offline":
        connection.request.side_effect = OSError(TOKEN)
    elif mode == "wrong-type":
        response.headers.replace_header("Content-Type", "text/html")
    elif mode in {"redirect", "denied", "unavailable"}:
        response.status = {"redirect": 302, "denied": 401, "unavailable": 503}[mode]
        response.headers["Location"] = "https://example.invalid/"
    else:
        payload = {
            "unexpected-data": json.dumps({**get_echo_status(), "private": TOKEN}).encode(),
            "malformed": TOKEN.encode(),
            "oversized": b" " * echo_bridge.MAX_RESPONSE_BYTES + TOKEN.encode(),
        }[mode]
        response.read = io.BytesIO(payload).read

    assert echo_bridge.main() == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("Echo bridge:")
    assert TOKEN not in captured.err
    assert "example.invalid" not in captured.err
    connection.request.assert_called_once()
    connection.close.assert_called_once()


def test_bridge_refuses_missing_credential_and_extra_arguments(endpoint, monkeypatch, capsys):
    factory, _, _ = endpoint
    monkeypatch.delenv("RICHARDLAB_ECHO_STATUS_TOKEN", raising=False)
    monkeypatch.setattr(echo_bridge.sys, "argv", ["echo_bridge"])
    assert echo_bridge.main() == 1

    monkeypatch.setattr(echo_bridge.sys, "argv", ["echo_bridge", "https://example.invalid/"])
    assert echo_bridge.main() == 2

    assert capsys.readouterr().out == ""
    factory.assert_not_called()
