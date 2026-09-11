import argparse

from iot.service import IoTService
from iot.traffic.capture import TrafficCapture
from iot.traffic.report import build_traffic_report


def build_parser():
    parser = argparse.ArgumentParser(
        prog="richardlab-iot",
        description="RichardLab IoT discovery and traffic observation",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    discover = subparsers.add_parser(
        "discover",
        help="Discover and fingerprint devices on an authorized network",
    )

    discover.add_argument(
        "network",
        help="Network in CIDR notation, for example 192.168.1.0/24",
    )

    discover.add_argument(
        "--timeout",
        type=float,
        default=0.25,
        help="TCP connection timeout in seconds",
    )

    discover.add_argument(
        "--ports",
        nargs="+",
        type=int,
        help="Optional list of TCP ports to check",
    )

    discover.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the operation without contacting the network",
    )

    traffic = subparsers.add_parser(
        "traffic",
        help="Observe metadata-only network traffic",
    )

    traffic.add_argument(
        "--interface",
        required=True,
        help="Network interface to capture, for example wlp0s20f3",
    )

    traffic.add_argument(
        "--network",
        required=True,
        help="Local network in CIDR notation",
    )

    traffic.add_argument(
        "--seconds",
        type=int,
        default=10,
        help="Capture duration in seconds",
    )

    traffic.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the operation without capturing traffic",
    )

    return parser


def print_discovery(devices):
    print("RICHARDLAB IoT DISCOVERY")
    print("========================")

    for device in devices:
        changes = {
            "changed": bool(device.changes),
            "changes": device.changes,
        }

        print()
        print(device.ip)

        if device.hostname:
            print(f"  hostname : {device.hostname}")

        if device.mac:
            print(f"  mac      : {device.mac}")

        if device.vendor:
            print(f"  vendor   : {device.vendor}")

        print(
            "  ports    : "
            + (
                ", ".join(map(str, device.open_ports))
                if device.open_ports
                else "none"
            )
        )

        print(
            "  protocols: "
            + (
                ", ".join(device.protocols)
                if device.protocols
                else "none"
            )
        )

        print(
            "  type     : "
            f"{device.device_type or 'unclassified'}"
        )

        print(
            f"  confidence: {device.confidence:.2f}"
        )

        if changes["changed"]:
            print(
                "  change   : "
                + ", ".join(changes["changes"])
            )
        else:
            print("  change   : no_change")

    print()
    print(f"Devices discovered: {len(devices)}")
    print("Inventory updated: YES")


def print_traffic_report(report):
    print("RICHARDLAB NETWORK ACTIVITY REPORT")
    print("===================================")

    print()
    print("Capture")
    print(f"  interface : {report.interface}")
    print(f"  duration  : {report.duration_seconds} seconds")

    summary = report.summary

    print()
    print("Summary")
    print(f"  flows     : {summary['total_flows']}")
    print(f"  LAN       : {summary['lan_flows']}")
    print(f"  private   : {summary['private_flows']}")
    print(f"  Internet  : {summary['internet_flows']}")
    print(f"  localhost : {summary['localhost_flows']}")
    print(f"  invalid   : {summary['invalid_flows']}")

    if report.flows:
        print()
        print("Flows")

        for flow in sorted(
            report.flows,
            key=lambda item: item["bytes"],
            reverse=True,
        ):
            print()
            print(
                f"  {flow['source_ip']}:{flow['source_port']}"
                f" -> "
                f"{flow['destination_ip']}:{flow['destination_port']}"
            )
            print(f"    protocol : {flow['protocol']}")
            print(f"    packets  : {flow['packets']}")
            print(f"    bytes    : {flow['bytes']}")
            print(
                f"    source   : {flow['source_class']}"
            )
            print(
                f"    dest     : {flow['destination_class']}"
            )

            if flow["source_known_device"]:
                print("    source   : known inventory device")

            if flow["destination_known_device"]:
                print("    dest     : known inventory device")

    if report.inventory_notes:
        print()
        print("Inventory Correlation")

        for note in report.inventory_notes:
            print(f"  {note}")

    print()
    print("Evidence Boundary")
    print(
        "  Traffic observations apply only to the capture window."
    )


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "discover":
        if args.dry_run:
            print("RICHARDLAB IoT DISCOVERY")
            print("========================")
            print(f"Network : {args.network}")
            print(f"Timeout : {args.timeout}")
            print(
                "Ports   : "
                + (
                    "default"
                    if args.ports is None
                    else ", ".join(map(str, args.ports))
                )
            )
            print("Mode    : DRY RUN")
            print("Network contacted: NO")
            return 0

        service = IoTService()

        devices = service.discover(
            args.network,
            ports=args.ports,
            timeout=args.timeout,
        )

        print_discovery(devices)

        return 0

    if args.command == "traffic":
        if args.seconds <= 0:
            parser.error("--seconds must be greater than zero")

        if args.dry_run:
            print("RICHARDLAB NETWORK TRAFFIC")
            print("==========================")
            print(f"Interface : {args.interface}")
            print(f"Network   : {args.network}")
            print(f"Seconds   : {args.seconds}")
            print("Mode      : DRY RUN")
            print("Traffic captured: NO")
            return 0

        capture = TrafficCapture(
            interface=args.interface,
            seconds=args.seconds,
        )

        observer = capture.run()

        service = IoTService()

        try:
            inventory = service.inventory.all()
        except AttributeError:
            inventory = []

        report = build_traffic_report(
            flows=observer.snapshot(),
            interface=args.interface,
            duration_seconds=args.seconds,
            local_network=args.network,
            inventory=inventory,
        )

        print_traffic_report(report)

        return 0

    parser.error("Unknown command")


if __name__ == "__main__":
    raise SystemExit(main())
