#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime
import hashlib
import re
import sys


ROOT = Path.home() / "RichardLab"
EXPERIMENTS = ROOT / "experiments"
REPORTS = ROOT / "reports"


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def file_info(path):
    stat = path.stat()
    return {
        "name": path.name,
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime),
        "sha256": sha256(path),
    }


def experiment_key(name):
    match = re.match(r"experiment-(\d+)([a-z]?)\.(py|sh)$", name)
    if not match:
        return None

    number = match.group(1)
    suffix = match.group(2)

    return number, suffix


def find_related_experiments(target):
    key = experiment_key(target.name)

    if not key:
        return []

    number, _ = key
    related = []

    for path in sorted(EXPERIMENTS.iterdir()):
        if not path.is_file():
            continue

        other_key = experiment_key(path.name)

        if other_key and other_key[0] == number and path != target:
            related.append(path)

    return related


def find_related_outputs(target):
    stem = target.stem.replace("experiment-", "")
    matches = []

    for directory in (EXPERIMENTS, REPORTS):
        if not directory.exists():
            continue

        for path in directory.iterdir():
            if not path.is_file():
                continue

            if stem in path.name or target.stem in path.name:
                matches.append(path)

    return sorted(set(matches))


def inspect(target):
    info = file_info(target)

    print()
    print("EXPERIMENT INSPECTOR")
    print("═" * 60)
    print(f"Experiment : {info['name']}")
    print(f"Type       : {target.suffix.upper().lstrip('.')}")
    print(f"Size       : {info['size']} bytes")
    print(f"Modified   : {info['modified']}")
    print(f"SHA-256    : {info['sha256']}")
    print()

    related = find_related_experiments(target)

    print("RELATED EXPERIMENTS")
    print("─" * 60)

    if related:
        for path in related:
            other = file_info(path)
            print(
                f"{path.name:<24} "
                f"{other['modified'].strftime('%Y-%m-%d %H:%M:%S')}  "
                f"{other['size']} bytes"
            )
        print()
        print("Evidence:")
        print("  Shared experiment number in filename.")
        print("  Chronology may indicate a revision sequence.")
        print("  Filename similarity alone does NOT prove lineage.")
    else:
        print("None found.")

    print()
    outputs = find_related_outputs(target)

    print("RELATED OUTPUTS / REPORTS")
    print("─" * 60)

    if outputs:
        for path in outputs:
            other = file_info(path)
            print(
                f"{path.relative_to(ROOT)}  "
                f"{other['size']} bytes  "
                f"{other['modified'].strftime('%Y-%m-%d %H:%M:%S')}"
            )
    else:
        print("None found.")

    print()
    print("INSPECTION COMPLETE")
    print()


def main():
    if len(sys.argv) != 2:
        print("Usage: python mission_control/experiment_inspector.py <experiment>")
        print("Example:")
        print("  python mission_control/experiment_inspector.py experiment-011d.py")
        sys.exit(1)

    target = EXPERIMENTS / sys.argv[1]

    if not target.exists():
        print(f"ERROR: Experiment not found: {target}")
        sys.exit(1)

    if not target.is_file():
        print(f"ERROR: Not a file: {target}")
        sys.exit(1)

    inspect(target)


if __name__ == "__main__":
    main()
