#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AIRequest:
    prompt: str
    system: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.2
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AIResponse:
    text: str
    provider: str
    model: str
    success: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class AIProvider:
    """
    Common interface for every RichardLab AI brain.

    Providers may be local or cloud-based, but the Hive
    should not need to know how a particular provider works.
    """

    name = "unknown"

    def available(self) -> bool:
        return False

    def generate(self, request: AIRequest) -> AIResponse:
        raise NotImplementedError
