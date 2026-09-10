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
