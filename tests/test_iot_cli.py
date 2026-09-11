from unittest.mock import patch

from iot.cli import build_parser, main


def test_traffic_command_parses():
    parser = build_parser()

    args = parser.parse_args([
        "traffic",
        "--interface",
        "wlp0s20f3",
        "--network",
        "192.168.1.0/24",
        "--seconds",
        "10",
    ])

    assert args.command == "traffic"
    assert args.interface == "wlp0s20f3"
    assert args.network == "192.168.1.0/24"
    assert args.seconds == 10


def test_traffic_dry_run_does_not_capture(capsys):
    with patch("iot.cli.TrafficCapture") as capture:
        result = main([
            "traffic",
            "--interface",
            "wlp0s20f3",
            "--network",
            "192.168.1.0/24",
            "--seconds",
            "10",
            "--dry-run",
        ])

    assert result == 0
    capture.assert_not_called()

    output = capsys.readouterr().out

    assert "RICHARDLAB NETWORK TRAFFIC" in output
    assert "Interface : wlp0s20f3" in output
    assert "Network   : 192.168.1.0/24" in output
    assert "Traffic captured: NO" in output


def test_traffic_command_uses_capture_and_inventory(capsys):
    fake_capture = patch("iot.cli.TrafficCapture")
    fake_service = patch("iot.cli.IoTService")

    with fake_capture as capture_patch, fake_service as service_patch:
        capture_instance = capture_patch.return_value

        observer = capture_instance.run.return_value
        observer.snapshot.return_value = []

        service_instance = service_patch.return_value
        service_instance.inventory.all.return_value = []

        result = main([
            "traffic",
            "--interface",
            "wlp0s20f3",
            "--network",
            "192.168.1.0/24",
            "--seconds",
            "10",
        ])

    assert result == 0

    capture_patch.assert_called_once_with(
        interface="wlp0s20f3",
        seconds=10,
    )

    capture_instance.run.assert_called_once()

    service_instance.inventory.all.assert_called_once()

    output = capsys.readouterr().out

    assert "RICHARDLAB NETWORK ACTIVITY REPORT" in output
    assert "flows     : 0" in output


def test_traffic_rejects_invalid_seconds():
    try:
        main([
            "traffic",
            "--interface",
            "wlp0s20f3",
            "--network",
            "192.168.1.0/24",
            "--seconds",
            "0",
        ])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("Expected parser error")
