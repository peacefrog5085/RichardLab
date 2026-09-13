from pathlib import Path

from ai.security.audit import SecurityAudit


def test_project_boundary():
    audit = SecurityAudit(Path.cwd())
    finding = audit._check_project_boundary()

    assert finding.status == "PASS"
    assert finding.details["exists"] is True


def test_config_check():
    audit = SecurityAudit(Path.cwd())
    finding = audit._check_config()

    assert finding.check == "ai_config"
    assert finding.status in {"PASS", "ACTION_REQUIRED"}


def test_report_structure():
    audit = SecurityAudit(Path.cwd())
    report = audit.run()

    assert report.status in {"PASS", "REVIEW", "ACTION_REQUIRED"}
    assert report.findings
    assert all(finding.check for finding in report.findings)


def test_secret_check_passes_clean_project(tmp_path):
    audit = SecurityAudit(tmp_path)

    finding = audit._check_secrets()

    assert finding.check == "secrets"
    assert finding.status == "PASS"


def test_secret_check_detects_credential_without_exposing_value(tmp_path):
    secret = "sk-" + "A" * 30
    target = tmp_path / "config.txt"
    target.write_text(f"api_key={secret}\n", encoding="utf-8")

    audit = SecurityAudit(tmp_path)

    finding = audit._check_secrets()

    assert finding.status == "ACTION_REQUIRED"
    assert finding.details["match_count"] == 1
    assert finding.details["matches"][0]["pattern"] == "openai_api_key"
    assert secret not in str(finding.details)
