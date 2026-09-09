#!/usr/bin/env python3

import sys

from ai.gateway import build_provider, build_router, load_config
from ai.hive.core import HiveCore


def main():
    if len(sys.argv) < 2:
        print('Usage: ./lab.py "your question"')
        sys.exit(1)

    prompt = " ".join(sys.argv[1:]).strip()

    if not prompt:
        print("No request provided.")
        sys.exit(1)

    config = load_config()

    print("RichardLab")
    print("==========")
    print()

    try:
        hive = HiveCore(
            config=config,
            provider_factory=build_provider,
            router_factory=build_router,
        )

        result = hive.dispatch(prompt)

        print(f"Route:    {result.route}")
        print(f"Worker:   {result.worker}")
        print(f"Provider: {result.provider}")
        print()

        if isinstance(result.result, (dict, list)):
            import json
            print(json.dumps(result.result, indent=2, default=str))
        else:
            print(result.result)

        if result.elapsed_seconds is not None:
            print()
            print(f"Elapsed:  {result.elapsed_seconds:.2f}s")

    except Exception as exc:
        print(f"RichardLab error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
