import json
import time
import urllib.request

from .base import AIProvider, AIResponse


class OllamaProvider(AIProvider):
    name = "ollama"

    def __init__(self, config):
        self.base_url = config.get(
            "base_url",
            "http://localhost:11434"
        ).rstrip("/")

        self.model = config.get(
            "model",
            "gemma2:2b"
        )

        self.timeout = config.get(
            "timeout_seconds",
            60
        )

        self.keep_alive = config.get(
            "keep_alive",
            "10m"
        )

        self.num_thread = config.get(
            "num_thread",
            4
        )

        self.num_ctx = config.get(
            "num_ctx",
            1024
        )

        self.num_predict = config.get(
            "num_predict",
            512
        )

    def health(self):
        start = time.time()

        try:
            request = urllib.request.Request(
                f"{self.base_url}/api/tags",
                method="GET"
            )

            with urllib.request.urlopen(
                request,
                timeout=5
            ) as response:
                data = json.loads(
                    response.read().decode("utf-8")
                )

            models = [
                model.get("name")
                for model in data.get("models", [])
            ]

            return {
                "provider": self.name,
                "status": "READY",
                "model": self.model,
                "models": models,
                "elapsed_seconds": round(
                    time.time() - start,
                    3
                )
            }

        except Exception as exc:
            return {
                "provider": self.name,
                "status": "OFFLINE",
                "error": str(exc),
                "elapsed_seconds": round(
                    time.time() - start,
                    3
                )
            }

    def ask(self, prompt, system=None):
        if system:
            prompt = f"{system}\n\n{prompt}"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": self.keep_alive,
            "options": {
                "num_thread": self.num_thread,
                "num_ctx": self.num_ctx,
                "num_predict": self.num_predict
            }
        }

        data = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=data,
            headers={
                "Content-Type": "application/json"
            },
            method="POST"
        )

        start = time.time()

        with urllib.request.urlopen(
            request,
            timeout=self.timeout
        ) as response:
            result = json.loads(
                response.read().decode("utf-8")
            )

        elapsed = time.time() - start

        return AIResponse(
            text=result.get("response", "").strip(),
            provider=self.name,
            model=self.model,
            elapsed_seconds=elapsed,
            metadata={
                "total_duration": result.get(
                    "total_duration"
                ),
                "load_duration": result.get(
                    "load_duration"
                ),
                "prompt_eval_count": result.get(
                    "prompt_eval_count"
                ),
                "eval_count": result.get(
                    "eval_count"
                )
            }
        )
