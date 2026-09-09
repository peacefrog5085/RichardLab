#!/usr/bin/env python3

"""
RichardLab Compass v3

Purpose:
    Explore possible explanations without treating them as facts.

Core principles:
    Never assume the map is the territory.
    Explore freely. Conclude carefully.
    RichardLab may question a definition, but may never silently redefine it.

Epistemic states:
    FACT
    INFERENCE
    CANDIDATE_HYPOTHESIS
    SUPPORTED
    CONTRADICTED
    UNRESOLVED
    UNKNOWN

The Compass generates investigative possibilities.
Evidence determines their status.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


COMPASS_VERSION = "3.0"

COMPASS_PRINCIPLE = "Never assume the map is the territory."
COMPASS_RULE = "Explore freely. Conclude carefully."

EPISTEMIC_STATES = (
    "FACT",
    "INFERENCE",
    "CANDIDATE_HYPOTHESIS",
    "SUPPORTED",
    "CONTRADICTED",
    "UNRESOLVED",
    "UNKNOWN",
)


@dataclass(frozen=True)
class CompassDirection:
    name: str
    question: str
    purpose: str


DIRECTIONS = (
    CompassDirection(
        "forward",
        "What follows if the observation or hypothesis is correct?",
        "Explore consequences and predictions.",
    ),
    CompassDirection(
        "backward",
        "What conditions could have produced the observation?",
        "Search for possible causes and prerequisites.",
    ),
    CompassDirection(
        "inside_out",
        "What assumptions are contained within the observation?",
        "Expose definitions, premises, measurements, and framing.",
    ),
    CompassDirection(
        "outside_in",
        "What external conditions could influence the observation?",
        "Examine environmental and systemic factors.",
    ),
    CompassDirection(
        "inversion",
        "What happens if the central assumption is reversed?",
        "Search for counterexamples and alternative explanations.",
    ),
    CompassDirection(
        "zero_state",
        "What happens when the presumed factor is removed?",
        "Establish a baseline or control.",
    ),
    CompassDirection(
        "one_state",
        "What happens when the presumed factor is isolated or maximized?",
        "Examine the strongest identifiable expression of a factor.",
    ),
    CompassDirection(
        "simultaneous",
        "Can apparently contradictory states coexist under different conditions?",
        "Test whether contradiction is contextual.",
    ),
    CompassDirection(
        "recursive",
        "Does observation or measurement alter the system?",
        "Identify observer effects and feedback.",
    ),
    CompassDirection(
        "unknown",
        "What cannot currently be determined?",
        "Preserve uncertainty and identify missing evidence.",
    ),
)


@dataclass(frozen=True)
class Hypothesis:
    hypothesis_id: str
    direction: str
    statement: str
    prediction: str
    supporting_evidence: str
    contradicting_evidence: str
    variable_to_change: str
    variables_to_control: str
    discriminating_test: str
    status: str = "CANDIDATE_HYPOTHESIS"


def _hypothesis(
    *,
    hypothesis_id: str,
    direction: str,
    statement: str,
    prediction: str,
    supporting: str,
    contradicting: str,
    change: str,
    controls: str,
    test: str,
) -> dict[str, Any]:
    """Create one candidate hypothesis using explicit named fields."""

    return asdict(
        Hypothesis(
            hypothesis_id=hypothesis_id,
            direction=direction,
            statement=statement,
            prediction=prediction,
            supporting_evidence=supporting,
            contradicting_evidence=contradicting,
            variable_to_change=change,
            variables_to_control=controls,
            discriminating_test=test,
        )
    )


def generate_hypotheses(observation: str) -> list[dict[str, Any]]:
    """
    Generate deterministic candidate hypotheses.

    These are investigative structures, not conclusions.
    No evidence is invented here.
    """

    if not isinstance(observation, str):
        raise TypeError("observation must be a string")

    observation = observation.strip()

    if not observation:
        raise ValueError("observation cannot be empty")

    common_control = (
        "All other known relevant conditions, definitions, "
        "measurements, and environmental factors."
    )

    return [
        _hypothesis(
            hypothesis_id="H1",
            direction="forward",
            statement=(
                "The observed result has a reproducible consequence "
                "under the stated conditions."
            ),
            prediction=(
                "Repeating the conditions produces the predicted consequence."
            ),
            supporting=(
                "Repeated observations matching the prediction."
            ),
            contradicting=(
                "Repeated observations failing to produce the prediction."
            ),
            change="The condition believed to produce the consequence.",
            controls=common_control,
            test=(
                "Repeat the observation under controlled conditions "
                "and measure the predicted consequence."
            ),
        ),

        _hypothesis(
            hypothesis_id="H2",
            direction="backward",
            statement=(
                "One or more identifiable prior conditions may have "
                "produced the observation."
            ),
            prediction=(
                "Reproducing those conditions reproduces the observation."
            ),
            supporting=(
                "The observation is reproduced when the proposed prior "
                "conditions are recreated."
            ),
            contradicting=(
                "The observation occurs without the proposed prior conditions "
                "or cannot be reproduced when they are recreated."
            ),
            change="The suspected prerequisite condition.",
            controls=common_control,
            test=(
                "Reconstruct the suspected prerequisite conditions "
                "and repeat the observation."
            ),
        ),

        _hypothesis(
            hypothesis_id="H3",
            direction="inside_out",
            statement=(
                "The observation may depend on an assumption, definition, "
                "representation, or measurement method."
            ),
            prediction=(
                "Changing the identified assumption, definition, "
                "representation, or measurement method changes the result."
            ),
            supporting=(
                "The result changes when the identified assumption or "
                "measurement method is changed."
            ),
            contradicting=(
                "The result remains unchanged when the identified assumption "
                "or measurement method is changed."
            ),
            change="One explicitly identified assumption or measurement method.",
            controls=common_control,
            test=(
                "Change exactly one identified assumption or measurement "
                "method while holding the target system constant."
            ),
        ),

        _hypothesis(
            hypothesis_id="H4",
            direction="outside_in",
            statement=(
                "An external condition may influence the observed result."
            ),
            prediction=(
                "Changing the external condition changes the result."
            ),
            supporting=(
                "The result changes when the identified external condition "
                "changes."
            ),
            contradicting=(
                "The result remains unchanged when the external condition "
                "changes."
            ),
            change="One explicitly identified external condition.",
            controls=(
                "The target system and all other known relevant conditions."
            ),
            test=(
                "Repeat the observation under controlled variations "
                "of the external condition."
            ),
        ),

        _hypothesis(
            hypothesis_id="H5",
            direction="inversion",
            statement=(
                "The apparent explanation may depend on an assumption "
                "that can be reversed."
            ),
            prediction=(
                "Reversing the assumption produces a distinguishable result."
            ),
            supporting=(
                "The predicted difference appears when the assumption "
                "is reversed."
            ),
            contradicting=(
                "Reversing the assumption produces no distinguishable result."
            ),
            change="The central assumption being investigated.",
            controls=common_control,
            test=(
                "Repeat the test with the central assumption explicitly reversed."
            ),
        ),

        _hypothesis(
            hypothesis_id="H6",
            direction="zero_state",
            statement=(
                "The presumed factor may be necessary for the observed effect."
            ),
            prediction=(
                "Removing the factor reduces or eliminates the effect."
            ),
            supporting=(
                "The effect decreases or disappears when the factor is removed."
            ),
            contradicting=(
                "The effect remains unchanged when the factor is removed."
            ),
            change="Presence versus absence of the suspected factor.",
            controls=common_control,
            test=(
                "Compare controlled runs with and without the suspected factor."
            ),
        ),

        _hypothesis(
            hypothesis_id="H7",
            direction="one_state",
            statement=(
                "The presumed factor may influence the magnitude or character "
                "of the result."
            ),
            prediction=(
                "Increasing or isolating the factor produces a measurable change."
            ),
            supporting=(
                "A measurable relationship appears between the factor "
                "and the observed result."
            ),
            contradicting=(
                "Changing the factor produces no measurable change."
            ),
            change="Magnitude or isolation of the suspected factor.",
            controls=common_control,
            test=(
                "Compare multiple controlled levels of the factor "
                "and measure the resulting changes."
            ),
        ),

        _hypothesis(
            hypothesis_id="H8",
            direction="simultaneous",
            statement=(
                "Apparently contradictory observations may each be valid "
                "under different conditions or representations."
            ),
            prediction=(
                "Each result is reproducible when its associated conditions "
                "are restored."
            ),
            supporting=(
                "Both observations are independently reproducible "
                "under their documented conditions."
            ),
            contradicting=(
                "One or both observations cannot be reproduced under "
                "their documented conditions."
            ),
            change="The relevant condition or representation.",
            controls=common_control,
            test=(
                "Reproduce both states while recording the exact conditions, "
                "definitions, representations, and measurements for each."
            ),
        ),

        _hypothesis(
            hypothesis_id="H9",
            direction="recursive",
            statement=(
                "The measurement or observation process may affect "
                "the system being measured."
            ),
            prediction=(
                "Changing the measurement process changes the result."
            ),
            supporting=(
                "Independent measurement methods produce systematically "
                "different results."
            ),
            contradicting=(
                "Independent measurement methods produce the same result "
                "within established measurement uncertainty."
            ),
            change="Measurement method or measurement intensity.",
            controls=(
                "The target system and all other known relevant conditions."
            ),
            test=(
                "Repeat the observation using independent measurement methods "
                "and compare the results."
            ),
        ),

        _hypothesis(
            hypothesis_id="H10",
            direction="unknown",
            statement=(
                "The available evidence may be insufficient to distinguish "
                "competing explanations."
            ),
            prediction=(
                "Additional controlled evidence separates at least "
                "two competing explanations."
            ),
            supporting=(
                "The currently available evidence cannot distinguish "
                "the competing explanations."
            ),
            contradicting=(
                "Existing evidence already distinguishes the competing "
                "explanations sufficiently."
            ),
            change="The minimum missing evidence required for discrimination.",
            controls=(
                "Everything already established by the available evidence."
            ),
            test=(
                "Identify and collect the smallest evidence set capable "
                "of distinguishing the competing explanations."
            ),
        ),
    ]


def orient(observation: str) -> dict[str, Any]:
    """
    Orient an observation without determining its truth.
    """

    if not isinstance(observation, str):
        raise TypeError("observation must be a string")

    observation = observation.strip()

    if not observation:
        raise ValueError("observation cannot be empty")

    hypotheses = generate_hypotheses(observation)

    return {
        "compass_version": COMPASS_VERSION,
        "principle": COMPASS_PRINCIPLE,
        "rule": COMPASS_RULE,
        "observation": observation,
        "truth_status": "UNDETERMINED",
        "hypotheses": hypotheses,
    }


def evaluate_hypothesis(
    hypothesis: dict[str, Any],
    supporting_evidence: list[str] | None = None,
    contradicting_evidence: list[str] | None = None,
) -> dict[str, Any]:
    """
    Evaluate a hypothesis using explicitly supplied evidence.

    This function does not invent evidence.

    Rules:
        support only -> SUPPORTED
        contradiction only -> CONTRADICTED
        both -> UNRESOLVED
        neither -> UNRESOLVED
    """

    supporting = list(supporting_evidence or [])
    contradicting = list(contradicting_evidence or [])

    if supporting and contradicting:
        status = "UNRESOLVED"
    elif supporting:
        status = "SUPPORTED"
    elif contradicting:
        status = "CONTRADICTED"
    else:
        status = "UNRESOLVED"

    result = dict(hypothesis)

    result["supporting_evidence"] = supporting
    result["contradicting_evidence"] = contradicting
    result["status"] = status

    return result


def format_orientation(result: dict[str, Any]) -> str:
    lines = [
        "===== RICHARDLAB COMPASS v3 =====",
        f"PRINCIPLE: {result['principle']}",
        f"RULE: {result['rule']}",
        "",
        f"OBSERVATION: {result['observation']}",
        f"TRUTH STATUS: {result['truth_status']}",
        "",
    ]

    for hypothesis in result["hypotheses"]:
        lines.extend(
            [
                f"{hypothesis['hypothesis_id']} [{hypothesis['direction']}]",
                f"  Hypothesis: {hypothesis['statement']}",
                f"  Prediction: {hypothesis['prediction']}",
                f"  Support:    {hypothesis['supporting_evidence']}",
                f"  Contradict: {hypothesis['contradicting_evidence']}",
                f"  Change:     {hypothesis['variable_to_change']}",
                f"  Control:    {hypothesis['variables_to_control']}",
                f"  Test:       {hypothesis['discriminating_test']}",
                f"  Status:     {hypothesis['status']}",
                "",
            ]
        )

    return "\n".join(lines).rstrip()


def direction(name: str) -> dict[str, str]:
    normalized = (
        name.strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
    )

    for item in DIRECTIONS:
        if item.name == normalized:
            return asdict(item)

    valid = ", ".join(item.name for item in DIRECTIONS)
    raise ValueError(
        f"Unknown Compass direction '{name}'. Valid directions: {valid}"
    )


def directions() -> list[dict[str, str]]:
    return [asdict(item) for item in DIRECTIONS]


__all__ = [
    "COMPASS_VERSION",
    "COMPASS_PRINCIPLE",
    "COMPASS_RULE",
    "EPISTEMIC_STATES",
    "CompassDirection",
    "Hypothesis",
    "DIRECTIONS",
    "directions",
    "direction",
    "generate_hypotheses",
    "orient",
    "evaluate_hypothesis",
    "format_orientation",
]
