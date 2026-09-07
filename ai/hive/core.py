#!/usr/bin/env python3

import json
import re
from dataclasses import dataclass, field
from typing import Any

from ..lab_tools_registry import load_registry
from ..router.deterministic import classify
from ..tool_registry import call_tool


@dataclass
class HiveResult:
    route: str
    worker: str
    result: Any
    provider: str | None = None
    elapsed_seconds: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self):
        return {
            "route": self.route,
            "worker": self.worker,
            "provider": self.provider,
            "elapsed_seconds": self.elapsed_seconds,
            "metadata": self.metadata,
            "result": self.result,
        }


class HiveCore:
    def __init__(self, config, provider_factory, router_factory):
        self.config = config
        self.provider_factory = provider_factory
        self.router_factory = router_factory
        self._ensure_registry()

    def _ensure_registry(self):
        try:
            load_registry()
        except ValueError as exc:
            if "Tool already registered" not in str(exc):
                raise

    def _extract_experiment(self, prompt: str) -> str:
        match = re.search(
            r"\bexperiment[- ]?(\d{3}[a-z]?)\b",
            prompt.lower(),
        )

        if not match:
            raise ValueError(
                f"Could not identify an experiment number in request: {prompt}"
            )

        number = match.group(1)
        return f"experiment-{number}.py"

    def _reasoning_evidence(self, prompt: str) -> tuple[str | None, dict[str, Any] | None]:
        try:
            experiment = self._extract_experiment(prompt)
        except ValueError:
            return None, None

        evidence = call_tool(
            "get_experiment_evidence",
            experiment_name=experiment,
        )

        return experiment, evidence

    def _build_reasoning_prompt(
        self,
        prompt: str,
        experiment: str | None,
        evidence: dict[str, Any] | None,
    ) -> str:
        if evidence is None:
            return (
                "Analyze the user's request using your general reasoning ability.\n\n"
                "USER REQUEST:\n"
                f"{prompt}\n\n"
                "Do not invent RichardLab-specific facts that are not supplied."
            )

        compact_evidence = dict(evidence)

        # Source code is deep evidence. Keep it available to the reasoning
        # system, but label it explicitly so it knows it is raw source.
        source_files = compact_evidence.pop("source_files", {})

        evidence_json = json.dumps(
            compact_evidence,
            indent=2,
            default=str,
        )

        source_json = json.dumps(
            source_files,
            indent=2,
        )

        return f"""
You are the reasoning system for RichardLab.

Analyze the user's question using the supplied RichardLab evidence.

Rules:
1. Treat supplied evidence as the source of truth.
2. Separate direct facts from inference.
3. Do not invent missing history, intentions, causes, or events.
4. If the evidence is insufficient to answer "why", explicitly say what is unknown.
5. Distinguish source similarity from proven lineage.
6. Distinguish lab-level system metrics from experiment-specific metrics.
7. When source code is supplied, compare the actual code rather than guessing.
8. Keep conclusions proportional to the evidence.

USER REQUEST:
{prompt}

TARGET EXPERIMENT:
{experiment}

STRUCTURED EVIDENCE:
{evidence_json}

RAW SOURCE EVIDENCE:
{source_json}
""".strip()

    def dispatch_local(self, prompt, route):
        if route == "system_status":
            result = call_tool("get_lab_status")

            return HiveResult(
                route=route,
                worker="system",
                result=result,
                provider="local",
                metadata={
                    "tool": "get_lab_status",
                    "safety": "read_only",
                },
            )

        if route == "experiment_list":
            result = call_tool("list_experiments")

            return HiveResult(
                route=route,
                worker="experiments",
                result=result,
                provider="local",
                metadata={
                    "tool": "list_experiments",
                    "safety": "read_only",
                },
            )

        if route == "experiment_inspect":
            experiment = self._extract_experiment(prompt)
            result = call_tool(
                "inspect_experiment",
                experiment_name=experiment,
            )

            return HiveResult(
                route=route,
                worker="experiments",
                result=result,
                provider="local",
                metadata={
                    "tool": "inspect_experiment",
                    "experiment": experiment,
                    "safety": "read_only",
                },
            )

        if route == "experiment_family":
            experiment = self._extract_experiment(prompt)
            result = call_tool(
                "get_experiment_family",
                experiment_name=experiment,
            )

            return HiveResult(
                route=route,
                worker="experiments",
                result=result,
                provider="local",
                metadata={
                    "tool": "get_experiment_family",
                    "experiment": experiment,
                    "safety": "read_only",
                },
            )

        raise RuntimeError(
            f"No deterministic worker registered for route: {route}"
        )

    def dispatch_reasoning(self, prompt):
        experiment, evidence = self._reasoning_evidence(prompt)

        reasoning_prompt = self._build_reasoning_prompt(
            prompt,
            experiment,
            evidence,
        )

        router = self.router_factory(
            self.config,
            self.provider_factory,
        )

        result, health = router.ask(
            reasoning_prompt,
            system="You are the reasoning system for RichardLab.",
        )

        metadata = {
            "provider_metadata": result.metadata or {},
            "provider_health": {
                name: state.as_dict()
                for name, state in health.items()
            },
            "evidence_collected": evidence is not None,
            "evidence_experiment": experiment,
        }

        if evidence is not None:
            metadata["evidence_summary"] = {
                "family_count": len(evidence.get("family", [])),
                "similarity_count": len(evidence.get("similarities", [])),
                "run_count": len(evidence.get("runs", [])),
                "artifact_count": len(evidence.get("artifacts", [])),
                "related_output_count": len(
                    evidence.get("related_outputs", [])
                ),
                "source_file_count": len(
                    evidence.get("source_files", {})
                ),
            }

        return HiveResult(
            route="ai_reasoning",
            worker="reasoning",
            result=result.text,
            provider=result.provider,
            elapsed_seconds=result.elapsed_seconds,
            metadata=metadata,
        )

    def dispatch(self, prompt):
        route = classify(prompt)

        if route == "ai_reasoning":
            return self.dispatch_reasoning(prompt)

        return self.dispatch_local(prompt, route)
