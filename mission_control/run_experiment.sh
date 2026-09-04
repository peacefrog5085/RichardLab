#!/usr/bin/env bash

LAB="$HOME/RichardLab"
REGISTRY="$LAB/data/experiment_runs.csv"

mkdir -p "$LAB/data"

if [[ ! -f "$REGISTRY" ]]; then
    echo "run_id,experiment,start_time,end_time,duration_seconds,exit_status,result" > "$REGISTRY"
fi

clear
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                     EXPERIMENT RUNNER                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo
echo "Available experiments:"
echo

find "$LAB/experiments" \
    -maxdepth 1 \
    -type f \
    \( -name "*.py" -o -name "*.sh" \) \
    -printf '%f\n' \
    | sort

echo
read -rp "Experiment filename: " experiment

if [[ -z "$experiment" ]]; then
    echo "No experiment selected."
    exit 0
fi

target="$LAB/experiments/$experiment"

if [[ ! -f "$target" ]]; then
    echo
    echo "ERROR: Experiment not found:"
    echo "$experiment"
    exit 1
fi

case "$experiment" in
    *.py)
        command=(python3 "$target")
        ;;
    *.sh)
        command=(bash "$target")
        ;;
    *)
        echo "ERROR: Unsupported experiment type."
        exit 1
        ;;
esac

run_id="$(date '+%Y%m%d_%H%M%S')"
start_epoch="$(date +%s)"
start_time="$(date '+%Y-%m-%d %H:%M:%S')"

echo
echo "RUN START"
echo "────────────────────────────────────────────────────────────"
echo "Run ID    : $run_id"
echo "Experiment: $experiment"
echo "Started   : $start_time"
echo

"${command[@]}"
exit_status=$?

end_epoch="$(date +%s)"
end_time="$(date '+%Y-%m-%d %H:%M:%S')"
duration=$((end_epoch - start_epoch))

if [[ $exit_status -eq 0 ]]; then
    result="SUCCESS"
else
    result="FAILED"
fi

printf '%s,%s,"%s","%s",%s,%s,%s\n' \
    "$run_id" \
    "$experiment" \
    "$start_time" \
    "$end_time" \
    "$duration" \
    "$exit_status" \
    "$result" >> "$REGISTRY"

echo
echo "RUN COMPLETE"
echo "────────────────────────────────────────────────────────────"
echo "Run ID    : $run_id"
echo "Experiment: $experiment"
echo "Finished  : $end_time"
echo "Duration  : ${duration}s"
echo "Exit code : $exit_status"
echo "Result    : $result"
echo
echo "Registry  : $REGISTRY"

read -rp "Press ENTER to return..."
exit "$exit_status"
