#!/usr/bin/env python3

import json

from .lab_tools_registry import load_registry
from .tool_registry import list_tools


def main():
    load_registry()

    print(
        json.dumps(
            {
                "tool_count": len(list_tools()),
                "tools": list_tools(),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
