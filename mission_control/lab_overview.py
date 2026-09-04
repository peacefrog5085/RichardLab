#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime
import subprocess
import re
import psutil

LAB = Path.home() / "RichardLab"
PROJECTS = LAB / "projects"
EXPERIMENTS = LAB / "experiments"
REPORTS = LAB / "reports"


def git_info():
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

    return {
        "branch": run_git("branch", "--show-current") or "UNKNOWN",
        "status": "CLEAN" if not run_git("status", "--porcelain") else "CHANGES",
        "commit": run_git("log", "-1", "--pretty=format:%h %s") or "UNKNOWN",
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

        control = path / "control.sh"
        if control.is_file() and control.stat().st_mode & 0o111:
            ready += 1

    return discovered, ready


def experiment_info():
    if not EXPERIMENTS.exists():
        return 0, 0

    pattern = re.compile(r"experiment-(\d+)([a-z]?)\.(py|sh)$")
    files = [
        path for path in EXPERIMENTS.iterdir()
        if path.is_file() and pattern.match(path.name)
    ]

    families = {
        pattern.match(path.name).group(1)
        for path in files
    }

    return len(files), len(families)


def latest_file(directory):
    if not directory.exists():
        return None

    files = [path for path in directory.rglob("*") if path.is_file()]

    if not files:
        return None

    return max(files, key=lambda path: path.stat().st_mtime)


def system_info():
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage(str(LAB))

    return {
        "cpu": psutil.cpu_percent(interval=1),
        "ram": memory.percent,
        "disk": disk.percent,
    }


def main():
    git = git_info()
    projects, ready_projects = project_info()
    experiments, families = experiment_info()

    latest_experiment = latest_file(EXPERIMENTS)
    latest_report = latest_file(REPORTS)

    system = system_info()

    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║                  RICHARDLAB OVERVIEW                   ║")
    print("║                       v1.0                             ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print("║                                                        ║")

    print("║ REPOSITORY")
    print("║")
    print(f"║ Branch:      {git['branch']}")
    print(f"║ Working:     {git['status']}")
    print(f"║ Last commit: {git['commit']}")
    print("║")

    print("╠══════════════════════════════════════════════════════════╣")
    print("║ PROJECTS")
    print("║")
    print(f"║ Projects:    {projects}")
    print(f"║ Ready:       {ready_projects}")
    print("║")

    print("╠══════════════════════════════════════════════════════════╣")
    print("║ EXPERIMENTS")
    print("║")
    print(f"║ Experiments: {experiments}")
    print(f"║ Families:    {families}")
    print("║")

    print("╠══════════════════════════════════════════════════════════╣")
    print("║ ACTIVITY")
    print("║")

    if latest_experiment:
        modified = datetime.fromtimestamp(
            latest_experiment.stat().st_mtime
        ).strftime("%Y-%m-%d %H:%M:%S")

        print(f"║ Latest experiment: {latest_experiment.name}")
        print(f"║ Modified:          {modified}")
    else:
        print("║ Latest experiment: None")

    if latest_report:
        print(f"║ Latest report:     {latest_report.name}")
    else:
        print("║ Latest report:     None")

    print("║")

    print("╠══════════════════════════════════════════════════════════╣")
    print("║ SYSTEM")
    print("║")
    print(f"║ CPU:  {system['cpu']:5.1f}%")
    print(f"║ RAM:  {system['ram']:5.1f}%")
    print(f"║ DISK: {system['disk']:5.1f}%")
    print("║")

    print("╠══════════════════════════════════════════════════════════╣")
    print("║ OVERVIEW COMPLETE")
    print("╚══════════════════════════════════════════════════════════╝")
    print()


if __name__ == "__main__":
    main()
