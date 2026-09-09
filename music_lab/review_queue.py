#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a human-review queue from RichardLab music parsing results."
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=Path("music_lab/music_parsed.json"),
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("music_lab/music_review_queue.json"),
    )

    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Input file not found: {args.input}")

    records = json.loads(
        args.input.read_text(encoding="utf-8")
    )

    review = []

    for index, record in enumerate(records, start=1):
        confidence = record.get("confidence")

        if confidence == "high":
            continue

        artist = record.get("artist")
        title = record.get("title")
        method = record.get("parse_method")

        if artist:
            review_type = "PARSER_REVIEW"
            reason = "Artist was inferred, but parser confidence is not high."
        else:
            review_type = "ARTIST_UNKNOWN"
            reason = "Filename provides a title but no reliable artist."

        review.append(
            {
                "review_id": len(review) + 1,
                "source_index": index,
                "review_type": review_type,
                "confidence": confidence,
                "artist": artist,
                "title": title,
                "version": record.get("version", []),
                "parse_method": method,
                "reason": reason,
                "filename": record.get("filename"),
                "path": record.get("path"),
                "decision": None,
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)

    args.output.write_text(
        json.dumps(
            review,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    parser_review = sum(
        r["review_type"] == "PARSER_REVIEW"
        for r in review
    )

    unknown = sum(
        r["review_type"] == "ARTIST_UNKNOWN"
        for r in review
    )

    print("RichardLab Music Review Queue")
    print("=" * 50)
    print(f"Tracks requiring review: {len(review)}")
    print(f"Parser review:            {parser_review}")
    print(f"Artist unknown:           {unknown}")
    print(f"Output:                   {args.output}")


if __name__ == "__main__":
    main()
