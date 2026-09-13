from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..tool_registry import call_tool


@dataclass(frozen=True)
class StateSnapshot:
    """Observed state presented to the Hive decision layer."""

    attention: str = "NONE"
    changes: tuple[dict[str, Any], ...] = ()
    observations: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "attention": self.attention,
            "changes": list(self.changes),
            "observations": self.observations,
        }


@dataclass(frozen=True)
class Decision:
    """Explicit statement of what the Hive decided should happen."""

    objective: str
    decision: str
    reason: str
    capability: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "objective": self.objective,
            "decision": self.decision,
            "reason": self.reason,
            "capability": self.capability,
        }



_COUNCIL_RECOMMENDATIONS = frozenset(
    {
        "REVIEW_STATE_CHANGE",
    }
)


def extract_council_recommendation(
    synthesis: Any,
) -> dict[str, Any]:
    """Extract an explicitly declared recommendation from Council synthesis.

    Ordinary synthesis text is never treated as an instruction. A recommendation
    must use the explicit ``RECOMMENDATION: <decision>`` marker.
    """

    if not isinstance(synthesis, str):
        return {
            "decision": "REVIEW_STATE_CHANGE",
            "reason": (
                "Council synthesis is not text; an explicit recommendation "
                "is required."
            ),
            "capability": None,
        }

    for line in synthesis.splitlines():
        stripped = line.strip()

        if not stripped.upper().startswith("RECOMMENDATION:"):
            continue

        raw_decision = stripped.split(":", 1)[1].strip()

        if raw_decision in _COUNCIL_RECOMMENDATIONS:
            return {
                "decision": raw_decision,
                "reason": "Council explicitly recommended review.",
                "capability": None,
            }

        return {
            "decision": "REVIEW_STATE_CHANGE",
            "reason": (
                f"Unknown Council recommendation '{raw_decision}'; "
                "deterministic control requires review."
            ),
            "capability": None,
        }

    return {
        "decision": "REVIEW_STATE_CHANGE",
        "reason": (
            "No explicit Council recommendation was found; "
            "deterministic control requires explicit review."
        ),
        "capability": None,
    }


def council_recommendation_to_decision(
    recommendation: dict[str, Any],
) -> Decision:
    """Translate a Council recommendation into a deterministic Control decision."""

    raw_decision = recommendation.get("decision")
    reason = recommendation.get("reason")
    capability = recommendation.get("capability")

    if raw_decision == "REVIEW_STATE_CHANGE":
        return Decision(
            objective="understand the detected state change",
            decision=raw_decision,
            reason=reason or "Council requested review of a state change.",
            capability=capability,
        )

    if raw_decision:
        return Decision(
            objective="review an unrecognized Council recommendation",
            decision="REVIEW_STATE_CHANGE",
            reason=(
                f"Unknown Council decision '{raw_decision}'; "
                "deterministic control requires review."
            ),
            capability=None,
        )

    return Decision(
        objective="review an incomplete Council recommendation",
        decision="REVIEW_STATE_CHANGE",
        reason=(
            "Council recommendation is missing or incomplete; "
            "deterministic control requires review."
        ),
        capability=None,
    )


@dataclass(frozen=True)
class ActionPlan:
    """Concrete action derived from a Hive decision."""

    action: str
    target: str | None = None
    inputs: dict[str, Any] = field(default_factory=dict)
    expected_result: str | None = None
    verification: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "target": self.target,
            "inputs": self.inputs,
            "expected_result": self.expected_result,
            "verification": self.verification,
        }


@dataclass(frozen=True)
class ActionResult:
    """Observed outcome of an executed action."""

    status: str
    result: Any = None
    verified: bool = False
    evidence: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "result": self.result,
            "verified": self.verified,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class ControlCycle:
    """Complete State → Decision → Action → Verification record."""

    state: StateSnapshot
    decision: Decision
    plan: ActionPlan
    result: ActionResult | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "state": self.state.as_dict(),
            "decision": self.decision.as_dict(),
            "plan": self.plan.as_dict(),
            "result": (
                self.result.as_dict()
                if self.result is not None
                else None
            ),
        }


def state_from_heartbeat(heartbeat: Any) -> StateSnapshot:
    """Convert an existing heartbeat result into control-layer state."""

    if hasattr(heartbeat, "as_dict"):
        raw = heartbeat.as_dict()
    elif isinstance(heartbeat, dict):
        raw = heartbeat
    else:
        raise TypeError("heartbeat must be a HeartbeatResult or dict")

    changes = tuple(raw.get("changes", []))
    snapshot = raw.get("snapshot", {})

    if hasattr(snapshot, "__dict__"):
        observations = dict(snapshot.__dict__)
    elif isinstance(snapshot, dict):
        observations = dict(snapshot)
    else:
        observations = {}

    return StateSnapshot(
        attention=str(raw.get("attention", "NONE")),
        changes=changes,
        observations=observations,
    )


