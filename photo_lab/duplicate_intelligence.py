#!/usr/bin/env python3

import csv
from collections import defaultdict
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).resolve().parent / "data"
REPORT_DIR = Path(__file__).resolve().parent / "reports"


def newest_inventory():
    files = sorted(DATA_DIR.glob("photo_inventory_*.csv"))
    if not files:
        raise FileNotFoundError("No photo inventory CSV found.")
    return files[-1]


def newest_metadata():
    files = sorted(DATA_DIR.glob("photo_metadata_*.csv"))
    if not files:
        return None
    return files[-1]


def load_csv(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def score_file(row):
    path = row["path"]
    score = 50
    reasons = []

    # Prefer dated archive folders.
    if "/Pictures/20" in path:
        score += 20
        reasons.append("dated archive")

    # Older modification dates are useful provenance evidence.
    modified = row.get("modified", "")
    if modified:
        try:
            year = datetime.fromisoformat(modified).year
            if year <= 2021:
                score += 15
                reasons.append("older file timestamp")
            elif year >= 2024:
                score -= 5
                reasons.append("recent file timestamp")
        except ValueError:
            pass

    # Named folders can contain meaningful organizational context.
    path_lower = path.lower()

    if "my buddy" in path_lower:
        score += 5
        reasons.append("named-person context")

    if "my love" in path_lower:
        score += 5
        reasons.append("named-person context")

    # Generic import/copy folders are weaker provenance candidates.
    if "pictures-1-001" in path_lower:
        score -= 10
        reasons.append("generic copy/import folder")

    # Prefer paths with a normal dated photo archive structure.
    if "/Pictures/2017/" in path or "/Pictures/2018/" in path:
        score += 5
        reasons.append("historical archive structure")

    return score, reasons


def main():
    inventory_path = newest_inventory()
    metadata_path = newest_metadata()

    inventory = load_csv(inventory_path)

    metadata_by_path = {}

    if metadata_path:
        metadata = load_csv(metadata_path)
        metadata_by_path = {
            row["path"]: row
            for row in metadata
        }

    groups = defaultdict(list)

    for row in inventory:
        groups[row["sha256"]].append(row)

    duplicate_groups = [
        (sha256, rows)
        for sha256, rows in groups.items()
        if len(rows) > 1
    ]

    duplicate_groups.sort(
        key=lambda item: min(row["path"] for row in item[1])
    )

    report_path = REPORT_DIR / "duplicate_intelligence_latest.txt"
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    potential_bytes = 0
    extra_candidates = 0

    with report_path.open("w", encoding="utf-8") as report:

        report.write("RICHARDLAB PHOTO LAB\n")
        report.write("====================\n")
        report.write("DUPLICATE INTELLIGENCE / PROVENANCE REVIEW\n\n")

        report.write(f"Inventory: {inventory_path.name}\n")

        if metadata_path:
            report.write(f"Metadata:  {metadata_path.name}\n")
        else:
            report.write("Metadata:  NOT AVAILABLE\n")

        report.write(f"Duplicate groups: {len(duplicate_groups)}\n")

        for number, (sha256, rows) in enumerate(
            duplicate_groups,
            start=1
        ):

            scored = []

            for row in rows:
                score, reasons = score_file(row)

                metadata = metadata_by_path.get(row["path"], {})

                scored.append({
                    "row": row,
                    "score": score,
                    "reasons": reasons,
                    "metadata": metadata,
                })

            scored.sort(
                key=lambda item: (
                    -item["score"],
                    len(item["row"]["path"]),
                    item["row"]["path"],
                )
            )

            keeper = scored[0]

            report.write("\n")
            report.write("=" * 72 + "\n")
            report.write(f"GROUP {number:04d}\n")
            report.write("=" * 72 + "\n")

            report.write(f"SHA-256: {sha256}\n")
            report.write(f"Copies: {len(rows)}\n")

            report.write("\nRECOMMENDED KEEPER\n")
            report.write("------------------\n")
            report.write(f"Score: {keeper['score']}/100\n")
            report.write(f"Path:  {keeper['row']['path']}\n")
            report.write(
                f"Size:  {keeper['row']['size_bytes']} bytes\n"
            )
            report.write(
                f"Modified: {keeper['row']['modified']}\n"
            )

            if keeper["reasons"]:
                report.write(
                    "Evidence: " + ", ".join(keeper["reasons"]) + "\n"
                )

            md = keeper["metadata"]

            if md:
                report.write(
                    f"Capture date: "
                    f"{md.get('date_original') or 'unknown'}\n"
                )
                report.write(
                    f"Camera: "
                    f"{md.get('make') or ''} "
                    f"{md.get('model') or ''}\n"
                )

                if (
                    md.get("gps_latitude")
                    and md.get("gps_longitude")
                ):
                    report.write("GPS: PRESENT\n")

            report.write("\nALL COPIES\n")
            report.write("----------\n")

            for item in scored:
                row = item["row"]

                if row["path"] == keeper["row"]["path"]:
                    status = "KEEP"
                else:
                    status = "REVIEW"

                    try:
                        potential_bytes += int(row["size_bytes"])
                    except ValueError:
                        pass

                    extra_candidates += 1

                report.write(f"\n[{status}]\n")
                report.write(f"Score: {item['score']}/100\n")
                report.write(f"Path: {row['path']}\n")
                report.write(f"Size: {row['size_bytes']} bytes\n")
                report.write(f"Modified: {row['modified']}\n")

                if item["reasons"]:
                    report.write(
                        "Evidence: "
                        + ", ".join(item["reasons"])
                        + "\n"
                    )

                md = item["metadata"]

                if md:
                    report.write(
                        f"Capture date: "
                        f"{md.get('date_original') or 'unknown'}\n"
                    )

                    camera = (
                        f"{md.get('make') or ''} "
                        f"{md.get('model') or ''}"
                    ).strip()

                    if camera:
                        report.write(f"Camera: {camera}\n")

                    if (
                        md.get("gps_latitude")
                        and md.get("gps_longitude")
                    ):
                        report.write("GPS: PRESENT\n")

        report.write("\n")
        report.write("=" * 72 + "\n")
        report.write("SUMMARY\n")
        report.write("=" * 72 + "\n")
        report.write(
            f"Duplicate groups:       {len(duplicate_groups)}\n"
        )
        report.write(
            f"Extra-copy candidates:  {extra_candidates}\n"
        )
        report.write(
            f"Potential recoverable GB: "
            f"{potential_bytes / (1024 ** 3):.2f}\n"
        )
        report.write("\n")
        report.write("SAFETY\n")
        report.write("------\n")
        report.write("NO FILES WERE MODIFIED.\n")
        report.write("NO FILES WERE MOVED.\n")
        report.write("NO FILES WERE DELETED.\n")
        report.write(
            "Scores are recommendations, not deletion commands.\n"
        )
        report.write(
            "Folder context is preserved because provenance matters.\n"
        )

    print("===== DUPLICATE INTELLIGENCE =====")
    print(f"Inventory:              {inventory_path.name}")

    if metadata_path:
        print(f"Metadata:               {metadata_path.name}")
    else:
        print("Metadata:               NOT AVAILABLE")

    print(f"Duplicate groups:       {len(duplicate_groups)}")
    print(f"Extra-copy candidates:  {extra_candidates}")
    print(
        f"Potential GB:           "
        f"{potential_bytes / (1024 ** 3):.2f}"
    )
    print()
    print(f"Report:                 {report_path}")
    print()
    print("NO FILES WERE MODIFIED.")
    print("NO FILES WERE MOVED.")
    print("NO FILES WERE DELETED.")


if __name__ == "__main__":
    main()
