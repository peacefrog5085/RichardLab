#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime

LAB = Path.home() / "RichardLab"
EXPERIMENTS = LAB / "experiments"


def experiment_files():
    if not EXPERIMENTS.exists():
        return []

    return sorted(
        [
            p for p in EXPERIMENTS.iterdir()
            if p.is_file()
            and p.suffix.lower() in {".py", ".sh"}
        ],
        key=lambda p: p.stat().st_mtime
    )


def experiment_type(path):
    if path.suffix.lower() == ".py":
        return "PYTHON"

    if path.suffix.lower() == ".sh":
        return "BASH"

    return "OTHER"


def main():
    experiments = experiment_files()

    print()
    print("RICHARDLAB EXPERIMENT REGISTRY")
    print("==============================")
    print(f"Location: {EXPERIMENTS}")
    print(f"Experiments: {len(experiments)}")
    print()

    if not experiments:
        print("No experiments found.")
        return

    for index, path in enumerate(experiments, start=1):
        stat = path.stat()

        modified = datetime.fromtimestamp(
            stat.st_mtime
        ).strftime("%Y-%m-%d %H:%M:%S")

        size = stat.st_size
        kind = experiment_type(path)

        print(
            f"{index:02d}  "
            f"{path.name:<25} "
            f"{kind:<7} "
            f"{size:>6} bytes  "
            f"{modified}"
        )

    latest = experiments[-1]

    print()
    print("==============================")
    print(f"LATEST: {latest.name}")
    print(f"TYPE:   {experiment_type(latest)}")
    print("==============================")
    print()


if __name__ == "__main__":
    main()
