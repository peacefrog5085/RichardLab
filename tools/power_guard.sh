#!/usr/bin/env bash

set -u

LAB="${HOME}/RichardLab"

get_power_source() {
    if [[ -r /sys/class/power_supply/ADP0/online ]]; then
        if [[ "$(cat /sys/class/power_supply/ADP0/online)" == "1" ]]; then
            echo "AC"
        else
            echo "BATTERY"
        fi
        return
    fi

    echo "UNKNOWN"
}

POWER_SOURCE="$(get_power_source)"

echo "RichardLab Power Guard"
echo "────────────────────────────────────────"
echo "Power source: $POWER_SOURCE"

if [[ "$POWER_SOURCE" == "UNKNOWN" ]]; then
    echo "WARNING: Unable to determine power source."
    exit 1
fi

if [[ "$EUID" -eq 0 ]]; then
    /usr/sbin/tlp auto
else
    sudo /usr/sbin/tlp auto
fi

echo
echo "TLP synchronized."

if command -v tlp-stat >/dev/null 2>&1; then
    sudo tlp-stat -s | grep -E 'State|Mode|Power source' || true
fi

echo
