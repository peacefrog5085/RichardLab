from __future__ import annotations

from ai.hive.council import Council
from ai.hive.debate import AgentRole


class FakeWorker:
    def __init__(self, name: str, result: str):
        self.name = name
        self.result = result
        self.calls = []

    def execute(self, task, *, system=None):
        self.calls.append((task, system))
        return self.result


def test_council_preserves_independent_debate_results():
    observer = FakeWorker("openai-observer", "Facts")
    explorer = FakeWorker("openai-explorer", "Possibility")
    contrarian = FakeWorker("openai-contrarian", "Challenge")

    council = Council(
        {
            "observer": (
                AgentRole("observer", "Observe."),
                observer,
            ),
            "explorer": (
                AgentRole("explorer", "Explore."),
                explorer,
            ),
            "contrarian": (
                AgentRole("contrarian", "Challenge."),
                contrarian,
            ),
        }
    )

    result = council.deliberate("What happened?")

    assert result.question == "What happened?"
    assert [r.role for r in result.debate.responses] == [
        "contrarian",
        "explorer",
        "observer",
    ]
    assert [r.result for r in result.debate.responses] == [
        "Challenge",
        "Possibility",
        "Facts",
    ]


def test_council_parses_structured_audit():
    observer = FakeWorker("observer-worker", "Observation")

    auditor = FakeWorker(
        "auditor-worker",
        """AGREEMENTS
- Both agents agree on the basic fact.

CONTRADICTIONS
- Agent A says X while Agent B says Y.

UNSUPPORTED CLAIMS
- Agent B provides no evidence for Y.

UNKNOWNS
- The underlying cause remains unknown.

EVIDENCE NEEDED
- Obtain the original source data.
""",
    )

    synthesizer = FakeWorker("synth-worker", "Final conclusion")

    council = Council(
        {
            "observer": (
                AgentRole("observer", "Observe."),
                observer,
            ),
        },
        auditor=auditor,
        synthesizer=synthesizer,
    )

    result = council.deliberate("Test question")

    assert result.audit is not None
    assert result.audit.agreements == (
        "Both agents agree on the basic fact.",
    )
    assert result.audit.contradictions == (
        "Agent A says X while Agent B says Y.",
    )
    assert result.audit.unsupported_claims == (
        "Agent B provides no evidence for Y.",
    )
    assert result.audit.unknowns == (
        "The underlying cause remains unknown.",
    )
    assert result.audit.evidence_needed == (
        "Obtain the original source data.",
    )
    assert result.synthesis == "Final conclusion"
    assert len(auditor.calls) == 1
    assert len(synthesizer.calls) == 1


def test_council_can_audit_and_synthesize_empty_sections():
    observer = FakeWorker("observer-worker", "Observation")

    auditor = FakeWorker(
        "auditor-worker",
        """AGREEMENTS
NONE

CONTRADICTIONS
NONE

UNSUPPORTED CLAIMS
NONE

UNKNOWNS
- Something remains unknown.

EVIDENCE NEEDED
NONE
""",
    )

    synthesizer = FakeWorker("synth-worker", "Final conclusion")

    council = Council(
        {
            "observer": (
                AgentRole("observer", "Observe."),
                observer,
            ),
        },
        auditor=auditor,
        synthesizer=synthesizer,
    )

    result = council.deliberate("Test question")

    assert result.audit is not None
    assert result.audit.agreements == ()
    assert result.audit.contradictions == ()
    assert result.audit.unsupported_claims == ()
    assert result.audit.unknowns == ("Something remains unknown.",)
    assert result.audit.evidence_needed == ()
    assert result.synthesis == "Final conclusion"


def test_council_preserves_auditor_failure_as_uncertainty():
    observer = FakeWorker("observer-worker", "Observation")

    class BrokenAuditor(FakeWorker):
        def execute(self, task, *, system=None):
            raise RuntimeError("auditor unavailable")

    council = Council(
        {
            "observer": (
                AgentRole("observer", "Observe."),
                observer,
            ),
        },
        auditor=BrokenAuditor("auditor-worker", ""),
    )

    result = council.deliberate("Test question")

    assert result.audit is not None
    assert "Auditor execution failed" in result.audit.unknowns[0]
