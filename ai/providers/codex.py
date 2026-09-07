import shutil
import subprocess
import time

from .base import AIProvider, AIResponse


class CodexProvider(AIProvider):
    name = "codex"

    def __init__(self, config=None):
        config = config or {}

        self.command = config.get(
            "command",
            "codex"
        )

        self.timeout = config.get(
            "timeout_seconds",
            300
        )

    def health(self):
        executable = shutil.which(self.command)

        if not executable:
            return {
                "provider": self.name,
                "status": "UNAVAILABLE",
                "reason": "codex executable not found"
            }

        return {
            "provider": self.name,
            "status": "READY",
            "command": executable
        }

    def ask(self, prompt, system=None):
        if system:
            prompt = f"{system}\n\n{prompt}"

        start = time.time()

        result = subprocess.run(
            [
                self.command,
                "exec",
                "--",
                prompt
            ],
            capture_output=True,
            text=True,
            timeout=self.timeout
        )

        elapsed = time.time() - start

        if result.returncode != 0:
            raise RuntimeError(
                result.stderr.strip()
                or f"codex exited with {result.returncode}"
            )

        return AIResponse(
            text=result.stdout.strip(),
            provider=self.name,
            model="codex-cli",
            elapsed_seconds=elapsed,
            metadata={
                "returncode": result.returncode
            }
        )
