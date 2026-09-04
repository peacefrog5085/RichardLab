#!/usr/bin/env bash

LAB="$HOME/RichardLab"
REPORT="$LAB/reports/experiment_002_$(date '+%Y-%m-%d_%H-%M-%S').csv"

mkdir -p "$LAB/reports"

echo "workload,seconds,temp_c,ram_used_gb,swap_used_gb" > "$REPORT"

echo
echo "================================================"
echo "       RICHARD DIGITAL LAB"
echo "       EXPERIMENT #002"
echo "       CPU / THERMAL CAPACITY CURVE"
echo "================================================"
echo
echo "Starting controlled workload test..."
echo

get_temp() {
    if [ -r /sys/class/thermal/thermal_zone1/temp ]; then
        awk '{printf "%.1f", $1/1000}' /sys/class/thermal/thermal_zone1/temp
    else
        echo "0"
    fi
}

get_ram() {
    free -g | awk '/Mem:/ {print $3}'
}

get_swap() {
    free -g | awk '/Swap:/ {print $3}'
}

for WORKLOAD in 1 2 4 8 16 32
do

    echo "-----------------------------------------------"
    echo "WORKLOAD: $WORKLOAD"
    echo "-----------------------------------------------"

    TEMP_BEFORE=$(get_temp)

    START=$(date +%s.%N)

    python3 - "$WORKLOAD" <<'PY'
import sys

workload = int(sys.argv[1])

total = 0

for x in range(workload * 5000000):
    total += (x * x) % 97

print(total)
PY

    END=$(date +%s.%N)

    ELAPSED=$(awk "BEGIN {print $END-$START}")

    sleep 2

    TEMP_AFTER=$(get_temp)
    RAM=$(get_ram)
    SWAP=$(get_swap)

    echo "$WORKLOAD,$ELAPSED,$TEMP_AFTER,$RAM,$SWAP" >> "$REPORT"

    echo "Time:       $ELAPSED seconds"
    echo "Temperature: $TEMP_AFTER°C"
    echo "RAM used:    $RAM GB"
    echo "Swap used:   $SWAP GB"

    if awk "BEGIN {exit !($TEMP_AFTER >= 85)}"; then
        echo
        echo "SAFETY LIMIT REACHED."
        echo "Stopping experiment."
        break
    fi

done

echo
echo "================================================"
echo "EXPERIMENT COMPLETE"
echo "================================================"
echo
echo "Dataset:"
echo "$REPORT"
echo
cat "$REPORT"
