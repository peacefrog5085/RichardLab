#!/usr/bin/env bash

LAB="$HOME/RichardLab"
REGISTRY="$LAB/data/experiment_runs.csv"
ARTIFACT_REGISTRY="$LAB/data/experiment_artifacts.csv"

clear

echo "╔════════════════════════════════════════════════════════════╗"
echo "║                     PROVENANCE VIEW                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo

if [[ ! -f "$REGISTRY" ]]; then
    echo "No experiment run registry found."
    echo
    read -rp "Press ENTER to return..."
    exit 0
fi

echo "Available Run IDs:"
echo

tail -n +2 "$REGISTRY" | cut -d',' -f1 | sort -r

echo
read -rp "Run ID: " run_id

if [[ -z "$run_id" ]]; then
    exit 0
fi

run_record="$(awk -F, -v id="$run_id" 'NR>1 && $1==id {print; exit}' "$REGISTRY")"

if [[ -z "$run_record" ]]; then
    echo
    echo "ERROR: Run not found:"
    echo "$run_id"
    read -rp "Press ENTER to return..."
    exit 1
fi

IFS=',' read -r record_id experiment start_time end_time duration exit_status result <<< "$run_record"

echo
echo "PROVENANCE RECORD"
echo "════════════════════════════════════════════════════════════════════"
echo
echo "Run ID           : $record_id"
echo "Experiment       : $experiment"
echo "Start time       : ${start_time//\"/}"
echo "End time         : ${end_time//\"/}"
echo "Duration         : $duration seconds"
echo "Exit status      : $exit_status"
echo "Result           : $result"

echo
echo "ARTIFACTS"
echo "────────────────────────────────────────────────────────────────────"

if [[ ! -f "$ARTIFACT_REGISTRY" ]]; then
    echo "No artifact registry found."
else
    artifact_count=0

    while IFS=',' read -r aid aexperiment artifact artifact_type size modified sha256; do
        [[ "$aid" == "$run_id" ]] || continue

        artifact_count=$((artifact_count + 1))

        echo
        echo "[$artifact_count] $artifact"
        echo "    Experiment : $aexperiment"
        echo "    Type       : $artifact_type"
        echo "    Size       : $size bytes"
        echo "    Modified   : ${modified//\"/}"
        echo "    SHA-256    : $sha256"

    done < <(tail -n +2 "$ARTIFACT_REGISTRY")

    if [[ "$artifact_count" -eq 0 ]]; then
        echo
        echo "No artifacts registered for this run."
    fi
fi

echo
echo "════════════════════════════════════════════════════════════════════"
echo "PROVENANCE COMPLETE"
echo

read -rp "Press ENTER to return..."
