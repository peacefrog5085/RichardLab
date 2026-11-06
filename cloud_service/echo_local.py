"""Serve Echo status on IPv4 loopback after explicit local opt-in."""

import hmac
import json
import logging
import os
import re
from datetime import datetime, timezone
from uuid import uuid4

from flask import Flask, jsonify, request

from core.runtime.echo_status import StatusUnavailable, get_echo_status


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9._~+/-]{32,}={0,2}", re.ASCII)
STATUS_PATH = "/api/v1/echo/status"


def create_app(token: str | None) -> Flask:
    if not token or not TOKEN_PATTERN.fullmatch(token):
        raise ValueError("Configure a valid Echo status bearer credential")
    expected_token = token.encode("ascii")

    app = Flask(__name__, static_folder=None)
    app.config["TRUSTED_HOSTS"] = ["127.0.0.1", "localhost"]
    app.logger.setLevel(logging.INFO)

    @app.get(STATUS_PATH, provide_automatic_options=False)
    def echo_status():
        scheme, _, supplied_token = request.headers.get("Authorization", "").partition(" ")
        if (
            scheme.lower() != "bearer"
            or not TOKEN_PATTERN.fullmatch(supplied_token)
            or not hmac.compare_digest(supplied_token.encode("ascii"), expected_token)
        ):
            response = jsonify(error="unauthorized")
            response.status_code = 401
            response.headers["WWW-Authenticate"] = 'Bearer realm="echo-status"'
            outcome = "denied"
        else:
            try:
                response = jsonify(get_echo_status())
                outcome = "success"
            except StatusUnavailable:
                response = jsonify(error="status_unavailable")
                response.status_code = 503
                outcome = "unavailable"

        response.headers["Cache-Control"] = "no-store"
        app.logger.info("%s", json.dumps({
            "event": "echo.status.request",
            "request_id": uuid4().hex,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": "echo.status.read",
            "outcome": outcome,
        }))
        return response

    return app


def main() -> None:
    try:
        app = create_app(os.environ.get("RICHARDLAB_ECHO_STATUS_TOKEN"))
    except ValueError as exc:
        raise SystemExit(str(exc)) from None

    # Use the restricted audit event for access logging.
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    app.run(host="127.0.0.1", port=8081, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
