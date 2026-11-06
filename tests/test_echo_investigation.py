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

    def run_cli(self, *arguments):
        source = self.directory / "packet.json"
        source.write_bytes(json.dumps(self.packet).encode("utf-8"))
        return subprocess.run(
            [sys.executable, "-m", "cli.echo_investigation", str(source),
             "--output", str(self.output), *arguments],
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
