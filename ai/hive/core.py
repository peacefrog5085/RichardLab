#!/usr/bin/env python3

import json
import re
from dataclasses import dataclass, field
from typing import Any

from ..lab_tools_registry import load_registry
from ..router.deterministic import classify
from ..router.capabilities import capability_for_route
from ..tool_registry import call_tool
from ..workers import WorkerRegistry, WorkerPolicy
from ..workers.gemini import GeminiWorker
from ..workers.ollama import OllamaWorker
from ..workers.codex import CodexWorker
from ..workers.openai import OpenAIWorker
from knowledge.knowledge import consult
from .council import Council


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

        self.worker_registry = WorkerRegistry()
        self._register_workers()
        self.worker_policy = WorkerPolicy(
            self.worker_registry,
            self.config,
        )

        self._ensure_registry()
        self.council = self._build_council()

    def _register_workers(self):
        workers = (
            GeminiWorker(self.config, self.provider_factory),
            OllamaWorker(self.config, self.provider_factory),
            CodexWorker(self.config, self.provider_factory),
            OpenAIWorker(self.config, self.provider_factory),
        )

        for worker in workers:
            self.worker_registry.register(worker)

    def _build_council(self) -> Council:
        """Build the multi-agent Council from registered Hive workers."""
        from .debate import DEFAULT_ROLES

        agents = {}

        for role in DEFAULT_ROLES:
            worker_name = self._council_worker_name(role.name)
            worker = self.worker_registry.get(worker_name)
            agents[role.name] = (role, worker)

        auditor = self.worker_registry.get(
            self._council_worker_name("auditor")
        )
        synthesizer = self.worker_registry.get(
            self._council_worker_name("synthesizer")
        )

        return Council(
            agents=agents,
            auditor=auditor,
            synthesizer=synthesizer,
        )

    def _council_worker_name(self, role: str) -> str:
        """Resolve a configured worker for a Council role."""
        council_config = self.config.get("council", {})
        role_config = council_config.get(role)

        if isinstance(role_config, dict):
            worker_name = role_config.get("worker")
        else:
            worker_name = role_config

        if worker_name:
            return worker_name

        routing = self.config.get("routing", {})
        primary = routing.get("primary")

        if primary in self.worker_registry.names():
            return primary

        names = self.worker_registry.names()
        if not names:
            raise RuntimeError("No workers are registered for the Council")

        return names[0]

    def worker_info(self) -> list[dict[str, Any]]:
        """Return the currently registered Hive workers."""
        return [
            worker.info()
            for worker in self.worker_registry.list()
        ]

    def heartbeat(self, path=None):
        """
        Read current RichardLab heartbeat state.

        The heartbeat is deterministic and observational. It does not
        invoke AI reasoning or mutate durable knowledge.
        """
        from mission_control.heartbeat import pulse

        if path is None:
            return pulse()

        return pulse(path)

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
        heartbeat=None,
    ) -> str:
        if evidence is None:
            return (
                "Analyze the user's request using your general reasoning ability.\n\n"
                "USER REQUEST:\n"
                f"{prompt}\n\n"
                "Do not invent RichardLab-specific facts that are not supplied."
            )

        # The context selector is authoritative for reasoning context.
        # Always serialize the bounded reasoning packet rather than the
        # complete evidence bundle.
        if knowledge is None:
            knowledge = self._knowledge_consultation(prompt)

        from ai.hive.context_selector import select_reasoning_context

        compact_evidence = select_reasoning_context(
            prompt,
            evidence,
            knowledge=knowledge,
            heartbeat=heartbeat,
        )

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

    def dispatch_council(self, prompt: str):
        """Run the RichardLab multi-agent Council explicitly."""
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Council prompt must be a non-empty string")

        return self.council.deliberate(prompt.strip())

    def dispatch_reasoning(self, prompt, route="ai_reasoning"):
        capability = capability_for_route(route)

        if capability is None:
            raise RuntimeError(
                f"No AI worker capability mapped for route: {route}"
            )

        # WorkerPolicy decides WHO should perform the task.
        # Hive owns execution so the selected worker is actually used.
        worker_decision = self.worker_policy.select(capability)

        if worker_decision.selected is None:
            raise RuntimeError(
                "No worker selected for capability "
                f"{capability}: {worker_decision.reason}"
            )

        worker = self.worker_registry.get(worker_decision.selected)

        experiment, evidence = self._reasoning_evidence(prompt)

        knowledge = self._knowledge_consultation(prompt)

        # Heartbeat is a quiet observational substrate. Capture one
        # deterministic pulse for this reasoning cycle and pass the
        # result into the bounded context selector.
        heartbeat = self.heartbeat()

        reasoning_prompt = self._build_reasoning_prompt(
            prompt,
            experiment,
            evidence,
            knowledge,
            heartbeat,
        )

        routing = self.config.get("routing", {})
        automatic_fallback = routing.get(
            "allow_automatic_fallback",
            False,
        )
        fallback_name = routing.get("fallback")

        provider_result = None
        execution_error = None
        executed_worker = worker
        fallback_used = False

        try:
            provider_result = worker.execute(
                reasoning_prompt,
                system="You are the reasoning system for RichardLab.",
            )
        except Exception as exc:
            execution_error = exc

            if (
                automatic_fallback
                and fallback_name
                and fallback_name != worker.name
                and fallback_name in worker_decision.candidates
            ):
                fallback_worker = self.worker_registry.get(fallback_name)

                try:
                    fallback_worker.health()
                    provider_result = fallback_worker.execute(
                        reasoning_prompt,
                        system="You are the reasoning system for RichardLab.",
                    )
                    executed_worker = fallback_worker
                    fallback_used = True
                except Exception as fallback_exc:
                    execution_error = fallback_exc

            if provider_result is None:
                raise execution_error

        metadata = {
            "worker_selection": {
                "capability": worker_decision.capability,
                "candidates": list(worker_decision.candidates),
                "selected": worker_decision.selected,
                "policy": worker_decision.policy,
                "reason": worker_decision.reason,
            },
            "worker_execution": {
                "selected": worker.name,
                "executed": executed_worker.name,
                "fallback_used": fallback_used,
            },
            "provider_metadata": provider_result.metadata or {},
            "evidence_collected": evidence is not None,
            "evidence_experiment": experiment,
            "knowledge_decision": knowledge.get("decision"),
            "knowledge_id": knowledge.get("knowledge_id"),
            "knowledge_matches": len(knowledge.get("matches", [])),
        }

        if fallback_used:
            metadata["router_fallback"] = True
            metadata["router_primary_provider"] = worker.name

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
            worker=executed_worker.name,
            result=provider_result.text,
            provider=provider_result.provider,
            elapsed_seconds=provider_result.elapsed_seconds,
            metadata=metadata,
        )

    def dispatch(self, prompt):
        route = classify(prompt)

        if route == "ai_reasoning":
            return self.dispatch_reasoning(prompt, route=route)

        return self.dispatch_local(prompt, route)
