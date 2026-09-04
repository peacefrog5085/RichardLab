import os
from pathlib import Path
import psutil

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
    "reports",
    "value_flow",
]

def module_status(name):
    path = LAB / name

    if not path.exists():
        return "MISSING", 0

    files = [p for p in path.rglob("*") if p.is_file()]

    if not files:
        return "EMPTY", 0

    if name == "experiments":
        return "ACTIVE", len(files)

    if name == "reports":
        return "ACTIVE", len(files)

    if name == "mission_control":
        return "ACTIVE", len(files)

    return "READY", len(files)

def system_health():
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage(str(LAB))

    def level(value, warning, critical):
        if value >= critical:
            return "CRITICAL"
        if value >= warning:
            return "WATCH"
        return "NORMAL"

    return {
        "cpu": level(cpu, 70, 90),
        "ram": level(ram.percent, 75, 90),
        "disk": level(disk.percent, 80, 95),
        "cpu_value": cpu,
        "ram_value": ram.percent,
        "disk_value": disk.percent,
    }

def overall_status(system, modules):
    if any(value == "CRITICAL" for value in system.values()):
        return "ATTENTION"

    if any(status == "MISSING" for status, _ in modules.values()):
        return "DEGRADED"

    return "OPERATIONAL"

def main():
    system = system_health()

    modules = {
        name: module_status(name)
        for name in MODULES
    }

    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║                  RICHARDLAB HEALTH                  ║")
    print("║                       v2.0                           ║")
    print("╠══════════════════════════════════════════════════════╣")
    print("║                                                      ║")

    print("║ SYSTEM")
    print(f"║ CPU:        {system['cpu']:9} ({system['cpu_value']:5.1f}%)")
    print(f"║ RAM:        {system['ram']:9} ({system['ram_value']:5.1f}%)")
    print(f"║ DISK:       {system['disk']:9} ({system['disk_value']:5.1f}%)")
    print("║")

    print("╠══════════════════════════════════════════════════════╣")
    print("║ MODULES")
    print("║")

    for name, (status, count) in modules.items():
        print(f"║ {name.upper():18} {status:10} {count:5} files")

    print("║")

    overall = overall_status(system, modules)

    print("╠══════════════════════════════════════════════════════╣")
    print(f"║ LAB HEALTH: {overall}")
    print("╚══════════════════════════════════════════════════════╝")
    print()

if __name__ == "__main__":
    main()
