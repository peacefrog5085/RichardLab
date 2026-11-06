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

### Check inputs before publishing

```powershell
python -m cli.echo_investigation docs/echo/examples/synthetic-investigation.json --check
```

To check the packet together with a local human review, run:

```powershell
python -m cli.echo_investigation docs/echo/examples/synthetic-investigation.json --check --review reports/echo-review.json
```

Check mode runs the same validation as report generation, including quote matching and review digest verification. It uses local files, leaves the packet and review intact, and creates or modifies no report files. Each claim must include a citations list. Use an explicit empty list for a claim with no evidence citations.

Choose exactly one of `--check`, `--output`, and `--review-template`. Check mode prints `Validation passed.` and exits with code 0 on success. It prints an error to standard error and exits with code 1 for invalid or unreadable inputs. Command-line usage errors exit with code 2.

### Start a review from a template

```powershell
python -m cli.echo_investigation docs/echo/examples/synthetic-investigation.json --review-template
```

The command validates the packet and prints draft JSON with the digest of the exact packet bytes. Copy it into a UTF-8 JSON file, fill in the blank disposition and note, then validate the completed file with `--check --review`. Template mode takes only the packet, writes no files, and emits no JSON if validation fails.
