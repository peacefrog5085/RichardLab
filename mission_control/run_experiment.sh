#!/usr/bin/env bash

LAB="$HOME/RichardLab"
REGISTRY="$LAB/data/experiment_runs.csv"
ARTIFACT_REGISTRY="$LAB/data/experiment_artifacts.csv"
METRICS_REGISTRY="$LAB/data/experiment_metrics.csv"

mkdir -p "$LAB/data"

if [[ ! -f "$REGISTRY" ]]; then
    echo "run_id,experiment,git_commit,source_sha256,start_time,end_time,duration_seconds,exit_status,result" > "$REGISTRY"
elif ! head -n 1 "$REGISTRY" | grep -q "git_commit,source_sha256"; then
    tmp_registry="$(mktemp)"
    {
        echo "run_id,experiment,git_commit,source_sha256,start_time,end_time,duration_seconds,exit_status,result"
        tail -n +2 "$REGISTRY" | awk -F',' 'BEGIN{OFS=","} NF>=7 {print $1,$2,"UNKNOWN","UNKNOWN",$3,$4,$5,$6,$7}'
    } > "$tmp_registry"
    mv "$tmp_registry" "$REGISTRY"
fi

if [[ ! -f "$ARTIFACT_REGISTRY" ]]; then
    echo "run_id,experiment,artifact,artifact_type,size_bytes,modified_time,sha256" > "$ARTIFACT_REGISTRY"
fi

if [[ ! -f "$METRICS_REGISTRY" ]]; then
    echo "run_id,experiment,phase,timestamp,cpu_percent,ram_percent,swap_percent,disk_percent" > "$METRICS_REGISTRY"
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
        command=("$LAB/.venv/bin/python" "$target")
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
git_commit="$(git -C "$LAB" rev-parse HEAD 2>/dev/null || echo "UNKNOWN")"
source_sha256="$(sha256sum "$target" | awk '{print $1}')"
start_epoch="$(date +%s)"
start_time="$(date '+%Y-%m-%d %H:%M:%S')"

metrics_start="$("$LAB/.venv/bin/python" -c 'import psutil; print(psutil.cpu_percent(interval=1), psutil.virtual_memory().percent, psutil.swap_memory().percent, psutil.disk_usage("/").percent)')"
read -r start_cpu start_ram start_swap start_disk <<< "$metrics_start"
printf '%s,%s,START,"%s",%s,%s,%s,%s\n' "$run_id" "$experiment" "$start_time" "$start_cpu" "$start_ram" "$start_swap" "$start_disk" >> "$METRICS_REGISTRY"

echo
echo "RUN START"
echo "────────────────────────────────────────────────────────────"
echo "Run ID    : $run_id"
echo "Experiment: $experiment"
echo "Git commit: $git_commit"
echo "Source SHA : $source_sha256"
echo "Started   : $start_time"
echo

"${command[@]}"
exit_status=$?

end_epoch="$(date +%s)"
end_time="$(date '+%Y-%m-%d %H:%M:%S')"

metrics_end="$("$LAB/.venv/bin/python" -c 'import psutil; print(psutil.cpu_percent(interval=1), psutil.virtual_memory().percent, psutil.swap_memory().percent, psutil.disk_usage("/").percent)')"
read -r end_cpu end_ram end_swap end_disk <<< "$metrics_end"
printf '%s,%s,END,"%s",%s,%s,%s,%s\n' "$run_id" "$experiment" "$end_time" "$end_cpu" "$end_ram" "$end_swap" "$end_disk" >> "$METRICS_REGISTRY"
duration=$((end_epoch - start_epoch))

if [[ $exit_status -eq 0 ]]; then
    result="SUCCESS"
else
    result="FAILED"
fi

printf '%s,%s,%s,%s,"%s","%s",%s,%s,%s\n' \
    "$run_id" \
    "$experiment" \
    "$git_commit" \
    "$source_sha256" \
    "$start_time" \
    "$end_time" \
    "$duration" \
    "$exit_status" \
    "$result" >> "$REGISTRY"

echo
echo "ARTIFACT REGISTRATION"
echo "────────────────────────────────────────────────────────────"

stem="${experiment%.*}"
report_stem="${stem//-/_}"

mapfile -t artifacts < <(
    find "$LAB/reports"         -maxdepth 1         -type f         -iname "*${report_stem}*"         -newermt "$start_time"         -printf '%p\n'         2>/dev/null         | sort
)

if [[ ${#artifacts[@]} -gt 0 ]]; then
    for artifact_path in "${artifacts[@]}"; do
        artifact="$(basename "$artifact_path")"
        extension="${artifact##*.}"
        size="$(stat -c '%s' "$artifact_path")"
        modified="$(stat -c '%y' "$artifact_path" | cut -d'.' -f1)"
        sha256="$(sha256sum "$artifact_path" | awk '{print $1}')"

        case "${extension,,}" in
            png|jpg|jpeg|gif|webp)
                artifact_type="IMAGE"
                ;;
            txt|md|log)
                artifact_type="TEXT"
                ;;
            csv|json|tsv)
                artifact_type="DATA"
                ;;
            *)
                artifact_type="${extension^^}"
                ;;
        esac

        printf '%s,%s,%s,%s,%s,"%s",%s\n'             "$run_id"             "$experiment"             "$artifact"             "$artifact_type"             "$size"             "$modified"             "$sha256" >> "$ARTIFACT_REGISTRY"

        echo "$artifact"
    done
else
    echo "No new matching artifacts detected."
fi

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
echo "Metrics   : $METRICS_REGISTRY"

read -rp "Press ENTER to return..."
exit "$exit_status"
