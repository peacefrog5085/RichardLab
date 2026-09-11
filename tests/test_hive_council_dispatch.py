from __future__ import annotations

import pytest

from ai.hive.core import HiveCore


class FakeCouncil:
    def __init__(self):
        self.calls = []

    def deliberate(self, prompt):
        self.calls.append(prompt)
        return {
            "type": "council_result",
            "prompt": prompt,
        }


def make_core():
    core = object.__new__(HiveCore)
    core.council = FakeCouncil()
    return core


def test_dispatch_council_calls_council():
    core = make_core()

    result = core.dispatch_council("  Test question  ")

    assert result == {
        "type": "council_result",
        "prompt": "Test question",
    }
    assert core.council.calls == ["Test question"]


@pytest.mark.parametrize(
    "prompt",
    [
        "",
        "   ",
        None,
        123,
    ],
)
def test_dispatch_council_rejects_empty_or_invalid_prompt(prompt):
    core = make_core()

    with pytest.raises(ValueError):
        core.dispatch_council(prompt)
