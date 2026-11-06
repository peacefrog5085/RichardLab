# Architecture

## Existing components

- The [local CLI](../../cli/richardlab.py) is the interactive entry point. Hive handles routing and worker policy. [Council](../../ai/hive/council.py) structures contradictions, unsupported claims, unknowns, and evidence needed.
- [Mission Control](../../mission_control/experiment_registry.py) enumerates experiments. The [evidence collector](../../ai/hive/evidence.py) collects experiment artifacts and run metadata. [Local knowledge](../../knowledge/knowledge.py) maintains experiment knowledge and recommendations.
- The [integration baseline](../integrations/BASELINE_AND_DEPLOYMENT.md) and [threat model](../security/THREAT_MODEL.md) govern connector boundaries. Registry entries describe policy. Live capability requires independent verification.

## Echo continuity

This directory owns engineering continuity. [Experiment registry](EXPERIMENT_REGISTRY.md) and [evidence index](EVIDENCE_INDEX.md) point to original records. The operator can carry sanitized Markdown across session surfaces.

## Offline investigation

From the repository root, run the [CLI](../../cli/echo_investigation.py) with the [synthetic packet](examples/synthetic-investigation.json) and an output path in an existing directory.

```powershell
python -m cli.echo_investigation docs/echo/examples/synthetic-investigation.json --output reports/echo-investigation.md
```

The UTF-8 JSON packet supplies one question, sources with origin labels and passage IDs, and claims with citations. Each citation supplies a source ID, passage ID, verbatim substring, and a relationship of `supports` or `contradicts`. The report uses inline display whitespace. The check compares the original quote against the original passage before formatting.

The reviewer carries forward Council's concepts of contradiction, unsupported claims, and evidence needed. It groups repeated origin labels, preserves competing evidence, and leaves human review pending. The packet author supplies the relationships and origins. An exact quote match checks textual provenance within the packet. Human review evaluates whether the citation supports the claim and whether origins are independent.

The CLI uses the Python standard library and local files. It validates and renders the packet before publishing the report through a same-directory atomic replacement. An existing report at the chosen path is replaced on success.

Set the top-level packet field `"evidence_kind": "real"` for excerpts from actual sources. Use `"synthetic"` for constructed examples. Packets without this field retain the synthetic label. The report displays the packet author's classification.

An optional source `path` such as `.github/workflows/report-privacy.yml` appears in its citations. Use a repository-relative path with forward slashes and omit dot and parent segments. The CLI displays the path as metadata and validates the quote against the supplied passage. Distinct origin counts still use the source's `origin` field.

If an older report omitted paths already present in the packet, regenerate the report for byte-for-byte verification. Its original packet digest still works with `--match-report`.

A source with a `path` can also supply `"line_ranges": {"P1": [12, 14]}`. The bounds are inclusive one-based integers, and each key must name a passage in that source. The citation displays the path followed by the range, or a single line number when the bounds match. These locators come from the packet author. Quote checking still uses the supplied passage text.

### Optional human review

Pass `--review reports/echo-review.json` to record a local review. The review file contains three fields.

```json
{
  "packet_sha256": "<64 hexadecimal digits from Get-FileHash>",
  "disposition": "Unresolved",
  "note": "Both accounts remain plausible."
}
```

On PowerShell, get the digest with `(Get-FileHash -Algorithm SHA256 docs/echo/examples/synthetic-investigation.json).Hash`. The digest covers the exact file bytes, including whitespace and line endings. A missing review argument leaves human review pending. A supplied review with an invalid or stale digest fails before publishing. The recorded disposition and note describe the reviewer's judgment, and the report still shows conflicting evidence. The digest provides packet matching only.

Every generated Markdown report includes a **Packet SHA-256** field. It matches the review template's `packet_sha256` for the same packet bytes, whether human review is pending or recorded.

### Check inputs before publishing

```powershell
python -m cli.echo_investigation docs/echo/examples/synthetic-investigation.json --check
```

To check the packet together with a local human review, run:

```powershell
python -m cli.echo_investigation docs/echo/examples/synthetic-investigation.json --check --review reports/echo-review.json
```

Check mode runs the same validation as report generation, including quote matching and review digest verification. It uses local files, leaves the packet and review intact, and creates or modifies no report files. Each claim must include a citations list. Use an explicit empty list for a claim with no evidence citations.

Choose exactly one of `--check`, `--check-sources`, `--output`, `--review-template`, `--match-report`, and `--verify-report`. Check mode prints `Validation passed.` and exits with code 0 on success. It prints an error to standard error and exits with code 1 for invalid or unreadable inputs. Command-line usage errors exit with code 2.

### Check pinned source passages

From the local Git checkout, run `python -m cli.echo_investigation PACKET.json --check-sources`. Every source needs a full Git commit ID in `commit`, a repository-relative `path`, and a `line_ranges` entry for every passage. The check compares each passage as an exact substring of its inclusive line range, normalizing CRLF to LF. It reads UTF-8 Git blobs up to 1 MiB, uses only objects already available locally, and writes no report. Use ordinary `--check` for packets without complete Git locators.

A passage mismatch reports the one-based source and passage positions in packet order and the requested line range. The diagnostic contains only those numbers and a fixed message.

### Start a review from a template

```powershell
python -m cli.echo_investigation docs/echo/examples/synthetic-investigation.json --review-template
```

The command validates the packet and prints draft JSON with the digest of the exact packet bytes. Copy it into a UTF-8 JSON file, fill in the blank disposition and note, then validate the completed file with `--check --review`. Template mode takes only the packet, writes no files, and emits no JSON if validation fails.

### Match a saved report to its packet

```powershell
python -m cli.echo_investigation docs/echo/examples/synthetic-investigation.json --match-report reports/echo-investigation.md
```

Match mode reads the digest from the generated report header and compares it with the exact packet bytes. It writes no files. A match exits with code 0. A mismatch or an unreadable or invalid input exits with code 1. The result covers the packet digest only. Use `--check` for packet and review validation.

### Verify a saved report against regenerated Markdown

```powershell
python -m cli.echo_investigation docs/echo/examples/synthetic-investigation.json --verify-report reports/echo-investigation.md
```

For a report with a recorded review, supply the review with `--review reports/echo-review.json`. Verify mode validates the inputs, regenerates Markdown in memory, and compares the full UTF-8 bytes, including line endings. It writes no files. An exact match exits with code 0. A difference or an invalid or unreadable input exits with code 1.

A mismatch reports the first differing byte position, counting from 1. If one report ends after a matching prefix, the position is the first byte beyond that prefix. The diagnostic contains no report text.
