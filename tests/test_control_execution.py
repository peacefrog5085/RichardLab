from ai.hive.control import (
    ActionPlan,
    ActionResult,
    execute_plan,
    authorize_plan,
    verify,
)


class FakeHive:
    def __init__(self):
        self.calls = 0

    def heartbeat(self):
        self.calls += 1
        return {
            "attention": "NONE",
            "changes": [],
            "snapshot": {
                "experiments": 14,
                "experiment_families": 10,
            },
        }


def test_none_plan_does_not_execute():
    plan = ActionPlan(
        action="none",
        expected_result="no action required",
        verification="state_remains_stable",
    )

    authorization = authorize_plan(plan)
    result = execute_plan(plan, authorization=authorization)

    assert result.status == "SUCCESS"
    assert result.verified is False

    verified = verify(plan, result)

    assert verified.status == "SUCCESS"
    assert verified.verified is True


def test_state_change_plan_uses_existing_heartbeat():
    hive = FakeHive()

    plan = ActionPlan(
        action="inspect_state_change",
        expected_result="evidence explaining the observed change",
        verification="change_explained",
    )

    authorization = authorize_plan(plan)
    result = execute_plan(plan, hive, authorization=authorization)

    assert result.status == "SUCCESS"
    assert hive.calls == 1
    assert result.evidence["source"] == "existing_heartbeat"

    verified = verify(plan, result)

    assert verified.status == "SUCCESS"
    assert verified.verified is True


def test_observation_plan_uses_existing_heartbeat():
    hive = FakeHive()

    plan = ActionPlan(
        action="record_observation",
        expected_result="change remains represented in current state",
        verification="observation_recorded",
    )

    authorization = authorize_plan(plan)
    result = execute_plan(plan, hive, authorization=authorization)

    assert result.status == "SUCCESS"
    assert hive.calls == 1

    verified = verify(plan, result)

    assert verified.status == "SUCCESS"
    assert verified.verified is True


def test_unknown_action_is_blocked():
    plan = ActionPlan(
        action="do_something_unregistered",
        verification="something",
    )

    result = execute_plan(plan)

    assert result.status == "BLOCKED"
    assert result.verified is False


def test_failed_result_never_verifies():
    plan = ActionPlan(
        action="inspect_state_change",
        verification="change_explained",
    )

    result = ActionResult(
        status="FAILED",
        result="failure",
        verified=False,
    )

    verified = verify(plan, result)

    assert verified.status == "FAILED"
    assert verified.verified is False
