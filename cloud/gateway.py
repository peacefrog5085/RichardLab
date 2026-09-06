#!/usr/bin/env python3

import json
import os
import urllib.request

from ai.lab_tools import get_lab_status
from .health import check_cloud_health


DEFAULT_CLOUD_URL = "http://127.0.0.1:8080"


def get_cloud_url():
    return os.environ.get("RICHARDLAB_CLOUD_URL", DEFAULT_CLOUD_URL)


def cloud_status():
    return check_cloud_health(get_cloud_url())


def send_lab_status():
    url = get_cloud_url().rstrip("/") + "/lab/status"
    lab_status = get_lab_status()

    payload = json.dumps(lab_status).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))

        return {
            "sent": True,
            "status_code": response.status,
            "response": result,
        }

    except Exception as exc:
        return {
            "sent": False,
            "error": str(exc),
        }


if __name__ == "__main__":
    print("RichardLab Cloud Gateway")
    print("========================")
    print()
    print("Cloud URL:", get_cloud_url())
    print()
    print(json.dumps(cloud_status(), indent=2))
    print()
    print("Sending RichardLab state...")
    print()
    print(json.dumps(send_lab_status(), indent=2))
