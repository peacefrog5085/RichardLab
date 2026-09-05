#!/usr/bin/env python3

from pathlib import Path
from collections import defaultdict
from datetime import datetime
import csv

PHOTO_LAB = Path.home() / "RichardLab" / "photo_lab"
DATA_DIR = PHOTO_LAB / "data"
REPORT_DIR = PHOTO_LAB / "reports"


def newest_inventory():
    files = list(DATA_DIR.glob("photo_inventory_*.csv"))
    return max(files, key=lambda p: p.stat().st_mtime) if files else None


def load_inventory(path):
    groups = defaultdict(list)

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            groups[row["sha256"]].append(row)

    return groups


def choose_keeper(files):
    return sorted(
        files,
        key=lambda row: (len(row["path"]), row["path"].lower())
    )[0]


def main():
    inventory = newest_inventory()

    if inventory is None:
        print("No photo inventory found.")
        return 1

    groups = load_inventory(inventory)

    duplicate_groups = [
        files for files in groups.values()
        if len(files) > 1
    ]

    duplicate_files = sum(len(files) for files in duplicate_groups)
    extra_candidates = sum(
        len(files) - 1 for files in duplicate_groups
    )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = REPORT_DIR / f"duplicate_report_{timestamp}.txt"

    with report.open("w", encoding="utf-8") as out:
        out.write("RICHARDLAB PHOTO LAB\n")
        out.write("EXACT DUPLICATE ANALYSIS v0.1\n")
        out.write("=" * 60 + "\n\n")
        out.write("READ-ONLY MODE\n")
        out.write("No files were modified or deleted.\n\n")
        out.write(f"Inventory: {inventory.name}\n")
        out.write(f"Duplicate groups: {len(duplicate_groups)}\n")
        out.write(f"Files involved: {duplicate_files}\n")
        out.write(f"Extra-copy candidates: {extra_candidates}\n\n")

        for number, files in enumerate(
            sorted(
                duplicate_groups,
                key=lambda group: choose_keeper(group)["path"].lower()
            ),
            1
        ):
            keeper = choose_keeper(files)

            out.write("-" * 60 + "\n")
            out.write(f"DUPLICATE GROUP {number:04d}\n")
            out.write(f"SHA-256: {keeper['sha256']}\n\n")

            out.write("RECOMMENDED KEEPER:\n")
            out.write(f"  {keeper['path']}\n\n")

            out.write("MATCHING FILES:\n")

            for row in files:
                marker = "KEEP" if row is keeper else "EXTRA"
                out.write(
                    f"  [{marker}] {row['path']}\n"
                )

            out.write("\n")

    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║                 RICHARDLAB PHOTO LAB                   ║")
    print("║              DUPLICATE ANALYZER v0.1                  ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print("║ READ-ONLY MODE                                         ║")
    print("║ NO FILES WILL BE DELETED OR MODIFIED                  ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    print(f"Inventory:        {inventory.name}")
    print(f"Duplicate groups: {len(duplicate_groups)}")
    print(f"Files involved:   {duplicate_files}")
    print(f"Extra candidates: {extra_candidates}")
    print()
    print(f"Report: {report}")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
