#!/usr/bin/env python3

import argparse
import json
from pathlib import Path


def load_report(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def index_files(report):
    return {
        item["path"]: item
        for item in report.get("files", [])
    }


def compare(old_report, new_report):
    old_files = index_files(old_report)
    new_files = index_files(new_report)

    old_paths = set(old_files)
    new_paths = set(new_files)

    results = {
        "NEW": [],
        "CHANGED": [],
        "UNCHANGED": [],
        "MISSING": [],
    }

    for path in sorted(new_paths - old_paths):
        results["NEW"].append(path)

    for path in sorted(old_paths - new_paths):
        results["MISSING"].append(path)

    for path in sorted(old_paths & new_paths):
        old_hash = old_files[path].get("sha256")
        new_hash = new_files[path].get("sha256")

        if old_hash != new_hash:
            results["CHANGED"].append(path)
        else:
            results["UNCHANGED"].append(path)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Compare two RichardLab forensic reports"
    )

    parser.add_argument("old_report")
    parser.add_argument("new_report")

    args = parser.parse_args()

    old_path = Path(args.old_report).expanduser().resolve()
    new_path = Path(args.new_report).expanduser().resolve()

    if not old_path.exists():
        print(f"ERROR: Old report not found: {old_path}")
        raise SystemExit(1)

    if not new_path.exists():
        print(f"ERROR: New report not found: {new_path}")
        raise SystemExit(1)

    old_report = load_report(old_path)
    new_report = load_report(new_path)

    results = compare(old_report, new_report)

    print()
    print("RICHARDLAB FORENSIC COMPARISON")
    print("==============================")
    print(f"OLD: {old_path.name}")
    print(f"NEW: {new_path.name}")
    print()

    for category in ["NEW", "CHANGED", "UNCHANGED", "MISSING"]:
        items = results[category]

        print(f"{category}: {len(items)}")

        for item in items:
            print(f"  {item}")

        print()

    print("==============================")
    print("COMPARISON COMPLETE")
    print("==============================")
    print()


if __name__ == "__main__":
    main()
