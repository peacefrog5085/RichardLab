#!/usr/bin/env bash

LAB="$HOME/RichardLab"
EXPERIMENTS="$LAB/experiments"

header() {
    clear
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║                  EXPERIMENT REGISTRY                   ║"
    echo "╠══════════════════════════════════════════════════════════╣"
}

show_experiments() {
    header

    local count=0

    for file in "$EXPERIMENTS"/experiment-*; do
        [ -f "$file" ] || continue

        name="$(basename "$file")"
        count=$((count + 1))

        case "$file" in
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

        printf "║  %-30s %-10s ║\n" "$name" "$type"
    done

    echo "╠══════════════════════════════════════════════════════════╣"
    printf "║  Experiments discovered: %-32s║\n" "$count"
    echo "╚══════════════════════════════════════════════════════════╝"
}

show_experiments

echo
read -rp "Press ENTER to return..."
