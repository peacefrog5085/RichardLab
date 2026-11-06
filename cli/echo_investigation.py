"""Build an offline Markdown review from a supplied synthetic evidence packet."""

import argparse
import html
import json
import os
import re
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile


MAX_PACKET_BYTES = 64 * 1024


def require_text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be nonempty text")
    return value


def require_items(value, field):
    if not isinstance(value, list) or not value:
        raise ValueError(f"{field} must be a nonempty list")
    if any(not isinstance(item, dict) for item in value):
        raise ValueError(f"{field} must contain objects")
    return value


def markdown(value):
    # Keep packet content inline and prevent it from creating links or HTML.
    return re.sub(r"([\\\x60*_\[\]~!])", r"\\\1", html.escape(" ".join(value.split())))


def render_report(packet):
    if not isinstance(packet, dict):
        raise ValueError("Packet must be an object")
    question = require_text(packet.get("question"), "Question")
    sources = {}
    for source in require_items(packet.get("sources"), "Sources"):
        source_id = require_text(source.get("id"), "Source ID")
        origin = require_text(source.get("origin"), "Source origin").strip().casefold()
        passages = source.get("passages")
        if source_id in sources:
            raise ValueError("Duplicate source ID")
        if not isinstance(passages, dict) or not passages:
            raise ValueError("Source must contain passages keyed by ID")
        for passage_id, passage in passages.items():
            require_text(passage_id, "Passage ID")
            require_text(passage, "Passage")
        sources[source_id] = (origin, passages)

    lines = [
        "# Echo investigation", "", "**Synthetic evidence**", "",
        f"**Question** {markdown(question)}", "",
        "**Human review: pending**", "",
        "Citation relationships and origins are supplied by the packet author.",
        "",
    ]
    for number, claim in enumerate(require_items(packet.get("claims"), "Claims"), 1):
        claim_text = require_text(claim.get("text"), "Claim")
        citations = claim.get("citations")
        if citations != []:
            require_items(citations, "Citations")
        lines.extend([f"## Claim {number}", "", markdown(claim_text), ""])
        origins = set()
        relations = set()
        for citation in citations:
            source_id = require_text(citation.get("source"), "Citation source")
            passage_id = require_text(citation.get("passage"), "Citation passage")
            quote = require_text(citation.get("quote"), "Citation quote")
            relation = citation.get("relation")
            if source_id not in sources:
                raise ValueError(f"Unknown source in claim {number}")
            origin, passages = sources[source_id]
            if passage_id not in passages:
                raise ValueError(f"Unknown passage in claim {number}")
            if quote not in passages[passage_id]:
                raise ValueError(f"Quote mismatch in claim {number}")
            if relation not in ("supports", "contradicts"):
                raise ValueError(f"Invalid citation relationship in claim {number}")
            origins.add(origin)
            relations.add(relation)
            reference = markdown(f"{source_id}/{passage_id}")
            lines.append(f"- **{reference}** ({markdown(origin)}, {relation}) — {markdown(quote)}")
        if citations:
            lines.extend(["", f"{len(origins)} distinct origins across {len(citations)} citations."])
        if len(origins) < len(citations):
            lines.append("Duplicate origins — citations sharing an origin count once.")
        if relations == {"supports", "contradicts"}:
            lines.append("Conflicting evidence — retain both accounts for review.")
        if "supports" not in relations:
            lines.append("Unsupported claim — the packet supplies no supporting citation.")
        lines.append("")
    lines.extend([
        "## Evidence needed", "",
        "Verify the stated origins and citation relationships. Resolve any conflicting",
        "accounts before drawing a conclusion.", "",
    ])
    return "\n".join(lines)


def publish_report(path, report):
    temporary_path = None
    try:
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=path.parent,
            suffix=".tmp", delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(report)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path, help="Local JSON packet with synthetic excerpts")
    parser.add_argument("--output", type=Path, required=True, help="Local Markdown report path")
    args = parser.parse_args(argv)
    try:
        if args.output.suffix.lower() != ".md":
            raise ValueError("Output must have a .md extension")
        if args.packet.resolve() == args.output.resolve():
            raise ValueError("Input and output must be separate files")
        with args.packet.open("rb") as handle:
            data = handle.read(MAX_PACKET_BYTES + 1)
        if len(data) > MAX_PACKET_BYTES:
            raise ValueError("Packet exceeds 64 KiB")
        try:
            packet = json.loads(data.decode("utf-8"))
        except (ValueError, RecursionError):
            raise ValueError("Packet must be valid UTF-8 JSON") from None
        publish_report(args.output, render_report(packet))
    except (OSError, UnicodeError):
        print("Echo investigation failed to read the packet or publish the report.", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Echo investigation: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
