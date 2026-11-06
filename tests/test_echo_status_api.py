import builtins
import io
import json
import logging
import os
import socket
import subprocess
from datetime import datetime

import pytest

from cloud_service import echo_local
from cloud_service.app import app as cloud_app
from core.runtime.echo_status import StatusUnavailable


TOKEN = "test-credential-for-echo-status-only"
AUTH = {"Authorization": f"Bearer {TOKEN}"}
PATH = echo_local.STATUS_PATH


@pytest.fixture
def local_app():
    app = echo_local.create_app(TOKEN)
    app.testing = True
    return app


def test_status_contract(local_app):
    response = local_app.test_client().get(PATH, headers=AUTH)

    assert response.status_code == 200
    assert response.is_json
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json == {
        "service": "RichardLab Echo 777",
        "api_version": "v1",
        "health": {"status": "available", "scope": "status_api"},
        "verified_capabilities": ["echo.status.read"],
    }


@pytest.mark.parametrize("headers", [
    {},
    {"Authorization": "Bearer " + "x" * 32},
    {"Authorization": f"Basic {TOKEN}"},
    {"Authorization": "Bearer " + "é" * 32},
    {"Authorization": f"Bearer {TOKEN}, Bearer {TOKEN}"},
])
def test_unauthorized_requests_do_not_consult_status(local_app, headers, monkeypatch):
    def unexpected_status_call():
        pytest.fail("Unauthorized request called the status service")

    monkeypatch.setattr(echo_local, "get_echo_status", unexpected_status_call)
    response = local_app.test_client().get(PATH, headers=headers)

    assert response.status_code == 401
    assert response.json == {"error": "unauthorized"}
    assert response.headers["WWW-Authenticate"] == 'Bearer realm="echo-status"'
    assert response.headers["Cache-Control"] == "no-store"


@pytest.mark.parametrize("token", [None, "", "short", " " + TOKEN])
def test_invalid_credentials_prevent_enablement(token):
    with pytest.raises(ValueError, match="Configure a valid Echo status bearer credential"):
        echo_local.create_app(token)


def test_launcher_binds_only_to_loopback(monkeypatch):
    monkeypatch.setenv("RICHARDLAB_ECHO_STATUS_TOKEN", TOKEN)
    calls = []
    monkeypatch.setattr(echo_local.Flask, "run", lambda app, **kwargs: calls.append(kwargs))
    monkeypatch.setattr(logging.getLogger("werkzeug"), "setLevel", lambda level: None)

    echo_local.main()

    assert calls == [{
        "host": "127.0.0.1", "port": 8081, "debug": False, "use_reloader": False,
    }]


def test_local_app_exposes_only_status(local_app):
    client = local_app.test_client()
    assert {rule.rule for rule in local_app.url_map.iter_rules()} == {PATH}
    for method in ("POST", "PUT", "PATCH", "DELETE", "OPTIONS"):
        assert client.open(PATH, method=method, headers=AUTH).status_code == 405
    assert client.head(PATH, headers=AUTH).status_code == 200
    assert client.head(PATH).status_code == 401
    assert client.get(PATH, headers={**AUTH, "Host": "external.example"}).status_code == 400


def test_status_requests_do_not_access_files_processes_or_network(
    local_app, tmp_path, monkeypatch, caplog,
):
    evidence = "private-evidence-marker"
    host = "private-host-marker"
    private_path = tmp_path / "private-investigation.json"
    private_path.write_text(evidence, encoding="utf-8")
    monkeypatch.setenv("ECHO_TEST_PRIVATE_HOST", host)
    monkeypatch.setenv("ECHO_TEST_EVIDENCE_PATH", str(private_path))
    client = local_app.test_client()

    def unavailable():
        raise StatusUnavailable(f"{evidence} {host} {private_path} {TOKEN}")

    def forbidden(*args, **kwargs):
        pytest.fail("Status request attempted filesystem, process, or network access")

    with monkeypatch.context() as guard:
        for module, name in [
            (builtins, "open"), (io, "open"), (os, "open"), (os, "listdir"),
            (os, "scandir"), (os, "replace"), (os, "unlink"), (os, "mkdir"),
            (os, "system"), (subprocess, "Popen"), (socket, "socket"),
        ]:
            guard.setattr(module, name, forbidden)
        success = client.get(PATH, headers=AUTH, query_string={"ignored": evidence})
        denied = client.get(PATH, headers={"Authorization": f"Bearer {evidence}"})
        guard.setattr(echo_local, "get_echo_status", unavailable)
        failed = client.get(PATH, headers=AUTH)

    assert success.status_code == 200
    assert denied.status_code == 401
    assert failed.status_code == 503
    assert failed.json == {"error": "status_unavailable"}
    assert failed.headers["Cache-Control"] == "no-store"
    assert list(tmp_path.iterdir()) == [private_path]
    assert private_path.read_text(encoding="utf-8") == evidence

    events = [json.loads(record.getMessage()) for record in caplog.records
              if record.name == local_app.logger.name]
    assert [event["outcome"] for event in events] == ["success", "denied", "unavailable"]
    assert len({event["request_id"] for event in events}) == 3
    for event in events:
        assert set(event) == {"event", "operation", "outcome", "request_id", "timestamp"}
        assert event["event"] == "echo.status.request"
        assert event["operation"] == "echo.status.read"
        assert datetime.fromisoformat(event["timestamp"]).utcoffset().total_seconds() == 0
    public_text = caplog.text + "".join(
        response.get_data(as_text=True) for response in (success, denied, failed)
    )
    for private_value in (evidence, host, str(private_path), TOKEN):
        assert private_value not in public_text


def test_existing_cloud_routes_preserve_their_contract():
    client = cloud_app.test_client()
    assert client.get(PATH, headers=AUTH).status_code == 404
    for path, status in (("/", "ONLINE"), ("/health", "HEALTHY")):
        response = client.get(path)
        assert response.status_code == 200
        assert response.json["service"] == "RichardLab Cloud"
        assert response.json["status"] == status
        assert datetime.fromisoformat(response.json["timestamp"]).tzinfo is not None

    assert client.get("/lab/status").status_code == 405
    payload = {"sample": "legacy echo"}
    accepted = client.post("/lab/status", json=payload)
    assert accepted.status_code == 200
    assert accepted.json["accepted"] is True
    assert accepted.json["service"] == "RichardLab Cloud"
    assert accepted.json["lab_status"] == payload
    assert datetime.fromisoformat(accepted.json["received_at"]).tzinfo is not None

    for invalid in ({"json": []}, {"data": "{", "content_type": "application/json"}):
        rejected = client.post("/lab/status", **invalid)
        assert rejected.status_code == 400
        assert rejected.json == {"accepted": False, "error": "Expected a JSON object"}
