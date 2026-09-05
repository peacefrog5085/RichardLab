#!/usr/bin/env python3

import csv
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

    samantha_a = []
    samantha_b = []

    for row in rows:
        path = row["path"]

        if (
            "My Love Samantha R Sprague -1-001 (2)"
            in path
        ):
            samantha_a.append(row)

        elif (
            "My Love Samantha R Sprague -1-001"
            in path
        ):
            samantha_b.append(row)

    hashes_a = {
        row["sha256"]: row
        for row in samantha_a
    }

    hashes_b = {
        row["sha256"]: row
        for row in samantha_b
    }

    matched = []
    unmatched = []

    for row in samantha_b:
        sha = row["sha256"]

        if sha in hashes_a:
            keeper = hashes_a[sha]

            matched.append({
                "decision": "QUARANTINE_CANDIDATE",
                "sha256": sha,
                "original_path": row["path"],
                "keeper_path": keeper["path"],
                "size_bytes": row["size_bytes"],
                "modified": row["modified"],
                "quarantine_destination": (
                    "~/RichardLab/photo_lab/"
                    "quarantine/Samantha_duplicate/"
                    + Path(row["path"]).name
                ),
                "rollback_note": (
                    "Restore original_path and verify "
                    "SHA-256 before permanent deletion."
                ),
            })
        else:
            unmatched.append(row)

    manifest_path = (
        REPORT_DIR / "quarantine_manifest_latest.csv"
    )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    fields = [
        "decision",
        "sha256",
        "original_path",
        "keeper_path",
        "size_bytes",
        "modified",
        "quarantine_destination",
        "rollback_note",
    ]

    with manifest_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fields,
        )

        writer.writeheader()

        for row in matched:
            writer.writerow(row)

        for row in unmatched:
            writer.writerow({
                "decision": "PROTECTED_UNMATCHED",
                "sha256": row["sha256"],
                "original_path": row["path"],
                "keeper_path": "",
                "size_bytes": row["size_bytes"],
                "modified": row["modified"],
                "quarantine_destination": "",
                "rollback_note": (
                    "DO NOT MOVE. No identical counterpart "
                    "was found in Samantha (2)."
                ),
            })

    print("===== SAMANTHA QUARANTINE MANIFEST =====")
    print(f"Inventory:              {inventory_path.name}")
    print()
    print(f"Samantha (2) files:     {len(samantha_a)}")
    print(f"Samantha files:         {len(samantha_b)}")
    print(f"Exact matches:          {len(matched)}")
    print(f"Unmatched/protected:    {len(unmatched)}")
    print()
    print(f"Manifest:               {manifest_path}")
    print()
    print("NO FILES WERE MOVED.")
    print("NO FILES WERE DELETED.")
    print("NO FILES WERE MODIFIED.")

    if unmatched:
        print()
        print("WARNING:")
        print(
            "Unmatched files were protected and must be reviewed."
        )


if __name__ == "__main__":
    main()
