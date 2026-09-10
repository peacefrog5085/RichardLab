from mission_control.heartbeat import HeartbeatChange, HeartbeatResult, HeartbeatSnapshot
from ai.hive.context_selector import select_reasoning_context, packet_size


def make_heartbeat(
    *,
    attention="NONE",
    changes=None,
    experiments=14,
    latest_experiment="experiment-011d.py",
):
    snapshot = HeartbeatSnapshot(
        timestamp="2026-09-10T20:00:00+00:00",
        system={
            "cpu": "NORMAL",
            "ram": "NORMAL",
            "disk": "NORMAL",
        },
        git={
            "branch": "master",
            "status": "CLEAN",
            "commit": "test123",
        },
        projects=5,
        ready_projects=5,
        experiments=experiments,
        experiment_families=10,
        latest_experiment=latest_experiment,
        latest_report="experiment_011d_summary.txt",
        knowledge_records=7,
        modules={
            "ai": {"status": "READY", "files": 10},
            "experiments": {"status": "ACTIVE", "files": 24},
            "knowledge": {"status": "READY", "files": 4},
        },
    )

    return HeartbeatResult(
        pulse=9,
        snapshot=snapshot,
        previous=None,
        changes=changes or [],
        attention=attention,
        reason=(
            "A meaningful lab state change requires review."
            if attention == "REVIEW"
            else "No meaningful change detected."
        ),
    )


def make_evidence():
    return {
        "target": {
            "experiment": "experiment-011d.py",
        },
        "file_info": {
            "path": "experiments/experiment-011d.py",
        },
        "git": {
            "branch": "master",
            "status": "CLEAN",
        },
        "family": [],
        "similarities": [],
        "related_outputs": [],
        "runs": [],
        "artifacts": [],
        "system_metrics": [],
        "source_files": {
            "experiment-011d.py": "print('test')",
        },
    }


def test_heartbeat_is_included_in_reasoning_packet():
    heartbeat = make_heartbeat(attention="REVIEW")

    packet = select_reasoning_context(
        "What is happening with RichardLab right now?",
        make_evidence(),
        heartbeat=heartbeat,
    )

    assert packet["heartbeat"] is not None
    assert packet["heartbeat"]["attention"] == "REVIEW"
    assert packet["heartbeat"]["state"]["experiments"] == 14
    assert packet["heartbeat"]["state"]["latest_experiment"] == (
        "experiment-011d.py"
    )


def test_heartbeat_changes_are_preserved():
    heartbeat = make_heartbeat(
        attention="REVIEW",
        changes=[
            HeartbeatChange(
                category="experiments",
                field="value",
                previous=14,
                current=15,
                severity="REVIEW",
            )
        ],
    )

    packet = select_reasoning_context(
        "Why did the experiment count change?",
        make_evidence(),
        heartbeat=heartbeat,
    )

    assert packet["heartbeat"]["changes"] == [
        {
            "category": "experiments",
            "field": "value",
            "previous": 14,
            "current": 15,
            "severity": "REVIEW",
        }
    ]


def test_heartbeat_is_bounded_and_does_not_include_previous_snapshot():
    heartbeat = make_heartbeat(
        attention="REVIEW",
        changes=[
            HeartbeatChange(
                category="git",
                field="commit",
                previous="old",
                current="new",
                severity="REVIEW",
            )
        ],
    )

    packet = select_reasoning_context(
        "What is happening with RichardLab?",
        make_evidence(),
        heartbeat=heartbeat,
        max_chars=12000,
    )

    assert packet_size(packet) <= 12000
    assert "previous" not in packet["heartbeat"]
    assert "timestamp" not in packet["heartbeat"]


def test_selector_still_works_without_heartbeat():
    packet = select_reasoning_context(
        "What does experiment-011d.py do?",
        make_evidence(),
    )

    assert packet["heartbeat"] is None
