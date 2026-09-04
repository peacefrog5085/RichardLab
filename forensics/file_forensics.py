#!/usr/bin/env python3

import argparse
import hashlib
import json
import mimetypes
import os
import pwd
import grp
from datetime import datetime
from pathlib import Path


def sha256_file(path):
    digest = hashlib.sha256()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def file_record(path):
    stat = path.stat()

    try:
        owner = pwd.getpwuid(stat.st_uid).pw_name
    except KeyError:
        owner = str(stat.st_uid)

    try:
        group = grp.getgrgid(stat.st_gid).gr_name
    except KeyError:
        group = str(stat.st_gid)

    mime, _ = mimetypes.guess_type(path.name)

    return {
        "name": path.name,
        "path": str(path.resolve()),
        "size_bytes": stat.st_size,
        "sha256": sha256_file(path),
        "mime_type": mime or "unknown",
        "permissions": oct(stat.st_mode & 0o777),
        "owner": owner,
        "group": group,
        "modified": datetime.fromtimestamp(
            stat.st_mtime
        ).isoformat(),

        "accessed": datetime.fromtimestamp(
            stat.st_atime
        ).isoformat(),

        "created": datetime.fromtimestamp(
            stat.st_ctime
        ).isoformat(),
    }


def collect_files(target):
    if target.is_file():
        return [target]

    return sorted(
        p for p in target.rglob("*")
        if p.is_file()
    )


def main():
    parser = argparse.ArgumentParser(
        description="RichardLab Digital Forensics File Analyzer"
    )

    parser.add_argument(
        "target",
        help="File or directory to examine"
    )

    parser.add_argument(
        "-o",
        "--output",
        help="Output JSON report path"
    )

    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()

    if not target.exists():
        print(f"ERROR: Target does not exist: {target}")
        raise SystemExit(1)

    files = collect_files(target)

    print()
    print("RICHARDLAB DIGITAL FORENSICS")
    print("============================")
    print(f"Target: {target}")
    print(f"Files found: {len(files)}")
    print()

    records = []

    for index, path in enumerate(files, start=1):
        print(f"[{index}/{len(files)}] Analyzing: {path.name}")

        try:
            record = file_record(path)
            records.append(record)
        except PermissionError:
            print("  Permission denied")
        except OSError as e:
            print(f"  ERROR: {e}")

    report = {
        "tool": "RichardLab Digital Forensics",
        "version": "1.0",
        "generated": datetime.now().isoformat(),
        "target": str(target),
        "file_count": len(records),
        "files": records,
    }

    if args.output:
        output = Path(args.output).expanduser().resolve()
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output = (
            Path.home()
            / "RichardLab"
            / "forensics"
            / f"forensic_report_{timestamp}.json"
        )

    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print()
    print("============================")
    print("FORENSIC SCAN COMPLETE")
    print(f"Records: {len(records)}")
    print(f"Report:  {output}")
    print("============================")
    print()


if __name__ == "__main__":
    main()
