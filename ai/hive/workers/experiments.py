#!/usr/bin/env python3

from mission_control import experiment_family_map
from mission_control import experiment_inspector
from mission_control import experiment_registry

from ...hive.evidence import collect_experiment_evidence
from ...tool_registry import register


def list_experiments():
    experiments = experiment_registry.experiment_files()

    return [
        {
            "name": path.name,
            "type": experiment_registry.experiment_type(path),
            "family": experiment_family_map.experiment_key(path.name),
        }
        for path in experiments
    ]


def inspect_experiment(experiment_name: str):
    experiments = experiment_registry.experiment_files()

    target = None
    for path in experiments:
        if path.name == experiment_name:
            target = path
            break

    if target is None:
        raise ValueError(f"Experiment not found: {experiment_name}")

    return experiment_inspector.inspect(target)


def get_experiment_family(experiment_name: str):
    experiments = experiment_registry.experiment_files()

    target = None
    for path in experiments:
        if path.name == experiment_name:
            target = path
            break

    if target is None:
        raise ValueError(f"Experiment not found: {experiment_name}")

    family = experiment_inspector.find_family(target)

    return {
        "experiment": target.name,
        "family": [path.name for path in family],
    }


def get_experiment_evidence(experiment_name: str):
    bundle = collect_experiment_evidence(experiment_name)
    return bundle.as_dict()


def register_tools():
    register(
        name="list_experiments",
        description="List all RichardLab experiments with their file type and experiment family.",
        function=list_experiments,
        category="experiments",
        safety="read_only",
    )

    register(
        name="inspect_experiment",
        description="Inspect a specific RichardLab experiment and return its available metadata, family, related outputs, and analysis.",
        function=inspect_experiment,
        category="experiments",
        safety="read_only",
    )

    register(
        name="get_experiment_family",
        description="Return the related experiment files belonging to the same RichardLab experiment family.",
        function=get_experiment_family,
        category="experiments",
        safety="read_only",
    )

    register(
        name="get_experiment_evidence",
        description="Collect structured evidence for a RichardLab experiment, including file metadata, family relationships, source similarity, Git history, related outputs, execution runs, artifacts, and available lab system metrics.",
        function=get_experiment_evidence,
        category="evidence",
        safety="read_only",
    )
