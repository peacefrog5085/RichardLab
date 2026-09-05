#!/usr/bin/env python3

import csv
import json
from collections import defaultdict, Counter
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).resolve().parent / "data"
REPORT_DIR = Path(__file__).resolve().parent / "reports"


def newest_file(pattern):
    files = sorted(DATA_DIR.glob(pattern))
    if not files:
        return None
    return files[-1]


def load_csv(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def parse_year(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(value).year
    except ValueError:
        pass

    try:
        return int(value[:4])
    except (ValueError, TypeError):
        return None


def folder_label(path):
    parts = Path(path).parts

    try:
        pictures_index = parts.index("Pictures")
        relative = parts[pictures_index + 1:]
    except ValueError:
        relative = parts[-3:]

    if not relative:
        return "/Pictures"

    return "/Pictures/" + "/".join(relative[:-1])


def analyze():
    inventory_path = newest_file("photo_inventory_*.csv")

    if not inventory_path:
        raise FileNotFoundError("No photo inventory CSV found.")

    metadata_path = newest_file("photo_metadata_*.csv")

    inventory = load_csv(inventory_path)

    metadata_by_path = {}

    if metadata_path:
        metadata = load_csv(metadata_path)
        metadata_by_path = {
            row["path"]: row
            for row in metadata
        }

    # Map every hash to every location.
    hash_locations = defaultdict(list)

    for row in inventory:
        hash_locations[row["sha256"]].append(row["path"])

    # Analyze folders.
    folders = defaultdict(list)

    for row in inventory:
        folder = str(Path(row["path"]).parent)
        folders[folder].append(row)

    results = []

    for folder, rows in folders.items():
        total = len(rows)
        exact_duplicate_count = 0
        unique_count = 0
        duplicate_bytes = 0
        years = Counter()
        cameras = Counter()

        for row in rows:
            locations = hash_locations[row["sha256"]]

            if len(locations) > 1:
                exact_duplicate_count += 1
                duplicate_bytes += int(row["size_bytes"])
            else:
                unique_count += 1

            metadata = metadata_by_path.get(row["path"], {})

            capture = metadata.get("date_original", "")
            year = parse_year(capture)

            if year:
                years[year] += 1

            camera = (
                f"{metadata.get('make', '')} "
                f"{metadata.get('model', '')}"
            ).strip()

            if camera:
                cameras[camera] += 1

        duplicate_percent = (
            (exact_duplicate_count / total) * 100
            if total else 0
        )

        results.append({
            "folder": folder,
            "total_images": total,
            "exact_duplicates": exact_duplicate_count,
            "unique_images": unique_count,
            "duplicate_percent": round(duplicate_percent, 1),
            "duplicate_bytes": duplicate_bytes,
            "duplicate_gb": round(
                duplicate_bytes / (1024 ** 3), 3
            ),
            "capture_years": dict(sorted(years.items())),
            "cameras": dict(cameras.most_common(10)),
        })

    results.sort(
        key=lambda item: (
            -item["exact_duplicates"],
            -item["total_images"],
            item["folder"],
        )
    )

    return inventory_path, metadata_path, results


def recommendation(item):
    total = item["total_images"]
    duplicate_percent = item["duplicate_percent"]
    unique = item["unique_images"]

    if total == 0:
        return "EMPTY"

    if unique == 0:
        return "DUPLICATE COLLECTION - REVIEW"

    if duplicate_percent >= 90:
        return "HIGH REDUNDANCY - REVIEW"

    if duplicate_percent >= 60:
        return "SUBSTANTIAL OVERLAP - REVIEW"

    if duplicate_percent >= 25:
        return "PARTIAL OVERLAP - PRESERVE CONTEXT"

    return "MOSTLY UNIQUE - PRESERVE"


def write_report(inventory_path, metadata_path, results):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    report_path = REPORT_DIR / "collection_intelligence_latest.txt"

    total_images = sum(x["total_images"] for x in results)
    duplicate_images = sum(x["exact_duplicates"] for x in results)
    unique_images = sum(x["unique_images"] for x in results)
    duplicate_bytes = sum(x["duplicate_bytes"] for x in results)

    with report_path.open("w", encoding="utf-8") as f:

        f.write("RICHARDLAB PHOTO LAB\n")
        f.write("====================\n")
        f.write("COLLECTION INTELLIGENCE\n\n")

        f.write(f"Inventory: {inventory_path.name}\n")

        if metadata_path:
            f.write(f"Metadata:  {metadata_path.name}\n")
        else:
            f.write("Metadata:  NOT AVAILABLE\n")

        f.write("\n")
        f.write("LIBRARY SUMMARY\n")
        f.write("---------------\n")
        f.write(f"Folders analyzed:       {len(results)}\n")
        f.write(f"Images analyzed:        {total_images}\n")
        f.write(f"Images with duplicates: {duplicate_images}\n")
        f.write(f"Unique images:           {unique_images}\n")
        f.write(
            f"Duplicate bytes:        "
            f"{duplicate_bytes:,}\n"
        )
        f.write(
            f"Duplicate GB:           "
            f"{duplicate_bytes / (1024 ** 3):.3f}\n"
        )

        f.write("\n")
        f.write("=" * 78 + "\n")
        f.write("FOLDER ANALYSIS\n")
        f.write("=" * 78 + "\n")

        for number, item in enumerate(results, start=1):

            f.write("\n")
            f.write(f"COLLECTION {number:04d}\n")
            f.write("-" * 78 + "\n")

            f.write(f"Folder:              {item['folder']}\n")
            f.write(f"Total images:        {item['total_images']}\n")
            f.write(f"Exact duplicates:    {item['exact_duplicates']}\n")
            f.write(f"Unique images:       {item['unique_images']}\n")
            f.write(
                f"Duplicate percent:   "
                f"{item['duplicate_percent']:.1f}%\n"
            )
            f.write(
                f"Duplicate GB:        "
                f"{item['duplicate_gb']:.3f}\n"
            )

            f.write(
                f"Recommendation:      "
                f"{recommendation(item)}\n"
            )

            if item["capture_years"]:
                f.write("\nCapture years:\n")

                for year, count in item["capture_years"].items():
                    f.write(f"  {year}: {count}\n")

            if item["cameras"]:
                f.write("\nCameras:\n")

                for camera, count in item["cameras"].items():
                    f.write(f"  {camera}: {count}\n")

        f.write("\n")
        f.write("=" * 78 + "\n")
        f.write("SAFETY\n")
        f.write("=" * 78 + "\n")
        f.write("NO FILES WERE MODIFIED.\n")
        f.write("NO FILES WERE MOVED.\n")
        f.write("NO FILES WERE DELETED.\n")
        f.write(
            "Recommendations describe collection structure only.\n"
        )
        f.write(
            "Folder organization is preserved as provenance.\n"
        )

    return report_path


def main():
    inventory_path, metadata_path, results = analyze()

    report_path = write_report(
        inventory_path,
        metadata_path,
        results,
    )

    total = sum(x["total_images"] for x in results)
    duplicates = sum(x["exact_duplicates"] for x in results)
    unique = sum(x["unique_images"] for x in results)

    print("===== COLLECTION INTELLIGENCE =====")
    print(f"Inventory:              {inventory_path.name}")

    if metadata_path:
        print(f"Metadata:               {metadata_path.name}")
    else:
        print("Metadata:               NOT AVAILABLE")

    print(f"Folders analyzed:       {len(results)}")
    print(f"Images analyzed:        {total}")
    print(f"Images with duplicates: {duplicates}")
    print(f"Unique images:          {unique}")
    print()
    print(f"Report:                 {report_path}")
    print()
    print("NO FILES WERE MODIFIED.")
    print("NO FILES WERE MOVED.")
    print("NO FILES WERE DELETED.")


if __name__ == "__main__":
    main()
