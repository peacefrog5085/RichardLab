#!/usr/bin/env python3

import json
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]

def _parse_timestamp(value):
    """
    Parse a ledger timestamp and normalize it to a timezone-aware datetime.

    Historical experiment CSV entries may contain naive timestamps such as
    '2026-09-04 15:09:23'. Those are interpreted as local time.
    """
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        if not text:
            raise ValueError("Empty timestamp")

        dt = datetime.fromisoformat(text)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.now().astimezone().tzinfo)

    return dt.astimezone()


DATA_DIR = PROJECT_ROOT / "data"
LEDGER_PATH = DATA_DIR / "build_time_ledger.jsonl"


def _now():
    return datetime.now().astimezone()


def _git_commits():
    command = [
        "git", "-C", str(PROJECT_ROOT),
        "log", "--all",
        "--format=%H|%aI|%s",
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        return []

    if result.returncode != 0:
        return []

    commits = []

    for line in result.stdout.splitlines():
        parts = line.split("|", 2)

        if len(parts) != 3:
            continue

        commit, timestamp, message = parts

        try:
            dt = _parse_timestamp(timestamp)
        except ValueError:
            continue

        commits.append({
            "commit": commit,
            "timestamp": dt.isoformat(),
            "message": message,
        })

    commits.sort(key=lambda item: item["timestamp"])

    return commits


def _git_windows(commits, gap_minutes=120, max_window_minutes=180):
    if not commits:
        return []

    windows = []

    start = _parse_timestamp(
        commits[0]["timestamp"]
    )
    end = start
    items = [commits[0]]

    for commit in commits[1:]:
        current = _parse_timestamp(
            commit["timestamp"]
        )

        gap = (
            current - end
        ).total_seconds() / 60

        if gap <= gap_minutes:
            end = current
            items.append(commit)
            continue

        raw_minutes = (
            end - start
        ).total_seconds() / 60

        duration = max(
            1,
            min(
                round(raw_minutes),
                max_window_minutes,
            ),
        )

        windows.append({
            "start": start.isoformat(),
            "end": end.isoformat(),
            "duration_minutes": duration,
            "commit_count": len(items),
            "commits": items,
        })

        start = current
        end = current
        items = [commit]

    raw_minutes = (
        end - start
    ).total_seconds() / 60

    duration = max(
        1,
        min(
            round(raw_minutes),
            max_window_minutes,
        ),
    )

    windows.append({
        "start": start.isoformat(),
        "end": end.isoformat(),
        "duration_minutes": duration,
        "commit_count": len(items),
        "commits": items,
    })

    return windows


def _experiment_activity():
    path = DATA_DIR / "experiment_runs.csv"

    if not path.exists():
        return []

    import csv

    try:
        with path.open(
            newline="",
            encoding="utf-8",
        ) as handle:
            rows = list(csv.DictReader(handle))
    except Exception:
        return []

    activity = []

    for row in rows:
        try:
            start = _parse_timestamp(
                row["start_time"]
            )
            end = _parse_timestamp(
                row["end_time"]
            )

            seconds = max(
                0,
                (end - start).total_seconds(),
            )

            activity.append({
                "experiment": row.get(
                    "experiment"
                ),
                "run_id": row.get(
                    "run_id"
                ),
                "start": start.isoformat(),
                "end": end.isoformat(),
                "duration_seconds":
                    round(seconds),
                "duration_minutes":
                    round(seconds / 60, 2),
                "exit_status":
                    row.get("exit_status"),
            })

        except (
            KeyError,
            ValueError,
            TypeError,
        ):
            continue

    return activity


def _shell_history_activity():
    """
    Inspect available Bash history metadata.

    Only timestamps already present in shell history are used.
    No shell history is modified.
    """

    history_file = os.environ.get(
        "HISTFILE",
        str(Path.home() / ".bash_history"),
    )

    path = Path(history_file)

    if not path.exists():
        return {
            "available": False,
            "reason": "Bash history file not found.",
            "events": [],
            "windows": [],
        }

    try:
        lines = path.read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines()
    except OSError as exc:
        return {
            "available": False,
            "reason": str(exc),
            "events": [],
            "windows": [],
        }

    events = []

    current_timestamp = None

    for line in lines:
        if line.startswith("#") and line[1:].isdigit():
            try:
                current_timestamp = datetime.fromtimestamp(
                    int(line[1:])
                ).astimezone()
            except (ValueError, OSError):
                current_timestamp = None

            continue

        if current_timestamp is None:
            continue

        lowered = line.lower()

        if (
            "richardlab" in lowered
            or "cd ~/richardlab" in lowered
            or "cd /home/rich/richardlab" in lowered
        ):
            events.append({
                "timestamp":
                    current_timestamp.isoformat(),
                "command": line[:500],
            })

    events.sort(
        key=lambda item: item["timestamp"]
    )

    windows = []

    if events:
        start = _parse_timestamp(
            events[0]["timestamp"]
        )
        end = start
        items = [events[0]]

        for event in events[1:]:
            current = _parse_timestamp(
                event["timestamp"]
            )

            gap = (
                current - end
            ).total_seconds() / 60

            if gap <= 120:
                end = current
                items.append(event)
            else:
                duration = max(
                    1,
                    min(
                        round(
                            (
                                end - start
                            ).total_seconds()
                            / 60
                        ),
                        180,
                    ),
                )

                windows.append({
                    "start":
                        start.isoformat(),
                    "end":
                        end.isoformat(),
                    "duration_minutes":
                        duration,
                    "command_count":
                        len(items),
                })

                start = current
                end = current
                items = [event]

        duration = max(
            1,
            min(
                round(
                    (
                        end - start
                    ).total_seconds()
                    / 60
                ),
                180,
            ),
        )

        windows.append({
            "start": start.isoformat(),
            "end": end.isoformat(),
            "duration_minutes": duration,
            "command_count": len(items),
        })

    return {
        "available": True,
        "event_count": len(events),
        "events": events,
        "windows": windows,
    }



def _file_activity_windows(events, gap_minutes=30, max_window_minutes=120):
    """
    Cluster filesystem modification events into likely development periods.

    This is deliberately conservative:
    - events must occur within gap_minutes of the previous event
    - each reconstructed window is capped
    - the result is evidence, not proof of hands-on work
    """

    if not events:
        return []

    windows = []

    start = _parse_timestamp(
        events[0]["timestamp"]
    )
    end = start
    items = [events[0]]

    for event in events[1:]:
        current = _parse_timestamp(
            event["timestamp"]
        )

        gap = (
            current - end
        ).total_seconds() / 60

        if gap <= gap_minutes:
            end = current
            items.append(event)
            continue

        raw_minutes = (
            end - start
        ).total_seconds() / 60

        duration = max(
            1,
            min(
                round(raw_minutes),
                max_window_minutes,
            ),
        )

        windows.append({
            "start": start.isoformat(),
            "end": end.isoformat(),
            "duration_minutes": duration,
            "file_event_count": len(items),
            "files": [
                item["path"]
                for item in items
            ],
        })

        start = current
        end = current
        items = [event]

    raw_minutes = (
        end - start
    ).total_seconds() / 60

    duration = max(
        1,
        min(
            round(raw_minutes),
            max_window_minutes,
        ),
    )

    windows.append({
        "start": start.isoformat(),
        "end": end.isoformat(),
        "duration_minutes": duration,
        "file_event_count": len(items),
        "files": [
            item["path"]
            for item in items
        ],
    })

    return windows


def _file_activity():
    try:
        result = subprocess.run(
            [
                "git", "-C",
                str(PROJECT_ROOT),
                "ls-files",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        return []

    if result.returncode != 0:
        return []

    events = []

    for relative in result.stdout.splitlines():
        path = PROJECT_ROOT / relative

        try:
            timestamp = datetime.fromtimestamp(
                path.stat().st_mtime
            ).astimezone()

            events.append({
                "path": relative,
                "timestamp":
                    timestamp.isoformat(),
            })

        except OSError:
            continue

    events.sort(
        key=lambda item: item["timestamp"]
    )

    return events


def _session_minutes(sessions):
    total = 0

    for session in sessions:
        try:
            start = _parse_timestamp(
                session["start"]
            )
            end = _parse_timestamp(
                session["end"]
            )

            total += max(
                0,
                (
                    end - start
                ).total_seconds() / 60,
            )

        except (
            KeyError,
            ValueError,
            TypeError,
        ):
            continue

    return round(total)


def _format_minutes(minutes):
    minutes = round(minutes)

    hours = minutes // 60
    remainder = minutes % 60

    return f"{hours}h {remainder:02d}m"


def _interval_from_window(
    window,
    source,
    use_cap=True,
):
    start = datetime.fromisoformat(
        window["start"]
    )

    if use_cap:
        end = start + timedelta(
            minutes=window[
                "duration_minutes"
            ]
        )
    else:
        end = datetime.fromisoformat(
            window["end"]
        )

    return (
        start,
        end,
        source,
    )


def _merge_intervals(intervals):
    if not intervals:
        return []

    normalized = []

    for start, end, source in intervals:
        if end < start:
            start, end = end, start

        normalized.append(
            (start, end, source)
        )

    normalized.sort(
        key=lambda item: item[0]
    )

    merged = []

    current_start = normalized[0][0]
    current_end = normalized[0][1]
    sources = {normalized[0][2]}

    for start, end, source in normalized[1:]:

        if start <= current_end:
            current_end = max(
                current_end,
                end,
            )
            sources.add(source)

        else:
            merged.append({
                "start":
                    current_start.isoformat(),
                "end":
                    current_end.isoformat(),
                "sources":
                    sorted(sources),
                "duration_minutes":
                    round(
                        (
                            current_end
                            - current_start
                        ).total_seconds()
                        / 60
                    ),
            })

            current_start = start
            current_end = end
            sources = {source}

    merged.append({
        "start":
            current_start.isoformat(),
        "end":
            current_end.isoformat(),
        "sources":
            sorted(sources),
        "duration_minutes":
            round(
                (
                    current_end
                    - current_start
                ).total_seconds()
                / 60
            ),
    })

    return merged


def record_session(
    start_time,
    end_time,
    subsystem="RichardLab",
    notes="",
):
    entry = {
        "type": "session",
        "start": start_time,
        "end": end_time,
        "subsystem": subsystem,
        "notes": notes,
        "recorded_at":
            _now().isoformat(),
    }

    LEDGER_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with LEDGER_PATH.open(
        "a",
        encoding="utf-8",
    ) as handle:
        handle.write(
            json.dumps(entry)
            + "\n"
        )

    return entry


def get_recorded_sessions():
    if not LEDGER_PATH.exists():
        return []

    sessions = []

    with LEDGER_PATH.open(
        encoding="utf-8"
    ) as handle:

        for line in handle:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            if entry.get("type") == "session":
                sessions.append(entry)

    return sessions


def build_time_report():

    sessions = (
        get_recorded_sessions()
    )

    commits = _git_commits()

    git_windows = _git_windows(
        commits
    )

    experiment_runs = (
        _experiment_activity()
    )

    file_events = (
        _file_activity()
    )

    file_windows = (
        _file_activity_windows(
            file_events
        )
    )

    shell_activity = (
        _shell_history_activity()
    )

    recorded_minutes = (
        _session_minutes(
            sessions
        )
    )

    git_minutes = sum(
        window[
            "duration_minutes"
        ]
        for window in git_windows
    )

    experiment_minutes = sum(
        item[
            "duration_minutes"
        ]
        for item in experiment_runs
    )

    shell_minutes = sum(
        window[
            "duration_minutes"
        ]
        for window in
        shell_activity[
            "windows"
        ]
    )

    file_minutes = sum(
        window[
            "duration_minutes"
        ]
        for window in file_windows
    )

    intervals = []

    # IMPORTANT:
    # Use the capped duration when reconstructing the actual
    # Git evidence interval. This keeps the overlap calculation
    # consistent with the reported Git total.

    for window in git_windows:
        intervals.append(
            _interval_from_window(
                window,
                "git",
                use_cap=True,
            )
        )

    for run in experiment_runs:
        intervals.append((
            datetime.fromisoformat(
                run["start"]
            ),
            datetime.fromisoformat(
                run["end"]
            ),
            "experiment",
        ))

    for window in shell_activity[
        "windows"
    ]:
        intervals.append(
            _interval_from_window(
                window,
                "shell",
                use_cap=True,
            )
        )

    for window in file_windows:
        intervals.append(
            _interval_from_window(
                window,
                "filesystem",
                use_cap=True,
            )
        )

    merged = _merge_intervals(
        intervals
    )

    merged_minutes = sum(
        item[
            "duration_minutes"
        ]
        for item in merged
    )

    return {
        "project": "RichardLab",

        "generated_at":
            _now().isoformat(),

        "confirmed": {
            "session_count":
                len(sessions),
            "minutes":
                recorded_minutes,
            "formatted":
                _format_minutes(
                    recorded_minutes
                ),
        },

        "reconstructed": {

            "git": {
                "commit_count":
                    len(commits),
                "activity_window_count":
                    len(git_windows),
                "minutes":
                    git_minutes,
                "formatted":
                    _format_minutes(
                        git_minutes
                    ),
                "windows":
                    git_windows,
            },

            "experiments": {
                "run_count":
                    len(experiment_runs),
                "minutes":
                    experiment_minutes,
                "formatted":
                    _format_minutes(
                        experiment_minutes
                    ),
                "runs":
                    experiment_runs,
            },

            "shell_history": {
                "available":
                    shell_activity[
                        "available"
                    ],
                "event_count":
                    shell_activity.get(
                        "event_count",
                        0,
                    ),
                "minutes":
                    shell_minutes,
                "formatted":
                    _format_minutes(
                        shell_minutes
                    ),
                "windows":
                    shell_activity[
                        "windows"
                    ],
            },

            "file_activity": {
                "tracked_file_count":
                    len(file_events),
                "events":
                    file_events,
                "window_count":
                    len(file_windows),
                "reconstructed_minutes":
                    file_minutes,
                "reconstructed_formatted":
                    _format_minutes(
                        file_minutes
                    ),
                "windows":
                    file_windows,
                "note":
                    "Filesystem modification events are clustered conservatively into evidence windows. They are not proof of continuous hands-on work.",
            },

            "overlap_adjusted": {
                "minutes":
                    merged_minutes,
                "formatted":
                    _format_minutes(
                        merged_minutes
                    ),
                "intervals":
                    merged,
            },
        },

        "historical_estimate": {
            "available": False,
            "minutes": None,
            "formatted": None,
            "note":
                "Historical estimates remain separate until supported by explicit evidence.",
        },

        "methodology": {
            "confirmed":
                "Explicitly recorded start/end sessions.",

            "git":
                "Git commits are grouped into activity windows. Each reconstructed window is capped at 180 minutes.",

            "experiments":
                "Experiment runtime comes from experiment_runs.csv.",

            "shell":
                "Only timestamped Bash history entries referencing RichardLab are considered.",

            "files":
                "Tracked-file modification timestamps are clustered into conservative evidence windows with a 30-minute event gap and 120-minute maximum window.",

            "overlap":
                "Git, experiment, and shell-history intervals are merged before calculating the overlap-adjusted reconstruction.",

            "warning":
                "Reconstructed time is evidence-based but cannot prove continuous hands-on work.",
        },
    }


def get_build_time():
    return build_time_report()


def register_tools():
    from ...tool_registry import register

    register(
        name="get_build_time",
        description=(
            "Report RichardLab build time using confirmed sessions "
            "and evidence-based reconstruction from Git activity, "
            "experiment runs, shell history, file activity, and "
            "overlap analysis."
        ),
        function=get_build_time,
        category="provenance",
        safety="read_only",
    )


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "RichardLab build-time forensic ledger."
        )
    )

    parser.add_argument(
        "command",
        choices=[
            "report",
            "start",
            "stop",
        ],
        nargs="?",
        default="report",
    )

    parser.add_argument(
        "--subsystem",
        default="RichardLab",
    )

    parser.add_argument(
        "--notes",
        default="",
    )

    parser.add_argument(
        "--start",
    )

    parser.add_argument(
        "--end",
    )

    args = parser.parse_args()

    if args.command == "report":
        print(
            json.dumps(
                get_build_time(),
                indent=2,
            )
        )
        return

    if args.command == "start":
        start = (
            args.start
            or _now().isoformat()
        )

        print(
            json.dumps(
                {
                    "action": "start",
                    "start": start,
                    "subsystem":
                        args.subsystem,
                    "notes":
                        args.notes,
                },
                indent=2,
            )
        )

        return

    if args.command == "stop":

        if not args.start:
            parser.error(
                "--start is required for stop"
            )

        end = (
            args.end
            or _now().isoformat()
        )

        entry = record_session(
            args.start,
            end,
            subsystem=args.subsystem,
            notes=args.notes,
        )

        print(
            json.dumps(
                entry,
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
