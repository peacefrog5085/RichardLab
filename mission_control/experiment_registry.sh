#!/usr/bin/env bash

LAB="$HOME/RichardLab"
EXPERIMENTS="$LAB/experiments"
INSPECTOR="$LAB/mission_control/experiment_inspector.py"

header() {
    clear
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║                  EXPERIMENT REGISTRY                   ║"
    echo "╠══════════════════════════════════════════════════════════╣"
}

get_experiments() {
    find "$EXPERIMENTS" -maxdepth 1 -type f \
        \( -name 'experiment-*.sh' -o -name 'experiment-*.py' \) \
        -printf '%f\n' | sort -V
}

show_experiments() {
    header

    local count=0

    while IFS= read -r name; do
        count=$((count + 1))

        case "$name" in
            *.sh)
                type="BASH"
                ;;
            *.py)
                type="PYTHON"
                ;;
            *)
                type="OTHER"
                ;;
        esac

        printf "║  [%02d] %-27s %-10s ║\n" "$count" "$name" "$type"
    done < <(get_experiments)

    echo "╠══════════════════════════════════════════════════════════╣"
    printf "║  Experiments discovered: %-32s║\n" "$count"
    echo "╚══════════════════════════════════════════════════════════╝"
}

select_experiment() {
    local files=()
    while IFS= read -r name; do
        files+=("$name")
    done < <(get_experiments)

    while true; do
        show_experiments

        echo
        echo "  [00] RETURN TO MISSION CONTROL"
        echo

        read -rp "EXPERIMENT SELECT > " choice

        if [[ "$choice" == "0" || "$choice" == "00" ]]; then
            return
        fi

        if [[ "$choice" =~ ^[0-9]+$ ]]; then
            index=$((10#$choice))

            if (( index >= 1 && index <= ${#files[@]} )); then
                target="${files[$((index - 1))]}"

                clear
                python3 "$INSPECTOR" "$target"

                echo
                read -rp "Press ENTER to return to Experiment Registry..."
                continue
            fi
        fi

        echo
        echo "Unknown experiment selection."
        sleep 1
    done
}

select_experiment
