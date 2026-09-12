from ai.hive.council import Council
from ai.hive.debate import AgentRole


class Result:
    def __init__(self, text, provider="test-provider", model="test-model", response_id="resp-test"):
        self.text = text
        self.provider = provider
        self.model = model
        self.elapsed_seconds = 0.01
        self.metadata = {"response_id": response_id}


class Worker:
    def __init__(self, name, text):
        self.name = name
        self.text = text

    def execute(self, task, *, system=None):
        return Result(self.text, response_id=f"resp-{self.name}")


def test_council_trace_links_all_stages_to_one_batch():
    workers = {
        name: Worker(name, name)
        for name in ("observer", "explorer", "contrarian", "auditor", "synthesizer")
    }

    council = Council(
        {
            role: (AgentRole(role, role), workers[role])
            for role in ("observer", "explorer", "contrarian")
        },
        auditor=workers["auditor"],
        synthesizer=workers["synthesizer"],
    )

    result = council.deliberate("trace this")

    trace = result.evidence_trace
    assert trace is not None
    assert trace["batch_id"]
    records = trace["records"]

    assert [r["stage"] for r in records[:3]] == ["debate", "debate", "debate"]
    assert records[3]["stage"] == "audit"
    assert records[4]["stage"] == "synthesis"
    assert all(r["batch_id"] == trace["batch_id"] for r in records)
    assert all(r["trace_id"] for r in records)
    assert all(r["input_sha256"] for r in records)
    assert all(r["success"] for r in records)

    debate_trace_ids = {r["trace_id"] for r in result.debate.traces}
    assert len(debate_trace_ids) == 3
    assert all(r["response_id"] for r in records)
    assert result.audit.trace["stage"] == "audit"


def test_trace_does_not_store_plain_question_or_prompt():
    worker = Worker("observer", "result")
    council = Council(
        {"observer": (AgentRole("observer", "Observe."), worker)}
    )

    result = council.deliberate("SECRET QUESTION")

    serialized = str(result.evidence_trace)
    assert "SECRET QUESTION" not in serialized
    assert "USER QUESTION:" not in serialized
