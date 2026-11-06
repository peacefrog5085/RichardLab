"""Build an offline Markdown review from a supplied synthetic evidence packet."""

import argparse
import hashlib
import html
import json
import os
import re
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile


MAX_JSON_BYTES = 64 * 1024


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


def read_json(path, label):
    with path.open("rb") as handle:
        data = handle.read(MAX_JSON_BYTES + 1)
    if len(data) > MAX_JSON_BYTES:
        raise ValueError(f"{label} exceeds 64 KiB")
    try:
        return json.loads(data.decode("utf-8")), data
    except (ValueError, RecursionError):
        raise ValueError(f"{label} must be valid UTF-8 JSON") from None


def read_review(path, packet_digest):
    review, _ = read_json(path, "Review")
    if not isinstance(review, dict):
        raise ValueError("Review must be an object")
    digest = review.get("packet_sha256")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
        raise ValueError("Review packet_sha256 must be a 64-digit hexadecimal digest")
    if digest.lower() != packet_digest:
        raise ValueError("Review digest does not match packet")
    return (
        require_text(review.get("disposition"), "Review disposition"),
        require_text(review.get("note"), "Review note"),
    )


def match_report(path, packet_digest):
    with path.open("rb") as handle:
        # The question can expand up to sixfold when escaped as Markdown.
        header = handle.read(6 * MAX_JSON_BYTES + 1024).split(b"\n", 7)
    lines = [line.removesuffix(b"\r") for line in header[:7]]
    digest = None
    if (
        len(header) == 8
        and lines[:4] == [b"# Echo investigation", b"", b"**Synthetic evidence**", b""]
        and lines[4].startswith(b"**Question** ")
        and lines[5] == b""
    ):
        digest = re.fullmatch(rb"\*\*Packet SHA-256\*\* `([0-9a-fA-F]{64})`", lines[6])
    if digest is None:
        raise ValueError("Report header must contain a valid Packet SHA-256")
    if digest[1].lower() != packet_digest.encode("ascii"):
        raise ValueError("Report packet digest does not match the supplied packet")


def render_report(packet, review=None, *, packet_digest):
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
        f"**Packet SHA-256** `{packet_digest}`", "",
    ]
    if review is None:
        lines.extend(["**Human review: pending**", ""])
    else:
        disposition, note = review
        lines.extend([
            "**Human review: recorded**", "",
            f"**Reviewer disposition** {markdown(disposition)}",
            f"**Reviewer note** {markdown(note)}", "",
        ])
    lines.extend([
        "Citation relationships and origins are supplied by the packet author.",
        "",
    ])
    for number, claim in enumerate(require_items(packet.get("claims"), "Claims"), 1):
        claim_text = require_text(claim.get("text"), "Claim")
        if "citations" not in claim:
            raise ValueError(f"Missing citations in claim {number}")
        citations = claim["citations"]
        if not isinstance(citations, list):
            raise ValueError(f"Citations in claim {number} must be a list")
        if any(not isinstance(citation, dict) for citation in citations):
            raise ValueError(f"Citations in claim {number} must contain objects")
        lines.extend([f"## Claim {number}", "", markdown(claim_text), ""])
        origins = set()
        relations = set()
        for citation_number, citation in enumerate(citations, 1):
            source_id = require_text(citation.get("source"), f"Citation {citation_number} source in claim {number}")
            passage_id = require_text(citation.get("passage"), f"Citation {citation_number} passage in claim {number}")
            quote = require_text(citation.get("quote"), f"Citation {citation_number} quote in claim {number}")
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
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output", type=Path, help="Local Markdown report path")
    mode.add_argument("--check", action="store_true", help="Validate inputs without writing a report")
    mode.add_argument("--review-template", action="store_true", help="Print draft review JSON")
    mode.add_argument("--match-report", type=Path, help="Compare a saved report's packet digest")
    parser.add_argument("--review", type=Path, help="Local JSON review bound to the packet digest")
    args = parser.parse_args(argv)
    if args.review_template and args.review is not None:
        parser.error("--review is not allowed with argument --review-template")
    if args.match_report is not None and args.review is not None:
        parser.error("--review is not allowed with argument --match-report")
    try:
        if args.output is not None:
            if args.output.suffix.lower() != ".md":
                raise ValueError("Output must have a .md extension")
            output_path = args.output.resolve()
            if args.packet.resolve() == output_path or (
                args.review is not None and args.review.resolve() == output_path
            ):
                raise ValueError("Input and output must be separate files")
        packet, packet_bytes = read_json(args.packet, "Packet")
        packet_digest = hashlib.sha256(packet_bytes).hexdigest()
        if args.match_report is not None:
            match_report(args.match_report, packet_digest)
            print("Report packet digest matches.")
            return 0
        review = read_review(args.review, packet_digest) if args.review is not None else None
        report = render_report(packet, review, packet_digest=packet_digest)
        if args.output is None:
            report.encode("utf-8")
            if args.review_template:
                print(json.dumps({
                    "packet_sha256": packet_digest,
                    "disposition": "",
                    "note": "",
                }, indent=2))
            else:
                print("Validation passed.")
        else:
            publish_report(args.output, report)
    except UnicodeError:
        print("Echo investigation: Packet or review text cannot be encoded as UTF-8.", file=sys.stderr)
        return 1
    except OSError:
        action = "read an input" if args.output is None else "read an input or publish the report"
        print(f"Echo investigation failed to {action}.", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"Echo investigation: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
