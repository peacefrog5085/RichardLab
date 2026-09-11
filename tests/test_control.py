from ai.hive.control import (
    ActionPlan,
    ActionResult,
    Decision,
    StateSnapshot,
    decide,
    plan_for,
    state_from_heartbeat,
    verify,
)


def test_stable_state_produces_no_action():
    state = StateSnapshot(attention="NONE")

    decision = decide(state)
    plan = plan_for(decision)

    assert decision.decision == "NO_ACTION"
    assert plan.action == "none"


def test_review_state_produces_review_decision():
    state = StateSnapshot(
        attention="REVIEW",
        changes=(
            {
                "category": "git",
                "field": "commit",
                "previous": "old",
                "current": "new",
                "severity": "REVIEW",
            },
        ),
    )

    decision = decide(state)
    plan = plan_for(decision)

    assert decision.decision == "REVIEW_STATE_CHANGE"
    assert plan.action == "inspect_state_change"
    assert plan.verification == "change_explained"


def test_critical_state_produces_action():
    state = StateSnapshot(attention="ACTION")

    decision = decide(state)
    plan = plan_for(decision)

    assert decision.decision == "REVIEW_CRITICAL_STATE"
    assert plan.action == "inspect_lab_status"


def test_heartbeat_becomes_control_state():
    heartbeat = {
        "attention": "WATCH",
        "changes": [
            {
                "category": "experiments",
                "field": "value",
                "previous": 14,
                "current": 15,
                "severity": "WATCH",
            }
        ],
        "snapshot": {
            "experiments": 15,
            "knowledge_records": 7,
        },
    }

    state = state_from_heartbeat(heartbeat)

    assert state.attention == "WATCH"
    assert len(state.changes) == 1
    assert state.observations["experiments"] == 15


def test_successful_action_can_be_verified():
    plan = ActionPlan(
        action="inspect_lab_status",
        expected_result="current lab state",
        verification="status_observed",
    )

    result = ActionResult(
        status="SUCCESS",
        result={"lab": "RichardLab"},
    )

    verified = verify(plan, result)

    assert verified.verified is True
    assert verified.status == "SUCCESS"
