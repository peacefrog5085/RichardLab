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




def test_hive_council_result_can_flow_into_control_decision():
    from types import SimpleNamespace

    from ai.hive.control import (
        council_recommendation_to_decision,
        extract_council_recommendation,
    )
    from ai.hive.core import HiveCore

    class FakeCouncil:
        def deliberate(self, question):
            return SimpleNamespace(
                question=question,
                synthesis="RECOMMENDATION: REVIEW_STATE_CHANGE",
            )

    hive = object.__new__(HiveCore)
    hive.council = FakeCouncil()

    result = hive.dispatch_council("What changed?")

    recommendation = extract_council_recommendation(result.synthesis)
    decision = council_recommendation_to_decision(recommendation)

    assert result.question == "What changed?"
    assert decision.decision == "REVIEW_STATE_CHANGE"
    assert decision.capability is None


def test_hive_council_result_does_not_execute_control_action():
    from types import SimpleNamespace

    from ai.hive.core import HiveCore

    class FakeCouncil:
        def deliberate(self, question):
            return SimpleNamespace(
                question=question,
                synthesis="RECOMMENDATION: REVIEW_STATE_CHANGE",
            )

    hive = object.__new__(HiveCore)
    hive.council = FakeCouncil()

    result = hive.dispatch_council("Review the state.")

    assert result.synthesis == "RECOMMENDATION: REVIEW_STATE_CHANGE"


def test_council_recommendation_reaches_action_plan():
    from ai.hive.control import (
        council_recommendation_to_decision,
        extract_council_recommendation,
        plan_for,
    )

    synthesis = "RECOMMENDATION: REVIEW_STATE_CHANGE"

    recommendation = extract_council_recommendation(synthesis)
    decision = council_recommendation_to_decision(recommendation)
    plan = plan_for(decision)

    assert decision.decision == "REVIEW_STATE_CHANGE"
    assert plan.action == "inspect_state_change"
    assert plan.verification == "change_explained"


def test_council_recommendation_pipeline_does_not_execute():
    from ai.hive.control import (
        council_recommendation_to_decision,
        execute_plan,
        extract_council_recommendation,
        plan_for,
    )

    synthesis = "RECOMMENDATION: REVIEW_STATE_CHANGE"

    recommendation = extract_council_recommendation(synthesis)
    decision = council_recommendation_to_decision(recommendation)
    plan = plan_for(decision)

    assert plan.action == "inspect_state_change"

    # Constructing the plan must not execute it.
    # Execution remains an explicit later operation.
    assert decision.capability is None


def test_state_becomes_control_cycle_without_execution():
    from ai.hive.control import (
        ControlCycle,
        StateSnapshot,
        build_control_cycle,
    )

    state = StateSnapshot(
        attention="REVIEW",
        changes=({"type": "test_change"},),
        observations={"source": "test"},
    )

    cycle = build_control_cycle(state)

    assert isinstance(cycle, ControlCycle)
    assert cycle.state == state
    assert cycle.decision.decision == "REVIEW_STATE_CHANGE"
    assert cycle.plan.action == "inspect_state_change"
    assert cycle.result is None


def test_control_cycle_preserves_no_action_state():
    from ai.hive.control import (
        StateSnapshot,
        build_control_cycle,
    )

    state = StateSnapshot(attention="NONE")

    cycle = build_control_cycle(state)

    assert cycle.decision.decision == "NO_ACTION"
    assert cycle.plan.action == "none"
    assert cycle.result is None


def test_council_recommendation_builds_complete_control_cycle():
    from ai.hive.control import (
        StateSnapshot,
        build_control_cycle,
        council_recommendation_to_decision,
        extract_council_recommendation,
    )

    state = StateSnapshot(
        attention="REVIEW",
        changes=({"type": "council_detected_change"},),
        observations={"source": "council"},
    )

    synthesis = "RECOMMENDATION: REVIEW_STATE_CHANGE"

    recommendation = extract_council_recommendation(synthesis)
    council_decision = council_recommendation_to_decision(recommendation)
    cycle = build_control_cycle(state)

    assert council_decision.decision == "REVIEW_STATE_CHANGE"
    assert cycle.state == state
    assert cycle.decision.decision == "REVIEW_STATE_CHANGE"
    assert cycle.plan.action == "inspect_state_change"
    assert cycle.result is None


def test_council_recommendation_cannot_bypass_state_control():
    from ai.hive.control import (
        StateSnapshot,
        build_control_cycle,
        council_recommendation_to_decision,
        extract_council_recommendation,
    )

    state = StateSnapshot(attention="NONE")
    synthesis = "RECOMMENDATION: REVIEW_STATE_CHANGE"

    recommendation = extract_council_recommendation(synthesis)
    council_decision = council_recommendation_to_decision(recommendation)
    cycle = build_control_cycle(state)

    assert council_decision.decision == "REVIEW_STATE_CHANGE"

    # The Council recommendation does not directly replace the
    # deterministic state-derived control decision.
    assert cycle.decision.decision == "NO_ACTION"
    assert cycle.plan.action == "none"
    assert cycle.result is None
