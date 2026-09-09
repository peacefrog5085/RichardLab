import json
import shutil
import subprocess
import time

from .base import AIProvider, AIResponse


class GeminiProvider(AIProvider):
    name = "gemini"

    def __init__(self, config=None):
        config = config or {}

        self.command = config.get(
            "command",
            "gemini"
        )

        self.timeout = config.get(
            "timeout_seconds",
            120
        )

    def health(self):
        executable = shutil.which(
            self.command
        )

        if not executable:
            return {
                "provider": self.name,
                "status": "UNAVAILABLE",
                "reason": "gemini executable not found"
            }

        # The Gemini CLI can take longer than a short health-check
        # timeout to respond to --version even when inference works.
        # Executable discovery is therefore the lightweight health check.
        return {
            "provider": self.name,
            "status": "READY",
            "command": executable,
            "health_check": "executable_present"
        }

    def ask(self, prompt, system=None):
        if system:
            prompt = (
                f"{system}\n\n"
                f"{prompt}"
            )

        command = [
            self.command,
            "-p",
            prompt,
            "--output-format",
            "json"
        ]

        start = time.time()

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=self.timeout
        )

        elapsed = time.time() - start

        raw = result.stdout.strip()

        data = {}

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            pass

        if result.returncode != 0:
            error = data.get(
                "error",
                {}
            )

            message = (
                error.get("message")
                if isinstance(error, dict)
                else None
            )

            message = (
                message
                or result.stderr.strip()
                or raw
                or f"Gemini exited with "
                   f"{result.returncode}"
            )

            lowered = message.lower()

            if "quota" in lowered:
                reason = "QUOTA_EXCEEDED"
            elif "authentication" in lowered:
                reason = "AUTH_REQUIRED"
            elif "unauthorized" in lowered:
                reason = "AUTH_REQUIRED"
            else:
                reason = "INFERENCE_ERROR"

            raise RuntimeError(
                f"{reason}: {message}"
            )

        text = data.get(
            "response",
            raw
        ).strip()

        return AIResponse(
            text=text,
            provider=self.name,
            model="gemini-cli",
            elapsed_seconds=elapsed,
            metadata={
                "session_id": data.get(
                    "session_id"
                ),
                "stats": data.get(
                    "stats"
                )
            }
        )
