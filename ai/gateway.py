#!/usr/bin/env python3

import json
import sys
import time
import urllib.request
from pathlib import Path

from .tools import call_tool


AI_DIR = Path(__file__).resolve().parent
CONFIG_PATH = AI_DIR / "config.json"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def ask_model(config, prompt):
    url = config["base_url"].rstrip("/") + "/api/generate"

    payload = {
        "model": config["model"],
        "prompt": prompt,
        "stream": False,
    }

    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    start = time.time()

    with urllib.request.urlopen(
        request,
        timeout=config.get("timeout_seconds", 300),
    ) as response:
        result = json.loads(response.read().decode("utf-8"))

    elapsed = time.time() - start

    return result, elapsed


def build_lab_prompt(user_prompt, lab_status):
    status_json = json.dumps(lab_status, indent=2)

    return f"""
You are the local AI assistant for RichardLab.

You have been given authoritative structured data from a RichardLab tool.

Treat the supplied tool data as the source of truth.
Do not invent measurements, files, experiment results, or system states.
If the data does not contain an answer, say that clearly.

Explain the lab state in plain language.
Be concise but useful.

USER REQUEST:
{user_prompt}

TOOL: get_lab_status

TOOL RESULT:
{status_json}

Now answer the user's request using the tool result.
"""


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 ai/gateway.py \"your question\"")
        sys.exit(1)

    user_prompt = " ".join(sys.argv[1:])
    config = load_config()

    print("RichardLab Local AI")
    print("===================")
    print(f"Model: {config['model']}")
    print("Tool: get_lab_status")
    print()

    try:
        lab_status = call_tool("get_lab_status")

        prompt = build_lab_prompt(user_prompt, lab_status)

        result, elapsed = ask_model(config, prompt)

        response_text = result.get("response", "").strip()

        print(response_text)
        print()
        print(f"Response time: {elapsed:.2f}s")

        if "eval_count" in result and "eval_duration" in result:
            eval_seconds = result["eval_duration"] / 1_000_000_000
            if eval_seconds > 0:
                tok_sec = result["eval_count"] / eval_seconds
                print(f"Generated tokens: {result['eval_count']}")
                print(f"Generation speed: {tok_sec:.2f} tok/s")

    except Exception as exc:
        print(f"AI gateway error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
