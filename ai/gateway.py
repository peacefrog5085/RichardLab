#!/usr/bin/env python3

import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path


LAB = Path(__file__).resolve().parent.parent
CONFIG_FILE = LAB / "ai" / "config.json"


def load_config():
    with CONFIG_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def ollama_request(base_url, payload, timeout):
    url = f"{base_url.rstrip('/')}/api/generate"
    data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def main():
    config = load_config()

    if len(sys.argv) < 2:
        print("Usage: python3 ai/gateway.py \"your prompt\"")
        sys.exit(1)

    prompt = " ".join(sys.argv[1:])

    model = config["model"]
    base_url = config["base_url"]
    timeout = config.get("timeout_seconds", 300)

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

    print(f"RichardLab AI")
    print(f"Model: {model}")
    print()

    start = time.perf_counter()

    try:
        result = ollama_request(base_url, payload, timeout)
    except urllib.error.URLError as e:
        print(f"ERROR: Could not reach Ollama: {e}")
        sys.exit(2)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(3)

    elapsed = time.perf_counter() - start

    response = result.get("response", "").strip()

    print(response)
    print()
    print("────────────────────────────────────────")
    print(f"Response time: {elapsed:.2f} seconds")

    eval_count = result.get("eval_count")
    eval_duration = result.get("eval_duration")

    if eval_count and eval_duration:
        seconds = eval_duration / 1_000_000_000
        tok_per_sec = eval_count / seconds if seconds else 0
        print(f"Generated:     {eval_count} tokens")
        print(f"Generation:    {tok_per_sec:.2f} tokens/sec")


if __name__ == "__main__":
    main()
