#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime
import csv
import hashlib

PHOTO_ROOT = Path.home() / "Pictures"
DATA_DIR = Path.home() / "RichardLab" / "photo_lab" / "data"
REPORT_DIR = Path.home() / "RichardLab" / "photo_lab" / "reports"

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp"
}


def sha256_file(path, chunk_size=1024 * 1024):
    digest = hashlib.sha256()

    with path.open("rb") as f:
        while chunk := f.read(chunk_size):
            digest.update(chunk)

    return digest.hexdigest()


def find_images():
    return sorted(
        path for path in PHOTO_ROOT.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def main():
    if not PHOTO_ROOT.exists():
        print(f"Photo directory not found: {PHOTO_ROOT}")
        return 1

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    images = find_images()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = DATA_DIR / f"photo_inventory_{timestamp}.csv"

    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║                 RICHARDLAB PHOTO LAB                   ║")
    print("║                  INVENTORY v0.1                        ║")
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
            "size_bytes",
            "modified",
            "sha256",
        ])

        for number, path in enumerate(images, 1):
            stat = path.stat()

            modified = datetime.fromtimestamp(
                stat.st_mtime
            ).isoformat(timespec="seconds")

            file_hash = sha256_file(path)

            writer.writerow([
                str(path),
                path.name,
                path.suffix.lower(),
                stat.st_size,
                modified,
                file_hash,
            ])

            if number % 100 == 0 or number == len(images):
                print(f"Indexed {number}/{len(images)}")

    print()
    print("Inventory complete.")
    print(f"Catalog: {output}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
