#!/usr/bin/env python3

import json
import re
from dataclasses import dataclass, field
from typing import Any

from ..lab_tools_registry import load_registry
from ..router.deterministic import classify
from ..tool_registry import call_tool
from knowledge.knowledge import consult


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

    def _knowledge_consultation(self, prompt: str) -> dict[str, Any]:
        """Consult durable RichardLab knowledge without modifying it."""
        try:
            return consult(prompt)
        except Exception as exc:
            return {
                "query": prompt,
                "decision": "REVIEW",
                "reason": f"Knowledge consultation failed: {exc}",
                "knowledge_id": None,
                "matches": [],
            }

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
        knowledge: dict[str, Any] | None = None,
    ) -> str:
        if evidence is None:
            return (
                "Analyze the user's request using your general reasoning ability.\n\n"
                "USER REQUEST:\n"
                f"{prompt}\n\n"
                "Do not invent RichardLab-specific facts that are not supplied."
            )

        # The context selector is authoritative for reasoning context.
        # Do not independently re-expand source_files or other evidence here.
        compact_evidence = dict(evidence)

        if knowledge is None:
            knowledge = self._knowledge_consultation(prompt)

        compact_evidence["knowledge"] = knowledge

        evidence_json = json.dumps(
            compact_evidence,
            indent=2,
            default=str,
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
9. Treat durable knowledge as prior evidence, not unquestionable truth.
10. If knowledge says BLOCK, explain the documented failure or constraint before recommending that approach.
11. If knowledge says REUSE, identify the successful baseline and its conditions when relevant.
12. If knowledge says CAUTION or REVIEW, explicitly preserve the uncertainty.
13. Do not claim that a knowledge match proves the current situation is identical.

USER REQUEST:
{prompt}

TARGET EXPERIMENT:
{experiment}

SELECTED RICHARDLAB EVIDENCE:
{evidence_json}
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

        knowledge = self._knowledge_consultation(prompt)

        reasoning_prompt = self._build_reasoning_prompt(
            prompt,
            experiment,
            evidence,
            knowledge,
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
            "knowledge_decision": knowledge.get("decision"),
            "knowledge_id": knowledge.get("knowledge_id"),
            "knowledge_matches": len(knowledge.get("matches", [])),
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
