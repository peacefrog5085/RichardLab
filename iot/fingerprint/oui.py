from typing import Optional


# Small deterministic seed database.
# This is intentionally kept separate from device evidence so the
# vendor result remains an inference rather than an observed fact.
OUI_DATABASE = {
    "e4:6c:d1": "Unknown",
}


def normalize_mac(mac: str) -> str:
    return mac.strip().lower().replace("-", ":")


def lookup_vendor(mac: Optional[str]) -> Optional[str]:
    if not mac:
        return None

    normalized = normalize_mac(mac)
    parts = normalized.split(":")

    if len(parts) != 6 or any(len(part) != 2 for part in parts):
        return None

    oui = ":".join(parts[:3])

    return OUI_DATABASE.get(oui)
