"""Build an offline Markdown review from a supplied evidence packet."""

import argparse
import hashlib
import html
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile


MAX_JSON_BYTES = 64 * 1024
MAX_SOURCE_BYTES = 1024 * 1024


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
        and lines[:2] == [b"# Echo investigation", b""]
        and lines[2] in (b"**Synthetic evidence**", b"**Real evidence**")
        and lines[3] == b""
        and lines[4].startswith(b"**Question** ")
        and lines[5] == b""
    ):
        digest = re.fullmatch(rb"\*\*Packet SHA-256\*\* `([0-9a-fA-F]{64})`", lines[6])
    if digest is None:
        raise ValueError("Report header must contain a valid Packet SHA-256")
    if digest[1].lower() != packet_digest.encode("ascii"):
        raise ValueError("Report packet digest does not match the supplied packet")


def source_line_suffixes(source, passages):
    if "line_ranges" not in source:
        return {}
    if "path" not in source:
        raise ValueError("Source line ranges require a source path")
    ranges = source["line_ranges"]
    if not isinstance(ranges, dict):
        raise ValueError("Source line ranges must be keyed by passage ID")
    suffixes = {}
    for passage_id, bounds in ranges.items():
        if passage_id not in passages:
            raise ValueError("Unknown passage in source line ranges")
        if (
            not isinstance(bounds, list)
            or len(bounds) != 2
            or any(type(bound) is not int for bound in bounds)
            or not 1 <= bounds[0] <= bounds[1]
        ):
            raise ValueError("Source line ranges must contain two positive, ordered integers")
        start, end = bounds
        suffixes[passage_id] = f":{start}" if start == end else f":{start}–{end}"
    return suffixes


def read_local_git(*arguments, error):
    try:
        result = subprocess.run(
            ["git", "--no-lazy-fetch", "--no-replace-objects", *arguments],
            env={**os.environ, "GIT_ALLOW_PROTOCOL": ""},
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=10, check=True,
        )
    except (OSError, subprocess.SubprocessError):
        raise ValueError(error) from None
    return result.stdout


def check_pinned_sources(packet):
    # The renderer has already validated the packet, including paths and ranges.
    for source in packet["sources"]:
        commit = source.get("commit")
        if not isinstance(commit, str) or not re.fullmatch(r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})", commit):
            raise ValueError("Source commit must be a full Git object ID")
        passages = source["passages"]
        ranges = source.get("line_ranges", {})
        if ranges.keys() != passages.keys():
            raise ValueError("Source check requires a line range for every passage")

        commit = commit.lower()
        resolved = read_local_git("rev-parse", "--verify", f"{commit}^{{commit}}",
                                  error="Pinned Git commit is unavailable")
        if resolved.strip() != commit.encode("ascii"):
            raise ValueError("Source commit must be a full Git object ID for a commit")
        object_spec = f"{commit}:{source['path']}"
        size = read_local_git("cat-file", "-s", object_spec, error="Pinned Git source file is unavailable")
        if int(size) > MAX_SOURCE_BYTES:
            raise ValueError("Pinned Git source file exceeds 1 MiB")
        blob = read_local_git("cat-file", "blob", object_spec, error="Pinned Git source is not a readable blob")
        try:
            lines = blob.decode("utf-8").replace("\r\n", "\n").removesuffix("\n").split("\n")
        except UnicodeDecodeError:
            raise ValueError("Pinned Git source file must be UTF-8") from None
        for passage_id, passage in passages.items():
            start, end = ranges[passage_id]
            if end > len(lines) or passage.replace("\r\n", "\n") not in "\n".join(lines[start - 1:end]):
                raise ValueError("Passage does not match pinned Git lines")


def render_report(packet, review=None, *, packet_digest):
    if not isinstance(packet, dict):
        raise ValueError("Packet must be an object")
    evidence_kind = packet.get("evidence_kind", "synthetic")
    if evidence_kind not in ("synthetic", "real"):
        raise ValueError("Evidence kind must be synthetic or real")
    question = require_text(packet.get("question"), "Question")
    sources = {}
    for source in require_items(packet.get("sources"), "Sources"):
        source_id = require_text(source.get("id"), "Source ID")
        origin = require_text(source.get("origin"), "Source origin").strip().casefold()
        location = markdown(origin)
        if "path" in source:
            path = source["path"]
            if (
                not isinstance(path, str)
                or not path.isprintable()
                or "\\" in path
                or ":" in path
                or any(part in ("", ".", "..") for part in path.split("/"))
            ):
                raise ValueError("Source path must be repository-relative")
            location += f", {markdown(path)}"
        passages = source.get("passages")
        if source_id in sources:
            raise ValueError("Duplicate source ID")
        if not isinstance(passages, dict) or not passages:
            raise ValueError("Source must contain passages keyed by ID")
        for passage_id, passage in passages.items():
            require_text(passage_id, "Passage ID")
            require_text(passage, "Passage")
        sources[source_id] = (origin, location, passages, source_line_suffixes(source, passages))

    lines = [
        "# Echo investigation", "", f"**{evidence_kind.capitalize()} evidence**", "",
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
            origin, location, passages, line_suffixes = sources[source_id]
            if passage_id not in passages:
                raise ValueError(f"Unknown passage in claim {number}")
            if quote not in passages[passage_id]:
                raise ValueError(f"Quote mismatch in claim {number}")
            if relation not in ("supports", "contradicts"):
                raise ValueError(f"Invalid citation relationship in claim {number}")
            origins.add(origin)
            relations.add(relation)
            reference = markdown(f"{source_id}/{passage_id}")
            locator = location + line_suffixes.get(passage_id, "")
            lines.append(f"- **{reference}** ({locator}, {relation}) — {markdown(quote)}")
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
    parser.add_argument("packet", type=Path, help="Local JSON packet with evidence excerpts")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output", type=Path, help="Local Markdown report path")
    mode.add_argument("--check", action="store_true", help="Validate inputs without writing a report")
    mode.add_argument("--check-sources", action="store_true", help="Verify passages against local Git commits")
    mode.add_argument("--review-template", action="store_true", help="Print draft review JSON")
    mode.add_argument("--match-report", type=Path, help="Compare a saved report's packet digest")
    mode.add_argument("--verify-report", type=Path, help="Compare a saved report with regenerated Markdown")
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
            report_bytes = report.encode("utf-8")
            if args.check_sources:
                check_pinned_sources(packet)
                print("Source passages verified.")
            elif args.verify_report is not None:
                with args.verify_report.open("rb") as handle:
                    saved_bytes = handle.read(len(report_bytes) + 1)
                if saved_bytes != report_bytes:
                    position = next(
                        (index for index, (saved, expected) in
                         enumerate(zip(saved_bytes, report_bytes), start=1) if saved != expected),
                        min(len(saved_bytes), len(report_bytes)) + 1,
                    )
                    raise ValueError(
                        "Saved report does not match regenerated Markdown "
                        f"(first differing byte position: {position})"
                    )
                print("Saved report matches regenerated Markdown.")
            elif args.review_template:
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
