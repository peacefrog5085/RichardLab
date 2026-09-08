#!/usr/bin/env python3

import argparse
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_DIR = ROOT / "knowledge"
STORE = KNOWLEDGE_DIR / "knowledge.jsonl"


VALID_KINDS = {
    "observation",
    "known_failure",
    "known_good",
    "constraint",
    "recommendation",
    "decision",
    "instruction",
    "preference",
    "hypothesis",
    "conclusion",
}

VALID_STATUSES = {
    "passed",
    "failed",
    "partial",
    "inconclusive",
    "active",
    "superseded",
    "uncertain",
}

VALID_CONFIDENCE = {"low", "medium", "high"}

VALID_ACTIONS = {
    "BLOCK",
    "REUSE",
    "CAUTION",
    "REVIEW",
    "NO_KNOWN_MEMORY",
}


def now():
    return datetime.now(timezone.utc).isoformat()


def ensure_store():
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    STORE.touch(exist_ok=True)


def normalize(text):
    return re.sub(r"\s+", " ", str(text).strip().lower())


def tokenize(text):
    return {
        token
        for token in re.findall(r"[a-z0-9_./:-]+", normalize(text))
        if len(token) > 2
    }


def load_all():
    ensure_store()
    records = []

    with STORE.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                print(
                    f"WARNING: ignoring malformed knowledge line "
                    f"{line_number}: {exc}",
                    file=sys.stderr,
                )
                continue

            # Backward compatibility for v1 memories.
            record.setdefault("knowledge_version", 1)
            record.setdefault("status", "active")
            record.setdefault("conditions", [])
            record.setdefault("applies_when", [])
            record.setdefault("do_not", [])
            record.setdefault("evidence", [])
            record.setdefault("related", [])
            record.setdefault("supersedes", "")
            record.setdefault("source", {})
            record.setdefault("created_at", "")
            record.setdefault("updated_at", "")

            records.append(record)

    return records


def append(record):
    ensure_store()

    with STORE.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
        )


def make_id():
    return "K-" + uuid.uuid4().hex[:12].upper()


def split_list(value, separator=","):
    if not value:
        return []

    return [
        item.strip()
        for item in value.split(separator)
        if item.strip()
    ]


def build_record(args):
    kind = args.kind.strip().lower()
    status = args.status.strip().lower()
    confidence = args.confidence.strip().lower()

    if kind not in VALID_KINDS:
        raise ValueError(
            f"Invalid kind '{kind}'. "
            f"Choose from: {', '.join(sorted(VALID_KINDS))}"
        )

    if status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid status '{status}'. "
            f"Choose from: {', '.join(sorted(VALID_STATUSES))}"
        )

    if confidence not in VALID_CONFIDENCE:
        raise ValueError(
            f"Invalid confidence '{confidence}'. "
            f"Choose from: {', '.join(sorted(VALID_CONFIDENCE))}"
        )

    return {
        "knowledge_version": 2,
        "knowledge_id": make_id(),
        "created_at": now(),
        "updated_at": now(),
        "kind": kind,
        "status": status,
        "subject": args.subject,
        "finding": args.finding,
        "reason": args.reason or "",
        "action": args.action or "",
        "do_not": split_list(args.do_not, "|"),
        "conditions": split_list(args.conditions, "|"),
        "applies_when": split_list(args.applies_when, "|"),
        "confidence": confidence,
        "tags": split_list(args.tags),
        "source": {
            "type": args.source_type,
            "run_id": args.run_id or "",
            "experiment": args.experiment or "",
            "git_commit": args.git_commit or "",
            "source_sha256": args.source_sha256 or "",
        },
        "evidence": split_list(args.evidence, "|"),
        "supersedes": args.supersedes or "",
        "related": split_list(args.related),
    }


def searchable_text(record):
    source = record.get("source", {})

    parts = [
        record.get("kind", ""),
        record.get("status", ""),
        record.get("subject", ""),
        record.get("finding", ""),
        record.get("reason", ""),
        record.get("action", ""),
        " ".join(record.get("do_not", [])),
        " ".join(record.get("conditions", [])),
        " ".join(record.get("applies_when", [])),
        " ".join(record.get("tags", [])),
        " ".join(record.get("evidence", [])),
        source.get("experiment", ""),
        source.get("run_id", ""),
    ]

    return " ".join(parts)


