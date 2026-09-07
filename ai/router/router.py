#!/usr/bin/env python3

from __future__ import annotations

from ai.providers.base import AIRequest, AIResponse
from ai.providers.local.ollama import OllamaProvider


class AIRouter:
    """
    RichardLab AI routing layer.

    Current policy:
      1. Prefer local AI when available.
      2. Return a clear failure when no provider is available.

    Cloud providers will be added without changing callers.
    """

    def __init__(self):
        self.local = OllamaProvider()

    def status(self) -> dict:
        return {
            "local": {
                "provider": self.local.name,
                "available": self.local.available(),
                "model": self.local.default_model,
            }
        }

    def ask(self, request: AIRequest) -> AIResponse:
        if self.local.available():
            return self.local.generate(request)

        return AIResponse(
            text="",
            provider="none",
            model="none",
            success=False,
            metadata={
                "error": "No AI provider is currently available."
            },
        )
