#!/usr/bin/env python3

from pathlib import Path
from collections import Counter
from datetime import datetime
import csv
import subprocess

PHOTO_ROOT = Path.home() / "Pictures"
PHOTO_LAB = Path.home() / "RichardLab" / "photo_lab"
DATA_DIR = PHOTO_LAB / "data"

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp"
}


def find_images():
    return sorted(
        p for p in PHOTO_ROOT.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )


def read_metadata(path):
    command = [
        "exiftool",
        "-DateTimeOriginal",
        "-CreateDate",
        "-GPSLatitude",
        "-GPSLongitude",
        "-Make",
        "-Model",
        "-FileType",
        str(path),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    metadata = {
        "original": "",
        "create": "",
        "lat": "",
        "lon": "",
        "make": "",
        "model": "",
        "type": "",
    }

    field_map = {
        "Date/Time Original": "original",
        "Create Date": "create",
        "GPS Latitude": "lat",
        "GPS Longitude": "lon",
        "Make": "make",
        "Camera Model Name": "model",
        "File Type": "type",
    }

    for line in result.stdout.splitlines():
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        if key in field_map:
            metadata[field_map[key]] = value

    return metadata


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    images = find_images()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = DATA_DIR / f"photo_metadata_{timestamp}.csv"

    years = Counter()
    extensions = Counter()

    date_count = 0
    gps_count = 0
    camera_count = 0

    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║                 RICHARDLAB PHOTO LAB                   ║")
    print("║              METADATA ANALYZER v0.1                   ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print("║ READ-ONLY MODE                                         ║")
    print("║ Originals will NOT be modified.                       ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    print(f"Scanning: {PHOTO_ROOT}")
    print(f"Images found: {len(images)}")
    print()

    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow([
            "path",
            "filename",
            "extension",
            "date_original",
            "create_date",
            "gps_latitude",
            "gps_longitude",
            "make",
            "model",
            "file_type",
        ])

        for number, path in enumerate(images, 1):
            metadata = read_metadata(path)

            if metadata["original"]:
                date_count += 1

                try:
                    import re
                    match = re.match(r"^(\d{4}):\d{2}:\d{2}", metadata["original"])
                    if match:
                        year = match.group(1)
                        years[year] += 1
                except Exception:
                    pass

            if metadata["lat"] and metadata["lon"]:
                gps_count += 1

            if metadata["make"] or metadata["model"]:
                camera_count += 1

            extensions[path.suffix.lower()] += 1

            writer.writerow([
                str(path),
                path.name,
                path.suffix.lower(),
                metadata["original"],
                metadata["create"],
                metadata["lat"],
                metadata["lon"],
                metadata["make"],
                metadata["model"],
                metadata["type"],
            ])

            if number % 100 == 0 or number == len(images):
                print(f"Analyzed {number}/{len(images)}")

    print()
    print("===== METADATA SUMMARY =====")
    print(f"Images scanned:       {len(images)}")
    print(f"Capture dates:        {date_count}")
    print(f"GPS locations:        {gps_count}")
    print(f"Camera metadata:      {camera_count}")
    print()

    print("YEARS:")
    for year, count in sorted(years.items()):
        print(f"  {year}: {count}")

    print()
    print("FILE TYPES:")
    for ext, count in extensions.most_common():
        print(f"  {ext}: {count}")

    print()
    print(f"Catalog: {output}")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
