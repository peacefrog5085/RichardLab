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

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Make the RichardLab project root importable when this file is
# launched directly as a script.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def header() -> None:
    print()
    print("=" * 52)
    print("                 RICHARDLAB")
    print("     Observation -> Experiment -> Evidence")
    print("=" * 52)
    print()
    print(f"Project: {PROJECT_ROOT}")
    print()


def system_status() -> None:
    print()
    print("===== RICHARDLAB STATUS =====")

    checks = {
        "Python": sys.executable,
        "Gateway": PROJECT_ROOT / "ai" / "gateway.py",
        "Hive": PROJECT_ROOT / "ai" / "hive" / "core.py",
        "Router": PROJECT_ROOT / "ai" / "router" / "router.py",
        "Workers": PROJECT_ROOT / "ai" / "workers",
        "Experiments": PROJECT_ROOT / "experiments",
        "Evidence": PROJECT_ROOT / "data",
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

    try:
        from ai.gateway import load_config, build_provider
        from ai.workers import WorkerRegistry
        from ai.workers.gemini import GeminiWorker
        from ai.workers.ollama import OllamaWorker
        from ai.workers.codex import CodexWorker

        config = load_config()
        registry = WorkerRegistry()

        registry.register(
            GeminiWorker(config, build_provider)
        )
        registry.register(
            OllamaWorker(config, build_provider)
        )
        registry.register(
            CodexWorker(config, build_provider)
        )

        for worker in registry.list():
            print(f"\n{worker.name}")
            print(f"  kind:         {worker.kind}")
            print(f"  capabilities: {', '.join(worker.capabilities)}")

    except Exception as exc:
        print(f"Worker inspection failed: {exc}")

    print()


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

    print()


def dashboard_status() -> None:
    print()
    print("===== DASHBOARD =====")
    print()
    print("Dashboard launcher: NOT YET IMPLEMENTED")
    print("The CLI front door is ready for dashboard integration.")
    print()


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
            dashboard_status()
        elif choice == "2":
            print("\nAsk RichardLab integration: next layer.")
        elif choice == "3":
            print("\nExperiment launcher integration: next layer.")
        elif choice == "4":
            print("\nEvidence interface integration: next layer.")
        elif choice == "5":
            print("\nKnowledge interface integration: next layer.")
        elif choice == "6":
            system_status()
        elif choice == "7":
            worker_status()
        elif choice == "8":
            security_status()
        elif choice == "9":
            print("\nDeveloper / Codex integration: next layer.")
        else:
            print(f"\nUnknown selection: {choice}")

        input("Press Enter to return to the RichardLab menu...")


if __name__ == "__main__":
    raise SystemExit(main())
