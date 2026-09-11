#!/usr/bin/env python3

import json
import sys
from pathlib import Path

from .providers import (
    CodexProvider,
    GeminiProvider,
    OllamaProvider,
    OpenAIProvider,
    GrokProvider,
)
from .router import AIRouter
from .hive.core import HiveCore


AI_DIR = Path(__file__).resolve().parent
CONFIG_PATH = AI_DIR / "config.json"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_provider(name, config):
    provider_config = config.get(
        "providers",
        {}
    ).get(name, {})

    if name == "codex":
        return CodexProvider(provider_config)

    if name == "gemini":
        return GeminiProvider(provider_config)

    if name == "ollama":
        return OllamaProvider(provider_config)

    if name == "openai":
        return OpenAIProvider(provider_config)

    if name == "grok":
        return GrokProvider(provider_config)
    raise ValueError(
        f"Unknown AI provider: {name}"
    )


def build_router(config, provider_factory):
    return AIRouter(
        config,
        provider_factory
    )


def _print_council_result(result):
    print("RichardLab AI Council")
    print("=====================")
    print()
    print("QUESTION")
    print("--------")
    print(result.question)
    print()

    print("INDEPENDENT AGENTS")
    print("-------------------")

    for response in result.debate.responses:
        print()
        print(f"[{response.role.upper()}]")
        print(f"Worker: {response.worker}")

        if response.error:
            print(f"ERROR: {response.error}")
        elif isinstance(response.result, (dict, list)):
            print(json.dumps(response.result, indent=2, default=str))
        else:
            print(response.result)

    print()

    print("AUDITOR")
    print("-------")

    if result.audit is None:
        print("No audit available.")
    else:
        print(json.dumps(result.audit.as_dict(), indent=2, default=str))

    print()

    print("SYNTHESIS")
    print("---------")

    if result.synthesis is None:
        print("No synthesis available.")
    elif isinstance(result.synthesis, (dict, list)):
        print(json.dumps(result.synthesis, indent=2, default=str))
    else:
        print(result.synthesis)

    print()


def main():
    if len(sys.argv) < 2:
        print(
            "Usage:"
        )
        print(
            "  python -m ai.gateway \"your question\""
        )
        print(
            "  python -m ai.gateway council \"your question\""
        )
        sys.exit(1)

    council_mode = sys.argv[1].lower() == "council"

    if council_mode:
        if len(sys.argv) < 3:
            print(
                "Usage: python -m ai.gateway council "
                "\"your question\""
            )
            sys.exit(1)

        user_prompt = " ".join(sys.argv[2:])
    else:
        user_prompt = " ".join(sys.argv[1:])

    config = load_config()

    try:
        hive = HiveCore(
            config=config,
            provider_factory=build_provider,
            router_factory=build_router,
        )

        if council_mode:
            result = hive.dispatch_council(user_prompt)
            _print_council_result(result)
            return

        print("RichardLab AI Gateway")
        print("=====================")

        result = hive.dispatch(user_prompt)

        print(f"Route: {result.route}")
        print(f"Worker: {result.worker}")
        print(f"Provider: {result.provider}")

        if result.metadata:
            if result.metadata.get("router_fallback"):
                print("Router: automatic fallback used")
                print(
                    "Primary provider: "
                    f"{result.metadata.get('router_primary_provider')}"
                )

        print()

        if isinstance(result.result, (dict, list)):
            print(
                json.dumps(
                    result.result,
                    indent=2,
                    default=str
                )
            )
        else:
            print(result.result)

        print()

        if result.elapsed_seconds is not None:
            print(
                f"Elapsed time: "
                f"{result.elapsed_seconds:.2f}s"
            )

    except Exception as exc:
        print(
            f"AI gateway error: {exc}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
