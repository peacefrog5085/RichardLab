#!/usr/bin/env python3

import os
import psutil
from pathlib import Path
from datetime import datetime


LAB = Path.home() / "RichardLab"

MODULES = [
    "ai",
    "data",
    "dashboard",
    "experiments",
    "forensics",
    "knowledge",
    "media",
    "mission_control",
    "photo_lab",
    "reports",
    "value_flow",
]


def count_files(directory):
    path = LAB / directory
    if not path.exists():
        return 0
    return sum(1 for p in path.rglob("*") if p.is_file())


def latest_file(directory):
    path = LAB / directory

    if not path.exists():
        return None

    files = [p for p in path.rglob("*") if p.is_file()]

    if not files:
        return None

    return max(files, key=lambda p: p.stat().st_mtime)


def get_lab_status():
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage(str(LAB))
    cpu = psutil.cpu_percent(interval=1)

    modules = {}

    for module in MODULES:
        path = LAB / module
        modules[module] = {
            "status": "READY" if path.exists() else "MISSING",
            "files": count_files(module),
        }

    latest = latest_file("reports")

    return {
        "lab": "RichardLab",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "host": os.uname().nodename,
        "system": {
            "cpu_percent": cpu,
            "ram_used_gb": round(memory.used / (1024**3), 2),
            "ram_total_gb": round(memory.total / (1024**3), 2),
            "ram_percent": memory.percent,
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_percent": disk.percent,
        },
        "modules": modules,
        "activity": {
            "experiment_files": count_files("experiments"),
            "report_files": count_files("reports"),
            "latest_report": latest.name if latest else None,
        },
    }


if __name__ == "__main__":
    import json

    print(json.dumps(get_lab_status(), indent=2))