def similarity(query, record):
    query_tokens = tokenize(query)
    record_tokens = tokenize(searchable_text(record))

    if not query_tokens or not record_tokens:
        return 0.0

    overlap = query_tokens & record_tokens

    if not overlap:
        return 0.0

    return len(overlap) / len(query_tokens)


def search_records(query, minimum=0.0):
    records = load_all()
    results = []

    for record in records:
        if record.get("status") == "superseded":
            continue

        score = similarity(query, record)

        if score >= minimum:
            results.append((score, record))

    results.sort(
        key=lambda item: (
            item[0],
            {"high": 3, "medium": 2, "low": 1}.get(
                item[1].get("confidence"), 0
            ),
            item[1].get("updated_at", ""),
        ),
        reverse=True,
    )

    return results


def recommendation(results):
    if not results:
        return {
            "decision": "NO_KNOWN_MEMORY",
            "reason": "No sufficiently similar knowledge was found.",
        }

    strongest = results[0][1]
    kind = normalize(strongest.get("kind", ""))
    status = normalize(strongest.get("status", ""))
    confidence = normalize(strongest.get("confidence", "medium"))

    # Explicit constraints and known failures are strongest.
    if kind in {"constraint", "known_failure"} or status == "failed":
        return {
            "decision": "BLOCK",
            "reason": (
                strongest.get("reason")
                or strongest.get("finding")
                or "A previous failure or active constraint applies."
            ),
            "knowledge_id": strongest.get("knowledge_id"),
        }

    if kind in {"known_good", "recommendation"} or status == "passed":
        return {
            "decision": "REUSE",
            "reason": (
                strongest.get("finding")
                or "A previous successful approach was found."
            ),
            "knowledge_id": strongest.get("knowledge_id"),
        }

    if status in {"partial", "inconclusive", "uncertain"}:
        return {
            "decision": "CAUTION",
            "reason": (
                strongest.get("finding")
                or "Related knowledge exists but is not conclusive."
            ),
            "knowledge_id": strongest.get("knowledge_id"),
        }

    if confidence == "low":
        return {
            "decision": "REVIEW",
            "reason": (
                strongest.get("finding")
                or "Low-confidence knowledge exists and should be reviewed."
            ),
            "knowledge_id": strongest.get("knowledge_id"),
        }

    return {
        "decision": "REVIEW",
        "reason": (
            strongest.get("finding")
            or "Related knowledge exists and should be reviewed."
        ),
        "knowledge_id": strongest.get("knowledge_id"),
    }


def print_record(record, score=None):
    if score is not None:
        print(f"Score      : {score:.2f}")

    print(f"ID         : {record.get('knowledge_id')}")
    print(f"Version    : {record.get('knowledge_version', 1)}")
    print(f"Kind       : {record.get('kind')}")
    print(f"Status     : {record.get('status')}")
    print(f"Subject    : {record.get('subject')}")
    print(f"Finding    : {record.get('finding')}")

    if record.get("reason"):
        print(f"Reason     : {record['reason']}")

    if record.get("action"):
        print(f"Action     : {record['action']}")

    if record.get("do_not"):
        print("Do not     :")
        for item in record["do_not"]:
            print(f"  - {item}")

    if record.get("conditions"):
        print("Conditions :")
        for item in record["conditions"]:
            print(f"  - {item}")

    if record.get("applies_when"):
        print("Applies when:")
        for item in record["applies_when"]:
            print(f"  - {item}")

    print(f"Confidence : {record.get('confidence')}")

    if record.get("tags"):
        print(f"Tags       : {', '.join(record['tags'])}")

    source = record.get("source", {})

    if source.get("run_id"):
        print(f"Run ID     : {source['run_id']}")

    if source.get("experiment"):
        print(f"Experiment : {source['experiment']}")

    if source.get("git_commit"):
        print(f"Git commit : {source['git_commit']}")

    if source.get("source_sha256"):
        print(f"Source SHA : {source['source_sha256']}")

    if record.get("evidence"):
        print("Evidence   :")
        for item in record["evidence"]:
            print(f"  - {item}")

    if record.get("supersedes"):
        print(f"Supersedes : {record['supersedes']}")

    if record.get("related"):
        print(f"Related    : {', '.join(record['related'])}")

    print(f"Created    : {record.get('created_at')}")
    print(f"Updated    : {record.get('updated_at')}")


