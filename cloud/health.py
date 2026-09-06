#!/usr/bin/env python3

import json
import urllib.request


def check_cloud_health(base_url="http://127.0.0.1:8080"):
    url = base_url.rstrip("/") + "/health"

    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))

        return {
            "reachable": True,
            "status_code": response.status,
            "response": data,
        }

    except Exception as exc:
        return {
            "reachable": False,
            "error": str(exc),
        }


if __name__ == "__main__":
    print(json.dumps(check_cloud_health(), indent=2))
