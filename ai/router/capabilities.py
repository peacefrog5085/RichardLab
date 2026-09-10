#!/usr/bin/env python3

"""
Deterministic mapping from RichardLab routes to AI worker capabilities.

This module does not inspect prompts, execute workers, or contact providers.
It only translates an already-classified route into the capability required
for that route.
"""

ROUTE_CAPABILITIES = {
    "ai_reasoning": "reasoning",
}


def capability_for_route(route: str) -> str | None:
    """Return the AI worker capability required by a route."""
    return ROUTE_CAPABILITIES.get(route)
