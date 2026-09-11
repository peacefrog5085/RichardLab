import subprocess
from typing import Iterable

from iot.traffic.observer import TrafficObserver
from iot.traffic.tcpdump_parser import parse_line


class TrafficCapture:
    """
    Bounded, metadata-only tcpdump capture.

    The capture records packet headers only. Packet payloads are not
    retained or passed into the RichardLab traffic observer.
    """

    def __init__(
        self,
        interface: str,
        seconds: int = 10,
        tcpdump_path: str = "/usr/bin/tcpdump",
    ):
        if seconds <= 0:
            raise ValueError("seconds must be greater than zero")

        self.interface = interface
        self.seconds = seconds
        self.tcpdump_path = tcpdump_path

    def run(self) -> TrafficObserver:
        observer = TrafficObserver()

        command = [
            "sudo",
            "timeout",
            str(self.seconds),
            self.tcpdump_path,
            "-i",
            self.interface,
            "-nn",
            "-q",
            "-l",
        ]

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        assert process.stdout is not None

        try:
            for line in process.stdout:
                parse_line(line, observer)
        finally:
            process.stdout.close()

            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

        return observer
