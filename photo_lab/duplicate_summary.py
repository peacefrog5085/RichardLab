#!/usr/bin/env python3

import csv
import json
from collections import defaultdict, Counter
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"

def newest_inventory():
    files = sorted(DATA_DIR.glob("photo_inventory_*.csv"))
    if not files:
        raise FileNotFoundError("No photo inventory found.")
    return files[-1]

def score_file(row):
    path = row["path"].lower()
    score = 50

    if "/pictures/20" in path:
        score += 20

    if "2017/" in path or "2018/" in path:
        score += 5

    modified = row.get("modified", "")
    if modified.startswith(("2017-", "2018-", "2019-", "2020-", "2021-")):
        score += 15
    elif modified.startswith(("2024-", "2025-", "2026-")):
        score -= 5

    if "my buddy" in path or "my love" in path:
        score += 5

    if "pictures-1-001" in path:
        score -= 10

    return score

def main():
    inventory = newest_inventory()
    groups = defaultdict(list)

    with inventory.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            groups[row["sha256"]].append(row)

    duplicate_groups = [
        rows for rows in groups.values()
        if len(rows) > 1
    ]

    candidates = []
    folder_counts = Counter()
    potential_bytes = 0

    for rows in duplicate_groups:
        scored = sorted(
            rows,
            key=lambda row: (
                -score_file(row),
                len(row["path"]),
                row["path"],
            ),
        )

        keeper = scored[0]

        for row in scored[1:]:
            score = score_file(row)

            candidates.append({
                "path": row["path"],
                "keeper": keeper["path"],
                "sha256": row["sha256"],
                "size_bytes": int(row["size_bytes"]),
                "score": score,
            })

            potential_bytes += int(row["size_bytes"])

            folder = str(Path(row["path"]).parent)
            folder_counts[folder] += 1

    high_confidence = [
        item for item in candidates
        if item["score"] <= 35
    ]

    medium_confidence = [
        item for item in candidates
        if 36 <= item["score"] <= 60
    ]

    summary = {
        "lab": "RichardLab",
        "module": "photo_lab",
        "inventory": inventory.name,
        "duplicate_groups": len(duplicate_groups),
        "extra_copy_candidates": len(candidates),
        "high_confidence_candidates": len(high_confidence),
        "medium_confidence_candidates": len(medium_confidence),
        "potential_recoverable_bytes": potential_bytes,
        "potential_recoverable_gb": round(
            potential_bytes / (1024 ** 3), 3
        ),
        "top_candidate_folders": [
            {
                "folder": folder,
                "candidate_count": count,
            }
            for folder, count in folder_counts.most_common(10)
        ],
        "safety": {
            "files_modified": False,
            "files_moved": False,
            "files_deleted": False,
        },
    }

    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
