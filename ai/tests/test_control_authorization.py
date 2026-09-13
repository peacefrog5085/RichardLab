from ai.hive.control import ActionPlan, authorize_plan


def test_none_action_is_authorized():
    plan = ActionPlan(action="none")

    decision = authorize_plan(plan)

    assert decision.status == "AUTHORIZED"
    assert decision.action == "none"


def test_known_deterministic_action_is_authorized():
    plan = ActionPlan(action="inspect_lab_status")

    decision = authorize_plan(plan)

    assert decision.status == "AUTHORIZED"
    assert decision.action == "inspect_lab_status"


def test_unknown_action_is_blocked():
    plan = ActionPlan(action="delete_everything")

    decision = authorize_plan(plan)

    assert decision.status == "BLOCKED"
    assert decision.action == "delete_everything"
    assert "not authorized" in decision.reason.lower()


def test_authorization_does_not_execute_action(monkeypatch):
    executed = False

    def fake_call_tool(*args, **kwargs):
        nonlocal executed
        executed = True
        raise AssertionError("authorization must not execute tools")

    monkeypatch.setattr("ai.hive.control.call_tool", fake_call_tool)

    plan = ActionPlan(action="inspect_lab_status")
    decision = authorize_plan(plan)

    assert decision.status == "AUTHORIZED"
    assert executed is False


def test_execute_plan_blocks_unauthorized_action():
    from ai.hive.control import execute_plan

    plan = ActionPlan(action="delete_everything")

    result = execute_plan(plan)

    assert result.status == "BLOCKED"
    assert result.verified is False
    assert result.evidence["action"] == "delete_everything"


def test_execute_plan_does_not_execute_unauthorized_tool(monkeypatch):
    from ai.hive.control import execute_plan

    executed = False

    def fake_call_tool(*args, **kwargs):
        nonlocal executed
        executed = True
        raise AssertionError("unauthorized action reached tool execution")

    monkeypatch.setattr("ai.hive.control.call_tool", fake_call_tool)

    plan = ActionPlan(action="delete_everything")
    result = execute_plan(plan)

    assert result.status == "BLOCKED"
    assert executed is False


def test_authorized_actions_have_executors():
    from ai.hive.control import (
        execute_plan,
        _AUTHORIZED_ACTIONS,
        authorize_plan,
    )

    for action in _AUTHORIZED_ACTIONS:
        plan = ActionPlan(action=action)
        authorization = authorize_plan(plan)
        result = execute_plan(plan, authorization=authorization)

        assert result.status != "BLOCKED", (
            f"Authorized action has no executor: {action}"
        )


def test_executor_does_not_accept_actions_outside_authorization():
    from ai.hive.control import execute_plan

    unsupported = ActionPlan(action="delete_everything")
    result = execute_plan(unsupported)

    authorization = authorize_plan(unsupported)

    assert authorization.status == "BLOCKED"
    assert result.status == "BLOCKED"


def test_control_cycle_can_record_authorization_decision():
    from ai.hive.control import (
        ActionPlan,
        ControlCycle,
        Decision,
        StateSnapshot,
        authorize_plan,
    )

    state = StateSnapshot(attention="REVIEW")
    decision = Decision(
        objective="understand the detected state change",
        decision="REVIEW_STATE_CHANGE",
        reason="A meaningful change requires review.",
    )
    plan = ActionPlan(action="inspect_state_change")

    authorization = authorize_plan(plan)

    cycle = ControlCycle(
        state=state,
        decision=decision,
        plan=plan,
        authorization=authorization,
    )

    assert cycle.authorization.status == "AUTHORIZED"
    assert cycle.result is None


def test_blocked_control_cycle_records_blocked_authorization():
    from ai.hive.control import (
        ActionPlan,
        ControlCycle,
        Decision,
        StateSnapshot,
        authorize_plan,
    )

    state = StateSnapshot(attention="REVIEW")
    decision = Decision(
        objective="test blocked action",
        decision="REVIEW_STATE_CHANGE",
        reason="Test authorization boundary.",
    )
    plan = ActionPlan(action="delete_everything")

    authorization = authorize_plan(plan)

    cycle = ControlCycle(
        state=state,
        decision=decision,
        plan=plan,
        authorization=authorization,
    )

    assert cycle.authorization.status == "BLOCKED"
    assert cycle.result is None


def test_build_control_cycle_records_authorization():
    from ai.hive.control import (
        StateSnapshot,
        build_control_cycle,
    )

    state = StateSnapshot(attention="REVIEW")

    cycle = build_control_cycle(state)

    assert cycle.authorization is not None
    assert cycle.authorization.status == "AUTHORIZED"
    assert cycle.authorization.action == "inspect_state_change"
    assert cycle.result is None


def test_build_control_cycle_records_blocked_authorization_for_unsupported_plan():
    from ai.hive.control import (
        ActionPlan,
        ControlCycle,
        Decision,
        StateSnapshot,
        authorize_plan,
    )

    state = StateSnapshot(attention="REVIEW")
    decision = Decision(
        objective="test blocked action",
        decision="REVIEW_STATE_CHANGE",
        reason="Test authorization boundary.",
    )
    plan = ActionPlan(action="delete_everything")

    authorization = authorize_plan(plan)

    cycle = ControlCycle(
        state=state,
        decision=decision,
        plan=plan,
        authorization=authorization,
    )

    assert cycle.authorization.status == "BLOCKED"
    assert cycle.authorization.action == "delete_everything"
    assert cycle.result is None




def test_execute_plan_requires_explicit_authorization():
    from ai.hive.control import execute_plan

    plan = ActionPlan(action="inspect_lab_status")

    result = execute_plan(plan, authorization=None)

    assert result.status == "BLOCKED"
    assert result.verified is False
