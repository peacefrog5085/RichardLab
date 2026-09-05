import os
import csv
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

def system_status():
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage(str(LAB))
    cpu = psutil.cpu_percent(interval=1)

    return cpu, memory, disk

def main():
    cpu, memory, disk = system_status()

    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║              RICHARDLAB MISSION CONTROL              ║")
    print("║                       v2.0                           ║")
    print("╠══════════════════════════════════════════════════════╣")
    print("║                                                      ║")

    print("║ SYSTEM")
    print(f"║ CPU:        {cpu:5.1f}%")
    print(f"║ RAM:        {memory.used / (1024**3):5.1f} / "
          f"{memory.total / (1024**3):.1f} GB ({memory.percent:5.1f}%)")
    print(f"║ DISK:       {disk.used / (1024**3):5.1f} / "
          f"{disk.total / (1024**3):.1f} GB ({disk.percent:5.1f}%)")
    print(f"║ HOST:       {os.uname().nodename}")
    print(f"║ TIME:       {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("║")

    print("╠══════════════════════════════════════════════════════╣")
    print("║ LAB MODULES")
    print("║")

    for module in MODULES:
        path = LAB / module
        status = "READY" if path.exists() else "MISSING"
        files = count_files(module)

        print(f"║ {module.upper():15} {status:8} {files:5} files")

    print("║")

    reports = count_files("reports")
    experiments = count_files("experiments")

    print("╠══════════════════════════════════════════════════════╣")
    print("║ LAB ACTIVITY")
    print("║")
    print(f"║ Experiment files: {experiments}")
    print(f"║ Report files:     {reports}")

    latest = latest_file("reports")

    if latest:
        print(f"║ Latest report:    {latest.name}")
    else:
        print("║ Latest report:    None")

    print("║")
    print("╠══════════════════════════════════════════════════════╣")
    print("║ STATUS: ONLINE")
    print("║")
    print("║ QUESTION EVERYTHING. VERIFY THE DATA.")
    print("╚══════════════════════════════════════════════════════╝")
    print()

if __name__ == "__main__":
    main()
