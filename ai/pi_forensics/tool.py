"""RichardLab tool interface for the deterministic π Forensics experiment."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .core import (
    build_identity_cases,
    expected_wait,
    probability_by_position,
    search_digits,
)


def run_pi_forensics(
    pi_dir: str | Path,
    birthday: str = "01211981",
    first_name: str = "RICHARD",
    last_name: str = "SPRAGUE",
) -> dict[str, Any]:
    """Run the predetermined π Forensics identity matrix against a corpus."""

    cases = build_identity_cases(
        birthday,
        first_name=first_name,
        last_name=last_name,
    )

    results = []

    for case in cases:
        hit = search_digits(case.sequence, pi_dir)

        results.append(
            {
                "name": case.name,
                "encoding": case.encoding,
                "sequence": case.sequence,
                "length": len(case.sequence),
                "found": hit.found,
                "position": hit.position,
                "context": hit.context,
                "expected_wait": expected_wait(case.sequence),
                "probability_by_position": (
                    probability_by_position(
                        case.sequence,
                        hit.position,
                    )
                    if hit.position is not None
                    else None
                ),
            }
        )

    return {
        "experiment": "PI-FORENSICS-200M-001",
        "corpus": str(Path(pi_dir)),
        "birthday": birthday,
        "first_name": first_name,
        "last_name": last_name,
        "case_count": len(results),
        "results": results,
    }
