#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime
import difflib
import hashlib
import re
import subprocess
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

    return match.group(1), match.group(2)


def source_similarity(a, b):
    left = a.read_text(errors="replace").splitlines()
    right = b.read_text(errors="replace").splitlines()

    return difflib.SequenceMatcher(None, left, right).ratio()


def git_history(path):
    try:
        result = subprocess.run(
            [
                "git",
                "log",
                "--follow",
                "-1",
                "--format=%H|%ad|%s",
                "--date=iso",
                "--",
                str(path),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )

        line = result.stdout.strip()

        if not line:
            return None

        commit, date, message = line.split("|", 2)

        return {
            "commit": commit,
            "date": date,
            "message": message,
        }

    except (subprocess.CalledProcessError, ValueError):
        return None


def assessment(similarity):
    if similarity >= 0.85:
        return "STRONG SOURCE SIMILARITY"

    if similarity >= 0.50:
        return "MODERATE SOURCE SIMILARITY"

    return "NO MEANINGFUL SOURCE SIMILARITY"


def find_family(target):
    key = experiment_key(target.name)

    if not key:
        return [target]

    number, _ = key
    family = []

    for path in EXPERIMENTS.iterdir():
        if not path.is_file():
            continue

        other_key = experiment_key(path.name)

        if other_key and other_key[0] == number:
            family.append(path)

    return sorted(
        family,
        key=lambda p: p.stat().st_mtime
    )


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

    return sorted(
        set(matches),
        key=lambda p: p.stat().st_mtime
    )


def inspect(target):
    info = file_info(target)
    family = find_family(target)

    print()
    print("EXPERIMENT INSPECTOR v2")
    print("═" * 68)

    print(f"Experiment : {info['name']}")
    print(f"Type       : {target.suffix.upper().lstrip('.')}")
    print(f"Size       : {info['size']} bytes")
    print(f"Modified   : {info['modified']}")
    print(f"SHA-256    : {info['sha256']}")

    print()
    print("GIT EVIDENCE")
    print("─" * 68)

    history = git_history(target)

    if history:
        print(f"Commit     : {history['commit']}")
        print(f"Date       : {history['date']}")
        print(f"Message    : {history['message']}")
    else:
        print("No Git history found.")

    print()
    print("FAMILY")
    print("─" * 68)

    for index, path in enumerate(family, start=1):
        marker = " ← TARGET" if path == target else ""

        print(
            f"{index}) {path.name:<24} "
            f"{path.stat().st_size:>7} bytes  "
            f"{datetime.fromtimestamp(path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}"
            f"{marker}"
        )

    print()
    print("ADJACENT SOURCE EVIDENCE")
    print("─" * 68)

    if len(family) < 2:
        print("Not enough files for comparison.")
    else:
        for a, b in zip(family, family[1:]):
            similarity = source_similarity(a, b)

            print()
            print(f"{a.name} → {b.name}")
            print(f"  Similarity : {similarity:.2%}")
            print(f"  Assessment : {assessment(similarity)}")

            a_history = git_history(a)
            b_history = git_history(b)

            if a_history and b_history:
                if a_history["commit"] == b_history["commit"]:
                    print("  Git        : SAME BASE COMMIT")
                else:
                    print("  Git        : DIFFERENT COMMITS")
            else:
                print("  Git        : UNAVAILABLE")

            time_difference = (
                b.stat().st_mtime - a.stat().st_mtime
            )

            print(f"  Time gap   : {time_difference:.0f} seconds")

    print()
    print("LINEAGE CONCLUSION")
    print("─" * 68)

    if len(family) < 2:
        print("Insufficient evidence.")

    else:
        for a, b in zip(family, family[1:]):
            similarity = source_similarity(a, b)

            if similarity >= 0.85:
                conclusion = "Strong candidate for related revision."

            elif similarity >= 0.50:
                conclusion = "Possible related revision; substantial changes detected."

            else:
                conclusion = "Lineage NOT supported by source similarity."

            print(f"{a.name} → {b.name}")
            print(f"  {conclusion}")

        print()
        print("Overall:")
        print("  Filename sequence suggests a family.")
        print("  Chronology establishes ordering.")
        print("  Source similarity provides relationship evidence.")
        print("  Git history does not prove individual lineage.")
        print("  No relationship is marked PROVEN without stronger evidence.")

    outputs = find_related_outputs(target)

    print()
    print("RELATED OUTPUTS / REPORTS")
    print("─" * 68)

    if outputs:
        for path in outputs:
            output_info = file_info(path)

            print(
                f"{path.relative_to(ROOT)}  "
                f"{output_info['size']} bytes  "
                f"{output_info['modified'].strftime('%Y-%m-%d %H:%M:%S')}"
            )
    else:
        print("None found.")

    print()
    print("INSPECTION COMPLETE")
    print()


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python mission_control/experiment_inspector.py "
            "<experiment>"
        )
        print(
            "Example: python mission_control/experiment_inspector.py "
            "experiment-011d.py"
        )
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
