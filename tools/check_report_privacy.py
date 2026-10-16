#!/usr/bin/env python3
"""Check the Git index for common private host details in public reports.

Reports only: this is a privacy guard, not a general secret scanner.
Never print matched values into CI logs.
"""
import ipaddress
import re
import subprocess
import sys
from pathlib import PurePosixPath

RULES = (
    ("home directory path", re.compile(r"(?:/home/[^/\s]+|/Users/[^/\s]+|[A-Za-z]:\\Users\\[^\\\s]+)", re.I)),
    ("machine identity field", re.compile(r"^\s*(?:User|Hostname|Machine):\s*(?!benchmark-host\s*$|\[REDACTED\]\s*$)\S+", re.M | re.I)),
    ("MAC address", re.compile(r"\b(?:[0-9a-f]{2}:){5}[0-9a-f]{2}\b", re.I)),
    ("raw diagnostic section", re.compile(r"^-+ (?:NETWORK|RUNNING PROCESSES|SERVICES|LAB STATUS) -+", re.M)),
    ("IPv6 link-local address", re.compile(r"\bfe[89ab][0-9a-f]:[0-9a-f:]+", re.I)),
)
IPV4 = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")

def problems(path, data):
    found = []
    if PurePosixPath(path).name.startswith("system_scan_") or path.startswith("private_reports/"):
        found.append("raw diagnostic must not be tracked")
    if path.startswith("reports/") and path.endswith((".txt", ".csv", ".json", ".md", ".log", ".yaml", ".yml")):
        text = data.decode("utf-8", errors="replace")
        found.extend(label for label, pattern in RULES if pattern.search(text))
        for match in IPV4.finditer(text):
            try:
                address = ipaddress.ip_address(match.group())
            except ValueError:
                continue
            if not address.is_loopback and (address.is_private or address.is_global):
                found.append("network IPv4 address")
                break
    return found

def main():
    paths = subprocess.check_output(["git", "ls-files", "-z"]).decode().split("\0")
    failed = False
    for path in filter(None, paths):
        if not (path.startswith(("reports/", "private_reports/")) or PurePosixPath(path).name.startswith("system_scan_")):
            continue
        data = subprocess.check_output(["git", "show", ":" + path])
        for reason in problems(path, data):
            print(f"{path}: {reason}", file=sys.stderr)
            failed = True
    if failed:
        print("Keep raw diagnostics local; sanitize public reports before committing.", file=sys.stderr)
    else:
        print("Tracked report privacy check passed.")
    return int(failed)

if __name__ == "__main__":
    raise SystemExit(main())
