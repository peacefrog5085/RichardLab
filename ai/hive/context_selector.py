#!/usr/bin/env python3

"""
Deterministic reasoning-context selection for RichardLab.

Evidence collection remains complete. This module decides what subset
should be presented to an AI model for a particular question.
"""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import re


DEFAULT_MAX_CHARS = 12000


def _intent(prompt: str) -> str:
    text = prompt.lower()

    if any(word in text for word in (
        "failure",
        "failed",
        "error",
        "broken",
        "constraint",
        "why didn't",
        "why did it fail",
    )):
        return "failure"

    if any(word in text for word in (
        "run",
        "execution",
        "executed",
        "worked",
        "working",
        "successful",
        "success",
    )):
        return "run"

    if any(word in text for word in (
        "recommend",
        "should i",
        "what should",
        "next step",
        "next steps",
    )):
        return "recommendation"

    return "about"


def _target_name(prompt: str, evidence: dict) -> str | None:
    target = evidence.get("target")

    if isinstance(target, dict):
        for key in ("experiment", "name", "path", "filename"):
            value = target.get(key)
            if value:
                return str(value)

    elif isinstance(target, str) and target.strip():
        return target.strip()

    match = re.search(
        r"\bexperiment[- ]?\d{3}[a-z]?\.py\b",
        prompt,
        flags=re.IGNORECASE,
    )

    return match.group(0) if match else None


def _dedupe_artifacts(artifacts: list[dict]) -> list[dict]:
    """
    Collapse identical artifact records while preserving all observed
    run IDs as provenance.
    """
    grouped: OrderedDict[tuple, dict] = OrderedDict()

    for row in artifacts:
        key = (
            row.get("sha256"),
            row.get("artifact"),
            row.get("artifact_type"),
        )

        if key not in grouped:
            item = deepcopy(row)
            item["observed_run_ids"] = []

            run_id = row.get("run_id")
            if run_id:
                item["observed_run_ids"].append(run_id)

            grouped[key] = item
        else:
            run_id = row.get("run_id")
            if run_id and run_id not in grouped[key]["observed_run_ids"]:
                grouped[key]["observed_run_ids"].append(run_id)

    return list(grouped.values())


def _select_runs(runs: list[dict], intent: str, limit: int = 6) -> list[dict]:
    if not runs:
        return []

    def failed(row: dict) -> bool:
        text = " ".join(
            str(row.get(key, "")).lower()
            for key in ("status", "result", "outcome", "error", "stderr")
        )
        return any(x in text for x in ("fail", "error", "exception", "blocked"))

    if intent == "failure":
        ordered = sorted(
            runs,
            key=lambda r: (
                not failed(r),
                str(r.get("run_id", "")),
            ),
            reverse=False,
        )
    else:
        ordered = sorted(
            runs,
            key=lambda r: str(r.get("run_id", "")),
            reverse=True,
        )

    return ordered[:limit]


def _select_metrics(metrics: list[dict], limit: int = 6) -> list[dict]:
    """
    Metrics are retained only as supporting context. Until explicit
    run-to-metric provenance exists, never claim these belong to the
    target experiment.
    """
    if not metrics:
        return []

    ordered = sorted(
        metrics,
        key=lambda row: str(row.get("timestamp", "")),
        reverse=True,
    )

    return ordered[:limit]


def _select_source_files(
    source_files: dict[str, str],
    target_name: str | None,
    intent: str,
) -> dict[str, str]:
    if not source_files:
        return {}

    selected: OrderedDict[str, str] = OrderedDict()

    # Target source gets first priority.
    if target_name and target_name in source_files:
        selected[target_name] = source_files[target_name]

    # For general "about" questions, sibling source is useful but should
    # not overwhelm the target.
    siblings = [
        (name, source)
        for name, source in source_files.items()
        if name != target_name
    ]

    if intent in ("about", "recommendation"):
        for name, source in siblings[:2]:
            selected[name] = source

    elif intent == "run":
        # One sibling is enough to establish immediate lineage.
        if siblings:
            selected[siblings[0][0]] = siblings[0][1]

    # Failure questions should focus on the target unless a sibling is
    # necessary for comparison.
    elif intent == "failure":
        if siblings:
            selected[siblings[0][0]] = siblings[0][1]

    return dict(selected)


