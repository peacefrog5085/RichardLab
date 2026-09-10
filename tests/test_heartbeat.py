from dataclasses import replace
from pathlib import Path

from mission_control.heartbeat import (
    HeartbeatSnapshot,
    detect_changes,
    determine_attention,
    pulse,
)


def make_snapshot(**overrides):
    base = HeartbeatSnapshot(
        timestamp="2026-09-10T19:00:00+00:00",
        system={
            "cpu": "NORMAL",
            "ram": "NORMAL",
            "disk": "NORMAL",
            "cpu_value": 5.0,
            "ram_value": 28.0,
            "disk_value": 14.7,
        },
        git={
            "branch": "master",
            "status": "CLEAN",
            "commit": "abc123 test",
        },
        projects=5,
        ready_projects=5,
        experiments=14,
        experiment_families=11,
        latest_experiment="experiment-011d.py",
        latest_report="experiment_011d_summary.txt",
        knowledge_records=7,
        modules={
            "ai": {"status": "READY", "files": 10},
            "knowledge": {"status": "READY", "files": 4},
        },
    )

    return replace(base, **overrides)


def test_first_pulse_creates_baseline(tmp_path, monkeypatch):
    state_file = tmp_path / "heartbeat_state.json"

    result = pulse(state_file)

    assert result.pulse == 1
    assert result.previous is None
    assert result.changes == []
    assert result.attention == "NONE"
    assert state_file.exists()


def test_second_unchanged_pulse_is_quiet(tmp_path):
    state_file = tmp_path / "heartbeat_state.json"

    first = pulse(state_file)
    second = pulse(state_file)

    assert first.pulse == 1
    assert second.pulse == 2
    assert second.previous is not None
    assert second.changes == []
    assert second.attention == "NONE"


def test_experiment_change_requires_review():
    previous = make_snapshot()
    current = replace(previous, experiments=15)

    changes = detect_changes(previous, current)
    attention, _ = determine_attention(current, changes)

    assert any(change.field == "value" for change in changes)
    assert attention == "REVIEW"


def test_git_commit_change_requires_review():
    previous = make_snapshot()
    current = replace(
        previous,
        git={
            "branch": "master",
            "status": "CLEAN",
            "commit": "def456 new",
        },
    )

    changes = detect_changes(previous, current)

    assert any(
        change.category == "git"
        and change.field == "commit"
        for change in changes
    )


def test_critical_system_state_requires_action():
    current = make_snapshot(
        system={
            "cpu": "CRITICAL",
            "ram": "NORMAL",
            "disk": "NORMAL",
            "cpu_value": 95.0,
            "ram_value": 28.0,
            "disk_value": 14.7,
        }
    )

    attention, reason = determine_attention(current, [])

    assert attention == "ACTION"
    assert "Critical" in reason


def test_missing_module_requires_review():
    current = make_snapshot(
        modules={
            "ai": {"status": "MISSING", "files": 0},
            "knowledge": {"status": "READY", "files": 4},
        }
    )

    attention, reason = determine_attention(current, [])

    assert attention == "REVIEW"
    assert "missing" in reason.lower()
