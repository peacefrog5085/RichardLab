#!/usr/bin/env python3

from pathlib import Path
from difflib import SequenceMatcher
import re

ROOT = Path.home() / "RichardLab"
EXPERIMENTS = ROOT / "experiments"


def experiment_key(name):
    match = re.match(r"experiment-(\d+)([a-z]?)\.(py|sh)$", name)
    if not match:
        return None
    return match.group(1)


def similarity(a, b):
    left = a.read_text(errors="replace").splitlines()
    right = b.read_text(errors="replace").splitlines()
    return SequenceMatcher(None, left, right).ratio()


def assessment(score):
    if score >= 0.85:
        return "STRONG"
    if score >= 0.50:
        return "MODERATE"
    return "WEAK"


def display_family(number, files):
    print()
    print(f"EXPERIMENT FAMILY {number}")
    print("─" * 68)

    for path in files:
        print(f"  • {path.name}")

    if len(files) < 2:
        print("  Insufficient files for relationship analysis.")
        return

    print()
    print("RELATIONSHIPS")
    print("─" * 68)

    for a, b in zip(files, files[1:]):
        score = similarity(a, b)
        print(f"  {a.name} → {b.name}")
        print(f"    Source similarity : {score:.2%}")
        print(f"    Evidence level    : {assessment(score)}")

        if score >= 0.85:
            print("    Interpretation     : Strong candidate for related revision.")
        elif score >= 0.50:
            print("    Interpretation     : Possible related revision.")
        else:
            print("    Interpretation     : Sequential filename, but weak source evidence.")


def main():
    files = [
        path for path in EXPERIMENTS.iterdir()
        if path.is_file() and experiment_key(path.name)
    ]

    families = {}

    for path in files:
        key = experiment_key(path.name)
        families.setdefault(key, []).append(path)

    for key in sorted(families, key=lambda x: int(x)):
        families[key].sort(key=lambda p: p.stat().st_mtime)

    print()
    print("RICHARDLAB EXPERIMENT FAMILY MAP")
    print("═" * 68)
    print(f"Families discovered : {len(families)}")
    print(f"Experiments          : {len(files)}")

    for key in sorted(families, key=lambda value: int(value)):
        display_family(key, families[key])

    print()
    print("═" * 68)
    print("MAP COMPLETE")
    print()


if __name__ == "__main__":
    main()
