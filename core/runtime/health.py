#!/usr/bin/env python3

from __future__ import annotations

import platform
import sys

from ai.router import AIRouter


def get_health() -> dict:
    router = AIRouter()

    return {
        "richardlab": "online",
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "ai": router.status(),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(get_health(), indent=2))
