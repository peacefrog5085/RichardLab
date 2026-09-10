#!/usr/bin/env python3

"""
RichardLab command-line front door.

Principles:
- deterministic
- inspectable
- read-only at the menu layer
- delegates actual work to existing RichardLab subsystems
- never executes arbitrary shell commands from user input
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def header() -> None:
    print()
    print("=" * 60)
    print("                     RICHARDLAB")
    print("     Observation -> Hypothesis -> Experiment")
    print("       -> Evidence -> Conclusion -> Knowledge")
    print("=" * 60)
    print()
    print(f"Project: {PROJECT_ROOT}")
    print()


def pause() -> None:
    try:
        input("\nPress Enter to return to the RichardLab menu...")
    except (EOFError, KeyboardInterrupt):
        print()


def run_existing_script(relative_path: str) -> None:
    script = PROJECT_ROOT / relative_path

    if not script.exists():
        print(f"\n[ACTION] Missing subsystem: {script}")
        return

    if not script.is_file():
        print(f"\n[ACTION] Not a file: {script}")
        return

    try:
        result = subprocess.run(
            [str(script)],
            cwd=PROJECT_ROOT,
            check=False,
        )

        if result.returncode != 0:
            print(
                f"\n[ACTION] Subsystem exited with status "
                f"{result.returncode}"
            )

    except OSError as exc:
        print(f"\n[ACTION] Could not launch subsystem: {exc}")


def system_status() -> None:
    print()
    print("===== RICHARDLAB STATUS =====")
    print()

    checks = {
        "Python": sys.executable,
        "Gateway": PROJECT_ROOT / "ai" / "gateway.py",
        "Hive": PROJECT_ROOT / "ai" / "hive" / "core.py",
        "Router": PROJECT_ROOT / "ai" / "router" / "router.py",
        "Workers": PROJECT_ROOT / "ai" / "workers",
        "Experiments": PROJECT_ROOT / "experiments",
        "Evidence": PROJECT_ROOT / "data",
        "Knowledge": PROJECT_ROOT / "knowledge",
    }

    for name, value in checks.items():
        if isinstance(value, Path):
            state = "PRESENT" if value.exists() else "MISSING"
            print(f"{name:12} {state:8} {value}")
        else:
            print(f"{name:12} {value}")

    print()


def worker_status() -> None:
    print()
    print("===== AI WORKERS =====")
    print()

    try:
        from ai.gateway import load_config, build_provider
        from ai.workers import WorkerRegistry
        from ai.workers.gemini import GeminiWorker
        from ai.workers.ollama import OllamaWorker
        from ai.workers.codex import CodexWorker

        config = load_config()
        registry = WorkerRegistry()

        registry.register(GeminiWorker(config, build_provider))
        registry.register(OllamaWorker(config, build_provider))
        registry.register(CodexWorker(config, build_provider))

        for worker in registry.list():
            print(f"{worker.name}")
            print(f"  kind:         {worker.kind}")
            print(f"  capabilities: {', '.join(worker.capabilities)}")

            try:
                health = worker.health()
                print(f"  health:       {health}")
            except Exception as exc:
                print(f"  health:       ERROR: {exc}")

            print()

    except Exception as exc:
        print(f"Worker inspection failed: {exc}")

    pause()


def security_status() -> None:
    print()
    print("===== RICHARDLAB SECURITY =====")
    print()

    try:
        from ai.security.audit import SecurityAudit

        report = SecurityAudit(PROJECT_ROOT).run()

        print(f"Overall status: {report.status}")
        print()

        for finding in report.findings:
            marker = {
                "PASS": "[PASS]",
                "REVIEW": "[REVIEW]",
                "ACTION_REQUIRED": "[ACTION]",
            }.get(finding.status, "[UNKNOWN]")

            print(f"  {marker} {finding.check}")
            print(f"          {finding.summary}")

        print()
        print("Security audit is read-only.")
        print("No firewall, service, file, or permission changes were made.")

    except Exception as exc:
        print("  [ACTION] Security audit failed")
        print(f"          {type(exc).__name__}: {exc}")

    pause()


def dashboard() -> None:
    run_existing_script("dashboard/lab.sh")


def ask_richardlab() -> None:
    print()
    print("===== ASK RICHARDLAB =====")
    print()
    print("Request enters HiveCore.")
    print("Deterministic routes remain local.")
    print("Reasoning requests use WorkerPolicy.")
    print()

    try:
        prompt = input("RichardLab> ").strip()
    except (EOFError, KeyboardInterrupt):
        return

    if not prompt:
        return

    try:
        from ai.gateway import load_config, build_provider, build_router
        from ai.hive.core import HiveCore

        config = load_config()

        hive = HiveCore(
            config,
            build_provider,
            build_router,
        )

        result = hive.dispatch(prompt)

        print()
        print("===== HIVE RESULT =====")
        print()
        print(f"Route:    {result.route}")
        print(f"Worker:   {result.worker}")
        print(f"Provider: {result.provider}")
        print(f"Elapsed:  {result.elapsed_seconds}")

        print()
        print("RESULT")
        print("-" * 60)
        print(result.result)

        if result.metadata:
            print()
            print("METADATA")
            print("-" * 60)
            print(json.dumps(result.metadata, indent=2, default=str))

    except Exception as exc:
        print()
        print("[ACTION] Hive request failed")
        print(f"{type(exc).__name__}: {exc}")

    pause()


def run_experiment() -> None:
    run_existing_script("mission_control/experiment_center.sh")


def inspect_evidence() -> None:
    print()
    print("===== INSPECT EVIDENCE =====")
    print()
    print("Evidence is collected through the existing EvidenceBundle.")
    print()

    try:
        experiment = input("Experiment filename: ").strip()
    except (EOFError, KeyboardInterrupt):
        return

    if not experiment:
        return

    if not experiment.endswith((".py", ".sh")):
        experiment += ".py"

    try:
        from ai.hive.evidence import collect_experiment_evidence

        bundle = collect_experiment_evidence(experiment)

        print()
        print(json.dumps(bundle.as_dict(), indent=2, default=str))

    except Exception as exc:
        print()
        print("[ACTION] Evidence collection failed")
        print(f"{type(exc).__name__}: {exc}")

    pause()


def knowledge_base() -> None:
    while True:
        print()
        print("===== KNOWLEDGE BASE =====")
        print()
        print("  1. Search / Consult")
        print("  2. Knowledge Statistics")
        print("  3. Learn From Experiment Runs")
        print("  4. List Recent Knowledge")
        print("  B. Back")
        print()

        try:
            choice = input("Knowledge> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return

        if choice == "b":
            return

        if choice == "1":
            knowledge_search()
        elif choice == "2":
            knowledge_stats()
        elif choice == "3":
            knowledge_learn()
        elif choice == "4":
            knowledge_recent()
        else:
            print("\nUnknown selection.")


def knowledge_search() -> None:
    print()
    print("===== KNOWLEDGE CONSULTATION =====")
    print()

    try:
        query = input("Knowledge query> ").strip()
    except (EOFError, KeyboardInterrupt):
        return

    if not query:
        return

    try:
        from knowledge.knowledge import consult

        result = consult(query)

        print()
        print(json.dumps(result, indent=2, default=str))

    except Exception as exc:
        print()
        print("[ACTION] Knowledge consultation failed")
        print(f"{type(exc).__name__}: {exc}")

    pause()


def knowledge_stats() -> None:
    print()
    print("===== KNOWLEDGE STATISTICS =====")
    print()

    try:
        from knowledge.knowledge import load_all

        records = load_all()

        print(f"Total knowledge records: {len(records)}")

        by_kind = {}
        by_status = {}

        for record in records:
            kind = record.get("kind", "unknown")
            status = record.get("status", "unknown")

            by_kind[kind] = by_kind.get(kind, 0) + 1
            by_status[status] = by_status.get(status, 0) + 1

        print()
        print("BY KIND")
        for key in sorted(by_kind):
            print(f"  {key:20} {by_kind[key]}")

        print()
        print("BY STATUS")
        for key in sorted(by_status):
            print(f"  {key:20} {by_status[key]}")

    except Exception as exc:
        print()
        print("[ACTION] Knowledge statistics failed")
        print(f"{type(exc).__name__}: {exc}")

    pause()


def knowledge_learn() -> None:
    print()
    print("===== LEARN FROM EXPERIMENT RUNS =====")
    print()

    try:
        from knowledge.learn import main as learn_main

        result = learn_main()

        if result is not None:
            print(f"\nLearner exit status: {result}")

    except Exception as exc:
        print()
        print("[ACTION] Knowledge learner failed")
        print(f"{type(exc).__name__}: {exc}")

    pause()


def knowledge_recent() -> None:
    print()
    print("===== RECENT KNOWLEDGE =====")
    print()

    try:
        from knowledge.knowledge import load_all

        records = load_all()

        recent = sorted(
            records,
            key=lambda record: record.get("updated_at", ""),
            reverse=True,
        )[:10]

        if not recent:
            print("No knowledge records found.")
        else:
            for record in recent:
                print(
                    f"{record.get('knowledge_id', '?')}  "
                    f"{record.get('kind', '?'):16} "
                    f"{record.get('status', '?'):12} "
                    f"{record.get('subject', '')}"
                )

    except Exception as exc:
        print()
        print("[ACTION] Knowledge inspection failed")
        print(f"{type(exc).__name__}: {exc}")

    pause()


def developer_codex() -> None:
    while True:
        print()
        print("===== DEVELOPER / CODEX =====")
        print()
        print("  1. Worker Status")
        print("  2. Codex Health")
        print("  3. Codex Worker Capabilities")
        print("  B. Back")
        print()

        try:
            choice = input("Developer> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return

        if choice == "b":
            return

        if choice == "1":
            worker_status()
            continue

        if choice in {"2", "3"}:
            try:
                from ai.gateway import load_config, build_provider
                from ai.workers.codex import CodexWorker

                config = load_config()
                worker = CodexWorker(config, build_provider)

                if choice == "2":
                    print()
                    print(json.dumps(
                        worker.health(),
                        indent=2,
                        default=str,
                    ))
                else:
                    print()
                    print("CODEX WORKER")
                    print("-" * 60)
                    print(f"name:         {worker.name}")
                    print(f"kind:         {worker.kind}")
                    print(f"description:  {worker.description}")
                    print("capabilities:")

                    for capability in worker.capabilities:
                        print(f"  - {capability}")

            except Exception as exc:
                print()
                print("[ACTION] Codex inspection failed")
                print(f"{type(exc).__name__}: {exc}")

            pause()
            continue

        print("\nUnknown selection.")


def show_menu() -> None:
    print("  1. Open Dashboard")
    print("  2. Ask RichardLab")
    print("  3. Run an Experiment")
    print("  4. Inspect Evidence")
    print("  5. Knowledge Base")
    print("  6. System Status")
    print("  7. AI / Worker Status")
    print("  8. Security Check")
    print("  9. Developer / Codex")
    print("  0. Exit")
    print()


def main() -> int:
    while True:
        header()
        show_menu()

        try:
            choice = input("Select: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting RichardLab.")
            return 0

        if choice == "0":
            print("Exiting RichardLab.")
            return 0

        if choice == "1":
            dashboard()
        elif choice == "2":
            ask_richardlab()
        elif choice == "3":
            run_experiment()
        elif choice == "4":
            inspect_evidence()
        elif choice == "5":
            knowledge_base()
        elif choice == "6":
            system_status()
            pause()
        elif choice == "7":
            worker_status()
        elif choice == "8":
            security_status()
        elif choice == "9":
            developer_codex()
        else:
            print(f"\nUnknown selection: {choice}")
            pause()


if __name__ == "__main__":
    raise SystemExit(main())
