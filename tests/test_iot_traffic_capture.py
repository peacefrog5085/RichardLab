from io import StringIO
from unittest.mock import MagicMock, patch

from iot.traffic.capture import TrafficCapture


def test_capture_rejects_invalid_duration():
    try:
        TrafficCapture("wlp0s20f3", seconds=0)
    except ValueError as exc:
        assert "seconds" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_capture_builds_expected_command():
    fake_process = MagicMock()

    fake_process.stdout = StringIO(
        "14:26:48.322488 IP "
        "192.168.1.165.33192 > "
        "173.194.133.2.443: tcp 3519\n"
    )

    with patch(
        "iot.traffic.capture.subprocess.Popen",
        return_value=fake_process,
    ) as popen:
        observer = TrafficCapture(
            "wlp0s20f3",
            seconds=10,
        ).run()

    command = popen.call_args.args[0]

    assert command == [
        "sudo",
        "timeout",
        "10",
        "/usr/bin/tcpdump",
        "-i",
        "wlp0s20f3",
        "-nn",
        "-q",
        "-l",
    ]

    flows = observer.snapshot()

    assert len(flows) == 1
    assert flows[0].source_ip == "192.168.1.165"
    assert flows[0].destination_ip == "173.194.133.2"
    assert flows[0].bytes == 3519


def test_capture_ignores_non_packet_output():
    fake_process = MagicMock()

    fake_process.stdout = StringIO(
        "tcpdump: listening on wlp0s20f3\n"
        "14:26:48.322488 IP "
        "192.168.1.165.33192 > "
        "173.194.133.2.443: tcp 3519\n"
    )

    with patch(
        "iot.traffic.capture.subprocess.Popen",
        return_value=fake_process,
    ):
        observer = TrafficCapture(
            "wlp0s20f3",
            seconds=5,
        ).run()

    assert len(observer.snapshot()) == 1
