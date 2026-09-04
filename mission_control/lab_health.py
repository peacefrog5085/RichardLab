#!/usr/bin/env python3

from pathlib import Path
import subprocess
import re
import psutil

LAB = Path.home() / "RichardLab"
PROJECTS = LAB / "projects"
EXPERIMENTS = LAB / "experiments"
REPORTS = LAB / "reports"

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
]


def count_files(path):
    if not path.exists():
        return 0
    return sum(1 for p in path.rglob("*") if p.is_file())


def module_status(name):
    path = LAB / name

    if not path.exists():
        return "MISSING", 0

    files = count_files(path)

    if files == 0:
        return "EMPTY", 0

    if name in {"experiments", "reports", "mission_control"}:
        return "ACTIVE", files

    return "READY", files


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


def git_info():
    if not (LAB / ".git").exists():
        return {
            "branch": "NOT A REPO",
            "status": "UNKNOWN",
            "commit": "NONE",
        }

    def run_git(*args):
        try:
            result = subprocess.run(
                ["git", "-C", str(LAB), *args],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return ""

    branch = run_git("branch", "--show-current") or "UNKNOWN"
    status = "CLEAN" if not run_git("status", "--porcelain") else "CHANGES"
    commit = run_git("log", "-1", "--pretty=format:%h %s") or "UNKNOWN"

    return {
        "branch": branch,
        "status": status,
        "commit": commit,
    }


def project_info():
    if not PROJECTS.exists():
        return 0, 0

    discovered = 0
    ready = 0

    for path in PROJECTS.iterdir():
        if not path.is_dir():
            continue

        discovered += 1

        if (path / "control.sh").is_file() and (path / "control.sh").stat().st_mode & 0o111:
            ready += 1

    return discovered, ready


def experiment_files():
    if not EXPERIMENTS.exists():
        return []

    pattern = re.compile(r"experiment-(\d+)([a-z]?)\.(py|sh)$")

    return sorted(
        [
            path
            for path in EXPERIMENTS.iterdir()
            if path.is_file() and pattern.match(path.name)
        ],
        key=lambda path: (
            int(pattern.match(path.name).group(1)),
            pattern.match(path.name).group(2),
            path.name,
        ),
    )


def experiment_family_count(files):
    families = set()

    pattern = re.compile(r"experiment-(\d+)([a-z]?)\.(py|sh)$")

    for path in files:
        match = pattern.match(path.name)
        if match:
            families.add(match.group(1))

    return len(families)


def latest_file(path):
    if not path.exists():
        return None

    files = [p for p in path.rglob("*") if p.is_file()]

    if not files:
        return None

    return max(files, key=lambda p: p.stat().st_mtime)


def overall_status(system, modules, git):
    if any(
        system[key] == "CRITICAL"
        for key in ("cpu", "ram", "disk")
    ):
        return "ATTENTION"

    if any(
        status == "MISSING"
        for status, _ in modules.values()
    ):
        return "DEGRADED"

    if git["status"] == "CHANGES":
        return "WATCH"

    return "OPERATIONAL"


def main():
    system = system_health()
    modules = {
        name: module_status(name)
        for name in MODULES
    }

    git = git_info()
    projects, ready_projects = project_info()

    experiments = experiment_files()
    families = experiment_family_count(experiments)

    latest_experiment = latest_file(EXPERIMENTS)
    latest_report = latest_file(REPORTS)

    overall = overall_status(system, modules, git)

    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║                  RICHARDLAB HEALTH                     ║")
    print("║                       v3.0                             ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print("║                                                        ║")

    print("║ SYSTEM")
    print(f"║ CPU:        {system['cpu']:9} ({system['cpu_value']:5.1f}%)")
    print(f"║ RAM:        {system['ram']:9} ({system['ram_value']:5.1f}%)")
    print(f"║ DISK:       {system['disk']:9} ({system['disk_value']:5.1f}%)")
    print("║")

    print("╠══════════════════════════════════════════════════════════╣")
    print("║ GIT")
    print("║")
    print(f"║ Branch:     {git['branch']}")
    print(f"║ Working:    {git['status']}")
    print(f"║ Last commit: {git['commit']}")
    print("║")

    print("╠══════════════════════════════════════════════════════════╣")
    print("║ PROJECTS")
    print("║")
    print(f"║ Discovered: {projects}")
    print(f"║ Ready:      {ready_projects}")
    print("║")

    print("╠══════════════════════════════════════════════════════════╣")
    print("║ EXPERIMENTS")
    print("║")
    print(f"║ Experiments: {len(experiments)}")
    print(f"║ Families:    {families}")
    print("║")

    print("╠══════════════════════════════════════════════════════════╣")
    print("║ ACTIVITY")
    print("║")

    if latest_experiment:
        print(f"║ Latest experiment: {latest_experiment.name}")
    else:
        print("║ Latest experiment: None")

    if latest_report:
        print(f"║ Latest report:     {latest_report.name}")
    else:
        print("║ Latest report:     None")

    print("║")

    print("╠══════════════════════════════════════════════════════════╣")
    print("║ MODULES")
    print("║")

    for name, (status, count) in modules.items():
        print(f"║ {name.upper():18} {status:10} {count:5} files")

    print("║")

    print("╠══════════════════════════════════════════════════════════╣")
    print(f"║ LAB HEALTH: {overall}")
    print("╚══════════════════════════════════════════════════════════╝")
    print()


if __name__ == "__main__":
    main()
