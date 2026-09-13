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
