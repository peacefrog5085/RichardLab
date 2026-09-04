#!/usr/bin/env bash

LAB="$HOME/RichardLab"
REPORT="$LAB/reports/experiment_001_$(date '+%Y-%m-%d_%H-%M-%S').txt"

mkdir -p "$LAB/reports"

{
echo "============================================================"
echo "          RICHARD DIGITAL LAB"
echo "          EXPERIMENT #001"
echo "          MACHINE CAPABILITY PROFILE"
echo "============================================================"
echo
echo "Date: $(date)"
echo "Machine: $(hostname)"
echo

echo "================ HARDWARE ================="
echo "CPU:"
lscpu | grep -E 'Model name|CPU\(s\)|Core\(s\)|Thread\(s\)'

echo
echo "Memory:"
free -h

echo
echo "Graphics:"
lspci | grep -Ei 'VGA|3D|Display'

echo
echo "Storage:"
df -h "$HOME"

echo
echo "================ CPU TEST ================="
echo "Calculating SHA256 hashes..."

START=$(date +%s.%N)

dd if=/dev/zero bs=1M count=256 2>/dev/null | sha256sum >/dev/null

END=$(date +%s.%N)

CPU_TIME=$(awk "BEGIN {print $END-$START}")

echo "256 MB SHA256 test:"
echo "$CPU_TIME seconds"

echo
echo "================ DISK TEST ================"
TESTFILE="/tmp/richardlab_disk_test"

START=$(date +%s.%N)

dd if=/dev/zero of="$TESTFILE" bs=1M count=512 conv=fdatasync 2>/dev/null

END=$(date +%s.%N)

DISK_TIME=$(awk "BEGIN {print $END-$START}")
DISK_SPEED=$(awk "BEGIN {print 512/$DISK_TIME}")

echo "512 MB sequential write:"
echo "$DISK_TIME seconds"
echo "Approximate speed:"
echo "$DISK_SPEED MB/s"

rm -f "$TESTFILE"

echo
echo "================ COMPRESSION TEST ========="

if command -v gzip >/dev/null 2>&1; then

    START=$(date +%s.%N)

    dd if=/dev/zero bs=1M count=256 2>/dev/null | gzip > /tmp/richardlab.gz

    END=$(date +%s.%N)

    GZIP_TIME=$(awk "BEGIN {print $END-$START}")

    echo "256 MB gzip test:"
    echo "$GZIP_TIME seconds"

    rm -f /tmp/richardlab.gz

else
    echo "gzip unavailable"
fi

echo
echo "================ PYTHON TEST ==============="

if command -v python3 >/dev/null 2>&1; then

python3 <<'PY'
import time

start = time.time()

total = 0

for i in range(1_000_000):
    total += (i * i) % 97

elapsed = time.time() - start

print(f"Python computation: {elapsed:.4f} seconds")
print(f"Result checksum: {total}")
PY

else
    echo "Python3 unavailable"
fi

echo
echo "================ SOFTWARE =================="

echo "Python:"
python3 --version 2>/dev/null || echo "Unavailable"

echo
echo "FFmpeg:"
ffmpeg -version 2>/dev/null | head -n 1 || echo "Unavailable"

echo
echo "Git:"
git --version 2>/dev/null || echo "Unavailable"

echo
echo "================ RESULT ===================="

echo "Experiment completed:"
date

echo
echo "Report:"
echo "$REPORT"

echo
echo "============================================================"

} | tee "$REPORT"

echo
echo "EXPERIMENT #001 COMPLETE"
echo
echo "Saved:"
echo "$REPORT"
