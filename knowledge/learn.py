#!/usr/bin/env python3

import csv
import sys
from pathlib import Path

from knowledge import append, load_all, make_id, now


ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "data" / "experiment_runs.csv"


def read_runs():
    if not RUNS.exists():
        return []

    with RUNS.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def already_learned(run_id):
    return any(
        record.get("source", {}).get("run_id") == run_id
        for record in load_all()
    )


def learn_run(run):
    run_id = run.get("run_id", "")
    experiment = run.get("experiment", "")
    result = run.get("result", "")
    exit_status = run.get("exit_status", "")
    git_commit = run.get("git_commit", "")
    source_sha256 = run.get("source_sha256", "")

    if not run_id:
        return None

    if already_learned(run_id):
        return None

    if result == "SUCCESS":
        status = "passed"
        kind = "known_good"
        finding = (
            f"{experiment} completed successfully under the recorded "
            f"RichardLab environment and source state."
        )
        action = (
            f"Consider this run's configuration and source state as a "
            f"known successful baseline when testing related work."
        )
        reason = f"Experiment exited successfully with status {exit_status}."
        confidence = "medium"
    elif result == "FAILED":
        status = "failed"
        kind = "known_failure"
        finding = (
            f"{experiment} failed under the recorded RichardLab "
            f"environment and source state."
        )
        action = (
            "Review this failure before repeating the same experiment "
            "or configuration."
        )
        reason = f"Experiment exited with status {exit_status}."
        confidence = "medium"
    else:
        status = "inconclusive"
        kind = "observation"
        finding = (
            f"{experiment} produced result '{result}' and requires "
            "review before treating the outcome as established knowledge."
        )
        action = "Review the run and record a more specific finding."
        reason = "The runner result was not SUCCESS or FAILED."
        confidence = "low"

    record = {
        "knowledge_id": make_id(),
        "created_at": now(),
        "updated_at": now(),
        "kind": kind,
        "status": status,
        "subject": experiment,
        "finding": finding,
        "reason": reason,
        "action": action,
        "confidence": confidence,
        "tags": [
            "auto-learned",
            "experiment",
            status,
        ],
        "source": {
            "type": "experiment_run",
            "run_id": run_id,
            "experiment": experiment,
            "git_commit": git_commit,
            "source_sha256": source_sha256,
        },
        "evidence": [
            f"Run {run_id}",
            f"Experiment: {experiment}",
            f"Exit status: {exit_status}",
            f"Result: {result}",
        ],
        "supersedes": "",
        "related": [],
    }

    append(record)
    return record


def main():
    runs = read_runs()

    if not runs:
        print("No experiment runs found.")
        return 0

    learned = 0

    for run in runs:
        record = learn_run(run)

        if record:
            learned += 1
            print(
                f"LEARNED {record['knowledge_id']} "
                f"<- {record['source']['run_id']} "
                f"{record['status'].upper()}"
            )

    print()
    print(f"Runs inspected : {len(runs)}")
    print(f"New memories   : {learned}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
