import argparse

from iot.service import IoTService


def build_parser():
    parser = argparse.ArgumentParser(
        prog="richardlab-iot",
        description="RichardLab IoT discovery and fingerprinting",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

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

    return parser


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
                f"  type     : "
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

        return 0


if __name__ == "__main__":
    raise SystemExit(main())
