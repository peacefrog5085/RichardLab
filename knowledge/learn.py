#!/usr/bin/env python3

import csv
from pathlib import Path

from knowledge import append, load_all, make_id, now


ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "data" / "experiment_runs.csv"
METRICS = ROOT / "data" / "experiment_metrics.csv"


def read_csv(path):
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_runs():
    return read_csv(RUNS)


def read_metrics():
    return read_csv(METRICS)


def metrics_for_run(run_id):
    rows = [
        row
        for row in read_metrics()
        if row.get("run_id") == run_id
    ]

    result = {}

    for row in rows:
        phase = row.get("phase", "").upper()

        if phase == "START":
            result["start"] = row
        elif phase == "END":
            result["end"] = row

    return result


def already_learned(run_id):
    return any(
        record.get("source", {}).get("run_id") == run_id
        for record in load_all()
    )


def environment_evidence(metrics):
    evidence = []

    start = metrics.get("start")
    end = metrics.get("end")

    if start:
        evidence.append(
            "START metrics: "
            f"CPU {start.get('cpu_percent')}%, "
            f"RAM {start.get('ram_percent')}%, "
            f"SWAP {start.get('swap_percent')}%, "
            f"DISK {start.get('disk_percent')}%"
        )

    if end:
        evidence.append(
            "END metrics: "
            f"CPU {end.get('cpu_percent')}%, "
            f"RAM {end.get('ram_percent')}%, "
            f"SWAP {end.get('swap_percent')}%, "
            f"DISK {end.get('disk_percent')}%"
        )

    return evidence


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

    metrics = metrics_for_run(run_id)

    evidence = [
        f"Run {run_id}",
        f"Experiment: {experiment}",
        f"Exit status: {exit_status}",
        f"Result: {result}",
    ]

    evidence.extend(environment_evidence(metrics))

    if result == "SUCCESS":
        status = "passed"
        kind = "known_good"
        finding = (
            f"{experiment} completed successfully under the recorded "
            f"RichardLab source and environment state."
        )
        action = (
            "Consider this run a known-good baseline when evaluating "
            "related experiments or configurations."
        )
        reason = f"Experiment exited successfully with status {exit_status}."
        confidence = "medium"

    elif result == "FAILED":
        status = "failed"
        kind = "known_failure"
        finding = (
            f"{experiment} failed under the recorded RichardLab source "
            f"and environment state."
        )
        action = (
            "Review this failure before repeating the same experiment "
            "or configuration."
        )
        reason = (
            f"Experiment exited with status {exit_status}. "
            "The learner records the failure but does not infer its cause."
        )
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
        "knowledge_version": 2,
        "knowledge_id": make_id(),
        "created_at": now(),
        "updated_at": now(),
        "kind": kind,
        "status": status,
        "subject": experiment,
        "finding": finding,
        "reason": reason,
        "action": action,
        "do_not": [],
        "conditions": [
            "RichardLab experiment execution",
            f"Git commit {git_commit}",
            f"source SHA256 {source_sha256}",
        ],
        "applies_when": [
            f"experiment is related to {experiment}",
        ],
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
        "evidence": evidence,
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
    skipped = 0

    for run in runs:
        if already_learned(run.get("run_id", "")):
            skipped += 1
            continue

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
    print(f"Already known  : {skipped}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
