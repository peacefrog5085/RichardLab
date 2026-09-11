from __future__ import annotations

import os
import time

from openai import OpenAI

from .base import AIProvider, AIRequest, AIResponse


class OpenAIProvider(AIProvider):
    """RichardLab provider for the OpenAI Responses API."""

    name = "openai"

    def __init__(self, config=None):
        config = config or {}

        self.model = config.get(
            "model",
            "gpt-5.6-luna",
        )

        self.timeout = config.get(
            "timeout_seconds",
            120,
        )

        self.api_key_env = config.get(
            "api_key_env",
            "OPENAI_API_KEY",
        )

        self.client = None

        api_key = os.environ.get(self.api_key_env)

        if api_key:
            self.client = OpenAI(
                api_key=api_key,
                timeout=self.timeout,
            )

    def health(self):
        if not os.environ.get(self.api_key_env):
            return {
                "provider": self.name,
                "status": "AUTH_REQUIRED",
                "reason": (
                    f"Environment variable "
                    f"{self.api_key_env} is not set"
                ),
            }

        if self.client is None:
            return {
                "provider": self.name,
                "status": "UNAVAILABLE",
                "reason": "OpenAI client not initialized",
            }

        return {
            "provider": self.name,
            "status": "READY",
            "model": self.model,
            "authentication": "environment",
        }

    def ask(self, prompt, system=None):
        if self.client is None:
            raise RuntimeError(
                f"AUTH_REQUIRED: {self.api_key_env} is not set"
            )

        start = time.time()

        kwargs = {
            "model": self.model,
            "input": prompt,
        }

        if system:
            kwargs["instructions"] = system

        try:
            response = self.client.responses.create(
                **kwargs
            )
        except Exception as exc:
            message = str(exc)

            lowered = message.lower()

            if "401" in lowered or "authentication" in lowered:
                reason = "AUTH_REQUIRED"
            elif "429" in lowered or "rate limit" in lowered:
                reason = "RATE_LIMITED"
            elif "quota" in lowered:
                reason = "QUOTA_EXCEEDED"
            else:
                reason = "INFERENCE_ERROR"

            raise RuntimeError(
                f"{reason}: {message}"
            ) from exc

        elapsed = time.time() - start

        return AIResponse(
            text=response.output_text.strip(),
            provider=self.name,
            model=self.model,
            elapsed_seconds=elapsed,
            metadata={
                "response_id": getattr(
                    response,
                    "id",
                    None,
                ),
            },
        )