def _select_knowledge(knowledge: dict | None, intent: str) -> dict | None:
    if not knowledge:
        return None

    result = deepcopy(knowledge)

    matches = result.get("matches")
    if isinstance(matches, list):
        # The first match is already the highest-ranked match.
        # Keep only the strongest few so duplicate observations do not
        # dominate the reasoning context.
        result["matches"] = matches[:3]

    return result


def _serialized_size(value) -> int:
    """Return deterministic JSON character size."""
    import json

    return len(
        json.dumps(
            value,
            ensure_ascii=False,
            default=str,
            separators=(",", ":"),
        )
    )


def _add_if_fits(
    packet: dict,
    section: str,
    value,
    budget: int,
) -> bool:
    """
    Add a complete section only if the resulting packet remains
    within the hard character budget.
    """

    candidate = deepcopy(packet)
    candidate[section] = deepcopy(value)

    if packet_size(candidate) <= budget:
        packet[section] = deepcopy(value)
        return True

    return False


def _append_list_if_fits(
    packet: dict,
    section: str,
    items: list,
    budget: int,
) -> tuple[list, list]:
    """
    Add list records one at a time.

    Records are never partially truncated.

    Returns:
        (selected, omitted)
    """

    selected = []
    omitted = []

    packet[section] = []

    for item in items:
        candidate = deepcopy(packet)
        candidate[section] = selected + [deepcopy(item)]

        if packet_size(candidate) <= budget:
            selected.append(deepcopy(item))
        else:
            omitted.append(deepcopy(item))

    packet[section] = selected

    return selected, omitted


def _append_source_files_if_fits(
    packet: dict,
    source_files: dict[str, str],
    budget: int,
) -> tuple[dict[str, str], list[str]]:
    """
    Add complete source files in priority order.

    A source file is atomic. It is either included in full or omitted.
    """

    selected: OrderedDict[str, str] = OrderedDict()
    omitted: list[str] = []

    # Preserve source files already reserved by the selector.
    # In particular, the target source is required evidence and must
    # never be erased when optional sibling files are evaluated.
    existing = packet.get("source_files") or {}
    selected.update(existing)

    for name, source in source_files.items():
        if name in selected:
            continue
        candidate = deepcopy(packet)
        candidate["source_files"] = {
            **selected,
            name: source,
        }

        if packet_size(candidate) <= budget:
            selected[name] = source
        else:
            omitted.append(name)

    packet["source_files"] = dict(selected)

    return dict(selected), omitted


def _selection_metadata(
    intent: str,
    target_name: str | None,
    max_chars: int,
) -> dict[str, object]:
    return {
        "intent": intent,
        "target": target_name,
        "max_chars": max_chars,
        "budget_enforced": True,
        "policy": "deterministic-question-aware-v2",
    }


