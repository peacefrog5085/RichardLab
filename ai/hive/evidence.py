#!/usr/bin/env python3

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mission_control import experiment_inspector
from mission_control import experiment_registry


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"


@dataclass
class EvidenceBundle:
    target: str
    file_info: dict[str, Any] = field(default_factory=dict)
    family: list[dict[str, Any]] = field(default_factory=list)
    similarities: list[dict[str, Any]] = field(default_factory=list)
    git: dict[str, Any] = field(default_factory=dict)
    related_outputs: list[dict[str, Any]] = field(default_factory=list)
    runs: list[dict[str, Any]] = field(default_factory=list)
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    system_metrics: list[dict[str, Any]] = field(default_factory=list)
    source_files: dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "file_info": self.file_info,
            "family": self.family,
            "similarities": self.similarities,
            "git": self.git,
            "related_outputs": self.related_outputs,
            "runs": self.runs,
            "artifacts": self.artifacts,
            "system_metrics": self.system_metrics,
            "source_files": self.source_files,
        }


def _path_info(path: Path) -> dict[str, Any]:
    stat = path.stat()

    return {
        "path": str(path.relative_to(PROJECT_ROOT)),
        "name": path.name,
        "size_bytes": stat.st_size,
        "modified_time": stat.st_mtime,
    }


def _read_csv(filename: str) -> list[dict[str, str]]:
    path = DATA_DIR / filename

    if not path.exists():
        return []

    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _find_experiment(name: str) -> Path:
    for path in experiment_registry.experiment_files():
        if path.name == name:
            return path

    raise ValueError(f"Experiment not found: {name}")


def _read_source(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return "<SOURCE_NOT_UTF8>"
    except OSError as exc:
        return f"<SOURCE_READ_ERROR: {exc}>"


def collect_experiment_evidence(experiment_name: str) -> EvidenceBundle:
    target = _find_experiment(experiment_name)

    info = experiment_inspector.file_info(target)
    family_paths = experiment_inspector.find_family(target)
    output_paths = experiment_inspector.find_related_outputs(target)
    git = experiment_inspector.git_history(target)

    family = [
        {
            "name": path.name,
            "path": str(path.relative_to(PROJECT_ROOT)),
        }
        for path in family_paths
    ]

    similarities = []

    for left, right in zip(family_paths, family_paths[1:]):
        score = experiment_inspector.source_similarity(left, right)

        similarities.append(
            {
                "from": left.name,
                "to": right.name,
                "score": score,
            }
        )

    related_outputs = [
        _path_info(path)
        for path in output_paths
        if path.exists()
    ]

    experiment_runs = [
        row
        for row in _read_csv("experiment_runs.csv")
        if row.get("experiment") == experiment_name
    ]

    experiment_artifacts = [
        row
        for row in _read_csv("experiment_artifacts.csv")
        if row.get("experiment") == experiment_name
    ]

    system_metrics = _read_csv("system_metrics.csv")

    source_files = {
        path.name: _read_source(path)
        for path in family_paths
    }

    return EvidenceBundle(
        target=experiment_name,
        file_info=info,
        family=family,
        similarities=similarities,
        git=git,
        related_outputs=related_outputs,
        runs=experiment_runs,
        artifacts=experiment_artifacts,
        system_metrics=system_metrics,
        source_files=source_files,
    )


def main() -> None:
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Collect structured RichardLab evidence for an experiment."
    )
    parser.add_argument("experiment")
    args = parser.parse_args()

    bundle = collect_experiment_evidence(args.experiment)
    print(json.dumps(bundle.as_dict(), indent=2, default=str))


if __name__ == "__main__":
    main()
