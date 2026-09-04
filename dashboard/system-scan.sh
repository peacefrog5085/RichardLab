#!/usr/bin/env bash

LAB="$HOME/RichardLab"
REPORT_DIR="$LAB/reports"
TIMESTAMP=$(date '+%Y-%m-%d_%H-%M-%S')
REPORT="$REPORT_DIR/system_scan_$TIMESTAMP.txt"

mkdir -p "$REPORT_DIR"

{
echo "============================================================"
echo "             RICHARD DIGITAL LAB"
echo "             SYSTEM SCAN v0.2"
echo "============================================================"
echo
echo "Scan time: $(date)"
echo "User:      $USER"
echo "Hostname:  $(hostname)"
echo
echo "---------------- SYSTEM ----------------"
echo "OS:"
grep -E '^(PRETTY_NAME|VERSION=)' /etc/os-release
echo
echo "Kernel:    $(uname -r)"
echo "Architecture: $(uname -m)"
echo "Uptime:    $(uptime -p)"
echo

echo "---------------- CPU ----------------"
lscpu | grep -E 'Model name|CPU\(s\)|Core\(s\) per socket|Thread\(s\) per core'
echo
echo "Current load:"
cat /proc/loadavg
echo

echo "---------------- MEMORY ----------------"
free -h
echo

echo "---------------- STORAGE ----------------"
df -h "$HOME"
echo
echo "Block devices:"
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS
echo

echo "---------------- GRAPHICS ----------------"
if command -v lspci >/dev/null 2>&1; then
    lspci | grep -Ei 'VGA|3D|Display' || echo "No graphics device detected."
else
    echo "lspci not available."
fi
echo

echo "---------------- NETWORK ----------------"
ip -brief address
echo
echo "Network interfaces:"
ip -brief link
echo

echo "---------------- USB ----------------"
if command -v lsusb >/dev/null 2>&1; then
    lsusb
else
    echo "lsusb not available."
fi
echo

echo "---------------- TEMPERATURE ----------------"
if command -v sensors >/dev/null 2>&1; then
    sensors
else
    echo "lm-sensors is not installed."
    echo "Temperature data unavailable."
fi
echo

echo "---------------- SOFTWARE ----------------"
echo "Python:"
if command -v python3 >/dev/null 2>&1; then
    python3 --version
else
    echo "Not installed"
fi

echo
echo "Git:"
if command -v git >/dev/null 2>&1; then
    git --version
else
    echo "Not installed"
fi

echo
echo "FFmpeg:"
if command -v ffmpeg >/dev/null 2>&1; then
    ffmpeg -version 2>/dev/null | head -n 1
else
    echo "Not installed"
fi

echo
echo "OBS:"
if command -v obs >/dev/null 2>&1; then
    obs --version 2>/dev/null | head -n 1
else
    echo "Not found in PATH"
fi

echo
echo "Kdenlive:"
if command -v kdenlive >/dev/null 2>&1; then
    kdenlive --version 2>/dev/null | head -n 1
else
    echo "Not found in PATH"
fi

echo
echo "---------------- RUNNING PROCESSES ----------------"
ps -eo pid,comm,%cpu,%mem --sort=-%cpu | head -n 15
echo

echo "---------------- SERVICES ----------------"
if command -v systemctl >/dev/null 2>&1; then
    systemctl --type=service --state=running --no-pager 2>/dev/null | head -n 30
else
    echo "systemctl unavailable."
fi

echo
echo "---------------- LAB STATUS ----------------"
echo "AI:          $LAB/ai"
echo "Forensics:   $LAB/forensics"
echo "Value Flow:  $LAB/value_flow"
echo "Experiments: $LAB/experiments"
echo "Media:       $LAB/media"
echo "Knowledge:   $LAB/knowledge"
echo "Reports:     $REPORT_DIR"
echo

echo "============================================================"
echo "SCAN COMPLETE"
echo "============================================================"

} | tee "$REPORT"

echo
echo "Report saved to:"
echo "$REPORT"
