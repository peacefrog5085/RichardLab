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
