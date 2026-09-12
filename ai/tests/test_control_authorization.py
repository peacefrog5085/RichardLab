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
    from ai.hive.control import execute_plan, _AUTHORIZED_ACTIONS

    for action in _AUTHORIZED_ACTIONS:
        plan = ActionPlan(action=action)
        result = execute_plan(plan)

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
