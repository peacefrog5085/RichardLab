from ai.router.capabilities import (
    ROUTE_CAPABILITIES,
    capability_for_route,
)


def test_ai_reasoning_maps_to_reasoning():
    assert capability_for_route("ai_reasoning") == "reasoning"


def test_unknown_route_has_no_capability():
    assert capability_for_route("unknown_route") is None


def test_local_routes_are_not_ai_capabilities():
    assert capability_for_route("system_status") is None
    assert capability_for_route("experiment_list") is None
    assert capability_for_route("experiment_inspect") is None
    assert capability_for_route("experiment_family") is None


def test_mapping_is_explicit():
    assert ROUTE_CAPABILITIES == {
        "ai_reasoning": "reasoning",
    }
