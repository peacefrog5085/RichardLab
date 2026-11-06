"""Read the local Echo status API and emit shareable JSON."""

import json
import os
import re
import sys
from http.client import HTTPConnection, HTTPException

from core.runtime.echo_status import get_echo_status


MAX_RESPONSE_BYTES = 4096


class BridgeError(RuntimeError):
    """A status fetch failed without producing a shareable payload."""


def read_status(token: str | None) -> dict:
    if not token or not re.fullmatch(r"[A-Za-z0-9._~+/-]{32,}={0,2}", token):
        raise BridgeError("Configure a valid Echo status bearer credential.")

    # A direct connection has no proxy, redirects, or user-supplied destination.
    connection = HTTPConnection("127.0.0.1", 8081, timeout=3)
    try:
        connection.request("GET", "/api/v1/echo/status", headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
        })
        with connection.getresponse() as response:
            if response.status == 401:
                raise BridgeError("Echo rejected the status credential.")
            if response.status != 200:
                raise BridgeError("Echo status is unavailable.")
            if response.headers.get_content_type() != "application/json":
                raise BridgeError("Echo returned an invalid status response.")
            payload = response.read(MAX_RESPONSE_BYTES + 1)
    except (OSError, HTTPException):
        raise BridgeError("Could not read the Echo status API on loopback.") from None
    finally:
        connection.close()

    if len(payload) > MAX_RESPONSE_BYTES:
        raise BridgeError("Echo returned an invalid status response.")
    try:
        status = json.loads(payload.decode("utf-8"))
    except (ValueError, RecursionError):
        raise BridgeError("Echo returned an invalid status response.") from None

    # Share only a response that matches the approved v1 status document.
    if status != get_echo_status():
        raise BridgeError("Echo returned an invalid status response.")
    return status


def main() -> int:
    if len(sys.argv) != 1:
        print("Usage: python -m cli.echo_bridge", file=sys.stderr)
        return 2
    try:
        status = read_status(os.environ.get("RICHARDLAB_ECHO_STATUS_TOKEN"))
    except BridgeError as exc:
        print(f"Echo bridge: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(status, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