def decide(state: StateSnapshot) -> Decision:
    """Make the first deterministic control decision."""

    if state.attention == "ACTION":
        return Decision(
            objective="restore or protect RichardLab operation",
            decision="REVIEW_CRITICAL_STATE",
            reason="Heartbeat reports a critical condition.",
        )

    if state.attention == "REVIEW":
        return Decision(
            objective="understand the detected state change",
            decision="REVIEW_STATE_CHANGE",
            reason="Heartbeat reports a meaningful change requiring review.",
        )

    if state.attention == "WATCH":
        return Decision(
            objective="observe the detected change",
            decision="OBSERVE_CHANGE",
            reason="Heartbeat reports a meaningful change without immediate action.",
        )

    return Decision(
        objective="maintain current RichardLab state",
        decision="NO_ACTION",
        reason="No meaningful state change requires intervention.",
    )


def plan_for(decision: Decision) -> ActionPlan:
    """Translate a deterministic decision into an executable plan."""

    if decision.decision == "REVIEW_CRITICAL_STATE":
        return ActionPlan(
            action="inspect_lab_status",
            expected_result="current lab state and health information",
            verification="status_observed",
        )

    if decision.decision == "REVIEW_STATE_CHANGE":
        return ActionPlan(
            action="inspect_state_change",
            expected_result="evidence explaining the observed change",
            verification="change_explained",
        )

    if decision.decision == "OBSERVE_CHANGE":
        return ActionPlan(
            action="record_observation",
            expected_result="change remains represented in current state",
            verification="observation_recorded",
        )

    return ActionPlan(
        action="none",
        expected_result="no action required",
        verification="state_remains_stable",
    )



def execute_plan(plan: ActionPlan, hive=None) -> ActionResult:
    """Execute an authorized deterministic RichardLab control action.

    Execution is intentionally narrow and reuses existing RichardLab
    mechanisms. This is not a second router or execution engine.
    """

    if plan.action == "none":
        return ActionResult(
            status="SUCCESS",
            result=None,
            verified=False,
            evidence={"action": "none"},
        )

    try:
        if plan.action == "inspect_lab_status":
            result = call_tool("get_lab_status")

            return ActionResult(
                status="SUCCESS",
                result=result,
                verified=False,
                evidence={
                    "action": plan.action,
                    "source": "existing_tool_registry",
                },
            )

        if plan.action in {
            "inspect_state_change",
            "record_observation",
        }:
            if hive is None:
                return ActionResult(
                    status="FAILED",
                    result="HiveCore is required for this action.",
                    verified=False,
                    evidence={"action": plan.action},
                )

            heartbeat = hive.heartbeat()

            return ActionResult(
                status="SUCCESS",
                result=heartbeat,
                verified=False,
                evidence={
                    "action": plan.action,
                    "source": "existing_heartbeat",
                },
            )

        return ActionResult(
            status="BLOCKED",
            result=f"Action is not authorized: {plan.action}",
            verified=False,
            evidence={
                "action": plan.action,
                "reason": (
                    "No deterministic executor is registered "
                    "for this action."
                ),
            },
        )

    except Exception as exc:
        return ActionResult(
            status="FAILED",
            result=str(exc),
            verified=False,
            evidence={
                "action": plan.action,
                "error_type": type(exc).__name__,
            },
        )

def verify(plan: ActionPlan, result: ActionResult) -> ActionResult:
    """Verify an action result against its declared verification contract."""

    if result.status != "SUCCESS":
        return ActionResult(
            status=result.status,
            result=result.result,
            verified=False,
            evidence=result.evidence,
        )

    return ActionResult(
        status=result.status,
        result=result.result,
        verified=True,
        evidence=result.evidence,
    )


@dataclass(frozen=True)
class AuthorizationDecision:
    """Deterministic authorization decision made before execution."""

    status: str
    action: str
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "action": self.action,
            "reason": self.reason,
        }


_AUTHORIZED_ACTIONS = frozenset(
    {
        "none",
        "inspect_lab_status",
        "inspect_state_change",
        "record_observation",
    }
)


def authorize_plan(plan: ActionPlan) -> AuthorizationDecision:
    """Authorize only explicitly registered deterministic control actions.

    Authorization is a pure policy decision. It does not execute tools,
    inspect external state, or mutate RichardLab.
    """

    if plan.action in _AUTHORIZED_ACTIONS:
        return AuthorizationDecision(
            status="AUTHORIZED",
            action=plan.action,
            reason=f"Action is explicitly authorized: {plan.action}",
        )

    return AuthorizationDecision(
        status="BLOCKED",
        action=plan.action,
        reason=f"Action is not authorized: {plan.action}",
    )
