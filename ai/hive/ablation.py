from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
from hashlib import sha256

from .council import Council, CouncilResult


@dataclass(frozen=True)
class AblationCase:
    removed_role: str | None
    result: CouncilResult
    output_sha256: str
    debate_roles: tuple[str, ...]
    trace_count: int


@dataclass(frozen=True)
class AblationReport:
    question: str
    baseline: AblationCase
    variants: tuple[AblationCase, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "baseline": self._case_dict(self.baseline),
            "variants": [self._case_dict(case) for case in self.variants],
        }

    @staticmethod
    def _case_dict(case: AblationCase) -> dict[str, Any]:
        return {
            "removed_role": case.removed_role,
            "output_sha256": case.output_sha256,
            "debate_roles": list(case.debate_roles),
            "trace_count": case.trace_count,
            "batch_id": case.result.evidence_trace.get("batch_id")
            if case.result.evidence_trace
            else None,
        }

    def changed_after_removal(self, role: str) -> bool:
        return any(
            case.removed_role == role
            and case.output_sha256 != self.baseline.output_sha256
            for case in self.variants
        )


class CouncilAblation:
    """Run controlled Council interventions by removing one debate role."""

    def __init__(
        self,
        council: Council,
        deliberate: Callable[[Council, str], CouncilResult] | None = None,
    ) -> None:
        self.council = council
        self._deliberate = deliberate or (lambda target, question: target.deliberate(question))

    def run(
        self,
        question: str,
        roles: tuple[str, ...] = ("observer", "explorer", "contrarian"),
    ) -> AblationReport:
        for role in roles:
            if role not in self.council.debate.agents:
                raise ValueError(f"Unknown Council role: {role}")

        baseline = self._run_case(question, self.council, None)
        variants: list[AblationCase] = []

        for role in roles:
            variant = self.council.without_role(role)
            variants.append(self._run_case(question, variant, role))

        return AblationReport(
            question=question,
            baseline=baseline,
            variants=tuple(variants),
        )

    def _run_case(
        self,
        question: str,
        council: Council,
        removed_role: str | None,
    ) -> AblationCase:
        result = self._deliberate(council, question)
        output = result.synthesis
        digest = sha256(str(output).encode("utf-8")).hexdigest()
        traces = result.evidence_trace or {}
        return AblationCase(
            removed_role=removed_role,
            result=result,
            output_sha256=digest,
            debate_roles=tuple(response.role for response in result.debate.responses),
            trace_count=len(traces.get("records", [])),
        )
