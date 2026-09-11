from __future__ import annotations

import time

from ai.hive.debate import (
    AgentRole,
    DebateEngine,
)


class FakeWorker:
    def __init__(self, name: str, response: str, delay: float = 0):
        self.name = name
        self.response = response
        self.delay = delay

    def execute(self, prompt, system=None):
        if self.delay:
            time.sleep(self.delay)

        assert "RICHARDLAB AGENT ROLE" in prompt
        assert system is not None

        return self.response


class BrokenWorker:
    name = "broken"

    def execute(self, prompt, system=None):
        raise RuntimeError("intentional test failure")


def make_engine():
    return DebateEngine(
        {
            "observer": (
                AgentRole(
                    "observer",
                    "facts only",
                ),
                FakeWorker("gpt-observer", "OBSERVED"),
            ),
            "explorer": (
                AgentRole(
                    "explorer",
                    "generate possibilities",
                ),
                FakeWorker("gpt-explorer", "POSSIBILITIES"),
            ),
            "contrarian": (
                AgentRole(
                    "contrarian",
                    "attack assumptions",
                ),
                FakeWorker("gpt-contrarian", "ATTACK"),
            ),
        }
    )


def test_three_agents_return_independent_results():
    result = make_engine().run("Why did this happen?")

    assert result.question == "Why did this happen?"
    assert len(result.responses) == 3

    roles = {response.role for response in result.responses}

    assert roles == {
        "observer",
        "explorer",
        "contrarian",
    }

    assert result.failed() == ()
    assert len(result.successful()) == 3


def test_results_are_preserved_by_role():
    result = make_engine().run("Test question")

    results = {
        response.role: response.result
        for response in result.responses
    }

    assert results["observer"] == "OBSERVED"
    assert results["explorer"] == "POSSIBILITIES"
    assert results["contrarian"] == "ATTACK"


def test_one_agent_failure_does_not_destroy_other_results():
    engine = DebateEngine(
        {
            "observer": (
                AgentRole("observer", "observe"),
                FakeWorker("good", "SUCCESS"),
            ),
            "broken": (
                AgentRole("contrarian", "attack"),
                BrokenWorker(),
            ),
        }
    )

    result = engine.run("Test")

    assert len(result.responses) == 2
    assert len(result.successful()) == 1
    assert len(result.failed()) == 1

    successful = result.successful()[0]

    assert successful.result == "SUCCESS"
    assert result.failed()[0].error.startswith("RuntimeError:")


def test_agents_execute_concurrently():
    engine = DebateEngine(
        {
            "one": (
                AgentRole("one", "test"),
                FakeWorker("one", "A", delay=0.25),
            ),
            "two": (
                AgentRole("two", "test"),
                FakeWorker("two", "B", delay=0.25),
            ),
            "three": (
                AgentRole("three", "test"),
                FakeWorker("three", "C", delay=0.25),
            ),
        }
    )

    started = time.monotonic()

    result = engine.run("parallel test")

    elapsed = time.monotonic() - started

    assert len(result.successful()) == 3

    # Sequential execution would be roughly 0.75 seconds.
    # Parallel execution should be substantially below that.
    assert elapsed < 0.60
