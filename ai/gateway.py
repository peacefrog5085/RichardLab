#!/usr/bin/env python3

import json
import sys
import time
from pathlib import Path

from .providers import (
    CodexProvider,
    GeminiProvider,
    OllamaProvider,
)
from .router import AIRouter


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

    raise ValueError(
        f"Unknown AI provider: {name}"
    )


def get_provider(config, preferred=None):
    routing = config.get("routing", {})

    provider_name = (
        preferred
        or routing.get("primary")
        or "codex"
    )

    provider = build_provider(
        provider_name,
        config
    )

    health = provider.health()

    if health.get("status") in (
        "READY",
    ):
        return provider

    fallback = routing.get(
        "fallback"
    )

    if fallback and fallback != provider_name:
        fallback_provider = build_provider(
            fallback,
            config
        )

        fallback_health = fallback_provider.health()

        if fallback_health.get("status") == "READY":
            return fallback_provider

    raise RuntimeError(
        f"No usable AI provider. "
        f"Primary={provider_name}; "
        f"health={health}"
    )


def build_lab_prompt(user_prompt, lab_status):
    status_json = json.dumps(
        lab_status,
        indent=2
    )

    return f"""
USER REQUEST:
{user_prompt}

AUTHORITATIVE RICHARDLAB DATA:
{status_json}

Use the supplied RichardLab data as the source of truth.
Do not invent files, measurements, experiments, or system states.
If the data does not contain an answer, say so clearly.
"""


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python -m ai.gateway "
            "\"your question\""
        )
        sys.exit(1)

    user_prompt = " ".join(sys.argv[1:])

    config = load_config()

    from .tools import call_tool

    print("RichardLab AI Gateway")
    print("=====================")

    try:
        lab_status = call_tool(
            "get_lab_status"
        )

        prompt = build_lab_prompt(
            user_prompt,
            lab_status
        )

        preferred = config.get(
            "routing",
            {}
        ).get("primary")

        provider = get_provider(
            config,
            preferred
        )

        print(
            f"Provider: {provider.name}"
        )

        result = provider.ask(
            prompt,
            system=(
                "You are the AI assistant "
                "for RichardLab."
            )
        )

        print()
        print(result.text)
        print()
        print(
            f"Provider time: "
            f"{result.elapsed_seconds:.2f}s"
        )

    except Exception as exc:
        print(
            f"AI gateway error: {exc}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
