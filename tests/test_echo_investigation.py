import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "docs/echo/examples/synthetic-investigation.json"


class EchoInvestigationTest(unittest.TestCase):
    def setUp(self):
        self.directory = Path(self.enterContext(TemporaryDirectory()))
        self.output = self.directory / "investigation.md"
        self.packet = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def run_cli(self, *arguments, with_output=True, packet_suffix=b""):
        source = self.directory / "packet.json"
        source.write_bytes(json.dumps(self.packet).encode("utf-8") + packet_suffix)
        output_args = ["--output", str(self.output)] if with_output else []
        return subprocess.run(
            [sys.executable, "-m", "cli.echo_investigation", str(source),
             *output_args, *arguments],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
        )

    def write_review(self, **fields):
        review = {
            "packet_sha256": hashlib.sha256(json.dumps(self.packet).encode("utf-8")).hexdigest(),
            "disposition": "Unresolved",
            "note": "Both accounts remain plausible.",
        }
        review.update(fields)
        path = self.directory / "review.json"
        path.write_text(json.dumps(review), encoding="utf-8")
        return str(path)

    def use_pinned_workflow_excerpt(self):
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        path = ".github/workflows/integration-security.yml"
        blob = subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT, text=True)
        quote = "- run: python -m pytest -q"
        line, = (number for number, text in enumerate(blob.splitlines(), 1) if quote in text)
        source = self.packet["sources"][0]
        source.update(commit=commit, path=path, passages={"P1": quote}, line_ranges={"P1": [line, line]})
        self.packet["sources"] = [source]
        self.packet["claims"] = [{
            "text": "The pinned workflow runs pytest.",
            "citations": [{"source": "S1", "passage": "P1", "quote": quote, "relation": "supports"}],
        }]
        return source

    def test_check_sources_accepts_pinned_git_excerpt_without_writing(self):
        self.use_pinned_workflow_excerpt()
        result = self.run_cli("--check-sources", with_output=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "Source passages verified.")
        self.assertCountEqual(self.directory.iterdir(), [self.directory / "packet.json"])

    def test_check_sources_rejects_wrong_lines(self):
        source = self.use_pinned_workflow_excerpt()
        source["line_ranges"]["P1"] = [1, 1]
        result = self.run_cli("--check-sources", with_output=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Passage does not match pinned Git lines", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_check_sources_rejects_unavailable_or_unpinned_commit(self):
        source = self.use_pinned_workflow_excerpt()
        for commit, message in (("f" * 40, "Pinned Git commit is unavailable"),
                                ("HEAD", "Source commit must be a full Git object ID")):
            with self.subTest(commit=commit):
                source["commit"] = commit
                result = self.run_cli("--check-sources", with_output=False)
                self.assertEqual(result.returncode, 1)
                self.assertIn(message, result.stderr)
                self.assertEqual(result.stdout, "")

    def test_check_sources_requires_line_range_for_every_passage(self):
        source = self.use_pinned_workflow_excerpt()
        source["line_ranges"] = {}
        result = self.run_cli("--check-sources", with_output=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Source check requires a line range for every passage", result.stderr)
        ordinary = self.run_cli("--check", with_output=False)
        self.assertEqual(ordinary.returncode, 0, ordinary.stderr)

    def test_citations_show_optional_passage_line_ranges(self):
        first, second, _ = self.packet["sources"]
        first.update(path="logs/first.txt", line_ranges={"P1": [12, 14]})
        second.update(path="logs/second.txt", line_ranges={"P1": [7, 7]})
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = self.output.read_text(encoding="utf-8")
        self.assertIn("- **S1/P1** (trial-log, logs/first.txt:12–14, supports)", report)
        self.assertIn("- **S2/P1** (trial-log, logs/second.txt:7, supports)", report)
        self.assertIn("- **S3/P1** (observer-log, contradicts)", report)

    def test_citations_reject_invalid_passage_line_ranges(self):
        source = self.packet["sources"][0]
        source["path"] = "logs/first.txt"
        for ranges, message in (
            ({"P1": [14, 12]}, "positive, ordered integers"),
            ({"P1": [0, 1]}, "positive, ordered integers"),
            ({"P1": [True, 2]}, "positive, ordered integers"),
            ({"missing": [1, 2]}, "Unknown passage in source line ranges"),
        ):
            with self.subTest(ranges=ranges):
                source["line_ranges"] = ranges
                result = self.run_cli()
                self.assertEqual(result.returncode, 1)
                self.assertIn(message, result.stderr)
                self.assertFalse(self.output.exists())

    def test_citation_line_ranges_require_source_path(self):
        self.packet["sources"][0]["line_ranges"] = {"P1": [1, 1]}
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn("Source line ranges require a source path", result.stderr)
        self.assertFalse(self.output.exists())

    def test_citations_distinguish_source_paths_without_splitting_origin(self):
        paths = (".github/workflows/first.yml", ".github/workflows/second.yml")
        for source, path in zip(self.packet["sources"], paths):
            source["path"] = path
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = self.output.read_text(encoding="utf-8")
        for source_id, path in zip(("S1", "S2"), paths):
            citation = next(line for line in report.splitlines() if line.startswith(f"- **{source_id}/P1**"))
            self.assertIn(path, citation)
        self.assertIn("2 distinct origins across 3 citations", report)

    def test_citations_reject_non_repository_relative_source_paths(self):
        for path in ("/private/file.yml", "../file.yml", "dir/../file.yml",
                     "C:/private/file.yml", r"\\host\share\file.yml", None):
            with self.subTest(path=path):
                self.packet["sources"][0]["path"] = path
                result = self.run_cli()
                self.assertEqual(result.returncode, 1)
                self.assertIn("Source path must be repository-relative", result.stderr)
                self.assertFalse(self.output.exists())

    def test_real_packet_report_label_matches_and_verifies(self):
        self.packet["evidence_kind"] = "real"
        generated = self.run_cli()
        self.assertEqual(generated.returncode, 0, generated.stderr)
        report = self.output.read_text(encoding="utf-8")
        self.assertIn("**Real evidence**", report.splitlines())
        self.assertNotIn("**Synthetic evidence**", report.splitlines())
        for mode in ("--match-report", "--verify-report"):
            with self.subTest(mode=mode):
                result = self.run_cli(mode, str(self.output), with_output=False)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_invalid_evidence_kind_is_rejected(self):
        self.packet["evidence_kind"] = "unclassified"
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn("Evidence kind must be synthetic or real", result.stderr)
        self.assertFalse(self.output.exists())

    def test_report_digest_matches_review_template_with_or_without_review(self):
        template = self.run_cli("--review-template", with_output=False)
        self.assertEqual(template.returncode, 0, template.stderr)
        digest = json.loads(template.stdout)["packet_sha256"]
        review = self.write_review()
        for arguments in ((), ("--review", review)):
            with self.subTest(reviewed=bool(arguments)):
                result = self.run_cli(*arguments)
                self.assertEqual(result.returncode, 0, result.stderr)
                report = self.output.read_text(encoding="utf-8")
                self.assertIn(f"**Packet SHA-256** `{digest}`", report)

    def test_report_digest_changes_with_packet_whitespace(self):
        for suffix in (b"", b"\n "):
            with self.subTest(suffix=suffix):
                result = self.run_cli(packet_suffix=suffix)
                self.assertEqual(result.returncode, 0, result.stderr)
                raw = (self.directory / "packet.json").read_bytes()
                digest = hashlib.sha256(raw).hexdigest()
                report = self.output.read_text(encoding="utf-8")
                self.assertIn(f"**Packet SHA-256** `{digest}`", report)

    def test_verify_report_reproduces_pending_and_reviewed_reports_without_writing(self):
        review = self.write_review()
        for arguments in ((), ("--review", review)):
            with self.subTest(reviewed=bool(arguments)):
                generated = self.run_cli(*arguments)
                self.assertEqual(generated.returncode, 0, generated.stderr)
                original = self.output.read_bytes()
                modified = self.output.stat().st_mtime_ns
                result = self.run_cli(
                    "--verify-report", str(self.output), *arguments, with_output=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), "Saved report matches regenerated Markdown.")
                self.assertEqual(self.output.read_bytes(), original)
                self.assertEqual(self.output.stat().st_mtime_ns, modified)
                if arguments:
                    pending = self.run_cli("--verify-report", str(self.output), with_output=False)
                    self.assertEqual(pending.returncode, 1)
                    self.assertIn("Saved report does not match regenerated Markdown", pending.stderr)

    def test_verify_report_reports_only_first_differing_byte_position(self):
        generated = self.run_cli()
        self.assertEqual(generated.returncode, 0, generated.stderr)
        original = self.output.read_bytes()
        offset = original.index(b"Duplicate origins")
        for edited, position in (
            (original[:offset] + b"Private replacement" + original[offset + 1:], offset + 1),
            (original[:offset], offset + 1),
            (original + b"Private addition", len(original) + 1),
        ):
            with self.subTest(position=position, size=len(edited)):
                self.output.write_bytes(edited)
                result = self.run_cli("--verify-report", str(self.output), with_output=False)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, "")
                self.assertEqual(
                    result.stderr.strip(),
                    f"Echo investigation: Saved report does not match regenerated Markdown "
                    f"(first differing byte position: {position})",
                )
                self.assertEqual(self.output.read_bytes(), edited)

    def test_verify_report_rejects_body_edit_even_when_packet_digest_matches(self):
        generated = self.run_cli()
        self.assertEqual(generated.returncode, 0, generated.stderr)
        edited = self.output.read_bytes() + b"\nAdded after generation.\n"
        self.output.write_bytes(edited)
        result = self.run_cli("--verify-report", str(self.output), with_output=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Saved report does not match regenerated Markdown", result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(self.output.read_bytes(), edited)
        matched = self.run_cli("--match-report", str(self.output), with_output=False)
        self.assertEqual(matched.returncode, 0, matched.stderr)

    def test_match_report_accepts_saved_report_without_modifying_it(self):
        generated = self.run_cli()
        self.assertEqual(generated.returncode, 0, generated.stderr)
        original = self.output.read_bytes()
        modified = self.output.stat().st_mtime_ns
        result = self.run_cli("--match-report", str(self.output), with_output=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "Report packet digest matches.")
        self.assertEqual(self.output.read_bytes(), original)
        self.assertEqual(self.output.stat().st_mtime_ns, modified)
        self.assertCountEqual(self.directory.iterdir(), [self.output, self.directory / "packet.json"])

    def test_match_report_rejects_whitespace_change_to_packet(self):
        generated = self.run_cli()
        self.assertEqual(generated.returncode, 0, generated.stderr)
        result = self.run_cli(
            "--match-report", str(self.output), with_output=False, packet_suffix=b"\n ",
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("Report packet digest does not match", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_match_report_requires_digest_in_report_header(self):
        generated = self.run_cli()
        self.assertEqual(generated.returncode, 0, generated.stderr)
        original = self.output.read_text(encoding="utf-8")
        digest_line = next(line for line in original.splitlines() if line.startswith("**Packet SHA-256**"))
        for replacement, suffix in (("", ""), ("**Packet SHA-256** `invalid`", ""), ("", digest_line + "\n")):
            with self.subTest(replacement=replacement, misplaced=bool(suffix)):
                self.output.write_text(original.replace(digest_line, replacement) + suffix, encoding="utf-8")
                result = self.run_cli("--match-report", str(self.output), with_output=False)
                self.assertEqual(result.returncode, 1)
                self.assertIn("Report header must contain a valid Packet SHA-256", result.stderr)
                self.assertEqual(result.stdout, "")

    def test_matching_review_records_unresolved_disposition(self):
        review = self.write_review()
        result = self.run_cli("--review", review)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = self.output.read_text(encoding="utf-8")
        self.assertIn("Human review: recorded", report)
        self.assertIn("Unresolved", report)
        self.assertIn("Both accounts remain plausible.", report)
        self.assertIn("Conflicting evidence", report)
        self.assertNotIn("Human review: pending", report)

    def test_review_template_emits_digest_and_blank_fields_without_writing(self):
        result = self.run_cli("--review-template", with_output=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        packet = self.directory / "packet.json"
        self.assertEqual(json.loads(result.stdout), {
            "packet_sha256": hashlib.sha256(packet.read_bytes()).hexdigest(),
            "disposition": "",
            "note": "",
        })
        self.assertCountEqual(self.directory.iterdir(), [packet])

    def test_review_template_rejects_invalid_citation_without_emitting_json(self):
        self.packet["claims"][0]["citations"][0]["quote"] = "fabricated quote"
        result = self.run_cli("--review-template", with_output=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Quote mismatch", result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertFalse(self.output.exists())

    def test_review_template_rejects_other_modes_and_existing_review(self):
        for args in (("--check",), ("--output", str(self.output)), ("--review", self.write_review())):
            with self.subTest(args=args):
                result = self.run_cli("--review-template", *args, with_output=False)
                self.assertEqual(result.returncode, 2)
                self.assertIn("not allowed with argument", result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertFalse(self.output.exists())

    def test_check_accepts_valid_packet_and_optional_review_without_writing(self):
        review = self.write_review()
        for review_args in ((), ("--review", review)):
            with self.subTest(review_args=review_args):
                result = self.run_cli("--check", *review_args, with_output=False)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("Validation passed.", result.stdout)
                self.assertEqual(
                    {path.name for path in self.directory.iterdir()},
                    {"packet.json", "review.json"},
                )

    def test_check_rejects_stale_review(self):
        review = self.write_review()
        self.packet["question"] += " "
        result = self.run_cli("--check", "--review", review, with_output=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Review digest does not match packet", result.stderr)
        self.assertFalse(self.output.exists())

    def test_check_rejects_missing_and_malformed_citations(self):
        for citations, message in (
            (None, "Missing citations in claim 1"),
            ({}, "Citations in claim 1 must be a list"),
            (["not an object"], "Citations in claim 1 must contain objects"),
            ([{"source": "S1"}], "Citation 1 passage in claim 1 must be nonempty text"),
        ):
            with self.subTest(citations=citations):
                claim = self.packet["claims"][0]
                if citations is None:
                    del claim["citations"]
                else:
                    claim["citations"] = citations
                result = self.run_cli("--check", with_output=False)
                self.assertEqual(result.returncode, 1)
                self.assertIn(message, result.stderr)
                self.assertFalse(self.output.exists())

    def test_check_rejects_invalid_citations(self):
        citation = self.packet["claims"][0]["citations"][0]
        for field, value, message in (
            ("source", "missing", "Unknown source"),
            ("passage", "missing", "Unknown passage"),
            ("quote", "fabricated quote", "Quote mismatch"),
            ("relation", "unknown", "Invalid citation relationship"),
        ):
            with self.subTest(field=field), patch.dict(citation, {field: value}):
                result = self.run_cli("--check", with_output=False)
                self.assertEqual(result.returncode, 1)
                self.assertIn(message, result.stderr)
                self.assertFalse(self.output.exists())

    def test_check_preserves_inputs_and_existing_report(self):
        from cli.echo_investigation import main

        packet = self.directory / "packet.json"
        packet.write_bytes(json.dumps(self.packet).encode("utf-8"))
        review = Path(self.write_review())
        self.output.write_bytes(b"previous report")
        paths = (packet, review, self.output)
        before = [(path.read_bytes(), path.stat().st_mtime_ns) for path in paths]

        with patch("socket.socket", side_effect=AssertionError("Network access attempted")):
            self.assertEqual(main([str(packet), "--check", "--review", str(review)]), 0)

        self.assertEqual([(path.read_bytes(), path.stat().st_mtime_ns) for path in paths], before)
        self.assertCountEqual(self.directory.iterdir(), paths)

    def test_check_rejects_output_option(self):
        result = self.run_cli("--check")
        self.assertEqual(result.returncode, 2)
        self.assertIn("not allowed with argument", result.stderr)
        self.assertFalse(self.output.exists())

    def test_stale_review_preserves_existing_report(self):
        review = self.write_review()
        self.packet["question"] += " "
        self.output.write_bytes(b"previous report")
        result = self.run_cli("--review", review)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Review digest does not match packet", result.stderr)
        self.assertEqual(self.output.read_bytes(), b"previous report")

    def test_invalid_review_leaves_no_report(self):
        review = self.write_review(note="")
        result = self.run_cli("--review", review)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Review note must be nonempty text", result.stderr)
        self.assertFalse(self.output.exists())

    def test_synthetic_report_preserves_conflict_and_pending_review(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = self.output.read_text(encoding="utf-8")
        for expected in (
            "Synthetic evidence", "Did the test beacon flash?",
            "Conflicting evidence", "Duplicate origins",
            "Human review: pending", "Evidence needed",
            "2 distinct origins across 3 citations",
            "S1/P1", "S2/P1", "S3/P1",
            "- **S1/P1** (trial-log, supports)",
            "The beacon flashed during the trial.",
            "The beacon stayed dark during the trial.",
        ):
            self.assertIn(expected, report)

    def test_invalid_references_and_quote_mismatch_leave_no_report(self):
        for field, value, message in (
            ("source", "missing", "Unknown source"),
            ("passage", "missing", "Unknown passage"),
            ("quote", "fabricated quote", "Quote mismatch"),
        ):
            with self.subTest(field=field):
                self.packet = json.loads(FIXTURE.read_text(encoding="utf-8"))
                self.packet["claims"][0]["citations"][0][field] = value
                result = self.run_cli()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
                self.assertFalse(self.output.exists())

    def test_failed_publish_preserves_existing_report_and_cleans_temp_file(self):
        from cli.echo_investigation import main

        self.output.write_text("previous report", encoding="utf-8")
        with patch("cli.echo_investigation.os.replace", side_effect=OSError):
            self.assertNotEqual(main([str(FIXTURE), "--output", str(self.output)]), 0)
        self.assertEqual(self.output.read_text(encoding="utf-8"), "previous report")
        self.assertEqual(list(self.directory.iterdir()), [self.output])


if __name__ == "__main__":
    unittest.main()
