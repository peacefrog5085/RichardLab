#!/usr/bin/env python3

import re


STATUS_PATTERNS = [
    r"\bstatus\b",
    r"\bhealth\b",
    r"\bhealthy\b",
    r"\bhow is the lab\b",
    r"\bis the lab ok\b",
]

LIST_EXPERIMENT_PATTERNS = [
    r"\blist\b.*\bexperiments?\b",
    r"\bwhat experiments\b",
    r"\bwhich experiments\b",
    r"\bshow me (all|the) experiments?\b",
    r"\bwhat\b.*\bexperiments?\b.*\bexist\b",
]

FAMILY_EXPERIMENT_PATTERNS = [
    r"\bfamily\b.*\bexperiment\b",
    r"\bexperiment\b.*\bfamily\b",
    r"\brelated\b.*\bexperiments?\b",
    r"\bexperiments?\b.*\brelated\b",
]

INSPECT_EXPERIMENT_PATTERNS = [
    r"\binspect\b.*\bexperiment\b",
    r"\bdetails?\b.*\bexperiment\b",
    r"\bshow\b.*\bdetails?\b.*\bexperiment\b",
    r"\bshow\b.*\bexperiment[- ]?\d+[a-z]?\b",
]

REASONING_PATTERNS = [
    r"\bwhy\b",
    r"\bhow\b",
    r"\banaly[sz]e\b",
    r"\bexplain\b",
    r"\bcompare\b",
    r"\brelationship\b",
    r"\bchanged?\b",
    r"\bdifference\b",
]


def matches_any(text: str, patterns: list[str]) -> bool:
    return any(
        re.search(pattern, text)
        for pattern in patterns
    )


def classify(prompt: str) -> str:
    text = prompt.lower().strip()

    if matches_any(text, STATUS_PATTERNS):
        return "system_status"

    if matches_any(text, REASONING_PATTERNS):
        return "ai_reasoning"

    if matches_any(text, FAMILY_EXPERIMENT_PATTERNS):
        return "experiment_family"

    if matches_any(text, INSPECT_EXPERIMENT_PATTERNS):
        return "experiment_inspect"

    if matches_any(text, LIST_EXPERIMENT_PATTERNS):
        return "experiment_list"

    return "ai_reasoning"


def can_answer_locally(prompt: str) -> bool:
    return classify(prompt) != "ai_reasoning"
