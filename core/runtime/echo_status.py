"""Restricted status metadata shared by Echo transports."""


class StatusUnavailable(RuntimeError):
    """Required status metadata could not be supplied."""


def get_echo_status() -> dict:
    """Report liveness of the status API from approved in-memory metadata."""
    return {
        "service": "RichardLab Echo 777",
        "api_version": "v1",
        "health": {"status": "available", "scope": "status_api"},
        "verified_capabilities": ["echo.status.read"],
    }
