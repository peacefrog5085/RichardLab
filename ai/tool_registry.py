#!/usr/bin/env python3

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    function: Callable[..., Any]
    category: str = "general"
    safety: str = "read_only"


TOOLS: dict[str, Tool] = {}


def register(
    name: str,
    description: str,
    function: Callable[..., Any],
    category: str = "general",
    safety: str = "read_only",
):
    if name in TOOLS:
        raise ValueError(
            f"Tool already registered: {name}"
        )

    TOOLS[name] = Tool(
        name=name,
        description=description,
        function=function,
        category=category,
        safety=safety,
    )


def list_tools():
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "category": tool.category,
            "safety": tool.safety,
        }
        for tool in TOOLS.values()
    ]


def get_tool(name: str) -> Tool:
    if name not in TOOLS:
        raise ValueError(
            f"Unknown tool: {name}"
        )

    return TOOLS[name]


def call_tool(name: str, **kwargs):
    tool = get_tool(name)

    return tool.function(**kwargs)
