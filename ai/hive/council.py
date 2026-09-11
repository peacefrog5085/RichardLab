from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .debate import (
    AgentResponse,
    AgentRole,
    DebateEngine,
    DebateResult,
)


@dataclass(frozen=True)
class AuditResult:
    """Structured cross-examination of independent agent responses."""

    question: str
    responses_reviewed: tuple[AgentResponse, ...]
    agreements: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()
    unsupported_claims: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()
    evidence_needed: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "responses_reviewed": [
                {
                    "role": response.role,
                    "worker": response.worker,
                    "result": response.result,
                    "error": response.error,
                }
                for response in self.responses_reviewed
            ],
            "agreements": list(self.agreements),
            "contradictions": list(self.contradictions),
            "unsupported_claims": list(self.unsupported_claims),
            "unknowns": list(self.unknowns),
            "evidence_needed": list(self.evidence_needed),
        }


@dataclass(frozen=True)
class CouncilResult:
    """Complete RichardLab multi-agent reasoning record."""

    question: str
    debate: DebateResult
    audit: AuditResult | None = None
    synthesis: Any = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "debate": self.debate.as_dict(),
            "audit": self.audit.as_dict() if self.audit else None,
            "synthesis": self.synthesis,
        }


class Council:
    """
    Coordinate independent reasoning, auditing, and synthesis.

    The Council deliberately preserves the independent debate outputs.
    It does not collapse disagreement into a vote or manufacture certainty.
    """

    def __init__(
        self,
        agents: dict[str, tuple[AgentRole, Any]],
        auditor: Any | None = None,
        synthesizer: Any | None = None,
    ) -> None:
        self.debate = DebateEngine(agents)
        self.auditor = auditor
        self.synthesizer = synthesizer

    def deliberate(self, question: str) -> CouncilResult:
        debate = self.debate.run(question)

        audit = None
        if self.auditor is not None:
            audit = self._audit(question, debate)

        synthesis = None
        if self.synthesizer is not None:
            synthesis = self._synthesize(question, debate, audit)

        return CouncilResult(
            question=question,
            debate=debate,
            audit=audit,
            synthesis=synthesis,
        )

    def _audit(
        self,
        question: str,
        debate: DebateResult,
    ) -> AuditResult:
        prompt = self._audit_prompt(question, debate)

        try:
            result = self.auditor.execute(
                prompt,
                system=(
                    "You are the RichardLab Auditor. "
                    "Cross-examine independent reasoning. "
                    "Do not decide by majority vote. "
                    "Preserve uncertainty and identify unsupported claims."
                ),
            )
        except Exception as exc:
            return AuditResult(
                question=question,
                responses_reviewed=debate.responses,
                unknowns=(
                    f"Auditor execution failed: "
                    f"{type(exc).__name__}: {exc}",
                ),
            )

        audit_text = self._result_text(result)
        parsed = self._parse_audit(audit_text)

        return AuditResult(
            question=question,
            responses_reviewed=debate.responses,
            agreements=parsed["agreements"],
            contradictions=parsed["contradictions"],
            unsupported_claims=parsed["unsupported_claims"],
            unknowns=parsed["unknowns"],
            evidence_needed=parsed["evidence_needed"],
        )

    def _synthesize(
        self,
        question: str,
        debate: DebateResult,
        audit: AuditResult | None,
    ) -> Any:
        prompt = self._synthesis_prompt(question, debate, audit)

        result = self.synthesizer.execute(
            prompt,
            system=(
                "You are the RichardLab Synthesizer. "
                "Produce conclusions proportional to the evidence. "
                "Do not convert disagreement into certainty. "
                "Explicitly preserve important unknowns."
            ),
        )

        return self._result_text(result)

    @staticmethod
    def _result_text(result: Any) -> Any:
        """Normalize provider responses while preserving simple test doubles."""
        return getattr(result, "text", result)

    @staticmethod
    def _parse_audit(text: Any) -> dict[str, tuple[str, ...]]:
        """Parse the Auditor's structured five-section response."""
        if not isinstance(text, str):
            text = str(text)

        sections = {
            "agreements": "AGREEMENTS",
            "contradictions": "CONTRADICTIONS",
            "unsupported_claims": "UNSUPPORTED CLAIMS",
            "unknowns": "UNKNOWNS",
            "evidence_needed": "EVIDENCE NEEDED",
        }

        lines = text.splitlines()
        current = None
        parsed = {key: [] for key in sections}

        heading_map = {heading: key for key, heading in sections.items()}

        for raw_line in lines:
            line = raw_line.strip()

            normalized = line.lstrip("#*- ").strip().upper().rstrip(":")
            if normalized in heading_map:
                current = heading_map[normalized]
                continue

            if current is None or not line:
                continue

            item = line.lstrip("-*• ").strip()
            if item and item.upper() != "NONE":
                parsed[current].append(item)

        return {
            key: tuple(values)
            for key, values in parsed.items()
        }

    @staticmethod
    def _audit_prompt(
        question: str,
        debate: DebateResult,
    ) -> str:
        responses = []

        for response in debate.responses:
            responses.append(
                {
                    "role": response.role,
                    "worker": response.worker,
                    "result": response.result,
                    "error": response.error,
                }
            )

        return (
            "RICHARDLAB AUDIT REQUEST\n\n"
            "USER QUESTION:\n"
            f"{question}\n\n"
            "INDEPENDENT RESPONSES:\n"
            f"{responses}\n\n"
            "Audit the responses.\n"
            "Identify:\n"
            "1. Areas of agreement.\n"
            "2. Contradictions.\n"
            "3. Unsupported claims.\n"
            "4. Important unknowns.\n"
            "5. Evidence that would resolve disagreement.\n\n"
            "Return the audit using exactly these headings:\n"
            "AGREEMENTS\n"
            "CONTRADICTIONS\n"
            "UNSUPPORTED CLAIMS\n"
            "UNKNOWNS\n"
            "EVIDENCE NEEDED\n\n"
            "Under each heading, provide concise bullet points. "
            "If a category has nothing to report, write NONE.\n\n"
            "Do not choose a conclusion merely because multiple agents "
            "agree. Evaluate the reasoning and evidence."
        )

    @staticmethod
    def _synthesis_prompt(
        question: str,
        debate: DebateResult,
        audit: AuditResult | None,
    ) -> str:
        return (
            "RICHARDLAB SYNTHESIS REQUEST\n\n"
            "USER QUESTION:\n"
            f"{question}\n\n"
            "INDEPENDENT DEBATE:\n"
            f"{debate.as_dict()}\n\n"
            "AUDIT:\n"
            f"{audit.as_dict() if audit else 'No audit available.'}\n\n"
            "Produce an evidence-proportional conclusion.\n"
            "Separate:\n"
            "- Known facts\n"
            "- Strong inferences\n"
            "- Plausible possibilities\n"
            "- Contradictions\n"
            "- Unknowns\n"
            "- Evidence still needed\n\n"
            "Do not invent missing information."
        )
