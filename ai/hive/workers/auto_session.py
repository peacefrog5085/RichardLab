#!/usr/bin/env python3

import argparse
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
LEDGER_PATH = PROJECT_ROOT / "data" / "build_time_ledger.jsonl"

IGNORE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
}

IGNORE_FILES = {
    LEDGER_PATH,
}


def now():
    return datetime.now().astimezone()


def should_ignore(path):
    try:
        relative = path.relative_to(PROJECT_ROOT)
    except ValueError:
        return True

    if any(part in IGNORE_DIRS for part in relative.parts):
        return True

    if path == LEDGER_PATH:
        return True

    return False


def snapshot_files():
    result = {}

    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file() or should_ignore(path):
            continue

        try:
            stat = path.stat()
        except OSError:
            continue

        result[str(path.relative_to(PROJECT_ROOT))] = (
            stat.st_mtime_ns,
            stat.st_size,
        )

    return result


def git_state():
    try:
        result = subprocess.run(
            ["git", "-C", str(PROJECT_ROOT), "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            return {
                "available": False,
                "changed_files": 0,
            }

        lines = [
            line for line in result.stdout.splitlines()
            if line.strip()
        ]

        return {
            "available": True,
            "changed_files": len(lines),
        }

    except Exception as exc:
        return {
            "available": False,
            "changed_files": 0,
            "error": str(exc),
        }


def latest_commit():
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(PROJECT_ROOT),
                "log",
                "-1",
                "--format=%H|%aI|%s",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            return None

        parts = result.stdout.strip().split("|", 2)

        if len(parts) != 3:
            return None

        return {
            "commit": parts[0],
            "timestamp": parts[1],
            "message": parts[2],
        }

    except Exception:
        return None


def write_event(event):
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)

    with LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event) + "\n")


def record_activity_snapshot(
    subsystem="RichardLab",
    notes="automatic activity snapshot",
):
    timestamp = now()

    event = {
        "type": "activity_snapshot",
        "timestamp": timestamp.isoformat(),
        "subsystem": subsystem,
        "git": git_state(),
        "latest_commit": latest_commit(),
        "notes": notes,
    }

    write_event(event)

    return event


def watch(
    interval_seconds=60,
    idle_minutes=30,
    subsystem="RichardLab",
):
    print()
    print("RICHARDLAB AUTOMATIC SESSION WATCHER")
    print("====================================")
    print(f"Project: {PROJECT_ROOT}")
    print(f"Ledger:  {LEDGER_PATH}")
    print(f"Poll:    {interval_seconds}s")
    print(f"Idle:    {idle_minutes}m")
    print()
    print("Watching for development activity.")
    print("Press Ctrl+C to stop.")
    print()

    previous = snapshot_files()
    last_activity = None
    session_start = None
    session_events = 0

    try:
        while True:
            time.sleep(interval_seconds)

            current = snapshot_files()

            changed = {
                path
                for path, state in current.items()
                if previous.get(path) != state
            }

            changed.update(
                path
                for path in previous
                if path not in current
            )

            timestamp = now()

            if changed:
                if session_start is None:
                    session_start = timestamp

                last_activity = timestamp
                session_events += 1

                event = {
                    "type": "automatic_activity",
                    "timestamp": timestamp.isoformat(),
                    "subsystem": subsystem,
                    "changed_files": sorted(changed)[:100],
                    "changed_file_count": len(changed),
                    "git": git_state(),
                    "latest_commit": latest_commit(),
                    "confidence": "proxy",
                    "session_events": session_events,
                }

                write_event(event)

                print(
                    f"[{timestamp.isoformat()}] "
                    f"activity: {len(changed)} file(s)"
                )

            elif (
                session_start is not None
                and last_activity is not None
                and (
                    timestamp - last_activity
                ).total_seconds()
                >= idle_minutes * 60
            ):
                duration = (
                    last_activity - session_start
                ).total_seconds() / 60

                duration = max(1, round(duration))

                event = {
                    "type": "automatic_session_closed",
                    "timestamp": timestamp.isoformat(),
                    "subsystem": subsystem,
                    "start": session_start.isoformat(),
                    "end": last_activity.isoformat(),
                    "duration_minutes": duration,
                    "events": session_events,
                    "confidence": "proxy",
                    "reason": "idle_timeout",
                }

                write_event(event)

                print(
                    f"[{timestamp.isoformat()}] "
                    f"session closed: {duration} minute(s)"
                )

                session_start = None
                last_activity = None
                session_events = 0

            previous = current

    except KeyboardInterrupt:
        timestamp = now()

        if session_start is not None and last_activity is not None:
            duration = (
                last_activity - session_start
            ).total_seconds() / 60

            duration = max(1, round(duration))

            event = {
                "type": "automatic_session_closed",
                "timestamp": timestamp.isoformat(),
                "subsystem": subsystem,
                "start": session_start.isoformat(),
                "end": last_activity.isoformat(),
                "duration_minutes": duration,
                "events": session_events,
                "confidence": "proxy",
                "reason": "watcher_stopped",
            }

            write_event(event)

            print(
                f"\nSession closed: {duration} minute(s)"
            )

        print("\nWatcher stopped.")


def main():
    parser = argparse.ArgumentParser(
        description="RichardLab automatic development activity tracker."
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    snapshot_parser = subparsers.add_parser(
        "snapshot",
        help="Record one activity snapshot.",
    )

    snapshot_parser.add_argument(
        "--subsystem",
        default="RichardLab",
    )

    snapshot_parser.add_argument(
        "--notes",
        default="automatic activity snapshot",
    )

    watch_parser = subparsers.add_parser(
        "watch",
        help="Watch RichardLab for development activity.",
    )

    watch_parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Polling interval in seconds.",
    )

    watch_parser.add_argument(
        "--idle",
        type=int,
        default=30,
        help="Minutes of inactivity before closing a session.",
    )

    watch_parser.add_argument(
        "--subsystem",
        default="RichardLab",
    )

    args = parser.parse_args()

    if args.command == "snapshot":
        event = record_activity_snapshot(
            subsystem=args.subsystem,
            notes=args.notes,
        )
        print(json.dumps(event, indent=2))

    elif args.command == "watch":
        watch(
            interval_seconds=args.interval,
            idle_minutes=args.idle,
            subsystem=args.subsystem,
        )


if __name__ == "__main__":
    main()
