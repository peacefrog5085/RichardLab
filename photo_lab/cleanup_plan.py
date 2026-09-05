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

    hashes = defaultdict(list)

    for row in rows:
        hashes[row["sha256"]].append(row)

    folders = defaultdict(list)

    for row in rows:
        folders[str(Path(row["path"]).parent)].append(row)

    plans = []

    for folder, files in folders.items():
        total = len(files)

        unique = sum(
            1 for row in files
            if len(hashes[row["sha256"]]) == 1
        )

        duplicate = total - unique

        if total == 0:
            continue

        if unique == 0:
            action = "REVIEW COMPLETE DUPLICATE COLLECTION"
        elif duplicate / total >= 0.90:
            action = "REVIEW HIGH-REDUNDANCY COLLECTION"
        elif duplicate / total >= 0.25:
            action = "PRESERVE COLLECTION / REVIEW DUPLICATES"
        else:
            action = "PRESERVE COLLECTION"

        duplicate_bytes = sum(
            int(row["size_bytes"])
            for row in files
            if len(hashes[row["sha256"]]) > 1
        )

        plans.append({
            "folder": folder,
            "total": total,
            "unique": unique,
            "duplicate": duplicate,
            "duplicate_percent": round(
                duplicate / total * 100, 1
            ),
            "duplicate_bytes": duplicate_bytes,
            "action": action,
        })

    plans.sort(
        key=lambda item: (
            -item["duplicate_percent"],
            -item["total"],
            item["folder"],
        )
    )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    report_path = REPORT_DIR / "cleanup_plan_latest.txt"

    with report_path.open("w", encoding="utf-8") as f:
        f.write("RICHARDLAB PHOTO LAB\n")
        f.write("====================\n")
        f.write("SAFE CLEANUP PLAN\n\n")

        f.write(f"Inventory: {inventory_path.name}\n\n")

        f.write("IMPORTANT SAFETY RULES\n")
        f.write("----------------------\n")
        f.write("NO FILES WILL BE DELETED.\n")
        f.write("NO FILES WILL BE MOVED.\n")
        f.write("NO FILES WILL BE MODIFIED.\n")
        f.write("This report contains recommendations only.\n\n")

        f.write("=" * 78 + "\n")
        f.write("PROPOSED COLLECTION ACTIONS\n")
        f.write("=" * 78 + "\n")

        for number, plan in enumerate(plans, start=1):
            f.write("\n")
            f.write(f"COLLECTION {number:04d}\n")
            f.write("-" * 78 + "\n")
            f.write(f"Folder:             {plan['folder']}\n")
            f.write(f"Total images:       {plan['total']}\n")
            f.write(f"Unique images:      {plan['unique']}\n")
            f.write(f"Duplicate images:   {plan['duplicate']}\n")
            f.write(
                f"Duplicate percent:  "
                f"{plan['duplicate_percent']:.1f}%\n"
            )
            f.write(
                f"Duplicate bytes:    "
                f"{plan['duplicate_bytes']:,}\n"
            )
            f.write(f"PROPOSED ACTION:    {plan['action']}\n")

            if plan["unique"] == 0:
                f.write(
                    "NOTE: Every image in this collection exists "
                    "elsewhere by SHA-256.\n"
                )

            elif plan["duplicate"] == 0:
                f.write(
                    "NOTE: No exact duplicate images were found "
                    "in this collection.\n"
                )

            else:
                f.write(
                    "NOTE: Preserve the collection; review duplicate "
                    "files individually.\n"
                )

        f.write("\n")
        f.write("=" * 78 + "\n")
        f.write("FINAL SAFETY CHECK\n")
        f.write("=" * 78 + "\n")
        f.write("DELETION EXECUTED: NO\n")
        f.write("MOVEMENT EXECUTED: NO\n")
        f.write("MODIFICATION EXECUTED: NO\n")

    print("===== SAFE CLEANUP PLAN =====")
    print(f"Inventory:       {inventory_path.name}")
    print(f"Collections:     {len(plans)}")
    print()
    print(f"Report:          {report_path}")
    print()
    print("NO FILES WERE DELETED.")
    print("NO FILES WERE MOVED.")
    print("NO FILES WERE MODIFIED.")


if __name__ == "__main__":
    main()
