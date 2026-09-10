#!/usr/bin/env python3

"""
RichardLab Heartbeat Substrate

A quiet, deterministic continuity layer for RichardLab.

The heartbeat:
    - observes existing lab state
    - records a compact state snapshot
    - compares the current state with the previous pulse
    - identifies meaningful changes
    - assigns an attention level
    - does NOT call AI by itself
    - does NOT duplicate the knowledge system

Architecture:

    existing sensors
          ↓
    HeartbeatSnapshot
          ↓
    HeartbeatDiff
          ↓
    HeartbeatAttention
          ↓
    Hive when reasoning is actually warranted
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mission_control.lab_health import (
    experiment_family_count,
    experiment_files,
    git_info,
    module_status,
    project_info,
    system_health,
)
from knowledge import load_all


LAB = Path.home() / "RichardLab"
STATE_FILE = LAB / "data" / "heartbeat_state.json"

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


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class HeartbeatSnapshot:
    timestamp: str
    system: dict[str, Any]
    git: dict[str, Any]
    projects: int
    ready_projects: int
    experiments: int
    experiment_families: int
    latest_experiment: str | None
    latest_report: str | None
    knowledge_records: int
    modules: dict[str, dict[str, Any]]

    def comparable(self) -> dict[str, Any]:
        """
        Return state fields used for change detection.

        Timestamp is intentionally excluded.
        """
        return {
            "system": {
                "cpu": self.system.get("cpu"),
                "ram": self.system.get("ram"),
                "disk": self.system.get("disk"),
            },
            "git": self.git,
            "projects": self.projects,
            "ready_projects": self.ready_projects,
            "experiments": self.experiments,
            "experiment_families": self.experiment_families,
            "latest_experiment": self.latest_experiment,
            "latest_report": self.latest_report,
            "knowledge_records": self.knowledge_records,
            "modules": self.modules,
        }


@dataclass(frozen=True)
class HeartbeatChange:
    category: str
    field: str
    previous: Any
    current: Any
    severity: str = "WATCH"


@dataclass(frozen=True)
class HeartbeatResult:
    pulse: int
    snapshot: HeartbeatSnapshot
    previous: HeartbeatSnapshot | None
    changes: list[HeartbeatChange] = field(default_factory=list)
    attention: str = "NONE"
    reason: str = "No meaningful change detected."

    @property
    def action_required(self) -> bool:
        return self.attention in {"REVIEW", "ACTION"}

    def as_dict(self) -> dict[str, Any]:
        return {
            "pulse": self.pulse,
            "snapshot": asdict(self.snapshot),
            "previous": asdict(self.previous) if self.previous else None,
            "changes": [asdict(change) for change in self.changes],
            "attention": self.attention,
            "reason": self.reason,
            "action_required": self.action_required,
        }


def _latest_name(
    path: Path,
    extensions: tuple[str, ...] | None = None,
) -> str | None:
    if not path.exists():
        return None

    files = [p for p in path.rglob("*") if p.is_file()]

    if extensions is not None:
        files = [p for p in files if p.suffix in extensions]

    if not files:
        return None

    return max(files, key=lambda p: p.stat().st_mtime).name


def collect_snapshot() -> HeartbeatSnapshot:
    """
    Collect one deterministic snapshot from existing RichardLab APIs.
    """
    system = system_health()
    git = git_info()
    projects, ready_projects = project_info()

    experiments = experiment_files()

    modules: dict[str, dict[str, Any]] = {}

    for name in MODULES:
        status, count = module_status(name)

        # Heartbeat runtime state is substrate state, not a lab change.
        # Do not let the heartbeat observe its own state file.
        if name == "data":
            heartbeat_state = LAB / "data" / "heartbeat_state.json"
            if heartbeat_state.exists():
                count -= 1

        modules[name] = {
            "status": status,
            "files": count,
        }

    return HeartbeatSnapshot(
        timestamp=utc_now(),
        system=system,
        git=git,
        projects=projects,
        ready_projects=ready_projects,
        experiments=len(experiments),
        experiment_families=experiment_family_count(experiments),
        latest_experiment=_latest_name(
            LAB / "experiments",
            (".py", ".sh"),
        ),
        latest_report=_latest_name(
            LAB / "reports",
            (".md", ".txt", ".json", ".csv"),
        ),
        knowledge_records=len(load_all()),
        modules=modules,
    )


def _load_state(path: Path = STATE_FILE) -> tuple[int, HeartbeatSnapshot | None]:
    if not path.exists():
        return 0, None

    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return 0, None

    pulse = int(data.get("pulse", 0))

    snapshot_data = data.get("snapshot")
    if not snapshot_data:
        return pulse, None

    try:
        snapshot = HeartbeatSnapshot(**snapshot_data)
    except (TypeError, ValueError):
        return pulse, None

    return pulse, snapshot


def _save_state(
    pulse: int,
    snapshot: HeartbeatSnapshot,
    path: Path = STATE_FILE,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "pulse": pulse,
        "snapshot": asdict(snapshot),
    }

    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True))
    temporary.replace(path)


def detect_changes(
    previous: HeartbeatSnapshot | None,
    current: HeartbeatSnapshot,
) -> list[HeartbeatChange]:
    """
    Compare meaningful state only.

    Volatile measurements such as exact CPU/RAM percentages are not
    treated as changes. Their health levels are.
    """
    if previous is None:
        return []

    changes: list[HeartbeatChange] = []

    previous_state = previous.comparable()
    current_state = current.comparable()

    def compare_dict(category: str, field: str, severity: str = "WATCH") -> None:
        old = previous_state[category].get(field)
        new = current_state[category].get(field)

        if old != new:
            changes.append(
                HeartbeatChange(
                    category=category,
                    field=field,
                    previous=old,
                    current=new,
                    severity=severity,
                )
            )

    def compare_scalar(field: str, severity: str = "WATCH") -> None:
        old = previous_state.get(field)
        new = current_state.get(field)

        if old != new:
            changes.append(
                HeartbeatChange(
                    category=field,
                    field="value",
                    previous=old,
                    current=new,
                    severity=severity,
                )
            )

    compare_dict("system", "cpu", "WATCH")
    compare_dict("system", "ram", "WATCH")
    compare_dict("system", "disk", "WATCH")

    compare_dict("git", "branch", "REVIEW")
    compare_dict("git", "status", "WATCH")
    compare_dict("git", "commit", "REVIEW")

    compare_scalar("projects", "WATCH")
    compare_scalar("ready_projects", "WATCH")
    compare_scalar("experiments", "REVIEW")
    compare_scalar("experiment_families", "REVIEW")
    compare_scalar("latest_experiment", "REVIEW")
    compare_scalar("latest_report", "WATCH")
    compare_scalar("knowledge_records", "WATCH")

    previous_modules = previous_state["modules"]
    current_modules = current_state["modules"]

    for name in sorted(set(previous_modules) | set(current_modules)):
        old = previous_modules.get(name)
        new = current_modules.get(name)

        if old != new:
            changes.append(
                HeartbeatChange(
                    category="module",
                    field=name,
                    previous=old,
                    current=new,
                    severity="REVIEW",
                )
            )

    return changes


def determine_attention(
    snapshot: HeartbeatSnapshot,
    changes: list[HeartbeatChange],
) -> tuple[str, str]:
    """
    Convert observed state into attention.

    This is deterministic. AI reasoning happens elsewhere.
    """
    critical_system = any(
        snapshot.system.get(key) == "CRITICAL"
        for key in ("cpu", "ram", "disk")
    )

    missing_modules = any(
        info.get("status") == "MISSING"
        for info in snapshot.modules.values()
    )

    if critical_system:
        return "ACTION", "Critical system resource condition detected."

    if missing_modules:
        return "REVIEW", "One or more RichardLab modules are missing."

    if any(change.severity == "REVIEW" for change in changes):
        return "REVIEW", "A meaningful lab state change requires review."

    if changes:
        return "WATCH", "RichardLab changed since the previous heartbeat."

    return "NONE", "No meaningful change detected."


def pulse(path: Path = STATE_FILE) -> HeartbeatResult:
    """
    Execute exactly one heartbeat.

    The pulse:
        1. collects current state
        2. loads previous state
        3. detects meaningful changes
        4. determines attention
        5. persists current state
    """
    previous_pulse, previous = _load_state(path)

    current = collect_snapshot()
    changes = detect_changes(previous, current)
    attention, reason = determine_attention(current, changes)

    current_pulse = previous_pulse + 1

    _save_state(
        current_pulse,
        current,
        path,
    )

    return HeartbeatResult(
        pulse=current_pulse,
        snapshot=current,
        previous=previous,
        changes=changes,
        attention=attention,
        reason=reason,
    )


def format_result(result: HeartbeatResult) -> str:
    s = result.snapshot
    lines = [
        "",
        "╔══════════════════════════════════════════════════════════╗",
        "║                 RICHARDLAB HEARTBEAT                   ║",
        "╠══════════════════════════════════════════════════════════╣",
        f"║ Pulse:        {result.pulse:<40}║",
        f"║ Time:         {s.timestamp:<40}║",
        f"║ Attention:    {result.attention:<40}║",
        "║                                                        ║",
        "║ SYSTEM                                                 ║",
        f"║ CPU:          {s.system['cpu']:<10} ({s.system['cpu_value']:5.1f}%)"
        "                       ║",
        f"║ RAM:          {s.system['ram']:<10} ({s.system['ram_value']:5.1f}%)"
        "                       ║",
        f"║ DISK:         {s.system['disk']:<10} ({s.system['disk_value']:5.1f}%)"
        "                       ║",
        "║                                                        ║",
        "║ CONTINUITY                                             ║",
        f"║ Git:          {s.git['status']:<40}║",
        f"║ Commit:       {s.git['commit'][:40]:<40}║",
        f"║ Projects:     {s.projects}/{s.ready_projects:<38}║",
        f"║ Experiments:  {s.experiments:<40}║",
        f"║ Families:     {s.experiment_families:<40}║",
        f"║ Knowledge:    {s.knowledge_records:<40}║",
        "║                                                        ║",
        f"║ Changes:      {len(result.changes):<40}║",
        f"║ Decision:     {result.reason[:40]:<40}║",
        "╚══════════════════════════════════════════════════════════╝",
        "",
    ]

    if result.changes:
        lines.append("CHANGES:")
        for change in result.changes:
            lines.append(
                f"  [{change.severity}] "
                f"{change.category}.{change.field}: "
                f"{change.previous!r} -> {change.current!r}"
            )

    return "\n".join(lines)


def main() -> int:
    result = pulse()
    print(format_result(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
