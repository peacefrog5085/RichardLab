#!/usr/bin/env python3

from pathlib import Path


LAB = Path.home() / "RichardLab"
FORENSICS_DIR = LAB / "forensics"


def forensic_reports():
    if not FORENSICS_DIR.exists():
        return []

    return sorted(
        FORENSICS_DIR.glob("forensic_report_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def latest_report():
    reports = forensic_reports()
    return reports[0] if reports else None


def print_reports():
    reports = forensic_reports()

    if not reports:
        print("No forensic reports found.")
        return

    print("FORENSIC SNAPSHOTS")
    print("────────────────────────────────────────")

    for index, report in enumerate(reports, start=1):
        print(f"{index}) {report.name}")

    print()
    print(f"LATEST: {reports[0].name}")


if __name__ == "__main__":
    print_reports()
