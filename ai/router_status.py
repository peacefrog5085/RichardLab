#!/usr/bin/env python3

import json

from .gateway import load_config, build_provider
from .router import AIRouter


def main():
    config = load_config()

    router = AIRouter(
        config,
        build_provider
    )

    health = router.health()

    output = {
        "primary": config["routing"].get(
            "primary"
        ),
        "fallback": config["routing"].get(
            "fallback"
        ),
        "automatic_fallback": config[
            "routing"
        ].get(
            "allow_automatic_fallback",
            False
        ),
        "providers": {
            name: item.as_dict()
            for name, item in health.items()
        }
    }

    primary = output["primary"]
    primary_state = output[
        "providers"
    ].get(primary, {})

    output["overall"] = (
        "READY"
        if primary_state.get("status") == "READY"
        else "DEGRADED"
    )

    print(
        json.dumps(
            output,
            indent=2
        )
    )


if __name__ == "__main__":
    main()
