#!/usr/bin/env bash

LAB="$HOME/RichardLab"
PROJECTS="$LAB/projects"

show_projects() {
    clear

    echo "╔══════════════════════════════════════════════════════╗"
    echo "║                  PROJECT REGISTRY                    ║"
    echo "╠══════════════════════════════════════════════════════╣"

    local count=0

    for dir in "$PROJECTS"/*; do
        [ -d "$dir" ] || continue

        count=$((count + 1))
        name="$(basename "$dir")"

        if [ -x "$dir/control.sh" ]; then
            status="READY"
        elif [ -f "$dir/control.sh" ]; then
            status="FOUND"
        else
            status="NO CONTROL"
        fi

        printf "║  %-18s %-12s               ║\n" "$name" "$status"
    done

    echo "╠══════════════════════════════════════════════════════╣"
    printf "║  Projects discovered: %-28s║\n" "$count"
    echo "╚══════════════════════════════════════════════════════╝"
}

show_projects

echo
read -rp "Press ENTER to return..."
