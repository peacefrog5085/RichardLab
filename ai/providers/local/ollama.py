#!/usr/bin/env python3

from __future__ import annotations

import json
import urllib.error
import urllib.request

from ai.providers.base import AIProvider, AIRequest, AIResponse


class OllamaProvider(AIProvider):
    name = "ollama"

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434",
        default_model: str = "llama3.2:3b",
    ):
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model

    def available(self) -> bool:
        try:
            request = urllib.request.Request(
                f"{self.base_url}/api/tags",
                method="GET",
            )

            with urllib.request.urlopen(request, timeout=2):
                return True

        except (urllib.error.URLError, TimeoutError, OSError):
            return False

    def generate(self, request: AIRequest) -> AIResponse:
        model = request.model or self.default_model

        payload = {
            "model": model,
            "prompt": request.prompt,
            "system": request.system or "",
            "stream": False,
            "options": {
                "temperature": request.temperature,
            },
        }

        data = json.dumps(payload).encode("utf-8")

        http_request = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                http_request,
                timeout=120,
            ) as response:
                result = json.loads(response.read().decode("utf-8"))

            return AIResponse(
                text=result.get("response", ""),
                provider=self.name,
                model=model,
                success=True,
                metadata=result,
            )

        except Exception as exc:
            return AIResponse(
                text="",
                provider=self.name,
                model=model,
                success=False,
                metadata={"error": str(exc)},
            )
