#!/usr/bin/env python3

import json

from .lab_tools import get_lab_status


TOOLS = {
    "get_lab_status": {
        "description": (
            "Return the current structured status "
            "of RichardLab, including system resources, "
            "module states, and activity."
        ),
        "function": get_lab_status
    }
}


def list_tools():
    return {
        name: {
            "description": info["description"]
        }
        for name, info in TOOLS.items()
    }


def call_tool(name):
    if name not in TOOLS:
        raise ValueError(
            f"Unknown tool: {name}"
        )

    return TOOLS[name]["function"]()


if __name__ == "__main__":
    print(
        json.dumps(
            list_tools(),
            indent=2
        )
    )
