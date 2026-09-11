from iot.fingerprint.oui import lookup_vendor
from iot.models import DeviceObservation


def fingerprint(device: DeviceObservation) -> DeviceObservation:
    """
    Apply deterministic, non-invasive fingerprints to an observation.

    This function interprets collected evidence. It does not contact
    network devices.
    """
    ports = set(device.open_ports)
    protocols = set(device.protocols)

    scores: dict[str, float] = {}

    def add(name: str, score: float) -> None:
        scores[name] = scores.get(name, 0.0) + score

    # MAC/OUI vendor intelligence is derived from observed MAC evidence.
    if device.mac:
        vendor = lookup_vendor(device.mac)

        if vendor:
            device.vendor = vendor
            device.observations.append(
                f"vendor_oui_match:{vendor}"
            )

    if 1883 in ports or "mqtt" in protocols:
        add("iot_device", 0.55)

    if 5683 in ports or "coap" in protocols:
        add("iot_device", 0.55)

    if "http" in protocols or "https" in protocols:
        add("network_appliance", 0.15)

    if "ssh" in protocols:
        add("network_appliance", 0.10)

    if "telnet" in protocols:
        add("legacy_iot_or_appliance", 0.25)

    for evidence in device.http_evidence:
        server = evidence.get("server")

        if server:
            device.observations.append(
                f"http_server:{server}"
            )

            if server.lower() == "micro_httpd":
                add("network_appliance", 0.25)

    if "iot_device" in scores:
        device.device_type = "probable_iot"
        device.confidence = min(scores["iot_device"], 1.0)
        device.observations.append("iot_protocol_detected")

    elif "legacy_iot_or_appliance" in scores:
        device.device_type = "possible_iot_or_appliance"
        device.confidence = min(
            scores["legacy_iot_or_appliance"],
            1.0,
        )
        device.observations.append("legacy_service_detected")

    elif "network_appliance" in scores:
        device.device_type = "network_appliance"
        device.confidence = min(
            scores["network_appliance"],
            1.0,
        )
        device.observations.append(
            "web_or_management_service_detected"
        )

    return device
