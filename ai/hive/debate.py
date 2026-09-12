from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any

from .trace import CouncilTrace


@dataclass(frozen=True)
class AgentRole:
    name: str
    mission: str


@dataclass(frozen=True)
class AgentResponse:
    role: str
    worker: str
    result: Any
    error: str | None = None


@dataclass(frozen=True)
class DebateResult:
    question: str
    responses: tuple[AgentResponse, ...]
    batch_id: str | None = None
    traces: tuple[dict[str, Any], ...] = ()

    def successful(self) -> tuple[AgentResponse, ...]:
        return tuple(
            response
            for response in self.responses
            if response.error is None
        )

    def failed(self) -> tuple[AgentResponse, ...]:
        return tuple(
            response
            for response in self.responses
            if response.error is not None
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "batch_id": self.batch_id,
            "traces": list(self.traces),
            "responses": [
                {
                    "role": response.role,
                    "worker": response.worker,
                    "result": response.result,
                    "error": response.error,
                }
                for response in self.responses
            ],
        }


DEFAULT_ROLES = (
    AgentRole(
        name="observer",
        mission=(
            "Identify what is directly known. Separate observations, "
            "evidence, assumptions, and unknowns. Do not speculate "
            "beyond the supplied information."
        ),
    ),
    AgentRole(
        name="explorer",
        mission=(
            "Generate alternative explanations, hypotheses, unusual "
            "possibilities, and overlooked interpretations. Clearly "
            "label speculation as speculation."
        ),
    ),
    AgentRole(
        name="contrarian",
        mission=(
            "Attack assumptions and conclusions. Look for contradictions, "
            "missing evidence, alternative explanations, and ways the "
            "current reasoning could be wrong."
        ),
    ),
)


class DebateEngine:
    """
    Run independent reasoning agents concurrently.

    This layer coordinates workers but does not decide which conclusion
    is correct. It preserves independent outputs for later auditing.
    """

    def __init__(self, agents: dict[str, tuple[AgentRole, Any]]) -> None:
        self.agents = agents

    def _execute_agent(
        self,
        role: AgentRole,
        worker: Any,
        question: str,
        trace: CouncilTrace,
    ) -> AgentResponse:
        prompt = (
            "RICHARDLAB AGENT ROLE\n"
            f"ROLE: {role.name}\n"
            f"MISSION: {role.mission}\n\n"
            "USER QUESTION:\n"
            f"{question}\n\n"
            "Return your analysis according to your assigned role. "
            "Do not pretend certainty where evidence is missing."
        )

        start_time = trace.start()
        try:
            result = worker.execute(
                prompt,
                system=(
                    "You are a specialized reasoning agent inside "
                    "RichardLab. Perform only your assigned role."
                ),
            )
            trace.finish(
                start_time=start_time,
                stage="debate",
                role=role.name,
                worker=worker,
                result=result,
                input_value=prompt,
            )
            return AgentResponse(
                role=role.name,
                worker=worker.name,
                result=result,
            )
        except Exception as exc:
            trace.finish(
                start_time=start_time,
                stage="debate",
                role=role.name,
                worker=worker,
                error=f"{type(exc).__name__}: {exc}",
                input_value=prompt,
            )
            return AgentResponse(
                role=role.name,
                worker=getattr(worker, "name", type(worker).__name__),
                result=None,
                error=f"{type(exc).__name__}: {exc}",
            )

    def run(self, question: str, trace: CouncilTrace | None = None) -> DebateResult:
        responses: list[AgentResponse] = []
        trace = trace or CouncilTrace(question)

        with ThreadPoolExecutor(
            max_workers=max(1, len(self.agents))
        ) as executor:
            futures = {
                executor.submit(
                    self._execute_agent,
                    role,
                    worker,
                    question,
                    trace,
                ): role.name
                for role, worker in self.agents.values()
            }

            for future in as_completed(futures):
                responses.append(future.result())

        responses.sort(key=lambda response: response.role)

        return DebateResult(
            question=question,
            responses=tuple(responses),
            batch_id=trace.batch_id,
            traces=tuple(
                record.as_dict()
                for record in trace.records
                if record.stage == "debate"
            ),
        )
