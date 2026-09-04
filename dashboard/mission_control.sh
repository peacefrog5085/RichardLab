#!/usr/bin/env bash

LAB="$HOME/RichardLab"

clear

header() {
    clear
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║                  RICHARDLAB                             ║"
    echo "║                 MISSION CONTROL                         ║"
    echo "╠══════════════════════════════════════════════════════════╣"
    echo "║  LAB: $LAB"
    echo "║  DATE: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo
}

pause_screen() {
    echo
    read -rp "Press ENTER to return to Mission Control..."
}

show_projects() {
    while true; do
        header

        echo "ACTIVE PROJECTS"
        echo "──────────────────────────────────────────────────────────"
        echo
        echo "  [01] THE VALUE FLOW PROJECT"
        echo "       Marvel → Disney / Value Flow Map"
        echo
        echo "  [02] FIND RICHARD SOME DAMN LAND"
        echo "       Property / land acquisition research"
        echo
        echo "  [03] CREDIT FORENSIC CLEANUP"
        echo "       Credit reporting / recovery project"
        echo
        echo "  [04] RICHARDLAB / AI LAB"
        echo "       AI experiments / tools / research"
        echo
        echo "  [05] MEDIA LAB"
        echo "       YouTube / OBS / Kdenlive / FFmpeg"
        echo
        echo "  [00] RETURN TO MAIN CONSOLE"
        echo

        read -rp "PROJECT SELECT > " project_choice

        case "$project_choice" in
            1|01)
                "$LAB/projects/value_flow/control.sh"
                ;;
            2|02)
                "$LAB/projects/land_project/control.sh"
                ;;
            3|03)
                "$LAB/projects/credit_cleanup/control.sh"
                ;;
            4|04)
                "$LAB/projects/ai_lab/control.sh"
                ;;
            5|05)
                "$LAB/projects/media_lab/control.sh"
                ;;
            0|00)
                return
                ;;
            *)
                echo
                echo "Unknown project."
                sleep 1
                ;;
        esac
    done
}

system_status() {
    header

    echo "SYSTEM STATUS"
    echo "──────────────────────────────────────────────────────────"
    echo

    echo "RichardLab:"
    if [ -d "$LAB" ]; then
        echo "  ✓ Lab directory online"
    else
        echo "  ✗ Lab directory missing"
    fi

    echo
    echo "Python:"
    if command -v python3 >/dev/null 2>&1; then
        echo "  ✓ $(python3 --version)"
    else
        echo "  ✗ Python3 unavailable"
    fi

    echo
    echo "Git:"
    if command -v git >/dev/null 2>&1; then
        echo "  ✓ $(git --version)"
    else
        echo "  ✗ Git unavailable"
    fi

    echo
    echo "Storage:"
    df -h "$LAB" | tail -1

    echo
    echo "Memory:"
    free -h | awk '/Mem:/ {print "  " $3 " used / " $2 " total"}'

    echo
    echo "CPU:"
    echo "  $(nproc) logical processors"

    pause_screen
}

project_status() {
    "$LAB/mission_control/project_registry.sh"
}

create_structure() {
    mkdir -p \
        "$LAB/projects/value_flow" \
        "$LAB/projects/land_project" \
        "$LAB/projects/credit_cleanup" \
        "$LAB/projects/ai_lab" \
        "$LAB/projects/media_lab" \
        "$LAB/data" \
        "$LAB/logs" \
        "$LAB/tools"

    touch \
        "$LAB/projects/value_flow/README.md" \
        "$LAB/projects/land_project/README.md" \
        "$LAB/projects/credit_cleanup/README.md" \
        "$LAB/projects/ai_lab/README.md" \
        "$LAB/projects/media_lab/README.md"

    echo "RichardLab project structure initialized."
}

while true; do
    header

    echo "                    MAIN CONSOLE"
    echo
    echo "  [1] OVERVIEW"
    echo "  [2] PROJECTS"
    echo "  [3] SYSTEM STATUS"
    echo "  [4] PROJECT STATUS"
    echo "  [5] EXPERIMENT STATUS"
    echo "  [6] FAMILY MAP"
    echo "  [7] LAB HEALTH"
    echo "  [8] INITIALIZE / REPAIR LAB"
    echo "  [9] OPEN LAB DIRECTORY"
    echo "  [0] EXIT"
    echo
    read -rp "MISSION CONTROL > " choice

    case "$choice" in
        1)
            python3 "$LAB/mission_control/lab_overview.py"
            pause_screen
            ;;

        2)
            show_projects
            ;;

        3)
            system_status
            ;;

        4)
            project_status
            ;;

        5)
            "$LAB/mission_control/experiment_registry.sh"
            ;;

        6)
            python3 "$LAB/mission_control/experiment_family_map.py"
            pause_screen
            ;;

        7)
            python3 "$LAB/mission_control/lab_health.py"
            pause_screen
            ;;

        8)
            create_structure
            pause_screen
            ;;

        9)
            cd "$LAB" || exit
            bash
            ;;

        0)
            clear
            echo "Mission Control offline."
            exit 0
            ;;

        *)
            echo
            echo "Unknown command. The computer remains unimpressed."
            sleep 1
            ;;
    esac
done
