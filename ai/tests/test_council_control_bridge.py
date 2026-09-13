from ai.hive.control import (
    Decision,
    council_recommendation_to_decision,
)


def test_council_recommendation_becomes_control_decision():
    recommendation = {
        "decision": "REVIEW_STATE_CHANGE",
        "reason": "Council identified a meaningful state change.",
        "capability": None,
    }

    decision = council_recommendation_to_decision(recommendation)

    assert isinstance(decision, Decision)
    assert decision.decision == "REVIEW_STATE_CHANGE"
    assert decision.reason == "Council identified a meaningful state change."


def test_council_recommendation_does_not_execute():
    recommendation = {
        "decision": "REVIEW_STATE_CHANGE",
        "reason": "Review required.",
    }

    decision = council_recommendation_to_decision(recommendation)

    assert decision.capability is None


def test_unknown_council_decision_is_review():
    recommendation = {
        "decision": "DO_SOMETHING_DANGEROUS",
        "reason": "The Council suggested it.",
    }

    decision = council_recommendation_to_decision(recommendation)

    assert decision.decision == "REVIEW_STATE_CHANGE"
    assert "unknown" in decision.reason.lower()


def test_missing_council_recommendation_is_review():
    decision = council_recommendation_to_decision({})

    assert decision.decision == "REVIEW_STATE_CHANGE"


def test_extract_explicit_council_recommendation():
    from ai.hive.control import extract_council_recommendation

    synthesis = """
Known facts:
- The system observed a meaningful state change.

Unknowns:
- The cause is not yet established.

RECOMMENDATION: REVIEW_STATE_CHANGE
"""

    recommendation = extract_council_recommendation(synthesis)

    assert recommendation["decision"] == "REVIEW_STATE_CHANGE"


def test_synthesis_without_explicit_recommendation_returns_review():
    from ai.hive.control import extract_council_recommendation

    synthesis = """
Known facts:
- Something changed.

Strong inferences:
- More investigation may be useful.
"""

    recommendation = extract_council_recommendation(synthesis)

    assert recommendation["decision"] == "REVIEW_STATE_CHANGE"
    assert "explicit" in recommendation["reason"].lower()


def test_unknown_explicit_recommendation_does_not_create_action():
    from ai.hive.control import extract_council_recommendation

    synthesis = """
RECOMMENDATION: DELETE_EVERYTHING
"""

    recommendation = extract_council_recommendation(synthesis)

    assert recommendation["decision"] == "REVIEW_STATE_CHANGE"
    assert "unknown" in recommendation["reason"].lower()


def test_recommendation_extraction_does_not_execute():
    from ai.hive.control import extract_council_recommendation

    synthesis = "RECOMMENDATION: REVIEW_STATE_CHANGE"

    recommendation = extract_council_recommendation(synthesis)

    assert recommendation["decision"] == "REVIEW_STATE_CHANGE"
    assert recommendation["capability"] is None
