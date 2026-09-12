from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    """Return a machine-readable UTC timestamp."""
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def text_hash(value: Any) -> str:
    """Hash text for provenance without storing the prompt itself."""
    return sha256(str(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ExecutionTrace:
    """Deterministic provenance record for one Council execution stage."""

    trace_id: str
    batch_id: str
    stage: str
    role: str | None
    worker: str
    provider: str | None
    model: str | None
    start_time: str
    end_time: str
    elapsed_seconds: float | None
    success: bool
    response_id: str | None
    input_sha256: str
    error: str | None = None
    parent_trace_ids: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class CouncilTrace:
    """Collect execution provenance for a single Council deliberation."""

    def __init__(self, question: str, batch_id: str | None = None) -> None:
        self.question = question
        self.batch_id = batch_id or f"council-{uuid4().hex}"
        self.records: list[ExecutionTrace] = []

    def start(self) -> str:
        return utc_now()

    def finish(
        self,
        *,
        start_time: str,
        stage: str,
        role: str | None,
        worker: Any,
        result: Any = None,
        error: Exception | str | None = None,
        input_value: Any = "",
        parent_trace_ids: tuple[str, ...] = (),
    ) -> ExecutionTrace:
        end_time = utc_now()
        provider = getattr(result, "provider", None)
        model = getattr(result, "model", None)
        metadata = getattr(result, "metadata", None) or {}
        if isinstance(metadata, dict):
            response_id = metadata.get("response_id")
        else:
            response_id = None

        elapsed = getattr(result, "elapsed_seconds", None)
        worker_name = getattr(worker, "name", type(worker).__name__)

        record = ExecutionTrace(
            trace_id=f"trace-{uuid4().hex}",
            batch_id=self.batch_id,
            stage=stage,
            role=role,
            worker=worker_name,
            provider=provider,
            model=model,
            start_time=start_time,
            end_time=end_time,
            elapsed_seconds=elapsed,
            success=error is None,
            response_id=response_id,
            input_sha256=text_hash(input_value),
            error=None if error is None else str(error),
            parent_trace_ids=parent_trace_ids,
        )
        self.records.append(record)
        return record

    def as_dict(self) -> dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "question_sha256": text_hash(self.question),
            "records": [record.as_dict() for record in self.records],
        }
