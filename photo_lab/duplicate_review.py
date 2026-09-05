#!/usr/bin/env python3

import csv
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
REPORT_DIR = Path(__file__).resolve().parent / "reports"


def newest_inventory():
    inventories = sorted(DATA_DIR.glob("photo_inventory_*.csv"))
    if not inventories:
        raise FileNotFoundError("No photo inventory CSV found.")
    return inventories[-1]


def load_inventory(path):
    groups = defaultdict(list)

    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            groups[row["sha256"]].append(row)

    return groups


def classify_duplicates(groups):
    duplicate_groups = []
    extra_candidates = []

    for sha256, files in groups.items():
        if len(files) <= 1:
            continue

        ordered = sorted(
            files,
            key=lambda row: (len(row["path"]), row["path"])
        )

        keeper = ordered[0]

        group = {
            "sha256": sha256,
            "count": len(files),
            "keeper": keeper,
            "copies": ordered,
        }

        duplicate_groups.append(group)

        for row in ordered[1:]:
            extra_candidates.append({
                "sha256": sha256,
                "keeper": keeper["path"],
                "candidate": row["path"],
                "size_bytes": int(row["size_bytes"]),
                "modified": row["modified"],
            })

    return duplicate_groups, extra_candidates


def write_report(inventory, groups, duplicate_groups, extra_candidates):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    report = REPORT_DIR / "duplicate_review_latest.txt"

    potential_bytes = sum(
        item["size_bytes"] for item in extra_candidates
    )

    with report.open("w", encoding="utf-8") as f:
        f.write("RICHARDLAB PHOTO LAB\n")
        f.write("====================\n")
        f.write("DUPLICATE REVIEW\n\n")

        f.write(f"Inventory: {inventory.name}\n")
        f.write(f"Duplicate groups: {len(duplicate_groups)}\n")
        f.write(f"Extra-copy candidates: {len(extra_candidates)}\n")
        f.write(
            f"Potential recoverable GB: "
            f"{potential_bytes / (1024 ** 3):.2f}\n"
        )

        f.write("\n")
        f.write("IMPORTANT: NO FILES WERE MODIFIED.\n")
        f.write("NO FILES WERE DELETED.\n")
        f.write("Candidates require human review.\n")

        f.write("\n")
        f.write("=" * 72 + "\n")

        for number, group in enumerate(duplicate_groups, start=1):
            keeper = group["keeper"]

            f.write(f"\nGROUP {number:04d}\n")
            f.write(f"SHA-256: {group['sha256']}\n")
            f.write(f"Copies: {group['count']}\n")
            f.write(f"RECOMMENDED KEEP: {keeper['path']}\n")
            f.write(f"KEEP SIZE: {keeper['size_bytes']} bytes\n")
            f.write(f"KEEP MODIFIED: {keeper['modified']}\n")

            for row in group["copies"]:
                if row["path"] == keeper["path"]:
                    label = "KEEP"
                else:
                    label = "EXTRA COPY / REVIEW"

                f.write(f"\n  [{label}]\n")
                f.write(f"  Path: {row['path']}\n")
                f.write(f"  Size: {row['size_bytes']} bytes\n")
                f.write(f"  Modified: {row['modified']}\n")

    return report, potential_bytes


def main():
    inventory = newest_inventory()
    groups = load_inventory(inventory)

    duplicate_groups, extra_candidates = classify_duplicates(groups)

    report, potential_bytes = write_report(
        inventory,
        groups,
        duplicate_groups,
        extra_candidates,
    )

    print("===== DUPLICATE REVIEW =====")
    print(f"Inventory:              {inventory.name}")
    print(f"Duplicate groups:       {len(duplicate_groups)}")
    print(f"Extra-copy candidates:  {len(extra_candidates)}")
    print(
        f"Potential GB:           "
        f"{potential_bytes / (1024 ** 3):.2f}"
    )
    print()
    print(f"Review report:          {report}")
    print()
    print("NO FILES WERE MODIFIED.")
    print("NO FILES WERE DELETED.")


if __name__ == "__main__":
    main()
