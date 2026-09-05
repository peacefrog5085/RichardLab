#!/usr/bin/env python3

import csv
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
REPORT_DIR = Path(__file__).resolve().parent / "reports"


def newest_inventory():
    files = sorted(DATA_DIR.glob("photo_inventory_*.csv"))
    if not files:
        raise FileNotFoundError("No photo inventory found.")
    return files[-1]


def load_inventory(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    inventory_path = newest_inventory()
    rows = load_inventory(inventory_path)

    samantha_folders = defaultdict(list)

    for row in rows:
        path = row["path"]

        if "My Love Samantha R Sprague" in path:
            folder = str(Path(path).parent)
            samantha_folders[folder].append(row)

    if len(samantha_folders) < 2:
        raise RuntimeError(
            "Could not find both Samantha collections."
        )

    folders = sorted(
        samantha_folders,
        key=lambda folder: (
            "(2)" not in folder,
            folder,
        )
    )

    folder_a = folders[0]
    folder_b = folders[1]

    files_a = samantha_folders[folder_a]
    files_b = samantha_folders[folder_b]

    hashes_a = {
        row["sha256"]: row
        for row in files_a
    }

    hashes_b = {
        row["sha256"]: row
        for row in files_b
    }

    only_a = [
        row for sha, row in hashes_a.items()
        if sha not in hashes_b
    ]

    only_b = [
        row for sha, row in hashes_b.items()
        if sha not in hashes_a
    ]

    shared = len(set(hashes_a) & set(hashes_b))

    report_path = REPORT_DIR / "samantha_collection_compare_latest.txt"
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    with report_path.open("w", encoding="utf-8") as report:
        report.write("RICHARDLAB PHOTO LAB\n")
        report.write("====================\n")
        report.write("SAMANTHA COLLECTION COMPARISON\n\n")

        report.write(f"Inventory: {inventory_path.name}\n\n")

        report.write("COLLECTION A\n")
        report.write("------------\n")
        report.write(f"{folder_a}\n")
        report.write(f"Files: {len(files_a)}\n\n")

        report.write("COLLECTION B\n")
        report.write("------------\n")
        report.write(f"{folder_b}\n")
        report.write(f"Files: {len(files_b)}\n\n")

        report.write("COMPARISON\n")
        report.write("----------\n")
        report.write(f"Shared exact images: {shared}\n")
        report.write(f"Only in Collection A: {len(only_a)}\n")
        report.write(f"Only in Collection B: {len(only_b)}\n\n")

        report.write("=" * 78 + "\n")
        report.write("ONLY IN COLLECTION A\n")
        report.write("=" * 78 + "\n")

        for row in only_a:
            report.write(f"\nPath: {row['path']}\n")
            report.write(f"SHA-256: {row['sha256']}\n")
            report.write(f"Size: {row['size_bytes']} bytes\n")
            report.write(f"Modified: {row['modified']}\n")

        report.write("\n")
        report.write("=" * 78 + "\n")
        report.write("ONLY IN COLLECTION B\n")
        report.write("=" * 78 + "\n")

        for row in only_b:
            report.write(f"\nPath: {row['path']}\n")
            report.write(f"SHA-256: {row['sha256']}\n")
            report.write(f"Size: {row['size_bytes']} bytes\n")
            report.write(f"Modified: {row['modified']}\n")

        report.write("\n")
        report.write("=" * 78 + "\n")
        report.write("SAFETY\n")
        report.write("=" * 78 + "\n")
        report.write("NO FILES WERE MODIFIED.\n")
        report.write("NO FILES WERE MOVED.\n")
        report.write("NO FILES WERE DELETED.\n")

    print("===== SAMANTHA COLLECTION COMPARISON =====")
    print(f"Collection A: {folder_a}")
    print(f"Files:        {len(files_a)}")
    print()
    print(f"Collection B: {folder_b}")
    print(f"Files:        {len(files_b)}")
    print()
    print(f"Shared exact images:  {shared}")
    print(f"Only in A:            {len(only_a)}")
    print(f"Only in B:            {len(only_b)}")
    print()
    print(f"Report: {report_path}")
    print()
    print("NO FILES WERE MODIFIED.")
    print("NO FILES WERE MOVED.")
    print("NO FILES WERE DELETED.")


if __name__ == "__main__":
    main()
