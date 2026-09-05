#!/usr/bin/env python3

import csv
import hashlib
import shutil
from pathlib import Path
from datetime import datetime

LAB_ROOT = Path.home() / "RichardLab"
PICTURES_ROOT = Path.home() / "Pictures"

MANIFEST = (
    LAB_ROOT
    / "photo_lab"
    / "reports"
    / "quarantine_manifest_latest.csv"
)

QUARANTINE_ROOT = (
    LAB_ROOT
    / "photo_lab"
    / "quarantine"
    / "Samantha_duplicate"
)

LOG = (
    LAB_ROOT
    / "photo_lab"
    / "reports"
    / "quarantine_execution_latest.csv"
)


def sha256_file(path):
    h = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)

    return h.hexdigest()


def main():
    if not MANIFEST.exists():
        raise FileNotFoundError(
            f"Manifest not found: {MANIFEST}"
        )

    rows = []

    with MANIFEST.open(
        newline="",
        encoding="utf-8",
    ) as f:
        rows = list(csv.DictReader(f))

    candidates = [
        row
        for row in rows
        if row["decision"] == "QUARANTINE_CANDIDATE"
    ]

    if not candidates:
        print("No quarantine candidates found.")
        return

    print("===== RICHARDLAB SAFE QUARANTINE =====")
    print(f"Candidates: {len(candidates)}")
    print()
    print("This operation will:")
    print("1. Verify each original exists.")
    print("2. Verify its SHA-256.")
    print("3. Copy it into quarantine.")
    print("4. Verify the quarantine copy.")
    print("5. Record the transaction.")
    print("6. Remove the original ONLY after verification.")
    print()
    print("QUARANTINE IS REVERSIBLE.")
    print("PERMANENT DELETION WILL NOT OCCUR.")
    print()

    confirmation = input(
        "Type QUARANTINE-SAMANTHA to proceed: "
    )

    if confirmation != "QUARANTINE-SAMANTHA":
        print("Confirmation not received.")
        print("NO FILES WERE MODIFIED.")
        print("NO FILES WERE MOVED.")
        return

    QUARANTINE_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    fields = [
        "timestamp",
        "status",
        "original_path",
        "quarantine_path",
        "expected_sha256",
        "original_sha256",
        "quarantine_sha256",
        "size_bytes",
        "error",
    ]

    success = 0
    failed = 0

    with LOG.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as log_file:

        writer = csv.DictWriter(
            log_file,
            fieldnames=fields,
        )

        writer.writeheader()

        for index, row in enumerate(candidates, start=1):

            original = Path(row["original_path"])
            expected_sha = row["sha256"]

            # Preserve the relative filename.
            destination = (
                QUARANTINE_ROOT
                / original.name
            )

            timestamp = datetime.now().isoformat(
                timespec="seconds"
            )

            print(
                f"[{index}/{len(candidates)}] "
                f"{original.name}"
            )

            try:
                if not original.exists():
                    raise FileNotFoundError(
                        "Original file does not exist."
                    )

                if not original.is_file():
                    raise RuntimeError(
                        "Original path is not a regular file."
                    )

                original_sha = sha256_file(original)

                if original_sha != expected_sha:
                    raise RuntimeError(
                        "ORIGINAL HASH MISMATCH"
                    )

                if destination.exists():
                    destination_sha = sha256_file(
                        destination
                    )

                    if destination_sha != expected_sha:
                        raise RuntimeError(
                            "QUARANTINE DESTINATION EXISTS "
                            "WITH DIFFERENT HASH"
                        )

                    # Already safely quarantined.
                    quarantine_sha = destination_sha

                else:
                    shutil.copy2(
                        original,
                        destination,
                    )

                    quarantine_sha = sha256_file(
                        destination
                    )

                    if quarantine_sha != expected_sha:
                        destination.unlink(
                            missing_ok=True
                        )

                        raise RuntimeError(
                            "QUARANTINE HASH VERIFICATION FAILED"
                        )

                # Only now remove the original.
                original.unlink()

                status = "QUARANTINED"
                success += 1

                error = ""

            except Exception as exc:
                status = "FAILED"
                failed += 1
                original_sha = ""
                quarantine_sha = ""
                error = str(exc)

            writer.writerow({
                "timestamp": timestamp,
                "status": status,
                "original_path": str(original),
                "quarantine_path": str(destination),
                "expected_sha256": expected_sha,
                "original_sha256": original_sha,
                "quarantine_sha256": quarantine_sha,
                "size_bytes": row["size_bytes"],
                "error": error,
            })

            log_file.flush()

    print()
    print("===== QUARANTINE COMPLETE =====")
    print(f"Successful: {success}")
    print(f"Failed:     {failed}")
    print()
    print(f"Quarantine: {QUARANTINE_ROOT}")
    print(f"Log:        {LOG}")
    print()
    print("PERMANENT DELETION: NONE")


if __name__ == "__main__":
    main()
