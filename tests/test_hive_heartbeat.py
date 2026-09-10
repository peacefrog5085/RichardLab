from dataclasses import replace

from ai.hive.core import HiveCore
from mission_control.heartbeat import HeartbeatResult, HeartbeatSnapshot


def make_snapshot():
    return HeartbeatSnapshot(
        timestamp="2026-01-01T00:00:00+00:00",
        system={
            "cpu": "NORMAL",
            "ram": "NORMAL",
            "disk": "NORMAL",
        },
        git={
            "branch": "master",
            "status": "CLEAN",
            "commit": "abc123 test",
        },
        projects=5,
        ready_projects=5,
        experiments=14,
        experiment_families=10,
        latest_experiment="experiment-011d.py",
        latest_report=None,
        knowledge_records=7,
        modules={
            "data": {"status": "READY", "files": 19},
            "experiments": {"status": "ACTIVE", "files": 24},
        },
    )


def test_hive_exposes_heartbeat(monkeypatch, tmp_path):
    snapshot = make_snapshot()
    expected = HeartbeatResult(
        pulse=7,
        snapshot=snapshot,
        previous=None,
        changes=[],
        attention="NONE",
        reason="No meaningful change detected.",
    )

    def fake_pulse(path):
        assert path == tmp_path / "heartbeat_state.json"
        return expected

    monkeypatch.setattr(
        "mission_control.heartbeat.pulse",
        fake_pulse,
    )

    hive = HiveCore.__new__(HiveCore)
    result = hive.heartbeat(tmp_path / "heartbeat_state.json")

    assert result is expected
    assert result.attention == "NONE"
    assert result.action_required is False


def test_hive_heartbeat_returns_state_change(monkeypatch, tmp_path):
    previous = make_snapshot()
    current = replace(previous, experiments=15)

    expected = HeartbeatResult(
        pulse=8,
        snapshot=current,
        previous=previous,
        changes=[],
        attention="REVIEW",
        reason="A meaningful lab state change requires review.",
    )

    monkeypatch.setattr(
        "mission_control.heartbeat.pulse",
        lambda path: expected,
    )

    hive = HiveCore.__new__(HiveCore)
    result = hive.heartbeat(tmp_path / "heartbeat_state.json")

    assert result.attention == "REVIEW"
    assert result.action_required is True
    assert result.snapshot.experiments == 15