def select_reasoning_context(
    prompt: str,
    evidence,
    knowledge: dict | None = None,
    max_chars: int = DEFAULT_MAX_CHARS,
) -> dict:
    """
    Produce a deterministic, question-aware, size-bounded reasoning packet.

    Priority order:

        1. target identity and target source
        2. direct execution evidence
        3. knowledge
        4. artifacts
        5. family/similarity metadata
        6. related outputs
        7. system metrics
        8. sibling source

    Rules:

        * Evidence collection remains complete.
        * The original evidence object is never modified.
        * Records are included atomically.
        * The target source is reserved before optional context.
        * max_chars is a hard budget when required evidence fits.
        * Omitted material is explicitly recorded.
    """

    if max_chars <= 0:
        raise ValueError("max_chars must be greater than zero")

    if hasattr(evidence, "as_dict"):
        source = deepcopy(evidence.as_dict())
    elif isinstance(evidence, dict):
        source = deepcopy(evidence)
    else:
        raise TypeError(
            "evidence must be an EvidenceBundle or dict"
        )

    intent = _intent(prompt)
    target_name = _target_name(prompt, source)

    # Reserve the structural bookkeeping envelope before selecting
    # evidence. This prevents final selection metadata and omission
    # records from pushing an otherwise valid packet over max_chars.
    metadata_reserve = 1200
    evidence_budget = max_chars - metadata_reserve

    if evidence_budget <= 0:
        raise ValueError(
            "max_chars is too small for the selector metadata envelope"
        )

    packet = {
        "selection": _selection_metadata(
            intent,
            target_name,
            max_chars,
        ),
        "target": deepcopy(source.get("target")),
        "file_info": deepcopy(source.get("file_info")),
        "git": deepcopy(source.get("git")),
        "family": [],
        "similarities": [],
        "related_outputs": [],
        "runs": [],
        "artifacts": [],
        "system_metrics": [],
        "source_files": {},
        "knowledge": None,
        "omissions": {
            "source_files": [],
            "runs": [],
            "artifacts": [],
            "system_metrics": [],
            "knowledge_matches": [],
            "sections": [],
        },
    }

    source_files = source.get("source_files") or {}

    # ------------------------------------------------------------
    # 1. RESERVE TARGET SOURCE FIRST
    # ------------------------------------------------------------

    target_source_available = (
        target_name is not None
        and target_name in source_files
    )

    if target_source_available:
        packet["source_files"][target_name] = source_files[target_name]

    target_required_size = packet_size(packet)

    required_evidence_exceeds_budget = (
        target_required_size > evidence_budget
    )

    # ------------------------------------------------------------
    # 2. RUNS
    # ------------------------------------------------------------

    selected_runs, omitted_runs = _append_list_if_fits(
        packet,
        "runs",
        _select_runs(source.get("runs") or [], intent),
        max_chars,
    )

    packet["omissions"]["runs"] = [
        str(row.get("run_id", "<unknown>"))
        for row in omitted_runs
    ]

    # ------------------------------------------------------------
    # 3. KNOWLEDGE
    # ------------------------------------------------------------

    selected_knowledge = _select_knowledge(
        knowledge,
        intent,
    )

    if selected_knowledge:
        matches = selected_knowledge.get("matches")

        if isinstance(matches, list):
            kept_matches = []
            omitted_matches = []

            packet["knowledge"] = {
                key: value
                for key, value in selected_knowledge.items()
                if key != "matches"
            }
            packet["knowledge"]["matches"] = []

            for match in matches:
                candidate = deepcopy(packet)
                candidate["knowledge"]["matches"] = (
                    kept_matches + [deepcopy(match)]
                )

                if packet_size(candidate) <= max_chars:
                    kept_matches.append(deepcopy(match))
                else:
                    omitted_matches.append(deepcopy(match))

            packet["knowledge"]["matches"] = kept_matches

            packet["omissions"]["knowledge_matches"] = [
                str(
                    match.get(
                        "knowledge_id",
                        match.get("id", "<unknown>"),
                    )
                )
                for match in omitted_matches
            ]

        elif _add_if_fits(
            packet,
            "knowledge",
            selected_knowledge,
            max_chars,
        ):
            pass
        else:
            packet["knowledge"] = None
            packet["omissions"]["sections"].append(
                "knowledge"
            )

    # ------------------------------------------------------------
    # 4. ARTIFACTS
    # ------------------------------------------------------------

    deduped_artifacts = _dedupe_artifacts(
        source.get("artifacts") or []
    )

    selected_artifacts, omitted_artifacts = _append_list_if_fits(
        packet,
        "artifacts",
        deduped_artifacts,
        max_chars,
    )

    packet["omissions"]["artifacts"] = [
        str(
            row.get(
                "artifact",
                row.get("sha256", "<unknown>"),
            )
        )
        for row in omitted_artifacts
    ]

    # ------------------------------------------------------------
    # 5. FAMILY
    # ------------------------------------------------------------

    if not _add_if_fits(
        packet,
        "family",
        source.get("family") or [],
        max_chars,
    ):
        packet["omissions"]["sections"].append("family")

    # ------------------------------------------------------------
    # 6. SIMILARITIES
    # ------------------------------------------------------------

    if not _add_if_fits(
        packet,
        "similarities",
        source.get("similarities") or [],
        max_chars,
    ):
        packet["omissions"]["sections"].append(
            "similarities"
        )

    # ------------------------------------------------------------
    # 7. RELATED OUTPUTS
    # ------------------------------------------------------------

    if not _add_if_fits(
        packet,
        "related_outputs",
        source.get("related_outputs") or [],
        max_chars,
    ):
        packet["omissions"]["sections"].append(
            "related_outputs"
        )

    # ------------------------------------------------------------
    # 8. SYSTEM METRICS
    # ------------------------------------------------------------

    selected_metrics, omitted_metrics = _append_list_if_fits(
        packet,
        "system_metrics",
        _select_metrics(
            source.get("system_metrics") or []
        ),
        max_chars,
    )

    packet["omissions"]["system_metrics"] = [
        str(row.get("timestamp", "<unknown>"))
        for row in omitted_metrics
    ]

    # ------------------------------------------------------------
    # 9. SIBLING SOURCE
    # ------------------------------------------------------------

    selected_sources = _select_source_files(
        source_files,
        target_name,
        intent,
    )

    siblings = {
        name: value
        for name, value in selected_sources.items()
        if name != target_name
    }

    selected_siblings, omitted_sources = (
        _append_source_files_if_fits(
            packet,
            siblings,
            max_chars,
        )
    )

    packet["omissions"]["source_files"] = omitted_sources

    # ------------------------------------------------------------
    # FINAL AUDIT
    # ------------------------------------------------------------

    actual_size = packet_size(packet)

    packet["selection"]["evidence_budget"] = evidence_budget
    packet["selection"]["metadata_reserve"] = metadata_reserve

    packet["selection"]["actual_chars"] = actual_size
    packet["selection"]["budget_remaining"] = max(
        0,
        max_chars - actual_size,
    )
    packet["selection"][
        "budget_exceeded_by_required_evidence"
    ] = required_evidence_exceeds_budget

    # If the target itself is larger than the budget, the selector
    # preserves it intact and explicitly reports the condition.
    if required_evidence_exceeds_budget:
        packet["omissions"]["sections"].append(
            "budget_exceeded_by_required_evidence"
        )

    # Metadata is already part of the packet. Recalculate once more
    # so reported size reflects the final structure.
    actual_size = packet_size(packet)

    packet["selection"]["actual_chars"] = actual_size
    packet["selection"]["budget_remaining"] = max(
        0,
        max_chars - actual_size,
    )

    # ------------------------------------------------------------
    # FINAL HARD-BUDGET ENFORCEMENT
    # ------------------------------------------------------------
    #
    # All earlier selection decisions are provisional. The final
    # serialized packet is authoritative. Remove optional material
    # in reverse priority until the completed packet fits.
    #
    # The target source is required and is never removed here.

    def _remove_last_list_item(key: str) -> bool:
        values = packet.get(key)

        if not isinstance(values, list) or not values:
            return False

        values.pop()
        return True

    optional_list_priority = [
        "system_metrics",
        "related_outputs",
        "similarities",
        "family",
        "artifacts",
        "runs",
    ]

    while packet_size(packet) > max_chars:

        changed = False

        # Remove lower-priority list records first.
        for key in optional_list_priority:
            if _remove_last_list_item(key):
                changed = True
                packet["omissions"]["sections"].append(
                    f"budget_trim:{key}"
                )
                break

        if changed:
            continue

        # Knowledge matches are individually removable.
        if packet.get("knowledge"):
            matches = packet["knowledge"].get("matches")

            if isinstance(matches, list) and matches:
                removed = matches.pop()

                packet["omissions"][
                    "knowledge_matches"
                ].append(
                    str(
                        removed.get(
                            "knowledge_id",
                            removed.get("id", "<unknown>"),
                        )
                    )
                )

                continue

        # Sibling source is optional. Remove siblings but never
        # remove the required target source.
        source_names = list(packet["source_files"])

        removable_sources = [
            name
            for name in source_names
            if name != target_name
        ]

        if removable_sources:
            name = removable_sources[-1]
            del packet["source_files"][name]
            packet["omissions"]["source_files"].append(name)
            continue

        # If we reach this point, only required evidence remains.
        break

    actual_size = packet_size(packet)

    packet["selection"]["actual_chars"] = actual_size
    packet["selection"]["budget_remaining"] = max(
        0,
        max_chars - actual_size,
    )

    packet["selection"][
        "budget_exceeded_by_required_evidence"
    ] = (
        actual_size > max_chars
    )

    if actual_size > max_chars:
        if "budget_exceeded_by_required_evidence" not in (
            packet["omissions"]["sections"]
        ):
            packet["omissions"]["sections"].append(
                "budget_exceeded_by_required_evidence"
            )

    return packet


def packet_size(packet: dict) -> int:
    import json

    return len(
        json.dumps(
            packet,
            ensure_ascii=False,
            default=str,
            separators=(",", ":"),
        )
    )


__all__ = [
    "DEFAULT_MAX_CHARS",
    "select_reasoning_context",
    "packet_size",
]
