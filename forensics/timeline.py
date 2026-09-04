#!/usr/bin/env python3

import argparse
import json
from datetime import datetime
from pathlib import Path


def load_report(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_time(value):
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return datetime.max


def main():
    parser = argparse.ArgumentParser(
        description="Create a chronological timeline from a RichardLab forensic report"
    )

    parser.add_argument("report")

    args = parser.parse_args()

    report_path = Path(args.report).expanduser().resolve()

    if not report_path.exists():
        print(f"ERROR: Report not found: {report_path}")
        raise SystemExit(1)

    report = load_report(report_path)

    files = report.get("files", [])

    files.sort(
        key=lambda item: parse_time(item.get("modified"))
    )

    print()
    print("RICHARDLAB FORENSIC TIMELINE")
    print("============================")
    print(f"Source: {report_path.name}")
    print(f"Files:  {len(files)}")
    print()

    for item in files:
        modified = item.get("modified", "unknown")
        name = item.get("name", "unknown")
        size = item.get("size_bytes", 0)
        sha256 = item.get("sha256", "unknown")

        print(f"{modified}")
        print(f"  FILE:   {name}")
        print(f"  SIZE:   {size:,} bytes")
        print(f"  SHA256: {sha256}")
        print()

    print("============================")
    print("TIMELINE COMPLETE")
    print("============================")
    print()


if __name__ == "__main__":
    main()
