#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import socket
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "ai" / "config.json"


@dataclass(frozen=True)
class SecurityFinding:
    check: str
    status: str
    summary: str
    details: dict[str, Any]


@dataclass(frozen=True)
class SecurityReport:
    status: str
    findings: tuple[SecurityFinding, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "findings": [asdict(finding) for finding in self.findings],
        }


class SecurityAudit:
    """
    Read-only RichardLab security inspection.

    This subsystem observes the environment.
    It does not modify firewall rules, services, files, permissions,
    network configuration, or execution policy.
    """

    def __init__(self, project_root: Path = PROJECT_ROOT) -> None:
        self.project_root = Path(project_root)

    def run(self) -> SecurityReport:
        findings = (
            self._check_project_boundary(),
            self._check_config(),
            self._check_network_exposure(),
            self._check_ollama(),
            self._check_secrets(),
            self._check_secret_file_policy(),
            self._check_git_history_secrets(),
            self._check_git_state(),
        )

        statuses = {finding.status for finding in findings}

        if "ACTION_REQUIRED" in statuses:
            overall = "ACTION_REQUIRED"
        elif "REVIEW" in statuses:
            overall = "REVIEW"
        else:
            overall = "PASS"

        return SecurityReport(
            status=overall,
            findings=findings,
        )

    def _check_project_boundary(self) -> SecurityFinding:
        exists = self.project_root.is_dir()

        return SecurityFinding(
            check="project_boundary",
            status="PASS" if exists else "ACTION_REQUIRED",
            summary=(
                "RichardLab project boundary exists."
                if exists
                else "RichardLab project boundary is missing."
            ),
            details={
                "project_root": str(self.project_root),
                "exists": exists,
            },
        )

    def _check_config(self) -> SecurityFinding:
        if not CONFIG_PATH.exists():
            return SecurityFinding(
                check="ai_config",
                status="ACTION_REQUIRED",
                summary="AI configuration file is missing.",
                details={"path": str(CONFIG_PATH)},
            )

        try:
            with CONFIG_PATH.open("r", encoding="utf-8") as handle:
                config = json.load(handle)
        except Exception as exc:
            return SecurityFinding(
                check="ai_config",
                status="ACTION_REQUIRED",
                summary="AI configuration could not be parsed.",
                details={
                    "path": str(CONFIG_PATH),
                    "error": type(exc).__name__,
                },
            )

        routing = config.get("routing", {})
        providers = config.get("providers", {})

        required_providers = {"gemini", "ollama", "codex"}
        missing = sorted(required_providers - set(providers))

        if missing:
            status = "ACTION_REQUIRED"
        else:
            status = "PASS"

        return SecurityFinding(
            check="ai_config",
            status=status,
            summary=(
                "AI configuration is present and contains the expected providers."
                if status == "PASS"
                else "AI configuration is missing expected providers."
            ),
            details={
                "path": str(CONFIG_PATH),
                "primary": routing.get("primary"),
                "fallback": routing.get("fallback"),
                "automatic_fallback": routing.get(
                    "allow_automatic_fallback"
                ),
                "providers": sorted(providers),
                "missing_providers": missing,
            },
        )

    def _check_network_exposure(self) -> SecurityFinding:
        listeners = self._listening_sockets()

        richardlab_listeners = [
            item
            for item in listeners
            if item["process"].lower().startswith("richardlab")
        ]

        wildcard_listeners = [
            item
            for item in listeners
            if item["address"] in {"0.0.0.0", "::", "*"}
        ]

        if richardlab_listeners:
            status = "ACTION_REQUIRED"
            summary = "RichardLab has a network listener."
        else:
            status = "PASS"
            summary = "No RichardLab network listener was detected."

        return SecurityFinding(
            check="network_exposure",
            status=status,
            summary=summary,
            details={
                "richardlab_listeners": richardlab_listeners,
                "wildcard_listener_count": len(wildcard_listeners),
                "listener_count": len(listeners),
            },
        )

    def _check_ollama(self) -> SecurityFinding:
        listeners = self._listening_sockets()

        ollama = [
            item
            for item in listeners
            if "ollama" in item["process"].lower()
        ]

        if not ollama:
            return SecurityFinding(
                check="ollama_exposure",
                status="REVIEW",
                summary="Ollama listener was not detected.",
                details={"listeners": []},
            )

        exposed = [
            item
            for item in ollama
            if item["address"] not in {"127.0.0.1", "::1", "localhost"}
        ]

        if exposed:
            status = "ACTION_REQUIRED"
            summary = "Ollama appears to have a non-local listener."
        else:
            status = "PASS"
            summary = "Ollama appears restricted to localhost."

        return SecurityFinding(
            check="ollama_exposure",
            status=status,
            summary=summary,
            details={
                "listeners": ollama,
                "non_local_listeners": exposed,
            },
        )

    def _check_secrets(self) -> SecurityFinding:
        """Scan project files for common credential patterns.

        This check is read-only and never records matched secret values.
        """

        patterns = {
            "google_api_key": re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
            "openai_api_key": re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
            "xai_api_key": re.compile(r"xai-[A-Za-z0-9_-]{20,}"),
            "github_token": re.compile(
                r"gh[pousr]_[A-Za-z0-9_]{20,}"
            ),
            "private_key": re.compile(
                r"-----BEGIN (?:RSA|OPENSSH|EC|PRIVATE) KEY-----"
            ),
        }

        matches: list[dict[str, str]] = []

        for path in self.project_root.rglob("*"):
            if not path.is_file():
                continue

            try:
                relative = path.relative_to(self.project_root)
            except ValueError:
                continue

            if any(part in {".git", ".venv", "__pycache__"} for part in relative.parts):
                continue

            try:
                content = path.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )
            except OSError:
                continue

            for name, pattern in patterns.items():
                if pattern.search(content):
                    matches.append(
                        {
                            "path": str(relative),
                            "pattern": name,
                        }
                    )

        status = "ACTION_REQUIRED" if matches else "PASS"

        return SecurityFinding(
            check="secrets",
            status=status,
            summary=(
                "No common credential patterns were detected."
                if not matches
                else "Potential credential patterns were detected."
            ),
            details={
                "matches": matches,
                "match_count": len(matches),
            },
        )

    def _check_secret_file_policy(self) -> SecurityFinding:
        """Check that existing sensitive files are protected by .gitignore.

        This check is read-only and never reads or records secret contents.
        """

        sensitive_patterns = (
            ".env",
            ".env.*",
            "credentials.json",
            "secrets.json",
            "service-account.json",
            "*.pem",
            "*.key",
            "*.p12",
            "*.pfx",
        )

        gitignore = self.project_root / ".gitignore"

        try:
            ignored_rules = {
                line.strip()
                for line in gitignore.read_text(
                    encoding="utf-8",
                    errors="ignore",
                ).splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            }
        except OSError:
            ignored_rules = set()

        def matches_pattern(name: str, pattern: str) -> bool:
            if pattern.startswith("*."):
                return name.endswith(pattern[1:])
            if pattern.endswith(".*"):
                return name.startswith(pattern[:-1])
            return name == pattern

        matches = []

        for path in self.project_root.rglob("*"):
            if not path.is_file():
                continue

            try:
                relative = path.relative_to(self.project_root)
            except ValueError:
                continue

            if any(
                part in {".git", ".venv", "__pycache__"}
                for part in relative.parts
            ):
                continue

            if any(
                matches_pattern(path.name, pattern)
                for pattern in sensitive_patterns
            ):
                protected = any(
                    matches_pattern(path.name, rule)
                    for rule in ignored_rules
                )

                if not protected:
                    matches.append(
                        {
                            "path": str(relative),
                            "reason": "sensitive_filename_not_ignored",
                        }
                    )

        status = "ACTION_REQUIRED" if matches else "PASS"

        return SecurityFinding(
            check="secret_file_policy",
            status=status,
            summary=(
                "Existing sensitive files are protected by .gitignore."
                if not matches
                else "Existing sensitive files are not protected by .gitignore."
            ),
            details={
                "matches": matches,
                "match_count": len(matches),
            },
        )

    def _git_history_matches(self) -> list[dict[str, str]]:
        """Search Git history for common credential patterns.

        Results contain only commit, path, and pattern name.
        Secret values are never returned.
        """

        patterns = {
            "google_api_key": re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
            "openai_api_key": re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
            "xai_api_key": re.compile(r"xai-[A-Za-z0-9_-]{20,}"),
            "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
            "private_key": re.compile(
                r"-----BEGIN (?:RSA|OPENSSH|EC|PRIVATE) KEY-----"
            ),
        }

        try:
            commits = subprocess.run(
                ["git", "rev-list", "--all"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.splitlines()
        except (OSError, subprocess.CalledProcessError):
            return []

        matches = []

        for commit in commits:
            try:
                result = subprocess.run(
                    [
                        "git", "grep", "-n", "-I", "-E",
                        "|".join(pattern.pattern for pattern in patterns.values()),
                        commit, "--",
                        ":(exclude).venv",
                        ":(exclude)**/__pycache__",
                    ],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    check=False,
                )
            except OSError:
                continue

            if result.returncode not in {0, 1}:
                continue

            for line in result.stdout.splitlines():
                parts = line.split(":", 3)

                if len(parts) < 4:
                    continue

                path = parts[1]
                content = parts[3]

                for name, pattern in patterns.items():
                    if pattern.search(content):
                        matches.append(
                            {
                                "commit": commit,
                                "path": path,
                                "pattern": name,
                            }
                        )
                        break

        return matches

    def _check_git_history_secrets(self) -> SecurityFinding:
        """Check Git history for common credential patterns."""

        matches = self._git_history_matches()

        return SecurityFinding(
            check="git_history_secrets",
            status="ACTION_REQUIRED" if matches else "PASS",
            summary=(
                "No common credential patterns were detected in Git history."
                if not matches
                else "Potential credential patterns were detected in Git history."
            ),
            details={
                "matches": matches,
                "match_count": len(matches),
            },
        )

    def _check_git_state(self) -> SecurityFinding:
        git_dir = self.project_root / ".git"

        if not git_dir.exists():
            return SecurityFinding(
                check="git_state",
                status="REVIEW",
                summary="RichardLab is not currently detected as a Git repository.",
                details={"git_dir": str(git_dir)},
            )

        result = subprocess.run(
            ["git", "-C", str(self.project_root), "status", "--short"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            return SecurityFinding(
                check="git_state",
                status="REVIEW",
                summary="Git state could not be inspected.",
                details={"error": result.stderr.strip()},
            )

        changed = [
            line
            for line in result.stdout.splitlines()
            if line.strip()
        ]

        return SecurityFinding(
            check="git_state",
            status="REVIEW" if changed else "PASS",
            summary=(
                "RichardLab working tree is clean."
                if not changed
                else "RichardLab has uncommitted or untracked changes."
            ),
            details={
                "changed_count": len(changed),
                "changed": changed,
            },
        )

    @staticmethod
    def _listening_sockets() -> list[dict[str, str]]:
        commands = [
            ["sudo", "-n", "ss", "-lntpH"],
            ["ss", "-lntpH"],
        ]

        result = None

        for command in commands:
            try:
                candidate = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    check=False,
                )
            except OSError:
                continue

            if candidate.returncode == 0:
                result = candidate
                break

        if result is None:
            return []

        listeners: list[dict[str, str]] = []

        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) < 6:
                continue

            local = parts[3]
            process = " ".join(parts[5:])
            if "users:((\"" in process:
                process = process.split("users:((\"", 1)[1].split("\"", 1)[0]

            address, _, port = local.rpartition(":")

            listeners.append(
                {
                    "address": address.strip("[]"),
                    "port": port,
                    "process": process,
                }
            )

        return listeners


def main() -> int:
    report = SecurityAudit().run()
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return 0 if report.status != "ACTION_REQUIRED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
