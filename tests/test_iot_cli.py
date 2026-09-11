from iot.cli import main


def test_discover_dry_run(capsys):
    result = main([
        "discover",
        "192.168.1.0/24",
        "--ports",
        "80",
        "443",
        "1883",
        "--dry-run",
    ])

    output = capsys.readouterr().out

    assert result == 0
    assert "RICHARDLAB IoT DISCOVERY" in output
    assert "192.168.1.0/24" in output
    assert "80, 443, 1883" in output
    assert "DRY RUN" in output
    assert "Network contacted: NO" in output
