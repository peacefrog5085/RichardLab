from iot.fingerprint.oui import lookup_vendor, normalize_mac


def test_normalize_mac():
    assert normalize_mac("E4-6C-D1-50-7F-1E") == \
        "e4:6c:d1:50:7f:1e"


def test_lookup_unknown_vendor():
    assert lookup_vendor("00:11:22:33:44:55") is None


def test_lookup_missing_mac():
    assert lookup_vendor(None) is None


def test_lookup_invalid_mac():
    assert lookup_vendor("not-a-mac") is None
