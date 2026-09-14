"""CLI for the RichardLab π Forensics experiment."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import build_identity_cases, probability_by_position, search_digits


def main() -> int:
    p = argparse.ArgumentParser(description="RichardLab π Forensics")
    p.add_argument("--pi-dir", required=True, help="Directory containing pi_digits_*.txt")
    p.add_argument("--birthday", default="01211981", help="Digits only, e.g. 01211981")
    p.add_argument("--first-name", default="RICHARD")
    p.add_argument("--last-name", default="SPRAGUE")
    p.add_argument("--out", default="pi_forensics_results.json")
    args = p.parse_args()

    results = []
    for case in build_identity_cases(args.birthday, args.first_name, args.last_name):
        hit = search_digits(case.sequence, args.pi_dir)
        results.append({
            "name": case.name,
            "encoding": case.encoding,
            "sequence": case.sequence,
            "length": len(case.sequence),
            "found": hit.found,
            "position": hit.position,
            "context": hit.context,
            "expected_wait_scale": 10 ** len(case.sequence),
            "approx_probability_by_position": (
                probability_by_position(case.sequence, hit.position)
                if hit.position else 0.0
            ),
        })

    Path(args.out).write_text(
        json.dumps(results, indent=2),
        encoding="utf-8",
    )

    for r in results:
        status = f"FOUND at {r['position']}" if r["found"] else "NOT FOUND"
        print(f"{r['name']:<32} {status:<24} {r['sequence']}")

    print(f"\nWrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
