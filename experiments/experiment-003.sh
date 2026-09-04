#!/usr/bin/env bash

LAB="$HOME/RichardLab"
REPORT="$LAB/reports/experiment_003_$(date '+%Y-%m-%d_%H-%M-%S').csv"

mkdir -p "$LAB/reports"

echo "megabytes,seconds,ram_used_mib,ram_available_mib,swap_used_mib" > "$REPORT"

echo
echo "============================================================"
echo "          RICHARD DIGITAL LAB"
echo "          EXPERIMENT #003"
echo "          MEMORY CAPACITY CURVE"
echo "============================================================"
echo
echo "The test will gradually increase memory usage."
echo "It will stop before deliberately consuming all available RAM."
echo

free -h
echo

for MB in 512 1024 2048 3072 4096 5120
do
    echo "------------------------------------------------------------"
    echo "Testing allocation: ${MB} MB"
    echo "------------------------------------------------------------"

    BEFORE=$(free -m | awk '/Mem:/ {print $7}')

    START=$(date +%s.%N)

    python3 - "$MB" <<'PY'
import sys
import time

mb = int(sys.argv[1])

# Allocate approximately the requested amount.
size = mb * 1024 * 1024

data = bytearray(size)

# Touch each page so the OS actually backs the allocation with memory.
page = 4096

for i in range(0, len(data), page):
    data[i] = 1

# Keep allocation alive briefly so measurement is meaningful.
time.sleep(2)

del data
PY

    END=$(date +%s.%N)

    ELAPSED=$(awk "BEGIN {print $END-$START}")

    sleep 1

    RAM_USED=$(free -m | awk '/Mem:/ {print $3}')
    RAM_AVAILABLE=$(free -m | awk '/Mem:/ {print $7}')
    SWAP_USED=$(free -m | awk '/Swap:/ {print $3}')

    echo "$MB,$ELAPSED,$RAM_USED,$RAM_AVAILABLE,$SWAP_USED" >> "$REPORT"

    echo "Time:          $ELAPSED seconds"
    echo "RAM used:      ${RAM_USED} MiB"
    echo "RAM available: ${RAM_AVAILABLE} MiB"
    echo "Swap used:     ${SWAP_USED} MiB"
    echo

    if [ "$SWAP_USED" -gt 512 ]; then
        echo "Swap usage exceeded 512 MiB."
        echo "Stopping test to protect system responsiveness."
        break
    fi
done

echo
echo "============================================================"
echo "EXPERIMENT #003 COMPLETE"
echo "============================================================"
echo
echo "Dataset saved to:"
echo "$REPORT"
echo
cat "$REPORT"