def cmd_add(args):
    record = build_record(args)
    append(record)

    print("KNOWLEDGE RECORDED")
    print("────────────────────────────────────────")
    print_record(record)


def cmd_search(args):
    results = search_records(args.query, args.minimum)

    if not results:
        print("NO MATCHING KNOWLEDGE")
        return 1

    print(f"KNOWLEDGE SEARCH: {args.query}")
    print("────────────────────────────────────────")

    for index, (score, record) in enumerate(results[:args.limit], 1):
        print()
        print(f"[{index}]")
        print_record(record, score)

    return 0


def cmd_check(args):
    results = search_records(args.query, args.minimum)
    decision = recommendation(results)

    print("KNOWLEDGE CHECK")
    print("────────────────────────────────────────")
    print(f"Query      : {args.query}")
    print(f"Decision   : {decision['decision']}")
    print(f"Reason     : {decision['reason']}")

    if decision.get("knowledge_id"):
        print(f"Knowledge  : {decision['knowledge_id']}")

    if results:
        print()
        print("Strongest matching memory:")
        print_record(results[0][1], results[0][0])

    return 0


def cmd_stats(_args):
    records = load_all()

    by_kind = {}
    by_status = {}
    by_confidence = {}

    for record in records:
        kind = record.get("kind", "unknown")
        status = record.get("status", "unknown")
        confidence = record.get("confidence", "unknown")

        by_kind[kind] = by_kind.get(kind, 0) + 1
        by_status[status] = by_status.get(status, 0) + 1
        by_confidence[confidence] = by_confidence.get(confidence, 0) + 1

    print("RICHARDLAB KNOWLEDGE")
    print("────────────────────────────────────────")
    print(f"Store       : {STORE}")
    print(f"Total       : {len(records)}")

    print()
    print("By kind:")
    for key, value in sorted(by_kind.items()):
        print(f"  {key}: {value}")

    print()
    print("By status:")
    for key, value in sorted(by_status.items()):
        print(f"  {key}: {value}")

    print()
    print("By confidence:")
    for key, value in sorted(by_confidence.items()):
        print(f"  {key}: {value}")


def add_common_arguments(parser):
    parser.add_argument("--kind", required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--finding", required=True)
    parser.add_argument("--reason", default="")
    parser.add_argument("--action", default="")
    parser.add_argument("--do-not", default="")
    parser.add_argument("--conditions", default="")
    parser.add_argument("--applies-when", default="")
    parser.add_argument(
        "--confidence",
        choices=sorted(VALID_CONFIDENCE),
        default="medium",
    )
    parser.add_argument("--tags", default="")
    parser.add_argument("--source-type", default="unknown")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--experiment", default="")
    parser.add_argument("--git-commit", default="")
    parser.add_argument("--source-sha256", default="")
    parser.add_argument("--evidence", default="")
    parser.add_argument("--supersedes", default="")
    parser.add_argument("--related", default="")


def main():
    parser = argparse.ArgumentParser(
        description="RichardLab durable knowledge and memory engine."
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    add_parser = subparsers.add_parser("add")
    add_common_arguments(add_parser)
    add_parser.set_defaults(func=cmd_add)

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("query")
    search_parser.add_argument("--minimum", type=float, default=0.20)
    search_parser.add_argument("--limit", type=int, default=10)
    search_parser.set_defaults(func=cmd_search)

    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("query")
    check_parser.add_argument("--minimum", type=float, default=0.20)
    check_parser.set_defaults(func=cmd_check)

    stats_parser = subparsers.add_parser("stats")
    stats_parser.set_defaults(func=cmd_stats)

    args = parser.parse_args()

    try:
        return args.func(args)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
